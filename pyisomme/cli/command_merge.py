import argparse

import numpy as np
import pandas as pd

from pyisomme.info import Info
from pyisomme.isomme import Isomme


def add_parser_merge(
    command_parsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    merge_parser = command_parsers.add_parser(
        "merge",
        help="Merge ISO-MMEs",
        description="Merge channels from one or more ISO-MMEs into output_path.",
        epilog="Examples:\n"
        "  pyisomme merge merged.mme first.mme second.mme\n"
        "  pyisomme merge merged.mme test.mme --cfc C",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    merge_parser.add_argument(
        "output_path", help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)"
    )
    merge_parser.add_argument(
        "input_paths",
        nargs="+",
        help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)",
    )
    merge_parser.add_argument(
        "-c",
        "--codes",
        nargs="*",
        default=[],
        help="Channel Code Patterns to filter ISO-MMEs",
    )
    merge_parser.add_argument(
        "--delete-duplicates",
        action="store_true",
        help="Delete duplicate channels (same channel code)",
    )
    merge_parser.add_argument(
        "--delete-filter-duplicates",
        action="store_true",
        help="Delete filtered channels if channel with less filtering exists. "
        "Includes '--delete-duplicates' option",
    )
    merge_parser.add_argument("--set-test-object", dest="test_object")
    merge_parser.add_argument("--set-position", dest="position")
    merge_parser.add_argument("--set-main-location", dest="main_location")
    merge_parser.add_argument("--set-fine-location-1", dest="fine_location_1")
    merge_parser.add_argument("--set-fine-location-2", dest="fine_location_2")
    merge_parser.add_argument("--set-fine-location-3", dest="fine_location_3")
    merge_parser.add_argument("--set-physical-dimension", dest="physical_dimension")
    merge_parser.add_argument("--set-direction", dest="direction")
    merge_parser.add_argument("--set-filter-class", dest="filter_class")
    merge_parser.add_argument("--scale-x", default=1)
    merge_parser.add_argument("--scale-y", default=1)
    merge_parser.add_argument("--offset-x", default=0)
    merge_parser.add_argument("--offset-y", default=0)
    merge_parser.add_argument(
        "--auto-offset-y",
        action="store_true",
        help="Apply y-offset with value from t=0",
    )
    merge_parser.add_argument(
        "--append",
        action="store_true",
        help="Append channels to ISO-MME if output_path exists",
    )
    merge_parser.add_argument(
        "--resample",
        nargs=3,
        type=float,
        metavar=("START", "STEP", "STOP"),
        help="Resampling by linear interpolation (no extrapolation)",
    )
    merge_parser.add_argument(
        "--crop",
        nargs=2,
        type=float,
        metavar=("START", "STOP"),
        help="Crop ISO-MME channels to x-min to x-max e.g. (--crop 0.0 0.15)",
    )
    merge_parser.add_argument(
        "--cfc",
        help="Filter channels with Channel Frequency Class CFC "
        "(in Hz or as ISO-Code A/B/C/..)",
    )
    merge_parser.add_argument(
        "--delete-info",
        action="store_true",
        help="Delete test and channel info "
        "(hiding potentially confidential data when publishing)",
    )
    merge_parser.add_argument(
        "--set-test-number",
        help="Set test number of output path "
        "(default is first test number of input paths)",
    )


def execute_merge_command(options: argparse.Namespace) -> None:
    merged_isomme = Isomme().read(options.input_paths[0], *options.codes)
    for other_input_path in options.input_paths[1:]:
        merged_isomme.extend(Isomme().read(other_input_path, *options.codes))

    if options.delete_duplicates or options.delete_filter_duplicates:
        merged_isomme.delete_duplicates(
            filter_class_duplicates=options.delete_filter_duplicates
        )

    for channel in merged_isomme.channels:
        channel.set_code(
            test_object=options.test_object,
            position=options.position,
            main_location=options.main_location,
            fine_location_1=options.fine_location_1,
            fine_location_2=options.fine_location_2,
            fine_location_3=options.fine_location_3,
            physical_dimension=options.physical_dimension,
            direction=options.direction,
            filter_class=options.filter_class,
        )
        if options.auto_offset_y:
            channel.auto_offset_y()
        channel.scale_y(options.scale_y)
        channel.offset_y(options.offset_y)
        channel.scale_x(options.scale_x)
        channel.offset_x(options.offset_x)

        if options.cfc is not None:
            try:
                freq = float(options.cfc)
            except ValueError:
                channel.cfc(options.cfc, return_copy=False)
            else:
                channel.cfc_hz(freq, return_copy=False)

    if options.resample:
        for channel in merged_isomme.channels:
            start, step, stop = options.resample
            t = np.arange(start, stop + step, step)
            channel.data = pd.DataFrame(channel.get_data(t=t), index=t)
    if options.crop:
        merged_isomme.crop(*options.crop)
    if options.delete_info:
        merged_isomme.test_info = Info()
        merged_isomme.channel_info = Info()
        for channel in merged_isomme.channels:
            channel.info = Info()
    if options.set_test_number:
        merged_isomme.test_number = options.set_test_number

    if options.append:
        try:
            existing_isomme = Isomme().read(options.output_path)
            existing_isomme.extend(merged_isomme)
            existing_isomme.write(options.output_path)
        except Exception:
            merged_isomme.write(options.output_path)
    else:
        merged_isomme.write(options.output_path)
