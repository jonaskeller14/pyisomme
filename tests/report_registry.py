"""One registry and deterministic fixture builder for every concrete report."""
from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
import importlib
from pathlib import Path

import pyisomme
from pyisomme.code import Code
from pyisomme.report.report import Report


@dataclass(frozen=True)
class ReportSpec:
    stem: str
    module: str
    class_name: str
    n_isomme: int = 1

    @property
    def report_class(self) -> type[Report]:
        module = importlib.import_module(f"pyisomme.report.{self.module}")
        return getattr(module, self.class_name)


# Every usable concrete Report with its own Overall tree. The unfinished US-NCAP
# stub is deliberately excluded; ``test_every_report_module_is_registered`` below
# guards this list against silently going stale.
REPORTS = (
    ReportSpec("correlation", "correlation.correlation", "Correlation", 2),
    ReportSpec("euro_ncap_frontal_50kmh", "euro_ncap.frontal_50kmh", "EuroNCAP_Frontal_50kmh", 2),
    ReportSpec("euro_ncap_frontal_mpdb", "euro_ncap.frontal_mpdb", "EuroNCAP_Frontal_MPDB", 2),
    ReportSpec("euro_ncap_side_barrier", "euro_ncap.side_barrier", "EuroNCAP_Side_Barrier"),
    ReportSpec("euro_ncap_side_farside", "euro_ncap.side_farside", "EuroNCAP_Side_FarSide"),
    ReportSpec("euro_ncap_side_farside_vtc", "euro_ncap.side_farside_vtc", "EuroNCAP_Side_Farside_VTC", 2),
    ReportSpec("euro_ncap_side_pole", "euro_ncap.side_pole", "EuroNCAP_Side_Pole"),
    ReportSpec("iihs_frontal_odb", "iihs.frontal_odb", "IIHS_Frontal_ODB"),
    ReportSpec("iihs_frontal_small_overlap", "iihs.frontal_small_overlap", "IIHS_Frontal_Small_Overlap"),
    ReportSpec("un_frontal_50kmh_r137", "un.frontal_50kmh_r137", "UN_Frontal_50kmh_R137"),
    ReportSpec("un_frontal_56kmh_odb_r94", "un.frontal_56kmh_odb_r94", "UN_Frontal_56kmh_ODB_R94"),
    ReportSpec("un_side_barrier_r95", "un.side_barrier_r95", "UN_Side_Barrier_R95"),
    ReportSpec("un_side_pole_r135", "un.side_pole_r135", "UN_Side_Pole_R135"),
)

BY_STEM = {spec.stem: spec for spec in REPORTS}
BY_CLASS = {spec.class_name: spec for spec in REPORTS}

EXCLUDED_MODULES = {
    "report": "the base Report's empty default tree, not a protocol report",
    "us_ncap.frontal_56kmh": "unfinished stub; construction raises NotImplementedError",
}


def build_empty(spec: ReportSpec) -> Report:
    """Build a report for definition-only tests; no external fixture data needed."""
    isommes = [pyisomme.Isomme(test_number=f"T{i}") for i in range(spec.n_isomme)]
    return spec.report_class(isommes)


def _concretise(pattern: str) -> str:
    """Turn one 16-character fnmatch pattern into a deterministic matching code."""
    chars: list[str] = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "?":
            chars.append("1" if len(chars) < 2 else "B" if len(chars) == 15 else "0")
            index += 1
        elif char == "[":
            close = pattern.find("]", index + 1)
            if close < 0:
                chars.append("0")
                index += 1
            else:
                choices = pattern[index + 1:close].lstrip("!")
                chars.append(choices[0] if choices else "0")
                index = close + 1
        elif char == "*":
            chars.extend("0" for _ in range(16 - len(chars)))
            index += 1
        else:
            chars.append(char)
            index += 1

    code = "".join(chars[:16]).ljust(16, "0")
    if not fnmatch(code, pattern):
        raise ValueError(f"cannot make a concrete channel code for {pattern!r}: {code!r}")
    return code


def _range_for(code: Code, variant: int) -> tuple[float, float]:
    """Plausible SI values that exercise more than the all-green limit bands."""
    ranges = {
        "AC": (-100.0, 800.0),
        "AA": (-100.0, 100.0),
        "AV": (-5.0, 5.0),
        "DS": (-0.06, 0.01),
        "FO": (-5000.0, 5000.0),
        "MO": (-80.0, 80.0),
        "VE": (-1.5, 0.5),
    }
    low, high = ranges.get(code.physical_dimension, (0.2, 1.1))
    if code.main_location == "HICR":
        low, high = 400.0, 800.0
    scale = 1.0 - 0.04 * variant
    return low * scale, high * scale


def _add_channel(isomme: pyisomme.Isomme, pattern: str, variant: int) -> None:
    if not pattern or isomme.get_channel(pattern, filter=False, calculate=False,
                                         differentiate=False, integrate=False) is not None:
        return
    code = Code(_concretise(pattern))
    isomme.channels.append(pyisomme.create_sample(
        code,
        t_range=(-0.02, 0.12, 300),
        y_range=_range_for(code, variant),
        unit=code.get_default_unit(),
    ))


_CORRELATION_CODES = (
    "11HEAD0000H3ACXD",
    "11CHST0000H3DSXD",
    "11NECKUP00H3FOZD",
)

_VTC_CODES = tuple(
    f"11{location}{axis}{filter_class}"
    for location, filter_class in (
        ("HEAD0000H3AV", "A"),
        ("THSP0400H3AC", "A"),
        ("THSP1200H3AC", "A"),
        ("PELV0000H3AC", "A"),
    )
    for axis in "XYZ"
) + tuple(f"14BPILLO0000AC{axis}C" for axis in "XYZ") + ("11SEBE0003B3FO0C",)

# Some calculations deliberately request a concrete derived/output code while
# their Limit applies to all filter classes or result directions. Seeding these
# requests directly keeps the synthetic fixture about report scoring, not about
# whether a particular core calculation provider happens to be available.
_DIRECT_PATTERNS = (
    "?1HEAD??00??ACRA", "?3HEAD??00??ACRA", "?6HEAD??00??ACRA",
    "?1HEAD003C??ACRX", "?3HEAD003C??ACRX", "?6HEAD003C??ACRX",
    "?1CHST003C??ACRX",
    "?1FOOT0000??ACRA",
    "?1RIBSLE00??DSYC", "?1ABDOLE00??FOYB",
    "11THSP123C??ACRX",
    "M?MBAR0000??VEXA",
    "?1HICR0015??00RX",
)


def build_synthetic(spec: ReportSpec) -> Report:
    """
    Build one calculated-results fixture without depending on untracked ``data/``.

    Limit code patterns provide the report's measurable inputs. Correlation and
    VTC are the two data-shaped trees, so their explicit comparison channels are
    seeded before construction as well.
    """
    isommes = [pyisomme.Isomme(test_number=f"{spec.stem}-{i}")
               for i in range(spec.n_isomme)]

    if spec.stem == "correlation":
        for variant, isomme in enumerate(isommes):
            for code in _CORRELATION_CODES:
                _add_channel(isomme, code, variant)
    elif spec.stem == "euro_ncap_side_farside_vtc":
        for variant, isomme in enumerate(isommes):
            for code in _VTC_CODES:
                _add_channel(isomme, code, variant)

    for variant, isomme in enumerate(isommes):
        for pattern in _DIRECT_PATTERNS:
            _add_channel(isomme, pattern, variant)

    report = spec.report_class(isommes)
    for variant, isomme in enumerate(isommes):
        for _, criterion in report.overall(isomme).walk():
            for limit in criterion.limits.limit_list:
                for pattern in limit.code_patterns or ():
                    _add_channel(isomme, pattern, variant)
    return report


def build_euro_ncap_synthetic() -> Report:
    """Build the available EuroNCAP MetaReport from the same complete fixtures."""
    from pyisomme.report.euro_ncap import EuroNCAP

    def isommes(stem: str) -> list[pyisomme.Isomme]:
        return build_synthetic(BY_STEM[stem]).isomme_list

    return EuroNCAP(
        frontal_50kmh=[isommes("euro_ncap_frontal_50kmh")],
        frontal_mpdb=[isommes("euro_ncap_frontal_mpdb")],
        side_pole=[isommes("euro_ncap_side_pole")],
        side_barrier=[isommes("euro_ncap_side_barrier")],
        side_farside=[isommes("euro_ncap_side_farside")],
    )


def uncovered_report_modules() -> list[str]:
    """Report modules defining an Overall tree but missing from this registry."""
    covered = {spec.module for spec in REPORTS} | set(EXCLUDED_MODULES)
    root = Path(pyisomme.report.__file__).parent
    missing = []
    for path in sorted(root.rglob("*.py")):
        if "\nclass Overall(Criterion):" not in path.read_text(encoding="utf-8"):
            continue
        dotted = ".".join(path.relative_to(root).with_suffix("").parts)
        if dotted not in covered:
            missing.append(dotted)
    return missing
