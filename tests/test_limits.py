import logging

import numpy as np
import pandas as pd
import pytest

from pyisomme import Channel, Limit, LimitSet, limit_list_sort

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(module)-12s %(levelname)-8s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S",
    level=logging.WARNING,
)


class TestLimits:
    def test_limit_set_is_immutable(self):
        limit_set = LimitSet()

        with pytest.raises(AttributeError):
            limit_set.limits = () # pyright: ignore[reportAttributeAccessIssue]

    def test_find_limits(self):
        limits = LimitSet(
            limits=(
                Limit(
                    code_patterns=("11NECKUP????FOX?",),
                    func=lambda x: 500,
                    name="sdfsdf",
                    color="yellow",
                    linestyle="--",
                ),
                Limit(
                    code_patterns=("11NECKUP00H3FOXA",),
                    func=lambda x: 500,
                    name="sdfsdf",
                    color="yellow",
                    linestyle="--",
                ),
                Limit(
                    code_patterns=("11NECKUP????FOY?",),
                    func=lambda x: 750 - 7.5 * x,
                    name="da",
                    color="red",
                    linestyle="-",
                ),
            )
        )
        assert len(limits.find_limits("11NECKUP00H3FOXA")) == 2

    def test_find_limits_matches_each_limit_once(self):
        limit = Limit(
            code_patterns=("11NECKUP????FOX?", "11NECKUP00H3FOXA"),
            func=lambda x: 500,
        )
        limits = LimitSet(limits=(limit,))

        assert limits.find_limits("11NECKUP00H3FOXA", "11NECKUP00H3FOXA") == [limit]

    def test_find_limits_uses_case_sensitive_fnmatch_patterns(self):
        regex_limit = Limit(
            code_patterns=("11NECKUP.*FOX[AB]",),
            func=lambda x: 500,
        )
        literal_limit = Limit(
            code_patterns=("11NECKUP00H3FOXA",),
            func=lambda x: 500,
        )
        limits = LimitSet(limits=(regex_limit, literal_limit))

        assert limits.find_limits("11NECKUP00H3FOXA") == [literal_limit]
        assert limits.find_limits("11neckup00h3foxa") == []

    def test_get_limit_idx(self):
        c1 = Channel(
            code="?" * 16, unit="1", data=pd.DataFrame([2.9, 0, 0, 1.9, 1.9, -1.5])
        )
        c2 = Channel(code="?" * 16, unit="1", data=pd.DataFrame([4, 0, 0, 3, 0, 0]))
        c3 = Channel(code="?" * 16, unit="1", data=pd.DataFrame([7, 7, 6, 5, 5, 5]))
        c4 = Channel(
            code="?" * 16, unit="1", data=pd.DataFrame([-4, -7, -7, -7, -6, -7])
        )

        limits = LimitSet(
            limits=(
                Limit(
                    ("?" * 16,),
                    func=lambda x: np.interp(x, [2, 3], [5, 2]),
                    y_unit="1",
                    name="1",
                    rating=1,
                    upper=True,
                    color="green",
                ),
                Limit(
                    ("?" * 16,),
                    func=lambda x: np.interp(x, [2, 3], [5, 2]),
                    y_unit="1",
                    name="2",
                    rating=2,
                    lower=True,
                    color="red",
                ),
                Limit(
                    ("?" * 16,),
                    func=lambda x: np.interp(x, [2, 3], [-2, -5]),
                    y_unit="1",
                    name="1",
                    rating=1,
                    lower=True,
                    color="green",
                ),
                Limit(
                    ("?" * 16,),
                    func=lambda x: np.interp(x, [2, 3], [-2, -5]),
                    y_unit="1",
                    name="2",
                    rating=2,
                    upper=True,
                    color="red",
                ),
            )
        )

        # Plot_Line(
        #     channels={Isomme(test_number="test"): [[c1, c2, c3, c4]]},
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

    def test_get_limit_min_and_max_use_extreme_sample_ratings(self):
        channel = Channel(
            code="?" * 16,
            unit="1",
            data=pd.DataFrame([1.5, 2.5, 0.5]),
        )
        minimum = Limit(
            ("?" * 16,),
            func=lambda x: 1,
            y_unit="1",
            name="minimum",
            rating=1,
            upper=True,
        )
        middle_lower = Limit(
            ("?" * 16,),
            func=lambda x: 1,
            y_unit="1",
            name="middle lower",
            rating=2,
            lower=True,
        )
        middle_upper = Limit(
            ("?" * 16,),
            func=lambda x: 2,
            y_unit="1",
            name="middle upper",
            rating=2,
            upper=True,
        )
        maximum = Limit(
            ("?" * 16,),
            func=lambda x: 2,
            y_unit="1",
            name="maximum",
            rating=3,
            lower=True,
        )
        limits = LimitSet(limits=(minimum, middle_lower, middle_upper, maximum))

        assert limits.get_limit_min(channel) is minimum
        assert limits.get_limit_max(channel) is maximum

    def test_evaluation_converts_before_sorting_and_caches_thresholds(self):
        calls = {"newtons": 0, "kilonewtons": 0}

        def newtons(_x):
            calls["newtons"] += 1
            return 900

        def kilonewtons(_x):
            calls["kilonewtons"] += 1
            return 1

        limit_newtons = Limit(("?" * 16,), newtons, y_unit="N", rating=0, lower=True)
        limit_kilonewtons = Limit(
            ("?" * 16,), kilonewtons, y_unit="kN", rating=1, lower=True
        )
        channel = Channel(
            code="?" * 16,
            unit="N",
            data=pd.DataFrame([950.0, 975.0]),
        )
        evaluation = LimitSet(limits=(limit_kilonewtons, limit_newtons)).evaluate(
            channel
        )

        assert evaluation.ordered_limits == (limit_newtons, limit_kilonewtons)
        np.testing.assert_allclose(evaluation.ratings(), [0.5, 0.75])
        np.testing.assert_allclose(evaluation.ratings(), [0.5, 0.75])
        assert calls == {"newtons": 2, "kilonewtons": 2}

    def test_evaluation_rejects_limits_that_change_order(self):
        increasing = Limit(("?" * 16,), lambda x: x, y_unit="1", rating=0, upper=True)
        decreasing = Limit(
            ("?" * 16,), lambda x: 1 - x, y_unit="1", rating=1, lower=True
        )
        channel = Channel(
            code="?" * 16,
            unit="1",
            data=pd.DataFrame([0.5, 0.5], index=[0.0, 1.0]),
        )
        evaluation = LimitSet(limits=(increasing, decreasing)).evaluate(channel)

        with pytest.raises(ValueError, match="change order"):
            _ = evaluation.ordered_thresholds

    def test_evaluation_supports_infinite_ratings(self):
        good = Limit(
            ("?" * 16,),
            func=lambda x: 0,
            y_unit="1",
            name="Good",
            color="green",
            rating=np.inf,
            upper=True,
        )
        capping = Limit(
            ("?" * 16,),
            func=lambda x: 0,
            y_unit="1",
            name="Capping",
            color="gray",
            rating=-np.inf,
            lower=True,
        )
        channel = Channel(
            code="?" * 16,
            unit="1",
            data=pd.DataFrame([-1.0, 1.0]),
        )
        evaluation = LimitSet(limits=(capping, good)).evaluate(channel)

        np.testing.assert_array_equal(evaluation.ratings(), [np.inf, -np.inf])
        assert evaluation.get_limit_max_rating() == np.inf
        assert evaluation.get_limit_min_rating() == -np.inf
        assert evaluation.get_limit_max() is good
        assert evaluation.get_limit_min() is capping
        assert evaluation.get_limit_max_color() == "green"
        assert evaluation.get_limit_min_color() == "gray"
        assert evaluation.get_limit_max_idx() == 0
        assert evaluation.get_limit_min_idx() == 1
        assert evaluation.get_limit_max_y() == -1
        assert evaluation.get_limit_min_y() == 1

        # A capping result must poison an otherwise finite aggregate.
        assert np.min([4.0, evaluation.get_limit_min_rating()]) == -np.inf

    def test_infinite_rating_is_a_step_at_the_capping_threshold(self):
        poor = Limit(
            ("?" * 16,),
            func=lambda x: 2.62,
            y_unit="kN",
            name="Poor",
            color="red",
            rating=0,
            lower=True,
        )
        capping = Limit(
            ("?" * 16,),
            func=lambda x: 2.9,
            y_unit="kN",
            name="Capping",
            color="gray",
            rating=-np.inf,
            lower=True,
        )
        channel = Channel(
            code="?" * 16,
            unit="kN",
            data=pd.DataFrame([2.7, 2.9, 3.0]),
        )
        evaluation = LimitSet(limits=(poor, capping)).evaluate(channel)

        np.testing.assert_array_equal(evaluation.ratings(), [0, -np.inf, -np.inf])
        assert evaluation.get_limit_min() is capping
        assert evaluation.get_limit_min_color() == "gray"

    def test_limit_list_sort_converts_units(self):
        kilonewtons = Limit(("?" * 16,), lambda x: 1, y_unit="kN")
        newtons = Limit(("?" * 16,), lambda x: 900, y_unit="N")

        assert limit_list_sort([kilonewtons, newtons], x=0, x_unit="s", y_unit="N") == [
            newtons,
            kilonewtons,
        ]

    def test_limit_list_sort_uses_majority_order_across_x_positions(self):
        increasing = Limit(("?" * 16,), lambda x: x, y_unit="1")
        constant = Limit(("?" * 16,), lambda x: 1, y_unit="1")

        assert limit_list_sort(
            [increasing, constant],
            x=[0, 2, 3],
            x_unit="s",
            y_unit="1",
        ) == [constant, increasing]
