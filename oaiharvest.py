import urllib2
import zlib
import time
import re
import xml.dom.pulldom
import operator
import codecs
from argparse import ArgumentParser

nDataBytes, nRawBytes, nRecoveries, maxRecoveries = 0, 0, 0, 3

def getFile(link, command, verbose=1, sleepTime=0):
    global nRecoveries, nDataBytes, nRawBytes
    if sleepTime:
        time.sleep(sleepTime)
    remoteAddr = link + '?verb=%s' % command
    if verbose:
        print "\r", "getFile ...'%s'" % remoteAddr[-90:]
    headers = {'User-Agent': 'OAIHarvester/2.0', 'Accept': 'text/html',
               'Accept-Encoding': 'compress, deflate'}
    try:
        remoteData = urllib2.urlopen(remoteAddr).read()
    except urllib2.HTTPError, exValue:
        if exValue.code == 503:
            retryWait = int(exValue.hdrs.get("Retry-After", "-1"))
            if retryWait < 0:
                return None
            print 'Waiting %d seconds' % retryWait
            return getFile(link, command, 0, retryWait)
        print exValue
        if nRecoveries < maxRecoveries:
            nRecoveries += 1
            return getFile(link, command, 1, 60)
        return
    nRawBytes += len(remoteData)
    try:
        remoteData = zlib.decompressobj().decompress(remoteData)
    except:
        pass
    nDataBytes += len(remoteData)
    mo = re.search('<error *code=\"([^"]*)">(.*)</error>', remoteData)
    if mo:
        print "OAIERROR: code=%s '%s'" % (mo.group(1), mo.group(2))
    else:
        return remoteData

if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument("-l", "--link", dest="link",
                        help="URL of repository",
                        default="http://digital.lib.utk.edu/collections/oai2")
    parser.add_argument("-o", "--filename", dest="filename",
                        help="write repository to file", default="output.xml")
    parser.add_argument("-f", "--from", dest="fromDate",
                        help="harvest records from this date yyyy-mm-dd")
    parser.add_argument("-u", "--until", dest="until",
                        help="harvest records until this date yyyy-mm-dd")
    parser.add_argument("-m", "--mdprefix", dest="mdprefix",
                        default="oai_dc", help="use the specified metadata format")
    parser.add_argument("-s", "--setName", dest="setName",
                        help="harvest the specified set")

    args = parser.parse_args()

    if not args.link.startswith('http'):
        args.link = 'http://' + args.link

    print "Writing records to %s from repository %s" % (args.filename, args.link)

    verbOpts = ''
    if args.setName:
        verbOpts += '&set=%s' % args.setName
    if args.fromDate:
        verbOpts += '&from=%s' % args.fromDate
    if args.until:
        verbOpts += '&until=%s' % args.until
    if args.mdprefix:
        verbOpts += '&metadataPrefix=%s' % args.mdprefix

    print "Using url:%s" % args.link + '?ListRecords' + verbOpts

    ofile = codecs.lookup('utf-8')[-1](file(args.filename, 'wb'))

    ofile.write('<?xml version="1.0" encoding="UTF-8"?> \
        <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" \
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ \
        http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd"> \
        <responseDate>2015-10-11T00:35:52Z</responseDate> \
        <request>' + urllib2.urlencode(args.link) + '?ListRecords' + verbOpts + \
        '</request><ListRecords>\n')  # wrap list of records with this

    data = getFile(args.link, 'ListRecords' + verbOpts)

    recordCount = 0

    while data:
        events = xml.dom.pulldom.parseString(data)
        for (event, node) in events:
            if event == "START_ELEMENT" and node.tagName == 'record':
                events.expandNode(node)
                node.writexml(ofile)
                recordCount += 1
        more = re.search('<resumptionToken[^>]*>(.*)</resumptionToken>', data)
        if not more:
            break
        data = getFile(args.link, "ListRecords&resumptionToken=%s" % more.group(1))

    ofile.write('\n</ListRecords></OAI-PMH>\n'), ofile.close()

    print "\nRead %d bytes (%.2f compression)" % (nDataBytes, float(nDataBytes) / nRawBytes)

    print "Wrote out %d records" % recordCount
