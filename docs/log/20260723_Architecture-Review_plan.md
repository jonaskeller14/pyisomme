# pyisomme — Refactor Implementation Plan

Tracks the incremental rollout of the improvements in [ARCHITECTURE_REVIEW.md](ARCHITECTURE_REVIEW.md).
Each step is self-contained and must leave the test suite green.

**Status legend:** ⬜ Not started · 🟡 In progress · ✅ Done · ⏭️ Deferred

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | **Error taxonomy + 3 outcome states** | ✅ Done | `errors.py` (`PyisommeError` tree, `MissingData`, `Status`), `Criterion.require*()`, 3-state `Criterion.calculate()`; `tests/test_errors.py` green |
| 2 | Normalization boundary at ingest | ⬜ | Centralize convention-handling in `parsing.py`; log assumptions; fix integer-index fall-through |
| 3 | Kill `assert`-as-validation + cache `channel_codes.xml` | ⬜ | `Code.__new__` → `InvalidCodeError`; module-level XML cache |
| 4 | Fix aliasing + calc-history bugs | ⬜ | `integrate`/`differentiate` info copy; operator history strings |
| 5 | De-duplicate readers behind `ArchiveSource` | ⬜ | fs/zip/tar → one interface; single encoding-fallback helper |
| 6 | Tighten union types | ⬜ | `__getitem__`, `cfc`, `get_data` split |
| 7 | `get_channel` → provider registry | ⬜ | Biggest structural win; provider-by-provider |
| 8 | Explicit `Criterion.children` + occupant helper | ⬜ | Replace `dir()` reflection; de-dup position logic |

---

## Step 1 — Error taxonomy (3 outcome states)  ✅

**Goal:** stop conflating "missing input" (expected) with "bug" (unexpected) with
"legitimate NaN". Give each criterion exactly one of three outcomes, and let a criterion
declare its required inputs *by fetching them* (no redundant requirement lists).

### Tasks
- [x] `pyisomme/errors.py`: `PyisommeError` base + `MalformedFileError`, `InvalidCodeError`,
      `UnitError`, `MissingData`, and a `Status` enum (`PENDING`/`OK`/`NA`/`ERROR`).
- [x] `Criterion.require()` / `require_channel()` / `require_test_info()` accessors that
      raise `MissingData` when an input is absent.
- [x] Rewrite `Criterion.calculate()` to the 3-state model:
      `MissingData → NA`, any other exception → `ERROR`, success → `OK`.
- [x] Export the new names from `pyisomme/__init__.py`.
- [x] `tests/test_errors.py` — fixture-free unit tests for the three outcomes.

### Design notes
- `Status` default is `PENDING` (before `calculate()` runs). The three *outcome* states
  are `OK` / `NA` / `ERROR`.
- **Backward compatible:** `.status` was previously a `bool` read nowhere outside
  `criterion.py`; NA/ERROR criteria still leave `value`/`rating` as `np.nan` and
  `channel`/`color` as `None`, so existing pages render identically (they already guard
  `channel is None`). No migration of existing criteria is required for this step —
  un-migrated criteria that hit missing data will surface as `ERROR` (loud) until moved to
  `require*()`, which is the intended incremental path.
- `errors.py` imports nothing from `pyisomme` (no circular imports).

### Follow-on (later, incremental)
- Migrate concrete criteria from `self.isomme.get_channel(...)` + implicit `None`
  handling to `self.require_channel(...)`, so missing data becomes `NA` instead of
  `ERROR`. Do this file-by-file (start with `euro_ncap/frontal_50kmh.py`).
- Once Step 7's provider registry exists, have `get_channel` raise a typed absence that
  names the missing sub-input, feeding richer `NA` reasons.
