from __future__ import annotations

from typing import TYPE_CHECKING, Any
from typing_extensions import override
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np

from pyisomme.isomme import Isomme
from pyisomme.limits import limit_list_sort
from pyisomme.report.criterion import Criterion
from pyisomme.report.page.figure import Page_Figure

if TYPE_CHECKING:
    from pyisomme.report.report import Report


def limit_x(criterion: Criterion) -> float:
    """x at which a criterion's limits are evaluated; 0 when it has no channel."""
    if criterion.channel is None:
        return 0.0
    return criterion.limits.get_limit_min_x(criterion.channel)


class Page_Criterion_Values_Chart(Page_Figure):
    criteria: dict[Isomme, list[Criterion]]

    def __init__(self, report: Report[Any]) -> None:
        super().__init__(report)
        self.criteria = {}

    @override
    def figure(self, figsize: tuple[float, float]) -> Figure:
        fig, ax = plt.subplots(figsize=figsize, layout="constrained")

        bar_width = 0.8 / len(self.criteria)
        x_labels = [c.name for c in list(self.criteria.values())[0]]
        x = np.arange(len(x_labels))
        x_offsets = np.linspace(
            -0.4 + bar_width / 2, 0.4 - bar_width / 2, len(self.criteria)
        )

        unique_limits = np.zeros(len(x_labels), dtype=bool)
        line_values = np.array(
            [
                [abs(c.value) for c in criteria]
                for isomme, criteria in self.criteria.items()
            ]
        )

        # Same limits?
        for idx, c1 in enumerate(list(self.criteria.values())[0]):
            for c2_list in list(self.criteria.values())[1:]:
                c2 = c2_list[idx]
                x_limit1 = limit_x(c1)
                x_limit2 = limit_x(c2)
                if not np.all(
                    [
                        abs((l1.func(x_limit1) - l2.func(x_limit2)) / l1.func(x_limit1))
                        < 1e-6
                        for l1, l2 in zip(
                            limit_list_sort(c1.limits.limit_list),
                            limit_list_sort(c2.limits.limit_list),
                        )
                    ]
                ):
                    unique_limits[idx] = True
                    break

        # Calculate Column Factor
        col_factors = np.nanmax(1.1 * np.abs(line_values), axis=0)

        for criteria in self.criteria.values():
            for idx_col, criterion in enumerate(criteria):
                if not criterion.limits.limit_list:
                    continue

                x_limit = limit_x(criterion)
                col_factor_limit = 1.1 * np.nanmax(
                    [
                        abs(limit.func(x_limit))
                        if not np.isinf(abs(limit.func(x_limit)))
                        else np.nan
                        for limit in criterion.limits.limit_list
                    ]
                )
                if not np.isnan(col_factor_limit):
                    col_factors[idx_col] = np.nanmax(
                        [col_factor_limit, col_factors[idx_col]]
                    )

        # Plot Bars
        for idx_isomme, criteria in enumerate(self.criteria.values()):
            for idx_col, criterion in enumerate(criteria):
                limits = limit_list_sort(criterion.limits.limit_list, sym=True)

                x_limit = limit_x(criterion)
                limit_values = [
                    abs(limit.func(x_limit))
                    if not np.isinf(abs(limit.func(x_limit)))
                    else col_factors[idx_col]
                    for limit in limits
                ]

                for idx, (limit, limit_value) in enumerate(zip(limits, limit_values)):
                    if idx == 0:
                        bar_bottom = 0
                        bar_height = limit_value / col_factors[idx_col]
                    elif idx < len(limits) - 1:
                        if (limit.lower and limit.func(0) >= 0) or (
                            limit.upper and limit.func(0) < 0
                        ):
                            bar_bottom = limit_value / col_factors[idx_col]
                            bar_height = (
                                limit_values[idx + 1] - limit_value
                            ) / col_factors[idx_col]
                        elif (limit.upper and limit.func(0) >= 0) or (
                            limit.lower and limit.func(0) < 0
                        ):
                            bar_bottom = limit_values[idx - 1] / col_factors[idx_col]
                            bar_height = (
                                limit_value - limit_values[idx - 1]
                            ) / col_factors[idx_col]
                        else:
                            continue
                    else:  # idx == len(limits) - 1
                        bar_bottom = limit_value / col_factors[idx_col]
                        bar_height = 1 - limit_value / col_factors[idx_col]

                    ax.bar(
                        x=x[idx_col] + x_offsets[idx_isomme],
                        bottom=bar_bottom,
                        height=bar_height,
                        color=limit.color,
                        width=bar_width,
                        alpha=0.5,
                        label=limit.name,
                    )

        # Plot Lines
        for idx, isomme in enumerate(self.report.isomme_list):
            ax.plot(
                x + unique_limits * x_offsets[idx],
                line_values[idx, :] / col_factors,
                marker="o",
                label=isomme.test_number,
                linewidth=3,
                markersize=8,
            )

        ax.set_xticks(x, x_labels, rotation=30, ha="right")
        ax.get_yaxis().set_visible(False)

        # Legend (Delete duplicates)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(
            by_label.values(), by_label.keys(), bbox_to_anchor=(1, 1), loc="upper left"
        )

        return fig
