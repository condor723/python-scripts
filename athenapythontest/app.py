from concurrent.futures import as_completed
from os import environ
from time import time

# boto3 is Amazon's AWS SDK for python.
# https://boto3.readthedocs.io/en/latest/index.html
import boto3

# Flask has nothing to do with Athena queries; it's just an easy to use app server for python.
# http://flask.pocoo.org/docs/quickstart/
from flask import Flask, render_template, send_file

# pandas provides nice data wrappers. For example, read_sql_query can accept a database connection and SQL query, then
# return a navigable data object while hiding the mess of data traversal, binding, mapping, etc.
# http://pandas.pydata.org/pandas-docs/stable/api.html
from pandas import DataFrame, read_sql_query
from pandas.io.sql import DatabaseError

# PyAthena is a wrapper library around the AWS SDK's Athena API. It hides some complexities involved in querying Athena,
# directly, plus provides a pythonic interface to database queries.
# https://github.com/laughingman7743/PyAthena/#pyathena
from pyathena import connect
from pyathena.async_cursor import AsyncCursor


APP_NAME = "athenapythontest"
# Determine where the app is running. When the BVFLYNN_VPC environment variable is empty, assume the app is running
# locally.
# Note: This is VERY flynn-specific. If you deploy your app using a different method (e.g. EC2, directly), use a
# different method to determine when/where the app is deployed.
# https://github.com/bazaarvoice/flynn-ops#configuration
IS_DEPLOYED = environ.get("BVFLYNN_VPC") is not None
# Get the AWS region from the environment; assume us-east-1 if no region is set (for example, when running locally). If
# you are located in the EU, you should either change the default to eu-west-1 or set AWS_REGION=eu-west-1 in your
# environemnt. When deployed, your app container should define AWS_REGION as an environment variable.
# https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html
AWS_REGION = environ.get("AWS_REGION", "us-east-1")
# The bv-nexus AWS account. All Raven data as exposed through AWS Athena is accessible in the bv-nexus account.
BV_NEXUS_ACCOUNT = ""
# Query results will be saved in the Athena results S3 bucket. PyAthena (by way of boto3) knows how to read results from
# the bucket.
# Bazaarvoice has one Athena S3 bucket per region inside the bv-nexus account.
ATHENA_BUCKET = "s3://aws-athena-query-results-{}-{}/".format(BV_NEXUS_ACCOUNT, AWS_REGION)
QUERIES = [
    # Grab a magpie transaction.
    """SELECT client, dc, locale, dt, loadid, orderid, currency, ordertotal
    FROM bazaar_magpie_raw_logs.transaction
    LIMIT 1;""",
    # Get a review.
    """SELECT client, display_code, about_id, legacy_internal_id, submission_time, rating, status, title, text
    FROM bazaar_emo_content.review
    LIMIT 1;""",
    # Grab a product from the universal catalog.
    """SELECT client, external_id
    FROM bazaar_catalog_universal.extrinsic_product
    LIMIT 1;""",
    # Get stats for a product.
    """SELECT client, externalid, reviewstatistics
    FROM bazaar_bulk_data.product_stats
    LIMIT 1;""",
]


# Use boto3, directly, to work with AWS credentials on the fly (see below). STS (Security Token Service) is AWS's
# temporary credentials service.
# https://docs.aws.amazon.com/STS/latest/APIReference/Welcome.html
sts_client = boto3.client("sts")
app = Flask(APP_NAME)


def get_raven_athena_credentials():
    # When the app is deployed (e.g. to flynn or an EC2 instance), assume the Raven-Athena role. When the app is not
    # deployed (i.e. running locally), allow the app to use the developer's credentials (e.g. from ~/.aws/credentials)
    # by returning no access key and no session token.
    # https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
    credentials = {"AccessKeyId": None, "SecretAccessKey": None, "SessionToken": None}
    if IS_DEPLOYED:
        role_arn = "arn:aws:iam::{}:role/Raven-Athena".format(BV_NEXUS_ACCOUNT)
        # The session name isn't really important so long as it is reasonably descriptive and is unique per session.
        role_session_name = APP_NAME + str(time())
        app.logger.debug("assuming role...\n%s\nsession=%s", role_arn, role_session_name)
        assumed_role = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=role_session_name)
        credentials = assumed_role["Credentials"]
    return credentials


def create_connection():
    # Create a database connection based on all of the environment information set above.
    app.logger.info("creating connection...")
    aws_credentials = get_raven_athena_credentials()
    return connect(
        s3_staging_dir=ATHENA_BUCKET,
        region_name=AWS_REGION,
        aws_access_key_id=aws_credentials["AccessKeyId"],
        aws_secret_access_key=aws_credentials["SecretAccessKey"],
        aws_session_token=aws_credentials["SessionToken"],
    )


@app.route("/", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def index():
    return send_file("index.html")


@app.route("/single", methods=["GET"])
def single():
    query = QUERIES[0]
    conn = create_connection()
    app.logger.info("executing query...\n%s", query)
    try:
        # Ask pandas to read the query results into a DataFrame for us.
        df = read_sql_query(query, conn)
        result_data = df.to_csv(index=False)
    except DatabaseError as e:
        app.logger.exception("failed to execute query!")
        result_data = str(e)
    finally:
        # Always clean up after yourself!
        app.logger.debug("closing connection...")
        conn.close()
    # Send the query results to an HTML template. Flask's underlying template rendering engine (Jinja2) will ready the
    # data for a browser. The template can be found in ./templates.
    return render_template("single.html", query=query, results=result_data)


@app.route("/multiple", methods=["GET"])
def multiple():
    queries = {}
    futures = []
    conn = create_connection()
    try:
        # Create a non-blocking cursor so multiple queries can be run at the same time and collect the future objects
        # to be waited on.
        # https://docs.python.org/3/library/concurrent.futures.html#future-objects
        cursor = conn.cursor(AsyncCursor)
        for query in QUERIES:
            app.logger.info("executing query...\n%s", query)
            query_id_ignored, future = cursor.execute(query)
            futures.append(future)
        app.logger.info("waiting for query results...")
        for future in as_completed(futures):
            query_result = future.result()
            app.logger.debug("reading query results...\n%s", query_result.query)
            if "SUCCEEDED" == query_result.state:
                # Because an asynchronous cursor was used, and because of the asynchronous cursor's result structure,
                # pandas cannot use the results, directly. So, extract the column names and data, separately.
                # https://github.com/laughingman7743/PyAthena/#asynchronous-cursor
                columns = [x[0] for x in query_result.description]
                result_data = DataFrame.from_records(query_result, columns=columns)
                queries[query_result.query] = result_data.to_csv(index=False)
            else:
                queries[query_result.query] = query_result.state_change_reason
    finally:
        # Always clean up after yourself!
        app.logger.debug("closing connection...")
        conn.close()
    # Send the query results to an HTML template. Flask's underlying template rendering engine (Jinja2) will ready the
    # data for a browser. The template can be found in ./templates.
    return render_template("multiple.html", queries=queries)


if __name__ == "__main__":
    print("Do not run this script, directly. Use the start script, start.sh, instead.")
