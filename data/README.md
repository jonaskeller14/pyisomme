# data - References

Everything here is downloaded reference data and is **untracked** (see `.gitignore`) — with
one exception, `tests/`, described below.

## [tests](tests) — encoding fixtures (tracked)

Four tiny hand-built ISO-MME containers, one per text encoding, each as a folder and as a
`.zip`. They are the only fixtures `tests/` can count on after a fresh clone, so they are
committed. Rebuild them byte-for-byte with:

```bash
.venv/Scripts/python.exe data/tests/generate_fixtures.py
```

All four encode the *same* container — 3 channels (`11TIRS000000TIRP`, `11HEADCG0000ACXP`,
`11CHST0000H3DSXP`), 20 samples at 10 kHz — so `tests/test_parsing.py` asserts one
expectation across every encoding and only the header text differs:

| fixture | exercises |
| --- | --- |
| [ascii](tests/ascii) | 7-bit + CRLF. Structural traps only: a colon inside a value, an empty value, `NOVALUE`, tab padding, trailing whitespace |
| [iso-8859-1](tests/iso-8859-1) | Latin-1 (`ä ö ü ß é ç ± ° µ`). Invalid UTF-8, so it must reach the single-byte fallback |
| [windows-1252](tests/windows-1252) | Latin-1 **plus** 0x80–0x9F (`€ – — „ “ … ™`), which ISO-8859-1 leaves as C1 controls. Pins cp1252 ahead of ISO-8859-1 in `read_text_with_fallback` |
| [utf-8](tests/utf-8) | A BOM on the `.mme` plus characters outside Latin-1 (`Δ Ω → 日本語`) |

The channel headers also cover all three time-axis conventions: no timing at all (TIRS,
sample index), `explicit` via a reference channel, and `implicit` from first sample +
interval, with one `NOVALUE` dropout becoming `NaN`.

## Downloaded reference data (untracked)

Directory tree:
- [iso-mme-org](iso-mme-org) 
  - [MME 1.6 Testdata short](iso-mme-org/MME%201.6%20Testdata%20short) [[Download](https://www.iso-mme.org/forum/download/file.php?id=582)]
    - [98_7707](iso-mme-org/MME%201.6%20Testdata%20short/98_7707)
    - [3239](iso-mme-org/MME%201.6%20Testdata%20short/3239)
    - [AK3T02FO](iso-mme-org/MME%201.6%20Testdata%20short/AK3T02FO)
    - [AK3T02SI](iso-mme-org/MME%201.6%20Testdata%20short/AK3T02SI)
    - [VW1FGS15](iso-mme-org/MME%201.6%20Testdata%20short/VW1FGS15)
- [nhtsa](nhtsa) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle)]
  - [09203](nhtsa/09203) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases/#/vehicle/9203), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v00000/v09200/v09203ISO.zip)]
    - Fixed via [fix_channel_metadata.py](nhtsa/09203/fix_channel_metadata.py):
      chest displacement unit corrected from m to μm; dummy field set to TH (THOR, test object 2 / position 1, code 21) and H3 (Hybrid III, position 4, code 24)
  - [11391](nhtsa/11391) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/11391), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v11300/v11391ISO.zip)]
  - [14065](nhtsa/14065) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/14065), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v14000/v14065ISO.zip)]
  - [14084](nhtsa/14084) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/14084), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v14000/v14084ISO.zip)]
    - Fixed via [fix_channel_metadata.py](nhtsa/14084/fix_channel_metadata.py):
      chest displacement unit corrected from m to μm; dummy field set to H3 (driver, code 11) and HF (passenger, code 13)


  - [v09203ISO.zip](nhtsa/v09203ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases/#/vehicle/9203), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v00000/v09200/v09203ISO.zip)]
  - [v11391ISO.zip](nhtsa/v11391ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/11391), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v11300/v11391ISO.zip)]
  - [v14065ISO.zip](nhtsa/v14065ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/14065), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v14000/v14065ISO.zip)]
  - [v14084ISO.zip](nhtsa/v14084ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/14084), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v14000/v14084ISO.zip)]
  - [v15036ISO.zip](nhtsa/v15036ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/15036), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v15000/v15036ISO.zip)] — read directly as a zip by `tests/test_report.py`
