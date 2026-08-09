from datetime import date

from pyisomme.report.report_protocol import ReportProtocol


protocol_r94_2022 = ReportProtocol(
    version="2022",
    name="Regulation No. 94: Uniform provisions concerning the approval of vehicles with regard to the protection of the occupants in the event of a frontal collision",
    date=date(2022, 12, 29),
    sources=("references/UN-R94/B04.ckg738531jagx232x0m74928e357ft63809066928.pdf",),
)

protocol_r95_2023 = ReportProtocol(
    version="2023",
    name="Regulation No. 95: Uniform provisions concerning the approval of vehicles with regard to the protection of the occupants in the event of a lateral collision",
    date=date(2023, 9, 12),
    sources=("references/UN-R95/B04.qtu738801n2c4t17t97571269on1fn63832377126.pdf",),
)

protocol_r135_2016 = ReportProtocol(
    version="2016",
    name="Regulation No. 135: Uniform provisions concerning the approval of vehicles with regard to their Pole Side Impact performance (PSI)",
    date=date(2016, 2, 5),
    sources=("references/UN-R135/B04.hcu736002y3cij636z760633yex36763590547033.pdf",),
)

protocol_r137_2016 = ReportProtocol(
    version="2016",
    name="Regulation No. 137: Uniform provisions concerning the approval of passenger cars in  the  event  of  a  frontal  collision  with  focus  on  the  restraint system",
    date=date(2016, 6, 22),
    sources=("references/UN-R137/R137e.pdf",),
)

protocol_r137_2023 = ReportProtocol(
    version="2023",
    name="Regulation No. 137: Uniform provisions concerning the approval of passenger cars in  the  event  of  a  frontal  collision  with  focus  on  the  restraint system",
    date=date(2023, 9, 12),
    sources=("references/UN-R137/B04.80k7388018sqd01x91957452w3utcf63832377452.pdf",),
)
