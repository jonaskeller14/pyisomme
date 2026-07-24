# pyisomme — Refactor Implementation Plan

Tracks the incremental rollout of the improvements in [20260723_Architecture-Review.md](20260723_Architecture-Review.md).
Each step is self-contained and must leave the test suite green.

**Status legend:** ⬜ Not started · 🟡 In progress · ✅ Done · ⏭️ Deferred

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | **Error taxonomy + 3 outcome states** | ✅ Done | `errors.py` (`PyisommeError` tree, `MissingData`, `Status`), `Criterion.require*()`, 3-state `Criterion.calculate()`; `tests/test_errors.py` green |
| 2 | Normalization boundary at ingest | ✅ Done | `parse_xxx` split into `parse_header_and_data` + `resolve_time_axis`; assumptions recorded in the **standard** ISO/TS 13499 `Comments` field (prefix-marked, `get_normalization_notes`); fall-through explicit (TIRS=sample-index silent, else logged+recorded); non-numeric data → `MalformedFileError`; latent `n*dt` endpoint bug fixed; `tests/test_parsing.TestTimeAxisNormalization` green |
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

---

## Step 2 — Normalization boundary at ingest  ✅

**Goal:** resolve "conventions slightly differ" (implicit vs explicit reference channel,
missing `Time of first sample`, undeclared reference type, no timing at all) **once**, at
the parse boundary — and make every assumption *auditable* instead of a transient log
line. Stop the fall-through that silently produced a wrong (integer) time axis.

### Tasks
- [x] Split the old 80-line `parse_xxx` cascade into three focused units in `parsing.py`:
      `parse_header_and_data(text)` (structural), `resolve_time_axis(info, n, isomme)`
      (all convention handling, returns `(index, note)`), and a thin `parse_xxx` that wires
      them to a `Channel`.
- [x] Record each assumption into the **standard** ISO/TS 13499 `Comments` keyword
      (a repeatable free-text header field already used in .mme/.chn/.001), prefixed with
      `NORMALIZATION_COMMENT_PREFIX` and recoverable via `get_normalization_notes()`.
      Chosen over a custom key so exported files stay format-conformant; the note is
      *appended*, never clobbering an authored comment. `None` note ⇒ file fully specified
      the convention ⇒ nothing recorded.
- [x] Fix the integer-index fall-through: make it an **explicit, named** decision. TIRS
      (time-reference) channels legitimately use a sample index → silent; any other
      unresolved channel logs a `WARNING` **and** records the note.
- [x] Fail hard on structural corruption: non-numeric data → `MalformedFileError`
      (from Step 1's taxonomy) instead of a bare `ValueError`.
- [x] `tests/test_parsing.TestTimeAxisNormalization` — fixture-free coverage of every
      branch (declared/assumed implicit, sampling-interval-only, no-timing, TIRS, malformed).

### Design notes
- **Latent bug fixed for free:** the two *assumed*-implicit branches used
  `np.linspace(t0, n*dt, n)` — an endpoint of `n*dt` rather than `t0 + (n-1)*dt`, i.e. a
  subtly wrong sample step. Centralizing axis construction in one `implicit_axis(first,
  interval)` closure makes all paths use the single correct formula. Not exercised by the
  current fixtures (they all declare `Reference channel: implicit` with full timing, the
  already-correct path), so no test values shifted.
- **Behavior-preserving where it was already right:** fully-specified implicit/explicit
  channels return exactly the same index as before, with no `Normalization` key.
- **Did *not* canonicalize `info["Reference channel"]`** (e.g. writing back "implicit").
  That would change the write path's timing-reconstruction branch
  ([channel.py:412](../../pyisomme/channel.py#L412)); deferred to keep this step surgical.
- **Chose normalize-with-log over raise** for the no-timing fall-through: reference
  channels may simply not be parsed yet (channels are read in `.chn` order and a referent
  can appear later), so a missing reference is not necessarily malformed. `MalformedFileError`
  is reserved for genuinely unparseable *data*.

### Follow-on (later, incremental)
- The review's fuller `normalize(isomme)` pass (unit canonicalization, a test-level
  normalization log aggregated from per-channel notes) is still open; the per-channel note
  is the auditable substrate it would roll up.
