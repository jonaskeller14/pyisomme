import argparse

from pyisomme.isomme import Isomme
from pyisomme.report import REPORTS


def add_parser_report(
    command_parsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    report_parser = command_parsers.add_parser(
        "report",
        help="Create a Report",
        epilog="Example:\n  pyisomme report EuroNCAP_Frontal report.pptx test.mme",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
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


def execute_report_command(options: argparse.Namespace) -> None:
    isomme_list = [Isomme().read(input_path) for input_path in options.input_paths]
    if options.crop:
        for isomme in isomme_list:
            isomme.crop(options.crop)
    report = {report.__name__: report for report in REPORTS}[options.report_name](
        isomme_list
    )
    report.calculate()
    report.export_pptx(options.report_path, template=options.template)
