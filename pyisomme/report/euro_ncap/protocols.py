from datetime import date

from pyisomme.report.report_protocol import ReportProtocol


PROTOCOL_9_3 = ReportProtocol(
    version="9.3",
    name="Version 9.3 - Assessment Protocol Adult Occupant Protection",
    date=date(2023, 12, 5),
    sources=("references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf",),
)

PROTOCOL_VTC_1_0 = ReportProtocol(
    version="1.0",
    name="Version 1.0 - Virtual Far Side Simulation & Assessment Protocol",
    date=date(2023, 6, 15),
    sources=(
        "references/Euro-NCAP/euro-ncap-vtc-simulation-and-assessment-protocol-v10.pdf",
    ),
)

PROTOCOL_FARSIDE_2_4 = ReportProtocol(
    version="2.4",
    name="Version 2.4 - Far Side Occupant Test & Assessment Protocol",
    date=date(2023, 5, 12),
    sources=(
        "references/Euro-NCAP/euro-ncap-far-side-test-and-assessment-protocol-v24.pdf",
    ),
)
