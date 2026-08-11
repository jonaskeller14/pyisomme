from __future__ import annotations

import argparse
from collections import Counter
from fnmatch import fnmatch
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from pyisomme import Info
from pyisomme.channel import Channel
from pyisomme.code import CODE_COMPONENTS
from pyisomme.isomme import Isomme
from pyisomme.plotting import Plot_Line
from pyisomme.report import REPORTS
from pyisomme.unit import Unit


logger = logging.getLogger(__name__)

CODE_FIELDS = tuple(name for name, _ in CODE_COMPONENTS)
SET_FIELDS = ("unit", *CODE_FIELDS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    command_parsers = parser.add_subparsers(dest="command", required=True)

    list_parser = command_parsers.add_parser("list")
    list_parser.add_argument(
        "input_paths",
        nargs="+",
        help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)",
    )
    list_parser.add_argument(
        "-c",
        "--codes",
        nargs="*",
        default=[],
        help="Channel Code Patterns to filter ISO-MMEs",
    )

    merge_parser = command_parsers.add_parser("merge", help="Merge ISO-MMEs")
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

    set_parser = command_parsers.add_parser(
        "set",
        help="Set one metadata field on selected channels in place",
        description="Read an ISO-MME, set one metadata field on matching channels, and write "
        "the complete ISO-MME back in place. Quote wildcard patterns, e.g. -c '11*'.",
    )
    set_parser.add_argument(
        "input_paths",
        nargs="+",
        help="Writable ISO-MME path(s) (.mme/folder/.zip/.tar/.tar.gz)",
    )
    set_parser.add_argument(
        "field", choices=SET_FIELDS, help="Unit or channel-code field to set"
    )
    set_parser.add_argument(
        "value", help="New metadata value; unit relabels data without converting values"
    )
    set_parser.add_argument(
        "-c",
        "--codes",
        nargs="+",
        required=True,
        metavar="CODE_PATTERN",
        help="Quoted channel-code pattern(s); use -c '*' to select every channel",
    )

    convert_parser = command_parsers.add_parser(
        "convert",
        help="Convert selected channel data to another unit in place",
        description="Read one or more ISO-MMEs, numerically convert matching channels to another "
        "unit, and write each complete ISO-MME back in place. Quote wildcard patterns.",
    )
    convert_parser.add_argument(
        "input_paths",
        nargs="+",
        help="Writable ISO-MME path(s) (.mme/folder/.zip/.tar/.tar.gz)",
    )
    convert_parser.add_argument(
        "field",
        choices=("unit",),
        help="Metadata field whose values and data should be converted",
    )
    convert_parser.add_argument(
        "value", help="Target unit compatible with every selected channel"
    )
    convert_parser.add_argument(
        "-c",
        "--codes",
        nargs="+",
        required=True,
        metavar="CODE_PATTERN",
        help="Quoted channel-code pattern(s); use -c '*' to select every channel",
    )

    report_parser = command_parsers.add_parser("report", help="Create a Report")
    report_parser.add_argument(
        "report_name",
        choices=[report.__name__ for report in REPORTS],
        help="Report name",
    )
    report_parser.add_argument("report_path", help="Report Path (.pptx)")
    report_parser.add_argument(
        "input_paths",
        nargs="+",
        help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)",
    )
    report_parser.add_argument("--template", help="Path to Template (.pptx)")
    report_parser.add_argument(
        "--crop",
        nargs=2,
        type=float,
        metavar=("START", "STOP"),
        help="Crop ISO-MME channels to x-min to x-max e.g. (--crop 0.0 0.15)",
    )

    plot_parser = command_parsers.add_parser("plot", help="Plot Channels")
    plot_parser.add_argument(
        "input_paths",
        nargs="+",
        help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)",
    )
    plot_parser.add_argument(
        "-c",
        "--codes",
        nargs="*",
        default=[],
        help="Channel Code Patterns to select Channel to plot",
    )
    plot_parser.add_argument(
        "--calculate", action="store_true", help="Plot calculated Channel."
    )
    plot_parser.add_argument(
        "-n",
        "--n-channels",
        type=int,
        dest="n",
        help="Limit Number of channels to plot",
    )
    plot_parser.add_argument(
        "-x",
        "--xlim",
        nargs=2,
        type=float,
        metavar=("START", "STOP"),
        help="X-Axis Range [in ms]",
    )
    plot_parser.add_argument(
        "-y",
        "--ylim",
        nargs=2,
        type=float,
        metavar=("START", "STOP"),
        help="Y-Axis Range",
    )
    plot_parser.add_argument(
        "--legend-off", dest="legend", action="store_false", help="Hide legend"
    )
    return parser


def _writable_input(path: Path) -> bool:
    suffixes = [suffix.lower() for suffix in path.suffixes]
    return (
        path.suffix == ""
        or path.suffix.lower() in {".mme", ".zip", ".tar"}
        or (len(suffixes) >= 2 and suffixes[-2:] == [".tar", ".gz"])
    )


def _load_selected(
    input_paths: list[str], code_patterns: list[str]
) -> list[tuple[Path, Isomme, list[Channel]]]:
    paths = [Path(input_path) for input_path in input_paths]
    for path in paths:
        if not _writable_input(path):
            raise ValueError(
                f"Cannot write ISO-MME back to '{path}'. "
                "Use a .mme, folder, .zip, .tar, or .tar.gz path."
            )
    resolved_paths = [path.resolve() for path in paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise ValueError("Each input path may be specified only once.")

    selected = []
    for path in paths:
        isomme = Isomme().read(path)
        channels = [
            channel
            for channel in isomme.channels
            if any(fnmatch(str(channel.code), pattern) for pattern in code_patterns)
        ]
        if not channels:
            patterns = ", ".join(repr(pattern) for pattern in code_patterns)
            raise ValueError(f"No channels in '{path}' match: {patterns}")
        selected.append((path, isomme, channels))
    return selected


def _print_changes(
    path: Path, field: str, channels: list[Channel], changes: list[tuple[str, str, str]]
) -> None:
    print(f"{path}:")
    for code, old_value, new_value in changes:
        if field == "code":
            print(f"  {old_value} -> {new_value}")
        else:
            print(f"  {code}: {field} {old_value} -> {new_value}")
    print(f"  Matched {len(channels)} channel(s); changed {len(changes)}.")


def _set_channel_metadata(
    input_paths: list[str], field: str, value: str, code_patterns: list[str]
) -> None:
    selected = _load_selected(input_paths, code_patterns)
    changes_by_path: list[list[tuple[str, str, str]]] = []

    if field == "unit":
        new_unit = Unit(value)
        for _, _, channels in selected:
            changes_by_path.append(
                [
                    (str(channel.code), str(channel.unit), str(new_unit))
                    for channel in channels
                    if channel.unit != new_unit
                ]
            )
        for _, _, channels in selected:
            for channel in channels:
                channel.set_unit(new_unit)
    else:
        replacements_by_path = [
            [(channel, channel.code.set(**{field: value})) for channel in channels]
            for _, _, channels in selected
        ]
        changes_by_path = [
            [
                (str(channel.code), str(channel.code), str(new_code))
                for channel, new_code in replacements
                if channel.code != new_code
            ]
            for replacements in replacements_by_path
        ]
        for (path, isomme, _), replacements in zip(selected, replacements_by_path):
            old_code_counts = Counter(channel.code for channel in isomme.channels)
            for channel, new_code in replacements:
                channel.set_code(new_code)
            new_code_counts = Counter(channel.code for channel in isomme.channels)
            new_duplicates = sorted(
                str(code)
                for code, count in new_code_counts.items()
                if count > 1 and count > old_code_counts[code]
            )
            if new_duplicates:
                logger.warning(
                    "Code rewrite in '%s' created duplicate channel code(s): %s",
                    path,
                    ", ".join(new_duplicates),
                )

    output_field = "unit" if field == "unit" else "code"
    for (path, isomme, channels), changes in zip(selected, changes_by_path):
        isomme.write(path)
        _print_changes(path, output_field, channels, changes)


def _convert_channel_units(
    input_paths: list[str], value: str, code_patterns: list[str]
) -> None:
    selected = _load_selected(input_paths, code_patterns)
    new_unit = Unit(value)

    # Validate compatibility across every input before changing or writing any of them.
    for _, _, channels in selected:
        for channel in channels:
            channel.unit.to(new_unit)

    changes_by_path = [
        [
            (str(channel.code), str(channel.unit), str(new_unit))
            for channel in channels
            if channel.unit != new_unit
        ]
        for _, _, channels in selected
    ]
    for _, _, channels in selected:
        for channel in channels:
            channel.convert_unit(new_unit)

    for (path, isomme, channels), changes in zip(selected, changes_by_path):
        isomme.write(path)
        _print_changes(path, "unit", channels, changes)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    options = parser.parse_args(argv)
    logging.basicConfig(
        format="%(module)-12s %(levelname)-8s %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S",
        level=logging.INFO if options.verbose else logging.WARNING,
    )

    if options.command == "list":
        for isomme in [Isomme().read(input_path) for input_path in options.input_paths]:
            print("\n")
            print(isomme.test_number)
            channels = (
                isomme.channels
                if len(options.codes) == 0
                else isomme.get_channels(
                    *options.codes,
                    filter=False,
                    calculate=False,
                    integrate=False,
                    differentiate=False,
                )
            )
            for channel in channels:
                print(channel.code)

    elif options.command == "merge":
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
            merged_isomme.test_info = Info([])
            merged_isomme.channel_info = Info([])
            for channel in merged_isomme.channels:
                channel.info = Info([])
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

    elif options.command == "set":
        try:
            _set_channel_metadata(
                options.input_paths, options.field, options.value, options.codes
            )
        except (ValueError, TypeError) as error:
            parser.error(str(error))

    elif options.command == "convert":
        try:
            _convert_channel_units(options.input_paths, options.value, options.codes)
        except (ValueError, TypeError) as error:
            parser.error(str(error))

    elif options.command == "report":
        isomme_list = [Isomme().read(input_path) for input_path in options.input_paths]
        if options.crop:
            for isomme in isomme_list:
                isomme.crop(options.crop)
        report = {report.__name__: report for report in REPORTS}[options.report_name](
            isomme_list
        )
        report.calculate()  # type: ignore[attr-defined]
        report.export_pptx(options.report_path, template=options.template)  # type: ignore[attr-defined]

    elif options.command == "plot":
        if options.calculate:
            isomme_list = [
                Isomme().read(input_path) for input_path in options.input_paths
            ]
        else:
            isomme_list = [
                Isomme().read(input_path, "??TIRS??????????", *options.codes)
                for input_path in options.input_paths
            ]
        n = slice(None, options.n)
        channels_by_isomme: dict[Isomme, list[Channel]] = {}
        for isomme in isomme_list:
            channels = isomme.get_channels(*options.codes)
            channels.extend(
                resolved_channel
                for code in options.codes
                if (resolved_channel := isomme.get_channel(code)) is not None
            )
            channels_by_isomme[isomme] = list(
                {channel.code: channel for channel in channels}.values()
            )[n]

        Plot_Line(
            {
                isomme: [list(channels)]
                for isomme, channels in channels_by_isomme.items()
            },
            xlim=options.xlim,
            ylim=options.ylim,
            legend=options.legend,
        ).show()


if __name__ == "__main__":
    main()
