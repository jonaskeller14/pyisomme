from datetime import date

from pyisomme.report.report_protocol import ReportProtocol


PROTOCOL_MODERATE_VII = ReportProtocol(
    version="II",
    name="Moderate Overlap Crashworthiness Evaluation 2.0 Rating Guidelines",
    date=date(2024, 5, 1),
    sources=("references/IIHS/Moderate 2.0 Rating guidelines Phase 2_FINAL_May2024.pdf",),
)

PROTOCOL_MODERATE_VIII = ReportProtocol(
    version="III",
    name="Moderate Overlap Crashworthiness Evaluation 2.0 Rating Guidelines",
    date=date(2026, 2, 1),
    sources=("references/IIHS/Moderate_2.0_rating_guidelines.pdf",),
)

PROTOCOL_SMALL_OVERLAP_VII = ReportProtocol(
    version="VII",
    name="Small Overlap Frontal Crashworthiness Evaluation Rating Protocol",
    date=date(2024, 4, 1),
    sources=("references/IIHS/small_overlap_rating_protocol.pdf",),
)

PROTOCOL_SIDE_IMPACT_IV = ReportProtocol(
    version="IV",
    name="Side Impact Crashworthiness Evaluation 2.0 Rating Guidelines",
    date=date(2024, 4, 1),
    sources=("references/IIHS/side_impact_2.0_rating_guidelines.pdf",),
)
