from lxml import objectify, etree as ET
from pathlib import Path
import pandas as pd
import datetime
import sys
import csv
import logging

# HOW TO RUN
# python3 transform.py scfName.xml fieldsToPull.csv

# Logging
logging.basicConfig(filename='logfile', level=logging.DEBUG)
date = datetime.datetime.now()
logging.info("Starting python script at {}".format(date))


def getBrand(elements, ns):
    brand = ''
    if elements is not None:
        for elem in elements.iter('{' + ns + '}' + 'Name'):
            brand = elem.text
    return brand


def getIDAndOneChild(elements, ns, attribute, child):
    result = ''
    if elements is not None:
        attributes = ()
        for elem in elements.iter('{' + ns + '}' + attribute, '{' + ns + '}' + child):
            tName = ET.QName(elem.tag).localname
            if tName == attribute:
                entry = ''
                entry = entry + elem.attrib['id']
            else:
                entry = entry + ":" + elem.text
                attributes = attributes + (entry,)
        result = '|'.join(attributes)
    return result


def getElementsText(elements, elemList):
    result = ''
    if elements is not None:
        count = 0
        for el in elements.iter(elemList):
            if count is 0:
                result = result + el.text
            elif count == len(elemList):
                result = result + '|' + el.text
                count = 0
            else:
                result = result + ':' + el.text
            count = count + 1
    return result


def cdvParse(elements, ns):
    result = ''
    if elements is not None:
        attributes = ()
        for cdd in elements.iterfind('.//{' + ns + '}ContextDataDimension'):
            cddId = cdd.get('id')
            cdvId = cdd.getparent().get('id')
            entry = cddId + ':' + cdvId
            attributes = attributes + (entry,)
        result = '|'.join(attributes)
    return result


def main():
    # Load the Files
    the_file = sys.argv[1] if len(sys.argv) > 1 else ''
    fields_file = sys.argv[2] if len(sys.argv) > 2 else ''

    tf = Path(the_file)
    tf2 = Path(fields_file)
    if tf.is_file() and tf2.is_file():
        try:
            with open(the_file) as f:
                # Get the Fields to Pull
                data = pd.read_csv(fields_file, header=None, index_col=0)
                reviewFields = list(data.loc[['Review'], 1])
                productFields = list(data.loc[['Product'], 1])
                # Load the SCF XML
                xmldata = objectify.parse(f)
                data = xmldata.getroot()
                ns = data.nsmap[None]
                # Set some variables
                output = ()
                rCount = 0
                pCount = 0
                # Build the header row
                productHeaders = ['Product' + i for i in productFields]
                reviewHeaders = ['Review' + i for i in reviewFields]
                headerTuple = tuple(productHeaders + reviewHeaders)
                output = output + (headerTuple,)
                # Iterate thru products & reviews
                for product in data.xpath("//t:Product", namespaces={'t': ns}):
                    pRow = ()
                    pCount = pCount + 1
                    for pElem in productFields:
                        element = product.find('{' + ns + '}' + pElem)
                        if pElem == 'Brand':
                            elemValue = getBrand(element, ns)
                        elif pElem == 'Attributes':
                            elemValue = getIDAndOneChild(element, ns, 'Attribute', 'Value')
                        elif pElem == 'CategoryItems':
                            elemValue = getIDAndOneChild(element, ns, 'CategoryItem', 'CategoryName')
                        else:
                            elemValue = element.text if element is not None else ''
                        pRow = pRow + (elemValue,)
                    # pRow has all product columns included
                    # ITERATE OVER REVIEWS
                    for review in product.iterfind('.//{' + ns + '}Review'):
                        rRow = ()
                        prRow = ()
                        rCount = rCount + 1
                        for rElem in reviewFields:
                            rElement = review.find('{' + ns + '}' + rElem)
                            if rElem == 'Badges':
                                getList = ['BadgeType', 'Name', 'ContentType']
                                getListNS = ['{' + ns + '}' + i for i in getList]
                                rValue = getElementsText(rElement, tuple(getListNS))
                            elif rElem == 'UserProfileReference':
                                getList = ['ExternalId', 'DisplayName']
                                getListNS = ['{' + ns + '}' + i for i in getList]
                                rValue = getElementsText(rElement, tuple(getListNS))
                            elif rElem == 'ContextDataValues':
                                rValue = cdvParse(rElement, ns)
                            elif rElem == 'id':
                                rValue = review.get('id')
                            else:
                                rValue = rElement.text if rElement is not None else ''
                            # rRow has all review columns included
                            rRow = rRow + (rValue,)
                        # prRow combines pRow and rRow tuples into one tuple
                        prRow = pRow + rRow
                        # add prRow to final output tuple - creates tuple of tuples
                        output = output + (prRow,)

                # Write output to CSV
                outFile = the_file.replace('.xml', '.csv')
                result = open(outFile, 'w')
                writer = csv.writer(result, dialect='excel')
                writer.writerows(output)
                result.close()

                # Print data stats
                print('Product Count: ' + str(pCount))
                print('Review Count: ' + str(rCount))
                print('Output Tuple Length: ' + str(len(output)) + '\n')

        except IOError as x:
            print(x)

    else:
        logging.error("File(s) Do Not Exist: {},{}".format(str(tf), str(tf2)))
        print("File(s) Do Not Exist: {},{}".format(str(tf), str(tf2)))

    dateF = datetime.datetime.now()
    logging.info("Ending python script at {}".format(dateF))


if __name__ == "__main__":
    main()
