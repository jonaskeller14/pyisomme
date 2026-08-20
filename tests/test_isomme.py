import logging
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import pyisomme

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(module)-12s %(levelname)-8s %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S",
    level=logging.WARNING,
)


class TestIsomme(unittest.TestCase):
    FIXTURE = Path(__file__).parent.parent / "data" / "tests" / "ascii"

    def test_init(self):
        pyisomme.Isomme()
        pyisomme.Isomme(test_number="999", test_info=[], channels=[], channel_info=[])

    def test_read(self):
        paths = [
            self.FIXTURE,
            self.FIXTURE / "test.mme",
            self.FIXTURE.with_suffix(".zip"),
            self.FIXTURE / "Channel" / "test.chn",
            self.FIXTURE / "Channel" / "test.002",
        ]
        for path in paths:
            with self.subTest(path=path):
                isomme = pyisomme.Isomme().read(path, "11HEAD*")
                self.assertEqual(
                    [str(channel.code) for channel in isomme.channels],
                    ["11HEADCG0000ACXP"],
                )

    def test_write(self):
        isomme = pyisomme.Isomme(
            test_number="synthetic",
            channels=[
                pyisomme.Channel("11HEAD000000ACXP", pd.DataFrame([1.0, 2.0]), "g"),
                pyisomme.Channel("13CHST000000DSXP", pd.DataFrame([3.0, 4.0]), "m"),
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (
                "synthetic.mme",
                "synthetic.zip",
                "folder",
                "synthetic.tar",
                "synthetic.tar.gz",
            ):
                path = root / name
                with self.subTest(path=path):
                    isomme.write(path, "11HEAD*")
                    written = pyisomme.Isomme().read(path)
                    self.assertEqual(
                        [str(channel.code) for channel in written.channels],
                        ["11HEAD000000ACXP"],
                    )

    def test_get_test_info(self):
        isomme = pyisomme.Isomme(test_info=[("Laboratory test ref. number", "98/7707")])
        assert isomme.get_test_info(
            "Laboratory test ref. number"
        ) == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info(
            "Laboratory test ref. number"
        ) == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_get_channel_info(self):
        isomme = pyisomme.Isomme(
            channel_info=[("Laboratory test ref. number", "98/7707")]
        )
        assert isomme.get_test_info(
            "Laboratory test ref. number"
        ) == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info(
            "Laboratory test ref. number"
        ) == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_extend(self):
        isomme_1 = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([])),
                pyisomme.Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([])),
            ]
        )
        isomme_2 = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(code="11HEAD0000H3ACZA", data=pd.DataFrame([])),
            ]
        )
        isomme_1.extend(isomme_2)
        assert len(isomme_1.channels) == 3
        channel = pyisomme.Channel(code="13HEAD0000H3ACXA", data=pd.DataFrame([]))
        isomme_1.extend(channel)
        assert len(isomme_1.channels) == 4
        channel_list = [
            pyisomme.Channel(code="13HEAD0000H3ACYA", data=pd.DataFrame([])),
            pyisomme.Channel(code="13HEAD0000H3ACZA", data=pd.DataFrame([])),
        ]
        isomme_1.extend(channel_list)
        assert len(isomme_1.channels) == 6

    def test_delete_duplicates(self):
        isomme = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([1])),
                pyisomme.Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([2])),
                pyisomme.Channel(code="11HEAD0000H3ACZA", data=pd.DataFrame([3])),
                pyisomme.Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([4])),
                pyisomme.Channel(code="11HEAD0000H3ACX0", data=pd.DataFrame([5])),
                pyisomme.Channel(code="11HEAD0000H3ACXP", data=pd.DataFrame([6])),
            ]
        )
        isomme.delete_duplicates()
        assert len(isomme.channels) == 5
        isomme.delete_duplicates(filter_class_duplicates=True)
        assert len(isomme.channels) == 3 and "11HEAD0000H3ACX0" in [
            c.code for c in isomme.channels
        ]

    def test_get_channel_calculates_resultant(self):
        time = [0.0, 0.01, 0.02]
        isomme = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(
                    code="11HEAD0000H3ACXA",
                    data=pd.DataFrame([1.0, 2.0, 3.0], index=time),
                    unit="g",
                ),
                pyisomme.Channel(
                    code="11HEAD0000H3ACYA",
                    data=pd.DataFrame([0.0, 0.0, 0.0], index=time),
                    unit="g",
                ),
                pyisomme.Channel(
                    code="11HEAD0000H3ACZA",
                    data=pd.DataFrame([0.0, 0.0, 0.0], index=time),
                    unit="g",
                ),
            ]
        )
        channel = isomme.get_channel("11HEAD0000H3ACRA")
        assert channel is not None
        assert channel.code.direction == "R"
        assert channel.code.physical_dimension == "AC"
        assert channel.get_data().tolist() == [1.0, 2.0, 3.0]

    def test_get_channel_reconstructs_via_differentiate_and_calculate(self):
        time = [0.0, 0.01, 0.02]
        isomme = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(
                    code="11HEAD0000H3VEXA",
                    data=pd.DataFrame([0.0, 0.01, 0.02], index=time),
                    unit="m/s",
                ),
                pyisomme.Channel(
                    code="11HEAD0000H3VEYA",
                    data=pd.DataFrame([0.0, 0.0, 0.0], index=time),
                    unit="m/s",
                ),
                pyisomme.Channel(
                    code="11HEAD0000H3VEZA",
                    data=pd.DataFrame([0.0, 0.0, 0.0], index=time),
                    unit="m/s",
                ),
            ]
        )

        # Reconstruct the missing acceleration X channel by differentiating the existing velocity channel.
        acc_x = isomme.get_channel("11HEAD0000H3ACXA")
        assert acc_x is not None
        assert acc_x.code.physical_dimension == "AC"
        assert acc_x.code.direction == "X"
        assert np.allclose(acc_x.get_data().flatten(), [1.0, 1.0, 1.0], atol=1e-8)

        # Reconstruct the resultant acceleration by calculating from the reconstructed X/Y/Z acceleration channels.
        acc_r = isomme.get_channel("11HEAD0000H3ACRA")
        assert acc_r is not None
        assert acc_r.code.direction == "R"
        assert acc_r.code.physical_dimension == "AC"
        assert np.allclose(acc_r.get_data().flatten(), [1.0, 1.0, 1.0], atol=1e-8)

    def test_get_channel_integration_reconstructs_velocity(self):
        time = [0.0, 0.01, 0.02]
        isomme = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(
                    code="11HEAD0000H3ACXA",
                    data=pd.DataFrame([0.0, 1.0, 2.0], index=time),
                    unit="m/s^2",
                ),
            ]
        )
        velocity = isomme.get_channel("11HEAD0000H3VEXA")
        assert velocity is not None
        assert velocity.code.physical_dimension == "VE"
        assert np.allclose(velocity.get_data().flatten(), [0.0, 0.005, 0.02], atol=1e-8)

    def test_get_channel_filters_to_requested_class(self):
        # The ISO-6487 filter averages the first/last 10 points, so it needs a realistic
        # (not 3-sample) signal; use a 10 kHz record like real crash data.
        time = np.linspace(0.0, 0.1, 1000)
        isomme = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(
                    code="11HEAD0000H3ACX0",
                    data=pd.DataFrame(np.sin(2 * np.pi * 50 * time), index=time),
                    unit="g",
                ),
            ]
        )
        filtered = isomme.get_channel("11HEAD0000H3ACXA")
        assert filtered is not None
        assert filtered.code.filter_class == "A"
        assert filtered.code == "11HEAD0000H3ACXA"

    def test_get_channel_builds_hic_from_acceleration(self):
        time = [0.0, 0.01, 0.02, 0.03]
        isomme = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(
                    code="11HEAD000000ACXA",
                    data=pd.DataFrame([0.0, 1.0, 0.5, 0.0], index=time),
                    unit="g",
                ),
                pyisomme.Channel(
                    code="11HEAD000000ACYA",
                    data=pd.DataFrame([0.0, 0.0, 0.0, 0.0], index=time),
                    unit="g",
                ),
                pyisomme.Channel(
                    code="11HEAD000000ACZA",
                    data=pd.DataFrame([0.0, 0.0, 0.0, 0.0], index=time),
                    unit="g",
                ),
            ]
        )
        hic = isomme.get_channel("11HICR00150000RX")
        assert hic is not None
        assert hic.code.main_location == "HICR"
        assert hic.code.filter_class == "X"
        assert hic.get_data()[0] >= 0

    def test_get_channel_builds_bric(self):
        time = [0.0, 0.01]
        isomme = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(
                    code="11HEAD000000AVXD",
                    data=pd.DataFrame([10.0, 20.0], index=time),
                    unit="rad/s",
                ),
                pyisomme.Channel(
                    code="11HEAD000000AVYD",
                    data=pd.DataFrame([10.0, 30.0], index=time),
                    unit="rad/s",
                ),
                pyisomme.Channel(
                    code="11HEAD000000AVZD",
                    data=pd.DataFrame([10.0, 40.0], index=time),
                    unit="rad/s",
                ),
            ]
        )
        bric = isomme.get_channel("11BRIC00000000XX")
        assert bric is not None
        assert bric.code.main_location == "BRIC"
        assert bric.code.direction == "0"
        assert bric.get_data()[0] > 0

    def test_get_channel_builds_xms_from_acceleration(self):
        time = [0.0, 0.001, 0.002, 0.003, 0.004]
        isomme = pyisomme.Isomme(
            channels=[
                pyisomme.Channel(
                    code="11HEAD0000H3ACXA",
                    data=pd.DataFrame([0.0, 1.0, 2.0, 3.0, 4.0], index=time),
                    unit="g",
                ),
            ]
        )
        xms = isomme.get_channel("11HEAD003SH3ACXX")
        assert xms is not None
        assert xms.code.fine_location_2 == "3S"
        assert xms.code.filter_class == "X"
        assert xms.data.shape == (1, 1)


if __name__ == "__main__":
    unittest.main()
