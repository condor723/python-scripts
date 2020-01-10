# Reports to ETL from OpenAir -> BV CS Data Warehouse (Redshift DB)
OATopLevelURL = "https://www.openair.com/odata/v4/reports/"

# Report layout: ('Redshift Table', 'OpenAir Report #')
# Needs to be > 2 reports or script will break
# Function is looking for tuple of tuples
tbls_and_reports = (('projects', 'report101'),
                    ('users', 'report93'),
                    ('timesheets', 'report91'),
                    ('bookings', 'report102'))

S3_BUCKET = "sit-csodwh-prod"
S3_KEY_PREFIX = "Data"
S3_REGION = "us-east-1"

redshift_host = ""
redshift_port = "5439"
redshift_db = "main"
redshift_schema = "openair"
