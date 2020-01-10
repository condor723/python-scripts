from lxml import objectify, etree as ET
import sys

# HOW TO RUN
# python3 filter_pie.py filename

# Load the Feed
the_file = sys.argv[1] if sys.argv[1] else None
new_file = the_file.replace(".xml", '-new.xml')

f = open(the_file)
xmldata = objectify.parse(f)
data = xmldata.getroot()
ns = data.nsmap[None]

# comma delimited string of product IDs that you want to remove
id_list = ['7728399240', '1342791843928', '1342786797656', '1342791843928']

# iterates BY interaction
for products in data.xpath('//t:Products', namespaces={'t': ns}):
    pCount = len(products.Product)
    if pCount == 1:
        pid = products.Product.find('{' + ns + '}ExternalId')
        if pid is not None and str(pid) in id_list:
            data.remove(products.getparent())
            print('Interaction removed: ' + str(pid))
    else:
        for product in products.findall('{' + ns + '}Product'):
            pid = product.find('{' + ns + '}ExternalId')
            if pid is not None and str(pid) in id_list:
                products.remove(product)
                print ('Product removed: ' + str(pid))


objectify.deannotate(data, cleanup_namespaces=True)
newxml = ET.tostring(data, pretty_print=True)
f = open(new_file, 'w')
print('writing updated feed')
f.write('<?xml version="1.0" encoding="UTF-8"?>\r\n')
f.close()
f = open(new_file, 'ab')
f.write(newxml)
f.close()
