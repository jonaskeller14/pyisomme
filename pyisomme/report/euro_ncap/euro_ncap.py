from __future__ import annotations

from pyisomme.report.meta_report import MetaReport
from pyisomme.report.euro_ncap.frontal_50kmh import EuroNCAP_Frontal_50kmh
from pyisomme.report.euro_ncap.frontal_mpdb import EuroNCAP_Frontal_MPDB
from pyisomme.report.euro_ncap.side_pole import EuroNCAP_Side_Pole
from pyisomme.report.euro_ncap.side_barrier import EuroNCAP_Side_Barrier
from pyisomme.report.euro_ncap.side_farside import EuroNCAP_Side_FarSide

import numpy as np


class EuroNCAP(MetaReport):
    """
    The Adult Occupant Protection score, as far as the modelled load cases reach.

    §2 sums the individual test scores into one Adult Occupant Protection score.
    Of its parts this report models the frontal MPDB (§3.4, 8 points), the frontal
    full width (§4.3, 8 points) and the side section (§5.3, 12 points for barrier
    and pole together plus 4 for far side) — 32 points in total.

    TODO(protocol): the published Adult Occupant Protection score is out of 38 —
      whiplash (§6.3, 3 points front + 1 point rear) and rescue, extrication and
      safety (§7, 2 points) are not modelled by pyisomme, so :attr:`rating` is
      deliberately *not* expressed as the Euro NCAP percentage.
    """
    _name = "Euro-NCAP"
    title = "Euro-NCAP"

    #: §5.3: "the individual scores ... for the side impact test (max. 16 points)
    #: and the pole test (max. 16 points) are summed and scaled down to 12 points".
    MAX_SIDE_BARRIER_AND_POLE_RAW = 32.
    MAX_SIDE_BARRIER_AND_POLE = 12.
    #: §5.3: "the total score for far side occupant protection is limited to 4 points".
    MAX_FAR_SIDE = 4.

    #: 8 (§3.4) + 8 (§4.3) + 12 + 4 (§5.3). See the class docstring on the missing 6.
    max_rating = 32.

    def __init__(
        self,
        frontal_50kmh: EuroNCAP_Frontal_50kmh,
        frontal_mpdb: EuroNCAP_Frontal_MPDB,
        side_pole: EuroNCAP_Side_Pole,
        side_barrier: EuroNCAP_Side_Barrier,
        side_farside: EuroNCAP_Side_FarSide,
        title: str = "Euro-NCAP",
    ) -> None:
        self.frontal_50kmh = frontal_50kmh
        self.frontal_mpdb = frontal_mpdb
        self.side_pole = side_pole
        self.side_barrier = side_barrier
        self.side_farside = side_farside

        super().__init__(
            reports={
                "frontal_50kmh": frontal_50kmh,
                "frontal_mpdb": frontal_mpdb,
                "side_pole": side_pole,
                "side_barrier": side_barrier,
                "side_farside": side_farside,
            },
            title=title,
        )

    def aggregate_results(self) -> None:
        frontal_mpdb = self.sub_rating(self.frontal_mpdb)
        frontal_50kmh = self.sub_rating(self.frontal_50kmh)
        side_barrier = self.sub_rating(self.side_barrier)
        side_pole = self.sub_rating(self.side_pole)
        far_side = self.sub_rating(self.side_farside)

        # §5.3: barrier and pole (16 points each, after their modifiers) are summed
        # and scaled down to 12. `interp` clamps rather than extrapolates, so a
        # capped-to-zero test cannot drag the section negative.
        side = float(np.interp(side_barrier + side_pole,
                               [0., self.MAX_SIDE_BARRIER_AND_POLE_RAW],
                               [0., self.MAX_SIDE_BARRIER_AND_POLE],
                               left=0., right=self.MAX_SIDE_BARRIER_AND_POLE))
        # §5.3: far side is limited to 4 points. EuroNCAP_Side_FarSide already
        # scales its own 12 down to 4, so this only guards the bound.
        far_side = float(np.min([far_side, self.MAX_FAR_SIDE]))

        self.ratings = {
            "Frontal MPDB (§3.4)": frontal_mpdb,
            "Frontal Full Width (§4.3)": frontal_50kmh,
            "Side Barrier + Pole (§5.3)": side,
            "Far Side (§5.3)": far_side,
        }
        # Plain sum, not nansum: a load case with no data leaves the total unknown
        # rather than silently scoring it zero.
        self.rating = float(np.sum(list(self.ratings.values())))
