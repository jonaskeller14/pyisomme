# `pyisomme.report` Refactor — Implementation Plan

Executable, step-by-step plan derived from [`20260726_Report-Architecture-Review.md`](20260726_Report-Architecture-Review.md).
The review is the **why** (findings F1–F15, proposals P1–P11, goals G1–G9); this file is the **what**.

Companion file: [`20260726_Report-Architecture-Review_progress.md`](20260726_Report-Architecture-Review_progress.md) — the running log every session must update.

---

## How to run a step (for the agent session)

Each step is sized for **one fresh session**. A session's job:

1. Read this file's *Ground rules* + the step you were asked to do. Read `20260726_Report-Architecture-Review_progress.md` for what already happened.
2. Consult the review doc **only** for the finding/proposal IDs your step names — do not read it end to end.
3. Implement **only that step**. Do not opportunistically fix things belonging to later steps; note them in the progress file instead.
4. Verify against the step's *Acceptance criteria*.
5. Append a session entry to `20260726_Report-Architecture-Review_progress.md`.
6. **Stop — do not commit.** Hand the step over for manual review (see *Manual review gate* below).

### Ground rules (apply to every step)

- **Python:** always use the repo venv — `.venv/Scripts/python.exe` on Windows. The `python` on `PATH` is a broken Anaconda 3.12 (numpy 2.3.5 vs. scipy built for <1.29) and cannot even `import pyisomme`. See Step 0.
- **Git:** one branch per step (`refactor/step-<n>-<slug>`), branched from `dev`. One commit (or a small logical series) per step, created **only after the maintainer has reviewed the step** (see below). Never commit to `master`.
- **Manual review gate — a session never commits on its own.** Every step ends with the work *staged or
  unstaged in the working tree*, not in a commit. The session's last action is a handover summary:
  what changed (file by file), what was verified (commands and their output), what deviates from the
  plan, and what is still open. The maintainer reads the diff, then either asks for changes or says
  "commit" — only then does a commit happen, and only then does the step's status board row move to
  done. Recording the progress entry is *not* the same as being finished; the entry is part of what is
  under review, so write it before handing over.
- **Scope discipline:** if a step turns out to require something the plan did not anticipate, record it in the progress file and **stop** — do not improvise a larger change.
- **Invariant G9 — NaN propagation is intentional.** `np.min`/`np.sum`/`np.max` (propagating) must stay the default. Never "fix" a `nan` by switching to a `nan*` variant. The single deliberate `np.nanmean` (`frontal_50kmh.py:89`) stays.
- **Invariant G8 — the criterion tree is eagerly constructed and user-mutable.** Users set manual inputs between construction and `calculate()`. No lazy child construction, ever.
- **Invariant G4 — nesting stays.** The criterion tree mirrors the protocol structure and drives the PPTX. Do not flatten it.
- **No migration burden.** The project is pre-release; breaking API changes are acceptable and preferred over compatibility shims.
- **Behaviour changes must be visible.** If a step changes any computed value, say so explicitly in the progress entry, with the before/after numbers.

---

## Step 0 — Fix and standardise the Python environment

**Goal:** every subsequent step can run tests without fighting the interpreter.

**Findings addressed:** none (prerequisite).

**Current state (measured 2026-07-26):**

| | Interpreter | numpy | scipy | `import pyisomme` |
|---|---|---|---|---|
| `python` on PATH | `C:\ProgramData\anaconda3\python.exe` 3.12.7 | 2.3.5 | 1.12.0 | **fails** — `ValueError: numpy.dtype size changed` |
| `.venv` (repo) | Python 3.9.13 | 1.26.4 | 1.12.0 | **works** |

`.venv` already has all runtime deps plus `objective_rating_metrics` (the `dev` extra), and `data/` fixtures are present locally (`iso-mme-org`, `nhtsa`, `vtc-loadcase-example`). `tests.test_report.TestReport.test_EuroNCAP_Frontal_50kmh` passes there in ~29 s.

**Scope:**
- Document the venv as *the* development interpreter in `CLAUDE.md` (commands section) — replace bare `python` with the venv path or an activation line.
- Decide and record whether the target dev version stays 3.9 (matching `requires-python = ">=3.9"`) or moves to 3.12. **Recommendation: keep 3.9 as the floor** — it is what CI tests and what `.venv` runs — but verify the CI 3.12 leg still passes, since Step 3 (typing) and Step 4 (`Annotated`) have version-sensitive behaviour.
- Optionally repair the Anaconda base env (`pip install "numpy~=1.26.3"`) so a stray `python` call is not silently broken. Non-essential if the venv is documented.
- Confirm the full suite state: run `discover -s tests` in the venv and record which tests pass/fail/error **as the pre-refactor baseline**.

**Out of scope:** any change to `pyproject.toml` dependency pins; CI changes (Step 1).

**Acceptance criteria:**
- [ ] `CLAUDE.md` names the correct interpreter; a fresh session copying its commands succeeds.
- [ ] Full test suite has been run in the venv and its outcome recorded verbatim in the progress file.
- [ ] Progress entry states the chosen dev Python version and why.

---

## Step 1 — Safety net: golden tests + import smoke test

**Goal:** make every later refactor verifiable. Nothing below this line is safe without it.

**Findings addressed:** F12 (broken modules invisible), and the general risk of silently changing numbers.

**Scope:**
- **Import smoke test** (`tests/test_report_modules.py`): walk every module under `pyisomme/report/` with `pkgutil` and import it. This immediately fails on `us_ncap/frontal_56kmh.py` (imports a non-existent `pyisomme.report.us_ncap.calculate`) — that is the point; mark those known-broken modules with an explicit skip list containing a TODO referencing Step 2, so the test is green but the breakage is recorded.
- **Golden value tests** for the two reference reports (`EuroNCAP_Frontal_50kmh`, `EuroNCAP_Frontal_MPDB`) using the existing fixtures from `tests/test_report.py`: walk the criterion tree, serialise `path → (name, value, rating, color)` to JSON, and compare against a committed golden file with a numeric tolerance (`rtol=1e-9`). `nan` must compare equal to `nan` — the `nan`s *are* part of the expected behaviour (G9).
- Golden files live in `tests/golden/` and **are committed** (they are small JSON; unlike `data/`, they must be tracked).
- A documented way to regenerate: `python -m tests.golden_regen` or an env var, so later steps can accept an intended change deliberately.

**Out of scope:** fixing any defect the tests expose (Step 2); making CI blocking (Step 3).

**Decisions already made:**
- Tree serialisation walks children in **`dir()` order for now** (today's behaviour). Step 7 changes the order to declaration order — that will legitimately change the golden file's *key order* but not its values; use a dict keyed by path, not a list, so order is irrelevant.
- Compare `value` and `rating`; also capture `color` (cheap, catches limit-matching regressions).

**Acceptance criteria:**
- [ ] `tests/golden/euro_ncap_frontal_50kmh.json` and `..._mpdb.json` committed.
- [ ] Golden tests pass in the venv, twice in a row (no nondeterminism).
- [ ] Import smoke test passes, with known-broken modules in an explicit, commented skip list.
- [ ] Deliberately perturbing one limit value locally makes a golden test fail (verify the net actually catches things), then revert.

---

## Step 2 — Fix the known defects from the review's Appendix A

**Goal:** clear out real bugs before restructuring, so later diffs are pure refactors.

**Findings addressed:** Appendix A1, A5, A6, A9. (A2 is *not* a bug — see below.)

**Scope — fix exactly these:**

| ID | Location | Fix |
|---|---|---|
| A1 | `frontal_mpdb.py:183` | Missing `> 80` comparison → currently tests truthiness of a float, so it always assumes hard contact and **silently overrides a user's manual `hard_contact = False`**. Restore the comparison as in `frontal_50kmh.py:147`. Expected to be golden-neutral (default is already `True`) — confirm against Step 1's golden files and say so in the progress entry. |
| A5 | `us_ncap/frontal_56kmh.py:4` | Imports non-existent `pyisomme.report.us_ncap.calculate`; `us_ncap/` has no `__init__.py`. Either restore the missing module or reduce the report to an honest stub. **Decision: make it an honest stub** — this report is not in `REPORTS` and not part of the refactor's target scope. Add `__init__.py`. |
| A6 | `us_ncap/us_ncap.py:12` | `USNCAP.__init__` iterates `self.reports`, never assigned → `AttributeError` on construction. Assign the sub-report list (mirroring `EuroNCAP`) or stub the class out consistently with A5. |
| A9 | `pyisomme/limits.py:20` | `Limit.rating: float` has no default → a `Limit(...)` without `rating=` constructs fine and fails much later inside `get_limit_ratings()`. Give it `rating: float = np.nan` **and** raise a clear error at construction if a rating-consuming path needs it, or make `rating` a required constructor argument. Prefer the explicit error. |

Also: remove the corresponding entries from Step 1's skip list.

**Explicitly NOT in scope:**
- **A2 (`hard_contact`) is correct as designed** — `default=True` OR-ed with the curve check implements "video observation OR curve evidence", with a conservative default. Do not "fix" it. An optional readability improvement (`self.hard_contact = self.hard_contact or peak > 80`) is allowed; the tri-state redesign belongs to Step 4.
- A3, A4, A4b, A4c, A15, A16 require a **protocol/PDF decision by the maintainer** — do not guess. List them in the progress file as open questions.
- A8 (page `__init__` re-run) → Step 11. A11/A12 (`dir()` discovery) → Step 7. A13 (ragged tables) → Step 11. A14 (CI) → Step 3.

**Acceptance criteria:**
- [ ] Golden tests still pass, or every deviation is explained with before/after numbers.
- [ ] Import smoke test passes with an empty (or strictly smaller, justified) skip list.
- [ ] Open protocol questions (A3, A4, A4b, A4c, A15, A16) listed in the progress file for the maintainer.

---

## Step 3 — Typing and lint (proposal P5)

**Goal:** make typos in criterion paths, page wiring and **manual inputs** editor-time errors.

**Findings addressed:** F2, F3, F13 (statically), F12 (via CI).

**Scope:**
- Make `Report` generic in its overall criterion: `class Report(Generic[C])`, `criterion_overall: dict[Isomme, C]`, plus a typed accessor `def overall(self, isomme: Isomme) -> C`. This is what makes the ~530 `report.criterion_overall[...]....` chains checkable.
- Type `Criterion.__init__(self, report: Report, isomme: Isomme)` and every subclass signature (`p: int`, return types).
- Replace `self.isomme.get_channel(...).get_data(...)` with `self.require_channel(...)` at the ~61 sites where the result is dereferenced immediately. This is what `require_channel` was built for and currently has **zero** uses outside `criterion.py`. It converts "missing channel" from a swallowed `AttributeError`/`Status.ERROR` into a clean `Status.NA` naming the pattern.
- Add `[tool.mypy]` to `pyproject.toml` scoped to `pyisomme/report/` first (`disallow_untyped_defs = true`), plus `pyisomme/py.typed`.
- Add `[tool.ruff]` config; flip the lint job in `.github/workflows/ci.yml` to `continue-on-error: false`. Leave the **test** job non-blocking (fixtures are untracked) but add the import smoke test to the blocking lint job — it needs no fixtures.

**Watch out:** `require_channel` changes `Status.ERROR` → `Status.NA` for missing channels, and may change `value`/`rating` where a swallowed exception previously left a default. **Golden files may legitimately change** — diff them, justify each change, regenerate deliberately.

**Acceptance criteria:**
- [ ] `mypy pyisomme/report` clean in the venv.
- [ ] `ruff check .` clean; CI lint job blocking.
- [ ] Golden tests pass, or every diff is explained and the goldens regenerated deliberately.
- [ ] A deliberate typo like `report.overall(v1).criterion_drivr` is reported by mypy (verify, then revert).

---

## Step 4 — Manual inputs as a declared concept (proposal P11)

**Goal:** the G8 workflow becomes safe, discoverable and traceable. Independent of Steps 5–10.

**Findings addressed:** F13, F14, F15.

**Scope:**
- `Manual[T, manual(default, unit=…, doc=…, source=…)]` declarations based on `typing.Annotated` (type-transparent — mypy still sees `float`; works on 3.9 via `get_type_hints(include_extras=True)`). Migrate the ~59 existing manual-input class attributes across the 14 report modules.
- `Criterion.__setattr__` guard: reject assignment to names that are neither declared inputs nor framework fields, with a "did you mean …?" suggestion. Whitelist framework fields (`value`, `rating`, `color`, `status`, `channel`, `limits`, `na_reason`, `name`, `p`, …) via an explicit set — keep it a cheap name lookup.
- `Report.print_inputs()` / `get_inputs()` / `set_inputs(dict)` with JSON round-trip, so manual assumptions can be stored beside the ISO-MME container and replayed.
- **F15 fix:** move every manual input's consumption out of `__init__` into `calculation()`. The `p_driver`/`p_front_passenger`/`p_rear_passenger` case needs care — children are currently *constructed* with `p`, so this either waits for Step 6's `Ctx` or gets an interim fix that re-reads the position at calculate time. **Decision: interim fix here** (re-read in `calculation()`), superseded cleanly by Step 6.
- Tri-state where it makes sense: `hard_contact: Manual[bool | None]` with `None` = derive from curve. This *is* a behaviour change — the default becomes "derive" rather than "assume contact". **Flag it for maintainer approval in the progress file before committing**; if unapproved, keep the current default and only add the declaration.

**Out of scope:** rendering inputs in the PPTX (Step 13/`describe()` in Step 12).

**Acceptance criteria:**
- [ ] `report.print_inputs()` lists all inputs with path, default, current value, unit, doc.
- [ ] A typo'd assignment raises immediately with a helpful message (test it).
- [ ] A wrong-typed assignment (`submarining = "yes"`) is rejected.
- [ ] `set_inputs(get_inputs())` is a no-op round-trip; a saved JSON reproduces a run.
- [ ] Setting `p_driver` after construction now affects criteria **and** plots consistently (F15) — regression test.
- [ ] Golden tests pass (default input values must not change unless approved).

---

## Step 5 — Limit scales (proposal P3, part 1) — **WITHDRAWN 2026-08-02**

**Status: rejected by the maintainer after review. The helpers were built, reviewed and stashed; no
report module was ever migrated. P3 is dropped as a *generator*; the part of F5 worth keeping moves to
Steps 10 and 12 (see below).**

**Maintainer's decision:** the hand-written `extend_limit_list` block stays the authoring form for
protocol thresholds. A raw list is a literal transcription of the protocol table, checkable line by line
by an engineer with the PDF open and no knowledge of the framework's conventions. `sliding_scale(...)`
replaces a *visible* error (a wrong number, easy to spot in review) with an *invisible* one (right
numbers, wrong convention applied), and moves the blast radius of any single mistake from one criterion
to every criterion using the helper.

**Reasons recorded, so this is not relitigated:**

1. **The helper hides five implicit conventions** behind a three-number call: the 1/3–2/3 blend, the
   3-decimal rounding (`DECIMALS`), the "Poor row drops its `upper`/`lower` flag when a capping row sits
   at the same value" rule, direction derivation from the sign, and `symmetric=` mirroring. Each is
   correct today and none is visible at the call site.
2. **The domain is too irregular for the helper to cover.** By the equivalence proof's own tables:
   `EuroNCAP_Side_Pole` 3 of 8 blocks, `EuroNCAP_Frontal_MPDB` 22 of 27. Modifier tables (0/−1/−2 pt),
   Good/Poor pairs (D15), capping-only pairs and R95's three-row block (D13) have no helper. A migrated
   module would be a *mixture* of generated and raw blocks — harder to read than uniformly raw, because
   a reader must first work out which style a given block is in.
3. **The API erodes to reproduce irregularities.** `capping_code_patterns=` was added for exactly one
   call site — and that call site turned out to be a **typo**, fixed independently in `155f533`
   (2026-07-28). The helper had grown a parameter whose only purpose was faithfully reproducing a bug,
   and the parameter (and D12) went stale within a day.
4. **The proof is heavy and coupled.** It broke on its own within a week: `tests/test_limit_scales.py`
   calls `golden_utils.serialise_limit(limit, SAMPLE_X)`, but the matching `sample_x` parameter never
   reached `tests/golden_utils.py` and the module now raises `TypeError` on import-time use; the driver
   neck Fz case is stale against `155f533`. Neither failure was caught, because nothing else depends on
   the file.
5. **The benefit is smaller than it looks.** The saving is 126 interpolated intermediates repo-wide —
   numbers that are *printed in the protocol PDFs*, not invented by the module author — and a typo in
   one that changes a rating is already caught by `tests/test_golden.py` and
   `tests/test_report_structure.py`.

**What the maintainer's concern does *not* dispose of.** Two real problems in F5 survive and are
reassigned:

- **Duplication** — the same HIC/a3ms/neck scale is typed out in five places, so a protocol threshold
  change means editing N blocks. **The answer is reuse, not generation:** one named `HIC15` criterion
  class shared across reports states the numbers once and keeps them literal. → **Step 10**, which
  already owns this.
- **Flag conventions are genuinely error-prone** — the `capped_at_poor` rule in particular is encoded by
  accident in the raw lists and is exactly the kind of typo the maintainer worries about. **The answer
  is a checker, not a generator.** → **Step 12** (see its scope note): `validate()` asserts properties of
  a hand-written block without owning its numbers. This keeps F5's benefit (the two PDF numbers are
  stated once and machine-checked) with none of P3's single-point-of-failure risk.

**Disposition of the built code** (branch `refactor/step-4-manual-inputs`, uncommitted): staged and
stashed on 2026-08-02 — `pyisomme/report/scales.py`, the `sliding_scale`/`pass_fail`/`star_scale`
helpers in the three `limits.py` files, `tests/test_limit_scales.py`, and `CLAUDE.md`'s "Limit scales"
section. Recover it from the stash if Step 12 wants `Curve`/`Direction` as validator building blocks —
they are the reusable part. **Not** stashed, because it is an unrelated fix: the one-line
`from pyisomme.limits import Limit` → `pyisomme.limit` repair in `euro_ncap/limits.py`, without which
that module does not import at all.

**Left in place from Step 5's analysis:** D12 (resolved by `155f533`), D13, D14 (moot — no migration),
D15 in the progress file.

---

## Step 6 — `PeakCriterion` + migrate leaf criteria (proposal P4)

**Goal:** the ~80 % standard leaf becomes a 5-line declaration with a single source of truth for code patterns.

**Findings addressed:** F3 (structurally), F4. *(P3 part 2 — migrating limit blocks to generated scales
— is removed: Step 5 was withdrawn. Limit blocks stay hand-written `extend_limit_list` lists.)*

**Scope:**
- `PeakCriterion` base: `codes` + `reduce` (`MAX`/`MIN`/`MAX_ABS`/`FIRST`) + `unit` + `limits` + `interpolate`, with a framework-provided `calculation()` that does `require_channel` → reduce → rating → colour.
- **Single-source `codes`:** the same declaration feeds both the limits' `code_patterns` and the channel lookup (F4). Note the two are *not* identical today — limits use a filter-class wildcard (`…MOY?`) while lookups use a concrete class (`…MOYB`). Model this explicitly with a `filter_class` field; do **not** paper over it with wildcard magic.
- Migrate leaves in the two reference reports first (`frontal_50kmh`, `frontal_mpdb`), then the rest.
- `Reduce.MAX_ABS` replaces the hand-written `data[np.argmax(np.abs(data))]` idiom (8 sites).

**Explicitly out of scope:** rewriting any `Limit(...)` row. `PeakCriterion` may *supply* the
`code_patterns` a hand-written row uses, but the thresholds, colours and `upper`/`lower` flags stay
literal. See the withdrawn Step 5.

**Acceptance criteria:**
- [ ] Golden tests pass unchanged for both reference reports.
- [ ] `frontal_50kmh.py` line count materially reduced — record the actual number. The ≲ 900 (from 1472)
      estimate assumed Step 5's limit generation; without it, expect a smaller reduction.
- [ ] Every migrated leaf's channel pattern is declared exactly once.

---

## Step 7 — `sub()` descriptor + `Ctx` framework (proposals P1 + P2, framework only)

**Goal:** the wiring infrastructure, with no report migrated yet.

**Findings addressed:** F1, F6, F15 (properly).

**Scope:**
- `sub(cls, *, name=…, at=…, role=…)` typed descriptor (`Generic[C]` with `__get__` overloads so `self.driver.head.hic15` resolves in mypy and the IDE); `__set_name__` records declaration order.
- Base `Criterion.calculate()` walks declared children **in declaration order**, calculates them, then calls `self.calculation()`.
- Aggregation helpers: `min_of_children()`, `sum_of_children()`, `modifiers_sum()` — **all NaN-propagating** (G9). A NaN-tolerant variant must take an explicit `skip_missing="<reason>"` argument that Step 13 renders in the output.
- `add_child(name, criterion)` escape hatch for dynamic trees (the correlation report's `self.criteria` list — F6/A12).
- `Ctx` frozen dataclass (`report`, `isomme`, `position`, `dummy`, `side`) resolved **lazily at the start of `calculate()`**, replacing the `p` threading; children inherit unless overridden. This is the proper F15 fix that supersedes Step 4's interim one.
- Replace `dir()`-based discovery in `get_subcriterion`/`get_subcriteria`/`print_results` with the ordered children list (F6, A11).

**Out of scope:** migrating reports (Steps 8–9). Framework must coexist with the old manual style during the transition.

**Acceptance criteria:**
- [ ] Unit tests for the framework: declaration order preserved; children auto-calculated; `add_child` works; NaN propagation verified explicitly.
- [ ] mypy resolves `SomeCriterion.child.grandchild.rating` to `float`.
- [ ] Old-style reports still work and golden tests pass (framework is additive so far).
- [ ] `print_results()` now emits protocol order, not alphabetical — this changes *output text*; if a golden file captures ordering, regenerate deliberately.

---

## Step 8 — Migrate `frontal_50kmh` to the declarative tree (pilot)

**Goal:** prove the target style on the reference report before touching the rest.

**Scope:** convert `EuroNCAP_Frontal_50kmh` to `sub()` + `Ctx` + `PeakCriterion`. Remove the per-criterion `__init__`s, the explicit `child.calculate()` calls, and the `self.p = p` threading.

**Acceptance criteria:**
- [ ] Golden test for this report passes **unchanged** (this is the whole point of the pilot).
- [ ] Manual-input workflow still works end to end (Step 4's regression tests).
- [ ] Record the before/after line count and a short verdict on whether the style is worth rolling out — **if it is not, stop and report back rather than migrating the other reports.**

---

## Step 9 — Migrate the remaining reports

**Scope:** `frontal_mpdb`, then `side_*`, `un/*`, `iihs/*`, `correlation` (the last exercises `add_child`). One commit per report.

**Acceptance criteria:**
- [ ] Golden tests pass for the two covered reports; others verified by construct-and-calculate smoke runs.
- [ ] No `def __init__(self, report, isomme, p)` boilerplate left (target: 0 of the current 180).

---

## Step 10 — Shared criteria library (proposal P9)

**Scope:** `euro_ncap/criteria.py` with top-level, context-parameterised `HIC15`, `HeadA3ms`, `NeckMyExtension`, `NeckFzTension`, `NeckFxShear`, `ChestDeflection`, `ChestVC`, `FemurAxialForce`, `ShoulderBeltLoad`, `Submarining`, `DoorOpeningDuringImpact`, `DAMAGE`. Replace the 13 deep cross-report class paths and the copy-pasted limit blocks. Variants (rear-passenger caps, missing capping rows) become subclasses.

**Findings addressed:** F8, F5 (residual duplication).

**Careful:** the driver/front/rear neck blocks look identical but differ in capping rows and rating caps. Diff them explicitly (Step 12's `describe()` would make this trivial — if the ordering allows, consider swapping Steps 10 and 12).

**Acceptance criteria:**
- [ ] Golden tests pass unchanged.
- [ ] No `EuroNCAP_Frontal_50kmh.Criterion_Overall....` style references remain.

---

## Step 11 — Pages select from the tree (proposal P6)

**Scope:** `role` on criteria (`RESULT`/`AGGREGATE`/`MODIFIER`); `Page.select(overall) -> Sequence[Criterion]` replacing the repeated 10-entry chain blocks; remove the `page.__init__(page.report)` re-run hack in `export_pptx` (A8) by resolving criteria in `construct()`; fix the ragged-table assumption (A13).

**Findings addressed:** F7, A8, A13.

**Acceptance criteria:**
- [ ] Exported PPTX for both reference reports has the same slides, in the same order, with the same content as before (compare shape/text inventory, not bytes).
- [ ] No page re-`__init__` remains.

---

## Step 12 — `validate()` and `describe()` (proposals P7 + P8)

**Scope:**
- `Report.validate()`: every criterion named; no orphans; every declared code pattern is a valid 16-char `Code` template; `max_rating` declared and achievable; every manual input actually read by some `calculation()`; synthetic-`Isomme` construct→calculate→export smoke run for every registered report.
- **Limit-block checks — this is where the withdrawn Step 5's value lands.** `validate()` asserts
  *properties* of a hand-written `extend_limit_list` block without owning its numbers, catching exactly
  the transcription typos raw lists are exposed to:
  - the `upper`/`lower` flags are consistent with the ordering of the rows' values (a
    higher-is-worse scale has `upper` on the best row and `lower` on every worse one, and vice versa);
  - the Poor row is unflagged **iff** a Capping row sits at the same value (the `capped_at_poor`
    convention, today encoded only by accident — the single most likely silent typo);
  - on a Euro-NCAP 4-point scale, Marginal and Weak lie at 1/3 and 2/3 between Good and Poor to within
    the 3 decimals the modules type out;
  - a symmetric block's two sides are exact mirrors;
  - `y_unit` is consistent across the rows of one block.
  Each is a **warning naming the block**, not a hard failure — a protocol is allowed to be irregular
  (D13's R95 three-row block is genuinely asymmetric); an intentional exception is silenced with a
  documented opt-out on the criterion.
  `pyisomme/report/scales.py`'s `Curve` and `Direction` are the natural building blocks for these
  checks — recover them from the Step-5 stash rather than rewriting them.
- `Report.describe()`: Markdown/table dump of the *definition* — path, name, channel patterns, limits, aggregation rule, manual inputs, `source` PDF reference. Commit a golden dump per report so threshold changes show up in PR diffs.
- Add `source: str` (PDF section) to criteria as they are touched.

**Acceptance criteria:**
- [ ] `validate()` runs in CI without fixtures and passes for every registered report.
- [ ] Golden `describe()` dumps committed for the two reference reports.
- [ ] Max-rating propagation check catches a deliberately broken aggregation (verify, then revert).
- [ ] Perturbing one intermediate in a hand-written sliding-scale block (e.g. `566.667` → `556.667`) is
      reported by `validate()` (verify, then revert) — this is the check that replaces Step 5.

---

## Step 13 — Status propagation and rendering (proposal P10)

**Scope:**
- Status propagates: a parent with an `NA` child becomes `NA` (carrying the reason); with an `ERROR` child, `ERROR`. Per-criterion `na_policy` (`Propagate` vs `Neutral`) because a missing **modifier** should arguably score 0 rather than invalidate its parent — decide per criterion, default `Propagate`.
- Render it: tables/charts show `n/a — 11CHST0003??DSXC missing` instead of bare `nan`; `print_results()` gains a status column; `Report.calculate(strict=True)` re-raises on `ERROR`.
- Deliberate NaN-tolerance is marked: `skip_missing="single-dummy development runs"` renders an asterisk + reason in the PPTX.
- Manual inputs deviating from defaults appear in the output (F14 traceability).

**Acceptance criteria:**
- [ ] A report run against a test missing a chest channel shows `n/a` with the channel name, not `nan`.
- [ ] The `np.nanmean` occupant average is visibly marked when an occupant is missing.
- [ ] `strict=True` fails a run containing a `Status.ERROR`.

---

## Deferred / not planned

- **F11 (protocol versions as data):** only one report currently branches on `protocol`. Keep the inline ternary; revisit when a second version actually lands.
- **`EuroNCAP` MetaReport requiring all five load cases** (A10): make sub-reports optional when someone needs a partial assessment.
- **P3 — generated limit scales (`sliding_scale`/`pass_fail`/`star_scale`):** **rejected 2026-08-02** after the helpers were built and reviewed. Hand-written `Limit` lists stay the authoring form; the numbers stay literal and PDF-checkable. Duplication → Step 10 (reuse), typo-catching → Step 12 (`validate()`). Full reasoning in the withdrawn Step 5 above.
- **YAML/JSON report definitions:** rejected (review Appendix B1) — Python is required for the edge-case logic and for lint/type warnings. The P3 rejection is the same principle applied one level down: the threshold table is data best read as data, not as a call that reconstructs it.
- **Auto-repairing missing data with `nan*` aggregations:** rejected (review Appendix B5) — violates G9.
