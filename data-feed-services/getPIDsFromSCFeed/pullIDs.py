from __future__ import print_function
from lxml import objectify
import sys

# HOW TO RUN
# python3 pullIDs.py filename

# Load the Feed
the_file = sys.argv[1] if sys.argv[1] else None

# Load the Feed
xmldata = objectify.parse(open(the_file))
data = xmldata.getroot()
ns = data.nsmap[None]

# INTERATES BY Product ID
for product in data.xpath('t:Product', namespaces={'t': ns}):
        print(product.ExternalId.text)

print('DONE')
