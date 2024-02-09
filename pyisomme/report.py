from pyisomme.criterion import Criterion
from pyisomme.page import *

from pptx import Presentation
from tqdm import tqdm
from tqdm.contrib.logging import logging_redirect_tqdm
import time
import logging


class Report:
    name: str = None
    title: str = None
    isomme_list: list = None
    limits: dict = None
    criterion_master: dict = None
    pages: list

    def __init__(self, isomme_list: list, title: str = None):
        self.isomme_list = isomme_list
        self.title = title

        self.limits = {isomme: Limits(name=self.name, limit_list=[]) for isomme in isomme_list}

        self.criterion_master = {}
        for isomme in isomme_list:
            self.criterion_master[isomme] = self.Criterion_Master(self, isomme)

        self.pages = [  # FIXME, nicht hier definieren
            Page_Cover(self),
        ]

    def calculate(self):
        with logging_redirect_tqdm():
            for isomme in tqdm(self.isomme_list, desc="Calculate Report"):
                logging.info(f"Calculate Criteria for {isomme}")
                self.criterion_master[isomme].calculate()
        return self

    def print_results(self):
        def print_subcriteria_results(criterion, intend="\t"):
            print(f"{intend}{criterion.name if criterion.name is not None else criterion.__class__.__name__}: Value={criterion.value} Rating={criterion.rating}")

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

    def export_pptx(self, path, template="template.pptx"):
        presentation = Presentation(template)

        with logging_redirect_tqdm():
            for page_number, page in enumerate(tqdm(self.pages, desc="Construct Pages")):
                logging.info(f"{page_number}:{page.name}")
                page.__init__(self)  # update. report could be changed since init
                page.construct(presentation)

        while True:
            try:
                presentation.save(path)
                break
            except Exception as e:
                logging.critical(e)
                time.sleep(1)
        logging.info(f"pptx successfully exported: {path}")