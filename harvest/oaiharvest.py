"""Harvest Metadata from an OAI-PMH Feed."""
import urllib2
import requests
import zlib
import time
import re
import xml.dom.pulldom
import xml.dom.minidom
import codecs
from argparse import ArgumentParser

nDataBytes, nRawBytes = 0, 0


def getFile(link, command, sleepTime=0):
    """This generates the OAI-PMH link and retrieves the XML data over HTTP."""
    global nDataBytes, nRawBytes
    time.sleep(sleepTime)

    # Set URL with OAI-PMH Command for Retrieval
    remoteAddr = link + '?verb=%s' % command
    print("\t getFile ... %s" % remoteAddr[-90:])

    # Handle HTTP Response (Including Common Errors) from OAI-PMH Endpoint
    try:
        response = requests.get(remoteAddr)
        if response.status_code != 200:
            response.raise_for_status()
        else:
            remoteData = response.text
    except requests.HTTPError as exValue:
        status_code = exValue.response.status_code
        if status_code == 503:
            retryWait = int(response.headers.get("Retry-After", "-1"))
            if retryWait < 0:
                print("OAI-PMH Service %s Unavailable (Status 503)." % link)
                exit()
            else:
                print('Waiting %d seconds' % retryWait)
                return(getFile(link, command, retryWait))
        elif status_code == 404:
            print("404 Not Found Error with OAI-PMH URL: %s" % remoteAddr)
            exit()
        else:
            print(exValue)
            exit()

    # Count Bytes for Output Report, Compress Where Able for Efficiency.
    nRawBytes += len(remoteData)
    try:
        remoteData = zlib.decompressobj().decompress(remoteData)
    except:
        pass
    nDataBytes += len(remoteData)

    # Check for Any OAI-PMH Errors in the XML Response, Otherwise, Return XML
    oaiErr = re.search('<error *code=\"([^"]*)">(.*)</error>', remoteData)
    if oaiErr:
        print("OAIERROR: code=%s '%s'" % (oaiErr.group(1), oaiErr.group(2)))
        exit()
    else:
        return(remoteData)


def handleEncodingErrors(inputFile):
    # Handle OAI-PMH XML Encoding Errors
    # from http://boodebr.org/main/python/all-about-python-and-unicode#UNI_XML
    RE_XML_IL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                u'|' + \
                u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' %\
                (unichr(0xd800), unichr(0xdbff), unichr(0xdc00),
                 unichr(0xdfff), unichr(0xd800), unichr(0xdbff),
                 unichr(0xdc00), unichr(0xdfff), unichr(0xd800),
                 unichr(0xdbff), unichr(0xdc00), unichr(0xdfff))
    outputFile = re.sub(RE_XML_IL, "?", inputFile)
    return(outputFile)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-l", "--link", dest="link", help="OAI-PMH URL",
                        default="https://ecommons.cornell.edu/dspace-oai/request")
    parser.add_argument("-o", "--filename", dest="fname",
                        help="write repository to file", default="harvest.xml")
    parser.add_argument("-f", "--from", dest="fromDate",
                        help="harvest records from this date YYYY-MM-DD")
    parser.add_argument("-u", "--until", dest="until",
                        help="harvest records until this date YYYY-MM-DD")
    parser.add_argument("-m", "--mdprefix", dest="mdprefix", default="oai_dc",
                        help="use the specified metadata format")
    parser.add_argument("-s", "--setName", dest="setName",
                        help="harvest the specified OAI-PMH set")
    args = parser.parse_args()

    # Check OAI-PMH URL is valid
    if not args.link.startswith('http'):
        args.link = 'http://' + args.link

    # Start Harvest Process
    print("Writing records to %s from repository %s" % (args.fname, args.link))

    # Generate the OAI-PMH URL with Provided Arguments
    verbOpts = ''
    if args.setName:
        verbOpts += '&set=%s' % args.setName
    if args.fromDate:
        verbOpts += '&from=%s' % args.fromDate
    if args.until:
        verbOpts += '&until=%s' % args.until
    if args.mdprefix:
        verbOpts += '&metadataPrefix=%s' % args.mdprefix

    print("Using url:%s" % args.link + '?verb=ListRecords' + verbOpts)

    ofile = codecs.lookup('utf-8')[-1](file(args.filename, 'wb'))
    ofile.write('<?xml version="1.0" encoding="UTF-8"?><OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"> <responseDate>2015-10-11T00:35:52Z</responseDate> <ListRecords>\n')

    # Grab & Clean XML Records from OAI Feed
    data = getFile(args.link, 'ListRecords' + verbOpts)
    dataClean = handleEncodingErrors(data)

    # Iterate over Records, ResumptionTokens, & Write to File
    recordCount = 0
    while dataClean:
        events = xml.dom.pulldom.parseString(dataClean.encode('utf8'))
        for (event, node) in events:
            if event == "START_ELEMENT" and node.tagName == 'record':
                events.expandNode(node)
                node.writexml(ofile)
                recordCount += 1
        more = re.search('<resumptionToken[^>]*>(.*)</resumptionToken>',
                         dataClean)
        if not more:
            break
        else:
            data = getFile(args.link, "ListRecords&resumptionToken=%s" % more.group(1))
            dataClean = handleEncodingErrors(data)

    ofile.write('\n</ListRecords></OAI-PMH>\n'), ofile.close()
    print("\nRead %d bytes (%.2f compression)" % (nDataBytes, float(nDataBytes) / nRawBytes))
    print("Wrote out %d records" % recordCount)
