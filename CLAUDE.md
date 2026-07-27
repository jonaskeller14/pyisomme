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

**Every step ends with a manual review — do not commit it yourself.** Finish the work, append the progress
entry, leave everything in the working tree, and hand over a summary: what changed file by file, what was
verified (commands and their output), what deviates from the plan, what is still open. The maintainer
reads the diff and decides; commit only when explicitly asked to. This applies to the refactor steps and
to any other change in this repo.

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

**Runtime:** the full suite is ~6 min (112 tests). Everything outside `tests/test_report.py` and
`tests/test_golden.py` runs in ~6 s. Four report tests are opt-in because they take 79–112 s each:

```bash
PYISOMME_SLOW=1 .venv/Scripts/python.exe -m unittest tests.test_report   # include the slow four
```

Known limitation: running **all 13** report tests in one process (i.e. `tests.test_report` with
`PYISOMME_SLOW=1`) dies with a Windows stack overflow (exit `0xC00000FD`) partway through, somewhere
after `test_EuroNCAP_Side_Pole`. This is pre-existing (reproduced on the Step-2 tip) and unrelated to
correctness — every one of those tests passes when run on its own. Run the slow four individually.

### Static checking

Both are configured in [pyproject.toml](pyproject.toml) and both are **blocking in CI** since refactor
step 3, so keep them clean:

```bash
.venv/Scripts/python.exe -m ruff check .        # whole repo (docs/ notebooks excluded)
.venv/Scripts/python.exe -m mypy                # scoped to pyisomme/report/ by [tool.mypy] files=
```

- `mypy` is deliberately scoped to `pyisomme/report/` with `disallow_untyped_defs`. The core modules are
  still analysed (report/ needs their signatures) but their own errors are silenced through a
  `follow_imports = "silent"` override — widen `files` and drop that override when the core is annotated.
- `Report` is generic in its overall criterion. **Each report module defines its criterion tree as a
  module-level class named `Overall`**, and the report declares `class X(Report[Overall])` with
  `Criterion_Overall = Overall`. So `report.overall(isomme).criterion_driver…` — and any manual-input
  assignment on it — is checked end to end. Reuse across protocols imports the other module's tree
  directly (`from …frontal_50kmh import Overall as Overall_Frontal_50kmh`), never
  `OtherReport.Criterion_Overall.…`. `Page`/`Criterion` subclasses that walk the tree
  narrow `report:` to the concrete report class; classes reused **across** reports keep the base `Report`
  and stay unchecked (that duplication is what steps 9–10 remove).
- `Criterion.require_channel(...)` replaces `self.isomme.get_channel(...)` at every site that
  dereferences the result. A missing channel is a clean `Status.NA` naming the pattern, not an
  `AttributeError` swallowed into `Status.ERROR`. Do not reintroduce the raw call in a criterion.
- `pyisomme/py.typed` ships the annotations to downstream users.

### The refactor safety net

Two test modules exist purely to make the report refactor verifiable — read `tests/golden_utils.py`
before changing either:

- **`tests/test_golden.py`** — constructs `EuroNCAP_Frontal_50kmh`, `EuroNCAP_Frontal_MPDB` and
  `EuroNCAP_Side_Barrier`, then
  compares them against committed snapshots in `tests/golden/` (**tracked**, unlike `data/`). Two layers:
  a *definition* layer (criterion paths, names, all `Limit` rows — data-independent, so it works even
  where every value is `nan`) compared exactly, and a *results* layer (`value`/`rating`/`color`/`status`)
  compared with **no-regression** semantics: known numbers must stay identical, but a `nan` becoming a
  number — or an `ERROR` becoming `NA` — is reported as an improvement and tolerated. `nan == nan` (G9).
- **`tests/test_report_structure.py`** — the same *definition* layer, but for **all 13** reports and with
  **no fixture data at all**: each report is built from empty `Isomme` objects, so it runs in CI. Snapshot
  in `tests/golden/report_structure.json` (tracked). It catches a reparented criterion, a lost `Limit` row
  or a dropped page — the things a structural refactor breaks silently. Re-baseline deliberately with
  `python -m tests.test_report_structure --regen`. A report module defining an `Overall` but missing from
  its `REPORTS` list fails the coverage guard; deliberate omissions go in `EXCLUDED` with a reason.
- **`tests/test_report_modules.py`** — imports every module under `pyisomme/report/` and checks that each
  protocol subpackage is reachable as an attribute of `pyisomme.report` *in a fresh interpreter*. Needs no
  fixture data, so it is the one report test that can run in CI. Known breakage sits in explicit
  `BROKEN_MODULES` / `MISSING_REEXPORTS` sets with `TODO(step-…)` comments, guarded by staleness tests
  that fail if an entry becomes stale. Both sets are **empty** since Step 2 — everything imports and every
  subpackage is re-exported; re-populate them only with a `TODO(step-…)` naming the owning step.

When a step legitimately changes a number, re-baseline **deliberately** and explain the diff in the
progress log — the tests never rewrite the files themselves:

```bash
.venv/Scripts/python.exe -m tests.golden_regen                       # all
.venv/Scripts/python.exe -m tests.golden_regen euro_ncap_side_barrier
git diff tests/golden/
```

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
- **`Criterion`** ([pyisomme/report/criterion.py](pyisomme/report/criterion.py)) — a nested, self-registering assessment unit. Subclasses implement `calculation()` (sets `.value`, `.rating`, `.color`, attaches `.channel` and `Limit`s). Criteria are discovered reflectively: any attribute that is a `Criterion` instance is treated as a subcriterion (see `get_subcriterion`/`get_subcriteria` and `print_results`). A concrete report (e.g. [pyisomme/report/euro_ncap/frontal_50kmh.py](pyisomme/report/euro_ncap/frontal_50kmh.py)) defines its criterion tree as a **module-level class named `Overall`** whose children are nested inner classes.
- **`Page`** ([pyisomme/report/page.py](pyisomme/report/page.py)) — one slide; `construct(presentation)` draws it, often via the plotting helpers.
- **`Limit`/`Limits`** ([pyisomme/limits.py](pyisomme/limits.py)) — threshold curves/values matched to channels by code patterns; used both for rating criteria and for drawing limit bars in plots. Per-protocol limit definitions live in each subpackage's `limits.py`.

To add a new report/load case: create a module in the appropriate protocol subpackage; define its criterion tree as a module-level `class Overall(Criterion)`; declare `class X(Report[Overall])` with `Criterion_Overall = Overall` and its `name`/`title`/`protocols`; register the class in that subpackage's `__init__.py`; add it to the `REPORTS` list in [pyisomme/__main__.py](pyisomme/__main__.py) so it is reachable from the `report` CLI command; and add it to `REPORTS` in [tests/test_report_structure.py](tests/test_report_structure.py) (a coverage guard fails otherwise).

### Manual inputs

A value the report cannot measure — an engineer's judgement, a hand measurement, a seating
assumption — is a **manual input**: the user overwrites it between constructing the report and
calling `calculate()`. Since refactor step 4 they are *declared*, in
[pyisomme/report/manual.py](pyisomme/report/manual.py):

```python
class Criterion_Submarining(Criterion):
    submarining: Manual[bool, manual(False, source="video", unit=None,
                                     doc="Pelvis slid under the lap belt")]
```

- **No `= False`.** The `manual(...)` default is installed as the class attribute the first time a
  criterion of that class is constructed, so `self.submarining` reads work unchanged.
- `Manual` is `typing.Annotated`, so mypy still sees a plain `bool` — everything step 3 made
  checkable stays checkable. Declare it with `Manual[T, manual(...)]`, never as a bare attribute:
  an undeclared class attribute is *not* a manual input and will not be enumerated.
- **`Criterion.__setattr__` rejects any name the class does not declare**, with a "did you mean …?"
  suggestion, and rejects a wrongly typed value (`bool` is deliberately not accepted for a `float`).
  Its `value` parameter is typed `Undeclared` — an uninhabited class — **on purpose**: a type checker
  consults `__setattr__` only for names the class does not declare, so this keeps step 3's static catch of
  `criterion.hard_contct = False` while a `value: Any` would widen *every* assignment to `Any` and
  delete it. Do not relax that annotation.
  Assigning a `Criterion` (a subcriterion) or a `_`-prefixed name is exempt at runtime.
- `report.print_inputs()` lists every input with path, value, default, unit, doc and source;
  `get_inputs()` / `set_inputs()` round-trip through JSON, so the manual assumptions behind a run can
  be stored beside the ISO-MME container and replayed. `MetaReport` nests one level deeper, keyed by
  sub-report.
- **Inputs are read in `calculation()`, never in `__init__`** (F15). The exception is the seating
  position: children are *constructed* with `p=`, which is baked into their limits' code patterns, so
  each `Overall` calls `sync_positions()` at the top of `calculation()` and uses
  `Criterion.rebuild_child()` to rebuild an occupant subtree when its position changed — preserving
  the subtree's manual inputs and dropping its stale report-level limits. Step 7's lazy `Ctx`
  replaces this.

[tests/test_manual_inputs.py](tests/test_manual_inputs.py) covers all of it and needs no fixture data.

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
