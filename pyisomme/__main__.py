import argparse
import logging
import pandas as pd
import numpy as np

import pyisomme


REPORTS = [
    pyisomme.report.euro_ncap.frontal_mpdb.EuroNCAP_Frontal_MPDB,
    pyisomme.report.euro_ncap.frontal_50kmh.EuroNCAP_Frontal_50kmh,
    pyisomme.report.euro_ncap.side_barrier.EuroNCAP_Side_Barrier,
    pyisomme.report.euro_ncap.side_pole.EuroNCAP_Side_Pole,
    pyisomme.report.euro_ncap.side_farside.EuroNCAP_Side_FarSide,
    pyisomme.report.euro_ncap.side_farside_vtc.EuroNCAP_Side_Farside_VTC,
    pyisomme.report.un.frontal_50kmh_r137.UN_Frontal_50kmh_R137,
    pyisomme.report.un.frontal_56kmh_odb_r94.UN_Frontal_56kmh_ODB_R94,
    pyisomme.report.un.side_pole_r135.UN_Side_Pole_R135,
    pyisomme.report.un.side_barrier_r95.UN_Side_Barrier_R95,
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
            if options.auto_offset_y:
                channel.auto_offset_y()
            channel.scale_y(options.scale_y)
            channel.offset_y(options.offset_y)
            channel.scale_x(options.scale_x)
            channel.offset_x(options.offset_x)

            if options.cfc is not None:
                channel.cfc(options.cfc, return_copy=False)

        if options.resample:
            for channel in merged_isomme.channels:
                start, step, stop = options.resample
                t = np.arange(start, stop+step, step)
                channel.data = pd.DataFrame(channel.get_data(t=t), index=t)

        if options.crop:
            merged_isomme.crop(*options.crop)

        if options.append:
            try:
                existing_isomme = pyisomme.Isomme().read(options.output_path)
                existing_isomme.extend(merged_isomme)
                existing_isomme.write(options.output_path)
            except Exception:
                merged_isomme.write(options.output_path)
        else:
            merged_isomme.write(options.output_path)

    if options.command == "report":
        isomme_list = [pyisomme.Isomme().read(input_path) for input_path in options.input_paths]

        if options.crop:
            for isomme in isomme_list:
                isomme.crop(options.crop)

        report = {report.__name__: report for report in REPORTS}[options.report_name](isomme_list)
        report.calculate()
        report.export_pptx(options.report_path, template=options.template)

    if options.command == "plot":
        if options.calculate:
            isomme_list = [pyisomme.Isomme().read(input_path) for input_path in options.input_paths]
        else:
            isomme_list = [pyisomme.Isomme().read(input_path, *options.codes) for input_path in options.input_paths]
        n = slice(None, options.n)

        pyisomme.Plot_Line({isomme: [isomme.get_channels(*options.codes)[n]] for isomme in isomme_list},
                           xlim=options.xlim,
                           ylim=options.ylim,
                           legend=options.legend).show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--verbose", action="store_true", dest="verbose", help="Verbose mode")

    command_parsers = parser.add_subparsers(dest="command", required=True)

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
                              default=[],
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
    merge_parser.add_argument("--scale-x", default=1, dest="scale_x")
    merge_parser.add_argument("--scale-y", default=1, dest="scale_y")
    merge_parser.add_argument("--offset-x", default=0, dest="offset_x")
    merge_parser.add_argument("--offset-y", default=0, dest="offset_y")
    merge_parser.add_argument("--auto-offset-y",
                              action="store_true",
                              dest="auto_offset_y",
                              help="Apply y-offset with value from t=0")
    merge_parser.add_argument("--append",
                              action="store_true",
                              dest="append",
                              help="Append channels to ISO-MME if output_path exists")
    merge_parser.add_argument('--resample',
                              nargs=3,
                              type=float,
                              metavar=('START', 'STEP', 'STOP'),
                              help='Resampling by linear interpolation (no extrapolation)')
    merge_parser.add_argument("--crop",
                              dest="crop",
                              nargs=2,
                              type=float,
                              metavar=('START', 'STOP'),
                              help="Crop ISO-MME channels to x-min to x-max e.g. (--crop 0.0 0.15)")
    merge_parser.add_argument("--cfc",
                              dest="cfc",
                              help="Filter channels with Channel Frequency Class CFC (in Hz or as ISO-Code A/B/C/..)")

    report_parser = command_parsers.add_parser("report", help="Create a Report")
    report_parser.add_argument(dest="report_name",
                               choices=[report.__name__ for report in REPORTS],
                               help="Report name")
    report_parser.add_argument(dest="report_path",
                               help="Report Path (.pptx)")
    report_parser.add_argument(nargs="+",
                               dest="input_paths",
                               help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)")
    report_parser.add_argument("--template",
                               dest="template",
                               help="Path to Template (.pptx)")
    report_parser.add_argument("--crop",
                               dest="crop",
                               nargs=2,
                               type=float,
                               metavar=('START', 'STOP'),
                               help="Crop ISO-MME channels to x-min to x-max e.g. (--crop 0.0 0.15)")

    plot_parser = command_parsers.add_parser("plot", help="Plot Channels")
    plot_parser.add_argument(nargs="+",
                             dest="input_paths",
                             help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)")
    plot_parser.add_argument("-c", "--codes",
                             nargs="*",
                             dest="codes",
                             default=[],
                             help="Channel Code Patterns to select Channel to plot")
    plot_parser.add_argument("--calculate",
                             action="store_true",
                             dest="calculate",
                             help="Plot calculated Channel.")
    plot_parser.add_argument("-n", "--n-channels",
                             type=int,
                             dest="n",
                             help="Limit Number of channels to plot")
    plot_parser.add_argument("-x", "--xlim",
                             dest="xlim",
                             nargs=2,
                             type=float,
                             metavar=('START', 'STOP'),
                             help="X-Axis Range [in ms]")
    plot_parser.add_argument("-y", "--ylim",
                             dest="ylim",
                             nargs=2,
                             type=float,
                             metavar=('START', 'STOP'),
                             help="Y-Axis Range")
    plot_parser.add_argument("--legend-off",
                             dest="legend",
                             action="store_false",
                             help="Hide legend")

    options = parser.parse_args()

    main()
