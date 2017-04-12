"""Harvest Subset of DPLA Metadata from the DPLA API - Requires Auth."""
from argparse import ArgumentParser
import os
import requests
import json
import time


def generateCallOpts(args):
    callOpts = ''
    if args.provider:
        callOpts += '&admin.contributingInstitution=%s&exact_field_match=true' % args.provider
    if args.hub:
        callOpts += '&provider.name=%s&exact_field_match=true' % args.hub
    if args.afterDate:
        callOpts += '&sourceResource.date.after=%s' % args.afterDate
    if args.beforeDate:
        callOpts += '&sourceResource.date.before=%s' % args.beforeDate
    if args.title:
        callOpts += '&sourceResource.title=%s' % args.title
    if args.keyword:
        callOpts += '&q=%s' % args.keyword
    return(callOpts)


def dataAPIcall(dplaAPI, verbOpts, page_num):
    page_params = {'page_size': 500, 'page': page_num}
    data = requests.get(dplaAPI + verbOpts, params=page_params)
    req_url = data.url
    print("Using url:%s" % req_url)

    try:
        if data.status_code != 200 and data.status_code != 301:
            data.raise_for_status()
        elif data.status_code == 301:
            print("%s redirected to %s ." % dplaAPI + verbOpts, req_url)
            return(dataAPIcall(data.url, verbOpts, page_num))
        else:
            data.encoding = 'utf-8'
    except requests.HTTPError as exValue:
        status_code = exValue.response.status_code
        if status_code == 503:
            retryWait = int(data.headers.get("Retry-After", "-1"))
            if retryWait < 0:
                print("DPLA API Service %s Unavailable (Status 503)." % req_url)
                exit()
            else:
                print('Waiting %d seconds' % retryWait)
                time.sleep(retryWait)
                return(dataAPIcall(dplaAPI, verbOpts, page_num))
        elif status_code == 404:
            print("404 Not Found Error with API CALL: %s" % req_url)
            exit()
        else:
            print(exValue)
            exit()
    return(data)


def iterateRecordPull(data, dplaAPI, callOpts):
    recordlist = []
    recordCount = 0
    dplaRecordCount = data.json()['count']
    dplaPageCount = (dplaRecordCount / 500) + 1

    for p in range(1, int(dplaPageCount) + 1):
        for n in range(0, 500):
            try:
                DPLAobject = data.json()['docs'][n]
                recordlist.append(DPLAobject)
                n += 1
                recordCount += 1
            except IndexError:
                break
        p += 1
        data = dataAPIcall(dplaAPI, callOpts, str(p))
        print("Retrieving page %d of %d" % (p, dplaPageCount))
    output = {}
    output['recordCount'] = recordCount
    output['recordlist'] = recordlist
    return(output)


def main():
    parser = ArgumentParser()
    parser.add_argument("-o", "--filename", dest="filename",
                        help="write repository to file",
                        default="DPLAharvest.json")
    parser.add_argument("-k", "--apikey", dest="apikey",
                        help="your unique DPLA API key")
    parser.add_argument("-a", "--after", dest="afterDate",
                        help="items with creation date after yyyy-mm-dd")
    parser.add_argument("-f", "--before", dest="beforeDate",
                        help="items with creation date before yyyy-mm-dd")
    parser.add_argument("-t", "--title", dest="title",
                        help="search the item title")
    parser.add_argument("-q", "--keyword", dest="keyword",
                        help="keyword search")
    parser.add_argument("-p", "--provider", dest="provider",
                        help="specify a metadata provider / local institution")
    parser.add_argument("-u", "--hub", dest="hub",
                        help="specify a service or content hub")
    args = parser.parse_args()

    dplaAPI = 'https://api.dp.la/v2/items'

    # Check DPLA API Key as Argument or Environmental Variable
    try:
        if args.apikey:
            dplaAPI = dplaAPI + '?api_key=' + args.apikey
        else:
            apikey = os.environ['DPLA_APIKEY']
            dplaAPI = dplaAPI + '?api_key=' + apikey
    except NameError:
        parser.print_help()
        parser.error("a DPLA API key is required. \
                     \nProvide as an env variable DPLA_APIKEY or as flag -k. \
                     \nGet a DPLA API key here: \
                     \nhttp://dp.la/info/developers/codex/policies/#get-a-key")

    print("Writing records to %s from DPLA: %s" % (args.filename, dplaAPI))

    # Generate API Options and Cancel full DPLA Data Dump requests
    callOpts = generateCallOpts(args)
    if callOpts == '':
        print("Stop it. You don't really need the full DPLA metadata set. \
        \nSpecify a query parameter.")
        parser.print_help()
        exit()

    # Call API for first 500 Records
    data = dataAPIcall(dplaAPI, callOpts, '1')

    # Iterate over Rest of Records & Create Dict for Writing to Json
    dataDict = {}
    output = iterateRecordPull(data, dplaAPI, callOpts)
    recordCount = output['recordCount']
    dataDict['docs'] = output['recordlist']

    # Write Out JSON Data Harvest
    ofile = open(args.filename, 'w')
    json.dump(dataDict, ofile)
    ofile.close()

    print("Wrote out %d records" % recordCount)


if __name__ == '__main__':
    main()
