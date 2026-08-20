"""
US-NCAP meta report — **unfinished stub, not usable yet.**

It composes load-case sub-reports the way :class:`~pyisomme.report.euro_ncap.euro_ncap.EuroNCAP`
does, but none of those sub-reports exist: ``us_ncap/frontal_56kmh.py`` is itself an
unfinished stub and ``us_ncap/side_mdb.py`` / ``us_ncap/side_pole.py`` define no report
class at all. ``__init__`` previously iterated ``self.reports``, which was never assigned,
and died with ``AttributeError`` (review Appendix A6); it now says so explicitly.

Out of scope for the report refactor (plan Step 2) — see the sibling module docstring.
"""

from __future__ import annotations

from typing import Any

from pyisomme.report.meta_report import MetaReport


class USNCAP(MetaReport):
    _name = "US-NCAP"
    title = "US-NCAP"

    def __init__(
        self,
        frontal_56kmh: list,
        frontal_mpdb: list,
        side_pole: list,
        side_barrier: list,
        side_farside: list,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        raise NotImplementedError(
            "USNCAP is an unfinished stub: none of its load-case sub-reports are "
            "implemented (frontal_56kmh is a stub; side_mdb and side_pole define no "
            "report class). See the module docstring."
        )
