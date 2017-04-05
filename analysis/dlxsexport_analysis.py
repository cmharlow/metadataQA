import hashlib
import sys
import pprint
from argparse import ArgumentParser
from lxml import etree
import re

class RepoInvestigatorException(Exception):
    """This is our base exception for this script"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value,)

class Record:
    """Base class for nested metadata record in a DLXS export."""

    def __init__(self, elem, args):
        self.elem = elem
        self.args = args

    def get_record_id(self):
        try:
            record_id = self.elem.find("FILEDESC/PUBLICATIONSTMT/IDNO").text
            return record_id
        except:
            raise RepoInvestigatorException("Record does not have a valid Record Identifier")

    def get_elements(self):
        out = []
        for desc in self.elem.iterdescendants():
            if desc.tag == self.args.element and desc.text != None:
                out.append(desc.text.encode("utf-8").strip())
        if len(out) == 0:
            out = None
        self.elements = out
        return self.elements

    def get_xpath(self):
        out = []
        if self.elem.xpath(self.args.xpath) != None:
            for value in self.elem.xpath(self.args.xpath):
                if value.text != None:
                    out.append(value.text.encode("utf-8").strip())
        if len(out) == 0:
            out = None
        self.elements = out
        return self.elements

    def get_stats(self):
        stats = {}
        record = etree.ElementTree(self.elem)
        for desc in self.elem.iterdescendants():
            if len(desc) == False and desc.text != None: #ignore empties, does NOT have children elements
                stats.setdefault(re.sub('\[\d+\]','', record.getpath(desc)), 0)
                stats[re.sub('\[\d+\]','', record.getpath(desc))] += 1
        return stats

    def has_element(self):
        out = []
        present = False
        for desc in self.elem.iterdescendants():
            if desc.tag == self.args.element and desc.text != None:
                present = True
                return present

    def has_xpath(self):
        out = []
        present = False
        if self != None:
            if self.xpath(self.args.xpath) != None:
                for value in self.elem.xpath(self.args.xpath):
                    if value.text != None:
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


def pretty_print_stats(stats_averages):
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


def main():
    stats_aggregate = {
        "record_count": 0,
        "field_info": {}
    }
    element_stats_aggregate = {}

    parser = ArgumentParser(usage='%(prog)s [options] data_filename.xml')
    parser.add_argument("-e", "--element", dest="element", help="element to print to screen")
    parser.add_argument("-x", "--xpath", dest="xpath", help="get response of xpath expression on mods:mods record")
    parser.add_argument("-i", "--id", action="store_true", dest="id", default=False, help="prepend meta_id to line")
    parser.add_argument("-s", "--stats", action="store_true", dest="stats", default=False, help="only print stats for repository")
    parser.add_argument("-p", "--present", action="store_true", dest="present", default=False, help="print if there is value of defined element in record")
    parser.add_argument("datafile", help="put the datafile you want analyzed here")

    args = parser.parse_args()

    if not len(sys.argv) > 0:
        parser.print_help()
        exit()

    if args.element is None and args.xpath is None:
        args.stats = True

    s = 0
    for event, elem in etree.iterparse(args.datafile):
        if elem.tag == "record":
            r = Record(elem, args)
            record_id = r.get_record_id()

            if args.stats is False and args.present is False and args.element is not None:
                if r.get_elements() is not None:
                    for i in r.get_elements():
                        if args.id:
                            print("\t".join([record_id, i]))
                        else:
                            print(i)

            if args.stats is False and args.present is False and args.xpath is not None:
                if r.get_xpath() is not None:
                    for i in r.get_xpath():
                        if args.id:
                            print("\t".join([record_id, i]))
                        else:
                            print(i)

            if args.stats is False and args.element is not None and args.present is True:
                print("%s %s" % (record_id, r.has_element()))

            if args.stats is False and args.xpath is not None and args.present is True:
                print("%s %s" % (record_id, r.has_xpath()))

            if args.stats is True and args.element is None:
                if (s % 1000) == 0 and s != 0:
                    print("%d records processed" % s)
                s += 1
                collect_stats(stats_aggregate, r.get_stats())
            elem.clear()

    if args.stats is True and args.element is None:
        stats_averages = create_stats_averages(stats_aggregate)
        pretty_print_stats(stats_averages)

if __name__ == "__main__":
    main()
