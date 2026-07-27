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
| 1 | Safety net: golden tests + import smoke test | ⚠ done with deviations | `refactor/step-1-safety-net` |
| 2 | Fix known defects (Appendix A1, A5, A6, A9) | ⚠ done with deviations | `refactor/step-2-known-defects` |
| 3 | Typing and lint (P5) | ⚠ done with deviations | `refactor/step-3-typing-lint` |
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
| Q7 | **A4b** — `p_driver`/`p_front_passenger`/`p_rear_passenger` are consumed in `Criterion_Overall.__init__`, so overriding them post-construction moves the **plots** but not the **criteria**. Not a protocol question — it is F15, scheduled for Step 4 (interim) / Step 7 (`Ctx`). Listed here only so the Step-2 acceptance criterion's A-list is complete. | 2 | *no maintainer input needed — owned by Steps 4/7* |
| Q8 | **A1 follow-up** — with A1 fixed, MPDB now matches `frontal_50kmh`: a >80 g head peak forces `hard_contact = True` even when the user set `False` (the A2 "video OR curve" semantics). Verified on the fixtures: 190.94 g overrides `False`; 55.80 g / 48.12 g no longer do. Is that OR-direction right for MPDB too, or should MPDB differ? | 2 | |

---

## Deferred items discovered during implementation

Things noticed mid-step that belong to a later step (or to no step at all). Record instead of fixing.

| # | Item | Noticed in step | Belongs to |
|---|---|---|---|
| D1 | `Page_OLC_Trolley.__init__` (`frontal_mpdb.py:1279`) calls `calculate_olc(isomme.get_channel("M?MBAR*VEXA"))` with no `None` guard → `AttributeError` at **construction** time for any test without a moving-barrier channel. Breaks `EuroNCAP_Frontal_MPDB` *and* the `EuroNCAP` MetaReport on the current fixtures. Not in the review's Appendix A. | 0 | **done in Step 2** (guarded; unblocked 3 tests + the MPDB golden) |
| D2 | `pyisomme/report/__init__.py` imports only `euro_ncap`, `un`, `iihs` — not `correlation`, `us_ncap`, `fmvss`. So `pyisomme.report.correlation…` fails after a plain `import pyisomme`. `us_ncap/` also still has no `__init__.py`. Not in Appendix A (A5 covers only the `us_ncap` import). | 0 | **done in Step 2** |
| D3 | CLI `--help` lists `list, merge, report, plot` — CLAUDE.md claimed a non-existent `rename` subcommand. Corrected in this step. | 0 | done |
| D4 | `us_ncap/side_mdb.py` and `us_ncap/side_pole.py` contain nothing but two unused imports — no report class at all. Left untouched in Step 2 (ruff will flag the unused imports). | 2 | Step 3 (lint) — or delete them |
| D5 | `Criterion` declares `calculation()` `@abstractmethod` but does **not** use `ABCMeta`, so it is not enforced: `class Criterion_Chest(Criterion): pass` instantiates happily and only fails at calculate time. Several such empty placeholders exist in `us_ncap/frontal_56kmh.py`. | 2 | Step 7 (framework) |
| D6 | `USNCAP.__init__` still advertises five load-case parameters (`frontal_56kmh`, `frontal_mpdb`, `side_pole`, `side_barrier`, `side_farside`) that no `us_ncap` module implements. Signature left as-is because narrowing it would be guessing at the intended US-NCAP structure. | 2 | whoever finishes US-NCAP |
| D7 | `Page_OLC` (`page.py`) guards its OLC lookup with a **narrower** pattern set than the lookup it protects: it dereferences `get_channel("10VEH0OLC??VEXX", "14BPIL0OLC??VEXX", "10SEAT0OLC??VEXX")` but only checks `get_channel("14BPIL0OLC??VEXX", "10SEAT0OLC??VEXX")`. A test carrying only the `10VEH…` channel therefore renders `nan` although the data is there. Behaviour preserved verbatim in Step 3 (moved into `Page_OLC._olc_cell_text` with a NOTE); it is a page-content bug, not a typing one. | 3 | Step 11 (pages select from the tree) |
| D8 | Running **all 13** tests of `tests.test_report` in one process (`PYISOMME_SLOW=1 … -m unittest tests.test_report`) dies with a Windows stack overflow (exit `0xC00000FD`) right after `test_EuroNCAP_Side_Pole`. **Pre-existing** — reproduced identically on the Step-2 tip (`a0d55d4`) in a clean worktree. Every one of the 13 passes when run alone, and `discover -s tests` (which skips the slow four) is unaffected. Likely resource exhaustion across ~200 matplotlib figures / pptx exports in one interpreter. | 3 | unassigned — needs a real diagnosis, not a refactor step |

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

---

### Step 1 — Safety net: golden tests + import smoke test

**Date:** 2026-07-26 · **Branch:** `refactor/step-1-safety-net` · **Commit(s):** see branch tip
**Outcome:** done with deviations (two, both approved by the maintainer during the session — see below)

**What was implemented**
- `tests/golden_utils.py` — tree walk, serialisation, comparison, fixture builders, `BUILDERS` registry.
- `tests/test_golden.py` — 2 golden tests + 2 coverage guards + 12 unit tests of the comparison logic
  itself (the latter need no fixture data and run instantly).
- `tests/golden_regen.py` — `python -m tests.golden_regen [stem …]`. The tests never self-heal.
- `tests/golden/euro_ncap_frontal_50kmh.json` (129 kB) and `tests/golden/euro_ncap_side_barrier.json`
  (31 kB), both **committed**.
- `tests/test_report_modules.py` — import smoke test + subpackage re-export test.
- `tests/test_report.py` — 4 slow tests behind `@slow` (`PYISOMME_SLOW=1`), 3 broken tests `@unittest.skip`
  with `TODO(step-2, …)` reasons.
- `CLAUDE.md` — documents the net, the regeneration command and `PYISOMME_SLOW`.

**Decisions taken**

- **The golden net has two layers, not one.** The maintainer opened the exported 50 km/h PPTX and observed
  "a lot of nan". Measured: of 64 criterion nodes per test, only 35/31 carry a non-nan `value`
  (55 %/48 %) — but 48/41 carry a non-nan `rating` (75 %/64 %), and most remaining nans are *structural*
  (aggregate nodes such as `criterion_driver/criterion_chest` carry a rating and leave `value` at nan by
  design, status `OK`, `na_reason` `None`). A pure value golden would therefore be thin, so a
  **definition layer** was added: 64 criterion paths + names + **172 `Limit` rows** + 29 page classes,
  all captured with zero dependence on measurement data. This is a slice of Step 12's `describe()` (P8)
  pulled forward — **deviation from the plan**, taken because it is the layer that makes the sparse
  fixtures stop mattering for Steps 5, 6 and 10 (which move limits and code patterns around).
- **Results use no-regression semantics, not exact match** (maintainer's proposal, adopted). A known
  value/rating/color must stay identical (`rel_tol=1e-9`); a `nan` may stay `nan` *or become a number*,
  which is printed as a tolerated "improvement". Status may only move **up** `ERROR < PENDING < NA < OK`.
  This is deliberately looser than the plan's exact match and is what lets Step 3's `require_channel`
  (`ERROR → NA`) land without a re-baseline, while still failing on any lost or changed number.
- **Golden set = `EuroNCAP_Frontal_50kmh` + `EuroNCAP_Side_Barrier`** (maintainer's choice), *not*
  `EuroNCAP_Frontal_MPDB` as the plan assumed — MPDB cannot be constructed at all (item D1). Side Barrier
  was chosen over `UN_Side_Barrier_R95` on measured coverage: 13 nodes at **100 % rating coverage** and 48
  limit rows in 5 s, versus 7 nodes at 57 % and 15 limit rows. Its inputs come from `create_sample`, which
  is deterministic (`linspace`/`sin`, no RNG — `channel.py:567`), so synthetic channels are a legitimate
  way to raise coverage later without sourcing real ISO-MME data.
- **Slow tests are skipped, not deleted** (maintainer asked for "comment out + TODO"). Implemented as
  `@unittest.skipUnless(os.environ.get("PYISOMME_SLOW"), …)` rather than commented-out code: same effect,
  but the test stays visible as *skipped* in the output, stays parseable, and cannot silently rot against
  a refactor. **Note for the maintainer's post-refactor review: these four tests currently PASS.** They
  were parked for turnaround time (79–112 s each), not because of missing data.
- **Keys are attribute paths** (`criterion_driver/criterion_head/criterion_hic_15`), stored alongside each
  criterion's `name`. Steps 7–8 rename attributes when `sub()` descriptors land; that will show up as
  "criterion disappeared" + "new criterion" pairs and needs a deliberate regeneration. Accepted — the
  alternative (keying by protocol name) collides where `name` is `None`.

**Behaviour changes**
- None in `pyisomme/` — no library code was touched (verified: `git diff` against the Step 0 tip touches
  only `tests/` and `CLAUDE.md`).

**Verification** (commands run and their result)
- `.venv/Scripts/python.exe -m unittest tests.test_report_modules -v` → **OK**, 5 tests, 8.2 s.
- `.venv/Scripts/python.exe -m tests.golden_regen` → 64 criteria / 172 limit rows / 2 tests, and
  13 criteria / 48 limit rows / 1 test. Numbers match the independent coverage probe exactly.
- `.venv/Scripts/python.exe -m unittest tests.test_golden` run **twice**: OK, 16 tests, 59.3 s then 57.7 s
  — no nondeterminism, and zero "improvement" lines (so the goldens describe the current state exactly).
- **Net proven to fail (both layers), then reverted:**
  - definition layer — HIC Good limit `500.000 → 501.000` (`frontal_50kmh.py:183`) produced 3 regressions,
    naming `criterion_{driver,front_passenger,rear_passenger}/criterion_head/criterion_hic_15`.
  - results layer — Chest Deflection `np.min → np.max` (`frontal_50kmh.py:438`, a plausible refactor slip)
    produced 4 regressions with before/after numbers, e.g.
    `criterion_driver/…/criterion_chest_deflection.value: -27.640424739525812 -> 0.15536177772070078`.
    Notably `rating` did *not* move (it is computed from the channel, not from `value`), so a value-only
    defect would have been invisible without this layer.
  - `git status --porcelain pyisomme/` clean afterwards.
- `.venv/Scripts/python.exe -m unittest discover -s tests` → **OK (skipped=7)**, 111 tests, 465.7 s.
  The full suite now fits in a single command run again (it did not before — see Step 0).

**Deviations from the plan / left undone**
- Second golden is Side Barrier, not MPDB (blocked by D1) — see Decisions.
- Definition layer added ahead of Step 12 — see Decisions.
- Results comparison is no-regression rather than exact — see Decisions.
- Plan's "`python -m tests.golden_regen` **or** an env var" — only the module entry point was built. An
  env var that rewrites goldens during a test run was deliberately not added: it makes accidental
  self-healing too easy.

**Discovered during this step**
- `pyisomme.report.us_ncap.us_ncap` **imports fine** — the plan (Appendix A6) implies it is import-broken,
  but its defect is a runtime `AttributeError` in `__init__`, which no import test can see. It is
  therefore *not* in `BROKEN_MODULES`; only `us_ncap.frontal_56kmh` (A5) is.
- The D2 re-export failure is invisible to an in-process check: importing any submodule binds it onto its
  parent package, so once one test touches `pyisomme.report.correlation.correlation` the attribute exists.
  `TestReportSubpackageReexports` therefore shells out to a **fresh interpreter**. Verified by hand:
  `euro_ncap`/`un`/`iihs` → `True`; `correlation`/`fmvss`/`us_ncap` → `False`.

**Notes for the next session (Step 2)**
- Step 2's acceptance criterion "import smoke test passes with an empty or strictly smaller skip list"
  now means: remove `pyisomme.report.us_ncap.frontal_56kmh` from `BROKEN_MODULES` (A5) and shrink
  `MISSING_REEXPORTS` (D2, one line in `pyisomme/report/__init__.py`). The staleness guards will fail if a
  fix lands without the list being updated — that is intentional.
- Fixing D1 (the unguarded `calculate_olc`) unblocks three skipped tests at once
  (`test_EuroNCAP_Frontal_MPDB`, `test_EuroNCAP`) and lets MPDB be added to `golden_utils.BUILDERS`.
  Worth doing early in Step 2 even though the plan's Appendix-A list does not mention it.
- When a step changes a number on purpose: run `python -m tests.golden_regen <stem>`, paste the
  `git diff tests/golden/` summary into that step's entry, and say why.

---

### Step 2 — Fix the known defects from the review's Appendix A

**Date:** 2026-07-27 · **Branch:** `refactor/step-2-known-defects` (from the Step 1 tip, not `dev` —
the step's acceptance criteria are stated against Step 1's golden net) · **Commit(s):** see branch tip
**Outcome:** done with deviations (two additions beyond the plan's A-list — D1 and the MPDB golden)

**What was implemented**

| ID | Fix |
|---|---|
| **A1** | `frontal_mpdb.py:183` — restored the missing `> 80` comparison, matching `frontal_50kmh.py:147`. |
| **A5** | `us_ncap/__init__.py` added. `frontal_56kmh.py` no longer imports the non-existent `pyisomme.report.us_ncap.calculate` — the symbol it wanted (`calculate_p_head_hic15_ais_3plus`) has lived in `pyisomme/calculate.py` all along, so the import was simply stale, not missing. Both wildcard imports made explicit. |
| **A6** | `us_ncap/us_ncap.py` — `USNCAP.__init__` no longer iterates the never-assigned `self.reports`. |
| **A9** | `pyisomme/limits.py` — `Limit.rating` gets a documented `np.nan` default, and `Limits.get_limit_ratings()` raises a `ValueError` naming the offending limits and their `code_patterns`. |
| **D1** | `Page_OLC_Trolley.__init__` (`frontal_mpdb.py:1277`) guards the trolley-channel lookup; a test without `M?MBAR…VEXA` now gets an empty OLC plot and a log line instead of `AttributeError` at construction. |
| **D2** | `pyisomme/report/__init__.py` re-exports all six protocol subpackages, not three. |

Test-side consequences: `BROKEN_MODULES` and `MISSING_REEXPORTS` in `tests/test_report_modules.py` are
now **empty**; the three `@unittest.skip`s in `tests/test_report.py` (`test_EuroNCAP_Frontal_MPDB`,
`test_EuroNCAP`, `test_Correlation`) are gone because their causes are gone.

**Decisions taken**

- **A5/A6 are honest stubs that raise `NotImplementedError` at construction**, with a module docstring
  saying exactly what is missing. Fixing the import alone would not have been honest: `Criterion_Overall`
  references a `Criterion_Passenger` that **is never defined**, and the driver's chest/femur/neck criteria
  are empty `pass` bodies — so `USNCAP_Frontal_56kmh` could not be constructed even with a working import
  (a defect no import test can see, exactly like A6). `USNCAP` likewise composes sub-reports that do not
  exist: `side_mdb.py` and `side_pole.py` define no report class at all. The partial driver-head criterion
  and its star limits are **kept** as the record of the work done; only construction is blocked.
- **A6 was not "mirrored on `EuroNCAP`"** (the plan's first option) — there is nothing to mirror it with.
  The five-parameter signature is left untouched rather than narrowed to what exists, because choosing the
  real US-NCAP load-case set is a protocol decision, not a refactor decision (logged as D6).
- **A9 does not raise at construction.** The plan preferred an explicit error, but a rating-less `Limit` is
  a *supported* use — limits that only draw a reference line, as in `tests/test_limits.py:16-18`. So the
  error moved to the rating-consuming path, which is where the requirement actually exists. Previously
  that path died with `AttributeError: 'Limit' object has no attribute 'rating'` inside a list
  comprehension (the `None in [...]` guard on `limits.py:167` could never fire, because reading the
  annotated-but-unset attribute raised before the `in` test ran). It now names the limits and their
  patterns. `limit_list_sort` sorts by `func(0)`, not by rating, so the `nan` default changes no ordering.
- **D1 was fixed here even though the plan files it under Step 1/Step 3.** Justification: A1 lives in
  `frontal_mpdb.py`, and MPDB could not be *constructed*, so fixing A1 without D1 would have left this
  step's headline fix unverifiable and unprotected. Step 0's notes already recommended doing it early in
  Step 2. It is a `None` guard, not a redesign; Step 3 will replace it with `require_channel`.
- **A2 was left alone** (plan says it is correct as designed). The optional readability tweak the plan
  permits was not taken — with A1 restored, the two reports are now textually identical here, which is
  worth more to Step 10 (shared criteria library) than the shorter form.

**Behaviour changes**

- **A1 — real, and the point of the fix.** `hard_contact` was being forced `True` for any head-acceleration
  peak that is merely non-zero, silently discarding a user's manual `hard_contact = False`. Measured on the
  MPDB fixtures (driver head), before → after:

  | Test | peak \|a\| | manual `False` survives? |
  |---|---|---|
  | 09203 | 190.94 g | no → **no** (correct: >80 g is curve evidence of contact, per A2's OR semantics) |
  | 14084 | 55.80 g | no → **yes** |
  | AK3T02FO | 48.12 g | no → **yes** |

  **Default-neutral**: `hard_contact` defaults to `True`, so a run that sets nothing is unaffected —
  confirmed, the pre-existing goldens pass untouched. Whether the OR-direction is right for MPDB is Q8.
- **A5/A6** — `USNCAP_Frontal_56kmh(...)` and `USNCAP(...)` now raise `NotImplementedError` instead of
  `AttributeError`. Neither is in `REPORTS`; nothing constructs them.
- **A9** — a rating-less limit reaching `get_limit_ratings()` raises `ValueError` instead of
  `AttributeError`. `Criterion.calculate()` catches both as `Status.ERROR`, so no criterion result moves.
- **D1** — a report built from fixtures without a trolley channel gains an (empty) OLC trolley page rather
  than failing to construct.
- Nothing else: no computed `value`/`rating`/`color` in the golden set changed.

**Verification** (commands run and their result)
- `.venv/Scripts/python.exe -m unittest tests.test_report_modules tests.test_limits -v` → **OK**, 7 tests,
  9.4 s — with both skip lists empty, so the staleness guards are now proving the absence of breakage.
- `.venv/Scripts/python.exe -m unittest tests.test_golden` → **OK**, 16 tests, 11.7 s, **zero improvement
  lines** on the two pre-existing goldens ⇒ A1/A9/D1/D2 are value-neutral there.
- `.venv/Scripts/python.exe -m unittest tests.test_report.TestReport.test_EuroNCAP_Frontal_MPDB
  tests.test_report.TestReport.test_Correlation` → **OK**, 2 tests, 122 s (both previously skipped, both
  including `export_pptx`).
- A1 proven by hand (scratch script, not committed): construct MPDB, set
  `criterion_driver.criterion_head_neck.criterion_head.hard_contact = False`, calculate, read the flag
  back. Produced the table above.
- A9 proven by hand: `Limits([Limit(["?"*16], func=…, name="reference line", upper=True)]).get_limit_ratings(channel)`
  → `ValueError: Cannot rate channel '????????????????': the matching limits ['reference line'] declare no
  rating (code_patterns [['????????????????']]). …`
- `.venv/Scripts/python.exe -m unittest discover -s tests` → **OK (skipped=4)**, **112 tests**, 355.9 s.
  Baseline comparison: Step 1 was 111 tests / skipped=7. The 3 recovered skips are the ones listed above;
  the +1 test is the new MPDB golden; the remaining 4 skips are the opt-in `@slow` ones. Wall time was
  356 s against Step 1's 466 s, but that is **not** attributable to this step — run-to-run variance on this
  machine is large (the same `tests.test_golden` invocation took 59 s in Step 1 and 12 s here, on more
  tests). Treat suite timings as indicative only.

**Deviations from the plan / left undone**
- **D1 fixed here** rather than in Step 1/3 — see Decisions.
- **`tests/golden/euro_ncap_frontal_mpdb.json` added** (51 criteria, 147 limit rows, 3 tests), closing the
  Step-1 acceptance criterion that D1 had blocked. Baselined **after** the A1 fix, which is sound because
  A1 is default-neutral. The MPDB tree still records many `Status.ERROR` nodes from unguarded
  `get_channel(...)` dereferences (e.g. `frontal_mpdb.py:479`, `:927`); Step 3's `require_channel` will
  turn those into `NA`, which the no-regression comparison already tolerates as an improvement.
- **A5/A6 stubs raise rather than being deleted or completed** — see Decisions.
- **A9 raises in the consuming path, not at construction** — see Decisions.
- `us_ncap/side_mdb.py` and `side_pole.py` (empty but for two unused imports) left untouched — D4.

**Notes for the next session (Step 3 — typing and lint)**
- Three golden files now exist. MPDB is the one with real `Status.ERROR` nodes, so it is the best evidence
  that `require_channel` does what Step 3 claims: expect `ERROR → NA` improvements there, *not* regressions.
  If any MPDB `value`/`rating` moves, that is a genuine behaviour change and needs justifying.
- Ruff will flag things this step deliberately did not clean: the two content-free `us_ncap` modules (D4),
  and `frontal_56kmh.py`'s now-unreachable criterion tree.
- `Criterion`'s `@abstractmethod` is unenforced (D5) — worth deciding in Step 7 whether the base should
  become an actual ABC, which would have caught `us_ncap`'s empty placeholders at construction.
- CI (A14) is still `continue-on-error: true` on both jobs and only triggers on `master`; Step 3 owns
  making the lint job blocking and adding `tests/test_report_modules.py` to it — that test needs no
  fixtures and, as of this step, passes with both skip lists empty.

---

### Step 3 — Typing and lint (P5)

**Date:** 2026-07-27 · **Branch:** `refactor/step-3-typing-lint` (from the Step 2 tip `a0d55d4`) ·
**Commit(s):** see branch tip
**Outcome:** done with deviations (three, listed below) — plus one **incident**, see the last section.

**What was implemented**

- **`Report` is generic in its overall criterion.** `class Report(Generic[C])` with
  `criterion_overall: dict[Isomme, C]` and a typed `overall(isomme) -> C`. All 14 concrete reports that
  own a `Criterion_Overall` now declare `class X(Report["X.Criterion_Overall"])`. The string forward-ref
  to an inner class works at runtime on 3.9 (`Generic.__class_getitem__` accepts `str`) and mypy resolves
  it — verified before adopting it. One `cast(C, self.Criterion_Overall(...))` in `Report.__init__` is the
  price: the language cannot say "this inner class is `type[C]`".
- **Every signature under `pyisomme/report/` is annotated** — `disallow_untyped_defs` is on and there are
  **0** unannotated defs left (468 `no-untyped-def` at the start). 297 `__init__(self, report: …)`, all
  `calculation(self) -> None`, all `construct(self, presentation: Presentation) -> None`.
- **`require_channel` migration (F3).** 104 call sites in report modules now use
  `self.require_channel(...)` instead of `self.isomme.get_channel(...)`. `require_channel` gained an
  `isomme=` keyword so the VTC report's reference-test lookups can use it too. Measured effect on a full
  `PYISOMME_SLOW=1 tests.test_report` log: **94 `AttributeError: 'NoneType' …` tracebacks before → 0 after.**
  Only 16 raw `get_channel` calls remain in report code, all in `side_farside_vtc`'s
  `Criterion_Individual_ISO_Score` subclasses, which *deliberately* tolerate a missing channel (see below).
- **95 `report: <ConcreteReport>` narrowings** on the `Page`/`Criterion` classes that walk
  `report.criterion_overall` / `report.Criterion_Overall`. This is what makes the F2 chains checkable.
- **`pyproject.toml`:** `[tool.mypy]` scoped to `pyisomme/report/` (core modules analysed but silenced via
  `follow_imports = "silent"`), `[tool.ruff]` with `E`/`F`/`W`/`B`/`UP`, `mypy`/`ruff` added to the `dev`
  extra, `py.typed` created and added to `package-data`.
- **CI:** the lint job installs the dev extra and now runs **ruff, mypy and `tests/test_report_modules.py`
  blocking** (`continue-on-error` removed). The test job stays non-blocking — `data/` is still untracked.
- **`CLAUDE.md`:** new "Static checking" section documenting the scoping, the generic `Report[C]` pattern,
  the `require_channel` rule and the known `tests.test_report` crash.

**Decisions taken**

- **Criterion `__init__` takes the base `Report`, not the concrete report.** ~25 criterion *and page*
  classes are reused across reports (`EuroNCAP_Side_Barrier` borrows `EuroNCAP_Side_Pole`'s pages,
  `frontal_mpdb` borrows `frontal_50kmh`'s criteria, …). Narrowing their parameter is simply false, so
  those classes keep `report: Report` and their tree-walks stay unchecked. That is F8/F7 duplication,
  owned by Steps 9–11; typing exposes it rather than papering over it.
- **`report:` narrowing is applied per class, not globally.** Only classes that actually dereference the
  criterion tree get it. The alternative (making `Page`/`Criterion` generic in the report type) would have
  meant ~300 noisier declarations for the same result.
- **`E501` is not enforced.** The repo's longest line is 261 chars and the long ones are channel-pattern
  one-liners in `calculate.py`/`providers.py` — reformatting them is neither this step's scope nor
  obviously an improvement. Line length is left to a future formatter decision; every other `E`/`F`/`W`/
  `B`/`UP` rule is on and clean. `docs/` (notebooks) is excluded from ruff.
- **`ANN` was not enabled** although the plan mentions it. mypy's `disallow_untyped_defs` already covers
  exactly what `ANN` would add for `report/`, and `ANN` additionally demands annotations on lambdas, of
  which the page classes have many. Recorded rather than improvised.
- **The `us_ncap` stub's known breakage is now three `# type: ignore[…]` comments**, each naming the
  defect (undefined `Criterion_Passenger`; `pass`-bodied `Criterion_Chest/Femur/Neck` that are abstract
  and reject `p`). With `warn_unused_ignores = true` these are staleness guards, the same trick
  `BROKEN_MODULES` plays in `tests/test_report_modules.py`.
- **`us_ncap/side_mdb.py` and `side_pole.py` (D4) were kept, not deleted.** Ruff removed their two unused
  imports, which left them empty; each now carries a docstring saying it is a placeholder, so the `USNCAP`
  docstring that points at them stays true.
- **`side_farside_vtc`'s guarded channel lookups were left alone.** `Criterion_Individual_ISO_Score`
  explicitly tolerates a missing channel (score stays `nan`, status `OK`). Converting it to
  `require_channel` would turn `OK` into `NA` — a *downgrade* under the golden net's status ordering, i.e.
  a behaviour change with no mandate. Only the annotation (`ref_channel: Channel | None = None`) and the
  guard style (`None not in (…)` → explicit `is not None`, so mypy can narrow) changed. The two
  *unguarded* classes in the same file (`Criterion_HIC_15`, `Criterion_Head_a3ms`) were migrated.

**Behaviour changes**

1. **`Status.ERROR` → `Status.NA` at 51 criterion nodes** in the golden set (frontal_50kmh + MPDB). This is
   the intended `require_channel` effect: a missing channel is now "n/a, naming the pattern" instead of a
   swallowed `AttributeError` logged as a bug. No `value`, `rating` or `color` moved with it.
2. **A real defect found by mypy and fixed:** `frontal_mpdb.py` (MPDB passenger head) read
   `self.rating = np.value = np.min([...])` — `np.value`, not `self.value`. It was assigning an attribute
   **onto the numpy module** and leaving the criterion's own `value` at `nan`. mypy: *"Module has no
   attribute 'value'"*. Fixed to `self.value`. Effect, before → after:
   `criterion_passenger/criterion_head_neck/criterion_head.value`: `nan → 4.0` for tests **14084** and
   **AK3T02FO** (09203 has no passenger head data and stays `nan`). `rating` was already correct.
3. `float(...)` wrapping around 8 `np.interp` / `np.nanmean` / `np.max` results assigned to
   `value`/`rating`. Value-exact (`np.float64 → float`); NaN propagation untouched (G9).
4. `Page_Cover` subtitle now joins `str(isomme.test_number)`; a `None` test number renders `"None"`
   instead of raising `TypeError`. `Limits(name=...)` accepts `None` (already the de-facto behaviour) and
   `Limit(x_unit=/y_unit=)` accepts `int` (`y_unit=1` is used 16 times) — annotation-only.
5. `Correlation`'s page sort key is `None`-safe: a criterion whose `channel_r` is missing sorts first
   instead of raising `AttributeError` during page construction.
6. Nothing else. `EuroNCAP` MetaReport's `super().__init__(isomme_list=[], *args, **kwargs)` became
   `super().__init__([], *args, **kwargs)` — same call, minus the "multiple values for keyword" ambiguity.

**Goldens re-baselined deliberately.** `python -m tests.golden_regen`, then `git diff tests/golden/`:
**exactly 53 changes — 51 × `"status": ERROR → NA` and 2 × `"value": nan → 4.0`**, i.e. items 1 and 2
above and nothing else. `euro_ncap_side_barrier.json` is unchanged. Re-baselining (rather than letting the
net keep printing them as tolerated improvements) matters: with `ERROR` as the stored baseline, a later
step regressing `NA` back to `ERROR` would **not** be caught.

**Verification** (commands run and their result)
- `.venv/Scripts/python.exe -m mypy` → **Success: no issues found in 33 source files**
  (baseline before this step, same config pointed at the whole package: **566 errors in 28 files** —
  468 `no-untyped-def`, 43 `union-attr`, 29 `arg-type`, …).
- `.venv/Scripts/python.exe -m ruff check .` → **All checks passed!** (baseline: 85 errors).
- `.venv/Scripts/python.exe -m unittest discover -s tests` → **OK (skipped=4)**, **112 tests**, 356.7 s —
  identical to the Step-2 baseline (112 / skipped=4).
- `.venv/Scripts/python.exe -m unittest tests.test_golden` → **OK**, 17 tests, and after the re-baseline
  **zero** improvement lines.
- `.venv/Scripts/python.exe -m unittest tests.test_report_modules tests.test_limits` → **OK**, 7 tests.
- The four opt-in slow tests, run **individually**: `test_EuroNCAP_Side_Farside_VTC` OK (24.6 s),
  `test_IIHS_Frontal_Small_Overlap` OK, `test_UN_Frontal_50kmh_R137` OK (13.8 s),
  `test_UN_Frontal_56kmh_ODB_R94` OK (25.9 s). Running the whole module at once crashes — see D8, it is
  pre-existing and was reproduced on `a0d55d4`.
- **Acceptance criterion "a deliberate typo is reported by mypy" — verified on a scratch file, then
  deleted.** All four probes behaved as P5 promises:
  - `report.overall(v1).criterion_drivr` → `"Criterion_Overall" has no attribute "criterion_drivr";
    maybe "criterion_driver"…` `[attr-defined]`
  - `report.overall(v1).criterion_driver.criterion_head.criterion_hic_15.rating` → revealed type
    `builtins.float`
  - `…criterion_head.hard_contct = False` → `"Criterion_Head" has no attribute "hard_contct"; maybe
    "hard_contact"?` — **this is F13, the review's most dangerous finding, caught statically**
  - `…criterion_head.hard_contact = "yes"` → `Incompatible types in assignment (expression has type
    "str", variable has type "bool")`

**Deviations from the plan / left undone**
- `E501` not enforced and `ANN` not enabled — see Decisions.
- The plan's "~61 `Optional` sites" turned out to be 104 once indirect derefs
  (`self.channel = get_channel(...)` followed by `self.channel.get_data()`) were counted; all are migrated.
- Cross-report-reused classes keep the base `Report` and remain unchecked — see Decisions. Concretely:
  25 classes across `side_pole.py`, `frontal_50kmh.py`, `frontal_mpdb.py`.
- CI's **test** job is still `continue-on-error: true` (fixtures untracked), as the plan allows.

**Incident — local fixture data under `data/` was deleted**

While confirming that D8's crash is pre-existing, this session created a `git worktree` at `a0d55d4` and,
because `data/` is untracked, linked the fixture folders into it with Windows directory junctions
(`mklink /J`). `git worktree remove --force` then followed those junctions and recursively deleted the
**targets**: `data/iso-mme-org`, `data/nhtsa`, `data/pdb-org`, `data/tests` and `data/vtc-loadcase-example`
are now empty directories. Nothing tracked was lost (`git status` shows 0 deleted tracked files), and
`tests/golden/*.json` plus `out/` are intact — all of this step's verification, including the full suite
and the golden re-baseline, ran **before** the deletion, on the real data.

The Recycle Bin does not contain them (git deletes directly). `data/README.md` documents public download
URLs for `iso-mme-org` (iso-mme.org forum) and `nhtsa` (NHTSA vehicle database); `pdb-org`, `tests` and
`vtc-loadcase-example` have no documented source. **Restoring `data/` is a prerequisite for running
`tests/test_report.py`, `tests/test_golden.py` and `tests/test.py` again** — the lint-side checks
(ruff, mypy, `tests/test_report_modules.py`) need no fixtures and still pass.

Never link untracked data into a git worktree on Windows. If a baseline comparison needs the fixtures,
copy them, or run the comparison via `git stash` in the main tree.

**Notes for the next session (Step 4 — manual inputs as a declared concept)**
- **Check `data/` before doing anything.** If the fixture folders are still empty, the golden tests cannot
  run and Step 4's acceptance criteria ("golden tests pass") are unreachable — restore them first.
- Step 4's headline risk (F13, a typo'd manual input being a silent no-op) is **already caught statically**
  as of this step, for every input reachable through `report.overall(...)`. Step 4's `__setattr__` guard is
  now the *runtime* backstop for users who do not run mypy, not the only line of defence — worth saying so
  in its design, and worth reconsidering how much machinery it needs.
- The manual inputs are all plain class attributes with concrete types today, so `Manual[T, manual(...)]`
  must stay type-transparent or it will *remove* the checking this step just added. Verify with the same
  four probes above after migrating.
- Q6 (tri-state `hard_contact`) is still unanswered and still gates part of Step 4.
- `Criterion.p: int` is now declared on the base class. Step 4's interim F15 fix (re-reading the position
  in `calculation()`) and Step 7's `Ctx` both touch it; it is deliberately *not* `Optional`, because every
  criterion that has a position sets it in `__init__`.
