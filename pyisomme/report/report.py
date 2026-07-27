from __future__ import annotations

from pyisomme.isomme import Isomme
from pyisomme.report.page import Page, Page_Cover
from pyisomme.limits import Limits
from pyisomme.report.criterion import Criterion

from pptx import Presentation
from pptx.presentation import Presentation as PptxPresentation
from tqdm.auto import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
import numpy as np
import time
import logging
from pathlib import Path
from typing import Generic, TypeVar, cast


logger = logging.getLogger(__name__)

#: The overall criterion a concrete report is built around. Parameterising ``Report``
#: with it is what makes ``report.overall(isomme).criterion_driver...`` type-check —
#: a concrete report declares e.g. ``class X(Report["X.Criterion_Overall"])``.
C = TypeVar("C", bound=Criterion)


class Report(Generic[C]):
    name: str | None = None
    title: str
    isomme_list: list[Isomme]
    limits: dict[Isomme, Limits]
    criterion_overall: dict[Isomme, C]
    pages: list[Page]
    protocol: str | None = None
    protocols: dict[str, str] = {}

    def __init__(self, isomme_list: list[Isomme], title: str = "Unnamed Report", protocol: str | None = None) -> None:
        self.isomme_list = isomme_list
        self.title = title

        if protocol is not None:
            assert protocol in self.protocols.keys(), \
                f"Protocol {protocol} not available. Available protocols: {list(self.protocols.keys())}"
            self.protocol = protocol

        self.limits = {isomme: Limits(name=self.name or "Unnamed Limits", limit_list=[]) for isomme in isomme_list}

        self.criterion_overall = {}
        for isomme in self.isomme_list:
            # A concrete report's inner ``Criterion_Overall`` *is* the ``C`` it parameterises
            # ``Report`` with, but the language cannot express "this inner class is type[C]".
            self.criterion_overall[isomme] = cast(C, self.Criterion_Overall(self, isomme))

        self.pages = [
            Page_Cover(self),
        ]

    def overall(self, isomme: Isomme) -> C:
        """The overall criterion for ``isomme``, typed as the concrete report's own tree."""
        return self.criterion_overall[isomme]

    def calculate(self) -> Report[C]:
        with logging_redirect_tqdm():
            for isomme in tqdm(self.isomme_list, desc="Calculate Report"):
                logger.info(f"Calculate Criteria for {isomme}")
                self.criterion_overall[isomme].calculate()
        return self

    def print_results(self) -> Report[C]:
        def print_subcriteria_results(criterion: Criterion, intend: str = "\t") -> None:
            print(f"{intend}{criterion.name if criterion.name is not None else criterion.__class__.__name__}: "
                  f"Value={criterion.value:.5g} [{criterion.channel.unit if criterion.channel is not None else ''}] "
                  f"Rating={criterion.rating:.5g}")

            subcriteria = [getattr(criterion, a) for a in dir(criterion) if isinstance(getattr(criterion, a), Criterion)]
            for subcriterion in subcriteria:
                print_subcriteria_results(subcriterion, intend=f"{intend}\t")

        for isomme in self.isomme_list:
            print(isomme)
            print_subcriteria_results(self.criterion_overall[isomme])
        return self

    def __repr__(self) -> str:
        return f"Report(title='{self.title}', name='{self.name}')"

    class Criterion_Overall(Criterion):
        def calculation(self) -> None:
            pass

    def export_pptx(self, path: str | Path, template: str | Path | None = None) -> Report[C]:
        presentation: PptxPresentation = Presentation(template)

        with logging_redirect_tqdm():
            for page_number, page in enumerate(tqdm(self.pages, desc="Construct Pages")):
                logger.info(f"{page_number}:{page.name}")
                page.__init__(page.report)  # update. report could be changed since init  # TODO: TEST!
                page.construct(presentation)

        while True:
            try:
                presentation.save(path)
                break
            except PermissionError as e:
                logger.critical(e)
                time.sleep(3)
        logger.info(f"pptx successfully exported: {path}")
        return self


class MetaReport(Report[Criterion]):
    reports: list[Report]
    rating: float = np.nan

    def calculate(self) -> MetaReport:
        for report in self.reports:
            report.calculate()
        self.calculation()
        return self

    def calculation(self) -> None:
        pass

    def print_results(self) -> MetaReport:
        for report in self.reports:
            report.print_results()
        return self
