from pyisomme.report.page2.cover import CoverPage
from pyisomme.report.page2.criterion_rating_table import (
    CriterionRatingTablePage,
    CriterionTablePage,
    CriterionTableSpec,
    rating_table_spec_for,
)
from pyisomme.report.page2.criterion_values_chart import (
    CriterionValuesChartPage,
    CriterionValuesChartSpec,
    criterion_values_chart_spec_for,
)
from pyisomme.report.page2.criterion_values_table import (
    CriterionValuesTablePage,
    values_table_spec_for,
)
from pyisomme.report.page2.figure import FigurePage
from pyisomme.report.page2.hic import HICPage, HICSpec, hic_spec_for
from pyisomme.report.page2.line_table import LineTablePage, TableData
from pyisomme.report.page2.manual_inputs import (
    ManualInputsPage,
    ManualInputsSpec,
    manual_inputs_spec_for,
)
from pyisomme.report.page2.olc import OLCPage
from pyisomme.report.page2.plot_nxn import (
    ChannelPlotPage,
    ChannelPlotSpec,
    channel_plot_spec_for,
)
from pyisomme.report.page2.report_status import (
    ReportStatusPage,
    ReportStatusSpec,
    report_status_spec_for,
)

__all__ = [
    "ChannelPlotPage",
    "ChannelPlotSpec",
    "CoverPage",
    "CriterionTablePage",
    "CriterionTableSpec",
    "CriterionRatingTablePage",
    "CriterionValuesChartPage",
    "CriterionValuesChartSpec",
    "CriterionValuesTablePage",
    "FigurePage",
    "HICPage",
    "HICSpec",
    "LineTablePage",
    "ManualInputsPage",
    "ManualInputsSpec",
    "OLCPage",
    "ReportStatusPage",
    "ReportStatusSpec",
    "TableData",
    "rating_table_spec_for",
    "channel_plot_spec_for",
    "criterion_values_chart_spec_for",
    "hic_spec_for",
    "manual_inputs_spec_for",
    "report_status_spec_for",
    "values_table_spec_for",
]
