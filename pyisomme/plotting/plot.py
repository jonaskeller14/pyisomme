from __future__ import annotations

from abc import ABC, abstractmethod
import logging

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


class Plot(ABC):
    colors: list[str] = list(mcolors.TABLEAU_COLORS.values()) # pyright: ignore[reportAttributeAccessIssue]
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

    @abstractmethod
    def plot(self) -> Figure:
        ...
