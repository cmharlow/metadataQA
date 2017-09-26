import sys
from argparse import ArgumentParser
import csv
import re
import os
import pprint


class RepoInvestigatorException(Exception):
    """This is our base exception for this script."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value,)


class Record:
    """Base class for a MODS or nested metadata record in an OAI-PMH
       Repository file."""

    def __init__(self, elem, args):
        """Create the Record class instance."""
        self.elem = elem
        self.args = args

    def get_record_id(self, uri_column):
        """Find an identifier for the record, checking the OAI header."""
        try:
            record_id = self.elem[uri_column]
            return record_id
        except:
            raise RepoInvestigatorException("Record does not have a valid Record Identifier. Check the structure of the Harvested XML (does it have a OAI header? Are the namespaces correct?) and the XML path used here to get to the identifier.")

    def get_elements(self):
        """Get all the values for a given field."""
        if self.elem[self.args.element]:
            self.elements = self.elem[self.args.element]
            return [self.elements]

    def get_stats(self):
        """Get the field presence stats for the default report."""
        stats = {}
        metadata = self.elem
        if len(metadata):
            for key, value in metadata.items():
                if value:
                    stats.setdefault(key, 0)
                    stats[key] += 1
        return stats


def collect_stats(stats_aggregate, stats):
    """Method for generating the default field usage report."""
    # increment the record counter
    stats_aggregate["record_count"] += 1

    for field in stats:

        # get the total number of times a field occurs
        stats_aggregate["field_info"].setdefault(field, {"field_count": 0})
        stats_aggregate["field_info"][field]["field_count"] += 1

        # get average of all fields
        stats_aggregate["field_info"][field].setdefault("field_count_total", 0)
        stats_aggregate["field_info"][field]["field_count_total"] += stats[field]


def create_stats_averages(stats_aggregate):
    """Method for generating the default field usage report."""
    for field in stats_aggregate["field_info"]:
        field_count = stats_aggregate["field_info"][field]["field_count"]
        field_count_total = stats_aggregate["field_info"][field]["field_count_total"]

        field_count_total_average = (float(field_count_total) / float(stats_aggregate["record_count"]))
        stats_aggregate["field_info"][field]["field_count_total_average"] = field_count_total_average

        field_count_element_average = (float(field_count_total) / float(field_count))
        stats_aggregate["field_info"][field]["field_count_element_average"] = field_count_element_average

    return stats_aggregate


def calc_completeness(stats_averages):
    """Method for generating the default field usage report."""
    completeness = {}
    record_count = stats_averages["record_count"]
    completeness_total = 0
    wwww_total = 0
    dpla_total = 0
    collection_total = 0
    collection_field_to_count = 0

    wwww = [
        'mods:name/mods:namePart',       # who
        'mods:titleInfo/mods:title',         # what
        'mods:identifier',    # where
        'mods:originInfo/mods:dateCreated'           # when
    ]

    dpla = [
        'mods:titleInfo/mods:title',
        'mods:identifier',
        'mods:accessCondition'
    ]

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
            #gather wwww completeness
            if element in wwww:
                wwww_total += element_completeness_percent
            #gather dpla completeness
            if element in dpla:
                dpla_total += element_completeness_percent

    if int(collection_field_to_count) > 0:
        completeness["collection_completeness"] = collection_total / float(collection_field_to_count)
    else:
        completeness["collection_completeness"] = 0
    if int(len(wwww)) > 0:
        completeness["wwww_completeness"] = wwww_total / float(len(wwww))
    else:
        completeness["wwwe_completeness"] = 0
    if int(len(dpla)) > 0:
        completeness["dpla_completeness"] = dpla_total / float(len(dpla))
    else:
        completeness["dpla_completeness"] = 0
    completeness["average_completeness"] = ((completeness["collection_completeness"] +
                                             completeness["wwww_completeness"] +
                                             completeness["dpla_completeness"]) / float(4))
    return completeness


def pretty_print_stats(stats_averages):
    """Method for generating the default field usage report."""
    record_count = stats_averages["record_count"]
    #get header length
    element_length = 0
    for element in stats_averages["field_info"]:
        if element_length < len(element):
            element_length = len(element)

    print("\n\n")
    for element in sorted(stats_averages["field_info"]):
        percent = (stats_averages["field_info"][element]["field_count"] / float(record_count)) * 100
        percentPrint = "=" * (int((percent) / 4))
        columnOne = " " * (element_length - len(element)) + element
        print("%s: |%-25s| %6s/%s | %3d%% " % (
                    columnOne,
                    percentPrint,
                    stats_averages["field_info"][element]["field_count"],
                    record_count,
                    percent
                ))

    print("\n")
    completeness = calc_completeness(stats_averages)
    for i in ["collection_completeness", "wwww_completeness", "dpla_completeness", "average_completeness"]:
        print("%23s %f" % (i, completeness[i]))


def process(datafile, args, stats_aggregate, s):
    data = csv.DictReader(open(datafile, 'r',))
    for row in data:
        if row:
            r = Record(row, args)
            record_id = r.get_record_id(args.uri_column)

            if args.stats is False and args.element is not None:
                if r.get_elements() is not None:
                    for i in r.get_elements():
                        if args.id:
                            print("\t".join([record_id, i]))
                        else:
                            print(i)

            if args.stats is True and args.element is None:
                if (s % 1000) == 0 and s != 0:
                    print("%d records processed" % s)
                s += 1
                collect_stats(stats_aggregate, r.get_stats())
    return(stats_aggregate)


def main():
    # Sets up values needed for the default field report.
    stats_aggregate = {
        "record_count": 0,
        "field_info": {}
    }

    # CLI client options.
    parser = ArgumentParser(usage='%(prog)s [options] data_filename.xml')
    parser.add_argument("-e", "--element", dest="element",
                        help="element to print to screen")
    parser.add_argument("-i", "--id", action="store_true", dest="id",
                        default=False, help="prepend meta_id to line")
    parser.add_argument("-u", "--uri_column", dest="uri_column", required=True,
                        default="ID", help="column for field URIs")
    parser.add_argument("-s", "--stats", action="store_true", dest="stats",
                        default=False, help="only print stats for repository")
    parser.add_argument("-p", "--present", action="store_true", dest="present",
                        default=False, help="print if there is value of field")
    parser.add_argument("datafile", help="the datafile you want analyzed.")

    args = parser.parse_args()

    if not len(sys.argv) > 0:
        parser.print_help()
        parser.exit()

    if args.element is None:
        args.stats = True

    s = 0
    stats_aggregate = process(args.datafile, args, stats_aggregate, s)


    if args.stats is True:
        stats_averages = create_stats_averages(stats_aggregate)
        pretty_print_stats(stats_averages)



if __name__ == "__main__":
    main()
