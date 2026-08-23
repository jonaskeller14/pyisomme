from __future__ import annotations

import argparse

from pyisomme.code import Code


def add_parser_code(
    command_parsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    code_parser = command_parsers.add_parser(
        "code",
        help="Describe a 16-character channel code",
        description="Decode a channel code using the ISO-MME codification. The output "
        "includes each component's meaning and its default unit.",
        epilog="Example:\n  pyisomme code 11HEAD0000H3ACXA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    code_parser.add_argument(
        "code",
        metavar="CHANNEL_CODE",
        help="16-character channel code or channel-code pattern",
    )


def execute_code_command(
    parser: argparse.ArgumentParser, options: argparse.Namespace
) -> None:
    try:
        code = Code(options.code)
    except ValueError as error:
        parser.error(str(error))
    print(f"Code: {code}")
    for name, value in code.get_info().items():
        print(f"{name}: {value}")
    print(f"Default unit: {code.get_default_unit()}")
