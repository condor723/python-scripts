import sys
from lxml import etree, objectify
from datetime import datetime

# Example command
# python3 dateParser.py xml_file.xml 2019-11-05

# Load the Feed
the_file = sys.argv[1] if sys.argv[1] else None
the_date = sys.argv[2] if sys.argv[2] else None
new_file = the_file.replace(".xml", '-new.xml')


file = open(the_file)
tree = objectify.parse(file)
root = tree.getroot()
ns = '{' + root.nsmap[None] + '}'

for review in root.findall('.//' + ns + 'Review'):
    sub_time = review.find('.//' + ns + 'SubmissionTime')
    sub_time_xml = sub_time.text
    if sub_time_xml[-1] == "Z":
            submission_string = sub_time_xml[:-1].replace("T", " ")
    elif len(sub_time_xml) > 24:
        submission_string = sub_time_xml[:-6].replace("T", " ")
    else:
        submission_string = sub_time_xml.replace("T", " ")

    dt_object = datetime.strptime((submission_string), '%Y-%m-%d %H:%M:%S.%f')
    if the_date is not None:
        if dt_object < datetime.strptime(the_date + " 00:00:00.000", '%Y-%m-%d %H:%M:%S.%f'):
            # need to remove stuff here
            product = review.getparent()
            product.remove(review)
            print("Ditching Review ID: " + review.attrib['id'] + ": " + str(dt_object))
    else:
        print('Please provide a date.')

for question in root.findall('.//' + ns + 'Question'):
    sub_time = question.find('.//' + ns + 'SubmissionTime')
    sub_time_xml = sub_time.text
    if sub_time_xml[-1] == "Z":
            submission_string = sub_time_xml[:-1].replace("T", " ")
    elif len(sub_time_xml) > 24:
        submission_string = sub_time_xml[:-6].replace("T", " ")
    else:
        submission_string = sub_time_xml.replace("T", " ")

    dt_object = datetime.strptime((submission_string), '%Y-%m-%d %H:%M:%S.%f')
    if the_date is not None:
        if dt_object < datetime.strptime(the_date + " 00:00:00.000", '%Y-%m-%d %H:%M:%S.%f'):
            # need to remove stuff here
            product = question.getparent()
            product.remove(question)
            print("Ditching Question ID: " + question.attrib['id'] + ": " + str(dt_object))
    else:
        print('Please provide a date.')

objectify.deannotate(tree, cleanup_namespaces=True)
newxml = etree.tostring(tree, pretty_print=True)
f = open(new_file, 'w')
print('writing stuff')
f.write('<?xml version="1.0" encoding="UTF-8"?>\r\n')
f.close()
f = open(new_file, 'ab')
f.write(newxml)
f.close()

print("Done")
