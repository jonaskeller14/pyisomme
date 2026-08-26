from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pyisomme import Channel, Isomme, Unit, g0


class TestIsomme:
    FIXTURE = Path(__file__).parent.parent / "data" / "tests" / "ascii"

    def test_init(self):
        i1 = Isomme()
        assert i1.test_number is None

        i2 = Isomme(test_number="999", test_info=[], channels=[], channel_info=[])
        assert i2.test_number == "999"

    @pytest.mark.parametrize(
        "path",
        [
            FIXTURE,
            FIXTURE / "test.mme",
            FIXTURE.with_suffix(".zip"),
            FIXTURE / "Channel" / "test.chn",
            FIXTURE / "Channel" / "test.002",
        ],
    )
    def test_read(self, path):
        isomme = Isomme().read(path, "11HEAD*")
        assert [str(channel.code) for channel in isomme.channels] == [
            "11HEADCG0000ACXP"
        ]

    @pytest.mark.parametrize(
        "name",
        [
            "synthetic.mme",
            "synthetic.zip",
            "folder",
            "synthetic.tar",
            "synthetic.tar.gz",
        ],
    )
    def test_write(self, tmp_path, name):
        isomme = Isomme(
            test_number="synthetic",
            channels=[
                Channel("11HEAD000000ACXP", pd.DataFrame([1.0, 2.0]), "g"),
                Channel("13CHST000000DSXP", pd.DataFrame([3.0, 4.0]), "m"),
            ],
        )
        path = tmp_path / name
        isomme.write(path, "11HEAD*")
        written = Isomme().read(path)
        assert [str(channel.code) for channel in written.channels] == [
            "11HEAD000000ACXP"
        ]

    @pytest.mark.parametrize("name", ["results.zip", "results.tar", "results.tar.gz"])
    def test_archive_write_preserves_sibling_directory(self, tmp_path, name):
        isomme = Isomme(test_number="synthetic")
        path = tmp_path / name
        sibling_directory = tmp_path / "results"
        sibling_directory.mkdir()
        sentinel = sibling_directory / "keep.txt"
        sentinel.write_text("unrelated user data")
        path.write_text("previous archive")

        isomme.write(path)

        assert sentinel.read_text() == "unrelated user data"
        assert path.is_file()
        assert path.read_bytes() != b"previous archive"

    def test_write_is_the_only_public_writer(self):
        isomme = Isomme()

        for method_name in (
            "write_mme",
            "write_folder",
            "write_zip",
            "write_tar",
            "write_tar_gz",
        ):
            assert not hasattr(isomme, method_name)

    def test_write_normalizes_standard_gravity_unit_to_g(self, tmp_path):
        isomme = Isomme(
            test_number="synthetic",
            channels=[
                Channel(
                    "11HEAD000000ACXP",
                    pd.DataFrame([1.0, 2.0]),
                    Unit(g0),
                ),
            ],
        )

        isomme.write(tmp_path / "synthetic.mme")

        channel_text = (tmp_path / "Channel" / "synthetic.001").read_text()
        assert "Unit                        :g\n" in channel_text
        assert "g0" not in channel_text

        written = Isomme().read(tmp_path / "synthetic.mme")
        assert written.channels[0].unit == Unit(g0)

    def test_get_test_info(self):
        isomme = Isomme(test_info=[("Laboratory test ref. number", "98/7707")])
        assert isomme.get_test_info(
            "Laboratory test ref. number"
        ) == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info(
            "Laboratory test ref. number"
        ) == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_get_channel_info(self):
        isomme = Isomme(channel_info=[("Laboratory test ref. number", "98/7707")])
        assert isomme.get_test_info(
            "Laboratory test ref. number"
        ) == isomme.get_test_info("[XL]abo?atory * ref. number")
        assert isomme.get_test_info(
            "Laboratory test ref. number"
        ) == isomme.get_test_info("[XL]abo.atory .* ref. number")

    def test_extend(self):
        isomme_1 = Isomme(
            channels=[
                Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([])),
                Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([])),
            ]
        )
        isomme_2 = Isomme(
            channels=[
                Channel(code="11HEAD0000H3ACZA", data=pd.DataFrame([])),
            ]
        )
        isomme_1.extend(isomme_2)
        assert len(isomme_1.channels) == 3
        channel = Channel(code="13HEAD0000H3ACXA", data=pd.DataFrame([]))
        isomme_1.extend(channel)
        assert len(isomme_1.channels) == 4
        channel_list = [
            Channel(code="13HEAD0000H3ACYA", data=pd.DataFrame([])),
            Channel(code="13HEAD0000H3ACZA", data=pd.DataFrame([])),
        ]
        isomme_1.extend(channel_list)
        assert len(isomme_1.channels) == 6

    def test_delete_duplicates(self):
        isomme = Isomme(
            channels=[
                Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([1])),
                Channel(code="11HEAD0000H3ACYA", data=pd.DataFrame([2])),
                Channel(code="11HEAD0000H3ACZA", data=pd.DataFrame([3])),
                Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([4])),
                Channel(code="11HEAD0000H3ACX0", data=pd.DataFrame([5])),
                Channel(code="11HEAD0000H3ACXP", data=pd.DataFrame([6])),
            ]
        )
        isomme.delete_duplicates()
        assert len(isomme.channels) == 5
        isomme.delete_duplicates(filter_class_duplicates=True)
        assert len(isomme.channels) == 3 and "11HEAD0000H3ACX0" in [
            c.code for c in isomme.channels
        ]

    def test_delete_duplicates_keeps_unfiltered_equal_signal(self):
        isomme = Isomme(
            channels=[
                Channel(code="11HEAD0000H3ACXA", data=pd.DataFrame([1.0])),
                Channel(code="11HEAD0000H3ACX0", data=pd.DataFrame([1.0])),
            ]
        )

        isomme.delete_duplicates(filter_class_duplicates=True)

        assert [channel.code for channel in isomme.channels] == ["11HEAD0000H3ACX0"]

    def test_get_channel_calculates_resultant(self):
        time = [0.0, 0.01, 0.02]
        isomme = Isomme(
            channels=[
                Channel(
                    code="11HEAD0000H3ACXA",
                    data=pd.DataFrame([1.0, 2.0, 3.0], index=time),
                    unit="g",
                ),
                Channel(
                    code="11HEAD0000H3ACYA",
                    data=pd.DataFrame([0.0, 0.0, 0.0], index=time),
                    unit="g",
                ),
                Channel(
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
        isomme = Isomme(
            channels=[
                Channel(
                    code="11HEAD0000H3VEXA",
                    data=pd.DataFrame([0.0, 0.01, 0.02], index=time),
                    unit="m/s",
                ),
                Channel(
                    code="11HEAD0000H3VEYA",
                    data=pd.DataFrame([0.0, 0.0, 0.0], index=time),
                    unit="m/s",
                ),
                Channel(
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
        isomme = Isomme(
            channels=[
                Channel(
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
        isomme = Isomme(
            channels=[
                Channel(
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

    def test_get_channel_does_not_use_more_heavily_filtered_channel(self):
        isomme = Isomme(
            channels=[
                Channel(
                    code="11HEAD0000H3ACXB",
                    data=pd.DataFrame([0.0, 1.0, 2.0], index=[0.0, 0.01, 0.02]),
                    unit="g",
                ),
            ]
        )

        # A class B signal cannot be used to create the less-filtered class A signal.
        assert isomme.get_channel("11HEAD0000H3ACXA") is None
