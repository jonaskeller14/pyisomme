# pyisomme

## Features
- Read/write ISO-MME (compressed/uncompressed)
- Modify Channel and calculate Injury Risk Values (HIC, a3ms, DAMAGE, OLC, BrIC, NIJ, ...)
- Plot Curves and compare multiple ISO-MMEs
- Create PowerPoint Reports (Euro-NCAP, ...)
- Display Limit bars in plots
- Compare performance of left-hand-drive vehicle with right-hand-drive vehicle
- Command line tool script for fast and easy use [pyisomme_cmd.py](pyisomme_cmd.py)

## Examples
- [Read ISO-MME](docs/isomme_read.ipynb)
- [Write ISO-MME](docs/isomme_write.ipynb)


- [Signal deriviation/integration](docs/channel_diff_int.ipynb)
- [Add/Subtract/Multiply/Divide Signals](docs/channel_operators.ipynb)
- [Apply cfc-filter](docs/channel_filter.ipynb)


- [Plotting](docs/plotting.ipynb)

- [Report](docs/report.ipynb)

## Limitations
Only test-info (.mme), channel-info (.chn) and channel data files (.001/.002/...) are supported. All other files (videos, photos, txt-files) will be ignored when reading and writing.