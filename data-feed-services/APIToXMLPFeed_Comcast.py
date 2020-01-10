import sys
import json
import urllib.request
import datetime
import logging 

logging.basicConfig(filename='comcast.log',level=logging.DEBUG)

date = datetime.datetime.now()
logging.info("Starting python script at {}".format(date))
output = "output/feed-{}.xml".format(date.strftime('%Y%m%d-%H%M%S'))

def get_data_from_file():
    try:
        json_file = open(sys.argv[1],'r')
        json_data = json.loads(json_file.read())
        return json_data
    except FileNotFoundError as e:
        logging.warning("File not found")
        raise FileNotFoundError

def get_data_from_API():
    try:
        with urllib.request.urlopen("https://pcat.mobile.xfinity.com/products") as url:
            json_data = json.loads(url.read().decode())
            return json_data
    except Exception as e:
        print(str(e))
        raise

try:
    json_data = get_data_from_file()
except FileNotFoundError:
    try:
        json_data = get_data_from_API()
    except Exception as e:
        logging.error("Fallback request to API failed: {}".format(str(e)))
        exit(1)
except Exception as e:
    logging.error("Unexpected error while getting data: {}".format(str(e)))

#Check if we have full json with all products
try:
    if (len(json_data['products']) != json_data['totalNumberOfRecords']):
        logging.warning("Missing products in json")
except KeyError: 
    logging.warning("Json object might be incomplete - missing totalNumberOfRecords")

try: 
    with open(output, 'a') as out:
        out.write('<?xml version="1.0" encoding="utf-8"?>')
        out.write('<Feed xmlns="http://www.bazaarvoice.com/xs/PRR/ProductFeed/14.7" name="comcast" incremental="false" extractDate="{}T{}.000000">'.format(date.strftime('%Y-%m-%d'), date.strftime('%H:%M:%S')))

        out.write('<Brands>')
        for item in json_data['products']:
                out.write('<Brand><ExternalId>'+item['brandCode']+'</ExternalId><Name><![CDATA['+item['brand']+']]></Name></Brand>')    
        out.write('</Brands>')
        out.write('<Categories>')
        for item in json_data['products']:
                out.write('<Category><Name><![CDATA['+item['category']+']]></Name><ExternalId>'+item['category']+'</ExternalId></Category>')
        out.write('</Categories>')
        out.write('<Products>')
        for item in json_data['products']:
                out.write('<Product><ExternalId>'+item['productCode']+'</ExternalId><Name><![CDATA['+item['name']+']]></Name><CategoryExternalId><![CDATA['+item['category']+']]></CategoryExternalId><BrandExternalId>'+item['brandCode']+'</BrandExternalId><ImageUrl><![CDATA['+item['image']['url']+']]></ImageUrl></Product>')
        out.write('</Products>')
        out.write('</Feed>')
except Exception as e:
    logging.error("Error while writing output: {}".format(str(e)))