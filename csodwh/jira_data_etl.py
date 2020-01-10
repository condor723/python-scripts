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

    # Get Data from JIRA API
    # Returns JSON Response
    try:
        json_data = csodwh_utils.get_data_from_api(config.OATopLevelURL,
                                                   tars[1])
        if isinstance(json_data, dict):
            jdCount = len(json_data['value'])
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
                      for k, v in json_data['value'][0].items()]
        headerTuple = tuple(colHeaders)
        the_data = the_data + (headerTuple,)

        # Build the Data Rows
        for row in json_data['value']:
            pRow = ()
            for k, v in row.items():
                elemValue = v if v is not None else ''
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


if __name__ == "__main__":

    # Logging
    logging.basicConfig(filename='jira_etl.log', level=logging.INFO)
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
