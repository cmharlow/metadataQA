"""Perform some metadata analyses on SharedShelf-harvested metadata."""
from six import iteritems
from argparse import ArgumentParser
import json


class RepoInvestigatorException(Exception):
    """This is our base exception for this script."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value,)


class Record:
    """Base class for a metadata record/object."""

    def __init__(self, value, args):
        self.value = value
        self.args = args

    def get_elements(self):
        out = []
        try:
            elem_q = self.args.element
            if 'display_value' in elem_q:
                field_q = elem_q.split('.')[0]
                subfield_q = elem_q.split('.')[1]
                if field_q in self.value:
                    if self.value[field_q] and subfield_q in self.value[field_q]:
                        data_val = self.value[field_q][subfield_q]
                    else:
                        data_val = None
                else:
                    data_val = None
            elif 'links' in elem_q:
                links_out = []
                field_q = elem_q.split('.')[0]
                subfield_q = elem_q.split('.')[1]
                if field_q in self.value:
                    if self.value[field_q] and subfield_q in self.value[field_q]:
                        for blob in self.value[field_q][subfield_q]:
                            blob_id = blob['id']
                            links_out.append(blob_id)
                    else:
                        data_val = None
                else:
                    data_val = None
                data_val = links_out
            else:
                data_val = self.value[elem_q]

            if isinstance(data_val, list):
                for out_val in data_val:
                    if isinstance(out_val, dict):
                        print(out_val.keys())
                    else:
                        if out_val:
                            out.append(out_val)
            elif isinstance(data_val, dict):
                if 'publishing_status' in data_val:
                    for key, value in data_val:
                        out_val = key + " : " + value['status']
                        out.append(out_val)
                elif 'display_value' in data_val:
                    out_val = data_val['display_value']
                    if data_val:
                        out.append(out_val)
            else:
                if data_val:
                    out.append(data_val)
        except KeyError:
            pass
        if len(out) == 0:
            out = None
        self.elements = out
        return self.elements

    def get_stats(self):
        """Getting statistics for all fields."""
        stats = {}
        for field, value in iteritems(self.value):
            if isinstance(value, dict):
                for field2, value2 in iteritems(value):
                    if isinstance(value2, dict):
                        for field3, value3 in iteritems(value2):
                            if isinstance(value3, dict):
                                for field4, value4 in iteritems(value3):
                                    if value4 and value4 is not []:
                                        stats.setdefault(field + "." + field2 + "." + field3 + "." + field4, 0)
                                        stats[field + "." + field2 + "." + field3 + "." + field4] += 1
                            else:
                                if field and field2 and field3 and value3 is not []:
                                    stats.setdefault(field + "." + field2 + "." + field3, 0)
                                    stats[field + "." + field2 + "." + field3] += 1
                    else:
                        if field and field2 and value2 is not []:
                            stats.setdefault(field + "." + field2, 0)
                            stats[field + "." + field2] += 1
            else:
                if field and value is not []:
                    stats.setdefault(field, 0)
                    stats[field] += 1
        return stats

    def has_element(self):
        """Getting present/not for a specific element."""
        present = "False"
        elem_q = self.args.element
        if 'display_value' in elem_q:
            field_q = elem_q.split('.')[0]
            subfield_q = elem_q.split('.')[1]
            if field_q in self.value:
                if self.value[field_q] and subfield_q in self.value[field_q]:
                    present = True
        elif 'links' in elem_q:
            field_q = elem_q.split('.')[0]
            subfield_q = elem_q.split('.')[1]
            if field_q in self.value:
                if self.value[field_q] and subfield_q in self.value[field_q]:
                    present = True
        else:
            if elem_q in self.value:
                if self.value[elem_q]:
                    present = True
        return(present)


def collect_stats(stats_aggregate, stats):
    """Aggregate statitics for all fields as collected above."""
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
    """Get averages for each field's statistics."""
    for field in stats_aggregate["field_info"]:
        field_count = stats_aggregate["field_info"][field]["field_count"]
        field_count_total = stats_aggregate["field_info"][field]["field_count_total"]

        field_count_total_average = (float(field_count_total) / float(stats_aggregate["record_count"]))
        stats_aggregate["field_info"][field]["field_count_total_average"] = field_count_total_average

        field_count_element_average = (float(field_count_total) / float(field_count))
        stats_aggregate["field_info"][field]["field_count_element_average"] = field_count_element_average

    return stats_aggregate


def pretty_print_stats(stats_averages):
    """Generate pretty version of statistics to print in shell."""
    record_count = stats_averages["record_count"]
    # get header length
    element_length = 0
    for element in stats_averages["field_info"]:
        if element_length < len(element):
            element_length = len(element)

    print("\n\n")
    for element in sorted(stats_averages["field_info"]):
        percent = (stats_averages["field_info"][element]["field_count"] / float(record_count)) * 100
        percentPrint = "=" * int(int(percent) / 4)
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

    parser = ArgumentParser(usage='%(prog)s [options] data_dump.json')
    parser.add_argument("-e", "--element", dest="element",
                        help="element to print to screen")
    parser.add_argument("-i", "--id", action="store_true", dest="id",
                        default=False, help="prepend meta_id to line")
    parser.add_argument("-s", "--stats", action="store_true", dest="stats",
                        default=False, help="only print stats for repository")
    parser.add_argument("-p", "--present", action="store_true",
                        dest="present", default=False,
                        help="print if there is value of element in record")
    parser.add_argument("datafile", help="datafile you want analyzed")
    args = parser.parse_args()

    if args.element is None:
        args.stats = True

    s = 0
    with open(args.datafile) as data:
        ssdata = json.load(data)

    for key, value in ssdata.items():
        record = Record(value, args)
        record_id = str(value['project_id']) + "_" + str(key)

        if args.stats is False and args.present is False:
            if record.get_elements() is not None:
                for i in record.get_elements():
                    if args.id:
                        if i:
                            print("\t".join([record_id, str(i)]))
                    else:
                        if i:
                            print(str(i))

        if args.stats is False and args.present is True:
            print("%s %s" % (record_id, record.has_element()))

        if args.stats is True and args.element is None:
            if (s % 1000) == 0 and s != 0:
                print("%d records processed" % s)
            s += 1
            collect_stats(stats_aggregate, record.get_stats())

    if args.stats is True and args.element is None:
        stats_averages = create_stats_averages(stats_aggregate)
        pretty_print_stats(stats_averages)

if __name__ == "__main__":
    main()
