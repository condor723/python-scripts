from re import sub
import pandas as pd
import sys
import datetime
import itertools
from math import ceil as roundup
import logging

# HOW TO RUN
# python3 transform.py clientname filename incremental
# set incremental to true, default is false

# Global Variables
cbList = []


def id_clean(elem):
    if isinstance(elem, int):
        elem = str(elem)

    elem = elem.strip()
    if '&' in elem:
        elem = elem.replace('&', 'and')
    if any(char in elem for char in ('>', '<', ',', '.', '/', '', '',
           '', '', '®', '©', '™')):
        elem = sub(r'[>|<|,|\.|\/|||||®|©|™]', '', elem)
    if ' ' in elem:
        elem = elem.replace(' ', '_')
    return elem


def xml_clean(elem):
    if isinstance(elem, int):
        elem = str(elem)

    elem = elem.strip()
    if '&' in elem:
        elem = sub(r'&(?!amp;)(?!gt;)(?!lt;)(?!#)', '&amp;', elem)
    if '<' in elem:
        elem = sub(r'<', '&lt;', elem)
    if '>' in elem:
        elem = sub(r'>', '&gt;', elem)
    if any(char in elem for char in ('', '', '', '')):
        elem = sub(r'[|||]', '', elem)
    return elem


def validate_upcs(upcs):
    if isinstance(upcs, int):
        upcsSplit = [str(upcs)]
    else:
        upcsSplit = [x.strip() for x in upcs.split(',')]

    valid_upcs = []
    for upc in upcsSplit:
        if len(upc) in (6, 12):
            try:
                upc_digits = [int(x) for x in upc]
            except ValueError:
                logging.warning("'{}' has non-numeric characters".format(upc))
                continue
            for i in range(len(upc_digits[:-1])):
                if i % 2 == 0:
                    upc_digits[i] = upc_digits[i] * 3
            round_nearest_ten = int(roundup(float(
                                    sum(upc_digits[:-1])) / 10) * 10)
            if round_nearest_ten - sum(upc_digits[:-1]) == upc_digits[-1]:
                valid_upcs.append('<UPC>' + upc + '</UPC>')
            else:
                logging.warning('UPC: Invalid Checkdigit - {}'.format(upc))
        elif len(upc) in range(7, 12):
            zeroes = ''
            add = 12 - len(upc)
            for i in range(add):
                zeroes += '0'
            upc = zeroes + upc
            try:
                upc_digits = [int(x) for x in upc]
                for i in range(len(upc_digits[:-1])):
                    if i % 2 == 0:
                        upc_digits[i] = upc_digits[i] * 3
                round_nearest_ten = int(roundup(float(
                                        sum(upc_digits[:-1])) / 10) * 10)
                if round_nearest_ten - sum(upc_digits[:-1]) == upc_digits[-1]:
                    valid_upcs.append('<UPC>' + upc + '</UPC>')
                else:
                    upc = upc[len(zeroes):]
                    logging.warning('UPC: Invalid Length - {}'.format(upc))

            except ValueError:
                upc = upc[len(zeroes):]
                logging.warning('UPC: Invalid Length - {}'.format(upc))

    if len(valid_upcs) > 0:
        all_upcs = "".join(set(valid_upcs))
        return all_upcs
    else:
        return ''


def validate_eans(eans):
    if isinstance(eans, str):
        eansSplit = [x.strip() for x in eans.split(',')]
    else:
        eansSplit = [str(eans)]

    valid_eans = []
    for ean in eansSplit:
        if len(ean) in (8, 13):
            try:
                ean_digits = [int(x) for x in ean]
            except ValueError:
                logging.warning("'{}' has non-numeric characters".format(ean))
                continue
            for i in range(len(ean_digits[:-1])):
                if len(ean) == 8:
                    if i % 2 == 0:
                        ean_digits[i] = ean_digits[i] * 3
                else:
                    if i % 2 != 0:
                        ean_digits[i] = ean_digits[i] * 3
            round_nearest_ten = int(roundup(float(
                                    sum(ean_digits[:-1])) / 10) * 10)
            if round_nearest_ten - sum(ean_digits[:-1]) == ean_digits[-1]:
                valid_eans.append('<EAN>' + ean + '</EAN>')
            else:
                logging.warning('EAN: Invalid Checkdigit - {}'.format(ean))
        elif len(ean) in range(9, 13):
            zeroes = ''
            add = 13 - len(ean)
            for i in range(add):
                zeroes += '0'
            ean = zeroes + ean
            try:
                ean_digits = [int(x) for x in ean]
                for i in range(len(ean_digits[:-1])):
                    if i % 2 != 0:
                        ean_digits[i] = ean_digits[i] * 3
                round_nearest_ten = int(roundup(float(
                                        sum(ean_digits[:-1])) / 10) * 10)
                if round_nearest_ten - sum(ean_digits[:-1]) == ean_digits[-1]:
                    valid_eans.append('<EAN>' + ean + '</EAN>')
                else:
                    logging.warning('EAN: Invalid Length - {}'.format(ean))
            except ValueError:
                ean = ean[len(zeroes):]
                logging.warning(ean, 'EAN: Invalid Length - Too Many Zeroes? - {}'.format(ean))
        elif ean != '':
            logging.warning('EAN: Invalid Length')

    if len(valid_eans) > 0:
        all_eans = "".join(set(valid_eans))
        return all_eans
    else:
        return ''


def validate_mpns(mpns):
    if isinstance(mpns, int):
        mpnsSplit = [str(mpns)]
    else:
        mpnsSplit = [x.strip() for x in mpns.split(',')]

    valid_mpns = []
    for mpn in mpnsSplit:
        if mpn is not '':
            valid_mpns.append('<ManufacturerPartNumber>' +
                              xml_clean(mpn) + '</ManufacturerPartNumber>')

    if len(valid_mpns) > 0:
        all_mpns = "".join(set(valid_mpns))
        return all_mpns
    else:
        return ''


def validate_ex_ids(elem):
    elem = id_clean(elem)
    if '|_' in elem:
        elem = elem.rsplit('|_', 1)[1]
    return elem


def build_cats_brands(elem):
    name = xml_clean(elem)
    if name.endswith('|'):
        name = name[:-1]
    nameSplit = [x.strip() for x in name.split('|')]
    catName = ''
    global cbList
    if len(nameSplit) > 1:
        for i in range(len(nameSplit)):
            if i - 1 >= 0 and nameSplit[i] is not '':
                cbList.append([id_clean(nameSplit[i]), nameSplit[i],
                               id_clean(nameSplit[i - 1])])
            elif nameSplit[i] is not '':
                cbList.append([id_clean(nameSplit[i]), nameSplit[i], ''])
            catName = id_clean(nameSplit[i])
    else:
        if name is not '':
            cbList.append([id_clean(name), name, ''])
            catName = id_clean(name)
    return catName


def build_families(elem):
    elem = id_clean(elem)
    eList = []
    if elem is not '':
        eList.append('<Attribute id="BV_FE_FAMILY"><Value>' +
                     elem + '</Value></Attribute>')
        eList.append('<Attribute id="BV_FE_EXPAND"><Value>BV_FE_FAMILY:' +
                     elem + '</Value></Attribute>')

    if len(eList) > 0:
        all_families = "".join(set(eList))
        return all_families
    else:
        return ''


# BUILD XML FROM DATA FRAME
def product_to_xml(df):
    def row_to_xml(row):
        xml = ['<Product>']
        for i, col_name in enumerate(row.index):
            if row.iloc[i] is not '':
                xml.append('  <{0}>{1}</{0}>'.format(col_name, row.iloc[i]))

        xml.append('</Product>')
        return '\n'.join(xml)

    res = '\n'.join(df.apply(row_to_xml, axis=1))

    return res


def category_to_xml(df):
    def row_to_xml(row):
        xml = ['<Category>']
        for i, col_name in enumerate(row.index):
            if row.iloc[i] is not '':
                xml.append('  <{0}>{1}</{0}>'.format(col_name, row.iloc[i]))

        xml.append('</Category>')
        return '\n'.join(xml)

    dfCat = df.apply(row_to_xml, axis=1)
    if len(dfCat) is not 0:
        res = '\n'.join(df.apply(row_to_xml, axis=1))
    else:
        res = None
    return res


def brand_to_xml(df):
    def row_to_xml(row):
        xml = ['<Brand>']
        for i, col_name in enumerate(row.index):
            if row.iloc[i] is not '':
                xml.append('  <{0}>{1}</{0}>'.format(col_name, row.iloc[i]))

        xml.append('</Brand>')
        return '\n'.join(xml)

    res = '\n'.join(df.apply(row_to_xml, axis=1))

    return res


def main():
    # ASSIGN FUNCTIONS TO PANDAS DATAFRAME
    pd.DataFrame.product_to_xml = product_to_xml
    pd.DataFrame.category_to_xml = category_to_xml
    pd.DataFrame.brand_to_xml = brand_to_xml

    # LOGGING
    logging.basicConfig(filename='logfile', level=logging.DEBUG)
    date = datetime.datetime.now()
    logging.info("Starting python script at {}".format(date))

    # GET XLSX FILE
    client_name = sys.argv[1] if sys.argv[1] else None
    the_file = sys.argv[2] if sys.argv[2] else None
    incrmtl = sys.argv[3] if sys.argv[3] else 'false'

    # READ THE FILE
    colHeaders = ['ExternalId', 'Name', 'Description', 'BrandExternalId',
                  'UPCs', 'EANs', 'ManufacturerPartNumbers', 'ProductPageUrl',
                  'ImageUrl', 'CategoryExternalId', 'Attributes']
    data = pd.read_excel(the_file, header=None, names=colHeaders,
                         index_col=None)

    # REMOVE FIRST TWO ROWS
    data = data.iloc[2:]

    # REMOVE ROWS WITHOUT PRODUCTIDS
    tRows = len(data)
    logging.info("Total Rows: {}".format(tRows))
    data = data.dropna(subset=['ExternalId', 'Name', 'BrandExternalId'])
    noIds = tRows - len(data)
    if noIds > 0:
        logging.info("Total Missing Product IDs: {}".format(noIds))

    # REMOVE NAN VALUES
    data = data.fillna('')

    # REPLACE NEW LINES WITH PERIODS IN DESCRIPTIONS
    data['Name'] = data['Name'].apply(xml_clean)
    data['Description'] = data['Description'].apply(xml_clean)
    data['ProductPageUrl'] = data['ProductPageUrl'].apply(xml_clean)
    data['ImageUrl'] = data['ImageUrl'].apply(xml_clean)
    data['Attributes'] = data['Attributes'].apply(build_families)

    # REMOVE SPACES FROM UPCS / EANS / MPNS
    data['UPCs'] = data['UPCs'].apply(validate_upcs)
    data['EANs'] = data['EANs'].apply(validate_eans)
    data['ManufacturerPartNumbers'] = data['ManufacturerPartNumbers'].apply(validate_mpns)

    # BUILD CATEGORY AND BRAND DATAFRAMES
    global cbList
    cbCols = ['ExternalId', 'Name', 'ParentExternalId']
    # BUILD LIST OF CATEGORY NODES
    data['CategoryExternalId'] = data['CategoryExternalId'].apply(build_cats_brands)
    # DEDUPE LIST OF LISTS
    cbList.sort()
    cList = list(cbList for cbList, _ in itertools.groupby(cbList))
    # CREATE DATAFRAME FROM LIST
    catDF = pd.DataFrame(cList, columns=cbCols)

    cbList.clear()
    # BUILD LIST OF BRAND NODES
    data['BrandExternalId'].apply(build_cats_brands)
    # DEDUPE LIST OF LISTS
    cbList.sort()
    bList = list(cbList for cbList, _ in itertools.groupby(cbList))
    # CREATE DATAFRAME FROM LIST
    brandDF = pd.DataFrame(bList, columns=cbCols)

    # CLEANUP EXTERNALIDS
    data['ExternalId'] = data['ExternalId'].apply(id_clean)
    data['BrandExternalId'] = data['BrandExternalId'].apply(validate_ex_ids)
    #data['CategoryExternalId'] = data['CategoryExternalId'].apply(validate_ex_ids)
    #print(data['CategoryExternalId'])
    # GENERATE OUTPUT XML FILE
    output = 'outputfile'
    pFeedSchema = 'http://www.bazaarvoice.com/xs/PRR/ProductFeed/14.7'
    try:
        with open(output, 'w') as out:
            out.write('<?xml version="1.0" encoding="utf-8"?>\n')
            out.write('<Feed xmlns="{}" name="{}" incremental="{}" extractDate="{}T{}.000000">\n'
                      .format(pFeedSchema, client_name,
                              incrmtl,
                              date.strftime('%Y-%m-%d'),
                              date.strftime('%H:%M:%S')))
            out.write('<Brands>\n' + brandDF.brand_to_xml() + '</Brands>\n')
            catStr = catDF.category_to_xml()
            if catStr is not None:
                out.write('<Categories>\n' + catStr +
                          '</Categories>\n')
            out.write('<Products>\n' + data.product_to_xml() + '</Products>\n')
            out.write('</Feed>')
    except Exception as e:
        logging.error("Error while writing output: {}".format(str(e)))

    dateEnd = datetime.datetime.now()
    logging.info("Python script complete {}".format(dateEnd))


if __name__ == "__main__":
    main()
