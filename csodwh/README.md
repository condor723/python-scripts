# Client Services Operations Data Warehouse (CSODWH)


OpenAir Nightly Job
Loads the following OpenAir Reports into Redshift DB.
- Projects
- Users
- Timesheets
- Bookings

How to Run
Make sure your Python virtual environment is running.

python3 odata_etl.py

You will need credentials to:
- OpenAir
- Redshift

View logging here:

tail -f etl.log