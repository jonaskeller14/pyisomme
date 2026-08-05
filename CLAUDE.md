# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

pyisomme is a Python library and CLI for the **ISO-MME** crash-test data file format. It reads/writes ISO-MME containers, manipulates signal channels (filter, integrate, differentiate, arithmetic), computes injury-risk criteria (HIC, a3ms, DAMAGE, OLC, BrIC, NIJ, ...), plots curves, and generates PowerPoint assessment reports (Euro-NCAP, UN-R94/R137, US-NCAP, IIHS).

## Current work — `pyisomme.report` refactor

An incremental refactor of the report architecture is in progress. Before touching anything under
[pyisomme/report/](pyisomme/report/), read:

- **[docs/log/20260726_Report-Architecture-Review_plan.md](docs/log/20260726_Report-Architecture-Review_plan.md)** — the step-by-step plan, ground rules and per-step acceptance criteria. Work **one step at a time**; do not stray outside the step's scope.
- **[docs/log/20260726_Report-Architecture-Review_progress.md](docs/log/20260726_Report-Architecture-Review_progress.md)** — running log of what is done, decisions taken and open questions. **Every session must append an entry here before finishing.**
- [docs/log/20260726_Report-Architecture-Review.md](docs/log/20260726_Report-Architecture-Review.md) — the rationale (findings F1–F15, proposals P1–P11). Consult only the IDs your step names.

Invariants that must survive the refactor: NaN propagation is intentional (never swap in `np.nan*` to hide missing data); the criterion tree is eagerly constructed and user-mutable (manual inputs are set between construction and `calculate()`); criterion nesting stays.

**Every change ends with a manual review — do not commit it yourself.** Finish the work, append the
progress entry, leave everything in the working tree, and hand over a summary: what changed file by file,
what was verified (commands and their output), what deviates from the plan, what is still open. Commit
only when explicitly asked to. This applies to the refactor steps and to any other change in this repo.

## Commands

**Use the repo venv.** The `python` on `PATH` is a broken Anaconda 3.12 that cannot even `import
pyisomme` and is deliberately left unrepaired; `.venv` is Python **3.9.13** (the development target,
matching `requires-python` and the lower CI leg) with the `dev` extra installed.

```bash
.venv/Scripts/python.exe -m unittest discover -s tests
.venv/Scripts/python.exe -m pip install -e ".[dev]"      # editable install with dev extras

.venv/Scripts/python.exe -m pyisomme --help
.venv/Scripts/python.exe -m pyisomme <command> --help    # list | merge | report | plot

# Run a single test module / case / method
.venv/Scripts/python.exe -m unittest tests.test_golden
.venv/Scripts/python.exe -m unittest tests.test_golden.TestGolden.test_all_reports
```

The result goldens use deterministic synthetic channels and need no untracked `data/` fixtures.
PowerPoint export is deliberately opt-in; request all reports or a comma-separated subset by stem:

```powershell
$env:PYISOMME_PPTX='1'; .venv/Scripts/python.exe -m unittest tests.test_report
$env:PYISOMME_PPTX='euro_ncap_side_pole'; .venv/Scripts/python.exe -m unittest tests.test_report
```

Both result-golden calculations and PPTX exports isolate each report in a fresh process. This avoids
the known Windows stack overflow when all 13 reports are calculated in one interpreter.

### Static checking

Both are configured in [pyproject.toml](pyproject.toml) and **blocking in CI**, so keep them clean:

```bash
.venv/Scripts/python.exe -m ruff check .        # whole repo (docs/ notebooks excluded)
.venv/Scripts/python.exe -m mypy                # scoped to pyisomme/report/ by [tool.mypy] files=
```

- `mypy` is deliberately scoped to `pyisomme/report/` with `disallow_untyped_defs`. Core modules are
  analysed for their signatures but their own errors are silenced via a `follow_imports = "silent"`
  override — widen `files` and drop that override when the core is annotated.
- `Report` is generic in its overall criterion. **Each report module defines its criterion tree as a
  module-level class named `Overall`**, and the report declares `class X(Report[Overall])` with
  `Criterion_Overall = Overall`, so `report.overall(isomme).criterion_driver…` is checked end to end.
  Reuse across protocols imports the other module's tree directly
  (`from …frontal_50kmh import Overall as Overall_Frontal_50kmh`), never `OtherReport.Criterion_Overall`.
  `Page`/`Criterion` subclasses that walk the tree narrow `report:` to the concrete report class; classes
  reused **across** reports keep the base `Report` and stay unchecked (steps 9–10 remove that).
- `Criterion.require_channel(...)` replaces `self.isomme.get_channel(...)` at every site that
  dereferences the result: a missing channel becomes a clean `Status.NA` naming the pattern instead of an
  `AttributeError` swallowed into `Status.ERROR`. Do not reintroduce the raw call in a criterion.
- `pyisomme/py.typed` ships the annotations to downstream users.

### The refactor safety net

Three test modules make the report refactor verifiable — read `tests/golden_utils.py` and
`tests/report_registry.py` before changing any of them.

- **`tests/test_golden.py`** — builds all 13 concrete reports plus the `EuroNCAP` MetaReport with complete deterministic synthetic
  channels and compares full-precision `value`/`rating`/`color`/`status` snapshots with no-regression
  semantics. Known numbers must stay identical; `nan` becoming a number or `ERROR` becoming `NA` is an
  improvement. `print_results()` is captured too, as an exact rendering/order contract. Every report is
  calculated in a fresh process; no `data/` fixture or PPTX export is involved.
- **`tests/test_describe.py`** — exact, fixture-free Markdown definition snapshots for all 13 reports:
  pages, criterion paths/classes, sources, point budgets, aggregation, every `Limit` row and every manual
  input. It also owns the registry coverage guard; deliberate omissions carry a reason in
  `tests/report_registry.py`. This is the single definition snapshot—do not duplicate it in result JSON.
- **`tests/test_report_modules.py`** — imports every module under `pyisomme/report/` and checks each
  protocol subpackage is reachable as an attribute of `pyisomme.report` in a fresh interpreter. Known
  breakage sits in `BROKEN_MODULES` / `MISSING_REEXPORTS` with a `TODO(step-…)` naming the owning step,
  guarded by staleness tests. Both sets are **empty** — keep them that way.

When a change legitimately changes a snapshot, re-baseline **deliberately** and explain the diff in the
progress log — the tests never rewrite the files themselves:

```bash
.venv/Scripts/python.exe -m tests.golden_regen                       # all (or one, by name)
.venv/Scripts/python.exe -m tests.test_describe --regen
git diff tests/golden/
```

### `validate()` and `describe()`

A report can check and explain its own *definition*. Both are fixture-free — they read the criterion tree
and its `Limit` rows, never measurement data — so they run in CI.
[tests/test_validate.py](tests/test_validate.py) and [tests/test_describe.py](tests/test_describe.py)
cover them (the latter reuses the former's `build`/`leaf`/`attach` helpers).

- **`Report.validate()`** ([pyisomme/report/validate/](pyisomme/report/validate/)) → `list[Issue]`, empty
  when clean; `report.print_validation()` prints it. **Errors** are wrong whatever the protocol says
  (unnamed criterion, a code pattern that cannot match a 16-character code, an orphaned limit).
  **Warnings** are deviations from a *convention* (`limit_flags`, `limit_capping`, `limit_interpolation`,
  `limit_symmetry`, `limit_unit`) — a protocol is allowed to be irregular, so they never fail on their
  own. They assert *properties* of a hand-written `extend_limit_list` block without owning its numbers;
  thresholds stay literal and PDF-checkable.
- **Silence an intentional deviation on the criterion**, never by loosening a check:
  `validate_ignore = {"limit_symmetry": "shared 0 pt. row spans both signs"}`. The reason is mandatory.
- **One check, one module.** `validate/` holds a `check_<name>.py` per check, all listed in `CHECKS` in
  [validate/validate.py](pyisomme/report/validate/validate.py), which also owns the entry points
  (`validate_criterion`/`validate_tree`/`validate_report`). Shared helpers for reading a flat limit list
  back into blocks live in [validate/util.py](pyisomme/report/validate/util.py); `Issue` in
  [validate/issue.py](pyisomme/report/validate/issue.py). Import from the package, not from a module
  inside it. To add a check, write `check_<name>(path, criterion) -> Iterator[Issue]` and append it to
  `CHECKS`; `<name>` is both the string its findings carry and the `validate_ignore` key.
- **`Report.describe()`** ([pyisomme/report/describe.py](pyisomme/report/describe.py)) → Markdown: every
  criterion with class, `source`, max rating, aggregation, every `Limit` row and every manual input.
  Committed per reference report under `tests/golden/describe/`, so a moved threshold shows up as a line
  in a pull request instead of a character in a 1500-line module.

```bash
.venv/Scripts/python.exe -m tests.test_validate --regen    # tests/golden/validate.json
.venv/Scripts/python.exe -m tests.test_describe --regen    # tests/golden/describe/*.md
```

**Definition metadata on `Criterion` — declare the minimum.** `source`, `max_rating` and `aggregation`
are read only by `validate()`/`describe()`; nothing in `calculation()` consumes them.

- `max_rating` on a **leaf is derived** from its limit block — never declare it.
- `max_rating` on an **aggregate** is the protocol's point budget (a Euro-NCAP body region is 4, an
  occupant 16, the frontal load case 8) and nothing else records it — declare it there.
- `aggregation` (`"min"`/`"sum"`/`"mean"`/`"max"`/`"first"`) makes that checkable: the parent's budget
  must equal the aggregation of its children's. Only declare it where one rule really covers all
  children; leave it unset rather than writing something untrue.
- `source` is the protocol **section** (`"§5.2.1"`, not the whole document reference) — the one field no
  code can recover. It is **inherited down the tree**, so declaring it on `Overall` alone is complete;
  refine it where the PDF has a narrower section, and leaves never repeat it.

## Core Architecture

The domain model is a three-level hierarchy, all re-exported from the top-level `pyisomme` package ([pyisomme/__init__.py](pyisomme/__init__.py)):

- **`Isomme`** ([pyisomme/isomme.py](pyisomme/isomme.py)) — one test container. Holds `test_number`, `test_info`/`channel_info` (`Info` objects), and a `channels` list. `Isomme().read(path)` dispatches on file type (`.mme`, `.chn`, `.001`, folder, `.zip`, `.tar`, `.tar.gz`) to the matching `read_from_*` method. `write` mirrors this. Parsing lives in [pyisomme/parsing.py](pyisomme/parsing.py).
- **`Channel`** ([pyisomme/channel.py](pyisomme/channel.py)) — one signal: a `Code`, a pandas `DataFrame` (`data`), a `Unit`, and `Info`. Supports operator overloading (`+ - * / **`), `.cfc(...)` filtering, `.integrate()`, `.differentiate()`, unit conversion, offset/scale.
- **`Code`** ([pyisomme/code.py](pyisomme/code.py)) — a `str` subclass enforcing the **16-character ISO-MME channel code**. Each fixed-width slice is a named component: `test_object`, `position`, `main_location` (4), `fine_location_1/2/3` (2 each), `physical_dimension` (2), `direction`, `filter_class`. Descriptions and default SI units come from [pyisomme/channel_codes.xml](pyisomme/channel_codes.xml) (packaged data — see `package-data` in [pyproject.toml](pyproject.toml)).

### Channel lookup and lazy computation (the most important concept)

`Isomme.get_channel(*code_patterns, filter=, calculate=, differentiate=, integrate=)` and `get_channels(...)` are the primary access API. Code patterns are **fnmatch/regex-style with `?` wildcards**. If a requested channel does not exist as raw data, `get_channel` will *synthesize* it on demand by, in order: returning an existing match → CFC-filtering an unfiltered channel (pattern ending in `[ABCD]`) → **calculating** it (resultants from X/Y/Z or 1/2/3, plus criteria like BrIC, HIC, xms, ...) → differentiating/integrating. When adding a new derived quantity, extend this dispatch in `get_channel` and implement the math in [pyisomme/calculate/](pyisomme/calculate/) (functions decorated with `@debug_logging`).

### Reports (PowerPoint generation)

Reports live under [pyisomme/report/](pyisomme/report/), one subpackage per protocol family: `euro_ncap/`, `un/`, `us_ncap/`, `iihs/`, `fmvss/`, `correlation/`. Key building blocks:

- **`Report`** ([pyisomme/report/report.py](pyisomme/report/report.py)) — takes an `isomme_list`, builds a tree of criteria and a list of `Page`s. `.calculate()` evaluates all criteria; `.export_pptx(path, template)` renders slides via `python-pptx`. `MetaReport` composes several sub-reports (e.g. the top-level `EuroNCAP` bundles frontal/side load cases).
- **`Criterion`** ([pyisomme/report/criterion.py](pyisomme/report/criterion.py)) — a nested assessment unit. Subclasses implement `calculation()` (sets `.value`, `.rating`, `.color`, attaches `.channel` and `Limit`s). Children are declared with `sub()` (below); a criterion assigning them in `__init__` instead still works, and `get_children()` returns both, in **protocol order** — declared children in declaration order, then the ones `__init__` assigned, in the order it assigned them. Never alphabetical, and never `dir()`.
- **`Page`** ([pyisomme/report/page/](pyisomme/report/page/)) — one slide; `construct(presentation)` draws it, often via the plotting helpers. One module per template, all re-exported from the package: import `from pyisomme.report.page import Page_Plot_nxn`, never from a module inside it. `Page_Content` is a titled slide with a footer; `Page_Figure` adds the "measure the content placeholder, remove it, render a figure into the freed area" boilerplate, so a figure page only implements `figure(figsize) -> Figure`.
- **`Limit`/`Limits`** ([pyisomme/limits.py](pyisomme/limits.py)) — threshold curves/values matched to channels by code patterns; used both for rating criteria and for drawing limit bars in plots. Per-protocol limit definitions live in each subpackage's `limits.py`.

### The criterion tree: `sub()`, `Ctx` and `Role`

Step 7's framework, piloted on `euro_ncap/frontal_50kmh.py` in Step 8 and rolled out to all 13 reports
in Step 9. It is the only style now — no report threads `p` through its constructors any more.

```python
P_DRIVER = manual("1", source="test report", doc="Channel-code position of the driver.")

class Head(Criterion):
    name, max_rating, source = "Head", 4., "§4.1.1"
    hard_contact: Manual[bool, manual(True, source="video", doc="…")]

    hic15           = sub(HIC15)
    a3ms            = sub(HeadA3ms)
    steering_column = sub(DisplacementSteeringColumn, role=Role.MODIFIER)

    def calculation(self) -> None:            # aggregation only — the children are done
        self.rating = np.min([self.hic15.rating, self.a3ms.rating]) if self.hard_contact else 4.
        self.rating += self.modifiers_sum()

class Overall(Criterion):
    role = Role.AGGREGATE
    p_driver: Manual[str, P_DRIVER]           # the same object the `at=` below points at

    driver = sub(Driver, at=from_input(P_DRIVER), role=Role.AGGREGATE)
```

- **`sub(cls, *, name=…, at=…, role=…)`** is the one place a child is wired. It is **eager** (G8): the
  child is constructed with its parent, so the whole tree exists and is mutable before `calculate()`,
  which is when users set manual inputs. `sub` is `Generic[C]` with `__get__` overloads, so
  `self.driver.head.hic15.rating` resolves to `float` in mypy and in the IDE, and a typo in the chain
  is a static error. Inner classes stay nested (G4) and must be **defined above** the `sub()` line.
  `add_child(name, criterion)` is the escape hatch for a tree whose shape depends on the data.
- **`calculate()` is `prepare()` → `apply_limits()` → children in order → `calculation()`.** Only
  framework-owned children (declared + `add_child`) are calculated automatically, so a parent that
  calls `child.calculate()` itself does not run them twice. `prepare()` is the hook for
  deriving inputs the *children's* context depends on — it runs before them; `calculation()` runs
  after and is pure aggregation.
- **`Ctx`** ([pyisomme/report/ctx.py](pyisomme/report/ctx.py)) replaces threading `p` through
  constructors. It carries `report`, `isomme` and an immutable mapping of **code-template fields**, and
  **nothing occupant-specific** — 11 criteria under `euro_ncap/` + `iihs/` have no position and the
  correlation report is built from channels, so constructing or calculating a criterion must never
  require an occupant. `self.code("?{p}NECKUP00??MOY?")` fills the template; a template with no
  placeholder passes through, and a placeholder with no field is a clean `Status.NA` naming it. The
  chain is resolved **lazily at the start of `calculate()`**, which is the real F15 fix.
- **`at=` takes a `CtxSource`.** `where(p="1")` is literal fields; `from_input(P_DRIVER)` reads a
  **manual input on the nearest ancestor that declares it**, so it is not a second source of truth.
  Anything else a report needs — a barrier, a trolley, a second test object — is another
  implementation and needs **no change to `criterion.py`**.
- **`from_input` takes the declaration, not its name.** Hoist the `manual(...)` to a module-level
  constant and reference that same object from both the `Manual[...]` annotation and the `at=`; the
  link is then a real Python name that `mypy` and `ruff` check, so a rename or a typo is a static
  error instead of a `Status.NA` nobody reads. Matching is by **identity** (`manual` is a frozen
  dataclass, so two unrelated inputs with the same default and doc compare equal). `from_input("p")`
  still works and is the escape hatch for a declaration in another module.
- **A seating position is a `str`, not an `int`** — it is one character of `channel_codes.xml`'s
  `Position` element, `"1"`–`"9"` and `"A"`–`"Z"` (`?A…` is a valid code, `?10…` is not a code).
  `Ctx.FieldValue` is `str` for the same reason, and a `get_inputs()` file saved before this
  (`"p_driver": 1`) is **rejected** by the declaration's own type check rather than coerced.
- **`define_limits() -> list[Limit]`** replaces building rows in `__init__`: the framework calls it
  when the context is known and swaps the criterion's rows in both its own list and the report-level
  one, so a position set after construction moves the limits too. It is a no-op unless overridden.
  Rows stay hand-written — the hook decides *when* they are built, never what is in them.
  `Report.__init__` runs one `Criterion.build_limits()` pass over the finished tree, so `validate()`,
  `describe()` still sees the rows on a report nobody calculated.
  It cannot happen in `Criterion.__init__`: construction is bottom-up, so a node has no parent — and
  therefore no context — until its own subtree already exists.
- **`Role`** says what a node *is*, and never restricts `calculation()`: `RESULT` measures and rates,
  `AGGREGATE` derives its rating from its children (arbitrary logic allowed), `MODIFIER` is an
  adjustment added on top of the aggregate, typically ≤ 0 points. The aggregation helpers
  (`min_of_children`, `sum_of_children`, `max_of_children`, `mean_of_children`, `modifiers_sum`) take
  `RESULT` + `AGGREGATE` and exclude `MODIFIER`. Do not confuse it with the separate `aggregation`
  declaration above, which is the constrained one.
- **All aggregation helpers propagate NaN (G9)** — `np.min`/`np.sum`/`np.mean`, never the `nan*`
  variants. The one NaN-tolerant path is `mean_of_children(skip_missing="<reason>")`; the reason is
  mandatory and is recorded on `Criterion.skip_missing` when it actually drops a child.

[tests/test_criterion_tree.py](tests/test_criterion_tree.py) covers all of it and needs no fixtures.

To add a new report/load case: create a module in the appropriate protocol subpackage; define its criterion tree as a module-level `class Overall(Criterion)`; declare `class X(Report[Overall])` with `Criterion_Overall = Overall` and its `name`/`title`/`protocols`; register the class in that subpackage's `__init__.py`; add it to the `REPORTS` list in [pyisomme/__main__.py](pyisomme/__main__.py) so it is reachable from the `report` CLI command; and add a `ReportSpec` to [tests/report_registry.py](tests/report_registry.py) (a coverage guard fails otherwise).

### Manual inputs

A value the report cannot measure — an engineer's judgement, a hand measurement, a seating
assumption — is a **manual input**: the user overwrites it between constructing the report and
calling `calculate()`. They are *declared*, in [pyisomme/report/manual.py](pyisomme/report/manual.py):

```python
class Criterion_Submarining(Criterion):
    submarining: Manual[bool, manual(False, source="video", unit=None,
                                     doc="Pelvis slid under the lap belt")]
```

- **No `= False`.** The `manual(...)` default is installed as the class attribute the first time a
  criterion of that class is constructed, so `self.submarining` reads work unchanged.
- `Manual` is `typing.Annotated`, so mypy still sees a plain `bool`. Declare it with
  `Manual[T, manual(...)]`, never as a bare attribute: an undeclared class attribute is *not* a manual
  input and will not be enumerated.
- **`Criterion.__setattr__` rejects any name the class does not declare**, with a "did you mean …?"
  suggestion, and rejects a wrongly typed value (`bool` is deliberately not accepted for a `float`).
  Its `value` parameter is typed `Undeclared` — an uninhabited class — **on purpose**: a type checker
  consults `__setattr__` only for undeclared names, so this keeps the static catch of
  `criterion.hard_contct = False`, while `value: Any` would widen *every* assignment to `Any`. Do not
  relax that annotation. Assigning a `Criterion` (a subcriterion) or a `_`-prefixed name is exempt at
  runtime.
- `report.print_inputs()` lists every input with path, value, default, unit, doc and source;
  `get_inputs()` / `set_inputs()` round-trip through JSON, so the manual assumptions behind a run can be
  stored beside the ISO-MME container and replayed. `MetaReport` nests one level deeper, keyed by
  sub-report.
- **Inputs are read in `calculation()`, never in `__init__`** (F15). The one thing an `Overall`
  *does* do at construction is call its own `prepare()`, because the pages build their channel
  patterns from `p_driver`/`p` when the report is built; `prepare()` only ever fills a position with
  `set_derived_input`, which never overwrites a user-set value. Every report is migrated as of
  Step 9, so nothing rebuilds a subtree when a position changes any more — `Ctx` + `seat()`/
  `from_input()` + `prepare()` resolve it lazily at the start of `calculate()`.

[tests/test_manual_inputs.py](tests/test_manual_inputs.py) covers all of it and needs no fixture data.

### Plotting

[pyisomme/plotting/](pyisomme/plotting/) provides matplotlib-based `Plot_*` classes (line plots, tables) used by report pages and by the `plot` CLI command to compare multiple `Isomme`s and overlay limit bars. One module per class — `Plot` in [plot.py](pyisomme/plotting/plot.py), `Plot_Line`, `Plot_Table`, `Plot_Line_Table` — all re-exported from the package: import `from pyisomme.plotting import Plot_Line`, never from a module inside it (same rule as `report/page/`).

`plt.subplots()` is unstubbed in matplotlib 3.7.5, so each `plot()` narrows its figure with `fig = cast(Figure, fig)`; `Figure.patch` stays unresolvable even then and is reached via the `getattr` guard in the two table classes.

## Conventions

- Every module uses `logging.getLogger(__name__)`; the CLI and tests configure logging levels. Prefer logger calls over prints in library code (reports intentionally `print` results).
- Modules rely on `from __future__ import annotations` and string/forward-ref typing.
- Units are handled through `astropy.units` wrapped by [pyisomme/unit.py](pyisomme/unit.py); acceleration in "g" maps to `g0`. Convert with `Channel.convert_unit()`, not by mutating `.data` directly. A raw astropy unit must never reach `Channel.unit`.
- Writing methods do **not** warn before overwriting files — be careful with `merge` and `write`.
- Only `.mme`, `.chn`, and channel-data files (`.001`, `.002`, ...) are read/written; videos, photos, and other files are ignored.

## Bundled subprojects (not part of the pyisomme package)

- [head-trajectory-calculation/](head-trajectory-calculation/) — standalone analysis script.

## Third-party dependencies

- `objective_rating_metrics` (ISO 18571 correlation rating, used by [pyisomme/correlation.py](pyisomme/correlation.py)) is installed from PyPI via the `dev` extra in [pyproject.toml](pyproject.toml) — it is *not* vendored in-repo. Bump the version pin there when a new upstream release is needed.
