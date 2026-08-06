# pyisomme

## Installation

```
pip install pyisomme
```

## Features
- Read/write ISO-MME (compressed/uncompressed)
- Modify Channel and calculate Injury Risk Values (HIC, a3ms, DAMAGE, OLC, BrIC, NIJ, ...)
- Plot Curves and compare multiple ISO-MMEs
- Create PowerPoint Reports (Euro-NCAP, UN-R137, UN-R94)
- Display Limit bars in plots
- Compare performance of left-hand-drive vehicle with right-hand-drive vehicle
- Command-line tools for listing, merging, editing, converting, plotting, and reporting ISO-MME data

## Command Line Interface (CLI)

Installing the package provides the `pyisomme` command. The equivalent
`python -m pyisomme` form is also supported.

```bash
pyisomme --help
pyisomme <command> --help
```

| Command | Purpose |
| --- | --- |
| `list` | List channels, optionally selected by code patterns |
| `merge` | Merge and transform one or more ISO-MME containers |
| `set` | Relabel one metadata field on selected channels in place |
| `convert` | Numerically convert selected channel data to another unit in place |
| `plot` | Plot selected or calculated channels |
| `report` | Calculate and export an assessment report |

Edit channel codes

```bash
pyisomme set TEST1.mme TEST2.zip fine_location_3 H3 -c '11*' '13*'
```

Convert channel values and units (e.g. `0.04 m` becomes `40 mm`)

```bash
pyisomme convert TEST1.mme TEST2.zip unit mm -c '??CHST??????DS??'
```

Merge multiple ISO-MME containers:

```bash
pyisomme merge ./iso_merged.zip ./iso_1/v1.mme ./iso_2.zip ./iso_3.tar.gz
```

Resample from 0 to 100 ms with a 1 ms step and linear interpolation:

```bash
pyisomme merge ./resampled.mme ./iso_1/v1.mme --resample 0 0.001 0.1
```

Plot a calculated resultant head acceleration with filter class A / 1000 Hz:

```bash
pyisomme plot ./iso_1/v1.mme --codes '24HEAD??????ACRA' --xlim 0 100 --calculate
```

Create a report using only data from 0 to 200 ms:

```bash
pyisomme report EuroNCAP_Frontal_MPDB report.pptx data/nhtsa/09203 --crop 0 0.2
```

## Python Examples
- [Read ISO-MME](docs/isomme_read.ipynb)
- [Write ISO-MME](docs/isomme_write.ipynb)


- [Signal deriviation/integration](docs/channel_diff_int.ipynb)
- [Add/Subtract/Multiply/Divide Signals](docs/channel_operators.ipynb)
- [Apply cfc-filter](docs/channel_filter.ipynb)


- [Plotting](docs/plotting.ipynb)

- [Report](docs/report.ipynb)

## Limitations
- Only test-info (.mme), channel-info (.chn) and channel data files (.001/.002/...) are supported. All other files (videos, photos, txt-files) will be ignored when reading and writing.
- Writing methods do not ask before overwriting. In particular, `set` and `convert` rewrite every
  supplied ISO-MME container in place after validating all inputs and selections.
