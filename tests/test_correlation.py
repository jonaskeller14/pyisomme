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


class TestCorrelation(unittest.TestCase):
    def test_correlation(self):
        reference_channel = pyisomme.create_sample(
            t_range=(0, 0.1, 1000), y_range=(0, 10)
        )
        comparison_channel = pyisomme.create_sample(
            t_range=(0, 0.11, 1000), y_range=(0, 11)
        )
        correlation = pyisomme.Correlation_ISO18571(
            reference_channel, comparison_channel
        )
        logger.info(f"Correlation overall rating: {correlation.overall_rating()}")

    def test_correlation2(self):
        time = np.arange(0, 0.150, 0.0001)
        reference = np.sin(time * 20)
        comparison = np.sin(time * 20) * 1.3 + 0.00

        reference_channel = pyisomme.Channel(
            code="????????????????", data=pd.DataFrame(reference, index=time)
        )
        comparison_channel = pyisomme.Channel(
            code="????????????????", data=pd.DataFrame(comparison, index=time)
        )

        correlation = pyisomme.Correlation_ISO18571(
            reference_channel, comparison_channel
        )
        overall_rating = correlation.overall_rating()
        assert np.abs(overall_rating - 0.713) < 1e-6
        logger.info(f"Correlation Overall Rating {correlation.overall_rating()}")


if __name__ == "__main__":
    unittest.main()
