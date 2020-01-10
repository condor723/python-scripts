import config
import csodwh_utils
import csv
import datetime
import logging
import threading
import oa_creds
import os


def etl_report_to_table(tars):
    # Create CSVs
    output = '{}_{}.csv'.format(tars[0], str(date))
    the_data = ()
    tName = tars[0].capitalize()

    # Get Data from Open Air API
    # Returns JSON Response
    try:
        json_data = csodwh_utils.get_data_from_api(config.OATopLevelURL,
                                                   tars[1])
        if isinstance(json_data, list):
            jdCount = len(json_data)
            logging.info("{} OpenAir API Request Successful"
                         .format(tName))
            logging.info("{} OpenAir API Request Results: {}"
                         .format(tName, str(jdCount)))
        else:
            logging.error("{} OpenAir API Returned Unexpected Result: {}"
                          .format(tName, str(json_data)))
            exit(1)
    except Exception as e:
        logging.error("{} OpenAir API Request Failed: {}"
                      .format(tName, str(e)))
        exit(1)

    # Build CSVs
    try:
        # Build the Header Row
        colHeaders = [csodwh_utils.id_clean(k)
                      for k, v in json_data[0].items()]
        headerTuple = tuple(colHeaders)
        the_data = the_data + (headerTuple,)

        # Build the Data Rows
        for row in json_data:
            pRow = ()
            for k, v in row.items():
                elemValue = csodwh_utils.make_safe(v) if v is not None else ''
                pRow = pRow + (elemValue,)
            the_data = the_data + (pRow,)
        # Write output to CSV
        try:
            csodwh_utils.write_to_csv(output, the_data)
            logging.info("{} CSV Created Successfully"
                         .format(tName))
        except Exception as e:
            logging.error("Failed to Write {} CSV: {}"
                          .format(tName, str(e)))
            exit(1)
    except Exception as e:
        logging.error("Failed to Build {} Data Object: {}"
                      .format(tName, str(e)))
        exit(1)

    # Upload CSV to S3
    try:
        fDate = str(date).replace('-', '_')
        s3_key = "{}/{}/{}/{}".format(config.S3_KEY_PREFIX, fDate,
                                      tName, output)
        with open(output, 'rb') as f:
            try:
                s3_csv = csodwh_utils.upload_to_s3(f, config.S3_BUCKET,
                                                   config.S3_REGION,
                                                   s3_key)
                logging.info("{} CSV Uploaded to S3 Successfully: {}"
                             .format(tName, s3_csv))
                # os.remove(output)
            except Exception as e:
                logging.error("{}".format(str(e)))
                # os.remove(output)
                exit(1)
    except Exception as e:
        logging.error("Failed to Open {} CSV: {}"
                      .format(tName, str(e)))
        exit(1)

    # Load Data to Redshift From S3
    try:
        with open(output, 'r') as f:
            # Build Drop/Create SQL Statement
            reader = csv.reader(f, delimiter='|')
            longest, headers, type_list = [], [], []
            for row in reader:
                if len(headers) == 0:
                    headers = row
                    for col in row:
                        longest.append(65535)
                        type_list.append('')
                else:
                    for i in range(len(row)):
                        if type_list[i] == 'varchar':
                            pass
                        else:
                            var_type = csodwh_utils.dataType(row[i],
                                                             type_list[i])
                            type_list[i] = var_type
                    if len(row[i]) > longest[i]:
                        longest[i] = len(row[i])

            statement = ("drop table if exists openair.{};"
                         "create table openair.{} ("
                         ).format(tars[0], tars[0])

            for i in range(len(headers)):
                if type_list[i] == 'varchar':
                    statement = (statement + '\n{} varchar({}),').format(
                        headers[i].lower(), str(longest[i]))
                else:
                    statement = (statement + '\n' + '{} {}' + ',').format(
                        headers[i].lower(), type_list[i])
            statement = statement[:-1] + ');'
    except Exception as e:
        logging.error("Failed to Read {} CSV: {}"
                      .format(tName, str(e)))

    # Connect to Redshift
    try:
        # Execute Drop/Create SQL
        csodwh_utils.redshift_connect_execute(statement)
        logging.info("{} Table Dropped Successfully".format(tName))

        # Load CSVs into Redshift
        sql = """copy {} from '{}'
              access_key_id '{}'
              secret_access_key '{}'
              region '{}'
              ignoreheader 1 null as ''
              delimiter '|' escape removequotes;
              """.format(tars[0], s3_csv,
                         oa_creds.redshift_access_key_id,
                         oa_creds.redshift_secret_access_key,
                         config.S3_REGION)

        csodwh_utils.redshift_connect_execute(sql)
        logging.info("{} Loaded to Redshift Successfully".format(tName))

    except Exception as e:
        logging.error("Load Data to Redshift Failed: {}".format(e))


if __name__ == "__main__":

    # Logging
    logging.basicConfig(filename='etl.log', level=logging.INFO)
    date = datetime.date.today()
    startTime = datetime.datetime.now()
    logging.info("Starting Python Script: {}".format(startTime))

    # Implemented threading to speed up job & prevent errors
    # in one report to cause all to fail.
    # Loop Thru Tables & Reports that need to be ETL'd
    jobs = []
    for tar in config.tbls_and_reports:
        thread = threading.Thread(target=etl_report_to_table, args=(tar,))
        jobs.append(thread)

    for j in jobs:
        j.start()

    for j in jobs:
        j.join()

    # Logging End
    endTime = datetime.datetime.now()
    logging.info("Ended Python Script: {}".format(endTime))
    runTime = (endTime - startTime).total_seconds()
    logging.info("Python Script Run Time: {}".format(str(runTime)))
