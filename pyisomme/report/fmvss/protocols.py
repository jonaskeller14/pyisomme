from datetime import date

from pyisomme.report.report_protocol import ReportProtocol

PROTOCOL_2022_10_14 = ReportProtocol(
    version="2022-10-14",
    name="49 CFR 571.208 - Standard No. 208; Occupant crash protection",
    date=date(2022, 10, 14),
    sources=("references/FMVSS/B04.w8z738446fxw0xa22it81751sl8noj63801729751.pdf",),
)

PROTOCOL_214_2026_07_06 = ReportProtocol(
    version="2026-07-06",
    name="49 CFR 571.214 - Standard No. 214; Side impact protection",
    date=date(2026, 7, 6),
    sources=("references/FMVSS/§_571.214_Side_Impact_Protection.pdf",),
)
