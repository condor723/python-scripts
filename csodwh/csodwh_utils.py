import ast
import boto3
import config
import csv
import json
import oa_creds
import psycopg2
import urllib.request
from botocore.exceptions import ClientError
from dateutil.parser import parse
from re import sub


def get_data_from_api(OATopLevelURL, report):
    # Setting up basic http authentication
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, OATopLevelURL, oa_creds.oa_username,
                              oa_creds.oa_password)
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    opener = urllib.request.build_opener(handler)
    urllib.request.install_opener(opener)

    # Hit API until it returns <1000 records
    skip = 0
    jdCount = 1000
    json_results = []
    while jdCount == 1000:
        url = OATopLevelURL + report + '?$top=1000&$skip=' + str(skip)
        try:
            with urllib.request.urlopen(url) as link:
                json_data = json.loads(link.read().decode())
                jdCount = len(json_data['value'])
                skip += 1000
                json_results.extend(json_data['value'])
        except Exception as e:
            print(str(e))
            raise
    return json_results


def write_to_csv(file, data):
    try:
        with open(file, 'w') as out:
            writer = csv.writer(out, delimiter='|')
            writer.writerows(data)
            out.close()
    except Exception as e:
        print(str(e))
        raise


def redshift_connect_execute(statement):
    try:
        conn = psycopg2.connect(
            host=config.redshift_host,
            port=config.redshift_port,
            user=oa_creds.redshift_username,
            password=oa_creds.redshift_password,
            dbname=config.redshift_db)

        cur = conn.cursor()
        cur.execute(statement)
        conn.commit()
        return True
    except Exception as e:
        print(str(statement) + '\n' + str(e))
        raise


class S3Error(Exception):
    """ Exception used when S3 interactions fail"""
    pass


def upload_to_s3(file, bucket_name, region, object_name=None):
    try:
        if object_name is None:
            object_name = file
        else:
            object_name = object_name.replace('-', '_')
        s3 = boto3.resource('s3', region_name=region)
        s3.Bucket(bucket_name).put_object(Key=object_name, Body=file)
        return "s3://{}/{}".format(bucket_name, object_name)
    except (ClientError) as e:
        raise S3Error("Problem copying file to S3: {} -> s3://{}/{} [{}]"
                      .format(file, bucket_name, object_name, str(e)))


def key_exists(bucket_name, key_name):
    s3 = boto3.resource('s3')

    try:
        s3.Object(bucket_name, key_name).load()
    except ClientError as e:
        if e.response['Error']['Code'] == "404":
            exists = False
        else:
            raise e
    else:
        exists = True

    return exists


def download_file_from_s3(bucket_name, key_name, local_file_fqn):
    try:
        client = boto3.client('s3')
        if key_exists(bucket_name, key_name):
            client.download_file(bucket_name, key_name, local_file_fqn)
    except (ClientError) as e:
        raise S3Error("Problem downloading file from s3://{}/{} to {} [{}]"
                      .format(bucket_name, key_name, local_file_fqn, str(e)))
    return


def id_clean(elem):
    if isinstance(elem, int):
        elem = str(elem)

    elem = elem.strip()
    if '&' in elem:
        elem = elem.replace('&', 'and')
    if '-' in elem:
        elem = elem.replace('-', '')
    if '%' in elem:
        elem = elem.replace('%', 'percent')
    if ':' in elem:
        elem = elem.replace(':', '_')
    # user is a reserved word in postgres
    if elem.lower() == 'user':
        elem = 'user_id'
    if any(char in elem for char in ('>', '<', ',', '.', '/', '^H', '^P',
                                     '^Z', '^C', '®', '©', '™', '(', ')')):
        elem = sub(r'[>|<|,|\.|\/|^H|^P|^Z|^C|®|©|™|(|)]', '', elem)
    if ' ' in elem:
        elem = elem.replace(' ', '_')
    return elem


def make_safe(elem):
    if type(elem) in [int, float]:
        elem = str(elem)
    elem = elem.strip()
    # user is a reserved word in postgres
    if elem.lower() == 'user':
        elem = 'user_id'
    if any(char in elem for char in ('>', '<', '/', '®',
                                     '©', '™', '(', ')')):
        elem = sub(r'[>|<|\/|®|©|™|(|)]', '', elem)
    return elem


def dataType(elem, ctype):
    if isinstance(elem, str):
        elem = str(elem)
        if elem.find('|') != -1:
            elem = elem.replace('|', ':')
        elif elem.find('-') != -1 and is_date(elem):
            if len(elem) > 10:
                return 'varchar'
            else:
                return 'date'
        elif (elem.find(':') != -1 or elem.find('@') != -1):
            return 'varchar'
        else:
            try:
                # Evaluates numbers to an appropriate type, and strings an error
                t = ast.literal_eval(elem)
            except ValueError:
                return 'varchar'
            except SyntaxError:
                return 'varchar'

            if type(t) in [int, float]:
                if (type(t) in [int]) and ctype not in ['float', 'varchar']:
                    # Use smallest possible int type
                    if (-32768 < t < 32767) and ctype not in ['int', 'bigint']:
                        return 'varchar'
                    elif (-2147483648 < t < 2147483647) and ctype not in ['bigint']:
                        return 'int'
                    else:
                        return 'bigint'
                if type(t) is float and ctype not in ['varchar']:
                    return 'varchar'
            else:
                return 'varchar'


def is_date(string, fuzzy=False):
    # Return whether the string can be interpreted as a date.
    # :param string: str, string to check for date
    # :param fuzzy: bool, ignore unknown tokens in string if True
    try:
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False
