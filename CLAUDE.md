# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

pyisomme is a Python library and CLI for the **ISO-MME** crash-test data file format. It reads/writes ISO-MME containers, manipulates signal channels (filter, integrate, differentiate, arithmetic), computes injury-risk criteria (HIC, a3ms, DAMAGE, OLC, BrIC, NIJ, ...), plots curves, and generates PowerPoint assessment reports (Euro-NCAP, UN-R94/R137, US-NCAP, IIHS).

## Current work — `pyisomme.report` refactor

An incremental refactor of the report architecture is in progress. Before touching anything under
[pyisomme/report/](pyisomme/report/), read:

- **[docs/log/20260726_Report-Architecture-Review_plan.md](docs/log/20260726_Report-Architecture-Review_plan.md)** — the step-by-step plan, ground rules and per-step acceptance criteria. Work **one step at a time**; do not stray outside the step's scope.
- **[docs/log/20260726_Report-Architecture-Review_progress.md](docs/log/20260726_Report-Architecture-Review_progress.md)** — running log of what is done, decisions taken and open questions. **Every session must append an entry here before finishing.**
- [docs/log/20260726_Report-Architecture-Review.md](docs/log/20260726_Report-Architecture-Review.md) — the rationale (findings F1–F15, proposals P1–P11). Consult only the IDs your step names; do not read it end to end.

Invariants that must survive the refactor: NaN propagation is intentional (never swap in `np.nan*` to hide missing data); the criterion tree is eagerly constructed and user-mutable (manual inputs are set between construction and `calculate()`); criterion nesting stays.

## Commands

**Use the repo venv** — the `python` on `PATH` is a broken Anaconda 3.12 (numpy 2.3.5 against a scipy
built for <1.29) that cannot even `import pyisomme`. `.venv` is Python **3.9.13** with correct pins
(numpy 1.26.4, scipy 1.12.0) and the `dev` extra installed. 3.9 is the development target — it matches
`requires-python = ">=3.9"` and the lower leg of the CI matrix; the Anaconda install is deliberately
left unrepaired, so never invoke a bare `python`.

```bash
# Windows: prefix commands with the venv interpreter
.venv/Scripts/python.exe -m unittest discover -s tests

# Install for development (editable, with dev extras)
.venv/Scripts/python.exe -m pip install -e ".[dev]"

# Run the CLI
.venv/Scripts/python.exe -m pyisomme --help
.venv/Scripts/python.exe -m pyisomme <command> --help   # list | merge | report | plot

# Run a single test module / case / method
.venv/Scripts/python.exe -m unittest tests.test_report
.venv/Scripts/python.exe -m unittest tests.test_report.TestReport
.venv/Scripts/python.exe -m unittest tests.test_report.TestReport.test_EuroNCAP_Frontal_50kmh
```

Note: tests (`tests/test.py`, `tests/test_report.py`, etc.) read real fixture data from `data/` (e.g. `data/nhtsa/…`, `data/iso-mme-org/…`) and report tests write `.pptx` output into an `out/` directory. Fixture folders are largely untracked and must exist locally for those tests to pass.

**Runtime:** everything outside `tests/test_report.py` runs in ~6 s; the 13 report tests take ~12 min
together (`test_EuroNCAP` alone several minutes). Run report tests individually while iterating — a
full `discover` will blow past a 10-minute command timeout.

## Core Architecture

The domain model is a three-level hierarchy, all re-exported from the top-level `pyisomme` package ([pyisomme/__init__.py](pyisomme/__init__.py)):

- **`Isomme`** ([pyisomme/isomme.py](pyisomme/isomme.py)) — one test container. Holds `test_number`, `test_info`/`channel_info` (`Info` objects), and a `channels` list. `Isomme().read(path)` dispatches on file type (`.mme`, `.chn`, `.001`, folder, `.zip`, `.tar`, `.tar.gz`) to the matching `read_from_*` method. `write` mirrors this. Parsing lives in [pyisomme/parsing.py](pyisomme/parsing.py).
- **`Channel`** ([pyisomme/channel.py](pyisomme/channel.py)) — one signal: a `Code`, a pandas `DataFrame` (`data`), a `Unit`, and `Info`. Supports operator overloading (`+ - * / **`), `.cfc(...)` filtering, `.integrate()`, `.differentiate()`, unit conversion, offset/scale.
- **`Code`** ([pyisomme/code.py](pyisomme/code.py)) — a `str` subclass enforcing the **16-character ISO-MME channel code**. Each fixed-width slice is a named component: `test_object`, `position`, `main_location` (4), `fine_location_1/2/3` (2 each), `physical_dimension` (2), `direction`, `filter_class`. Descriptions and default SI units come from [pyisomme/channel_codes.xml](pyisomme/channel_codes.xml) (packaged data — see `package-data` in [pyproject.toml](pyproject.toml)).

### Channel lookup and lazy computation (the most important concept)

`Isomme.get_channel(*code_patterns, filter=, calculate=, differentiate=, integrate=)` and `get_channels(...)` are the primary access API. Code patterns are **fnmatch/regex-style with `?` wildcards**. If a requested channel does not exist as raw data, `get_channel` will *synthesize* it on demand by, in order: returning an existing match → CFC-filtering an unfiltered channel (pattern ending in `[ABCD]`) → **calculating** it (resultants from X/Y/Z or 1/2/3, plus criteria like BrIC, HIC, xms, ...) → differentiating/integrating. When adding a new derived quantity, extend this dispatch in `get_channel` and implement the math in [pyisomme/calculate.py](pyisomme/calculate.py) (functions decorated with `@debug_logging`).

### Reports (PowerPoint generation)

Reports live under [pyisomme/report/](pyisomme/report/), one subpackage per protocol family: `euro_ncap/`, `un/`, `us_ncap/`, `iihs/`, `fmvss/`, `correlation/`. Key building blocks:

- **`Report`** ([pyisomme/report/report.py](pyisomme/report/report.py)) — takes an `isomme_list`, builds a tree of criteria and a list of `Page`s. `.calculate()` evaluates all criteria; `.export_pptx(path, template)` renders slides via `python-pptx`. `MetaReport` composes several sub-reports (e.g. the top-level `EuroNCAP` bundles frontal/side load cases).
- **`Criterion`** ([pyisomme/report/criterion.py](pyisomme/report/criterion.py)) — a nested, self-registering assessment unit. Subclasses implement `calculation()` (sets `.value`, `.rating`, `.color`, attaches `.channel` and `Limit`s). Criteria are discovered reflectively: any attribute that is a `Criterion` instance is treated as a subcriterion (see `get_subcriterion`/`get_subcriteria` and `print_results`). A concrete report (e.g. [pyisomme/report/euro_ncap/frontal_50kmh.py](pyisomme/report/euro_ncap/frontal_50kmh.py)) defines its criterion tree as nested inner classes.
- **`Page`** ([pyisomme/report/page.py](pyisomme/report/page.py)) — one slide; `construct(presentation)` draws it, often via the plotting helpers.
- **`Limit`/`Limits`** ([pyisomme/limits.py](pyisomme/limits.py)) — threshold curves/values matched to channels by code patterns; used both for rating criteria and for drawing limit bars in plots. Per-protocol limit definitions live in each subpackage's `limits.py`.

To add a new report/load case: create a module in the appropriate protocol subpackage, subclass `Report` (or `MetaReport`) with its `name`/`title`/`protocols`, define the criterion tree, register the class in that subpackage's `__init__.py`, and add it to the `REPORTS` list in [pyisomme/__main__.py](pyisomme/__main__.py) so it is reachable from the `report` CLI command.

### Plotting

[pyisomme/plotting.py](pyisomme/plotting.py) provides matplotlib-based `Plot_*` classes (line plots, tables) used by report pages and by the `plot` CLI command to compare multiple `Isomme`s and overlay limit bars.

## Conventions

- Every module uses `logging.getLogger(__name__)`; the CLI and tests configure logging levels. Prefer logger calls over prints in library code (reports intentionally `print` results).
- Modules rely on `from __future__ import annotations` and string/forward-ref typing.
- Units are handled through `astropy.units` wrapped by [pyisomme/unit.py](pyisomme/unit.py); acceleration in "g" maps to `g0`. Convert with `Channel.convert_unit()`, not by mutating `.data` directly.
- Writing methods do **not** warn before overwriting files — be careful with `merge` and `write`.
- Only `.mme`, `.chn`, and channel-data files (`.001`, `.002`, ...) are read/written; videos, photos, and other files are ignored.

## Bundled subprojects (not part of the pyisomme package)

- [head-trajectory-calculation/](head-trajectory-calculation/) — standalone analysis script.

## Third-party dependencies

- `objective_rating_metrics` (ISO 18571 correlation rating, used by [pyisomme/correlation.py](pyisomme/correlation.py)) is installed from PyPI via the `dev` extra in [pyproject.toml](pyproject.toml) — it is *not* vendored in-repo. Bump the version pin there when a new upstream release is needed.
