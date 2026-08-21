import numpy as np
import pandas as pd
import pytest

from pyisomme import Channel, Isomme, calculate_olc, g0


class TestCalculateOLC:
    @pytest.fixture
    def isomme(self) -> Isomme:
        isomme = Isomme()

        # A ~20 g sled pulse: the vehicle velocity drops from 15.6 m/s so the free-flying
        # occupant (held at v_0) travels far enough relative to it to complete both the
        # free-flight (65 mm) and restraining (235 mm) phases OLC requires.
        time = np.linspace(0.0, 0.15, 151)
        velocity = np.clip(15.6 - 200.0 * time, 0.0, None)
        isomme.channels.append(
            Channel(
                code="11CHST000000VEXA",
                data=pd.DataFrame(velocity, index=time),
                unit="m/s",
            )
        )
        return isomme

    def test_calculate_olc(self, isomme):
        olc, olc_visual = calculate_olc(isomme.channels[0])
        assert olc is not None
        assert olc_visual is not None
        assert olc.code.fine_location_1 == "0O"
        assert olc.code.fine_location_2 == "LC"
        assert olc.unit == g0
        t_1 = olc_visual.info["t_1 [s]"]
        assert 0 < t_1 < 0.15
        assert olc_visual.get_data(t=t_1) == pytest.approx(15.6)

    def test_calculate_olc_provider(self, isomme):
        assert isomme.get_channel("11CHST0OLC00VEXX") is not None
        assert isomme.get_channel("11CHST0OLC00VEXA") is not None
