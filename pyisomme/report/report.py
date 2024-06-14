from pyisomme.report.page import Page_Cover
from pyisomme.limits import Limits
from pyisomme.report.criterion import Criterion

from pptx import Presentation
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
import time
import logging
import numpy as np


logger = logging.getLogger(__name__)


class Report:
    name: str = None
    title: str = None
    isomme_list: list = None
    limits: dict = None
    criterion_master: dict = None
    pages: list
    protocol: str
    protocols: dict = {}

    def __init__(self, isomme_list: list, title: str = "Report", protocol: str = None):
        self.isomme_list = isomme_list
        self.title = title

        if protocol is not None:
            assert protocol in self.protocols.keys(), f"Protocol {protocol} not available. Available protocols: {list(self.protocols.keys())}"
            self.protocol = protocol

        self.limits = {isomme: Limits(name=self.name, limit_list=[]) for isomme in isomme_list}

        self.criterion_master = {}
        for isomme in isomme_list:
            self.criterion_master[isomme] = self.Criterion_Master(self, isomme)

        self.pages = [
            Page_Cover(self),
        ]

    def calculate(self):
        with logging_redirect_tqdm():
            for isomme in tqdm(self.isomme_list, desc="Calculate Report"):
                logger.info(f"Calculate Criteria for {isomme}")
                self.criterion_master[isomme].calculate()
        return self

    def print_results(self):
        def print_subcriteria_results(criterion, intend="\t"):
            print(f"{intend}{criterion.name if criterion.name is not None else criterion.__class__.__name__}: Value={criterion.value:.5g} [{criterion.channel.unit if criterion.channel is not None else ''}] Rating={criterion.rating:.5g}")

            subcriteria = [getattr(criterion, a) for a in dir(criterion) if isinstance(getattr(criterion, a), Criterion)]
            for subcriterion in subcriteria:
                print_subcriteria_results(subcriterion, intend=f"{intend}\t")

        for isomme in self.isomme_list:
            print(isomme)
            print_subcriteria_results(self.criterion_master[isomme])

    def __repr__(self):
        return f"Report(title='{self.title}', name='{self.name}')"

    class Criterion_Master(Criterion):
        pass

    def export_pptx(self, path, template: str = None) -> None:
        presentation = Presentation(template)

        with logging_redirect_tqdm():
            for page_number, page in enumerate(tqdm(self.pages, desc="Construct Pages")):
                logger.info(f"{page_number}:{page.name}")
                page.__init__(self)  # update. report could be changed since init
                page.construct(presentation)

        while True:
            try:
                presentation.save(path)
                break
            except Exception as e:
                logger.critical(e)
                time.sleep(1)
        logger.info(f"pptx successfully exported: {path}")