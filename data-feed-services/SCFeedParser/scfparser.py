from lxml import objectify, etree as ET
import sys

# Load the Feed
the_file = sys.argv[1] if sys.argv[1] else None

file = open(the_file)
tree = objectify.parse(file)
root = tree.getroot()
ns = '{' + root.nsmap[None] + '}'
count = 0
productCount = 0
brands = []
brand_list = ['Miracle-Gro', 'miraclegro', 'naturescare', 'Nature\'s Care', 'Ortho', 'ortho', 'Ortho Elementals', 'Roundup', 'roundup', 'Tomcat', 'tomcatbrand']

for product in root.findall('./' + ns + 'Product'):
    productCount = productCount + 1
    brand = product.find('./' + ns + 'Brand')
    bName = brand.Name if brand is not None else 'Not Found'
    if bName:
        brands.append(bName)
        if bName in brand_list:
            product.getparent().remove(product)
            count = count + 1

print('Total Products: ' + str(productCount))
print("Products removed count: " + str(count))
print(set(brands))

objectify.deannotate(tree, cleanup_namespaces=True)
newxml = ET.tostring(tree, pretty_print=True)
f = open('scotts_cleaned_prod_SCF.xml', 'w')
print('writing stuff')
f.write('<?xml version="1.0" encoding="UTF-8"?>\r\n')
f.close()
f = open('scotts_cleaned_prod_SCF.xml', 'ab')
f.write(newxml)
f.close()
