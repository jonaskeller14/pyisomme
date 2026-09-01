from __future__ import annotations

import argparse
import logging

from pyisomme.cli.command_code import add_parser_code, execute_code_command
from pyisomme.cli.command_convert import add_parser_convert, execute_convert_command
from pyisomme.cli.command_list import add_parser_list, execute_list_command
from pyisomme.cli.command_merge import add_parser_merge, execute_merge_command
from pyisomme.cli.command_plot import add_parser_plot, execute_plot_command
from pyisomme.cli.command_report import add_parser_report, execute_report_command
from pyisomme.cli.command_set import add_parser_set, execute_set_command


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Read, modify, plot, and report ISO-MME crash-test data.",
        epilog="Examples:\n"
        "  pyisomme list test.mme -c '11HEAD??????AC?P'\n"
        "  pyisomme code 11HEAD0000H3ACXA\n"
        "  pyisomme set test.mme --main-location ABCD -c '11HEAD000000ACXP'\n"
        "  pyisomme convert test.mme --unit mm -c '1?CHST000000DSXP'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
    command_parsers = parser.add_subparsers(dest="command", required=True)

    add_parser_code(command_parsers)
    add_parser_convert(command_parsers)
    add_parser_list(command_parsers)
    add_parser_merge(command_parsers)
    add_parser_plot(command_parsers)
    add_parser_report(command_parsers)
    add_parser_set(command_parsers)

    options = parser.parse_args(argv)

    logging.basicConfig(
        format="%(module)-12s %(levelname)-8s %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S",
        level=logging.INFO if options.verbose else logging.WARNING,
    )

    if options.command == "list":
        execute_list_command(options)
    elif options.command == "code":
        execute_code_command(parser=parser, options=options)
    elif options.command == "merge":
        execute_merge_command(options=options)
    elif options.command == "set":
        execute_set_command(parser=parser, options=options)
    elif options.command == "convert":
        execute_convert_command(parser=parser, options=options)
    elif options.command == "report":
        execute_report_command(parser=parser, options=options)
    elif options.command == "plot":
        execute_plot_command(parser=parser, options=options)


if __name__ == "__main__":
    main()
