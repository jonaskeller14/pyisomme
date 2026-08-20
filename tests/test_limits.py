import logging
import unittest

import numpy as np
import pandas as pd

import pyisomme

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(module)-12s %(levelname)-8s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S",
    level=logging.WARNING,
)


class TestLimits(unittest.TestCase):
    def test_find_limits(self):
        limits = pyisomme.Limits(
            limit_list=[
                pyisomme.Limit(
                    code_patterns=("11NECKUP????FOX?",),
                    func=lambda x: 500,
                    name="sdfsdf",
                    color="yellow",
                    linestyle="--",
                ),
                pyisomme.Limit(
                    code_patterns=("11NECKUP.*FOX[AB]",),
                    func=lambda x: 500,
                    name="sdfsdf",
                    color="yellow",
                    linestyle="--",
                ),
                pyisomme.Limit(
                    code_patterns=("11NECKUP????FOY?",),
                    func=lambda x: 750 - 7.5 * x,
                    name="da",
                    color="red",
                    linestyle="-",
                ),
            ]
        )
        assert len(limits.find_limits("11NECKUP00H3FOXA")) == 2

    def test_get_limit_idx(self):
        c1 = pyisomme.Channel(
            code="?" * 16, unit="1", data=pd.DataFrame([2.9, 0, 0, 1.9, 1.9, -1.5])
        )
        c2 = pyisomme.Channel(
            code="?" * 16, unit="1", data=pd.DataFrame([4, 0, 0, 3, 0, 0])
        )
        c3 = pyisomme.Channel(
            code="?" * 16, unit="1", data=pd.DataFrame([7, 7, 6, 5, 5, 5])
        )
        c4 = pyisomme.Channel(
            code="?" * 16, unit="1", data=pd.DataFrame([-4, -7, -7, -7, -6, -7])
        )

        limits = pyisomme.Limits(
            limit_list=[
                pyisomme.Limit(
                    ("?" * 16,),
                    func=lambda x: np.interp(x, [2, 3], [5, 2]),
                    y_unit="1",
                    name="1",
                    rating=1,
                    upper=True,
                    color="green",
                ),
                pyisomme.Limit(
                    ("?" * 16,),
                    func=lambda x: np.interp(x, [2, 3], [5, 2]),
                    y_unit="1",
                    name="2",
                    rating=2,
                    lower=True,
                    color="red",
                ),
                pyisomme.Limit(
                    ("?" * 16,),
                    func=lambda x: np.interp(x, [2, 3], [-2, -5]),
                    y_unit="1",
                    name="1",
                    rating=1,
                    lower=True,
                    color="green",
                ),
                pyisomme.Limit(
                    ("?" * 16,),
                    func=lambda x: np.interp(x, [2, 3], [-2, -5]),
                    y_unit="1",
                    name="2",
                    rating=2,
                    upper=True,
                    color="red",
                ),
            ]
        )

        # pyisomme.Plot_Line(
        #     channels={pyisomme.Isomme(test_number="test"): [[c1, c2, c3, c4]]},
        #     limits=limits,
        # ).show()

        idx1_min = limits.get_limit_min_idx(c1)
        idx1_max = limits.get_limit_max_idx(c1)
        assert idx1_min == 5
        assert idx1_max == 3

        idx2_min = limits.get_limit_min_idx(c2)
        idx2_max = limits.get_limit_max_idx(c2)
        assert idx2_min == 1
        assert idx2_max == 3

        idx3_min = limits.get_limit_min_idx(c3)
        idx3_max = limits.get_limit_max_idx(c3)
        assert idx3_min == 2
        assert idx3_max == 3

        idx4_min = limits.get_limit_min_idx(c4)
        idx4_max = limits.get_limit_max_idx(c4)
        assert idx4_min == 4
        assert idx4_max == 1


if __name__ == "__main__":
    unittest.main()
