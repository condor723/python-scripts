import pandas as pd
import sys

# HOW TO RUN
# python3 transform.py clientname filename

# GET XLSX FILE
client_name = sys.argv[1] if sys.argv[1] else None
the_file = sys.argv[2] if sys.argv[2] else None

# READ THE FILE
data = pd.read_excel(the_file, header=None, index_col=0)

# REMOVE FIRST TWO ROWS AND LAST ROW
data = data.iloc[2:-1]
# REMOVE ROWS WITHOUT PRODUCTIDS
data = data.dropna(subset=[1])

# CLEANUP PRODUCTIDS
data.index = data.index.str.replace('/', '_')

# REPLACE NEW LINES WITH PERIODS
data.iloc[:, 1] = data.iloc[:, 1].str.replace('\n', '. ')

# REMOVE SPACES FROM UPCS & EANS
data.iloc[:, 3] = data.iloc[:, 3].str.replace(' ', '').str.replace(',', ' ').str.replace('\n', '')
data.iloc[:, 4] = data.iloc[:, 4].str.replace(' ', '').str.replace(',', ' ').str.replace('\n', '')

# CLEAN UP PRODUCT FAMILY VALUES IF THEY EXIST
if not data.iloc[:, 9].empty:
    data.iloc[:, 9] = data.iloc[:, 9].str.replace(' ', '_')
    # ADD BV_FE_EXPAND COLUMN
    data[11] = 'BV_FE_FAMILY:' + data[10]

# WRITE THE MULTISOURCE PRODUCT FEED CSV
new_file = client_name + '_product_feed.csv'
with open(new_file, 'w', encoding='utf-8') as nf:
    nf.write('//attributeMode=MERGE,catalogMode=INCREMENTAL, '
             'multiValueMode=APPEND,activateMode=ACTIVATE\n')
    nf.write('EXTERNALID|NAME|DESCRIPTION|BRAND|UPC|EAN|MPN|'
             'PRODUCTURL|IMAGEURL|CATEGORY|BV_FE_FAMILY|BV_FE_EXPAND\n')
data.to_csv(new_file, sep='|', header=False, mode='a')
