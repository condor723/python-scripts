import csv
import sys
from lxml import objectify, etree as ET

"""
Example command

python3 remove_reviewids.py csv_file.csv scf_file.xml
"""

target_review_ids = ''
target_scf = ''


def get_review_ids():
    header_row = True
    global target_scf
    try:
        id_file = sys.argv[1]
        target_scf = sys.argv[2]
    except Exception as e:
        print(
            "Did you specify both the Review ID and Standard Client feed file?"
        )
        return

    with open(id_file, 'r') as f:
        reader = csv.reader(f)
        your_list = list(reader)
        if header_row == True:
            your_list.pop(0)
        flat_list = [item for sublist in your_list for item in sublist]
        """
        the above flat list conversion translates to
        for sublist in your_list:
            for item in sublist:
                flat_list.append(item)
        """
    return flat_list


target_review_ids = get_review_ids()


def transform_scf():
    global target_scf
    try:
        file = open(target_scf)
        tree = objectify.parse(file)
        root = tree.getroot()
        print(root)
        namespace = '{' + root.nsmap[None] + '}'
        for product in root.findall('./' + namespace + 'Product'):
            for reviews in product.findall('./' + namespace + 'Reviews'):
                for review in reviews.findall('./' + namespace + 'Review'):
                    scf_review_id = review.get('id')
                    if scf_review_id not in target_review_ids:
                        review.getparent().remove(review)
    except Exception as e:
        print('Could not parse the provided XML file properly: ', e)

    try:
        objectify.deannotate(tree, cleanup_namespaces=True)
        newxml = ET.tostring(tree, pretty_print=True)
        f = open("edited_SCF.xml", 'w')
        print("writing to XML")
        f.write('<?xml version="1.0" encoding="UTF-8"?>\r\n')
        f.close()
        f = open("edited_SCF.xml", 'ab')
        f.write(newxml)
        f.close()
    except Exception as e:
        print('Could not write to edited XML file: ', e)


transform_scf()
# print(target_review_ids)