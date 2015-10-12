import codecs
from argparse import ArgumentParser
import os
import requests
import json

if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument("-o", "--filename", dest="filename", \
                        help="write repository to file", default="DPLAoutput.json")
    parser.add_argument("-k", "--apikey", dest="apikey", \
                        help="your unique DPLA API key")
    parser.add_argument("-a", "--after", dest="afterDate", \
                        help="items with creation date after yyyy-mm-dd")
    parser.add_argument("-f", "--before", dest="beforeDate", \
                        help="items with creation date before yyyy-mm-dd")
    parser.add_argument("-t", "--title", dest="title", \
                        help="search the item title")
    parser.add_argument("-q", "--keyword", dest="keyword", \
                        help="keywork search")
    parser.add_argument("-p", "--provider", dest="provider", \
                        help="specify the metadata provider")

    args = parser.parse_args()

    dplaAPI = 'http://api.dp.la/v2/items'
    try:
        if args.apikey:
            dplaAPI = dplaAPI + '?api_key=' + args.apikey
        elif apikey:
            apikey = os.environ['DPLA_APIKEY']
            dplaAPI = dplaAPI + '?api_key=' + apikey
    except NameError:
        parser.print_help()
        parser.error("a DPLA API key is required. \
                     \nProvide as an environmental variable DPLA_APIKEY or as flag -k. \
                     \nGet a DPLA API key here: \
                     \nhttp://dp.la/info/developers/codex/policies/#get-a-key")

    print "Writing records to %s from DPLA: %s" % (args.filename, dplaAPI)

    verbOpts = ''
    if args.provider:
        verbOpts += '&dataProvider=%s' % args.provider
    if args.afterDate:
        verbOpts += '&sourceResource.date.after=%s' % args.afterDate
    if args.beforeDate:
        verbOpts += '&sourceResource.date.before=%s' % args.beforeDate
    if args.title:
        verbOpts += '&sourceResource.title=%s' % args.title
    if args.keyword:
        verbOpts += '&q=%s' % args.keyword

    if verbOpts == '':
        print "Stop it. You don't need really need the full DPLA metadata set. \
        \nSpecify a query parameter."
        parser.print_help()
    else:
        print "Using url:%s" % dplaAPI + verbOpts

        recordlist = []

        page = '&page_size=500&page='
        data = requests.get(dplaAPI + verbOpts + page + '1')
        data.encoding ='utf-8'

        recordCount = 0
        dplaRecordCount = data.json()['count']
        dplaPageCount = ( dplaRecordCount / 500 ) + 1

        for p in range(1, dplaPageCount + 1):
            if p==1:
                print "Retrieving page %d of %d" % (p, dplaPageCount)
            for n in range(0, 500):
                try:
                    DPLAobject = data.json()['docs'][n]
                    recordlist.append(DPLAobject)
                    n += 1
                    recordCount += 1
                except IndexError:
                    break
            p += 1
            data = requests.get(dplaAPI + verbOpts + page + str(p))
            print "Retrieving page %d of %d" % (p, dplaPageCount)

        dataDict = {}
        dataDict['docs'] = recordList

        ofile = open(args.filename, 'w')
        json.dump(dataDict, ofile)
        ofile.close()

        print "Wrote out %d records" % recordCount


