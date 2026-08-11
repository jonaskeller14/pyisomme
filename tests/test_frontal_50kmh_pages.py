from __future__ import annotations

import unittest

import matplotlib.pyplot as plt
import numpy as np

from tests.report_registry import BY_STEM, build_synthetic


class TestHIC15Pages(unittest.TestCase):
    def test_all_occupants_have_side_by_side_plot_and_table(self) -> None:
        report = build_synthetic(BY_STEM["euro_ncap_frontal_50kmh"])

        page_types = (
            report.Page_Driver_HIC15,
            report.Page_Front_Passenger_HIC15,
            report.Page_Rear_Passenger_HIC15,
        )
        for page_type in page_types:
            with self.subTest(page=page_type.__name__):
                page = next(
                    page
                    for page in report.available_pages
                    if isinstance(page, page_type)
                )
                figure = page.figure((10, 8))
                self.addCleanup(plt.close, figure)

                self.assertEqual(3, len(figure.axes))
                resultant_axis = figure.axes[0]
                table_axis = figure.axes[1]
                hic_axis = figure.axes[2]
                self.assertEqual("HIC15 [-]", hic_axis.get_ylabel())
                self.assertEqual(2, len(hic_axis.lines))
                self.assertEqual(1, len(table_axis.tables))

                x_min, x_max = resultant_axis.get_xlim()
                np.testing.assert_allclose(
                    hic_axis.lines[0].get_xdata(),
                    [x_min, 10, 10, 25, 25, x_max],
                )
                np.testing.assert_allclose(
                    hic_axis.lines[0].get_ydata(),
                    [0, 0, 600, 600, 0, 0],
                )

                table_text = {
                    cell.get_text().get_text()
                    for cell in next(iter(table_axis.tables)).get_celld().values()
                }
                self.assertTrue(
                    {
                        "HIC15",
                        "Start [ms]",
                        "End [ms]",
                        "600.0",
                        "10.00",
                        "25.00",
                        "576.0",
                        "11.00",
                        "26.00",
                    }.issubset(table_text)
                )


if __name__ == "__main__":
    unittest.main()
