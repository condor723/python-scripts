from lxml import objectify, etree as ET
import sys

# HOW TO RUN
# python3 scf_by_id.py filename

# Load the Feed
the_file = sys.argv[1] if sys.argv[1] else None
new_file = the_file.replace(".xml", '-new.xml')

f = open(the_file)
xmldata = objectify.parse(f)
data = xmldata.getroot()
ns = data.nsmap[None]

# comma delimited strings that you want to keep #
id_list = ['sampling298569', 'sampling968483', 'sampling629026',
           'sampling565406', 'sampling038848']

# INTERATES BY Product ID
for product in data.xpath('t:Product', namespaces={'t': ns}):
    if product.get('id') not in id_list:
        data.remove(product)
    else:
        print(product.get('id'))


objectify.deannotate(data, cleanup_namespaces=True)
newxml = ET.tostring(data, pretty_print=True)
f = open(new_file, 'w')
print('writing stuff')
f.write('<?xml version="1.0" encoding="UTF-8"?>\r\n')
f.close()
f = open(new_file, 'ab')
f.write(newxml)
f.close()
