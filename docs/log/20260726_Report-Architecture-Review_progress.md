# `pyisomme.report` Refactor — Progress Log

Running log for the step-by-step refactor described in [`20260726_Report-Architecture-Review_plan.md`](20260726_Report-Architecture-Review_plan.md).
Rationale lives in [`20260726_Report-Architecture-Review.md`](20260726_Report-Architecture-Review.md).

**Every session must append an entry below before finishing.** A fresh session reads this file to learn
what was done, what was decided, and what was deliberately left alone.

**No session commits its own work.** A step ends uncommitted, with its entry written and a handover
summary for the maintainer — see *Manual review gate* in the plan. The entry is part of what is
reviewed; a row only reaches ☑/⚠ once the maintainer has approved and the commit exists.

---

## Status board

| Step | Title | Status | Branch / commit |
|---|---|---|---|
| 0 | Fix and standardise the Python environment | ☑ done | `refactor/step-0-env` |
| 1 | Safety net: golden tests + import smoke test | ⚠ done with deviations | `refactor/step-1-safety-net` |
| 2 | Fix known defects (Appendix A1, A5, A6, A9) | ⚠ done with deviations | `refactor/step-2-known-defects` |
| 3 | Typing and lint (P5) | ⚠ done with deviations | `refactor/step-3-typing-lint` |
| 3b | Criterion trees lifted to module level (maintainer request) | ☑ done | `refactor/step-3-typing-lint` |
| 3c | `data/` restored; one golden value re-baselined | ☑ done | `refactor/step-3-typing-lint` |
| 4 | Manual inputs as a declared concept (P11) | ⚠ done with deviations | `refactor/step-4-manual-inputs` |
| 5 | Limit scales: helpers + equivalence proof (P3a) | ✖ **rejected** — reviewed 2026-08-02, stashed | see plan §Step 5 (withdrawn) |
| 6 | `PeakCriterion` + migrate leaves (P4) | ✖ **withdrawn** — 2026-08-04, no code written | see plan §Step 6 (withdrawn) |
| 7 | `sub()` + `Ctx` framework (P1 + P2) | ⏳ awaiting review | uncommitted, `refactor/step-4-manual-inputs` |
| 8 | Migrate `frontal_50kmh` (pilot) | ⏳ awaiting review | uncommitted, `refactor/step-4-manual-inputs` |
| 9 | Migrate remaining reports | ◐ in progress — `euro_ncap/` done, 6 modules left | uncommitted, `refactor/step-4-manual-inputs` |
| 10 | Shared criteria library (P9) | ☐ todo | |
| 11 | Pages select from the tree (P6) | ☐ todo | |
| 12 | `validate()` + `describe()` (P7 + P8) | ☐ todo | |
| 13 | Status propagation and rendering (P10) | ☐ todo | |

Status values: ☐ todo · ◐ in progress · ⏳ awaiting review (work complete, uncommitted, with the
maintainer) · ☑ done · ⚠ done with deviations · ✖ blocked

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
| Q9 | **MPDB golden re-baseline** — with `data/nhtsa/09203` restored, `tests/test_golden.py` reproduces exactly what Step 3c predicted for MPDB: one regression (`14084` front-passenger chest VC `-0.08756 → -0.10723`, the H3 → HF fixture correction, ratio `0.229/0.187` to 2e-16) plus 10 tolerated improvements (driver + passenger tibia index `nan → ` number, `NA → OK` — the same fixture correction supplying the dummy code `calculate_tibia_index` needs). Both are fixture corrections, not code regressions, and both predate Step 4. Run `python -m tests.golden_regen euro_ncap_frontal_mpdb`? | 4 | **answered — done.** The maintainer had `09203`'s own metadata fixed first (`data/nhtsa/09203/fix_channel_metadata.py`, commit `c91608c`: dummy `21…→TH` / `24…→H3`, CHST/DS unit `m → μm`), which added a *third* correction — driver chest compression `-20244650.23 → -20.24 mm`, rating `-inf → 4.0`, colour gray → green. Re-baselined in `7d40c04`; all 17 golden tests pass. |
| Q10 | **Step 4** — `side_farside.py`'s `max_head_score` / `max_neck_score` / `max_chest_score` (`= 4`, read via a back-reference, never assigned anywhere) were **not** declared as manual inputs: they read as protocol constants, i.e. Step 12's `max_rating`, not as engineer's judgement. Confirm, or should they be settable? | 4 | |

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
| D9 | **D8's cause is not matplotlib/pptx.** Reproduced in Step 4 with a script that only *constructs and calculates* the 13 reports on synthetic channels — no plotting, no export: same `0xC00000FD`, right after the 8th report. Confirmed pre-existing by running the identical script against the stashed Step-3 tree: same crash, same point, identical ERROR-node counts (24/20/2/4/4/2/0). So a much cheaper repro exists and the "matplotlib figures" hypothesis is out. | 4 | joins D8 — unassigned |
| D10 | `Report.export_pptx` re-runs `page.__init__(page.report)` (A8) *after* `calculate()`. With Step 4's `sync_positions()` the criteria now follow a position set **before** `calculate()`, but a position set **between** `calculate()` and `export_pptx()` still moves only the plots. Deliberately not guarded here: A8 is Step 11's and `Ctx` is Step 7's. | 4 | Steps 7 / 11 |
| D11 | `data/nhtsa/09203` and `data/nhtsa/v15036ISO.zip` (lost in the Step-3 incident) were **restored** in Step 4 from NHTSA. Their URL pattern is `…/vehdb/v<10000-block>/v<100-block>/v<id>ISO.zip`, so 09203 lives under `v00000/v09200/` — note the first segment is `v00000`, not `v09000`; a `HEAD` request 403s, a ranged `GET` works. Undocumented in `data/README.md`; the two remaining gaps (`data/tests/*`, `data/vtc-loadcase-example/*`) still have no public source. | 4 | `data/README.md` upkeep |
| D12 | **`frontal_50kmh.py:374` — the driver neck Fz capping row matches a narrower pattern than its own scale.** Rows Good…Poor use `?{p}NECKUP00??FOZ?` (filter-class wildcard); the `Limit_C` row alone uses `?{p}NECKUP00??FOZA`. Every sibling scale in the file uses the wildcard throughout, and the front/rear passenger copies have no capping row at all, so nothing corroborates it — it reads as a typo. Not changed here (Step 5 changes no behaviour); `sliding_scale` reproduces it via an explicit `capping_code_patterns=` argument so the anomaly is visible at the call site. Exactly the F4 "two patterns for one channel" problem. | 5 | Step 6 (single-source `codes`) — **needs a protocol/maintainer yes-or-no first** | 
| D13 | **`un/side_barrier_r95.py` chest lateral deflection is a three-row pass/fail**: `Fail(−42, upper)`, `Pass(−42, lower)`, `Fail(+42, lower)` — the `Pass(+42, upper)` row of a symmetric pair is missing. It is **not** equivalent to `pass_fail(symmetric=True)`: measured, the four-row form moves `get_limit_ratings(interpolate=True)` mid-band from **0.5 → 1.0** (and 0.26 → 1.0 at +20 mm). It does not reach the criterion today, which rates with `interpolate=False`, and colours are unaffected — but any interpolating consumer sees it. Recorded in `tests/test_limit_scales.py::KEEP_RAW`. | 5 | Step 6 / Step 13 — do not migrate blindly |
| D14 | **`sliding_scale` emits rows in protocol order (Good→Capping); several modules write them in another order** (`frontal_50kmh`'s HIC runs Good→Capping, its chest deflection runs Capping→Good; `frontal_50kmh`'s ±Fx puts both capping rows last, `frontal_mpdb`'s puts one per side). Source order is *not* semantic — every consumer calls `limit_list_sort` first, and Step 5 proves the sorted order is identical — but `golden_utils.serialise` records `criterion.limits.limit_list` **in list order**, so Step 6's migration will produce a reordered `definition` layer for those criteria in all three goldens and in `report_structure.json`. That re-baseline is expected and must be recognised as a permutation, not a change. | 5 | Step 6 |
| D15 | **The "Good/Poor pair" shape has no helper** — a single threshold wearing Euro-NCAP colours, sometimes mirrored: `side_pole` chest/abdomen lateral VC and shoulder lateral force, `side_farside` upper/lower neck tension Fz and extension My, `frontal_mpdb` abdomen compression, plus the capping-only `side_pole` HIC 15 / a3ms pairs. Structurally `pass_fail` with different limit classes. A `good_poor()` next to `sliding_scale` would absorb ~8 blocks; the plan names no such helper and Step 5 did not improvise one. | 5 | Step 6 / Step 10 |

---

## Session log

Append newest entries at the bottom. Template:

```markdown
### Step <n> — <title>
**Date:** YYYY-MM-DD · **Branch:** refactor/step-<n>-<slug> · **Commit(s):** <sha, or "uncommitted — awaiting review">
**Outcome:** done / done with deviations / blocked
**Review:** ☐ pending · ☑ approved YYYY-MM-DD  ← the session writes ☐; only the commit flips it

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

---

### Step 3b — Criterion trees lifted to module level (follow-up to Step 3, maintainer request)

**Date:** 2026-07-27 · **Branch:** `refactor/step-3-typing-lint` · **Commit(s):** see branch tip
**Outcome:** done

**Why**

Step 3 parameterised each report with a forward-ref string,
`class EuroNCAP_Frontal_50kmh(Report["EuroNCAP_Frontal_50kmh.Criterion_Overall"])`. The maintainer asked
for the alternative the review already names (P5, "Con" column): define the overall criterion at module
level and reference it directly. Verified first on a scratch file that it gives *identical* checking —
same `attr-defined` errors, same `reveal_type` — before touching anything.

**What was implemented**

- Each report module's tree moved from a nested `Criterion_Overall` to a **module-level `class Overall`**
  (~5 900 lines dedented across 14 modules). The report now reads:

  ```python
  class Overall(Criterion): ...

  class EuroNCAP_Frontal_50kmh(Report[Overall]):
      Criterion_Overall = Overall
  ```

- `Report` itself no longer carries a nested `Criterion_Overall`; it declares
  `Criterion_Overall: type[Criterion] = Overall` against a module-level empty default in `report.py`, so a
  bare `Report` is still constructible and subclass rebinding type-checks.
- **Cross-protocol reuse now imports the tree directly** instead of reaching through a report class:
  `from …frontal_50kmh import Overall as Overall_Frontal_50kmh`, then
  `class Criterion_HIC_15(Overall_Frontal_50kmh.Criterion_Driver.Criterion_Head.Criterion_HIC_15)`.
  This was forced by typing — once `Criterion_Overall` is an assignment rather than a class statement,
  mypy cannot use `X.Criterion_Overall.Y` in a type position — and it is the shape Step 10 wants anyway.
  23 references rewritten; 6 now-unused report-class imports dropped by ruff. Same-module
  `self.report.Criterion_Overall.X` became `Overall.X` (23 more).
- **New: `tests/test_report_structure.py` + `tests/golden/report_structure.json`** — see below.
- `CLAUDE.md` and the CI lint job updated.

**New safety net (deviation from the plan — deliberate)**

`data/` is gone (see the Step 3 incident), so `tests/test_golden.py` cannot run and this move — a
whole-tree dedent across 14 modules — would otherwise have been unverifiable. So the throwaway checking
script was made permanent:

`tests/test_report_structure.py` constructs **all 13** reports from **empty `Isomme` objects** and
compares `golden_utils.serialise(...)["definition"]` against a committed snapshot: every criterion path,
name and class, every `Limit` row (with `func` samples), and the page class list. It needs no fixture data
whatsoever, so it runs in CI, and it covers 13 reports where the goldens cover 3.

Two facts make it trustworthy:

1. Its output for the three golden reports is **byte-identical** to the `definition` half of the committed
   golden files (4205 / 3574 / 1166 serialised lines, 0 differing). Empty Isommes yield the same tree as
   the real fixtures, because the positions fall back to their declared defaults.
2. Proven to fail, then reverted: perturbing one HIC limit (`500.000 → 501.000`) fails it, and deleting
   `self.criterion_femur = …` from the driver tree fails it. `git status` clean afterwards.

Step 12's `describe()` supersedes it; fold it in there.

**Behaviour changes**

- **None.** Before/after structural snapshots over all 13 reports (~17 000 serialised lines) differ in
  **exactly 13 lines** — one per report — and every one is the root criterion's `"class"` field,
  `"Criterion_Overall" → "Overall"`. No criterion path, name, limit row or page moved.
- The same one-line change was applied to each of the three committed golden files (each contained exactly
  one `"class": "Criterion_Overall"`, the root). This is a **hand-patch, not a regeneration**, because
  `golden_regen` needs `data/`; it is exactly the change the structural snapshot proves, and afterwards
  the goldens' `definition` halves again match the snapshot byte for byte. **The goldens' `results` halves
  were not re-verified** — re-run `python -m unittest tests.test_golden` once `data/` is restored.
- `self.report.Criterion_Overall.X → Overall.X` drops a dynamic lookup in favour of a static one. No
  report subclasses another today, so the class resolved is the same — confirmed by the snapshot, which
  records the class name of every criterion.

**Verification** (commands run and their result)
- `.venv/Scripts/python.exe -m mypy` → **Success: no issues found in 33 source files**.
- `.venv/Scripts/python.exe -m ruff check .` → **All checks passed!**
- Structural snapshot before vs after → 13 differing lines, all the root `"class"` field (above).
- `.venv/Scripts/python.exe -m unittest tests.test_report_structure` → **OK**, 2 tests.
- **Construct + calculate + `export_pptx` on synthetic channels for all 13 reports → 13/13 OK.**
  (A first run showed 12/13: the frontal reports rejected the made-up `WS` dummy code with
  `AssertionError: Dummy WS not supported by wrapper` — a defect in the throwaway fixture, not the code;
  with `H3` codes all 13 pass.)
- `.venv/Scripts/python.exe -m unittest discover -s tests` → 92 tests, 15 errors, **all
  `FileNotFoundError` from the missing `data/`**. The identical 15 fail on the Step-3 commit with the tree
  stashed (90 tests / 15 errors there — the +2 are the new structural tests), so this change costs nothing.
- Step 3's four mypy probes re-run and still behave: `criterion_drivr` → `"Overall" has no attribute …`,
  `hard_contct` → suggestion, `hard_contact = "yes"` → type error, `…hic_15.rating` → `float`.

**Deviations from the plan / left undone**
- `tests/test_report_structure.py` is new test infrastructure the plan assigns to Step 12 (`describe()`).
  Pulled forward because the golden net is unusable and this change needed *some* verification.
- The goldens' `definition` was hand-patched rather than regenerated — see Behaviour changes.

**Notes for the next session**
- After restoring `data/`: run `python -m unittest tests.test_golden` **first**. It should pass with zero
  improvement lines. If it does not, the hand-patch or this move is at fault, not your step.
- The `report:` narrowings and the `Overall` classes now sit side by side; when Step 7's `sub()` descriptor
  lands, `Overall` is the natural place to hang the declaration order.
- Cross-protocol reuse is now explicit imports of `Overall` trees. Step 10 (shared criteria library) can
  start from that list: `grep -rn "import Overall as" pyisomme/report/`.

---

### Step 3c — `data/` restored; one golden value re-baselined (H3 → HF passenger dummy)

**Date:** 2026-07-27 · **Branch:** `refactor/step-3-typing-lint` · **Commit(s):** see branch tip
**Outcome:** done

**What happened**

The maintainer re-downloaded the fixtures the Step-3 incident destroyed. `data/iso-mme-org` (28 MB) and
`data/nhtsa` (151 MB) are back, and `data/README.md` now records the two corrections applied to the NHTSA
`14084` test that were previously undocumented:

- `CHST DS fix unit m --> μm`
- `set dummy in channel codes 11 H3 and 13 HF`

Re-running `tests/test_golden.py` against the restored data left **one** regression:

```
results[14084]: criterion_front_passenger/criterion_chest/criterion_chest_vc.value:
    -0.08756077622265823 -> -0.10722683291437828
```

**Diagnosis — the old golden was wrong, the new value is right.**

`calculate_vc` (`calculate.py:745`) selects its deformation constant from the channel's dummy code
(`fine_location_3`): `H3 → 0.229 m`, `HF → 0.187 m`, both with scaling factor 1.3. VC is inversely
proportional to that constant, so re-tagging position 13 from `H3` to `HF` — the Hybrid III **5th
percentile female**, which is what actually sits in the front passenger seat of that test — scales the
value by `0.229 / 0.187`. Measured:

| | |
|---|---|
| new / old value | `1.2245989304812837` |
| `0.229 / 0.187` | `1.2245989304812834` |
| difference | `2.2e-16` (floating-point exact) |

The driver stays `H3` and its VC is unchanged, which is exactly why the maintainer's observation ("this
error only occurs for passenger") pinned it. The pre-incident golden was baselined from a fixture that
mislabelled the passenger dummy; the number that changed is a **fixture correction surfacing**, not a
code regression.

**Action:** `python -m tests.golden_regen euro_ncap_frontal_50kmh`. `git diff tests/golden/` is exactly
one line — the value above. The definition layer is untouched (still 64 criteria / 172 limit rows), and
`rating` (4.0) and `color` (green) do not move, because both values fall in the same limit band.

**Verification**
- `.venv/Scripts/python.exe -m unittest tests.test_golden` → `euro_ncap_frontal_50kmh` and
  `euro_ncap_side_barrier` **pass with zero improvement lines**; `euro_ncap_frontal_mpdb` errors on a
  missing fixture (below).
- `.venv/Scripts/python.exe -m unittest discover -s tests` → **102 tests, 11 errors**, every one a
  `FileNotFoundError` for a fixture folder that has not been restored yet. Was 90/15 while `data/` was
  empty, and 112/0 (4 skipped) before the incident.
- `mypy` → Success; `ruff check .` → All checks passed; `tests.test_report_structure` +
  `tests.test_report_modules` → OK, 7 tests.

**Fixtures still missing — 11 errors are waiting on these, no code change involved**

| Path | Blocks |
|---|---|
| `data/nhtsa/09203` | the **whole** `tests/test_report.py` module (module-level `v3`, so it cannot even import → all 13 report tests) and `golden_utils.build_euro_ncap_frontal_mpdb` → the MPDB golden |
| `data/tests/{ascii,utf-8,windows-1252,iso-8859-1}` and their `.zip` variants | `tests/test_parsing.py` (8 tests), `tests/test_isomme.py::test_read` / `test_write` |
| `data/vtc-loadcase-example/{test,sim}` | `test_EuroNCAP_Side_Farside_VTC` (currently masked by the `09203` import failure) |
| `data/pdb-org` | nothing that is collected today |

`data/README.md` documents public sources for `iso-mme-org` and `nhtsa` but not for `09203`,
`data/tests` or `vtc-loadcase-example`. Once `09203` is back, run
`python -m tests.golden_regen euro_ncap_frontal_mpdb` and check the diff: the MPDB golden was baselined
from the same pre-correction `14084` fixture, so **expect the same H3 → HF VC shift there**, plus
whatever the `CHST DS` unit fix moves. Both are fixture corrections; neither is a code regression.

**Notes for the next session**
- The golden net is live again for two of the three reports. Do not start Step 4 until MPDB is either
  restored or explicitly parked.
- `tests/test_report_structure.py` (step 3b) is unaffected by any of this — it needs no fixtures — and is
  the check to lean on while `data/` is incomplete.

---

### Step 4 — Manual inputs as a declared concept (P11)

**Date:** 2026-07-27 · **Branch:** `refactor/step-4-manual-inputs` (from the Step-3c tip `701b56e`) ·
**Commit(s):** see branch tip — reviewed and approved by the maintainer before committing
**Outcome:** done with deviations (four, listed below)

**Prerequisite cleared first: `data/nhtsa/09203` restored**

Step 3c's note said "do not start Step 4 until MPDB is either restored or explicitly parked". It is
restored, not parked: `09203` was re-downloaded from NHTSA, and `v15036ISO.zip` (whose absence the
`09203` failure had been masking in `tests/test_report.py`) with it. URL shape and the `v00000` gotcha
are recorded as D11.

`09203` turned out to carry the **same two raw-export defects as `14084`**, so at the maintainer's
request it got its own `data/nhtsa/09203/fix_channel_metadata.py` (commit `c91608c`) before the goldens
were trusted: the dummy slot filled (`21…` = position 1 = **THOR** → `TH`, identified by the four CRUX
IR-TRACC deflections tagged `[THORTEST]`; `24…` = position 4 = **Hybrid III** → `H3`, a single
`24CHST000000DSXP`), and the CHST/DS unit corrected `m → μm`, which puts the deflections at 3–41 mm
(30.27 mm for the THOR left-upper resultant, −40.60 mm for the Hybrid III) instead of a factor of a
million out. The MPDB golden was then re-baselined deliberately in `7d40c04` — 14 lines, definition
layer untouched — closing Q9. **All 17 golden tests now pass**, so this step's "goldens are
value-neutral" claim below is measured against a green net, not a known-failing one.

Both commits are *fixture* work, not Step-4 work; they sit on this branch only because that is where
the missing data surfaced.

**What was implemented**

- **`pyisomme/report/manual.py`** — the declaration idiom.
  `Manual[bool, manual(False, unit=…, doc=…, source=…)]`, where `Manual` is `typing.Annotated`, so a
  type checker still sees a plain `bool`. `manual(...)` carries the **default**, so a declaration needs
  no `= False`; the default is installed as the class attribute the first time a criterion of that class
  is constructed. Also `declared_inputs(cls)` (MRO walk + cache), `settable_names(cls)`, `InputSpec`
  and the runtime type check.
- **Annotations are resolved lazily, and only the ones that matter.** `typing.get_type_hints` is
  unusable here: report modules annotate `report: EuroNCAP_Frontal_50kmh` on criteria defined *before*
  the report class exists, so resolving a whole class raises `NameError`. Instead each raw annotation
  string is tested for the substring `manual(` and only those are `eval`-ed, in their own module's
  globals, at criterion-construction time (never at import time). Failure logs a warning rather than
  breaking the import.
- **`Criterion.__setattr__` guard (F13).** Rejects any name the class does not declare — with a
  `difflib` "Did you mean 'hard_contact'?" — and rejects a wrongly typed value. "Declared" means
  *anything* in the class body across the MRO: annotated framework fields, plain class attributes and
  manual inputs alike. No hand-maintained whitelist, so a new field never needs registering. Assigning
  a `Criterion` (subcriteria are attached dynamically) or a `_`-prefixed name is exempt.
- **`Report.get_inputs()` / `set_inputs()` / `print_inputs()` (F14).** `{test: {path: value}}`, JSON-safe
  by construction. `set_inputs` raises on an unknown test or path (with a suggestion) rather than
  applying half a file. `MetaReport` overrides all three to nest one level deeper, keyed by sub-report.
  Supporting walkers on `Criterion`: `get_children()`, `walk()`, `iter_inputs()`, `get_input_specs()`.
- **F15 interim fix — `sync_positions()` + `Criterion.rebuild_child()`.** Each `Overall` that threads a
  position now calls `sync_positions()` at the top of `calculation()`; if an occupant's `p` no longer
  matches the input, `rebuild_child()` reconstructs that subtree, **preserving its manual inputs** and
  removing its stale limits from the report-level list. Applied to `euro_ncap/frontal_50kmh`,
  `euro_ncap/frontal_mpdb`, `un/frontal_50kmh_r137`, `un/frontal_56kmh_odb_r94`,
  `iihs/frontal_small_overlap`.
- **41 manual inputs migrated** across 8 modules (`euro_ncap/frontal_50kmh` 27, `euro_ncap/frontal_mpdb` 5,
  `euro_ncap/side_pole` 1, `un/frontal_50kmh_r137` 3, `un/frontal_56kmh_odb_r94` 2,
  `iihs/frontal_small_overlap` 1, `us_ncap/frontal_56kmh` 2), each with `doc`, `source` and — where it
  has one — `unit`. Defaults are preserved **literally** (e.g. `pedal_rearward_displacement` keeps the
  integer `0`, not `0.0`) so the migration cannot move a number.
- `tests/test_manual_inputs.py` — 29 tests, **no fixture data**; added to the blocking CI lint job.
  `CLAUDE.md` gains a "Manual inputs" section.

**Decisions taken**

- **The `__setattr__` guard is hidden behind `if not TYPE_CHECKING:`.** *(Superseded — see the
  2026-07-27 follow-up entry at the end of this log: the guard is now a plain method whose `value`
  parameter is typed `Never`, which preserves the property below without the visibility hack.)* A
  `__setattr__` that mypy can see makes it accept *every* attribute assignment, which silently deletes
  Step 3's static catch of `criterion.hard_contct = False` — measured: with the guard visible, that
  probe stopped erroring. Hidden, all four Step-3 probes fire again and the runtime guard still runs.
  The two layers are complementary (mypy for those who run it, the guard for notebook users), and the
  comment in `criterion.py` says so, because the obvious "cleanup" is to un-hide it.
- **"Settable" = anything declared in the class body, not an explicit whitelist.** The plan proposed an
  explicit set of framework field names. Deriving it from `vars()` + `__annotations__` over the MRO is
  strictly better: it needs no upkeep, and it covers the ~30 non-input class attributes the reports
  already carry (`values`, `weights`, `ac_test`, `channel_r`, …) without listing them. The one thing it
  found — `Criterion_Reference_ISO_Score.criteria_individual_iso_score`, assigned in `__init__` but
  declared nowhere — is now an annotation.
- **Type checking rejects `bool` for a numeric input** even though `isinstance(True, int)` is true,
  and accepts `int` for a `float`. The whole point is catching `submarining = "yes"`-shaped mistakes;
  letting `forward_excursion = True` through would be the same bug with a different literal.
- **Not every plain class attribute became a manual input.** Computed fields stay plain:
  `correlation`'s `is_reference`/`is_comparison`/`channel_r`/`channel_c`, `side_farside_vtc`'s
  `ref_channel`/`ac_*`/`r_ac_*`. `side_farside`'s `max_*_score` are protocol constants — Step 12's
  `max_rating`, not judgement — so they are excluded too, but that is a judgement call: **Q10**.
- **`hard_contact` stays `bool`, not tri-state.** Q6 is unanswered, and the plan says: without approval,
  add the declaration only and keep the default. Done — the declaration's `doc` states the current
  "video OR curve" semantics explicitly so the question is visible at the point of use.
- **`rebuild_child` rather than "re-read the position in `calculation()`".** The plan's phrasing does not
  survive contact with the code: `p` is interpolated into the limits' `code_patterns` f-strings at
  construction, so re-reading it would leave a criterion looking up position 3 while rating against
  position 1's limits — nan ratings, silently. Rebuilding the subtree is the smallest change that is
  actually correct, and the input preservation it needs is exactly the machinery this step adds. It
  also removes the old subtree's limits from `report.limits[isomme]`, otherwise the plots would grow
  duplicate limit bars (regression-tested).

**Behaviour changes**

- **None to any computed value.** All three goldens produce output *identical* to the pre-step baseline
  measured on the same tree (`git stash`). Measured twice: first against the goldens as they stood
  (50kmh and side_barrier clean, MPDB showing exactly the pre-existing fixture diff, before **and**
  after the step), then again after the `09203` fix and MPDB re-baseline — **17/17 golden tests OK, zero
  improvement lines**. `tests/golden/report_structure.json` (13 reports, 273 criteria) is unchanged,
  which is the direct evidence that no default moved.
- **New failure modes, all deliberate:** a typo'd manual-input assignment now raises `AttributeError`
  instead of silently creating an attribute; a wrongly typed one raises `TypeError`. Both fire at the
  assignment, i.e. *before* `calculate()`, so neither can be swallowed into `Status.ERROR`.
- **F15:** `report.overall(v1).p_driver = 3` now moves the criteria as well as the plots. Previously the
  criteria kept position 1 while `Page_Driver_*` drew position 3 — a silently inconsistent report.
  Verified: `criterion_driver.p`, the nested `criterion_hic_15.p`, and the rebuilt limits'
  `code_patterns` all follow, `p_front_passenger` re-derives to 1, and manual inputs set on the old
  subtree survive the rebuild.
- Nothing else. No `pyisomme/` file outside `report/` was touched.

**Verification** (commands run and their result)

- `.venv/Scripts/python.exe -m mypy` → **Success: no issues found in 34 source files**.
- `.venv/Scripts/python.exe -m ruff check .` → **All checks passed!**
- **Type transparency proven** (scratch file, then deleted). `Manual[T, manual(...)]` must not cost the
  checking Step 3 bought. All four Step-3 probes still fire, and the revealed types are the bare ones:
  - `hard_contact` → `builtins.bool`; `p_driver` → `builtins.int`; `hic_15.rating` → `builtins.float`
  - `criterion_drivr` → `"Overall" has no attribute "criterion_drivr"; maybe "criterion_driver"…`
  - `hard_contct = False` → `"Criterion_Head" has no attribute "hard_contct"; maybe "hard_contact"?`
  - `hard_contact = "yes"` / `submarining = "yes"` → `Incompatible types in assignment`
- `.venv/Scripts/python.exe -m unittest tests.test_manual_inputs` → **OK**.
- `.venv/Scripts/python.exe -m unittest tests.test_report_structure tests.test_report_modules` → **OK**,
  7 tests — the structural snapshot is unchanged.
- **Guard swept over every report:** construct + calculate all 13, each in a fresh interpreter, counting
  `Status.ERROR` nodes and grepping the log for guard messages → **0 guard hits, 13/13 reports**.
- `.venv/Scripts/python.exe -m unittest tests.test_golden` → **OK, 17 tests, zero improvement lines**
  (after the `09203` fixture fix and the MPDB re-baseline — Q9). Before those two commits the run was
  identical on this tree and on the stashed pre-step tree: 50kmh and side_barrier clean, MPDB failing
  on the one pre-existing fixture-correction regression. Either way, Step 4 moves nothing.
- `.venv/Scripts/python.exe -m unittest discover -s tests` → **139 tests, 10 errors, 0 failures**.
  Baseline on the same tree with this step stashed: **102 tests, 10 errors, 0 failures** — same error
  set; the +37 are this step's tests. The 10 errors are all `FileNotFoundError` for fixtures the Step-3
  incident destroyed that have **no public source**
  (`data/vtc-loadcase-example/{test,sim}` — which alone breaks the import of the whole
  `tests/test_report.py` module — and `data/tests/{ascii,utf-8,windows-1252,iso-8859-1}`).

**Deviations from the plan / left undone**

- **Tri-state `hard_contact` not implemented** — Q6 unanswered; the plan's fallback ("keep the current
  default, add the declaration only") was taken.
- **The F15 fix is a subtree rebuild, not a re-read** — see Decisions. Same observable outcome, and
  Step 7's `Ctx` still supersedes it cleanly.
- **`validate()`-style "every declared input is actually read by some `calculation()`"** was not added;
  the review files that under P7/Step 12 and it needs an AST pass. Worth doing there — this step makes
  the input half of that check trivial.
- **PPTX traceability (P11's fourth bullet — deviating inputs rendered in the output)** is explicitly
  out of scope per the plan (Step 13). `print_inputs()` marks deviations with `*` in the meantime.
- Nothing was committed — manual review gate.

**Notes for the next session (Step 5 — limit-scale helpers)**

- **Step 5 changes no report module**, so `tests/golden/report_structure.json` must stay byte-identical;
  it is the cheapest check available and it needs no fixtures.
- The equivalence proof Step 5 asks for compares generated `Limit` objects against today's literals.
  `tests/golden_utils.serialise_limit` already encodes exactly the fields the plan lists
  (`func` samples, `upper`/`lower`, `color`, `rating`, `y_unit`) — reuse it rather than writing a
  second encoder.
- The golden net is **fully green** again (17/17) as of `7d40c04`, and all three fixtures are now
  metadata-correct. Any golden movement you see in Step 5 is yours.
- `Manual[...]` is now the declaration idiom for anything user-settable. If a limit helper grows a
  user-tunable knob, declare it the same way — and remember its class-attribute default comes from
  `manual(...)`, not from an `=`.

---

## 2026-07-27 — Follow-up to Step 4: un-hiding the `__setattr__` guard

Not a plan step. Maintainer review of Step 4 objected to the `if not TYPE_CHECKING:` block in
`criterion.py` and asked for a cleaner construction with the same guarantees.

**What changed**

- [pyisomme/report/criterion.py](../../pyisomme/report/criterion.py) — `Criterion.__setattr__` is a
  normal method again, dedented out of the `if not TYPE_CHECKING:` block. Its body is unchanged; only
  the `value` annotation moved from `Any` to a new module-level **uninhabited class** `Undeclared`,
  documented in its docstring.
- [CLAUDE.md](../../CLAUDE.md) — the "Manual inputs" bullet now describes the `Undeclared` annotation
  and says not to relax it, instead of telling the reader not to un-hide the block.

**Why this works** (the mechanism the Step-4 entry had wrong)

Step 4 concluded "a `__setattr__` mypy can see makes it accept *every* attribute assignment". That is
true only for `value: Any`. Mypy consults `__setattr__` **solely for names the class does not
declare** — a declared attribute is still checked against its own annotation. So an *uninhabited*
value type leaves every legitimate assignment alone and turns an undeclared name into an
`[assignment]` error. Both layers survive with no visibility trick.

`Undeclared` is a bespoke empty class rather than `NoReturn`/`Never`, which would type-check
identically. The only difference is the error text: mypy prints the alias target for `NoReturn`
(`variable has type "Never"` — opaque) but the class name for a real class
(`variable has type "Undeclared"`). Pyright prints `"Undeclared"` either way. One line of code to
make the one degraded message legible, and it aligns the two checkers.

The one regression is that message: an undeclared name now reads
`Incompatible types in assignment (expression has type "bool", variable has type "Undeclared")`
instead of `"Criterion_Head" has no attribute "hard_contct"; maybe "hard_contact"?` — it no longer
names the attribute or suggests the spelling. It still fails, at the same line, and the runtime guard
still prints the "did you mean" version. Judged an acceptable trade for deleting the hack; the
`attr-defined` message cannot be kept without hiding `__setattr__` again.

**Verification** (commands run and their result)

- `.venv/Scripts/python.exe -m mypy` → **Success: no issues found in 34 source files**.
- `.venv/Scripts/python.exe -m ruff check .` → **All checks passed!**
- **Static catch re-proven** (scratch file against the real `EuroNCAP_Frontal_50kmh` tree, then
  deleted). Exactly three errors, on exactly the three bad lines:
  - `head.hard_contact = "yes"` → `expression has type "str", variable has type "bool"` — the manual
    input still checks as `bool`, not as `Undeclared`
  - `head.hard_contct = True` → `variable has type "Undeclared"`
  - `overall.p_drivr = 1` → `variable has type "Undeclared"`
  - clean: `head.hard_contact = True`, `overall.p_driver = 1`, `head.value = 3.0`, `head.name = "Head"`
- **Pyright checked too** (`npx pyright@latest`, 1.1.411, on the same probe inside the repo, then
  deleted) — it is the engine behind VS Code's Pylance, and `pyisomme/py.typed` means *downstream
  users'* editors check their code against these annotations whether they asked for it or not. Same
  four errors, no false positives: `Cannot assign to attribute "hard_contact" for class
  "Criterion_Head" — "Literal['yes']" is not assignable to "bool"` for the type error, and
  `Argument of type "Literal[True]" cannot be assigned to parameter "value" of type "Undeclared" in
  function "__setattr__"` for each typo.
- Probed separately that a subcriterion assigned in `__init__` without a class-level declaration
  (`self.criterion_head = Head()`) is still inferred and still assignable from outside — the pattern
  every `Overall` uses — as are `_`-prefixed names.
- `.venv/Scripts/python.exe -m unittest tests.test_manual_inputs tests.test_report_structure
  tests.test_report_modules` → **OK, 44 tests**. Runtime guard behaviour is untouched.
- `.venv/Scripts/python.exe -m unittest discover -s tests` → **139 tests, 10 errors, 0 failures** —
  the same missing-fixture `FileNotFoundError` set as the Step-4 entry records. No change.

**Deviations / left undone**

- The `[attr-defined]`-style "did you mean" message is lost statically (see above); nothing else.
- Nothing was committed — manual review gate.

---

### Step 5 — Limit scales: build the helpers and prove equivalence (P3, part 1)

**Date:** 2026-07-27 · **Branch:** `refactor/step-4-manual-inputs` (Step 4 is committed; this work sits
uncommitted on top — no new branch was cut because Step 4's own branch is still the tip) ·
**Commit(s):** uncommitted — awaiting review
**Outcome:** done with deviations (four, listed below)
**Review:** ☐ pending

**What was implemented**

- **`pyisomme/report/scales.py`** (new, protocol-neutral) — the parts the three helpers share:
  - `Curve`, a frozen dataclass holding either a constant or an `(xs, ys)` table. `func()` returns the
    callable a `Limit` wants (`np.interp` for a table, which clamps outside `xs` exactly like the
    hand-written lambdas); `blend(other, fraction, decimals)` produces an interpolated intermediate;
    `__neg__` mirrors it. Structural `__eq__` comes free with the dataclass and is what the capping
    rule below tests.
  - `Direction` (`HIGHER_IS_WORSE` / `LOWER_IS_WORSE`) with `best_flags` / `worse_flags`, and
    `Direction.derive(better, worse)`. **This is the plan's "handle the negative-is-worse direction
    centrally"**: no call site passes `upper=`/`lower=` any more, and a negative scale (chest
    deflection, femur, neck My) is written with its PDF numbers and nothing else.
- **`euro_ncap/limits.py` — `sliding_scale(...)`.** Generates Good/Adequate/Marginal/Weak/Poor
  (+ Capping) from `higher=`, `lower=`, `capping=`. `symmetric=True` mirrors the ±Fx-shear and
  ±pubic-symphysis scales from their positive magnitudes.
- **`un/limits.py` — `pass_fail(...)`** (two rows, or four with `symmetric=True`; direction from the
  sign of the threshold) and **`us_ncap/limits.py` — `star_scale({stars: threshold})`** (one bounded
  row per star, plus the open-ended band below the worst entry).
- **`tests/test_limit_scales.py`** (new, 20 tests, **no fixture data**) — the equivalence proof, plus
  unit tests of the helper behaviours the table cannot isolate.
- `tests/golden_utils.serialise_limit` gained an optional `sample_x` argument (backwards compatible)
  so the proof can probe the millisecond-domain corridors; nothing else in the golden net changed.
- `CLAUDE.md` gains a "Limit scales" section.

**The equivalence proof — how it is built, and what it covers**

The plan asks for "a table of (report, criterion, hand-written list, helper call)". The *hand-written
list* column is deliberately **not** a transcription: each report is constructed from **empty
`Isomme`s** (the `tests/test_report_structure.py` trick, so it runs without `data/`) and the expected
rows are read off the live `criterion.limits.limit_list`. The proof therefore tracks the modules and
cannot drift from them. Each `build` receives the criterion, so `c.p` supplies the seating position the
module interpolated into its patterns — one table row covers driver, front and rear passenger wherever
they share a class.

Every row is encoded with `golden_utils.serialise_limit`: name, code patterns, rating, colour,
linestyle, `upper`/`lower`, `x_unit`/`y_unit` and 20 `func` samples — a superset of the fields the plan
names. Comparison is order-insensitive (the modules write the same scale in different orders; see D14)
**and** the `limit_list_sort` order is asserted row for row, because that is the order every rating and
colour lookup actually sees.

| | |
|---|---|
| table rows (helper calls) | **59** |
| criterion instances proven identical | **96** |
| `Limit` rows proven identical | **451** |
| of which hand-interpolated Marginal/Weak rows now generated | **126** |

Coverage per report, with a guard (`TestScaleCoverage`) that fails if a limit block in a *covered*
report is neither in the table nor in `KEEP_RAW` **with a reason**:

| Report | blocks covered | rows covered | kept raw |
|---|---|---|---|
| `EuroNCAP_Frontal_50kmh` | 27 / 30 | 166 / 172 | 3 × shoulder-belt-load modifier |
| `EuroNCAP_Frontal_MPDB` | 22 / 27 | 135 / 147 | OLC + DAMAGE + 2 × belt modifiers, abdomen Good/Poor pair |
| `EuroNCAP_Side_Pole` | 3 / 8 | 24 / 40 | 2 capping-only pairs, 3 Good/Poor pairs |
| `UN_Frontal_50kmh_R137` | 16 / 16 | 40 / 40 | — |
| `UN_Frontal_56kmh_ODB_R94` | 22 / 22 | 52 / 52 | — |

Plus spot cases without a guard: `EuroNCAP_Side_Barrier` (chest lateral compression — the same scale as
Side Pole but capped *at* the Poor limit), `EuroNCAP_Side_FarSide` (±lateral flexion Mx, symmetric with
no capping), `UN_Side_Barrier_R95`, `UN_Side_Pole_R135`.

**Decisions taken** (things the plan left open, or that the code forced)

- **Generated intermediates are rounded to 3 decimals (`DECIMALS = 3`).** This is the decision the whole
  proof hinges on. The modules type the intermediates at three decimals (`566.667`, `-40.333`,
  `-5.557`, `-2.067`, …); the exact interpolation is `566.6666…`. Rounding reproduces **every one of the
  126** literal intermediates *exactly* — checked, not approximated — so Step 6's migration can be
  value-neutral. `decimals=None` gives the exact scale and is offered, tested, and **not** the default:
  switching would move ratings slightly everywhere and is a protocol question, not a refactor one.
- **The Poor row carries no `upper`/`lower` flag when a capping row sits at the same value.** This is a
  real convention in the modules, not an inconsistency: with a flag on both rows, `Limits.get_limits`
  matches the Poor row first and a value beyond capping renders red "Poor" instead of gray "Capping".
  It holds across every capped scale in the repo (HIC, a3ms, chest VC, chest deflection, MPDB neck/chest,
  abdomen lateral) and the counter-examples confirm it: where capping ≠ Poor (driver neck Fz 2.900 vs
  2.620, neck My −57 vs −49, Side Pole chest −55 vs −50) both rows *are* flagged. `sliding_scale` derives
  it from `capping == lower`, and the docstring says why.
- **`points=4` is accepted but validated, not implemented as a variable.** The plan's signature has
  `points=4`. The intermediates' *ratings* (2.669 / 1.329, in `Limit_M`/`Limit_W`) are what make a
  Euro-NCAP scale a 4-point scale, and no other limit classes exist, so any other value would have to
  invent unverifiable ratings. `points != 4` raises a `ValueError` naming exactly that. The intermediate
  *positions* are derived from the class list (`index / (len + 1)` → 1/3, 2/3), so adding classes is the
  one change needed to generalise.
- **Direction is derived, with an override.** `Direction.derive` compares the two thresholds point-wise;
  the plan's explicit `direction=` argument stays available for the case it cannot read. The two
  thresholds may **touch** but not cross — the MPDB passenger neck corridors converge to the same 1.1 kN
  tail, which a strict-inequality rule rejected.
- **`capping_code_patterns=` was added, for one call site.** `frontal_50kmh`'s driver neck Fz matches its
  capping row on `…FOZA` while its other five rows use `…FOZ?`. Reproducing that is the only way the
  proof can be honest about it; the argument makes the anomaly visible in the call rather than hiding it
  behind a wildcard. Logged as **D12** — it needs a maintainer yes-or-no before Step 6 single-sources
  the pattern.
- **Callables are not accepted as a threshold.** `Curve` is a constant or a table, so `blend` and the
  capping-equality test stay structural. The one module threshold that is genuinely computed —
  R137's protocol-dependent passenger chest deflection (`-42 if protocol == "22.06.2016" else -34`) — is
  covered by resolving the protocol in the table row, and stays a raw lambda in the module until F11
  decides how protocol variants are expressed.
- **`unit=` maps to `y_unit`** (the plan's spelling) and `x_unit=` passes through. `None` means "leave
  the `Limit` class default", so a generated row is identical to a literal that omitted the argument.
- **Shapes deliberately left raw** and recorded in `KEEP_RAW` with reasons: modifier tables (0/−1/−2 pt),
  Good/Poor pairs, capping-only pairs (D15), and R95's three-row chest lateral deflection (D13).

**Behaviour changes**

- **None.** No report module was touched, so no criterion, limit, value, rating or colour moved. The
  three goldens and `report_structure.json` are byte-identical (17 + 2 tests pass with zero improvement
  lines). The helpers are new code that nothing calls yet.

**Verification** (commands run and their result)

- `.venv/Scripts/python.exe -m unittest tests.test_limit_scales` → **OK, 20 tests**, 0.15 s.
- **The proof was proven to fail, four ways, each reverted afterwards** (`git status` clean):
  - `DECIMALS` 3 → 4 → **67 failures** (the rounding decision is load-bearing)
  - Poor row always flagged (`capped_at_poor = False`) → **57 failures**
  - intermediates at 1/4, 2/4 instead of 1/3, 2/3 → **112 failures**
  - Good row given the *worse* flag → **112 failures**
- `.venv/Scripts/python.exe -m unittest tests.test_golden` → **OK, 17 tests**, 112 s.
- `.venv/Scripts/python.exe -m unittest tests.test_report_structure tests.test_report_modules
  tests.test_limits tests.test_manual_inputs` → **OK, 46 tests**, 22.9 s —
  `tests/golden/report_structure.json` unchanged, the direct evidence that no report module moved.
- `.venv/Scripts/python.exe -m mypy` → **Success: no issues found in 35 source files** (34 before; the
  new `scales.py` is inside the checked scope and fully annotated).
- `.venv/Scripts/python.exe -m ruff check .` → **All checks passed!**
- `.venv/Scripts/python.exe -m unittest discover -s tests` → **159 tests, 10 errors, 0 failures.**
  Baseline (Step 4 entry): 139 tests, 10 errors, 0 failures. The +20 are this step's; the 10 errors are
  the identical pre-existing set — `FileNotFoundError` for `data/vtc-loadcase-example/*` (which breaks
  the import of the whole `tests/test_report.py` module) and
  `data/tests/{ascii,utf-8,windows-1252,iso-8859-1}`, neither of which has a public source.
- D13's number measured directly (scratch script, deleted): the R95 three-row block rates
  `[0.5, 0.262, 0.0, 0.0]` at `[0, 20, −50, 50] mm` where `pass_fail(symmetric=True)` rates
  `[1.0, 1.0, 0.0, 0.0]`; colours identical.

**Deviations from the plan / left undone**

- **`points` is validated rather than variable** — see Decisions.
- **`capping_code_patterns=` is an extra parameter the plan did not foresee** — see Decisions / D12.
- **The plan's acceptance criterion "asymmetric cases (±Fx shear with a single capping pair) are either
  covered or explicitly documented"**: they are **covered**, by `symmetric=True` — `frontal_50kmh`
  driver ±Fx (capping pair 2.70/−2.70 written at the end of the block), `frontal_mpdb` driver and
  passenger ±Fx, Side Pole ±pubic symphysis, Far Side ±Mx. The genuinely asymmetric block in the repo is
  UN R95's chest lateral deflection, documented as keep-raw with the measured reason (D13).
- **No `good_poor()` helper** for the ~8 Euro-NCAP two-row pairs — the plan names three helpers and
  Step 5 does not improvise (D15).
- Nothing was committed — manual review gate.

**One thing in the working tree that is not mine**

Mid-session, `pyisomme/report/euro_ncap/frontal_50kmh.py` showed a one-line deletion — the comment
`#: The report's criterion tree, defined at module level (see Overall).` above
`Criterion_Overall = Overall` (added in Step 3b). No command of this session edits that file. I reverted
it (`git checkout -- pyisomme/report/euro_ncap/frontal_50kmh.py`) so that this step's diff contains no
report module, as its acceptance criteria require. **If that deletion was deliberate, re-apply it** — it
is inert either way.

**Notes for the next session (Step 6 — `PeakCriterion` + migrate leaves)**

- **Migrate against the proof, not against the source.** Every scale in the table has a helper call that
  is already proven identical; Step 6's job for those blocks is to paste the call, not to re-derive it.
  Once a block is migrated its `CASES` row is redundant with the module — keep the table until Step 6
  lands, then decide whether it folds into Step 12's `describe()`.
- **Expect a golden `definition` re-baseline that is a pure permutation** (D14). Check it as one: the
  set of serialised limit rows per criterion must be unchanged, only their order. Anything else is real.
- **D12 gates the driver neck Fz migration** — it needs the maintainer's answer, not a guess.
- The `Limit_G/A/M/W/P/C`, `Limit_Pass/Fail` and `Limit_1..5` classes are untouched, so a half-migrated
  module (some blocks raw, some generated) works fine. Migrate incrementally.
- `sliding_scale` takes `code_patterns` as its first positional argument, which is where Step 6's
  single-source `codes` declaration will feed in — the signature was chosen for that.

---

## 2026-08-01 — Out-of-band fix: `get_channel` crashed on report construction

Not a refactor step. `EuroNCAP_Frontal_50kmh([v1, v2])` raised
`NotImplementedError: Could not integrate code` from `Page_OLC.__init__`.

**Cause.** Commit `51fdd94` ("fix: various minor fixes") rewrote steps 4/5 of
`Isomme.get_channel` to null-check the recursive result instead of relying on
`AttributeError`. In doing so it moved `code_pattern.integrate()` /
`code_pattern.differentiate()` *outside* the `try`. Those raise `NotImplementedError` for
any dimension with no counterpart code (`DS` has no antiderivative, `AC` no derivative),
which the old code swallowed by design. `get_channel("10VEHCCG00??VEXA")` recurses into
`…DSXA` with `integrate=False`, whose differentiate branch then calls `Code("…DSXA").integrate()`
and the exception escapes to the caller.

**Fix.** [pyisomme/isomme.py](../../pyisomme/isomme.py) — derive the code inside its own
`try`/`except NotImplementedError`; an absent route logs and falls through as before.

**Verified.** `ruff check pyisomme/isomme.py` clean; `mypy` reports nothing in `isomme.py`;
`tests.test_report_structure` / `test_report_modules` / `test_manual_inputs` now *run* (they
aborted with the same NotImplementedError before). The 9 remaining `test_report_structure`
failures are unrelated to this fix and predate it in the working tree: the serialised limit
`y_unit` now prints `g0` instead of `9.80665 m / s2`, from the uncommitted `unit.py` rework.

**Left open.** `Page_OLC.__init__` (and the far-side pages) resolve channels at construction
time rather than at `construct()`/`calculate()` time — the thing that made a lookup bug surface
as a constructor crash. Untouched here; it belongs to the page/`Ctx` work (F15/step 7).

Nothing committed — manual review gate.

---

## 2026-08-02 — Step 5 review: **rejected**, helpers stashed

**Maintainer's verdict:** keep the hand-written list of `Limit` rows per case. P3's generated scales are
withdrawn. The full reasoning now lives in the plan (`…_plan.md` §Step 5, marked WITHDRAWN) so a future
session reads it before re-proposing the idea; the short version:

- A raw list is a literal transcription of the protocol table — checkable against the PDF line by line
  with no knowledge of the framework. `sliding_scale(...)` hides five conventions (1/3–2/3 blend,
  3-decimal rounding, the `capped_at_poor` flag rule, direction-from-sign, `symmetric=` mirroring) and
  converts a visible error into an invisible one.
- It also converts a *local* error into a *global* one: a typo breaks one criterion, a helper bug or a
  misapplied keyword breaks every criterion using it, plausibly and silently.
- The domain is too irregular to cover: 3/8 blocks in `Side_Pole`, 22/27 in `Frontal_MPDB`. A migrated
  module would mix generated and raw blocks.

**Two facts found during this review that support the verdict directly:**

- **D12 was a real bug, and the helper had grown a parameter to reproduce it.** `frontal_50kmh`'s driver
  neck Fz capping row did match `…FOZA` while its five siblings matched `…FOZ?`. The maintainer fixed it
  in **`155f533`** (2026-07-28, "fix(reports): Fixed reports and extended IIHS Small overlap report").
  So `sliding_scale`'s `capping_code_patterns=` argument existed solely to be bug-compatible, and both
  it and the `CASES` row went stale within a day. **D12 is closed — no protocol question remains.**
- **The equivalence proof was already broken.** `tests/test_limit_scales.py:506` calls
  `golden_utils.serialise_limit(limit, SAMPLE_X)`, but the matching optional `sample_x` parameter never
  reached `tests/golden_utils.py` (still `def serialise_limit(limit) -> dict:`, last touched in Step 2).
  The module raises `TypeError` on every comparison. Nothing detected this because nothing else imports
  it. Recorded as evidence of how heavy and how weakly-anchored the proof artefact was.

**What survives of F5.** Both halves of the finding are real and were reassigned rather than dropped:

- *Duplication* (the same HIC scale typed out in five places) → **Step 10**, by sharing one named
  criterion class. Reuse removes the copies without hiding the numbers.
- *Flag/interpolation typos* (the `capped_at_poor` convention especially) → **Step 12**, as
  `validate()` warnings that assert properties of a hand-written block without owning its numbers.
  `scales.py`'s `Curve`/`Direction` are the right building blocks for those checks — recover them from
  the stash rather than rewriting. Both plan sections were updated accordingly.

**Disposition of the code.** Staged as one set and handed to the maintainer to `git stash push --staged`:
`pyisomme/report/scales.py`, `tests/test_limit_scales.py`, the helpers in `euro_ncap/`, `un/` and
`us_ncap/limits.py`, and `CLAUDE.md`'s "Limit scales" section (1164 insertions, no deletions).

**Deliberately *not* staged — an unrelated fix that must stay in the tree.**
`pyisomme/report/euro_ncap/limits.py` also carried a one-line repair,
`from pyisomme.limits import Limit` → `from pyisomme.limit import Limit`. **`HEAD` is broken without
it**: `pyisomme/limits.py` imports `Limit` only under `TYPE_CHECKING`, so
`from pyisomme.limits import Limit` raises `ImportError` at runtime (verified) and
`pyisomme.report.euro_ncap.limits` — hence every Euro-NCAP report — fails to import. Regression from the
`limits.py` → `limit.py` split. The staged blob for that file therefore keeps the old import line, so
stashing removes only the helpers and leaves the fix behind as the sole unstaged change to it.
`tests/test_report_modules.py` should have caught this; check why it did not.

**Also left unstaged, as not-Step-5:** `docs/report.ipynb`, `docs/channel.ipynb`, `tmp.ipynb`,
`tmp.pptx`, `head-trajectory-calculation/`, `tests/test_plotting.py` (new IIHS NIJ page test),
`tests/test_golden.py` (a `#TODO: add all reports here` comment), and this file.

**Open follow-ups created by this decision**

- D13 (R95's three-row chest lateral deflection) and D15 (the unhelped Good/Poor pairs) are now
  **observations about the raw lists**, not migration blockers. D13 stays worth a look — the missing
  `Pass(+42, upper)` row does change `get_limit_ratings(interpolate=True)`, and Step 12's symmetry check
  would surface it.
- **D14 is moot** — no migration, so no golden re-baseline and no permutation to recognise.
- The `serialise_limit` / `TypeError` breakage disappears with the stash; if `scales.py` returns in
  Step 12, the `sample_x` parameter must land in `tests/golden_utils.py` in the same change.

Nothing committed — manual review gate.

---

## 2026-08-02 — Step 12: `validate()` and `describe()` (P7 + P8)

Implemented on top of the working tree of the (rejected) Step 5, on branch `refactor/step-4-manual-inputs`.
Nothing committed — manual review gate.

**What was built**

- **`Criterion.walk()` now yields `(path, criterion)`** ([pyisomme/report/criterion.py](../../pyisomme/report/criterion.py)),
  parent before children, `dir()`-ordered as before. It replaced *three* private copies of the same
  traversal: `Criterion.iter_inputs`, `Report.print_results` and `tests/golden_utils.walk`.
  Proven behaviour-identical to the old `dir()` recursion for all 13 reports (paths **and** object
  identities compared node by node).
- **`pyisomme/report/validate.py`** — `Report.validate(errors_only=False) -> list[Issue]`,
  `Report.print_validation()`, `MetaReport.validate()` (prefixes the sub-report onto the path).
  Nine checks; `Issue` carries `check`/`severity`/`path`/`message`.
  - *errors*: `name` (unnamed criterion), `code_pattern` (a pattern that cannot match a 16-character
    code), `orphan` (a criterion reachable at two paths; a limit in `report.limits` owned by no
    criterion — what a `rebuild_child` leak looks like), `max_rating` with an unknown `aggregation`.
  - *warnings* — **this is where the withdrawn Step 5's value landed**: `limit_flags`, `limit_capping`,
    `limit_interpolation`, `limit_symmetry`, `limit_unit`, plus `unused_input` and `max_rating`.
- **`pyisomme/report/describe.py`** — `Report.describe()` → Markdown: per criterion its class, `source`,
  max rating, aggregation, every `Limit` row (threshold, rating, colour, flag, unit) and every manual
  input. Committed for the two reference reports under `tests/golden/describe/` (845 and 634 lines).
- **`Criterion` gained four definition-only fields**: `source`, `max_rating`, `aggregation`,
  `validate_ignore`. None is read by any `calculation()`.
- **[tests/test_validate.py](../../tests/test_validate.py)** — 30 tests, fixture-free, 4 s:
  24 synthetic-criterion tests (each check fires on a broken block *and* stays quiet on the correct one),
  the 13-report error gate, a warnings snapshot (`tests/golden/validate.json`), a
  construct→calculate smoke run for all 13, the describe goldens, and an `@slow` export smoke run.

**Decisions**

- **`validate()` returns issues, it does not raise or return a bool.** The plan's acceptance criterion is
  "passes for every registered report"; the honest reading with warnings in the mix is *zero errors*,
  which the test asserts, **plus** a committed snapshot of the surviving warnings so a new one shows up
  in a diff and an old one disappearing is noticed too. Three warnings survive today (below).
- **`Curve`/`Direction` were not recovered from the Step-5 stash.** `Curve` is an *authoring-time* spec;
  `validate()` inspects *constructed* `Limit` objects, whose `func` is an opaque lambda, so it samples
  instead (`SAMPLE_X = 0, 0.01, 0.05, 0.1` — a corridor is checked at each x, and only the first failing
  sample is reported so a constant block cannot report the same finding four times). `Direction` is
  reimplemented in 15 lines rather than resurrecting the rejected module. Deviation from the plan's
  "recover them from the stash", taken deliberately.
- **`capped_at_poor` was generalised after the first run disagreed with reality.** The plan states it as
  "the Poor row is unflagged iff a Capping row sits at the same value". Written that way it fired 52 false
  positives on IIHS, where `Limit_G`/`Limit_A` share a value but have *different* ratings and are both
  correctly flagged. The invariant that actually holds is one level up: **two rows at the same value never
  carry the same flag** — because `Limits.get_limits` then has two limits at distance zero and `np.argmin`
  breaks the tie by list order. Euro-NCAP's P/C pair is the special case. Zero false positives after the
  change, and the Poor-row typo is still caught (tested).
- **Code patterns are fnmatch templates, not codes.** `?1CHST000[03]??DSX?` is 19 characters and matches
  16-character codes; the length check counts a character class as one. Straight `Code()` construction
  would have failed on 164 legitimate rows.
- **Two documented opt-outs added to report modules** (`validate_ignore = {check: reason}`):
  `side_farside.py`'s four pelvis/lumbar modifiers (a band pass whose single "0 pt." row spans both signs
  — not a scale, deliberately not mirrored) and `side_farside_vtc.py`'s two ISO-score classes (their two
  `Limit([], ...)` rows are a threshold read directly in `calculation()`, matching no channel on purpose).
- **`max_rating` is derived for leaves, declared for aggregates.** A leaf's limit block already states its
  maximum; `describe()` renders it as "4 (from limits)" and no report module gains a line. See the
  metadata note added to `CLAUDE.md`.
- **`source` is a *section*, and it is inherited down the tree.** The protocol document is a report-level
  fact that `describe()` prints once in the header, so `Criterion.source` holds only `"§5.2.1"`. A
  criterion that declares none renders its nearest ancestor's, marked `(inherited)`
  (`describe.resolve_sources`). That makes "declare it on `Overall` only" a complete answer rather than a
  gap, and refining per body region later is purely additive - no leaf ever repeats its parent.
- **`aggregation` is left unset almost everywhere, on purpose.** `Criterion_Head` is `min` over two result
  children *plus* `sum` over five modifiers — one string cannot say that. Expressing it needs Step 11's
  `role`. Declared only on `Criterion_Driver`, where `sum` really does cover all four children.

**Applied to `frontal_50kmh.py` as a sample** (19 lines added to 1594, +1.2 %): `Overall`
(`max_rating = 8.` and a **placeholder `source`**), `Criterion_Driver` (`max_rating, aggregation =
16., "sum"`), `max_rating = 4.` on `Criterion_Head`/`_Neck`/`_Chest`/`_Femur` — which makes the
propagation check live on a real branch — and a second, narrower `source` on `Criterion_Head` to show
the inheritance. `Criterion_HIC_15` and every other leaf were left untouched.

**Findings the new checks turned up — all left unfixed, they are behaviour changes**

1. **`IIHS_Frontal_Small_Overlap` chest VC, negative side is wrong** (`limit_flags` + `limit_symmetry`).
   Written as `P(-1.2, upper), M(-1.2, lower), A(-1.0, lower), G(-0.8, lower)`; the positive side is
   `G(0.8, upper), A(0.8, lower), M(1.0, lower), P(1.2, lower)`, i.e. M and A sit at different distances
   on the two sides. The criterion rates with `interpolate=False`, which takes the **first** matching row
   in `limit_list_sort` order, so a VC of -0.9 m/s is awarded **Marginal (-10 demerits)** where the
   positive-side equivalent (+0.9) gets **Acceptable (-2)**. The mirrored block
   (`G -0.8 lower, A -0.8 upper, M -1.0 upper, P -1.2 upper`) resolves it correctly. Needs the IIHS
   protocol to confirm before changing a rating.
2. **`UN_Side_Barrier_R95` chest lateral deflection** (`limit_symmetry`) — the already-logged **D13**:
   `+[Fail(42, lower)]` against `-[Fail(-42, upper), Pass(-42, lower)]`, i.e. the `Pass(+42, upper)` row
   is missing. Step 12's check surfaces it exactly as the Step-5 review predicted it would.

**Verification** (commands run and their result)

- `.venv/Scripts/python.exe -m unittest tests.test_validate` → **OK, 30 tests** (1 skipped: the `@slow`
  export run), 4.0 s.
- `... -m unittest tests.test_validate tests.test_report_modules tests.test_manual_inputs tests.test_limits`
  → **OK, 74 tests**, 48 s.
- **Acceptance criterion — the perturbed intermediate.** `566.667` → `556.667` in `frontal_50kmh.py`'s
  HIC15 block reported three warnings (driver, front and rear passenger), each naming the actual and the
  expected value. Reverted; `git status` clean for that file except the metadata sample.
- **Acceptance criterion — the broken aggregation.** `Criterion_Neck.max_rating` `4.` → `2.` reported
  `declares max_rating=16 but sum(['4', '4', '4', '2']) = 14` on `criterion_driver`. Reverted.
- `validate()` over all 13 registered reports: **0 errors, 3 warnings** (the two findings above; the
  IIHS one produces two).
- `... -m ruff check pyisomme/report/ tests/test_validate.py` → **All checks passed!** (the 43 repo-wide
  ruff errors are pre-existing, all in `pyisomme/calculate/`, `channel.py`, `info.py`, `limit.py`,
  `providers.py`, `unit.py` and three test modules — untouched here).
- `... -m mypy` → 8 errors, **all pre-existing in `limit.py`/`olc.py`/`damage.py`**; nothing in
  `validate.py`, `describe.py`, `criterion.py`, `report.py`, `meta_report.py` or the touched report
  modules.
- `tests/golden/report_structure.json` and the three `tests/test_golden.py` baselines are **not**
  regenerated: `walk()` was proven identical, and no limit, page or criterion moved. The 9
  `test_report_structure` failures in the working tree are **pre-existing** and unrelated — the `y_unit`
  repr change from the uncommitted `unit.py` rework, the R94 `?1TIIN...` pattern fix, and the new IIHS
  pages/limits.

**One repair that had to happen first**

`pyisomme/report/euro_ncap/limits.py` line 3 was back to `from pyisomme.limits import Limit`, which
raises `ImportError` at runtime (`limits.py` imports `Limit` only under `TYPE_CHECKING`), so **every
Euro-NCAP report failed to import**. Same one-line fix as recorded in the Step-5 entry — it was lost when
the stash was taken. Re-applied to `pyisomme.limit`. `tests/test_report_modules.py` should have caught
this and did not; worth a look.

**Left open**

- **`source` is unpopulated** everywhere but one placeholder on `Overall`. It is the only field no code
  can recover, and filling it means reading the protocol PDFs — a maintainer job, not a guess.
- **`aggregation`/`max_rating` for the remaining aggregates** wait on Step 11's `role`
  (`RESULT`/`AGGREGATE`/`MODIFIER`), which is what lets "min over results, plus sum over modifiers" be
  said at all.
- **Channel patterns inside `calculation()` are not checked** — only the limits' `code_patterns` are
  declarative today. Step 6's single-source `codes` makes them checkable by the same rule.
- The two findings above need a protocol decision before anything is changed.
- `tests/test_report_structure.py`'s docstring says "Step 12's `Report.describe()` supersedes this; fold
  it in there when it lands." It is **not** folded in: `report_structure.json` compares all 13 reports
  including sampled `Limit.func` values, `describe()` covers 2 and renders for humans. Folding them would
  lose coverage; left as two complementary nets.

---

## 2026-08-03 — Step 12 follow-up: `validate.py` split into a package, `describe` tests split out

Continues the same working tree on `refactor/step-4-manual-inputs`. Nothing committed — manual review gate.
The maintainer had started moving `pyisomme/report/validate.py` into a `validate/` package (one file per
check) and left it mid-flight: the check modules imported each other by bare module name
(`from issue import Issue`), every shared helper was still only in `validate.py`, so **no check module
imported at all** on its own. This session finished that move. No behaviour change was intended and none
was measured — `tests/golden/validate.json` and both `tests/golden/describe/*.md` regenerate byte-identical.

**The package** ([pyisomme/report/validate/](../../pyisomme/report/validate/))

| file | holds |
|---|---|
| `issue.py` | `Issue`, `IssueSeverity`, `format_issues` |
| `util.py` | **new** — everything the checks share: `SAMPLE_X`, `Direction` (now carrying `sign`), `Row`, `blocks`, `sample`, `sides`, `direction_of`, `flag`, `close`, `by_value`, `superseded`, `block_label`, `rows_text`, `per_side` |
| `check_<name>.py` × 9 | one check each; `check_max_rating.py` also owns `AGGREGATIONS` and `derived_max_rating`, `check_limit_interpolation.py` owns `DECIMALS`/`GOOD`/`MARGINAL`/`WEAK`/`POOR`, `check_code_pattern.py` owns the pattern regex and `_CODE_LENGTH` |
| `validate.py` | the `CHECKS` registry and the three entry points (`validate_criterion`, `validate_tree`, `validate_report`) — nothing else |
| `__init__.py` | the public surface, re-exported with `__all__` |

- The private `_`-prefixed helpers lost their underscore when they moved to `util.py` — they are now the
  package's internal vocabulary, spoken across nine modules, not one file's locals. `_sign(direction)`
  became the `Direction.sign` property, next to `best_flag`/`worse_flag` which it belongs with.
- Every module imports absolutely (`from pyisomme.report.validate.util import ...`), matching the rest of
  the repo. Every module gained `from __future__ import annotations` — `check_max_rating.py`'s
  `-> float | None` would otherwise be a runtime `TypeError` on the 3.9 target.
- **Consumers now import the package, not a module inside it**: `report.py`, `meta_report.py`,
  `describe.py` and `tests/test_validate.py` went from `pyisomme.report.validate.validate import …` to
  `pyisomme.report.validate import …`.
- `IssueSeverity` regained its `str` mixin (lost in the split) and an explicit `__str__` returning the
  value. Without the mixin `TestMaxRating.test_unknown_aggregation`'s `severity == "error"` is false;
  without the explicit `__str__` the rendered `[warning]` in `tests/golden/validate.json` becomes
  `[IssueSeverity.WARNING]` on 3.11+, where mixin-enum formatting changed. Both are now version-independent.
- `pyisomme/report/validate/` is a new subpackage under `pyisomme/report/`, so `tests/test_report_modules.py`
  walks it: all four of its guards pass, and `[tool.setuptools.packages.find] include = ["pyisomme*"]`
  already ships it.

**`describe()` tests moved out** — [tests/test_describe.py](../../tests/test_describe.py)

`TestDescribe`, `DESCRIBED`, `DESCRIBE_DIR` and `describe_path` left `tests/test_validate.py`; each module
now regenerates its own baseline (`-m tests.test_validate --regen` → `validate.json`,
`-m tests.test_describe --regen` → `describe/*.md`). `test_describe.py` imports `build`/`leaf`/`attach`
from `test_validate.py` rather than growing a third copy of them. CLAUDE.md updated for both the package
layout and the two regen commands.

**A real defect this surfaced: `tests/test_report.py` still used the old `validate()` contract**

Step 12 changed `Report.validate()` from `-> bool` (HEAD's version, which only checked that every criterion
is named) to `-> list[Issue]`, empty when clean. The 12 call sites in `tests/test_report.py` were left as
`self.assertTrue(report.validate())`, which now asserts the issue list is **non-empty** — so every clean
report *failed*: `AssertionError: [] is not true`. That is 8 of the 20 failures the working tree had.
Rewritten to `self.assertEqual(report.validate(errors_only=True), [])`, which is the new contract's
"nothing is definitely wrong" and tolerates the 3 known convention warnings.

**Verification** (commands run and their result)

- `.venv/Scripts/python.exe -m unittest tests.test_validate tests.test_describe` → **OK, 32 tests**
  (1 skipped: the `@slow` export run), 8.3 s.
- `... -m unittest tests.test_validate tests.test_describe tests.test_report_modules tests.test_manual_inputs`
  → **OK, 74 tests**, 26 s.
- `... -m unittest tests.test_report.TestReport.test_Correlation tests.test_report.TestReport.test_UN_Side_Pole_R135`
  → **OK, 2 tests** (both failed on the stale `assertTrue` before).
- `... -m tests.test_validate --regen` → 3 warnings over 13 reports; `... -m tests.test_describe --regen`
  → 845 and 634 lines. **`git diff tests/golden/` empty** — the split changed no finding and no dump.
- `... -m ruff check pyisomme/report tests/test_validate.py tests/test_describe.py tests/test_report.py tests/golden_utils.py`
  → **All checks passed!**
- `... -m mypy` (configured scope) → **Success: no issues found in 49 source files**.
- `... -m mypy tests/test_validate.py tests/test_describe.py` (outside the configured scope, checked on
  request) → **Success: no issues found in 2 source files**.

**Two config/annotation repairs needed to get there**

- `[tool.mypy]`'s `follow_imports = "silent"` override list had gone stale: `pyisomme.limit` (split out of
  `limits.py`) and the `pyisomme.calculate` **package**'s submodules were not covered, so 8 pre-existing
  core-module errors were failing the type check. Added `"pyisomme.limit"` and `"pyisomme.calculate.*"`.
  This changes no code — it restores the documented intent that only `pyisomme/report/` is enforced.
- To make the two test modules type-clean: `leaf()`'s dynamic class is annotated `type[Criterion]`,
  `sliding_scale()` builds its flag kwargs as `dict[str, Any]`, and dynamic subcriterion assignment goes
  through a new `attach(parent, name, child)` helper. `attach` uses `setattr`, which a type checker does
  not route through `Criterion.__setattr__` — whose value is typed `Undeclared` **on purpose** (step 4) to
  reject a mistyped input name. A subcriterion is the one thing that annotation cannot express, so the
  helper documents it once instead of scattering `# type: ignore` over the tests.
- `tests/golden_utils.py` gained two annotations (`serialise_limit(limit: Limit)`, `_read(...) -> Isomme`);
  it is imported by both test modules, so its untyped defs surfaced there.

**Still failing in the working tree — all pre-existing, none touched here**

Full suite before this session: `Ran 243 tests`, **20 failures / 2 errors**.
After: `Ran 243 tests in 1208 s`, **12 failures / 5 errors**. The eight `test_report` failures are gone
(the stale `assertTrue` above); the run got ~10× longer for the same reason — those tests now reach the
`calculate()` + `export_pptx()` they had been aborting before.

What remains:

- `test_report_structure` (9 reports) and `test_golden` (3) — the `y_unit` repr change from the
  uncommitted `unit.py` rework, exactly as the previous entry recorded. Diffed one to be sure:
  `EuroNCAP_Side_Pole` differs **only** in `y_unit`, golden
  `"  Name = Standard acceleration of gravity\n  Value = 9…"` against current `"g0"`. Not a
  validate/describe concern and deliberately not re-baselined here.
- `test_isomme.test_read`, `test_plotting…nij_page_uses_criterion_limits` — unchanged, both were already
  failing.
- **Three `test_report` errors are newly *visible*, not newly broken**: `test_EuroNCAP`,
  `test_EuroNCAP_Frontal_50kmh`, `test_EuroNCAP_Frontal_MPDB` all die in `export_pptx` →
  `plotting.plot_channel` → `Channel.convert_unit` with
  `UnitConversionError: 'm / s' (speed/velocity) and 'm / s' (speed/velocity) are not convertible` —
  the same wrapped-`Unit` identity problem as the `y_unit` diffs, i.e. the in-flight `unit.py` rework.
  The stale `assertTrue` had been aborting these tests two lines earlier, so fixing it uncovered them.
  **This one is worth the maintainer's attention**: it means the two reference reports currently cannot
  render a PPTX.

`ruff check .` is likewise still red repo-wide (35 findings: `pyisomme/calculate/`, `channel.py`, `info.py`,
`limit.py`, `providers.py`, `unit.py`, `tests/test_calculate.py`, `test_code.py`, `test_info.py`,
`test_unit.py`), almost all `W291`/`W293` whitespace plus 3 `F401` and 3 `E701`. All of it is committed
code from the `calculate`/`providers` work, outside this step; `ruff check --fix` clears 27 of the 35 when
someone wants to take it on.

## 2026-08-03 — Out-of-band: `page.py` split into a package (one module per template)

Continues the same working tree on `refactor/step-4-manual-inputs`. Nothing committed — manual review gate.
Requested directly by the maintainer, **not** a plan step: `pyisomme/report/page.py` (379 lines, 10 classes)
became `pyisomme/report/page/` with one module per page template. Step 11 still owns the real page work
(`role`, `Page.select(overall)`, dropping the `page.__init__` re-run, A13); this is the file layout only.

**The package** ([pyisomme/report/page/](../../pyisomme/report/page/))

| file | holds |
|---|---|
| `base.py` | `Page` — the bare interface (`name`, `report`, `construct`) |
| `content.py` | `Page_Content` — titled slide + footer; `_current_user()` |
| `figure.py` | `Page_Figure` — **new**, the shared "measure/remove the content placeholder, render a figure into it" template; `FIGSIZE_Y` |
| `cover.py` | `Page_Cover` |
| `criterion_table.py` | `Page_Criterion_Table` (+ `TRANSPARENT`) |
| `criterion_values_table.py` / `criterion_rating_table.py` | the two concrete criterion tables |
| `criterion_values_chart.py` | `Page_Criterion_Values_Chart` (+ `limit_x`) |
| `plot_nxn.py` / `line_table.py` / `olc.py` | `Page_Plot_nxn`, `Page_Line_Table`, `Page_OLC` |
| `__init__.py` | the public surface, re-exported with `__all__` |

Every existing import site keeps working unchanged — they all read
`from pyisomme.report.page import Page_Cover, Page_OLC, ...`, which is now the package. As with
`validate/`, **import from the package, not from a module inside it**.

**What changed beyond moving code**

- **`Page_Figure` (the point of the split).** Five `construct()` bodies repeated the same 18 lines:
  read `slide.placeholders[1]`'s geometry, unlink the placeholder, derive `figsize` from its aspect ratio,
  `savefig` to a `BytesIO`, `add_picture`. That is now inherited, and each figure page implements
  `figure(figsize) -> Figure` instead — `Page_Plot_nxn` and `Page_Line_Table` are down to one call each.
- **`plt.close(fig)` after `savefig`** (behaviour change, deliberate). Nothing closed these figures, so a
  13-page report left 13 figures in pyplot's registry and matplotlib warns past 20. The image is already
  written when it is closed, so the PPTX is unaffected.
- **`Page_Content.footer` is no longer evaluated at import time.** It was a class attribute
  `f"{datetime.now()…} | {os.getlogin()}"`, i.e. the *import* date, and `os.getlogin()` raises `OSError`
  without a controlling terminal — importing `pyisomme.report` at all would have died on such a host.
  It is now `footer: str | None = None` plus `get_footer()`, resolved while the slide is drawn, with a
  `getpass.getuser()` → `"unknown"` fallback. Setting `footer = "…"` on a page still overrides it.
- **`Page_Line_Table` now forwards `cell_colors`, `col_labels_colors` and `col_labels_fontweight`** to
  `Plot_Line_Table`. It declared all three and passed none. A no-op today (nothing sets them, and `None`
  leaves `Plot_Table`'s own defaults in place), but the declarations were dead.
- `row_label`/`cell_text` became real `@staticmethod`s on the two concrete tables. The base still declares
  them as `Callable` attributes, so the `staticmethod(lambda …)` overrides in `correlation.py`,
  `side_farside_vtc.py`, `frontal_50kmh_r137.py` and `frontal_56kmh_odb_r94.py` are untouched.
- `limit_x(criterion)` in `criterion_values_chart.py` replaces the same four-line
  `if criterion.channel is None: 0.0 else get_limit_min_x(...)` written out four times; one of the four sat
  inside a loop that recomputed it per limit. The bar/line maths is otherwise character-identical.
- `np.full((rows, cols), np.nan).tolist()` as a scratch buffer for the table text is gone — every cell was
  overwritten anyway; it is now built directly by comprehension.
- Imports: `from pyisomme import Channel, Isomme` (top-level package, which only resolved because
  `pyisomme/__init__.py` imports `report` *last*) → `from pyisomme.channel import Channel` /
  `pyisomme.isomme`. `Report` is a `TYPE_CHECKING` import everywhere, since `report.py` imports this package.
- `plt.Figure` → `from matplotlib.figure import Figure` (Pylance does not resolve the pyplot re-export;
  same class, so mypy is indifferent). The three pptx-driving modules carry a file-level
  `# pyright: reportAttributeAccessIssue=false, reportIndexIssue=false` (+ `reportOptionalOperand=false` in
  `content.py`): python-pptx hangs `slides`/`shapes`/`placeholders` off an unannotated `lazyproperty`
  descriptor, so nothing in those files is checkable. A `# type: ignore` would have been the wrong tool —
  mypy sees pptx as `Any` and `warn_unused_ignores` would flag every one of them.
- `pyisomme/report/page/` is a new subpackage under `pyisomme/report/`, so `tests/test_report_modules.py`
  walks it (all four guards pass, `BROKEN_MODULES`/`MISSING_REEXPORTS` stay empty) and
  `[tool.setuptools.packages.find] include = ["pyisomme*"]` already ships it. `CLAUDE.md`'s `Page` bullet
  now points at the package and names the `Page_Figure` contract.

**Verified**

- **Definition layer is byte-identical.** `tests.test_report_structure.produce()` dumped for all 13 reports
  before and after the split (old `page.py` restored from HEAD into the same working tree, so the
  maintainer's in-flight `unit.py`/report edits are held constant): `diff` empty, including every
  `pages: [...]` list. The 9 `test_report_structure` failures in this tree are the pre-existing `y_unit`
  repr diffs recorded in the previous entry, unchanged in count and content.
- `... -m unittest -v tests.test_report.TestReport.test_Correlation …test_UN_Side_Pole_R135
  …test_EuroNCAP_Side_Barrier` → **OK, 3 tests**, 34 s. These render 9 + 11 + n slides through
  `export_pptx`, covering `Page_Cover`, `Page_Content`, `Page_Criterion_Table` (both concrete tables),
  `Page_Criterion_Values_Chart` and `Page_Plot_nxn`.
- `Page_OLC`/`Page_Line_Table` **could not be exercised end to end**: `EuroNCAP_Frontal_50kmh` still dies in
  `Channel.convert_unit` with `UnitConversionError: 'm / s' … not convertible` — the in-flight `unit.py`
  problem from the previous entry. Confirmed identical before and after by running the same `Page_OLC`
  construct against HEAD's `page.py` in this tree: same exception, same message. Its `__init__` path
  (channel lookup, `cell_texts`, labels) does run.
- `... -m ruff check pyisomme/report/` → **All checks passed!**; `... -m mypy` → **Success: no issues found
  in 60 source files** (49 before — the 11 new modules).
- Repo-wide `ruff check .` is still the same **35 pre-existing findings** in `calculate/`, `channel.py`,
  `info.py`, `limit.py`, `providers.py`, `unit.py` and four test modules — verified unchanged by running it
  on the stashed tree. Left alone, as the previous entry scoped them out.

**Open**

- Nothing here fixes A8/A13 or `Page.select` — Step 11 still has its full scope, minus the boilerplate it
  would have had to touch five times.
- `Page.name` is still an annotation with no default: a page class that forgets it raises `AttributeError`
  in `__repr__`/`export_pptx` rather than failing at definition time. Left as found.

## 2026-08-03 — Out-of-band: `Unit` lost its wrapper on copy (the PPTX export blocker)

Continues the same working tree on `refactor/step-4-manual-inputs`. Nothing committed — manual review gate.
Not a plan step: a bug fix in `pyisomme/unit.py`, requested after the previous two entries recorded that
**`EuroNCAP_Frontal_50kmh`, `EuroNCAP_Frontal_MPDB` and the `EuroNCAP` MetaReport could not render a
PPTX**, dying in `Channel.convert_unit` with
`UnitConversionError: 'm / s' (speed/velocity) and 'm / s' (speed/velocity) are not convertible`.

**Root cause** — `Unit.__getattr__` delegated *every* attribute to the wrapped astropy unit, dunders
included. `copy` and `pickle` look their protocol methods up on the *instance*, so
`copy.deepcopy(Unit("m/s"))` reached astropy's `UnitBase.__deepcopy__` and returned the **bare astropy
unit**: the wrapper was silently gone. `calculate_olc` deep-copies its velocity channel
([calculate/olc.py:29](../../pyisomme/calculate/olc.py#L29)), so the OLC channel `10SEAT0OLC00VEXA` carried
a raw `CompositeUnit`. `Channel.convert_unit` then called *astropy's* `to()` with a `pyisomme` `Unit` as
the target — an object astropy cannot interpret, hence "m / s and m / s are not convertible". Three lines
reproduce it:

```python
c = Channel("10VEHC000000VEXA", df, unit="m/s")
type(copy.deepcopy(c).unit)                     # astropy.units.core.CompositeUnit  ← wrapper lost
copy.deepcopy(c).convert_unit(Unit("m/s"))      # UnitConversionError
```

The same delegation made `copy.copy(Unit("m/s"))` raise `RecursionError`: `copy` probes
`__setstate__`, `__getattr__` forwards it, and the lookup of `_astropy_unit` on a not-yet-initialised
instance recurses into itself.

**Fix** ([pyisomme/unit.py](../../pyisomme/unit.py), 14 lines added, 3 changed)

- `__getattr__` raises `AttributeError` for any `_`-prefixed name instead of delegating. Public astropy
  attributes (`physical_type`, `is_equivalent`, `decompose`, …) still delegate exactly as before; nothing
  in `pyisomme/` or `tests/` reads a private astropy attribute through the wrapper (checked by grep).
  This alone fixes both the deepcopy leak and the recursion.
- Explicit `__copy__`/`__deepcopy__` returning `Unit(self._astropy_unit)` — cheap, and they say what the
  intent is rather than leaving it to the default `__reduce_ex__` path.
- `__rmul__`/`__rtruediv__` returned **raw astropy units** (`2 * Unit("m")` was not a `Unit`); they now
  wrap, like `__mul__`/`__truediv__` already did. No call site in the repo hits them today — this closes
  the second way a raw unit could reach `Channel.unit`.
- `__hash__` added. Defining `__eq__` had dropped the inherited one, so a `Unit` could not be a dict key
  or set member; it hashes the wrapped unit, so hash and equality agree for `Unit`-vs-`Unit` and
  `Unit`-vs-astropy-unit alike.

**Tests** ([tests/test_unit.py](../../tests/test_unit.py), +62 lines) — `TestCopyingAndHashing`
(deepcopy/copy/pickle keep the wrapper, private names are not delegated, hashable, and the
**end-to-end regression**: a deep-copied `Channel` still converts `m/s → m/s` and `m/s → km/h`) and
`TestReflectedArithmetic`. All fixture-free, so they run in CI.

**Verified** (commands and results)

- `... -m unittest tests.test_unit tests.test_channel tests.test_calculate` → **OK, 59 tests**, 2.4 s.
- The three reports that could not export, each run alone with `PYISOMME_SLOW=1`:
  `test_EuroNCAP_Frontal_50kmh` → **OK** (41 s; it took 168 s to *fail* before),
  `test_EuroNCAP_Frontal_MPDB` → **OK** (125 s), `test_EuroNCAP` → **OK** (122 s).
- `... -m ruff check pyisomme/unit.py tests/test_unit.py` → 8 findings, **all pre-existing whitespace**
  (`W291`/`W293`) in code this change did not touch; repo-wide `ruff check .` is unchanged at **35**.
  The new code adds none (a first draft did: `B018` on a bare attribute access, rewritten as `getattr`).
- `... -m mypy` (configured scope) → **Success: no issues found in 60 source files**.
- Full suite, `... -m unittest discover -s tests`: **251 tests, 12 failures / 2 errors** in 898 s,
  against **243 tests, 12 failures / 5 errors** in 1208 s before (+8 new tests). The three vanished
  errors are exactly the three reports that could not export. Every remaining failure is one of the
  pre-existing three groups below — the fix changed **no computed value**: `test_golden` still fails on
  its *definition* layer only, with the same `y_unit`/tibia rows as before.

**D8/D9 (the 13-report stack overflow): hypothesis raised, then disproved.** An unbounded `__getattr__`
recursion is exactly the shape that produces a Windows `0xC00000FD`, so the D9 repro was re-run: construct
**and** calculate all 13 reports from empty `Isomme`s in one interpreter. It passes **with** the fix — but
it also passes **without** it (HEAD's `unit.py` restored into the same tree, `ALL 13 OK`, exit 0). So the
cheap repro no longer reproduces on the current tip at all, and this fix cannot be credited with it. D8/D9
stay open and now need a fresh repro before anyone can diagnose them.

**Not done here, deliberately**

- **The stale goldens are untouched.** The 9 `test_report_structure` + 3 `test_golden` failures are all
  definition-layer and predate this fix: 73 `y_unit` repr changes (`"9.80665 m / s2"`, and one 5-line
  CODATA dump, → `"g0"`) from the committed `unit.py` rework, plus the tibia-index pattern change
  `?1TIIN??????000?` → `?1TIIN??00??000?` and IIHS Small Overlap's new limits and 3 new pages from
  `a6f204f`. No `value`/`rating`/`color` regression anywhere. Re-baselining is a separate, deliberate
  decision — it wants its own diff.
- `tests/test_isomme.py::test_read` still errors on the missing fixture `data/nhtsa/11391.tar` (a `data/`
  gap like D11, not code), and `tests/test_plotting.py`'s `KeyError` is in the maintainer's own
  uncommitted test.
- `CLAUDE.md`'s unit convention now states the rule the bug broke: delegate public names only, and never
  let a raw astropy unit reach `Channel.unit`.

## 2026-08-03 — Out-of-band: re-baselined the four stale snapshots

Continues the same working tree on `refactor/step-4-manual-inputs`. Nothing committed — manual review gate.
The 9 `test_report_structure` + 3 `test_golden` failures the previous three entries kept recording were
**all stale baselines**, not regressions: every one is in the *definition* layer, and `compare()` reports
**0 regressions in the results layer and 0 improvements** for all three golden reports — no `value`,
`rating`, `color` or `status` moved. Re-baselined deliberately:

```
.venv/Scripts/python.exe -m tests.golden_regen
.venv/Scripts/python.exe -m tests.test_report_structure --regen
```

**What moved, and which commit moved it** (4 files, +313 / −132 lines)

| # rows | change | cause |
|---|---|---|
| ~108 | `y_unit` `"9.80665 m / s2"` — and one 5-line CODATA block for the `g0` quantity — → `"g0"` | `342e533` *refactor(Channel, Unit)*: the new `Unit` registers `g0` as a named astropy unit, so it now reprs as itself instead of its expansion |
| 1 | `frontal_50kmh` driver neck Fz capping row `?1NECKUP00??FOZA` → `?1NECKUP00??FOZ?` | `155f533` — this is **D12**, and it is settled: the narrow filter class was the typo the Step-5 entry suspected, already fixed in the module |
| 10 | tibia index `?1TIIN??????000?` → `?1TIIN??00??000?` (MPDB driver + passenger, R94 driver + passenger) | `a6f204f` *feat(tibia-index)* |
| 8 + 3 | `IIHS_Frontal_Small_Overlap`: tibia axial force and tibia index gained a 4-row limit block each (previously `[]`), and 3 pages appeared (`Page_Driver_Tibia_Compression`, `…_Tibia_Index_Total`, `…_Foot_Acceleration`) | `a6f204f` |

Nothing else changed: a key-by-key diff of the regenerated files against the old ones contains only
`y_unit`, the two `code_patterns` corrections, and the added IIHS rows/pages.

**Verified**

- `... -m unittest tests.test_golden tests.test_report_structure tests.test_validate tests.test_describe`
  → **OK, 51 tests** (1 skipped), 57 s. `validate.json` and the `describe/*.md` dumps needed **no**
  regeneration — they were already current.
- Full suite, `... -m unittest discover -s tests` → **251 tests, 0 failures, 2 errors** (409 s), from
  12 failures / 2 errors before the re-baseline and 12 failures / 5 errors at the start of the day. Both
  remaining errors are known and are not code: `test_isomme.test_read` wants the missing fixture
  `data/nhtsa/11391.tar`, and `test_plotting`'s `KeyError` is in the maintainer's own uncommitted test.

**Note for review:** `tests/golden/euro_ncap_frontal_50kmh.json` (like `pyisomme/unit.py` and
`tests/test_unit.py`) shows up **staged** rather than unstaged in `git status`. Nothing in this session ran
`git add`; use `git diff HEAD` to see the whole change.

## 2026-08-04 — Step 7 plan revision (no code): `Ctx` generalised, `role` defined

Planning only — nothing under `pyisomme/` was touched. Two corrections to Step 7, both raised by the
maintainer while reviewing the handover, both now written into the plan's Step 7 section:

1. **`Ctx` must not be an occupant object.** The plan (and the sketch) had it carry `position`,
   `dummy`, `side`. That builds the occupant crash test into the framework, and pyisomme's reports are
   not all occupant tests. Measured in the repo: under `euro_ncap/` + `iihs/`, **144 criteria take a
   position `p` and 11 take none** (`DoorOpeningDuringImpact`, the MPDB compatibility modifiers reading
   the literal `M?MBAR0OLC??VEX?`, the structural measurements), and
   `Correlation.Criterion_Curve_Correlation` takes neither — it is constructed with two `Channel`s. The
   current hand-wired code already distinguishes these; a mandatory `position` would have been a
   *regression*. Revised: the core carries `report`, `isomme` and an immutable mapping of
   **code-template fields** (`ctx.code("?{p}NECKUP00??MOY?")`); `at=` takes a context *source*
   resolving `(parent_ctx, criterion) -> Ctx`, of which occupant seating is one implementation living
   beside the reports that need it. Two acceptance criteria added: a tree with no occupant anywhere
   must build/calculate/validate, and a second `at=` source besides seating must exist.
2. **`role` needed strict definitions.** Added a table for `RESULT`/`AGGREGATE`/`MODIFIER` with their
   rating semantics, the three consumers that make the classification load-bearing (`modifiers_sum()`;
   `min_of_children()`/`sum_of_children()` excluding modifiers — the "min over results plus sum over
   modifiers" box CLAUDE.md records as inexpressible until this step; `validate()`'s budget check and
   Step 11's `Page.select`), and rules of thumb. Answering the question directly: **`AGGREGATE` is not
   limited to `min`/`max`/`mean`** — `calculation()` may do anything, and `frontal_50kmh`'s `Overall`
   (nanmean, halved, interp-clamped, plus a modifier) stays as it is. The *constrained* field is Step
   12's separate `aggregation` declaration, which is optional and exists only for the budget check.
   A fourth `INFO` role is explicitly **not** added on spec; raise it if a real case appears in Steps 8-9.

Handover artefacts for the next session (both temporary, delete when Step 7 lands):
[docs/log/20260803_Step-7-handover.md](20260803_Step-7-handover.md) and
[docs/log/20260803_Step-7-example.py](20260803_Step-7-example.py) — the latter is a non-executable
sketch of the target style on real `frontal_50kmh` criteria, ending in the six design questions
(D-1 … D-6) the implementing session must settle first. `docs/` is excluded from ruff and outside
mypy's scope, so neither file affects the gates.

## 2026-08-04 — Euro NCAP AOP v9.3 audit of the four main load cases (not a plan step)

Maintainer-requested review of
[references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf](../../references/Euro-NCAP/euro-ncap-assessment-protocol-aop-v93.pdf)
(§2–§5 and Appendix I) against `frontal_50kmh.py`, `frontal_mpdb.py`, `side_barrier.py` and
`side_pole.py`, then the fixes and extensions the maintainer signed off on. **Outside the step
sequence** — it touches criterion *definitions*, not the architecture, so Step 7 is unaffected except
that its `Ctx` work now has more modifier criteria per occupant to carry.

### Verified correct against the PDF (no change)

Every limit table matched, digit for digit, including the interpolated intermediate bands: §4.1.1
head (500/700/700, 72/80/80 with the thirds at 566.667/633.333 and 74.667/77.333), §4.1.2 neck with
capping **driver-only** (the front/rear copies correctly omit `Limit_C`), §4.1.3 chest on the 2023
value of 34.0 mm, §4.1.4 femur 2.60/6.20, the whole of §3.1.2–§3.1.5, §3.1.6.2's time-dependent
passenger shear/tension curves, the Appendix I femur cumulative-exceedance curves
(9.07@0 ms → 7.56@10 ms with thirds at 5.557/5.053 and 7.313/6.307), and §5.1.2's **50 mm MDB /
55 mm pole** capping split, which `side_barrier` already implemented by overriding only the capping row.

### Fixed

| # | Where | § | Change |
|---|-------|---|--------|
| 1 | `frontal_50kmh` rear passenger head | §4.1.1.3 | Branch was **inverted**: hard contact scored the 3 ms exceedance alone and *no* contact scored HIC15 + 3 ms. Swapped. The absent 80 g auto-detect is correct here — §4.1.1.3 is high-speed-film only — and is now documented on the input. |
| 2 | `frontal_mpdb` `Overall` | §3.4, §3.3 | The 16-point sum was never halved. Now `interp → /2 → modifiers → clamp ≥ 0`, so the compatibility penalty lands on the 8-point test score it is defined against. |
| 3 | `frontal_50kmh` rear passenger neck | §4.1.2 | `np.min([1, rating])` **clipped** the shared 4-point scale, flattening Good/Marginal/Weak onto 1.0. Replaced with `rating * max_rating / 4`, and the budgets (2/1/1) are now declared as `max_rating` with a `validate_ignore` reason. |
| 4 | `side_pole` head | §5.1.1.2 | Scored the 3 ms exceedance; the pole table asks for **peak** resultant acceleration (the barrier table, §5.1.1.1, is the one that asks for 3 ms). New `Criterion_Head_Peak_Acceleration` reading `?pHEAD??00??ACRA`. Since peak ≥ a3ms, the old code under-capped. |
| 5 | `frontal_50kmh` `Overall` | §4.3 | Averaged **all three** occupants. §4.3 averages driver and rear passenger; the front passenger enters only through the 90 % check, which then takes each front-row region from the worse of the two. New input `front_passenger_meets_90_percent` (default `True`) selects between the two. |
| 6 | `frontal_50kmh` chest VC | — | `self.value` took `np.min` of a curve whose loading peak is **positive** (`vc = v_t * c_t`, both factors carry the deflection's sign), so it reported the unloading trough. Now abs-argmax, matching `calculate_vc` and every side-impact VC site. Ratings were always correct — they scan the whole curve — only the reported number was wrong. |

### Extended (all new modifiers default to no penalty, so no result moved)

- **`frontal_50kmh`** — added the rear passenger's *Unstable Contact on the Airbag* (§4.2.1 says
  "Driver and Rear Passenger"; only the driver had it). **Removed** the dead
  `Criterion_ExceedingForwardExcursionLine` from the driver and front passenger: `calculation()` was
  `self.rating = 0` while declaring three manual inputs, and §4.2.1 scopes the modifier to the rear
  passenger, where the real logic already lives. That answers open question **Q4 / finding A15**.
- **`frontal_mpdb`** — §3.2.1 lists ten driver modifiers of which three existed. Added *Unstable
  Contact on the Airbag*, *Hazardous* and *Incorrect Airbag Deployment*, *Displacement of the Steering
  Column* (all §3.2.1.1, subclassed from the `frontal_50kmh` originals purely to override `source`),
  *Steering Wheel Contact*, *Displacement of the A Pillar* (−2, §3.2.1.2), *Integrity of the Passenger
  Compartment* (−1), *Variable Contact* and *Concentrated Loading* (−1 per leg, §3.2.1.4), *Upward
  Displacement of the Worst Performing Pedal* (§3.2.1.5), *Footwell Rupture* and *Pedal Blocking*
  (§3.2.1.6). Per §3.2.2 the passenger got the three airbag modifiers and the two knee modifiers, and
  deliberately **not** the steering-column, A-pillar, compartment-integrity or submarining ones.
- **`side_pole` / `side_barrier`** — added *Incorrect Airbag Deployment* (§5.2.4) and *Door Opening
  during the Impact* (§5.2.5) to both, and the pole-only *Side Head Protection Device* (§5.2.3, −2
  front / −2 rear). Both `Overall`s now clamp at ≥ 0 after modifiers.
- **Definition metadata** — `max_rating` / `aggregation` / `source` across all four modules; the two
  `source = "§TODO …"` placeholders resolved to `§4` and `§4.1.1`. Classes shared *across* protocols
  (`Criterion_HIC_15`, `Criterion_ShoulderBeltLoad`, `Criterion_Submarining`, `Criterion_Chest_VC`,
  `Criterion_DoorOpeningDuringImpact`) deliberately carry **no** `source` and inherit it from their
  position in each tree; where a shared class needed a different section in MPDB it was subclassed
  with one line. `aggregation` is declared only where every child has a budget (the occupants' `sum`,
  and the rear passenger's neck) — regions with modifier children leave it unset, as CLAUDE.md requires.
- `side_pole`/`side_barrier` `criterion_head_a3ms` was **renamed** `criterion_head_acceleration` so the
  attribute is honest in both (peak in the pole, 3 ms in the barrier) and the pages `side_barrier`
  inherits from `side_pole` keep working without an override.

### Verified

- `ruff check pyisomme/report/euro_ncap/` → clean; `mypy` → **Success, 60 source files**.
  (`ruff check pyisomme/` reports **24 pre-existing** errors in `channel.py`, `info.py`, `limit.py`,
  `providers.py`, `unit.py` and `calculate/tibia_index.py` — untouched here, present on `HEAD`.)
- `tests.test_validate` → **OK, 28 tests**, `validate.json` unchanged: every new `max_rating` and
  `aggregation` is self-consistent, and no new warning appeared.
- `tests.test_golden` before re-baselining reported **13 regressions, every one intended**: six
  "criterion disappeared" for the two removed excursion criteria, four `chest_vc.value` sign changes
  (e.g. `-0.1029 → 0.1386`), `Overall.rating 6.6298 → 6.7934` for `AK3T02FO` (arithmetically exactly
  `mean(13.5869, 12.9322)/2 → 13.5869/2`, i.e. the §4.3 fix), and the `criterion_head_a3ms` rename in
  `side_barrier`. Tolerated as improvements: 20 new criteria, plus
  `criterion_rear_passenger/criterion_head/criterion_hic_15.status: PENDING → NA` in both frontal
  fixtures — direct evidence that fix #1 now reaches HIC15 where it previously never did.
- Re-baselined deliberately: `tests.test_report_structure --regen`, `tests.test_describe --regen`,
  `tests.golden_regen`. The structure diff was read back criterion by criterion: **no `limits` block
  changed anywhere** — the only definition edits are added/removed criteria and the one rename.
- After the re-baseline, `... -m unittest tests.test_golden tests.test_report_structure
  tests.test_validate tests.test_describe tests.test_manual_inputs tests.test_report_modules`
  → **OK, 93 tests** (1 skipped), 393 s. The `Correlation` `ValueError: zero-size array` traceback in
  that output is pre-existing and *logged*, not a failure — `Criterion.calculate` turns it into
  `Status.ERROR`; it appears identically on `HEAD`.

### Not verified by the fixtures — read before trusting

`Overall` is `nan` in all three MPDB fixtures (the driver is `nan` in every one) and the rear
passenger's neck is `nan` in both frontal fixtures, so **fixes #2 and #3 are not exercised by any
golden**. Both were checked directly instead:

- MPDB perfect 4/4/4/4 on both occupants → `8.0`; with −8 compatibility → `0.0`; with −2 compatibility
  and −1 door → `5.0`.
- Rear passenger neck Fx shear at 1.00 / 1.50 / 1.95 / 2.50 kN → `1.0000 / 0.6002 / 0.0000 / 0.0000`
  against a linear expectation of `1.0 / 0.6 / 0.0 / 0.0` (the 0.0002 is the pre-existing piecewise
  Good/Marginal/Weak/Poor band structure, identical to the driver's).

A regression test for both belongs in `tests/`; not added here because it needs a fixture-free way to
pin an occupant's region ratings, which Step 7's `Ctx` will make cheap.

### Still open (not done — out of the agreed scope)

- **§5.3 has no aggregation anywhere.** `EuroNCAP` (`euro_ncap.py`) only concatenates pages: side
  barrier + pole are never summed and scaled to 12, far side is never capped at 4, and the four load
  cases are never combined into the Adult Occupant Protection score.
- **`side_pole` / `side_barrier` hard-code `p = 1`** with no manual input and no
  `Driver position object 1` lookup, unlike both frontal reports — the struck-side occupant is not
  always position 1.
- **MPDB compatibility is one third implemented.** `Criterion_SD_Modifier` and `Criterion_BO_Modifier`
  are `pass` stubs with their wiring commented out; §3.3.1 (barrier deformation SD, 50–150 mm) and
  §3.3.3 (bottoming out, −2) are missing. Only OLC (§3.3.2, 25–40 g) exists.
- **§3.1.3.1 asks for "max compression of all 4 ribs"** and §3.1.3.2 for "max compression (left or
  right)"; the code reads the single aggregate channels `CHST0000…DSXC` / `ABDO0000…DSXC`. Whether
  `get_channel` already synthesises the worst-of-four was not established.
- **`calculate_damage` labels DAMAGE `rad/s²`** (it inherits the angular-acceleration unit); DAMAGE is
  dimensionless. The limit rows in `frontal_mpdb` match that label, so the report is self-consistent —
  the wrong unit is in `pyisomme/calculate/damage.py`, outside this review's scope.

### 2026-08-04 (same session, follow-up) — §5.3 aggregation, `p` as an input, TODO markers

Four maintainer follow-ups on the audit above.

**1. The struck-side position is a manual input.** `EuroNCAP_Side_Pole` and `EuroNCAP_Side_Barrier`
replaced `p: int = 1` with `p: Manual[int, manual(1, source="test report", …)]`, derived from the
`Driver position object 1` test-info field exactly as the frontal reports do, plus the same interim
F15 `sync_position()` / `rebuild_child()` pair driven by a new `positioned_children` tuple. Verified:
setting `overall.p = 3` and calling `calculate()` moves the head limits from `?1HICR0015??00RX` to
`?3HICR0015??00RX` in both reports. `side_barrier` writes its own `sync_position` rather than aliasing
the pole's — mypy rejects an unbound method borrowed across unrelated classes
(`Invalid self argument "Overall"`).

**2. §5.3 aggregation now exists** ([euro_ncap.py](../../pyisomme/report/euro_ncap/euro_ncap.py)),
with `MetaReport` grown to support it:

- `MetaReport` gained `max_rating`, a `ratings` breakdown dict, a `sub_rating(report)` helper (the
  sub-report's `Overall`, averaged if a load case holds several tests) and a `print_results` that
  prints the breakdown and the total. `calculation()` keeps its no-op default and is now documented as
  the hook — not every meta-report has a scheme tying its load cases together.
- `EuroNCAP.calculation()` implements §5.3: barrier + pole (16 each, after modifiers) are summed and
  `np.interp`-scaled to 12 with clamping at both ends, far side is limited to 4, and the two frontal
  load cases contribute their 8 each. Total budget 32.
- **`nan` propagates on purpose** — `np.sum`, not `np.nansum`. A load case with no data must read as
  unknown, not as a low score.
- Checked by hand: a perfect run of all five sub-reports → `32.0`; halving the barrier and pushing far
  side to 9 → `{8, 8, 9, 4}` = `29.0` (far side correctly clamped to 4); an `nan` MPDB → total `nan`.
  `tests.test_report.TestReport.test_EuroNCAP` (opt-in slow) passes end to end — `validate(errors_only=True)`
  clean, `calculate()`, `out/EuroNCAP.pptx` written — and prints the new breakdown.

**3. Ruff.** `ruff check pyisomme/` is clean — the maintainer fixed the 24 core-module errors. **10
errors remain under `tests/`** (`test_calculate.py` E701, `test_code.py`/`test_info.py` W293,
`test_unit.py` W291, `test_info.py` F401), 9 of them `--fix`-able. Untouched here: those files are
uncommitted work belonging to another thread.

**4. `# TODO` markers for every open issue**, so none of them lives only in this log:

| Marker | File | Issue |
|---|---|---|
| `TODO(protocol)` | `euro_ncap.py` | AOP is really out of 38 — whiplash (§6.3, 4 pts) and rescue (§7, 2 pts) are not modelled, so `rating` is deliberately not a percentage |
| `TODO(protocol)` | `frontal_mpdb.py` | §3.3.1 barrier deformation SD and §3.3.3 bottoming out are missing; only OLC exists, so the penalty cannot reach the −8 cap |
| `TODO(channel)` ×2 | `frontal_mpdb.py` | §3.1.3.1 "all 4 ribs" and §3.1.3.2 "left or right" read single aggregate channels |
| `TODO(test)` | `frontal_mpdb.py` | the §3.4 halving is nan in every fixture |
| `TODO(test)` | `frontal_50kmh.py` | the rear-passenger neck rescaling is nan in every fixture |
| `TODO(unit)` | `calculate/damage.py` | DAMAGE is dimensionless but carries `rad/s²`; the MPDB limit rows match, so both must change together |
| `TODO(input)` ×4 | `side_farside.py`, `side_farside_vtc.py`, `un/side_barrier_r95.py`, `un/side_pole_r135.py` | still pin `p = 1`; the pole/barrier pattern is the template |

`side_farside*` and the two UN side reports were given the marker rather than the change: the far-side
files carry another thread's uncommitted edits, and the UN reports are a different protocol family,
outside this review.

**5. `Criterion_UnstableAirbagSteeringWheelContact` → `Criterion_UnstableAirbagContact`** (raised in
review: "rear passenger never has a steering wheel"). §4.2.1 scopes the modifier to "Driver **and
Rear Passenger**", so extending it to the rear passenger was right, but the class had promoted a
driver-only *example* — "detachment of the steering wheel from the column" — into its name. Renamed
class, attribute and the manual input (`unstable_airbag_steering_wheel_contact` →
`unstable_airbag_contact`) across `frontal_50kmh` and `frontal_mpdb`; the display name is now
"Modifier for Unstable Airbag Contact" and the input doc carries §4.2.1's actual test (head CoG past
the outside edge of the airbag) with the steering wheel demoted to the example it is. All three
goldens re-baselined for the path rename; **93 tests OK**. The genuinely driver-specific criteria
keep their names and their `is_driver` guards: `Criterion_DisplacementSteeringColumn` (§4.2.1),
`Criterion_SteeringWheelContact` (§4.2.2, chest) and `steering_wheel_airbag_exists`.

---

## 2026-08-04 — Step 7: the `sub()` + `Ctx` framework (P1 + P2), framework only

Implements the plan's Step 7. **No report is migrated** — the machinery is purely additive and
coexists with the 13 hand-wired reports, which is what makes it verifiable before Step 8 depends on
it. Written against `docs/log/20260803_Step-7-handover.md` and `…_Step-7-example.py`.

### The five design decisions

D-1, D-2, D-3 and D-5 were settled with the maintainer at the start of the session; D-4 and D-6 were
already settled in the plan on 2026-08-04.

| # | Decision | Taken |
|---|---|---|
| D-1 | Limits are rebuilt from a hook the framework calls at the start of `calculate()`, replacing the criterion's rows in **both** its own list and the report-level one | recommendation (a) |
| D-2 | The framework always calculates declared children; a conditional stays in the *aggregation*, not in whether the child runs | recommendation |
| D-3 | `parent` link added (`Criterion.parent`, `ancestors()`, `find_input_owner()`); existing back-references **not** rewritten — that is Step 9/10 and needs Q5 | recommendation |
| D-4 | `Ctx` carries `report`, `isomme` and a mapping of code-template fields, nothing occupant-specific; seating is a `CtxSource` living in a shared `occupant.py` | plan |
| D-5 | Only *framework-owned* children (declared + `add_child`) are auto-calculated; a not-yet-migrated `calculation()` keeps calculating its own, so nothing runs twice | see below |
| D-6 | `Role` = RESULT / AGGREGATE / MODIFIER, no speculative `INFO` | plan |

Two things the example file did not anticipate, both confirmed with the maintainer before coding:

- **The hook cannot be called `limits()`** — `Criterion.limits` is already the `Limits` object every
  `calculation()` reads (`self.limits.get_limit_min_rating(...)`); the example's own `HIC15` sketch
  used both spellings for the same name. It is **`define_limits() -> list[Limit]`**.
- **A `prepare()` hook was needed.** `calculate()` runs the children *before* `calculation()`, but
  Step 8's `derive_positions()` (the right-hand-drive flip filling `p_front_passenger` /
  `p_rear_passenger`) has to run *before* the children, because that is when a seat context source
  reads those inputs. `prepare()` is a documented no-op hook at the top of `calculate()`. This is an
  addition beyond the plan's listed scope — small, but it is a deviation, and it is what lets Step 8
  delete `sync_positions()` without moving the derivation back into `__init__` (F15).

### What was added

**`pyisomme/report/ctx.py` (new).** `Ctx` — a frozen dataclass of `report`, `isomme` and an immutable
`fields` mapping — plus `at(**fields)`, `field(name)`, `code(template)`, `codes(*templates)`; the
`CtxSource` protocol; and `where(**fields)`, the literal-field source. `Ctx` is deliberately **not**
an occupant object: nothing in it mentions a position, a dummy or a side.

- `code("?{p}NECKUP00??MOY?")` → `"?1NECKUP00??MOY?"`. A template with no placeholder passes through
  untouched (the vehicle-level case). A placeholder with no field raises `MissingData` naming the
  field, i.e. a clean `Status.NA` — never an `AttributeError`, never a silent default.
- The result is length-checked as an fnmatch *pattern*, so `?` wildcards and `[…]` character classes
  survive and count as one character each. That check reuses `check_code_pattern`'s length logic,
  which moved to `pyisomme/code.py` as the public `pattern_length()` alongside a new `CODE_LENGTH`
  constant — one source of truth, no behaviour change (`check_code_pattern` now imports both).

**`pyisomme/report/occupant.py` (new).** `Seat`, `SeatSource` and `seat(which, *, field="p")` — the
occupant layer, explicitly *not* part of the framework. One shared module rather than a copy per
protocol package, because `euro_ncap`, `un`, `iihs` and `us_ncap` seat dummies identically today.
`seat(Seat.DRIVER)` resolves by walking up the tree for the **nearest ancestor declaring the manual
input `p_driver`** and reading it — so it is not a second source of truth, and Step 4's public API
(`report.overall(v1).p_driver = 3`, `get_inputs()`/`set_inputs()`) is untouched. No ancestor declares
it → `Status.NA` naming the input. An occupant whose position is fixed by the protocol rather than
chosen by the user (Far Side's `p=1`) uses `at=where(p=1)` and has no manual input at all.

**`pyisomme/report/criterion.py`.**

- `Role` (+ `SCORING_ROLES`) with the three consumers documented per value, and `Criterion.role`
  defaulting to `RESULT`. A class may declare its own role; `sub(..., role=…)` overrides it for one
  placement, and `sub(..., role=None)` (the default) leaves the class's declaration alone.
- `sub(cls, *, name=…, at=…, role=…)`, a `Generic[C]` descriptor with two `__get__` overloads.
  `__set_name__` records module-monotone declaration order; **a subclass overriding an inherited
  child keeps that child's place**, so refining one region does not reorder the tree.
- Eager construction in `Criterion.__init__` (G8): the whole tree exists and is mutable before
  `calculate()`, which is when manual inputs are set.
- `get_children()` no longer walks `dir()` (F6, A11, A12): framework-owned children first (declared,
  in declaration order; then `add_child`, in insertion order), then not-yet-migrated ones from
  `vars(self)` **in the order `__init__` assigned them**, then a `dir()`-of-the-class safety net that
  finds nothing in any report today. `get_subcriterion()`/`get_subcriteria()` are now three lines over
  `walk()`. Neither has any caller outside `criterion.py`.
- `add_child(name, criterion)` — the escape hatch for a data-dependent tree (correlation, F6/A12).
  Added children are calculated like declared ones.
- `ctx` property, resolved on demand and never cached: the root builds a bare `Ctx`, every other node
  inherits its parent's and applies its own `at=`. `Criterion.code(template)` is the short spelling.
  `parent`, `ancestors()`, `find_input_owner(name)`.
- `calculate()` is now `prepare()` → `apply_limits()` → children in protocol order → `calculation()`.
- `define_limits()` / `apply_limits()`: `apply_limits()` is a **no-op unless the class overrides
  `define_limits`**, which is what lets the 12 unmigrated reports keep building rows in `__init__`.
  When it does apply, it drops the criterion's previous rows from the report-level list before
  extending it, so recalculating cannot duplicate limit bars in the plots.
- Aggregation helpers, all NaN-propagating (G9): `children_by_role()`, `ratings_of_children()`,
  `min_of_children()`, `max_of_children()`, `sum_of_children()`, `mean_of_children()`,
  `modifiers_sum()`. They default to the scoring roles (`RESULT` + `AGGREGATE`) and exclude
  `MODIFIER`, which is what finally expresses the "min over results **plus** sum over modifiers" box.
  `mean_of_children(skip_missing="<reason>")` is the only NaN-tolerant one; when it actually drops a
  child it records the reason in `Criterion.skip_missing` for Step 13 to render. `sum` over no
  children is `0.0` (so `+= self.modifiers_sum()` is always safe); `min`/`max`/`mean` over none is
  `nan` with a warning, not a `ValueError`.

**`tests/test_criterion_tree.py` (new, 43 tests, no fixtures, ~0.04 s).** Declaration order (including
the three wiring styles in one node and subclass overrides); auto-calculation and the *absence* of
double-calculation for legacy children; `prepare()` before children before `calculation()`; a failing
child not stopping its siblings; NaN through every helper and the `skip_missing` exception; modifiers
in and out of the headline; lazy context, a position set after construction (F15), `where()` as the
second source, a missing field and a missing seat input both as `Status.NA`; **a vehicle-level tree
and a correlation-style tree with no occupant anywhere**, built, calculated and validated; and
`define_limits()` rebuilding from the resolved context without duplicating rows.

### Verified

| Command | Result |
|---|---|
| `-m unittest discover -s tests` | **294 tests** (251 + 43 new), 2 errors — both pre-existing and unrelated: `test_isomme.test_read` wants the untracked `data/nhtsa/11391.tar`, `test_plotting`'s `KeyError` is the maintainer's uncommitted test |
| `-m unittest tests.test_golden` | 17 OK — **no golden result moved** |
| `-m unittest tests.test_report_structure tests.test_validate tests.test_manual_inputs tests.test_report_modules` | 72 OK, 1 skipped |
| `PYISOMME_SLOW=1 … test_IIHS_Frontal_Small_Overlap`, `… test_UN_Frontal_50kmh_R137` | both OK (PPTX exported), run one at a time per D8/D9 |
| `-m ruff check .` | 10 findings, **all pre-existing** in `tests/` (W291/W293/E701/F401) — none in the new code |
| `-m mypy` | clean, 62 files |
| mypy on a scratch tree | `self.driver.head.hic15` → `HIC15`, `.rating` → `builtins.float`; `hic_15` → `has no attribute … maybe "hic15"?`; `hard_contct = False` → `variable has type "Undeclared"` |

### Snapshots

`tests/golden/describe/*.md` re-baselined (`-m tests.test_describe --regen`) — **639 insertions, 639
deletions, and both files are line-for-line identical as multisets**, i.e. pure reordering with no
definition change. That is the expected consequence of `walk()` following declaration order: the
50 kmh dump now reads Overall → Driver → Head → HIC 15 → a3ms → the four modifiers → Neck → My
extension → Fz tension → Fx shear → … instead of alphabetically, and Door Opening moved from first to
last. The golden JSONs and `report_structure.json` are keyed by path and dumped with `sort_keys=True`,
so they did not move — Step 1 planned for exactly this.

`print_results()` now emits protocol order too, as the acceptance criterion requires. No golden
captures it.

### Deviations and what is still open

- **`prepare()` is beyond the plan's listed scope** (see above). Reject it and `derive_positions()`
  has to move back into `__init__` or into the seat source, both worse.
- **`define_limits`, not `limits`** — the example file's name collides with `Criterion.limits`.
- `role` is not yet shown by `describe()` or checked by `validate()`. Deliberate: adding it would
  churn the describe goldens a second time in one step, and the `max_rating`-vs-non-modifier check is
  Step 12's wording, already implemented against `get_children()`. Worth a follow-up once Steps 8–9
  have actually classified nodes — today every criterion is `RESULT` by default, so the check would be
  vacuous.
- `sync_positions()` / `rebuild_child()` / the ~180 `__init__(self, report, isomme, p)` blocks / the
  ~250 explicit `child.calculate()` calls are all **still there**, by design: Step 7 migrates nothing.
  Step 8 (pilot: `frontal_50kmh`) deletes them.
- `docs/log/20260803_Step-7-handover.md` says to delete itself when Step 7 lands, and the example file
  when Step 7 or 8 lands. **Both left in place** — they are untracked, so deleting them is
  unrecoverable, and the example's section 3 is the Step 8 blueprint. Maintainer's call.

---

## 2026-08-04 — Step 8: `frontal_50kmh` migrated to the declarative tree (pilot)

The plan numbers Step 6 next, but with Step 7 already landed the maintainer chose **8 before 6**: a
`PeakCriterion` written today wants to be `Ctx`-native, and a `Ctx`-native leaf only resolves once its
*parents* are wired with `sub(..., at=seat(...))`. Doing 6 first would have needed a transition shim
inside the new base class and rewritten every migrated leaf again in Step 8. Step 6 now shrinks the leaf
*bodies* against a tree that already has context.

**Leaf `calculation()` bodies are deliberately unchanged** — this step is the wiring only.

### Attribute names kept

`criterion_driver.criterion_head.criterion_hic_15`, not `driver.head.hic15`. The plan's acceptance
criterion is "golden test passes **unchanged**", and the golden JSONs, `report_structure.json`,
`describe/*.md`, the manual-input paths (`get_inputs()`/`set_inputs()`) and all 30 page classes are
keyed by exactly these names. Renaming is cosmetic, would have re-baselined four snapshots at once and
would have hidden the one thing this step has to prove. It belongs with Step 10/11, which touch those
paths anyway.

### What changed in `pyisomme/report/euro_ncap/frontal_50kmh.py`

| | before | after |
|---|---|---|
| criterion section | 1163 lines | **946** (−19 %) |
| `def __init__(self, report, isomme, p: int)` | 43 | **1** (the shim below) |
| `self.p` references | 216 | **0** |
| explicit `child.calculate()` | 59 | **0** |
| `f"?{self.p}…"` code patterns | 134 | **0** (now `self.ctx.code("?{p}…")`) |

- **`Overall.sync_positions()` is gone**, and with it every `rebuild_child()` call in this report. The
  right-hand-drive derivation moved to `prepare()`, which runs before the occupants calculate — which is
  when their `seat()` context reads `p_driver`/`p_front_passenger`/`p_rear_passenger`. `__init__` calls
  `prepare()` too, because the pages build their channel patterns from `p_driver` at construction.
- Every limit block became a `define_limits()` returning the same hand-written rows, with
  `self.ctx.codes("?{p}…")` in place of the f-strings. Thresholds, flags, colours and row order are
  untouched.
- Roles declared throughout: `AGGREGATE` on `Overall`, the three occupants and the eight body regions;
  `MODIFIER` on the eleven modifier criteria; `RESULT` (the default) on the rated leaves. The
  aggregations became `sum_of_children()` / `min_of_children()` / `modifiers_sum()` wherever they were
  exactly that; the conditional ones (`Head`'s hard-contact branch, `Neck`'s airbag branch,
  `Overall`'s §4.3 90 % rule) keep their explicit logic, which is what `role` is documented **not** to
  restrict.

### Two structural moves the migration forced

1. **Eight shared leaves moved to module level** — `Criterion_HIC_15`, `Criterion_Head_a3ms`,
   `Criterion_UnstableAirbagContact`, `Criterion_Chest_Deflection`, `Criterion_Chest_VC`,
   `Criterion_ShoulderBeltLoad`, `Criterion_Femur_Axial_Force`, `Criterion_Submarining`. A `sub()` in a
   class body can only name what is already bound, and the front and rear occupants reuse the driver's
   leaves; no nested class can reach a sibling's. The old nested names are kept as **class-attribute
   aliases** so the unmigrated reports' `Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15`
   paths still resolve. Step 10's shared criteria library replaces both — the aliases carry a
   `TODO(step-10)`.
   *mypy rejects an alias in **type** position*, so the five sites that use one as a **base class**
   (`side_barrier` ×2, `side_farside` ×2, `frontal_mpdb` ×1) now import the module-level class directly
   — which is what CLAUDE.md already asks for. The constructor call sites still use the deep path and
   still work.
2. **`PositionedCriterion`, a transition shim.** The other reports construct this file's shared leaves
   with `p=` and have not been migrated. The shim accepts the position and turns it into
   `where(p=p)`, so one implementation serves both callers and the criterion body only ever reads
   `self.ctx`. Ten classes use it. `TODO(step-9)`: delete with the `p=` call sites.

### One framework amendment to Step 7

`define_limits()` alone would have left the limit rows **empty for every definition-layer consumer**:
`validate()`, `describe()` and `tests/test_report_structure.py` read a freshly *constructed* report and
never calculate, and `apply_limits()` only ran inside `calculate()`. That would have silently switched
off `validate()`'s limit checks for every migrated report.

Fixed with `Criterion.build_limits()` — one walk applying `apply_limits()` over a finished tree, called
once by `Report.__init__`. It cannot happen inside `Criterion.__init__`: construction is bottom-up, so a
node's `_parent` is only set by its parent *after* its own subtree exists, and until then it has no
context to resolve. `calculate()` still applies them per node, which is what re-resolves a changed
position.

### Verified

| Command | Result |
|---|---|
| `-m unittest discover -s tests` | **294 tests**, 2 errors — the same two pre-existing ones (`test_isomme.test_read` wants the untracked `data/nhtsa/11391.tar`; `test_plotting`'s `KeyError` is the maintainer's uncommitted test) |
| `-m unittest tests.test_golden` | 17 OK — **`euro_ncap_frontal_50kmh.json` matched unchanged**, no re-baseline. This is the pilot's whole point |
| `-m unittest tests.test_report_structure` | OK — the definition layer of all 13 reports is byte-identical: same paths, names, classes and `Limit` rows |
| `-m unittest tests.test_describe tests.test_validate` | OK — **no snapshot moved**, so no threshold and no `source` inheritance changed |
| `-m unittest tests.test_manual_inputs` | 37 OK after updating the position assertions (below) |
| `PYISOMME_SLOW=1 … test_UN_Frontal_50kmh_R137`, `… test_IIHS_Frontal_Small_Overlap` | OK, PPTX exported |
| `-m ruff check .` | 10 findings, all pre-existing in `tests/` |
| `-m mypy` | clean, 62 files |

Hands-on, on an empty test: 172 limit rows at construction; `p_driver = 3` + `calculate()` moves the
driver's HIC rows from `?1HICR0015??00RX` to `?3HICR0015??00RX`, flips the front passenger to `?1…`
via the right-hand-drive rule, and leaves the report-level list at 172 rows — no duplicates, no stale
rows, and nothing rebuilt.

**`tests/test_manual_inputs.py`** — six assertions read `criterion.p`, the attribute this step deletes.
Replaced with a `position(criterion)` helper reading `criterion.ctx.field("p")`, which is the same fact
observed where it now lives. `test_mpdb_syncs_too` still asserts on `.p`: MPDB is unmigrated and still
rebuilds. The `TestPositionSyncF15` method names still say "rebuild"; the class docstring now records
that the behaviour is unchanged but the mechanism is gone for the migrated report.

### Verdict on the style (the plan asks for one)

**Worth rolling out.** −19 % on the criterion section is the smallest part of it: the four-places-to-wire-
a-child problem (F1) is structurally gone, 134 hand-built code patterns became 134 templates resolved in
one place, and the report no longer contains any machinery for "a position changed" — that is now one
line of context inheritance. The two costs are real but bounded: the shared leaves had to move to module
level (Step 10 was going to do that anyway) and the unmigrated reports need the `p=` shim until Step 9.

### Still open

- `role` is declared but not yet read by `describe()`/`validate()` — carried over from Step 7's entry;
  now that one report has real roles, the `max_rating`-vs-non-modifier check has something to check.
- The back-references (`self.report.criterion_overall[…].criterion_driver.steering_wheel_airbag_exists`)
  are **unchanged** on purpose: rewriting them to `self.parent…` is Step 9/10 and needs Q5 answered.
- `docs/log/20260803_Step-7-example.py` is now spent — its section 3 was the blueprint for this step.
  Left in place (untracked, so deleting is unrecoverable); maintainer's call.

---

## 2026-08-04 — Step 6 withdrawn; Step 9 part 1: the whole `euro_ncap` family migrated

### Step 6 (`PeakCriterion`) — withdrawn before any code was written

Written up in the plan's §Step 6, which now opens with the decision and keeps the original scope in a
collapsed block. The maintainer's reason, and the correction that settles it:

**F4 is not redundancy.** The step's premise was that a leaf declares its channel pattern twice and
that one declaration should feed both. It should not — the two mean different things. `calculation()`
requests a **concrete filter class** (`?{p}NECKUP00??MOYB`) because it rates one specific filtered
signal; `define_limits()` uses a **filter-class wildcard** (`?{p}NECKUP00??MOY?`) so the limit bars
apply to every filter class the plots may draw. Collapsing them would either narrow the limits to one
filter class or widen the lookup to any.

Two supporting facts, recorded so this is not relitigated: the drift the step guarded against already
fails **loudly** (`Limits.get_limit_ratings` raises `No limits found for channel …` → `Status.ERROR` →
`tests/test_golden.py` scores `OK → ERROR` as a regression), and nothing downstream depends on it —
Step 8 landed the pilot at 946 lines without it. `Reduce.MAX_ABS` (18 hand-copied sites across 8
modules) is flagged as the one salvageable piece, to be extracted as a plain helper function if ever
wanted, carrying none of the rest of P4.

### Step 9 part 1 — `euro_ncap/` is done

| module | lines | `__init__(…, p)` | `child.calculate()` | `self.p` |
|---|---|---|---|---|
| `frontal_mpdb` | 1619 → 1416 | 42 → 0 | 69 → 2 (MetaReport, not criteria) | 196 → 0 |
| `side_pole` | 582 → 523 | 12 → 0 | 16 → 0 | 89 → 0 |
| `side_barrier` | 275 → 242 | 5 → 0 | 14 → 0 | 27 → 0 |
| `side_farside` | 592 → 542 | 16 → 0 | 20 → 0 | 86 → 0 |

**The order was forced:** pole → barrier → farside, because each subclasses the previous one's
criteria; migrating one alone leaves the next constructing a `p=` that no longer exists.

- **Nine classes lifted to module level in `frontal_mpdb`** (`Criterion_UnstableAirbagContact`,
  the two airbag-deployment modifiers, `Criterion_Femur_Compression`,
  `Criterion_Knee_Slider_Compression`, `Criterion_VariableContact`, `Criterion_ConcentratedLoading`,
  `Criterion_Tibia_Index`, `Criterion_Tibia_Compression`). The passenger tree reached them through
  `Overall.Criterion_Driver.…`, and inside `Overall`'s own body the name `Overall` does not exist yet.
  No aliases needed — nothing outside the module used those paths. `TODO(step-10)`.
- **Reused base classes are imported under `…_F50` aliases** in `side_barrier`, `side_farside` and
  `frontal_mpdb`. The previous `class X(X)` self-shadowing worked at runtime but mypy rejects it
  (`Cannot resolve name … (possible cyclic definition)`).
- **`from_input(name, *, field="p")` added to `ctx.py`.** The general form of a user-chosen context;
  `occupant.seat()` is it with the seat's input name filled in. The side reports' occupant is "the
  struck-side occupant" with an input literally named `p` — labelling that `Seat.DRIVER` would have
  been untrue.
- **The far-side `TODO(input)` is resolved.** `EuroNCAP_Side_FarSide`'s occupant was pinned with
  `p: int = 1`; it is now `Manual[int, manual(1, …)]`, taken from the `Driver position object 1` test
  info in `prepare()`, with `_ctx_source = from_input("p")` on the root so the whole tree inherits it.
  Since Step 8 that *was* the whole change — nothing bakes the position in any more. Behaviour-neutral
  on the fixtures (`14084` reports position 1); ratings verified identical before and after.
- **Roles declared** across all four modules: `AGGREGATE` on the occupants and body regions,
  `MODIFIER` on every criterion the protocol names "Modifier …", `RESULT` (the default) on the leaves.
  The aggregations themselves were **left as explicit `np.min`/`np.sum` lists**: MPDB's driver is `nan`
  in every fixture, so the golden test could not catch a mis-classification there, and a wrong role in
  a helper call changes a score silently. Converting them is a separate, reviewable change.

### `validate()` earned its keep

It flagged `side_barrier`'s `p` as *declared but never read* — correct: after the migration the input
is read by the **framework**, through the context source in a `sub(...)` declaration, not by any line
of the report. `check_unused_input` now also counts a name appearing in `from_input("…")` or
`input_name="…"` (`_CTX_SOURCE_INPUT`). The check firing on a real gap the migration introduced is
exactly what it is for.

### How the migration was done

`docs/log/20260804_Step-9-handover.md` carries the recipe. In short: a line-based transform script
handles the uniform parts (delete the `__init__`, emit `sub()` at the end of the class body, turn
`extend_limit_list([...])` into `define_limits()` with the shared pattern list hoisted to `codes = …`,
drop the explicit `child.calculate()` calls, rewrite `f"?{self.p}…"` to `self.ctx.code("?{p}…")`), and
prints every statement it did not understand. Everything else — `Overall.__init__`/`prepare()`, the
`at=` sources, roles, module-level lifting — is done by hand.

**The one hazard worth repeating:** `self.p` means the *threaded position* on a child but the
*manual input* on `Overall` in the side reports. Every `Overall` was hand-written for that reason.

### Verified

| Command | Result |
|---|---|
| `-m unittest tests.test_golden` | 17 OK — `frontal_50kmh`, `frontal_mpdb` and `side_barrier` results **unchanged**, no re-baseline |
| `-m unittest tests.test_report_structure` | OK — the definition layer of all 13 reports is byte-identical after every module |
| `-m unittest tests.test_describe tests.test_validate` | OK — **no snapshot moved** |
| `-m unittest tests.test_manual_inputs` | 37 OK (`test_mpdb_syncs_too` now reads the context, like the rest) |
| `-m ruff check .` | 10 findings, all pre-existing in `tests/` |
| `-m mypy` | clean, 62 files |

### Still to do in Step 9

`side_farside_vtc` (5 `__init__(…, p)`, and criteria constructed from `Channel` arguments — the
non-standard one), the four `un/` reports (39 blocks between them), `iihs/frontal_small_overlap` (21),
the `us_ncap` stub (2) and `correlation` (already free of `p`, but its dynamic list wants
`add_child`). Then `PositionedCriterion`, `sync_positions` and `rebuild_child` can go.

**None of those six has golden *results* coverage** — the net is the definition layer plus
construct-and-calculate smoke runs, which is what the plan anticipated. Worth knowing before changing
any aggregation in them.

---

## 2026-08-04 — Step 9 part 2: the last eight reports migrated; the transition machinery deleted

Step 9 is **complete**. All 13 reports are on `sub()` + `Ctx`; nothing threads a position through a
constructor any more.

| module | lines | `__init__(…, p)` | `child.calculate()` | `self.p` |
|---|---|---|---|---|
| `us_ncap/frontal_56kmh` | 126 → 118 | 2 → 0 | 6 → 0 | 8 → 0 |
| `correlation/correlation` | 104 → 124 | 0 → 0 | 1 → 0 | 0 → 0 |
| `un/side_pole_r135` | 304 → 278 | 7 → 0 | 7 → 0 | 48 → 0 |
| `un/frontal_50kmh_r137` | 531 → 467 | 14 → 0 | 18 → 0 | 79 → 0 |
| `un/frontal_56kmh_odb_r94` | 603 → 530 | 14 → 0 | 24 → 0 | 76 → 0 |
| `un/side_barrier_r95` | 249 → 235 | 4 → 0 | 6 → 0 | 31 → 0 |
| `euro_ncap/side_farside_vtc` | 491 → 459 | 5 → 0 | 25 → 0 | 69 → 0 |
| `iihs/frontal_small_overlap` | 695 → 596 | 21 → 0 | 21 → 0 | 118 → 0 |

Repo-wide: **`def __init__(self, report, isomme, p)` is 0** (was 180 at the start of the refactor),
`self.p` in `pyisomme/report/` is 0 (one mention left, in a comment in `check_unused_input.py`), and
the only `self.<child>.calculate()` lines left are two that were already commented out in
`frontal_mpdb`.

### The order was forced again

`un/side_pole_r135` → `un/frontal_50kmh_r137` → `un/frontal_56kmh_odb_r94` → `un/side_barrier_r95`:
R95 subclasses criteria from both R137 and R135, and R94 subclasses five of R137's. Migrating a base
before its subclass leaves the subclass constructing a `p=` that no longer exists.

### Four classes lifted to module level in `un/frontal_50kmh_r137`

`Criterion_HPC36`, `Criterion_Head_a3ms`, `Criterion_Neck_My_extension`, `Criterion_Chest_VC` — the
ones `Criterion_Passenger` reuses from the driver, which a `sub()` inside `Overall`'s body cannot
name. **No aliases**: their only outside users (R94 twice each, R95 once) use them as *base classes*,
and mypy rejects a class-attribute alias in type position, so those modules import them directly
under `…_R137` aliases. `Criterion_Chest_Deflection` stays nested — R94 reaches it through the real
path `Overall.Criterion_Driver.Criterion_Chest_Deflection`, which mypy resolves. `TODO(step-10)`.

### The three `TODO(input)` positions are resolved

`un/side_pole_r135`, `un/side_barrier_r95` and `euro_ncap/side_farside_vtc` each pinned their occupant
with a plain `p: int = 1` overwritten from the `Driver position object 1` test info in `__init__`.
Each is now `p: Manual[int, manual(1, …)]` filled by `prepare()` with `set_derived_input`, and the
occupant is wired `at=from_input("p")` — the same shape Step 9 part 1 gave the Euro-NCAP far-side
report. Behaviour-neutral on the fixtures (verified below); the position is now settable after
construction, which it was not before.

### `correlation` is the one that is not mechanical (A12)

Its tree is one criterion per channel of the reference test, so its *shape* is the data's and it
cannot be declared. It now uses `Criterion.add_child()` — which is what that escape hatch exists for
— instead of a private `self.criteria` list the framework could not see. Four consequences:

- **The per-channel criteria are real children now**: they appear in `walk()`, `print_results()` and
  `describe()`, and the framework calculates them. Before, they were invisible to all of it.
- `Overall.criteria` is now a **property** over the children of that type, so
  `Page_Correlation_Overall_Rating_Table` is unchanged and still gets the same 77 criteria per test.
- **The "is this the reference test?" guard moved into the leaf.** It used to sit in
  `Overall.calculation()`, which skipped the whole child loop; with the framework owning the
  children it has to live where the work is, or the reference test would correlate against itself
  (77 ISO-18571 runs producing ~1.0). Same values, same colours; the only delta is that the
  reference test's leaves now end `Status.OK` with `value = nan` instead of staying `PENDING`.
- Child names are the reference channel's code, disambiguated with a trailing apostrophe on
  collision: `Isomme.channels` is a list, not a mapping, and `.set(filter_class="D")` collapses the
  filter classes, so two entries can want the same name and the old list kept both.

### `euro_ncap/side_farside_vtc`: siblings as constructor arguments

Its five resultant criteria were built as `Criterion_Head_COG_Angular_Velocity(report, isomme,
self.head_avx, self.head_avy, self.head_avz)` — a child handed references to its siblings, which
`sub()` cannot express. Replaced with a declared `components: tuple[str, ...]` of **attribute names**
resolved against `self.parent` in a property. Declaration order is calculation order, so each
resultant is declared after its three axes and reads them already calculated.

### `us_ncap/frontal_56kmh` (the stub)

Migrated as far as it can be: the driver and its four body regions are `sub()`s. `Criterion_Passenger`
is still referenced but never defined — one of the two reasons the report raises `NotImplementedError`
— so the reference moved from a dead `__init__` line into `Overall.calculation()`, with the `sub()`
spelling it wants written beside it in a comment.

### Transition machinery deleted

- **`PositionedCriterion`** (`frontal_50kmh`) — 12 classes rebased on `Criterion`; there is no `p=`
  call site left in the repo.
- **`Criterion.rebuild_child`** and **`Overall.sync_positions`/`sync_position`** — gone everywhere.
- **`Criterion.p: int`** — the class-level annotation for the threaded position. Not on the
  handover's list, but it is the same mechanism: leaving it declared kept `criterion.p = 3` settable
  on *every* criterion, which is exactly the F13 hole `__setattr__` closes. The reports that still
  have a `p` declare it themselves as a manual input. **Flagged as a deviation** — revert this one
  line if the maintainer wants the guard left as it was.
- `CLAUDE.md`'s "not-yet-migrated"/"unmigrated" wording and its description of the rebuild mechanism.
- `tests/test_manual_inputs.py::TestPositionSyncF15`'s class docstring. The method names still say
  "rebuild"; kept deliberately — they are the step-4 regression tests and the names are what a
  failure gets looked up by. The docstring now says to read them as "a position change that used to
  need a rebuild".

### Roles declared, aggregations left alone

`AGGREGATE` on every `Overall`, occupant and body region; `RESULT` (the default) on the leaves. The
`np.min`/`np.max`/`np.sum` lists were **not** converted to the helpers, for the reason recorded in
part 1: none of these eight reports has golden *results* coverage, so a mis-classified role would
change a score with nothing to catch it. Converting them is a separate, reviewable change.

### Verified

Every module was checked the same way, after each one: a **smoke harness** builds the report from the
same fixtures `tests/test_report.py` uses, runs `validate(errors_only=True)`, `calculate()`, and dumps
`golden_utils.serialise(report)` (definition + per-test `value`/`rating`/`color`/`status`) to JSON.
Baselines were captured from `HEAD` before any edit and diffed after.

| report | smoke diff |
|---|---|
| `un_side_pole_r135`, `un_side_barrier_r95` | **byte-identical** |
| `un_frontal_50kmh_r137`, `un_frontal_56kmh_odb_r94` | **byte-identical** |
| `euro_ncap_side_farside_vtc` (empty Isommes — the fixture is lost) | **byte-identical** |
| `iihs_frontal_small_overlap` | **byte-identical** |
| `correlation` | `Overall` value/rating/status identical for all three tests; the tree grew from 1 criterion to 78 (the per-channel children are now visible), and `criteria` is still 77 per test |

| Command | Result |
|---|---|
| `-m unittest discover -s tests` | **294 tests**, 2 errors — the same two pre-existing ones (`test_isomme.test_read` wants the untracked `data/nhtsa/11391.tar`; `test_plotting`'s `KeyError` is the maintainer's uncommitted duck-typed test, unrelated to the tree) |
| `-m unittest tests.test_golden` | 17 OK — **no re-baseline**, the three covered Euro-NCAP reports are unchanged |
| `-m unittest tests.test_report_structure` | OK — the definition layer of all 13 reports is byte-identical after every module |
| `-m unittest tests.test_describe tests.test_validate` | OK — **no snapshot moved** |
| `-m unittest tests.test_manual_inputs tests.test_criterion_tree tests.test_report_modules` | OK |
| `PYISOMME_SLOW=1 … test_IIHS_Frontal_Small_Overlap`, `… test_UN_Frontal_50kmh_R137`, `… test_UN_Frontal_56kmh_ODB_R94`, `… test_EuroNCAP_Frontal_MPDB` | OK individually, PPTX exported |
| `-m ruff check .` | 10 findings, all pre-existing in `tests/` |
| `-m mypy` | clean, 62 files |

**No snapshot was regenerated in this session.**

### Still open

- The eight class-attribute aliases in `frontal_50kmh` (`Criterion_HIC_15 = Criterion_HIC_15`, …)
  carry a `TODO(step-10)` and are untouched. Three of them (`Criterion_HIC_15`,
  `Criterion_Head_a3ms`, `Criterion_UnstableAirbagContact`) now appear to have no user at all —
  worth deleting with the shared criteria library rather than piecemeal.
- `role` is still declared but not read by `describe()`/`validate()` — carried over from Steps 7/8.
  All 13 reports now carry real roles, so the `max_rating`-vs-non-modifier check has full input.
- The aggregation helpers (`min_of_children`, `sum_of_children`, …) are used only in
  `frontal_50kmh`; the other twelve keep explicit lists. See "Roles declared" above.
- The back-references (`self.report.criterion_overall[…].criterion_driver.…`) are unchanged; still
  Step 10/11 and still needs Q5 answered.
- `docs/log/20260804_Step-9-handover.md` and `docs/log/step-9/migrate.py` are spent. The handover says
  to delete the former when Step 9 lands; both are untracked, so deleting is unrecoverable —
  maintainer's call.

---

## 2026-08-04 — `pyisomme/plotting.py` → `pyisomme/plotting/` package

Not a numbered refactor step: a maintainer-requested split of the plotting module, logged here because
it is the running record for this repo. **Pure move — no plotting logic changed.**

### What changed

| file | change |
|---|---|
| `pyisomme/plotting.py` | **deleted** (unstaged deletion, left in the working tree) |
| `pyisomme/plotting/__init__.py` | new — re-exports `Plot`, `Plot_Line`, `Plot_Table`, `Plot_Line_Table` with an explicit `__all__`, mirroring `report/page/__init__.py` |
| `pyisomme/plotting/plot.py` | new — base `Plot` (colors, linestyles, `figsize`/`nrows`/`ncols`, `show()`) |
| `pyisomme/plotting/plot_line.py` | new — `Plot_Line` and its limit line/fill/text helpers |
| `pyisomme/plotting/plot_table.py` | new — `Plot_Table` |
| `pyisomme/plotting/plot_line_table.py` | new — `Plot_Line_Table` (inherits `Plot_Line`, `Plot_Table`; MRO verified unchanged) |
| `pyproject.toml` | added `"pyisomme.plotting.*"` next to `"pyisomme.plotting"` in the mypy `follow_imports = "silent"` override — the old entry no longer covers the submodules |
| `CLAUDE.md` | Plotting section now points at the package and records the matplotlib typing workarounds |

**No import site needed fixing.** All four consumers (`report/page/criterion_table.py`,
`report/page/line_table.py`, `report/page/plot_nxn.py`, `__main__.py` via the top-level star-export)
import from `pyisomme.plotting`, which still resolves through the package `__init__`.
`setuptools.packages.find` already globs `pyisomme*`, so packaging needed no change.

### Type-checker fixes (maintainer request)

Pylance runs in **basic** mode (`.vscode/settings.json`) and matplotlib 3.7.5 ships no stubs, so
`plt.subplots()` infers as `FigureBase | Unknown`. Pyright reported 4 errors in the new package — all
pre-existing, all present in `HEAD:pyisomme/plotting.py` (verified by checking the extracted original).

- 3× `reportReturnType` on `return fig` → fixed at the source with `fig = cast(Figure, fig)` in each
  `plot()`, matching the `cast("list[Axes]", axs)` idiom two lines below. No runtime cost.
- 1× `reportAttributeAccessIssue` on `fig.patch` in `Plot_Line_Table.plot` → the `getattr(fig, "patch",
  None)` guard the maintainer already used in `Plot_Table` was mirrored. The cast alone does **not**
  fix this: Pylance cannot resolve `patch` on `Figure` either, so the guard has to stay in both.

Pyright over `pyisomme/plotting/`: **0 errors** (was 4). `mypy` run directly on the package still shows
3 pre-existing `redundant-cast` findings on the inherited `cast("list[Axes]", axs)` lines — outside the
repo mypy scope (`files = ["pyisomme/report"]`) and left alone, since dropping the cast would
re-break Pylance.

### Verified

| Command | Result |
|---|---|
| `-m pyright pyisomme/plotting/` | **0 errors**, 5 files (4 before the fix) |
| `-m mypy` (repo config) | clean, 62 files |
| `-m ruff check pyisomme/plotting/` | All checks passed |
| `-m ruff check .` | 10 findings, all pre-existing in `tests/`, none in touched files |
| 18 fast test modules (all but `test_report`/`test_golden`) | **265 tests, 2 errors** — the same two pre-existing ones (`test_isomme.test_read` wants the untracked `data/nhtsa/11391.tar`; `test_plotting`'s `KeyError` is the maintainer's uncommitted duck-typed test) |
| render smoke test | `Plot_Line`, `Plot_Table`, `Plot_Line_Table` each return a real `Figure`; `patch.get_visible()` is `False` on both table figures, so the `getattr` guard still fires at runtime |

`pyright` was pip-installed into `.venv` to get ground truth instead of guessing at Pylance's
diagnostics, then **uninstalled** — the venv is as it was found.

### Still open

- `tests/test_report.py` and `tests/test_golden.py` were **not** run (~6 min; the maintainer declined
  the full-suite run). The plotting classes are exercised by the report pages, so a report test is the
  remaining coverage gap for this change.
- The 3 `redundant-cast` mypy findings above, if the plotting package is ever pulled into the mypy
  `files` scope.

## 2026-08-05 — Out-of-band: all-report golden-test cleanup

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting review
**Outcome:** done with one pre-existing report defect made explicit
**Review:** ☐ pending

### What was implemented

- Added `tests/report_registry.py` as the single registry for all 13 concrete report trees. Its
  deterministic synthetic builder derives channels from each tree's `Limit.code_patterns` and seeds
  the two data-shaped cases (Correlation and Far-Side VTC) explicitly. Result tests no longer depend
  on untracked `data/` fixtures.
- Expanded calculated-result goldens from three Euro-NCAP reports to all 13 concrete reports plus the
  available `EuroNCAP` MetaReport. Each report runs in a fresh child process (`tests/golden_case.py`),
  avoiding D8/D9's Windows stack overflow. The JSON stores full-precision
  `value`/`rating`/`color`/`status` and exact `print_results()` lines.
- Kept definition and result snapshots separate. `tests/test_describe.py` now owns exact Markdown
  definitions for all 13 trees (pages, paths/classes, sources, aggregation, manual inputs and every
  `Limit` row). Removed the duplicating `tests/test_report_structure.py` and
  `tests/golden/report_structure.json`; its report-module coverage guard moved to `test_describe`.
- `tests/test_golden.py` now rejects every synthetic-data `Status.NA` and every unexpected
  `Status.ERROR`, so a re-baseline cannot normalize incomplete data or a swallowed exception. The
  one known error is listed explicitly below.
- Replaced the old always-exporting real-fixture `tests/test_report.py` with opt-in, process-isolated
  PPTX smoke coverage. Default test runs export nothing. `PYISOMME_PPTX=1` requests every report;
  `PYISOMME_PPTX=<comma-separated stems>` requests a subset. Each generated deck is reopened and its
  slide count checked against the report page count (`tests/report_pptx_case.py`).
- Updated `golden_regen`, `test_validate`, `test_manual_inputs`, CI's fixture-free command and
  `CLAUDE.md` to use the shared registry and the new snapshot/PPTX commands.

### Decisions taken

- **Do not combine describe Markdown with result JSON.** Markdown is the fixture-free,
  engineer-reviewable definition contract; JSON is the machine-comparable calculation contract.
  Their former shared definition layer was removed instead of preserving two copies.
- **Do capture `print_results()`, but not as the calculation oracle.** Its rounded text is an exact
  rendering/order contract. Full-precision JSON remains what detects calculation changes.
- The unfinished US-NCAP stub stays excluded with a reason. `IIHS_Frontal_ODB` is included honestly
  as its current one-node placeholder. Intentional aggregate `nan`s and unfinished calculation bodies
  remain visible in the result snapshots; no `nan*` repair was introduced.

### Behaviour changes

- No production report behaviour changed.
- The three pre-existing result JSON files were deliberately re-baselined from local real fixtures to
  deterministic complete synthetic inputs, and their duplicated definition sections were removed.
  Eleven concrete/MetaReport result JSON files and eleven definition Markdown files were added.
- `print_results()` protocol ordering and formatting are now regression-tested for every report.
- PPTX files are no longer generated by default.

### Verification

| Command | Result |
|---|---|
| `-m tests.test_describe --regen` | 13 definition Markdown files generated (15–830 lines each) |
| `-m tests.golden_regen` (+ `euro_ncap` after adding MetaReport) | 14 result JSON files generated; all synthetic fixtures contain zero `NA` nodes |
| `-m unittest tests.test_golden` | **16 tests OK**, twice after the final baselines (104.3 s for the final isolated pass) |
| `-m unittest tests.test_describe tests.test_validate tests.test_golden tests.test_report` | **48 tests OK, 1 skipped** before MetaReport was added; the later all-golden and CI runs cover the final state |
| `-m unittest tests.test_report_modules tests.test_describe tests.test_validate tests.test_manual_inputs` | **73 tests OK** (42.0 s) |
| `PYISOMME_PPTX=iihs_frontal_odb ... -m unittest tests.test_report` | **1 test OK**; deck reopened and slide count matched (run both before and after the generic selector change) |
| `-m unittest discover -s tests` | unittest completed **282 tests in 235.2 s: 280 pass, 1 skip, 1 pre-existing error** (`data/nhtsa/11391.tar` absent); the outer 240 s command timed out just after the summary |
| `-m mypy` | clean, 61 source files |
| targeted `ruff` over every touched Python file | all checks passed |
| `-m ruff check .` | one unrelated existing `W292` in `noxfile.py`; no finding in this change |
| `git diff --check` | clean (line-ending conversion warnings only) |

### Deviation / still open

- D16: the otherwise complete Far-Side fixture exposes
  `criterion_pelvis_lumbar_modifier/criterion_lumbar_mx` as the sole `ERROR`: the implementation reads
  an `MOX` moment (`N m`) and calls `convert_unit("kN")`. It is explicitly allowlisted in the direct
  Far-Side golden and the EuroNCAP MetaReport golden. This session did not change report logic or hide
  the defect with a false channel unit.
- The opt-in smoke checks deck readability and slide count, not pixel/layout equivalence. No expensive
  PPTX export runs in the default suite.

## 2026-08-05 — Out-of-band: restore 11391 tar fixtures

Created `data/nhtsa/11391.tar` and `data/nhtsa/11391.tar.gz` from the existing
`data/nhtsa/11391/` folder. Archive members start at `11391.mme`, `Channel/` and `NHTSA/` (no leading
`./`), which is required by `Isomme._read_from_source()` when it resolves `Channel/11391.chn` relative
to the MME member.

Verified both public read paths with `Isomme().read(path, "11HEAD??????ACX?")`: each returns test
number `11391` and the two matching head-X channels. Then ran
`.venv/Scripts/python.exe -m unittest tests.test_isomme.TestIsomme.test_read` → **OK** (1 test).
Final sizes: `11391.tar` 39,189,504 bytes; `11391.tar.gz` 15,266,468 bytes.

## 2026-08-05 — Out-of-band: re-baseline Far-Side lumbar Mx fix

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting review
**Outcome:** affected result goldens regenerated; obsolete error allowances removed
**Review:** ☐ pending

### What changed

- Regenerated `tests/golden/euro_ncap_side_farside.json` and `tests/golden/euro_ncap.json` after the
  maintainer corrected the lumbar Mx channel conversion in `side_farside.py` from `kN` to `N m`.
- Removed the direct Far-Side and EuroNCAP MetaReport entries from `tests/test_golden.py`'s temporary
  expected-error allowance. The coverage assertion now requires zero calculation errors across every
  result golden.
- No describe/definition snapshot was regenerated: the criterion tree, manual inputs, pages and
  `Limit` rows did not change.

### Behaviour changes captured

- `criterion_pelvis_lumbar_modifier/criterion_lumbar_mx`: `value nan`, `rating nan`, no colour,
  `Status.ERROR` → `-79.99889603229252 N m`, rating `0`, green, `Status.OK`.
- The pelvis/lumbar modifier now aggregates to `-4` instead of `nan`.
- With the complete synthetic fixture, the Far-Side overall rating and the EuroNCAP Far-Side/total
  ratings now propagate to `-inf` instead of `nan`; this follows the existing NaN/Inf propagation and
  reflects the already `-inf` synthetic head/chest result plus the now-known modifier.

### Verification

| Command | Result |
|---|---|
| `-m tests.golden_regen euro_ncap_side_farside euro_ncap` | regenerated 2 snapshots (1 and 8 test trees; 23 and 330 printed lines) |
| `-m unittest tests.test_golden` | **16 tests OK** in 53.625 s |
| `-m ruff check pyisomme/report/euro_ncap/side_farside.py tests/test_golden.py` | all checks passed |
| `-m mypy` | clean, 61 source files |
| `git diff --check` | clean; line-ending conversion warning for `tests/test_golden.py` only |

### Deviation / still open

- None for this re-baseline. The maintainer's staged report fix was left unchanged and no commit was
  created.

## 2026-08-07 — Out-of-band: complete IIHS crashworthiness reports from rating guidelines

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** small overlap rewritten; Moderate 2.0 and Side 2.0 added; IIHS scoring uses literal signed demerits
**Review:** ☐ pending

### What changed

- Read the four local IIHS guideline PDFs for Small Overlap VII, Moderate Overlap 2.0 II/III and
  Side Impact 2.0 IV. Rebuilt the reports around eager `Overall` trees, `sub()`/`Ctx`, typed manual
  inputs and explicit page criterion lists in the same organization as the Euro NCAP frontal reports.
- Added `pyisomme/report/iihs/frontal.py` for the genuinely shared H350M injury measurements. Every
  `Limit_*` row contains its protocol's literal signed demerit; body regions take the minimum child
  rating and occupant/report totals sum the signed deductions. No one-use demerit tuple remains.
- Reworked `frontal_small_overlap.py`; added `frontal_moderate_overlap.py` and `side_impact.py` with
  their distinct component weights, overall cutoffs, structure/restraint/head-protection manual
  decisions, Moderate rear-occupant Chest Index, Side five-rib/VC/pelvis calculations, and explicit
  rating/chart/table page lists. KTH rows remain in values tables but not one-dimensional charts.
- Reduced `iihs/common.py` to manual-demerit validation only. `iihs/limits.py` owns the four IIHS
  `Limit` display classes and no longer exposes GOOD/ACCEPTABLE/MARGINAL/POOR numeric constants.
  Removed the category/set-category path; measurable criteria use `get_limit_min_rating()` and
  `get_limit_min_color()` directly. The stepped `interpolate=False` flag convention is documented via
  per-criterion `validate_ignore` reasons.
- Removed the proposed `Criterion.require_channels()` API. Every multi-sensor criterion now calls
  `require_channel()` once per required code, so one absent rib/leg/pelvis sensor produces `Status.NA`
  instead of being silently omitted by `get_channels()`.
- Hardened `calculate_femur_impulse()` around absent pre/post-peak crossings and included the closing
  sample in the trapezoid. Registered `KTHC` in `channel_codes.xml`, eliminating invalid-code warnings.
- Registered the three concrete IIHS reports and replaced the unfinished ODB placeholder coverage.
  Added deterministic synthetic fixture inputs, focused IIHS regression tests, result JSON snapshots,
  describe Markdown and validation baselines.

### Behaviour changes captured

- IIHS ratings now retain the repository convention `0, -demerits` (higher is better), while aggregate
  `value` fields expose the positive total demerits used by the PDF overall cutoffs.
- Positive and negative VC/shear excursions are rated through absolute or polarity-specific derived
  channels, fixing cases where the old symmetric flat limit list returned a correct colour but rating 0.
- Two-dimensional KTH force/impulse corridors are evaluated together rather than pretending either
  force or impulse is a sufficient one-dimensional limit.
- Moderate H35F contact-only HIC/Nij remain explicit table rows but are omitted from the chart when the
  default no-contact input makes them inapplicable, avoiding all-NaN plot warnings.

### Verification

| Command | Result |
|---|---|
| `-m tests.golden_regen iihs_frontal_small_overlap iihs_frontal_moderate_overlap iihs_side_impact` | 3 result snapshots regenerated; 26/38/25 printed lines |
| `-m tests.test_validate --regen` | 14-report baseline regenerated; all 3 IIHS reports have zero findings |
| `-m tests.test_describe --regen` | 14 definition documents regenerated; IIHS files are 317/469/326 lines |
| targeted report/calculation suite (`test_iihs`, all goldens, modules, validate, describe, femur impulse, code) | **64 tests OK** in 70.377 s |
| `-m ruff check .` | all checks passed |
| `-m mypy` | clean, 64 source files |
| `git diff --check` | clean; line-ending conversion warnings only |
| synthetic `calculate()` + `export_pptx()` for all 3 IIHS reports | 5/8/8-slide decks rendered successfully; temporary decks then removed |

### Deviation / still open

- Video, intrusion, postcrash and pressure-mat judgments remain typed manual inputs; the guideline data
  is not present in ISO-MME channels and was not guessed.
- KTH is intentionally absent from values charts because its force/impulse corridor has no honest
  one-dimensional plot limit; both left/right results remain in the explicit values tables.
- The repository already contained unrelated staged/unstaged edits (including Euro NCAP, `ctx.py`,
  `limit.py`, handover notes and the head-trajectory subproject). They were preserved and no commit was
  created.

## 2026-08-07 — Follow-up: IIHS page expansion and simplification

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** detailed IIHS signal pages added; manual-demerit validation and KTHC XML registration removed
**Review:** ☐ pending

This entry supersedes two details in the preceding IIHS entry: `KTHC` is deliberately **not** registered
in `channel_codes.xml`, and the final reports contain 15/23/20 slides rather than 5/8/8.

### What changed

- Deleted `pyisomme/report/iihs/common.py` and removed `validate_demerits()` entirely. Manual qualitative
  and numeric demerit inputs are now consumed directly; the reports assume their callers provide valid
  values.
- Kept `KTHC` out of `channel_codes.xml` because it is not an ISO-defined main location. The invalid-code
  logging warning during the two-dimensional KTH calculation is accepted and intentional.
- Added explicit `Page_Plot_nxn` classes and explicit page lists, following the Euro NCAP frontal report
  organization. Small overlap now has 10 detailed signal pages; Moderate adds the same 10 driver pages
  plus 5 rear-passenger pages; Side adds 6 driver and 6 rear-passenger pages. Related multi-sensor rib
  measures share thorax/abdomen panels; manual-only decisions and the two-dimensional KTH result remain
  table-only, while the underlying left/right femur force histories are plotted.
- Expanded the deterministic IIHS synthetic fixture with raw head axes, chest resultant and Nij channels
  needed by the new pages. These additions are scoped to IIHS reports so unrelated report goldens remain
  unchanged.
- Regenerated the three IIHS result snapshots and the validate/describe baselines after the deliberate
  report-definition and page-list changes.

### Verification

| Command | Result |
|---|---|
| `-m unittest tests.test_iihs tests.test_golden tests.test_report_modules tests.test_validate tests.test_describe tests.test_calculate.TestCalculate.test_calculate_femur_impulse tests.test_code` | **64 tests OK** in 81.963 s |
| `-m ruff check .` | all checks passed |
| `-m mypy` | clean, 63 source files |
| synthetic `calculate()` + `export_pptx()` for all 3 IIHS reports | 15/23/20-slide decks rendered successfully; only the accepted KTHC warnings appeared |

### Deviation / still open

- The KTHC warning is retained by design rather than extending the ISO channel-code catalog with a
  protocol-local identifier.
- No commit was created; unrelated existing working-tree changes remain untouched.

## 2026-08-07 — IIHS PowerPoint inspection exports

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** all three IIHS decks exported to `out/` for maintainer inspection
**Review:** ☐ pending

- Ran `PYISOMME_PPTX=iihs_frontal_small_overlap,iihs_frontal_moderate_overlap,iihs_side_impact
  .venv/Scripts/python.exe -m unittest tests.test_report`.
- The opt-in test passed in 34.504 s and reopened each generated file to verify that its slide count
  matches the report page count.
- Left the 15-slide Small Overlap, 23-slide Moderate Overlap and 20-slide Side Impact `.pptx` files in
  `out/` for manual inspection. No source or snapshot definition was changed in this follow-up.

## 2026-08-07 — Follow-up: IIHS casing, driver label and Nij plot limits

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** report artifacts and page metadata follow the established Title Case convention; Nij bands render on component plots
**Review:** ☐ pending

### What changed

- `tests/test_report.py` now names generated files from the registered report class, e.g.
  `IIHS_Frontal_Moderate_Overlap.pptx`, rather than the lower-case builder stem.
- Changed each IIHS report name and every explicit IIHS page `name`/`title` to the Title Case style used
  by the Euro NCAP frontal reports, including the `NIJ` acronym.
- Small Overlap now specializes the shared H350M aggregate as `Criterion_Driver`, so the final row on the
  Driver Injury Ratings page reads `Driver` instead of `H350M injury measures`.
- Kept scoring Nij limits on their synthesized `NIJCIP00` channel. `make_nij_plot_limits()` copies those
  four rows for the plotted CF/CE/TF/TE component channels, so plot bands render without changing the
  scoring channel or synthetic-data requirements.
- Re-generated all affected IIHS result, validation and description baselines. Re-exported the 15/23/20
  slide decks to `out/` with the corrected file casing.

### Verification

| Command | Result |
|---|---|
| direct `tests.report_pptx_case` exports for Small/Moderate/Side | 15/23/20 pages equal 15/23/20 slides |
| `PYISOMME_PPTX=iihs_frontal_moderate_overlap -m unittest tests.test_report` | **1 test OK** in 14.064 s |
| relevant IIHS/golden/validation/describe/import suite | **58 tests OK** in 70.984 s |
| `-m ruff check .` | all checks passed |
| `-m mypy` | clean, 63 source files |
| `git diff --check` | clean; line-ending warnings only |

### Deviation / still open

- The first all-three opt-in `test_report` wrapper invocation exceeded its five-minute limit in the nested
  process path. Each direct child export, and a subsequent isolated wrapper run, completed successfully;
  no rendering or slide-count issue reproduced.

## 2026-08-07 — Follow-up: provider-backed IIHS frontal resultants

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** IIHS frontal criteria request combined channels through the standard provider path
**Review:** ☐ pending

### What changed

- Replaced the repeated left/right channel loops in the shared H350M criteria with one
  `require_channel()` request for the provider-built resultants: knee-slider displacement (`KNSL0000`),
  tibia index (`TIIN0000`), tibia axial force (`TIBI00LO`) and foot acceleration (`FOOT0000`).
- Applied the same pattern to Moderate's H35F rear femur compression (`FEMR0000`) and updated each
  matching `Limit` pattern to include the combined result channel as well as the source channels used by
  plots.
- Extended the tibia-index provider to aggregate directly recorded `TIIN…TO…` channels. It deliberately
  consults only recorded/filterable inputs, preserving the existing moment-based tibia-index calculation
  when direct index channels are absent.
- Added a regression for the direct total-moment tibia-index aggregation. Side-impact five-sensor torso
  and pelvis assessments remain explicit because their prescribed average-peak, worst-peak and positive
  force-sum operations are not a physical left/right resultant channel.
- Regenerated the three IIHS result snapshots and validate/describe baselines; refreshed the IIHS
  inspection decks in `out/`.

### Verification

| Command | Result |
|---|---|
| relevant IIHS/golden/validation/describe/import/provider suite | **61 tests OK** in 72.682 s |
| focused `test_calculate` tibia-index/femur-impulse cases | **3 tests OK** |
| scoped Ruff (`providers.py`, `report/iihs`, `test_calculate.py`) | all checks passed |
| direct PPTX exports | 15/23/20 pages equal 15/23/20 slides |

### Deviation / still open

- Repository-wide Ruff and mypy are currently blocked by an unrelated invalid annotated assignment in
  `pyisomme/report/report_protocol.py:14`; this file was not modified in this follow-up.

## 2026-08-07 — Correction: Foot Acceleration fixture and Tibia Index method

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** removed an artificial Foot Acceleration overflow; restored the distinct IIHS total-moment Tibia Index path
**Review:** ☐ pending

This entry corrects the preceding provider-resultant entry: no `TIIN…TO…` channel is copied into a
normal-moment `TIIN…00…` channel.

### What changed

- The extreme synthetic Foot Acceleration (`7.3273e+147`) came from CFC-filtering the fixture's only
  aggregate `FOOT0000…ACRA` signal before the Foot left/right provider could run. The IIHS criterion now
  disables that outer filtering when it requests `FOOT0000…ACRB`, and the IIHS fixture supplies the
  required left/right B-class source channels. The provider-built result is now `81.5767 g`, rated Good.
- Removed the temporary tibia-index provider bridge and its test. `TIIN…00…` keeps the normal bending
  moment method; IIHS now requests `TIIN00TO…`, which uses the existing
  `_build_tibia_index_using_total_moment()` provider and aggregates the adjusted-total-moment results
  without conflating the two methods.
- Regenerated IIHS result, validation and description baselines and refreshed all three inspection decks.

### Verification

| Command | Result |
|---|---|
| finite Foot / total-moment Tibia Index synthetic check | `81.57666381298868 g`, `TIIN00TO00000B` |
| relevant IIHS/golden/validation/describe/import/calculation suite | **60 tests OK** in 83.305 s |
| scoped Ruff | all checks passed |
| direct PPTX exports | 15/23/20 pages equal 15/23/20 slides |

### Deviation / still open

- Repository-wide Ruff and mypy remain blocked by the unrelated `report_protocol.py:14` syntax error;
  no change was made to that file.

## 2026-08-07 — Foot Acceleration unit consistency

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** the finite Foot Acceleration result and its displayed unit are now consistent
**Review:** ☐ pending

### What changed

- Converted the provider-built Foot Acceleration channel to `g0` before retaining it on the criterion.
  The criterion value, plotted signal, table unit and g-based limits now all use the same unit: `81.577 [g0]`.
- The total-moment Tibia Index remains a separate, existing provider route: `TIIN00TO…` dispatches to
  `_build_tibia_index_using_total_moment()`; no channel copy or cross-method fallback is present.
- Regenerated the three IIHS result snapshots plus validate/describe baselines, and refreshed the three
  inspection PPTX files.

### Verification

| Command | Result |
|---|---|
| finite Foot / total-moment Tibia Index check | `81.57666381298868 [g0]`, `TIIN00TO00000B` |
| relevant IIHS/golden/validation/describe/import/calculation suite | **60 tests OK** in 78.235 s |
| scoped Ruff | all checks passed |
| direct PPTX exports | 15/23/20 pages equal 15/23/20 slides |

### Deviation / still open

- The installed slide renderer cannot render in this environment because its bundled `@oai/artifact-tool`
  package is incomplete; export and slide-count checks completed successfully.
- Repository-wide Ruff and mypy remain blocked by the unrelated `report_protocol.py:14` syntax error;
  no change was made to that file.

## 2026-08-07 — Fix immutable Limit regressions

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** all 311 tests restored after the frozen-dataclass migration
**Review:** ☐ pending

### What changed

- Annotated the inherited dataclass field overrides in `report/euro_ncap/limits.py`,
  `report/iihs/limits.py`, `report/fmvss/limits.py`, `report/un/limits.py` and
  `report/us_ncap/limits.py`. Without annotations, the generated subclass constructors
  installed `Limit`'s base defaults (`name=None`, `color="black"`, `rating=nan`) instead
  of the protocol defaults; this caused the validation, IIHS and golden failures.
- Corrected `Ctx.fields` to use a real per-instance `default_factory` returning an
  immutable empty mapping. Retained the in-progress `Ctx.codes()` tuple return needed by
  immutable `Limit.code_patterns`.
- Finished the tuple migration in `side_farside_vtc.py` and the criterion-tree test.
  The test now uses `dataclasses.replace()` rather than mutating a frozen Limit.
- Reworked `get_full_limits()` to create its adjusted Limit with `dataclasses.replace()`
  instead of deep-copying and mutating a frozen instance.
- Added postponed annotation evaluation to the untracked `report_protocol.py`, making its
  union annotations importable and mypy-clean on the supported Python 3.9 target.
- Restored the existing validation golden's human-facing `Fail`/`Pass` labels; no result,
  definition, describe or validation snapshot needed re-baselining.

### Verification

| Command | Result |
|---|---|
| `-m unittest tests.test_limit tests.test_limits tests.test_criterion_tree tests.test_validate tests.test_iihs tests.test_report_modules` | **90 tests OK** in 13.873 s |
| `-m unittest tests.test_golden` | **16 tests OK** in 88.826 s |
| `-m unittest discover -s tests` | **311 tests OK, 1 skipped** in 195.528 s |
| `-m ruff check .` | all checks passed |
| `-m mypy` | clean, 64 source files |
| `git diff --check` | clean; line-ending conversion warnings only |

### Deviation / still open

- No behavior or protocol-number change is intended; the fixes restore the defaults and
  golden results from before commit `69105ed` while keeping Limit definitions frozen.
- Pre-existing staged `tests/test_limits.py`, unstaged `tests/test_validate.py`, handover
  notes, notebook and bundled subproject changes were preserved. No commit was created.
## 2026-08-09 — Out-of-band: Report / MetaReport composite architecture

**Branch:** `dev` · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** criterion reports and composite reports now share a small enforced presentation/lifecycle base
**Review:** ☐ pending

### What changed

- Added `BaseReport`, an ABC that owns report identity, cover labels, available/selected page state,
  ordered glob selection, `clear_pages()` / `reset_pages()`, validation printing and the shared PPTX
  export implementation. Saving a locked deck now retries three times and then raises instead of
  sleeping forever. Removed the in-progress `ReportInterface` typing Protocol; implementations no
  longer inherit empty Protocol method bodies.
- Made criterion-backed `Report` and composite `MetaReport` siblings under `BaseReport`. A bare
  `Report` now fails clearly because it has no `Criterion_Overall`; concrete protocol reports retain
  their typed trees, limits, manual inputs and per-report protocol selection.
- Rebuilt `MetaReport` around an ordered mapping of stable subreport keys to already constructed
  `BaseReport` objects. Its inputs, validation paths, printed headings and read-only protocol view use
  those keys. Ratings are per-instance, a generic unscored composite uses `rating = None`, and scored
  subclasses override the optional `aggregate_results()` hook.
- Meta reports now own optional cover/summary pages followed by every child's available pages. Their
  selected-page state is independent from child selection, and qualified patterns such as
  `frontal_mpdb/Page Name` disambiguate duplicate names while retaining available-page order.
- Migrated `EuroNCAP` to typed injection of its five constructed load-case reports and renamed its
  scoring hook to `aggregate_results()` without changing the score calculation. Its child protocols
  remain independently configurable (`meta.side_farside.protocol = ...`); no broad MetaReport
  protocol setter remains.
- Made `Page` a generic ABC and allowed `Page_Cover` to render any `BaseReport` via `coverage_labels`.
  Added focused hierarchy/composition/page/export regressions and adapted the synthetic EuroNCAP
  builder and the manual-input local fixture to the new API.
- Finished the overlapping protocol-metadata work sufficiently for Python 3.9 and static checking:
  `ReportProtocol` no longer uses the Python-3.10-only dataclass `slots` option, the protocol validator
  has postponed annotations, and `describe()` renders protocol versions explicitly. Re-baselined all
  14 describe snapshots; their only changes are `pages` becoming separate `available_pages` /
  `selected_pages` rows and the four UN protocol headers using version identifiers rather than dates.

### Behaviour / API changes

- `EuroNCAP(...)` now accepts constructed load-case `Report` objects, not lists of constructor
  arguments. Calculation result goldens, including the combined EuroNCAP score, are unchanged.
- `selected_pages` is a read-only tuple view. Selection changes use the named methods and preserve the
  report's defined page order; MetaReport selection does not mutate its children.
- A generic `MetaReport` is a valid non-scoring bundle (`rating is None`); missing data in an actual
  scoring scheme continues to propagate `nan` unchanged.
- Direct `Report(...)` construction is rejected instead of silently building an empty criterion tree.

### Verification

| Command | Result |
|---|---|
| `-m unittest discover -s tests` | **319 tests OK, 1 skipped** in 149.820 s |
| report/golden/architecture subset | **92 tests OK** in 100.062 s; includes all result goldens and a temporary MetaReport PPTX render/reopen |
| `-m tests.test_describe --regen` then `-m unittest tests.test_describe` | 14 definition snapshots regenerated; **5 tests OK** |
| `-m ruff check .` | all checks passed |
| `-m mypy` | clean, 69 source files |
| `git diff --check` | clean; line-ending conversion warnings only |

### Deviation / still open

- The `page.__init__(page.report)` export-time refresh moved into `BaseReport` but deliberately remains;
  the active refactor plan assigns its removal and lazy page selection to Step 11.
- The repository contained substantial staged and unstaged report/protocol/IIHS work before this
  session. It was preserved, no commit was created, and the combined working tree requires manual
  review.

## 2026-08-09 — Out-of-band: FMVSS 208 adult frontal rigid-barrier report

**Branch:** dev · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** configurable HF/H3 pass-fail report implemented from 49 CFR 571.208
**Review:** pending

### What changed

- Added pyisomme/report/fmvss/fmvss_208.py with an eager declarative tree for driver and front
  passenger containment, HIC15, chest a3ms, chest deflection, Nij, neck peak
  tension/compression and left/right femur force. Overall and occupant results are strict pass/fail
  minima; NaN is never skipped.
- Added DummyType.FEMALE_5TH (HF) and DummyType.MALE_50TH (H3) as construction-time report
  configuration. The stricter HF family is the default. Every measurement pattern carries the selected
  dummy identifier, preventing cross-family thresholds or derived Nij constants.
- Added 18 explicit pages in the Euro NCAP frontal style: cover, overall/occupant compliance tables,
  values charts/tables, and detailed head, neck load, Nij, chest and femur plots for both occupants.
- Added pyisomme/report/fmvss/protocols.py for the supplied 2022-10-14 eCFR source and re-exported /
  registered FMVSS_208 in the FMVSS package, top-level report registry, CLI registry and deterministic
  test registry.
- Added docs/log/20260809_FMVSS-208-Report.md, documenting the included S14.4/S14.5/S15 adult frontal
  criteria, conservative defaults and the deliberately excluded equipment, setup, child, lateral,
  rollover and low-risk-deployment provisions.
- Corrected calculate_neck_nij()'s combined channel: tension-flexion is now included and
  tension-extension is no longer counted twice. Added a regression with an analytical Ntf result of
  0.2.
- Added tests/test_fmvss.py, a result golden, a 279-line definition snapshot, and the report's empty
  validation baseline entry. Extended the synthetic fixture with HF raw head, chest and neck-moment
  channels so HIC15/a3ms are genuinely derived and every signal page is exercised.

### Behaviour / assumptions

- Dummy containment is a typed per-occupant manual input and defaults to False; compliance must be
  positively confirmed from video or post-test inspection.
- The default HF thresholds are HIC15 700, chest a3ms 60 g, chest compression 52 mm, Nij 1.0,
  neck tension/compression 2620/2520 N and femur compression 6805 N. H3 selects 63 mm,
  4170/4000 N and 10008 N while HIC15, chest a3ms and Nij remain unchanged.
- One Isomme represents one front-outboard adult rigid-barrier test with a single selected dummy
  family. Physical test speed, angle, belt state, positioning and other setup compliance are not
  inferred from signal data.
- The Nij fix can change a provider-derived total when a crash contains tension-flexion or
  tension-extension loading. Existing report goldens did not change; the new analytical regression
  demonstrates the corrected Ntf contribution.

### Verification

| Command | Result |
|---|---|
| focused FMVSS/Nij/import suite | **9 tests OK** in 18.861 s |
| python -m unittest discover -s tests | **323 tests OK, 1 skipped** in 254.850 s |
| python -m ruff check . | all checks passed |
| python -m mypy | clean, 71 source files |
| git diff --check and git diff --cached --check | clean; line-ending conversion warning only |
| synthetic calculate() + export_pptx() + reopen | **18 pages = 18 slides** |

### Deviation / still open

- The source pages were extracted and rendered with Poppler, but both available image-inspection
  surfaces failed because the Windows sandbox helper could not start. Thresholds were checked against
  the complete extracted S5/S6/S14/S15 passages; a maintainer should still visually compare the
  implementation with PDF pages 34-37 and 58-63 during manual review.
- The report intentionally does not claim complete FMVSS 208 vehicle certification; the precise scope
  and every conservative assumption are recorded in the dedicated scope document.
- Pre-existing progress-log, handover, notebook and bundled-subproject changes were preserved. The
  temporary rendered PDF pages and 18-slide smoke deck were removed after verification. No commit was
  created.

## 2026-08-09 — Follow-up: per-occupant FMVSS 208 dummy detection

**Branch:** dev · **Commit(s):** uncommitted — awaiting manual review
**Outcome:** report-level dummy selection replaced by automatic per-occupant H3/HF detection
**Review:** pending

### What changed

- Removed the `FMVSS_208(..., dummy_type=...)` constructor argument and report-wide dummy state.
  Each driver/passenger `Criterion_Occupant` now owns a typed `dummy_type` manual input.
- Derive that input from the ISO-MME `fine_location_3` field on channels at the occupant's resolved
  position. A unique `H3` or `HF` selects its corresponding channel patterns and limit family;
  missing or conflicting identifiers conservatively derive `HF`. A user assignment still wins over
  derivation and limits rebuild from it during calculation.
- Updated all signal pages to use the resolved dummy identifier of their own occupant. One report can
  therefore plot and assess, for example, an H3 driver at position 1 and an HF passenger at position 3.
- Changed the deterministic FMVSS fixture to that mixed H3-driver/HF-passenger arrangement. Added
  focused regressions for automatic mixed detection, family-specific limits/patterns, the conservative
  empty-data fallback and explicit per-occupant override.
- Re-baselined the FMVSS definition snapshot to record the two new manual inputs. Re-baselined the
  result golden because the mixed fixture's H3 driver now passes the 63 mm chest-deflection limit at
  about 60 mm; the passenger remains on the stricter HF family.
- Updated the dedicated scope/assumptions document. The user-removed analytical Nij typo regression
  was not restored; the underlying tension-flexion calculation correction remains unchanged.

### Verification

| Command | Result |
|---|---|
| `-m unittest tests.test_fmvss` | **4 tests OK** in 0.063 s |
| `-m tests.test_describe --regen` | FMVSS describe snapshot now contains one `dummy_type` input per occupant |
| `-m tests.golden_regen fmvss_208` | one intentional H3 chest-deflection result change; exact diff manually reviewed |
| `PYISOMME_PPTX=fmvss_208 ... -m unittest tests.test_report` | **1 test OK** in 40.906 s; **18 pages = 18 slides**, deck retained at `out/FMVSS_208.pptx` |
| `-m unittest discover -s tests` | **323 tests OK, 1 skipped** in 246.732 s |
| `-m ruff check .` | all checks passed |
| `-m mypy` | clean, 71 source files |
| `git diff --check` | clean; line-ending conversion warnings only |

### Deviation / still open

- Automatic identification intentionally accepts only `H3` and `HF`. Ambiguous positions do not
  guess: they use the stricter HF limits unless the engineer explicitly sets that occupant's input.
- The earlier PDF visual-review limitation still applies; this follow-up changes selection mechanics,
  not any regulatory threshold or scope.
- Existing staged work and unrelated untracked handover/notebook/subproject files were preserved.
  Follow-up edits remain unstaged on top of the partially staged FMVSS files. No commit was created.
