import hashlib
import sys
import pprint
from argparse import ArgumentParser
import json
import objectpath
import re


class RepoInvestigatorException(Exception):
    """This is our base exception for this script"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value,)


class Record:
    """Base class for a metadata record/object"""

    def __init__(self, elem, args):
        self.elem = elem
        self.args = args

    def get_record_id(self):
        try:
            record_id = self.elem['id']
            return record_id
        except:
            raise RepoInvestigatorException("Record does not have a valid Record Identifier")

    def get_elements(self):
        out = []
        try:
            record = objectpath.Tree(self.elem)
            response = record.execute(self.args.element)
            if response != None:
                if isinstance(response, list):
                    for item in response:
                        if isinstance(item, list):
                            for item2 in item:
                                if isinstance(item2, list):
                                    for item3 in item2:
                                        out.append((', '.join(item3)).encode("utf-8").strip())
                                elif isinstance(item2, dict):
                                    for key3, value3 in item2.iteritems():
                                        out.append((', '.join(value3)).encode("utf-8").strip())
                                else:
                                    out.append(item2.encode("utf-8").strip())
                        elif isinstance(item, dict):
                            for key, value in item.iteritems():
                                if isinstance(value, list):
                                    for item2 in value:
                                        if isinstance(item2, list):
                                            for item3 in item2:
                                                out.append((', '.join(item3)).encode("utf-8").strip())
                                        elif isinstance(item2, dict):
                                            for key3, value3 in item2.iteritems():
                                                out.append((', '.join(valu3)).encode("utf-8").strip())
                                        else:
                                            out.append(item2.encode("utf-8").strip())
                                elif isinstance(item, dict):
                                    for key2, value2 in item:
                                        if isinstance(value2, list):
                                            for value3 in value2:
                                                out.append((', '.join(value3)).encode("utf-8").strip())
                                        if isinstance(value2, dict):
                                            for key3, value3 in value2.iteritems():
                                                out.append((', '.join(value3)).encode("utf-8").strip())
                                        else:
                                            out.append(value2.encode("uft-8").strip())
                                else:
                                    out.append(response.encode("utf-8").strip())
                        else:
                            out.append(response.encode("utf-8").strip())
                elif isinstance(response, dict):
                    for key,value in response.iteritems():
                        if isinstance(value, list):
                            for item2 in value:
                                if isinstance(item2, list):
                                    for item3 in item2:
                                        out.append((', '.join(item3)).encode("utf-8").strip())
                                elif isinstance(item2, dict):
                                    for key3, value3 in item2.iteritems():
                                        out.append((', '.join(value3)).encode("utf-8").strip())
                                else:
                                    out.append(item2.encode("utf-8").strip())
                        elif isinstance(value, dict):
                            for key,value in value.iteritems():
                                if isinstance(value, list):
                                    for item2 in value:
                                        if isinstance(item2, list):
                                            for item3 in item2:
                                                out.append((', '.join(item3)).encode("utf-8").strip())
                                        elif isinstance(item2, dict):
                                            for key3, value3 in item2.iteritems():
                                                out.append((', '.join(value3)).encode("utf-8").strip())
                                        else:
                                            out.append(item2.encode("utf-8").strip())
                                elif isinstance(value, dict):
                                    for key2, value2 in value.iteritems():
                                        if isinstance(value2, list):
                                            for value3 in value2:
                                                out.append((', '.join(value3)).encode("utf-8").strip())
                                        if isinstance(value2, dict):
                                            for key3, value3 in value2.iteritems():
                                                out.append((', '.join(value3)).encode("utf-8").strip())
                                        else:
                                            out.append(value2.encode("uft-8").strip())
                                else:
                                    out.append(response.encode("utf-8").strip())
                        else:
                            out.append(response.encode("utf-8").strip())
                else:
                    out.append(response.encode("utf-8").strip())
        except Exception,e:
            pass
        if len(out) == 0:
            out = None
        self.elements = out
        return self.elements

    def get_stats(self):
        stats = {}
        for field,value in self.elem.iteritems():
            if isinstance(value, dict):
                for field2,value2 in value.iteritems():
                    if isinstance(value2, dict):
                        for field3,value3 in value2.iteritems():
                            if isinstance(value3, dict):
                                for field4, value4 in value3.iteritems():
                                    stats.setdefault(field + "." + field2 + "." + field3 + "." + field4,0)
                                    stats[field + "." + field2 + "." + field3 + "." + field4] += 1
                            else:
                                if field != None and field2 != None and field3 != None:
                                    stats.setdefault(field + "." + field2 + "." + field3,0)
                                    stats[field + "." + field2 + "." + field3] += 1
                    else:
                        if field != None and field2 != None:
                            stats.setdefault(field + "." + field2,0)
                            stats[field + "." + field2] += 1
            else:
                if field != None:
                    stats.setdefault(field,0)
                    stats[field] += 1
        return stats

    def has_element(self):
        out = []
        present = False
        record = objectpath.Tree(self.elem)
        response = record.execute(self.args.element)
        if reponse != None:
            present = True
            return present

def collect_stats(stats_aggregate, stats):
    #increment the record counter
    stats_aggregate["record_count"] += 1

    for field in stats:

        # get the total number of times a field occurs
        stats_aggregate["field_info"].setdefault(field, {"field_count": 0})
        stats_aggregate["field_info"][field]["field_count"] += 1

        # get average of all fields
        stats_aggregate["field_info"][field].setdefault("field_count_total", 0)
        stats_aggregate["field_info"][field]["field_count_total"] += stats[field]


def create_stats_averages(stats_aggregate):
    for field in stats_aggregate["field_info"]:
        field_count = stats_aggregate["field_info"][field]["field_count"]
        field_count_total = stats_aggregate["field_info"][field]["field_count_total"]

        field_count_total_average = (float(field_count_total) / float(stats_aggregate["record_count"]))
        stats_aggregate["field_info"][field]["field_count_total_average"] = field_count_total_average

        field_count_element_average = (float(field_count_total) / float(field_count))
        stats_aggregate["field_info"][field]["field_count_element_average"] = field_count_element_average

    return stats_aggregate


def calc_completeness(stats_averages):
    completeness = {}
    record_count = stats_averages["record_count"]
    completeness_total = 0
    collection_total = 0
    collection_field_to_count = 0

    populated_elements = len(stats_averages["field_info"])
    for element in sorted(stats_averages["field_info"]):
            element_completeness_percent = 0
            element_completeness_percent = ((stats_averages["field_info"][element]["field_count"]
                                             / float(record_count)) * 100)
            completeness_total += element_completeness_percent

            #gather collection completeness
            if element_completeness_percent > 10:
                collection_total += element_completeness_percent
                collection_field_to_count += 1

    completeness["collection_completeness"] = collection_total / float(collection_field_to_count)
    return completeness


def pretty_print_stats(stats_averages):
    record_count = stats_averages["record_count"]
    #get header length
    element_length = 0
    for element in stats_averages["field_info"]:
        if element_length < len(element):
            element_length = len(element)

    print "\n\n"
    for element in sorted(stats_averages["field_info"]):
        percent = (stats_averages["field_info"][element]["field_count"] / float(record_count)) * 100
        percentPrint = "=" * (int(percent) / 4)
        columnOne = " " * (element_length - len(element)) + element
        print "%s: |%-25s| %6s/%s | %3d%% " % (
            columnOne,
            percentPrint,
            stats_averages["field_info"][element]["field_count"],
            record_count,
            percent
        )

    print "\n"
    completeness = calc_completeness(stats_averages)
    for i in ["collection_completeness"]:
        print "%23s %f" % (i, completeness[i])


def main():
    stats_aggregate = {
        "record_count": 0,
        "field_info": {}
    }
    element_stats_aggregate = {}

    parser = ArgumentParser(usage='%(prog)s [options] data_filename.xml')
    parser.add_argument("-e", "--element", dest="element", help="element to print to screen")
    parser.add_argument("-i", "--id", action="store_true", dest="id", default=False, help="prepend meta_id to line")
    parser.add_argument("-s", "--stats", action="store_true", dest="stats", default=False, help="only print stats for repository")
    parser.add_argument("-p", "--present", action="store_true", dest="present", default=False, help="print if there is value of defined element in record")
    parser.add_argument("datafile", help="put the datafile you want analyzed here")

    args = parser.parse_args()

    if not len(sys.argv) > 0:
        parser.print_help()
        exit()

    if args.element is None:
        args.stats = True

    s = 0
    with open(args.datafile) as data:
        DPLAdata = json.load(data)
    records = DPLAdata['docs']
    numberRecords = len(records)

    for n in range(0, numberRecords):
        record = Record(records[n], args)
        record_id = record.get_record_id()

        if args.stats is False and args.present is False:
            if record.get_elements() is not None:
                for i in record.get_elements():
                    if args.id:
                        print "\t".join([record_id, i])
                    else:
                        print i

        if args.stats is False and args.present is True:
            print "%s %s" % (record_id, record.has_element())

        if args.stats is True and args.element is None:
            if (s % 1000) == 0 and s != 0:
                print "%d records processed" % s
            s += 1
            collect_stats(stats_aggregate, record.get_stats())
        n += 1

    if args.stats is True and args.element is None:
        stats_averages = create_stats_averages(stats_aggregate)
        pretty_print_stats(stats_averages)

if __name__ == "__main__":
    main()
