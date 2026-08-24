from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from pyisomme.isomme import Isomme
from pyisomme.plotting.plot_line import Plot_Line

if TYPE_CHECKING:
    from pyisomme.channel import Channel


def add_parser_plot(
    command_parsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    plot_parser = command_parsers.add_parser(
        "plot",
        help="Plot Channels",
        description="Plot one or more selected channels. At least one channel-code "
        "pattern is required.",
        epilog="Examples:\n"
        "  pyisomme plot test.mme -c '11HEAD??????AC?P'\n"
        "  pyisomme plot test.mme -c '24HEAD??????ACRA' --calculate -n 4",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    plot_parser.add_argument(
        "input_paths",
        nargs="+",
        help="ISO-MME Path (.mme/folder/.zip/.tar/.tar.gz/...)",
    )
    plot_parser.add_argument(
        "-c",
        "--codes",
        nargs="+",
        required=True,
        metavar="CODE_PATTERN",
        help="Quoted 16-character channel-code pattern(s) to plot",
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


def execute_plot_command(
    parser: argparse.ArgumentParser, options: argparse.Namespace
) -> None:
    if options.calculate:
        isomme_list = [Isomme().read(input_path) for input_path in options.input_paths]
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
        {isomme: [list(channels)] for isomme, channels in channels_by_isomme.items()},
        xlim=options.xlim,
        ylim=options.ylim,
        legend=options.legend,
    ).show()
