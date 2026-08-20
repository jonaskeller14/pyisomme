# matplotlib 3.7.5 ships no stubs, so Pylance falls back on its own bundled ones, which are stricter
# than (and lag behind) the runtime API this module targets — e.g. mcolors.TABLEAU_COLORS is absent
# from them although it exists at runtime. None of that is a real defect here, so the two rule
# families it produces are switched off rather than papered over at every call site.
# pyright: reportArgumentType=false, reportAttributeAccessIssue=false
from __future__ import annotations

import logging

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class Plot:
    colors: list[str] = list(mcolors.TABLEAU_COLORS.values())
    linestyles: list[str | tuple] = [
        "-",
        "--",
        "-.",
        ":",
        (0, (10, 3)),
        (0, (5, 1)),
    ]
    isomme_list: list
    figsize: tuple[float, float]
    fig: Figure
    nrows: int = 1
    ncols: int = 1

    def __init__(
        self, figsize: tuple[float, float], nrows: int | None, ncols: int | None
    ):
        self.figsize = figsize
        if nrows is not None:
            self.nrows = nrows
        if ncols is not None:
            self.ncols = ncols

    def show(self, *args, **kwargs) -> Plot:
        plt.show(*args, **kwargs)
        return self
