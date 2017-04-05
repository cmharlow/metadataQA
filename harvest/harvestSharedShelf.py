"""Harvest metadata mapped to field labels from SharedShelf API."""
from argparse import ArgumentParser
import os
import requests
import json
import re
import csv
import errno

base_url = 'http://catalog.sharedshelf.artstor.org/'
url_rest = '/assets?with_meta=true&limit=5000000'
publ_re = re.compile("^publishing_status[.-]\d+")


def getCookies(args, parser):
    """Get cookies from authentication of SharedShelf API."""
    try:
        if args.email and args.password:
            data = {'email': args.email, 'password': args.password}
            cookies = requests.post(base_url + 'account', data=data).cookies
        elif not args.email or not args.password:
            email = os.environ['ArtStor email:']
            password = os.environ['ArtStor password:']
            data = {'email': email, 'password': password}
            cookies = requests.post(base_url + 'account', data=data).cookies
        return(cookies)
    except Exception:
        parser.print_help()
        parser.error("need a valid ArtStor user email and password.")


def getCollections(cookies, proj_id):
    """Get + return data for all collections in SharedShelf."""
    projs_start = requests.get(base_url + 'projects', cookies=cookies)
    projs_start.encoding = 'utf8'
    projs = projs_start.json()
    colls = {}
    if proj_id:
        coll_name = None
        for proj in projs['items']:
            if proj['id'] == int(proj_id):
                coll_id = proj_id
                coll_name = proj['name']
                colls[coll_id] = coll_name
        if not coll_name:
            print("We couldn't find a collection for that ID. Here's a list: ")
            print("==========================================================")
            for proj in projs['items']:
                print('Collection: %s || ID: %d' % (proj['name'], proj['id']))
            exit()
    else:
        for proj in projs['items']:
            coll_id = proj['id']
            coll_name = proj['name']
            colls[coll_id] = coll_name
    return(colls)


def generateDataDump(cookies, colls, filename):
    total = 0
    output = {}
    for coll_id in colls:
        print("Retrieving project %s" % colls[coll_id])

        # Grab assets data for each unique SharedShelf Collection
        url = base_url + 'projects/' + str(coll_id) + url_rest
        data_start = requests.get(url, cookies=cookies)
        data_start.encoding = 'utf8'
        data = data_start.json()

        # Grab SharedShelf metadata fields for mapping values to text fields.
        fields_ss = data['metaData']['columns']
        assets = data['assets']
        fields = {}
        for n in range(len(fields_ss)):
            if publ_re.match(fields_ss[n]['dataIndex']) and 'publishing_status' not in fields:
                fields['publishing_status'] = ('publishing_status')
            else:
                fields[(fields_ss[n]['dataIndex'])] = (fields_ss[n]['header'])
        for n in range(len(assets)):
            for field in assets[n]:
                if field not in fields and field.replace('_multi_s', '_mfcl_lookup') in fields:
                    fields[field] = fields[field.replace('_multi_s', '_mfcl_lookup')] + "_facet"
                elif field not in fields:
                    fields[field] = field

        # Grab SharedShelf metadata field values and store in output.
        for n in range(len(assets)):
            record_id = assets[n]['id']
            output[record_id] = {}
            total += 1
            for field in assets[n]:
                if field in fields:
                    field_label = fields[field]
                    output[record_id][field_label] = assets[n][field]
                else:
                    output[record_id][field] = assets[n][field]
                    print("MISSING FIELD: " + field + ": " + data['assets'][n][field])

    if not os.path.exists(os.path.dirname(filename)) and os.path.dirname(filename):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, 'w') as ofile:
        json.dump(output, ofile)
    print("Wrote out %d records" % total)


def generateMetadataDump(cookies, colls, filename):
    output = {}
    for coll_id in colls:
        print("Retrieving metadata mapping from project %s" % colls[coll_id])

        # Grab assets data for each unique SharedShelf Collection
        url = base_url + 'projects/' + str(coll_id) + url_rest
        data_start = requests.get(url, cookies=cookies)
        data_start.encoding = 'utf8'
        data = data_start.json()

        # Grab SharedShelf metadata fields for mapping values to text fields.
        fields_ss = data['metaData']['columns']
        for n in range(len(fields_ss)):
            field_code = fields_ss[n]['dataIndex']
            field_label = fields_ss[n]['header']
            if field_label not in output and field_label:
                output[field_label] = [field_code]
            elif not field_label:
                output["No label for: " + field_code] = [field_code]
            else:
                if field_code not in output[field_label]:
                    output[field_label].append(field_code)

    if not os.path.exists(os.path.dirname(filename)) and os.path.dirname(filename):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    with open(filename, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Field Label', 'Field codes from various collections that map to that Label'])
        for key, value in output.items():
            row = [key]
            codes = None
            for subval in value:
                if codes:
                    codes += subval + " | "
                else:
                    codes = subval
            row.append(codes)
            writer.writerow(row)


def main():
    parser = ArgumentParser()

    parser.add_argument("-o", "--filename", dest="filename",
                        help="write to file", default="data/output.json")
    parser.add_argument("-e", "--email", dest="email",
                        help="Your SharedShelf User email. Required.")
    parser.add_argument("-p", "--password", dest="password",
                        help="Your SharedShelf User password. Required.")
    parser.add_argument("-c", "--collection", dest="coll",
                        help="A SharedShelf Collection ID if you only want to \
                              harvest a single SharedShelf Collection. \
                              Optional.")
    parser.add_argument("-m", "--metadata", dest="metadata", default=False,
                        action="store_true", help="Return collated metadata \
                        label to SharedShelf API field codes dictionaries.")
    args = parser.parse_args()
    # Authenticating the User on the SharedShelf API.
    cookies = getCookies(args, parser)

    # Get All Projects/Collections in SharedShelf First.
    print("Writing metadata to data/metadata_fields.csv from SharedShelf.")
    if args.metadata:
        colls = getCollections(cookies, None)
        generateMetadataDump(cookies, colls, "metadata_fields.csv")
    else:
        if args.coll:
            spec_id = args.coll
        else:
            spec_id = None
        colls = getCollections(cookies, spec_id)
        generateDataDump(cookies, colls, args.filename)


if __name__ == "__main__":
    main()
