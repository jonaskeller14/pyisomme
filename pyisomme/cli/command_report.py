from __future__ import annotations

import argparse
from pathlib import Path

from pyisomme.isomme import Isomme
from pyisomme.report import REPORTS

OUTPUT_SUFFIXES = {".html", ".pdf", ".pptx"}


def _output_path(value: str) -> Path:
    path = Path(value)
    if path.suffix.lower() not in OUTPUT_SUFFIXES:
        formats = ", ".join(sorted(OUTPUT_SUFFIXES))
        raise argparse.ArgumentTypeError(
            f"unsupported report output extension {path.suffix or '(none)'!r}; "
            f"expected one of: {formats}"
        )
    return path


def add_parser_report(
    command_parsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    report_parser = command_parsers.add_parser(
        "report",
        help="Calculate and export a report",
        epilog=(
            "Examples:\n"
            "  pyisomme report EuroNCAP_Frontal_MPDB test.mme -o report.pptx\n"
            "  pyisomme report EuroNCAP_Frontal_MPDB test.mme "
            "-o report.html -o report.pdf -o report.pptx"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    report_parser.add_argument(
        "report_name",
        choices=[report.__name__ for report in REPORTS],
        help="Report name",
    )
    report_parser.add_argument(
        "input_paths",
        nargs="+",
        help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)",
    )
    report_parser.add_argument(
        "-o",
        "--output",
        dest="output_paths",
        action="append",
        required=True,
        type=_output_path,
        metavar="PATH",
        help="Output path; repeat for .html, .pdf, and/or .pptx",
    )
    report_parser.add_argument(
        "--template", type=Path, help="PowerPoint template used for the .pptx output"
    )
    report_parser.add_argument(
        "--crop",
        nargs=2,
        type=float,
        metavar=("START", "STOP"),
        help="Crop ISO-MME channels to x-min to x-max e.g. (--crop 0.0 0.15)",
    )


def execute_report_command(
    parser: argparse.ArgumentParser, options: argparse.Namespace
) -> None:
    suffixes = [path.suffix.lower() for path in options.output_paths]
    if len(suffixes) != len(set(suffixes)):
        parser.error("report accepts at most one output path per format")
    if options.template is not None and ".pptx" not in suffixes:
        parser.error("--template requires a .pptx output")

    isomme_list = [Isomme().read(input_path) for input_path in options.input_paths]
    if options.crop:
        for isomme in isomme_list:
            isomme.crop(options.crop)
    report = {report.__name__: report for report in REPORTS}[options.report_name](
        isomme_list
    )
    report.calculate()
    report.export(*options.output_paths, template=options.template)
