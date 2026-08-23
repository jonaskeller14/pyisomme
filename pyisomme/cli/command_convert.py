import argparse
from pathlib import Path

from astropy.units.core import UnitConversionError

from pyisomme.isomme import Isomme
from pyisomme.unit import Unit

CODE_COMPONENT_HELP = "\n".join(
    [
        "Channel code components (a channel code has 16 characters):",
        "  test_object        character 1",
        "  position           character 2",
        "  main_location      characters 3-6",
        "  fine_location_1    characters 7-8",
        "  fine_location_2    characters 9-10",
        "  fine_location_3    characters 11-12",
        "  physical_dimension characters 13-14",
        "  direction          character 15",
        "  filter_class       character 16",
        "Channel-code patterns may contain wildcards. Quote wildcard patterns so",
        "the shell does not expand them. Wildcards may select incompatible or",
        "unwanted channels.",
    ]
)


def add_parser_convert(command_parsers: argparse._SubParsersAction) -> None:
    convert_parser = command_parsers.add_parser(
        "convert",
        help="Convert selected channel data to another unit in place",
        description="Read one or more ISO-MMEs, numerically convert matching channels to another "
        "unit, and write each complete ISO-MME back in place. Unlike 'set unit', this "
        "changes both the unit label and the numeric data.\n\n"
        "Specify the target unit with the required --unit option.\n\n"
        + CODE_COMPONENT_HELP,
        epilog="Examples:\n"
        "  pyisomme convert test.mme --unit mm -c '13CHST000000DSXP'\n"
        "  pyisomme convert test.mme second.mme --unit m/s -c '11HEAD000000ACXP'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    convert_parser.add_argument(
        "input_paths",
        nargs="+",
        help="Writable ISO-MME path(s) (.mme/folder/.zip/.tar/.tar.gz)",
    )
    convert_parser.add_argument(
        "--unit",
        required=True,
        dest="unit",
        metavar="UNIT",
        help="Target unit compatible with every selected channel",
    )
    convert_parser.add_argument(
        "-c",
        "--codes",
        nargs="+",
        required=True,
        metavar="CODE_PATTERN",
        help="Quoted 16-character channel-code pattern(s). Wildcards may select "
        "incompatible or unwanted channels",
    )
    convert_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the changes without writing the ISO-MME",
    )


def execute_convert_command(
    parser: argparse.ArgumentParser, options: argparse.Namespace
) -> None:
    # 1. Read Isomme
    paths = [Path(input_path) for input_path in options.input_paths]
    resolved_paths = [path.resolve() for path in paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise ValueError("Each input path may be specified only once.")
    isomme_list = [Isomme().read(path) for path in paths]

    # 2. Validate new unit and channel compatibility
    new_unit = Unit(options.unit)
    for isomme in isomme_list:
        selected_channels = isomme.get_channels(
            *options.codes,
            filter=False,
            calculate=False,
            differentiate=False,
            integrate=False,
        )
        for channel in selected_channels:
            try:
                channel.unit.to(new_unit)
            except UnitConversionError:
                parser.error(
                    f"Unit Conversion Error: {channel.code}: {str(channel.unit):>8} -> {new_unit}"
                )

    # 3. Convert
    for path, isomme in zip(paths, isomme_list):
        print(f"{isomme.test_number} [{path}]")
        for channel in isomme.get_channels(
            *options.codes,
            filter=False,
            calculate=False,
            differentiate=False,
            integrate=False,
        ):
            if channel.unit == new_unit:
                continue
            print(f"{channel.code}: {str(channel.unit):>8} -> {new_unit}")
            channel.convert_unit(new_unit=new_unit)

        # 4. Write
        if options.dry_run:
            print("Dry run: no files were written.")
        else:
            isomme.write(path=path)
