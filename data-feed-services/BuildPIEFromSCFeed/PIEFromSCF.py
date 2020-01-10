from lxml import objectify, etree as ET
from pathlib import Path
import datetime
import sys
import logging

# HOW TO RUN
# python3 PIEFromSCF.py filename

# LOGGING
logging.basicConfig(filename='logfile', level=logging.DEBUG)
date = datetime.datetime.now()
logging.info("Starting python script at {}".format(date))


def main():

    # Load the Feed
    the_file = sys.argv[1] if sys.argv[1] else None

    tf = Path(the_file)
    if tf.is_file():
        try:
            with open(the_file) as f:

                xmldata = objectify.parse(f)
                data = xmldata.getroot()
                ns = data.nsmap[None]

                # Create the PIE Feed
                pieNS = 'http://www.bazaarvoice.com/xs/PRR/PostPurchaseFeed/5.6'
                x_feed = objectify.Element("Feed", xmlns=pieNS)

                # Log Stuff Here
                log_data = []
                valid_int = 0
                invalid_int = 0
                total_int = 0
                optedOut_count = 0

                # Get the Current Date
                currentDT = datetime.datetime.now()
                dt_formatted = currentDT.strftime("%Y_%m_%S")

                # Find CDV For OptedIn Users in SCFeed & Build the PIE XML
                for cdv in data.xpath("//t:ContextDataDimension", namespaces={'t': ns}):
                    if cdv.get('id') == 'AgreedToTermsAndConditionsAPO':
                        if cdv.getparent().get('id') == 'true':
                            # Get to the Review Level
                            review = cdv.getparent().getparent().getparent()
                            rID = review.attrib['id']
                            subTime = review.SubmissionTime.text
                            userID = review.UserProfileReference.attrib['id']
                            rNickname = review.find('{' + ns + '}ReviewerNickname')
                            if rNickname is None:
                                rNickname = ''
                            locale = review.DisplayLocale.text
                            # Get to the Product Level
                            product = review.getparent().getparent()
                            pID = product.attrib['id']
                            pName = product.find('{' + ns + '}Name')
                            if pName is None:
                                pName = ''
                            pImg = product.find('{' + ns + '}ImageUrl')
                            if pImg is None:
                                pImg = ''
                            total_int = total_int + 1
                            # Build the interaction elements
                            email = review.find('{' + ns + '}UserEmailAddress')
                            if email is None:
                                # Log Review Missing Email Address
                                log_data.append("ProductId: {}, ReviewId: {} , ReviewerId: {} - Missing Email Address"
                                                .format(pID, rID, userID))
                                invalid_int = invalid_int + 1
                            else:
                                interaction = objectify.Element('Interaction')
                                interaction.append(objectify.Element('TransactionDate'))
                                interaction.TransactionDate[-1] = subTime
                                interaction.append(objectify.Element('EmailAddress'))
                                interaction.EmailAddress[-1] = email
                                interaction.append(objectify.Element('UserName'))
                                interaction.UserName[-1] = rNickname
                                interaction.append(objectify.Element('UserID'))
                                interaction.UserID[-1] = userID
                                interaction.append(objectify.Element('Locale'))
                                interaction.Locale[-1] = locale
                                # Build the Products element
                                x_products = objectify.Element('Products')
                                x_product = objectify.Element('Product')
                                x_product.append(objectify.Element('ExternalId'))
                                x_product.ExternalId[-1] = pID
                                x_product.append(objectify.Element('Name'))
                                x_product.Name[-1] = pName
                                x_product.append(objectify.Element('ImageUrl'))
                                x_product.ImageUrl[-1] = pImg
                                # Put it all together
                                x_products.append(x_product)
                                interaction.append(x_products)
                                x_feed.append(interaction)
                                valid_int = valid_int + 1
                        else:
                            # Count "AgreedToTermsAndConditionsAPO = False" & Log
                            optedOut_count = optedOut_count + 1

                # Log the Counts
                log_data.append('\nTotal OptedIn: ' + str(total_int))
                log_data.append('Valid OptedIn: ' + str(valid_int))
                log_data.append('Invalid OptedIn: ' + str(invalid_int))
                log_data.append('\nTotal OptedOut: ' + str(optedOut_count))
                # log_file = client_name + dt_formatted + ".log"
                log_file = 'logfile'
                log = open(log_file, 'w')
                log.write("\n".join(log_data))

                # Create the PIE XML Feed
                if valid_int > 0:
                    objectify.deannotate(x_feed, cleanup_namespaces=True)
                    newxml = ET.tostring(x_feed, pretty_print=True)
                    # out_file = client_name + "_PIE_" + dt_formatted + ".xml"
                    out_file = 'outputfile'
                    new_file = open(out_file, 'w')
                    new_file.write('<?xml version="1.0" encoding="UTF-8"?>\r\n')
                    new_file.close()
                    new_file = open(out_file, 'ab')
                    new_file.write(newxml)
                    new_file.close()

        except IOError as x:
            print(x)

    else:
        logging.error("File Does Not Exist: {}".format(str(tf)))
        print("File Does Not Exist: {}".format(str(tf)))

    dateF = datetime.datetime.now()
    logging.info("Ending python script at {}".format(dateF))


if __name__ == "__main__":
    main()
