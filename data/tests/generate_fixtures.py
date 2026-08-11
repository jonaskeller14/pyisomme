"""
Regenerate the encoding fixtures under ``data/tests/``.

``tests/test_parsing.py`` reads one small ISO-MME container per text encoding, as a folder
and as a ``.zip``. The containers are hand-built rather than downloaded so they can be
tracked in git (the rest of ``data/`` is not) and so they can carry characters chosen to
exercise the decoding path in :func:`pyisomme.sources.read_text_with_fallback`:

======================  ==================================================================
``ascii``               7-bit only. Carries the *structural* awkwardness instead: a colon
                        inside a value, an empty value, ``NOVALUE``, tab padding, trailing
                        whitespace and CRLF line endings.
``iso-8859-1``          Latin-1 only (0xA0-0xFF): ``ä ö ü ß é ç ± ° µ ½``. Invalid UTF-8,
                        so it must reach the single-byte fallback.
``windows-1252``        Latin-1 *plus* the 0x80-0x9F range that ISO-8859-1 leaves as C1
                        controls: ``€ – — „ " … ™``. Decoding this as ISO-8859-1 turns
                        ``…`` (0x85) into U+0085 NEL, which ``str.splitlines()`` treats as
                        a line break — it would split a header line in two. This fixture
                        is what proves cp1252 is tried before ISO-8859-1.
``utf-8``               A UTF-8 BOM on the ``.mme`` (as Windows editors write it) plus
                        characters outside Latin-1 entirely: ``Δ Ω → 日本語``.
======================  ==================================================================

All four decode to the *same* channel-level content (codes, units, sample values), so the
tests can assert one expectation across every encoding and let only the header text differ.

Usage::

    .venv/Scripts/python.exe data/tests/generate_fixtures.py
"""

from __future__ import annotations

from pathlib import Path
import math
import shutil
import zipfile


HERE = Path(__file__).parent

#: Container stem. Drives the .mme/.chn file names and every channel file name.
TEST_NUMBER = "test"

#: 20 samples at 10 kHz starting 0.5 ms before t0 — long enough to be a real time axis,
#: short enough that the whole fixture set stays a few kB.
N_SAMPLES = 20
SAMPLING_INTERVAL = 0.0001
TIME_OF_FIRST_SAMPLE = -0.0005


def _times() -> list[float]:
    return [TIME_OF_FIRST_SAMPLE + i * SAMPLING_INTERVAL for i in range(N_SAMPLES)]


def _head_acceleration() -> list[float]:
    """A plausible half-sine head pulse in g, zero until t0."""
    return [0.0 if t < 0 else 42.0 * math.sin(math.pi * t / 0.0020) for t in _times()]


def _chest_deflection() -> list[float | None]:
    """A monotone chest deflection ramp in µm, with one dropped sample (``NOVALUE``)."""
    values: list[float | None] = [
        0.0 if t < 0 else 1.4e4 * (t / 0.0020) ** 2 for t in _times()
    ]
    values[12] = None  # transducer dropout -> NOVALUE -> NaN
    return values


def _format_sample(value: float | None) -> str:
    return "NOVALUE" if value is None else f"{value:.6E}"


def _header(pairs: list[tuple[str, str]]) -> list[str]:
    """Format ``name:value`` pairs the way ISO-MME writers do (name padded to 28 columns)."""
    return [f"{name:<28}:{value}" for name, value in pairs]


# --------------------------------------------------------------------------------------
# Per-encoding header text
# --------------------------------------------------------------------------------------


class Variant:
    """One fixture: an encoding, a line ending, and the free-text header values."""

    def __init__(
        self,
        name: str,
        codec: str,
        *,
        bom: bool = False,
        newline: str = "\n",
        laboratory: str,
        customer: str,
        test_type: str,
        comments: list[str],
        head_channel_name: str,
        chest_channel_name: str,
        chest_unit: str,
    ) -> None:
        self.name = name
        self.codec = codec
        self.bom = bom
        self.newline = newline
        self.laboratory = laboratory
        self.customer = customer
        self.test_type = test_type
        self.comments = comments
        self.head_channel_name = head_channel_name
        self.chest_channel_name = chest_channel_name
        self.chest_unit = chest_unit


VARIANTS = [
    Variant(
        "ascii",
        "ascii",
        # Written on Windows: CRLF. Everything a 7-bit file can still do wrong.
        newline="\r\n",
        laboratory="MGA Research Corporation",
        customer="NHTSA / Office of Vehicle Safety Compliance",
        test_type="NCAP frontal rigid barrier, 56 km/h",
        comments=[
            "Time zero: first contact with the barrier face",
            "Chest deflection channel: IR-TRACC, 50 % ile Hybrid III",
        ],
        head_channel_name="Head CG X acceleration",
        chest_channel_name="Chest deflection X (IR-TRACC)",
        chest_unit="um",
    ),
    Variant(
        "iso-8859-1",
        "iso-8859-1",
        laboratory="Crash-Prüfzentrum Köln GmbH",
        customer="Société Automobile Française S.A.",
        test_type="Frontalaufprall ODB, 40 % Überdeckung",
        comments=[
            "Meßunsicherheit ±0,5 %; Prüftemperatur 22 °C",
            "Dummy: Hybrid III 50 %, Sitzposition vorne links",
        ],
        head_channel_name="Kopf-Schwerpunkt Beschleunigung X",
        chest_channel_name="Brustkorb-Eindrückung X (µm)",
        chest_unit="µm",  # U+00B5 MICRO SIGN - present in Latin-1 and cp1252 alike
    ),
    Variant(
        "windows-1252",
        "cp1252",
        laboratory="Crash-Prüfzentrum Köln GmbH",
        # 0x97 EM DASH and 0x92 RIGHT SINGLE QUOTE - not representable in ISO-8859-1.
        customer="Renault S.A. — Direction de la Sécurité",
        test_type="Frontalaufprall ODB, 40 % Überdeckung",
        # 0x80 EURO, 0x84/0x93 QUOTES, 0x85 HORIZONTAL ELLIPSIS, 0x99 TRADE MARK.
        comments=[
            "Prüfkosten 25.000 €; Bericht „Nr. 4711“ …",
            "Sensorik: Kistler™ – Drift ±0,5 % nachgeprüft",
        ],
        head_channel_name="Kopf-Schwerpunkt Beschleunigung X",
        chest_channel_name="Brustkorb-Eindrückung X (µm)",
        chest_unit="µm",
    ),
    Variant(
        "utf-8",
        "utf-8",
        bom=True,  # as a Windows editor saves it
        laboratory="Crash-Prüfzentrum Köln GmbH",
        customer="トヨタ自動車株式会社 (Toyota Motor Corp.)",
        test_type="Frontalaufprall ODB, 40 % Überdeckung",
        # Beyond Latin-1: GREEK CAPITAL DELTA, GREEK CAPITAL OMEGA, RIGHTWARDS ARROW.
        comments=[
            "Δv = 56,3 km/h → Pulsdauer 78 ms; Prüftemperatur 22 °C",
            "Brückenimpedanz 50 Ω; Meßunsicherheit ±0,5 % …",
        ],
        head_channel_name="Kopf-Schwerpunkt Beschleunigung X",
        chest_channel_name="Brustkorb-Eindrückung X (µm)",
        chest_unit="µm",
    ),
]


# --------------------------------------------------------------------------------------
# File bodies
# --------------------------------------------------------------------------------------


def mme_lines(v: Variant) -> list[str]:
    lines = _header(
        [
            ("Data format", "ISO-MME"),
            ("Version", "1.6"),
            ("Test number", TEST_NUMBER),
            ("Test date", "2026-05-14"),
            # Colons inside a value: the name/value split must land on the FIRST colon.
            ("Time of test", "10:32:45"),
            ("Test type", v.test_type),
            ("Laboratory name", v.laboratory),
            ("Customer name", v.customer),
            ("Test object", "Vehicle"),
            ("Number of test objects", "1"),
            ("Impact velocity", "56.3"),
            # Deliberately empty and explicitly-absent values: get_value() maps both to None.
            ("Regulation", ""),
            ("Client test ref number", "NOVALUE"),
        ]
    )
    # Padding style is not part of the format: a tab-separated line must parse the same.
    lines.append("Movie reference\t\t:NOVALUE")
    # A blank line and a trailing-whitespace line are both tolerated by parse_mme.
    lines.append("")
    lines.append("Test performed by           :Crash Team 3   ")
    lines += _header([("Comments", c) for c in v.comments])
    return lines


def chn_lines(v: Variant) -> list[str]:
    return _header(
        [
            ("Instrumentation standard", "SAEJ211, issued 1992"),
            ("Number of channels", "3"),
            ("Name of channel 001", "11TIRS000000TIRP / Time reference"),
            ("Name of channel 002", f"11HEADCG0000ACXP / {v.head_channel_name}"),
            ("Name of channel 003", f"11CHST0000H3DSXP / {v.chest_channel_name}"),
        ]
    )


def channel_001_lines(v: Variant) -> list[str]:
    """Time-reference channel. No timing header, so it falls back to the sample index."""
    values = _times()
    return _header(
        [
            ("Channel code", "11TIRS000000TIRP"),
            ("Name of the channel", "Time reference channel"),
            ("Data source", "calculated"),
            ("Test object number", "1"),
            ("Dimension", "TI"),
            ("Unit", "s"),
            ("Number of samples", str(N_SAMPLES)),
            ("Data status", "ok"),
        ]
    ) + [_format_sample(t) for t in values]


def channel_002_lines(v: Variant) -> list[str]:
    """Head acceleration with an *explicit* time reference pointing at channel 001."""
    return _header(
        [
            ("Channel code", "11HEADCG0000ACXP"),
            ("Laboratory channel code", "11HEADCG0000ACXP"),
            ("Name of the channel", v.head_channel_name),
            ("Reference channel", "explicit"),
            ("Reference channel name", "11TIRS000000TIRP"),
            ("Data source", "transducer"),
            ("Test object number", "1"),
            ("Location", "11HEADCG0000ACXP"),
            ("Direction", "X"),
            ("Dimension", "AC"),
            ("Channel frequency class", "1000"),
            ("Unit", "g"),
            ("Number of samples", str(N_SAMPLES)),
            ("Transducer type", "NOVALUE"),
            ("Data status", "ok"),
        ]
    ) + [_format_sample(a) for a in _head_acceleration()]


def channel_003_lines(v: Variant) -> list[str]:
    """Chest deflection with a declared *implicit* time axis and one dropped sample."""
    return _header(
        [
            ("Channel code", "11CHST0000H3DSXP"),
            ("Laboratory channel code", "11CHST0000H3DSXP"),
            ("Name of the channel", v.chest_channel_name),
            ("Reference channel", "implicit"),
            ("Reference channel name", "NOVALUE"),
            ("Data source", "transducer"),
            ("Test object number", "1"),
            ("Location", "11CHST0000H3DSXP"),
            ("Direction", "X"),
            ("Dimension", "DS"),
            ("Channel frequency class", "600"),
            ("Unit", v.chest_unit),
            ("Time of first sample", str(TIME_OF_FIRST_SAMPLE)),
            ("Sampling interval", str(SAMPLING_INTERVAL)),
            ("Number of samples", str(N_SAMPLES)),
            # A colon inside the value: the name/value split must happen at the FIRST colon.
            ("Comments", "IR-TRACC, calibrated 2026-04-02: drift within tolerance"),
            ("Data status", "ok"),
        ]
    ) + [_format_sample(d) for d in _chest_deflection()]


MEMBERS = {
    f"{TEST_NUMBER}.mme": mme_lines,
    f"Channel/{TEST_NUMBER}.chn": chn_lines,
    f"Channel/{TEST_NUMBER}.001": channel_001_lines,
    f"Channel/{TEST_NUMBER}.002": channel_002_lines,
    f"Channel/{TEST_NUMBER}.003": channel_003_lines,
}


def encode(v: Variant, member: str, lines: list[str]) -> bytes:
    data = v.newline.join(lines + [""]).encode(v.codec)
    # Only the .mme carries the BOM — mixed-BOM containers are what real archives look like.
    if v.bom and member.endswith(".mme"):
        data = b"\xef\xbb\xbf" + data
    return data


def build(v: Variant) -> None:
    root = HERE / v.name
    if root.exists():
        shutil.rmtree(root)
    members = {name: encode(v, name, builder(v)) for name, builder in MEMBERS.items()}

    for name, data in members.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    # Mirror the real-world layout (e.g. NHTSA's v09203ISO.zip): one folder inside the zip.
    zip_path = HERE / f"{v.name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(f"{TEST_NUMBER}/{name}", data)

    print(
        f"{v.name:<14} {v.codec:<12} {sum(len(d) for d in members.values()):>6} B  "
        f"-> {root.relative_to(HERE.parent)}/ and {zip_path.name}"
    )


if __name__ == "__main__":
    for variant in VARIANTS:
        build(variant)
