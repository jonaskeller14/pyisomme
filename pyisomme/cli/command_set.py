from __future__ import annotations

import argparse
from pathlib import Path

from pyisomme.code import CODE_COMPONENTS
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


def add_parser_set(
    command_parsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    set_parser = command_parsers.add_parser(
        "set",
        help="Set metadata fields on selected channels in place",
        description="Read an ISO-MME, set one or more metadata fields on matching channels, and write "
        "the complete ISO-MME back in place. This relabels a unit but does not change "
        "the numeric data.\n\n" + CODE_COMPONENT_HELP,
        epilog="Examples:\n"
        "  pyisomme set test.mme --unit mm -c '13CHST000000DSXP'\n"
        "  pyisomme set test.mme --main-location ABCD -c '11HEAD000000ACXP'\n"
        "  pyisomme set test.mme --test-object 3 --unit mm --filter-class A "
        "-c 'M*'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    set_parser.add_argument(
        "input_paths",
        nargs="+",
        help="Writable ISO-MME path(s) (.mme/folder/.zip/.tar/.tar.gz)",
    )
    for code_component, _ in CODE_COMPONENTS:
        set_parser.add_argument(
            f"--{code_component.replace('_', '-')}",
            dest=code_component,
            metavar=code_component.upper(),
            help=(f"Set '{code_component}' in the channel code"),
            default=None,
        )
    set_parser.add_argument(
        "--unit",
        dest="unit",
        metavar="UNIT",
        help="Relabel the unit without converting numeric data",
    )
    set_parser.add_argument(
        "-c",
        "--codes",
        nargs="+",
        required=True,
        metavar="CODE_PATTERN",
        help="Quoted 16-character channel-code pattern(s). Wildcards may select "
        "incompatible or unwanted channels",
    )
    set_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the changes without writing the ISO-MME",
    )


def execute_set_command(
    parser: argparse.ArgumentParser, options: argparse.Namespace
) -> None:
    # 1. Read Isomme
    paths = [Path(input_path) for input_path in options.input_paths]
    resolved_paths = [path.resolve() for path in paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise ValueError("Each input path may be specified only once.")
    isomme_list = [Isomme().read(path) for path in paths]

    # 2. Validate
    if options.unit is not None:
        Unit(options.unit)

    # 3. Set
    for path, isomme in zip(paths, isomme_list):
        print(f"{isomme.test_number} [{path}]")
        for channel in isomme.get_channels(
            *options.codes,
            filter=False,
            calculate=False,
            differentiate=False,
            integrate=False,
        ):
            old_channel_code = str(channel.code)
            old_channel_unit = f"[{channel.unit}]"

            if options.unit is not None:
                channel.set_unit(options.unit)
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

            new_channel_code = channel.code
            new_channel_unit = f"[{channel.unit}]"

            print(
                f"{old_channel_unit:>8} {old_channel_code} -> {new_channel_code} {new_channel_unit:<8}"
            )

        # 4. Write
        if options.dry_run:
            print("Dry run: no files were written.")
        else:
            isomme.write(path=path)
