import sys
from lxml import objectify

# HOW TO RUN
# python3 getBadgeNames.py filename

# GET THE FILE
the_file = sys.argv[1] if sys.argv[1] else None
tree = objectify.parse(open(the_file))
root = tree.getroot()
ns = '{' + root.nsmap[None] + '}'

bName = []
for badges in root.findall('.//' + ns + 'Badges'):
    badge = badges.find('.//' + ns + 'Name')
    bType = badges.find('.//' + ns + 'BadgeType')
    bName.append(bType + ": " + badge)

print(set(bName))
