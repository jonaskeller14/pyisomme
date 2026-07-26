# `pyisomme.report` Refactor — Progress Log

Running log for the step-by-step refactor described in [`20260726_Report-Architecture-Review_plan.md`](20260726_Report-Architecture-Review_plan.md).
Rationale lives in [`20260726_Report-Architecture-Review.md`](20260726_Report-Architecture-Review.md).

**Every session must append an entry below before finishing.** A fresh session reads this file to learn
what was done, what was decided, and what was deliberately left alone.

---

## Status board

| Step | Title | Status | Branch / commit |
|---|---|---|---|
| 0 | Fix and standardise the Python environment | ☑ done | `refactor/step-0-env` |
| 1 | Safety net: golden tests + import smoke test | ☐ todo | |
| 2 | Fix known defects (Appendix A1, A5, A6, A9) | ☐ todo | |
| 3 | Typing and lint (P5) | ☐ todo | |
| 4 | Manual inputs as a declared concept (P11) | ☐ todo | |
| 5 | Limit scales: helpers + equivalence proof (P3a) | ☐ todo | |
| 6 | `PeakCriterion` + migrate leaves (P4 + P3b) | ☐ todo | |
| 7 | `sub()` + `Ctx` framework (P1 + P2) | ☐ todo | |
| 8 | Migrate `frontal_50kmh` (pilot) | ☐ todo | |
| 9 | Migrate remaining reports | ☐ todo | |
| 10 | Shared criteria library (P9) | ☐ todo | |
| 11 | Pages select from the tree (P6) | ☐ todo | |
| 12 | `validate()` + `describe()` (P7 + P8) | ☐ todo | |
| 13 | Status propagation and rendering (P10) | ☐ todo | |

Status values: ☐ todo · ◐ in progress · ☑ done · ⚠ done with deviations · ✖ blocked

---

## Open questions for the maintainer

Things a session hit that need a human (usually a protocol/PDF) decision. Add here; do not guess.

| # | Question | Raised in step | Answer |
|---|---|---|---|
| Q1 | **A3** — rear-passenger head logic (`frontal_50kmh.py:864`) appears inverted vs. driver/front: `if hard_contact → a3ms only; else → min(hic, a3ms)`. Correct per AoP? | (review) | |
| Q2 | **A4** — rear-passenger neck aggregates with `np.sum` while driver/front use `np.min`. Intended (caps 2/1/1 = 4 pts)? | (review) | |
| Q3 | **A4c** — passenger positions derived as `1 if p_driver != 1 else 3/6`; `p_rear_passenger` flips 6↔4 as a side effect. Should the seat map be explicit and overridable? | (review) | |
| Q4 | **A15** — `ExceedingForwardExcursionLine` declares 3 manual inputs but driver/front `calculation()` is `self.rating = 0`; only the rear copy implements real logic. Intended, or unfinished? | (review) | |
| Q5 | **A16** — `steering_wheel_airbag_exists` lives on `Criterion_Driver` but is read via a back-reference from Head/Neck; the front-passenger tree never consults it. Should it be per-occupant? | (review) | |
| Q6 | **Step 4** — should `hard_contact` become tri-state (`None` = derive from curve, so a video observation of *no* contact can override a >80 g curve)? This changes the default behaviour. | (plan) | |

---

## Deferred items discovered during implementation

Things noticed mid-step that belong to a later step (or to no step at all). Record instead of fixing.

| # | Item | Noticed in step | Belongs to |
|---|---|---|---|
| D1 | `Page_OLC_Trolley.__init__` (`frontal_mpdb.py:1279`) calls `calculate_olc(isomme.get_channel("M?MBAR*VEXA"))` with no `None` guard → `AttributeError` at **construction** time for any test without a moving-barrier channel. Breaks `EuroNCAP_Frontal_MPDB` *and* the `EuroNCAP` MetaReport on the current fixtures. Not in the review's Appendix A. | 0 | Step 1 (blocks the MPDB golden file — see below) / Step 3 (`require_channel`) |
| D2 | `pyisomme/report/__init__.py` imports only `euro_ncap`, `un`, `iihs` — not `correlation`, `us_ncap`, `fmvss`. So `pyisomme.report.correlation…` fails after a plain `import pyisomme`. `us_ncap/` also still has no `__init__.py`. Not in Appendix A (A5 covers only the `us_ncap` import). | 0 | Step 1 (import smoke test) / Step 2 |
| D3 | CLI `--help` lists `list, merge, report, plot` — CLAUDE.md claimed a non-existent `rename` subcommand. Corrected in this step. | 0 | done |

---

## Session log

Append newest entries at the bottom. Template:

```markdown
### Step <n> — <title>
**Date:** YYYY-MM-DD · **Branch:** refactor/step-<n>-<slug> · **Commit(s):** <sha>
**Outcome:** done / done with deviations / blocked

**What was implemented**
- …

**Decisions taken** (anything the plan left open)
- …

**Behaviour changes** (values, ordering, output text — with before/after numbers, or "none")
- …

**Verification** (commands run and their result)
- `.venv/Scripts/python.exe -m unittest …` → OK (N tests)

**Deviations from the plan / left undone**
- …

**Notes for the next session**
- …
```

---

<!-- Session entries start here -->

### Step -1 — Baseline facts (recorded during planning, no code changed)

**Date:** 2026-07-26 · **Branch:** `dev` · **Commit(s):** none (docs only)

**Environment as found**

| | Interpreter | numpy | scipy | `import pyisomme` |
|---|---|---|---|---|
| `python` on PATH | `C:\ProgramData\anaconda3\python.exe` 3.12.7 | 2.3.5 | 1.12.0 | **fails** (`numpy.dtype size changed`) |
| `.venv` (repo, gitignored) | Python 3.9.13 | 1.26.4 | 1.12.0 | **works** |

`.venv` has all runtime deps plus `objective_rating_metrics` (`dev` extra). `data/` fixtures are present
locally (`iso-mme-org`, `nhtsa`, `pdb-org`, `vtc-loadcase-example`, `tests`).

**Verification run during planning**
- `.venv/Scripts/python.exe -m unittest tests.test_report.TestReport.test_EuroNCAP_Frontal_50kmh` → **OK**, 1 test, 29.0 s.

**Observations worth carrying forward**
- `print_results()` output confirms F6: subcriteria print alphabetically (Chest, Femur, Head, Neck), not in protocol order.
- The full test suite has **not** been run yet — Step 0 must do this and record the baseline.
- `us_ncap/frontal_56kmh.py` cannot be imported at all (missing `pyisomme.report.us_ncap.calculate`); `us_ncap/` has no `__init__.py`.

**Notes for the next session**
- Start with Step 0. Use `.venv/Scripts/python.exe` for everything.

---

### Step 0 — Fix and standardise the Python environment

**Date:** 2026-07-26 · **Branch:** `refactor/step-0-env` · **Commit(s):** see branch tip
**Outcome:** done

**What was implemented**
- Re-verified both interpreters. Findings identical to the Step -1 table: `.venv` = Python 3.9.13 /
  numpy 1.26.4 / scipy 1.12.0, `import pyisomme` OK; `python` on PATH = `C:\ProgramData\anaconda3\python.exe`
  3.12.7, `import pyisomme` still dies with
  `ValueError: numpy.dtype size changed, may indicate binary incompatibility. Expected 96 from C header, got 88 from PyObject`.
- `CLAUDE.md` Commands section: named 3.9.13 as *the* development target with its pins, stated that the
  Anaconda env is deliberately left broken (never call a bare `python`), corrected the CLI subcommand list
  (`list | merge | report | plot` — there is no `rename`), and added a runtime note (see below).
- `.venv/Scripts/python.exe -m pip check` → "No broken requirements found".
- `.venv/Scripts/python.exe -m pyisomme --help` → works.
- Ran the full test suite and recorded the pre-refactor baseline (below).

**Decisions taken**
- **Dev Python stays 3.9** (3.9.13 in `.venv`). Reasons: it matches `requires-python = ">=3.9"`
  (`pyproject.toml:29`), it is the lower leg of the CI matrix (`.github/workflows/ci.yml` tests 3.9 and 3.12),
  and it is the only interpreter on this machine that can import the package. Steps 3 (typing) and 4
  (`Annotated`) must therefore stay 3.9-compatible — `typing.Annotated` and
  `get_type_hints(include_extras=True)` both exist in 3.9, so the plan's approach holds.
- **The Anaconda base env is left unrepaired** (maintainer's call, asked and answered during this session).
  Downgrading numpy there would affect unrelated projects; the venv is documented instead. Consequence: a
  stray bare `python` stays broken by design.
- The CI 3.12 leg was **not** verified in this step: CI only triggers on `master` push / PR-to-`master`,
  and both its jobs are `continue-on-error: true`, so it proves nothing today. Making it meaningful is
  Step 3's job (plan explicitly puts CI changes there). Recorded rather than improvised.

**Behaviour changes**
- None. Documentation and process only; no code touched.

**Verification** (commands run and their result — this is the pre-refactor baseline)

Note: `-m unittest discover -s tests` in one go takes >10 min and was killed by a command timeout, so the
suite was run module-by-module (and `test_report` test-by-test). Totals below are the sum.

**Baseline: 90 tests — 87 pass, 3 errors, 0 failures.**

| Module | Tests | Result | Time |
|---|---|---|---|
| `tests.test_calculate` | 11 | OK | 0.58 s |
| `tests.test_channel` | 16 | OK | 0.04 s |
| `tests.test_code` | 2 | OK | 0.00 s |
| `tests.test_correlation` | 2 | OK | 3.33 s |
| `tests.test_errors` | 8 | OK | 0.00 s |
| `tests.test_isomme` | 14 | OK | 1.48 s |
| `tests.test_limits` | 2 | OK | 0.01 s |
| `tests.test_parsing` | 16 | OK | 0.12 s |
| `tests.test_plotting` | 0 | OK (no tests defined) | 0.00 s |
| `tests.test_sources` | 5 | OK | 0.10 s |
| `tests.test_unit` | 1 | OK | 0.00 s |
| **`tests.test_report`** | **13** | **10 OK / 3 ERROR** | ~12 min |

`tests.test_report.TestReport`, per test:

| Test | Result | Time |
|---|---|---|
| `test_EuroNCAP_Frontal_50kmh` | OK | 30.6 s |
| `test_EuroNCAP_Frontal_MPDB` | **ERROR** | 0.6 s |
| `test_EuroNCAP_Side_Barrier` | OK | 5.0 s |
| `test_EuroNCAP_Side_Pole` | OK | 33.7 s |
| `test_EuroNCAP_Side_FarSide` | OK | 23.6 s |
| `test_EuroNCAP_Side_Farside_VTC` | OK | 107.6 s |
| `test_IIHS_Frontal_Small_Overlap` | OK | 112.4 s |
| `test_Correlation` | **ERROR** | 0.3 s |
| `test_EuroNCAP` | **ERROR** | 4.0 s |
| `test_UN_Frontal_50kmh_R137` | OK | 78.6 s |
| `test_UN_Frontal_56kmh_ODB_R94` | OK | 100.8 s |
| `test_UN_Side_Pole_R135` | OK | 4.6 s |
| `test_UN_Side_Barrier_R95` | OK | 4.2 s |

The three errors, verbatim (two share one root cause):

```
ERROR: test_EuroNCAP_Frontal_MPDB (tests.test_report.TestReport)
  File "tests\test_report.py", line 36, in test_EuroNCAP_Frontal_MPDB
    report = ...EuroNCAP_Frontal_MPDB([self.v3, self.v2, self.v1])
  File "pyisomme\report\euro_ncap\frontal_mpdb.py", line 59, in __init__
    self.Page_OLC_Trolley(self)
  File "pyisomme\report\euro_ncap\frontal_mpdb.py", line 1280, in <dictcomp>
    calculate_olc(isomme.get_channel(f"M?MBAR0000??VEXA", f"M?MBARCG00??VEXA"))[1]]] ...
  File "pyisomme\calculate.py", line 965, in calculate_olc
    c_v = c_v.convert_unit("m/s")
AttributeError: 'NoneType' object has no attribute 'convert_unit'

ERROR: test_EuroNCAP (tests.test_report.TestReport)
  File "pyisomme\report\euro_ncap\euro_ncap.py", line 22, in __init__
    self.frontal_mpdb = EuroNCAP_Frontal_MPDB(*frontal_mpdb)
  ... identical stack, same AttributeError ...

ERROR: test_Correlation (tests.test_report.TestReport)
  File "tests\test_report.py", line 108, in test_Correlation
    report = pyisomme.report.correlation.correlation.Correlation([self.v1, self.v2, self.v3])
AttributeError: module 'pyisomme.report' has no attribute 'correlation'
```

Both root causes are **new** — neither appears in the review's Appendix A (grepped). Logged as D1/D2 above.

**Deviations from the plan / left undone**
- Anaconda repair skipped (deliberate, see Decisions).
- CI 3.12 verification deferred to Step 3 (see Decisions).
- The plan's `discover -s tests` one-liner could not complete inside a single command timeout; the
  per-module split is equivalent but does not produce one aggregate `Ran N tests` line.

**Notes for the next session (Step 1)**
- **Step 1's acceptance criterion "`tests/golden/euro_ncap_frontal_mpdb.json` committed" is currently
  unreachable**: `EuroNCAP_Frontal_MPDB` cannot even be *constructed* against the available fixtures (D1).
  Options, in preference order: (a) guard the trolley channel lookup in `Page_OLC_Trolley` — a one-line
  `None` check, arguably Step 2's Appendix-A territory but it blocks Step 1; (b) build the MPDB golden from
  a fixture that has an `M?MBAR…VEXA` channel, if one exists; (c) drop MPDB from Step 1 and pick a second
  reference report that runs. **Decide before starting Step 1** — do not silently drop the second golden.
- The import smoke test (Step 1) must cover `pyisomme/report/__init__.py`'s incomplete re-exports (D2),
  not only `pkgutil`-walking the files: `test_Correlation` fails on an *attribute*, and a module-walk alone
  would not have caught it.
- Baseline for later steps: any of the 87 passing tests turning red is a regression caused by that step;
  the 3 errors above are pre-existing.
