import argparse
import logging

import pyisomme


logging.basicConfig(level=logging.WARNING)

# TODO: plot 1.mme 2.mme code=11HEAD????H3ACXA code=11HEADCG??H3ACXA
# TODO: diff
# TODO: set 1.mme code=11HEAD* position=3
# TODO: list 11HEAD*

REPORTS = [
    pyisomme.report.euro_ncap.frontal_mpdb.EuroNCAP_Frontal_MPDB,
    pyisomme.report.euro_ncap.frontal_50kmh.EuroNCAP_Frontal_50kmh,
    pyisomme.report.euro_ncap.side_barrier.EuroNCAP_Side_Barrier,
    pyisomme.report.euro_ncap.side_pole.EuroNCAP_Side_Pole,
]


def main():
    logging.basicConfig(format='%(module)-12s %(levelname)-8s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S',
                        level=logging.INFO if options.verbose else logging.WARNING)

    if options.command == 'list':
        for isomme in [pyisomme.Isomme().read(input_path) for input_path in options.input_paths]:
            print("\n")
            print(isomme.test_number)

            if len(options.codes) == 0:
                channels = isomme.channels
            else:
                channels = isomme.get_channels(*options.codes, filter=False, calculate=False, integrate=False, differentiate=False)

            for channel in channels:
                print(channel.code)

    if options.command == "merge":
        merged_isomme = pyisomme.Isomme().read(options.input_paths[0], *options.codes)
        for other_input_path in options.input_paths[1:]:
            merged_isomme.extend(pyisomme.Isomme().read(other_input_path, *options.codes))

        if options.delete_duplicates or options.delete_filter_duplicates:
            merged_isomme.delete_duplicates(filter_class_duplicates=options.delete_filter_duplicates)

        for channel in merged_isomme.channels:
            channel.set_code(test_object=options.test_object,
                             position=options.position,
                             main_location=options.main_location,
                             fine_location_1=options.fine_location_1,
                             fine_location_2=options.fine_location_2,
                             fine_location_3=options.fine_location_3,
                             physical_dimension=options.physical_dimension,
                             direction=options.direction,
                             filter_class=options.filter_class)

        merged_isomme.write(options.output_path)

    if options.command == "report":
        isomme_list = [pyisomme.Isomme().read(input_path) for input_path in options.input_paths]

        report = {report.__name__: report for report in REPORTS}[options.report_name](isomme_list)
        report.calculate()
        report.export_pptx(options.report_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="Verbose mode")

    command_parsers = parser.add_subparsers(dest="command")

    list_parser = command_parsers.add_parser("list")
    list_parser.add_argument(nargs="+",
                             dest="input_paths",
                             help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)")
    list_parser.add_argument("-c", "--codes",
                             nargs="*",
                             dest="codes",
                             default=[],
                             help="Channel Code Patterns to filter ISO-MMEs")

    merge_parser = command_parsers.add_parser("merge", help="Merge ISO-MMEs")
    merge_parser.add_argument(dest="output_path",
                              help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)")
    merge_parser.add_argument(nargs="+",
                              dest="input_paths",
                              help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)")
    merge_parser.add_argument("-c", "--codes",
                              nargs="*",
                              dest="codes",
                              help="Channel Code Patterns to filter ISO-MMEs")
    merge_parser.add_argument("--delete-duplicates",
                              action="store_true",
                              dest="delete_duplicates",
                              help="Delete duplicate channels (same channel code)")
    merge_parser.add_argument("--delete-filter-duplicates",
                              action="store_true",
                              dest="delete_filter_duplicates",
                              help="Delete filtered channels if channel with less filtering exists. "
                                   "Includes '--delete-duplicates' option")
    merge_parser.add_argument("--set-test-object", dest="test_object")
    merge_parser.add_argument("--set-position", dest="position")
    merge_parser.add_argument("--set-main-location", dest="main_location")
    merge_parser.add_argument("--set-fine-location-1", dest="fine_location_1")
    merge_parser.add_argument("--set-fine-location-2", dest="fine_location_2")
    merge_parser.add_argument("--set-fine-location-3", dest="fine_location_3")
    merge_parser.add_argument("--set-physical-dimension", dest="physical_dimension")
    merge_parser.add_argument("--set-direction", dest="direction")
    merge_parser.add_argument("--set-filter-class", dest="filter_class")

    report_parser = command_parsers.add_parser("report", help="Create a Report")
    report_parser.add_argument(dest="report_name",
                               choices=[report.__name__ for report in REPORTS],
                               help="Report name")
    report_parser.add_argument(dest="report_path",
                               help="Report Path (.pptx)")
    report_parser.add_argument(nargs="+",
                               dest="input_paths",
                               help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)")

    options = parser.parse_args()

    main()
