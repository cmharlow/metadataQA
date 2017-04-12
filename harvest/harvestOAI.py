"""Harvest Metadata from an OAI-PMH Feed."""
from __future__ import unicode_literals
import requests
import zlib
import time
import re
import xml.dom.pulldom
import xml.dom.minidom
import codecs
from argparse import ArgumentParser
from builtins import chr

nDataBytes = 0
nRawBytes = 0
oaistart = """<?xml version="1.0" encoding="UTF-8"?><OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"> <responseDate>2015-10-11T00:35:52Z</responseDate> <ListRecords>\n"""
oaiend = """\n</ListRecords></OAI-PMH>\n"""


def getFile(link, command, sleepTime=0):
    """This generates the OAI-PMH link and retrieves the XML data over HTTP."""
    time.sleep(sleepTime)

    # Set URL with OAI-PMH Command for Retrieval
    remoteAddr = link + '?verb=%s' % command
    print("\t getFile ... %s" % remoteAddr[-90:])

    # Handle HTTP Response (Including Common Errors) from OAI-PMH Endpoint
    try:
        resp = requests.get(remoteAddr)
        if resp.status_code != 200 and resp.status_code != 301:
            resp.raise_for_status()
        elif resp.status_code == 301:
            print("%s redirected to %s ." % remoteAddr, resp.url)
            return(getFile(resp.url, command))
        elif '/xml' not in resp.headers.get('content-type'):
            print("ERROR: content-type=%s" % (resp.headers.get('content-type')))
            exit()
        else:
            remoteData = resp.text
    except requests.HTTPError as exValue:
        status_code = exValue.response.status_code
        if status_code == 503:
            retryWait = int(resp.headers.get("Retry-After", "-1"))
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
    return(remoteData.encode('utf8'))


def zipRemoteData(remoteData):
    # Count Bytes for Output Report, Compress Where Able for Efficiency.
    global nRawBytes, nDataBytes
    nRawBytes += len(remoteData)
    try:
        remoteData = zlib.decompressobj().decompress(remoteData)
    except:
        pass
    nDataBytes += len(remoteData)
    return(remoteData)


def checkOAIErrors(remoteData):
    # Check for OAI-PMH Errors in the XML Response
    oaiErr = re.search(b'<error *code=\"([^"]*)">(.*)</error>', remoteData)
    if oaiErr:
        print("OAIERROR: code=%s '%s'" % (oaiErr.group(1), oaiErr.group(2)))
        exit()
    else:
        return(remoteData)


def generateOAIopts(args, verbOpts=''):
    if args.setName:
        verbOpts += '&set=%s' % args.setName
    if args.fromDate:
        verbOpts += '&from=%s' % args.fromDate
    if args.until:
        verbOpts += '&until=%s' % args.until
    if args.mdprefix:
        verbOpts += '&metadataPrefix=%s' % args.mdprefix
    return(verbOpts)


def handleEncodingErrors(inputFile):
    # Handle OAI-PMH XML Encoding Errors
    # from http://boodebr.org/main/python/all-about-python-and-unicode#UNI_XML
    RE_XML_IL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                u'|' + \
                u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' %\
                (chr(0xd800), chr(0xdbff), chr(0xdc00),
                 chr(0xdfff), chr(0xd800), chr(0xdbff),
                 chr(0xdc00), chr(0xdfff), chr(0xd800),
                 chr(0xdbff), chr(0xdc00), chr(0xdfff))
    outputFile = re.sub(RE_XML_IL, u"?", inputFile.decode('utf-8'))
    return(outputFile)


def writeHarvest(link, data, ofile):
    recordCount = 0
    while data:
        # I need a better way to handle python 2/3 interop here, but not finding it.
        try:
            events = xml.dom.pulldom.parseString(data.encode('utf-8'))
            for (event, node) in events:
                if event == "START_ELEMENT" and node.tagName == 'record':
                    events.expandNode(node)
                    node.writexml(ofile)
                    recordCount += 1
        except TypeError as e:
            events = xml.dom.pulldom.parseString(data)
            for (event, node) in events:
                if event == "START_ELEMENT" and node.tagName == 'record':
                    events.expandNode(node)
                    node.writexml(ofile)
                    recordCount += 1
        more = re.search('<resumptionToken[^>]*>(.*)</resumptionToken>', data)
        if not more:
            break
        else:
            data = getFile(link, "ListRecords&resumptionToken=%s" % more.group(1))
            data = handleEncodingErrors(data)
    return(recordCount)


def main():
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
    verbOpts = generateOAIopts(args)
    print("Using url:%s" % args.link + '?verb=ListRecords' + verbOpts)

    # Create Start of XML Output File
    ofile = codecs.lookup('utf-8')[-1](open(args.fname, 'wb'))
    ofile.write(oaistart)

    # Grab & Clean XML Records from OAI Feed
    remoteData = getFile(args.link, 'ListRecords' + verbOpts)
    data = zipRemoteData(remoteData)
    data = checkOAIErrors(data)
    dataClean = handleEncodingErrors(data)

    # Iterate over Records, ResumptionTokens, & Write to File
    recordCount = writeHarvest(args.link, dataClean, ofile)

    # Finish Harvest Writer
    ofile.write(oaiend)
    ofile.close()

    # Print Simple Reports from Harvest
    print("\nRead %d bytes (%.2f compression)" % (nDataBytes, float(nDataBytes) / nRawBytes))
    print("Wrote out %d records" % recordCount)


if __name__ == "__main__":
    main()