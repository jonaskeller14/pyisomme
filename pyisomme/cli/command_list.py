import argparse

from pyisomme.isomme import Isomme


def add_parser_list(command_parsers: argparse._SubParsersAction) -> None:
    list_parser = command_parsers.add_parser(
        "list",
        help="List channel codes",
        description="List channel codes in one or more ISO-MMEs.",
        epilog="Examples:\n  pyisomme list test.mme\n"
        "  pyisomme list test.mme -c '11HEAD??????AC?P'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    list_parser.add_argument(
        "input_paths",
        nargs="+",
        help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)",
    )
    list_parser.add_argument(
        "-c",
        "--codes",
        nargs="*",
        help="Channel Code Patterns to filter ISO-MMEs",
    )


def execute_list_command(options: argparse.Namespace) -> None:
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
