# pyisomme — Refactor Implementation Plan

Tracks the incremental rollout of the improvements in [20260723_Architecture-Review.md](20260723_Architecture-Review.md).
Each step is self-contained and must leave the test suite green.

**Status legend:** ⬜ Not started · 🟡 In progress · ✅ Done · ⏭️ Deferred

| # | Step | Status | Notes |
|---|------|--------|-------|
| 1 | **Error taxonomy + 3 outcome states** | ✅ Done | `errors.py` (`PyisommeError` tree, `MissingData`, `Status`), `Criterion.require*()`, 3-state `Criterion.calculate()`; `tests/test_errors.py` green |
| 2 | Normalization boundary at ingest | ✅ Done | `parse_xxx` split into `parse_header_and_data` + `resolve_time_axis`; assumptions recorded in the **standard** ISO/TS 13499 `Comments` field (prefix-marked, `get_normalization_notes`); fall-through explicit (TIRS=sample-index silent, else logged+recorded); non-numeric data → `MalformedFileError`; latent `n*dt` endpoint bug fixed; `tests/test_parsing.TestTimeAxisNormalization` green |
| 3 | **Kill `assert`-as-validation + cache `channel_codes.xml`** | ✅ Done | `Code.__new__` → `InvalidCodeError` (survives `python -O`); `get_channel`/`get_channels` catch `InvalidCodeError`; `limits.py` validation asserts → `ValueError`; `channel_codes.xml` parsed once at import (`_CHANNEL_CODES_ROOT`); `tests/test_code.py` updated |
| 4 | **Fix aliasing + calc-history bugs** | ✅ Done | `integrate`/`differentiate` now `deepcopy(self.info)` (was mutating the source channel); `__add__` history logs `+` (was `-`), `__mul__` logs `*` (was `/`); mul/div physical-type skip documented; `tests/test_channel.py` green |
| 5 | **De-duplicate readers behind `ArchiveSource`** | ✅ Done | new `sources.py` (`ArchiveSource` + `FolderSource`/`ZipSource`/`TarSource`, one `read_text_with_fallback`); `read_from_*` collapse to thin wrappers over one `_read_from_source`; ~210 lines → ~100; byte-identical reads verified vs baseline; `tests/test_sources.py` green |
| 6 | **Tighten union types** | ✅ Done | `__getitem__` explicit `TypeError` for unsupported keys (kept int→Channel / slice→list / str→get_channels shorthand by choice); `cfc(filter_class)` + `cfc_hz(freq)` split w/ deprecation shim, `method: Literal`; `get_data`→`np.ndarray` (the `\|float` was never real) + new `get_value(t)→float`; fixes latent SAE info-aliasing bug; `tests/test_channel.py` +7 green |
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

---

## Step 3 — Kill `assert`-as-validation + cache `channel_codes.xml`  ✅

**Goal:** stop using `assert` for input validation and control flow (assertions are stripped
under `python -O`, so both the check *and* the `except AssertionError` control flow silently
vanish — invalid codes would sail straight through). And stop re-parsing the packaged
`channel_codes.xml` from disk on every code lookup.

### Tasks
- [x] `Code.__new__`: `assert re.fullmatch(...)` → raise `InvalidCodeError` (Step 1's
      taxonomy) with a descriptive message. Now enforced identically with/without `-O`.
- [x] `Isomme.get_channel`/`get_channels`: the two `try: Code(...) except AssertionError:
      continue` sites now catch `InvalidCodeError` (import added to `isomme.py`).
- [x] `code.py`: parse `channel_codes.xml` **once** at import into module-level
      `_CHANNEL_CODES_ROOT`; `get_info`/`get_default_unit`/`is_valid` read the cached root
      instead of `ET.parse(...)` per call. Pure speedup, no API change (a report triggers
      thousands of these lookups).
- [x] `limits.py`: replace validation asserts with explicit raises — `Limit.__init__`
      func-arity check and the two `get_limits`/`get_limit_ratings` "No limits found" /
      "rating defined" checks → `ValueError`.
- [x] `tests/test_code.py`: `assertRaises(AssertionError)` → `assertRaises(InvalidCodeError)`.

### Design notes
- **`InvalidCodeError` subclasses `ValueError`** (see `errors.py`), so any latent
  `except ValueError` around code construction keeps working; the `except AssertionError`
  sites were the only catchers of the old behavior and both were migrated.
- **No import cycle:** `errors.py` imports only `enum`; `code.py`/`limits.py` importing it is
  safe within the `__init__.py` load order.
- **`limits.py` uses `ValueError`, not `MissingData`.** "No limits found" is currently a
  loud failure (was `AssertionError`, caught by `Criterion.calculate`'s broad `except` →
  `ERROR`). `ValueError` preserves that exact outcome while being `-O`-safe. Reclassifying
  "no matching limit" as soft `NA` is an intentional *later* migration (Step 1 follow-on),
  not smuggled into this surgical step.
- **Left out of scope:** the `assert`s in `calculate.py` (dummy-type / method preconditions)
  and `limits.get_full_limits` internal invariants are domain-invariant guards, not
  external-input validation; deferred to keep this step focused on the `-O` foot-guns the
  review named (§5-D/E).

---

## Step 4 — Fix aliasing + calc-history bugs (§5-G, §5-I)  ✅

**Goal:** two one-liner correctness/provenance bugs. (1) `differentiate`/`integrate`
aliased and mutated the *source* channel's `.info`; (2) operator "Calculation History"
strings recorded the wrong symbol, landing misleading provenance in exported metadata.

### Tasks
- [x] `Channel.differentiate`/`integrate`: `new_info = self.info` → `copy.deepcopy(self.info)`.
      `Info.update` mutates in place and returns self, so the alias silently added a
      `Dimension` entry to the *source* channel on every derivation. `cfc` already did this
      correctly with `deepcopy`; the two derivation methods now match.
- [x] `__add__`: history string `f"{self.code} - {other.code}"` → `+` (all three branches:
      compatible-unit, incompatible-unit, scalar).
- [x] `__mul__`: history string `f"{self.code} / {other.code}"` → `*` (both branches).
- [x] `__truediv__` already logged `/` correctly — left unchanged.
- [x] Added a comment on `__mul__` documenting the *intentional* skip of the `physical_type`
      compatibility check that `__add__`/`__sub__` perform (mul/div across physical types is
      valid and the result unit is computed from operands).
- [x] `tests/test_channel.py`: `test_calculation_history_add_mul` (asserts the exact history
      tuple for `+ - * /`, both channel and scalar operands) and
      `test_{differentiate,integrate}_does_not_mutate_source_info` (source `.info` unchanged
      after derivation).

### Design notes
- **Operator methods were never affected by the aliasing bug:** they build info via
  `self.info + [...]`, which is `list.__add__` → a *new* list, not an in-place mutation. So
  only the two `update()`-based derivation methods needed the `deepcopy` fix.
- **`self.info + [...]` returns a plain `list`, not an `Info`** — pre-existing behavior,
  unchanged here; the `Channel` constructor accepts either, so out of scope for this
  surgical step.

---

## Step 5 — De-duplicate readers behind `ArchiveSource` (§5-F)  ✅

**Goal:** `read_from_mme` / `read_from_zip` / `read_from_tarfile` were ~90% identical,
differing only in the file-access primitive (fs glob vs `zipfile.namelist`/`open` vs
`tarfile.getnames`/`extractfile`); the utf-8→iso-8859-1 fallback was copy-pasted 6×. A
parser fix had to be applied in three places.

### Tasks
- [x] New `pyisomme/sources.py`: abstract `ArchiveSource` (`names() -> list[str]`,
      `read_bytes(name) -> bytes`, plus `read_text`/`close`/context-manager sugar) with
      three backends — `FolderSource` (rglob, POSIX-relative names), `ZipSource`,
      `TarSource`. One `read_text_with_fallback(bytes) -> str` replaces the 6 inline
      try/except decode blocks.
- [x] One `Isomme._read_from_source(source, *patterns, mme_name=None)` holds the entire
      MME→CHN→channel-iteration logic. `read_from_zip`/`read_from_tarfile` become
      two-liners that build the source in a `with`; `read_from_mme` builds a
      `FolderSource(mme_path.parent)` and passes the known `mme_name` (fs case already
      knows its .mme, so it skips the search). `read_from_folder`/`_chn`/`_xxx` still
      resolve the .mme then delegate — unchanged.
- [x] Removed now-unused `zipfile`/`tarfile` imports from `isomme.py`.
- [x] `tests/test_sources.py` — fixture-free: encoding fallback (utf-8 + 0xFC→iso-8859-1)
      and all three backends round-tripping a synthetic 3-member container.

### Design notes
- **Behavior-preserving, verified byte-for-byte:** captured a pre-refactor baseline
  (sorted channel-code hash per source) and confirmed folder/zip/tar/tar.gz reads of
  `data/nhtsa/11391` are identical after — plus all NHTSA zip/folder fixtures still read
  with matching channel counts. (The zip fixture legitimately differs from the folder
  fixture in *content* — `H3` vs `00` fine-location — which is a fixture artifact, not
  reader logic; each source still reads exactly its own bytes.)
- **Unified match patterns via `fnmatch.filter`:** `str(Path(...).joinpath(...))` +
  `fnmatch.filter` is what the zip/tar readers already did and works cross-platform
  because `fnmatch` normalizes case *and* path separators (`normcase`). The three readers'
  slightly-divergent CHN/xxx patterns were consolidated to the more precise
  `<mme-parent>/[cC]hannel*/<test>.chn` and `<chn-parent>/<test>.<nnn>` forms; identical
  results on every fixture since file stems equal the test number there.
- **Resource cleanup:** `ZipSource`/`TarSource` now close their handle via the
  context-manager wrappers — the old `read_from_zip` never closed its `ZipFile`.
- **Minor perf trade-off:** `FolderSource.names()` does one `rglob("*")` up front instead
  of per-pattern globs. Negligible next to reading hundreds of channel files, and it keeps
  the backend interface uniform.

---

## Step 6 — Tighten union types (§2)  ✅

**Goal:** kill the three functions whose *return* or *parameter* type is decided by an
`isinstance` check inside, forcing every caller to re-discover the runtime type
(`__getitem__ -> list | Channel | None`, `cfc(value: int | str)`,
`get_data -> np.ndarray | float`).

### Tasks
- [x] **`Isomme.__getitem__`** — the silent `None` fall-through for unsupported key types
      is replaced by an explicit `TypeError`. Return type annotation narrowed to
      `Channel | list[Channel]` (was `... | None`). The `str` code-pattern shorthand
      (`iso["<pattern>"]` -> `get_channels`, a list) was **kept by owner preference**: the
      review flagged the key-type-dependent return (`int`->Channel vs `str`->list) as a
      footgun, but the ergonomic shorthand is wanted; the docstring now spells out the
      return-type-by-key-type behavior and points at `get_channel` for single-match intent.
- [x] **`Channel.cfc`** split by the two domain concepts: `cfc(filter_class: str)`
      ("0"/"A"/"B"/"C"/"D") and `cfc_hz(freq: float)` (cutoff in Hz), sharing a private
      `_apply_cfc(cfc, filter_class, method, return_copy)` core. The bidirectional
      class↔freq mapping collapses to one dict `_FILTER_CLASS_CFC`; unknown class →
      `ValueError`. Internal callers (`get_channel` filter step, `Isomme.cfc` wrapper)
      pass a filter-class letter unchanged. CLI `--cfc` now routes a numeric arg to
      `cfc_hz` (its help always promised "Hz or ISO-Code", but numeric strings previously
      hit `NotImplementedError`). `method` is annotated `Literal["ISO-6487", "SAE-J211-1"]`
      (class-level `_CFC_METHODS` alias); the `else: raise NotImplementedError` stays as the
      runtime backstop. `filter_class` is left as `str` **on purpose** — internal callers
      pass a computed slice (`code_pattern[-1]`), so a `Literal` there would be a false
      positive, and the runtime `_FILTER_CLASS_CFC` check already rejects bad classes with a
      descriptive `ValueError`.
- [x] **`Channel.get_data`** return type corrected to `np.ndarray` and the two `@overload`
      stubs dropped (`overload` import removed). Added **`get_value(t) -> float`** for the
      single-sample case; migrated the two internal scalar callers (`auto_offset_y`,
      `adjust_to_range`).
- [x] `tests/test_channel.py` +7: cfc/cfc_hz equivalence, non-standard-freq → "S",
      unknown-class `ValueError`, numeric-cfc deprecation+delegation, cfc no-mutate (both
      methods), `get_value`/`get_data` types, `__getitem__` sequence-only + str `TypeError`.

### Design notes
- **The `get_data -> | float` union was a lie, not a real narrowing.** `scipy`'s
  `interp1d(...)(t)` returns a (0-d) `np.ndarray` even for scalar `t`, so `get_data` has
  *always* returned an ndarray. Correcting the annotation to `np.ndarray` removes the union
  **with zero call-site migration** — the ~60 `get_data(t=...)` sites keep working
  byte-identically (a 0-d array broadcasts wherever a float did). `get_value` is the
  additive, opt-in scalar path (`float(get_data(...))`), not a forced rename. The review
  itself flagged the full rename as *lower priority* ("the overloads make it tolerable"),
  so broad migration is deliberately **deferred**; only the two sites the type-checker
  flagged as wanting a scalar were moved.
- **`cfc` keeps a backward-compat shim, by design.** The primary signature is now
  `cfc(filter_class: str)`, but a non-`str` arg (the old `cfc(1000)` / `cfc(60)` used in
  the docs notebooks and by any downstream code) emits a `DeprecationWarning` and delegates
  to `cfc_hz`. This tightens the *documented* type while giving a real migration path
  instead of a hard break — the notebooks still run.
- **Latent aliasing bug fixed for free (same class as Step 4 §5-G).** The `SAE-J211-1`
  branch did `info = self.info` then `info.update(...)`, mutating the *source* channel's
  info on every filter (the `ISO-6487` branch already `deepcopy`'d). Consolidating the tail
  into `_apply_cfc` and using `deepcopy` uniformly fixes it; covered by
  `test_cfc_does_not_mutate_source_info` over both methods.
- **Removing string indexing is a (small) behavior change, but a safe one:** no in-repo
  caller used `iso["<pattern>"]` (grep-verified), the review explicitly recommends routing
  pattern lookup through `get_channel`/`get_channels`, and the raised `TypeError` names the
  replacement rather than failing silently.

### Follow-on (later, incremental)
- The broader `get_data(t=scalar)` → `get_value` migration across `calculate.py` /
  `isomme.py` (~60 sites) can proceed opportunistically as those areas are touched; the
  honest `np.ndarray` annotation already removed the misleading union.
- `calculate.py`'s pervasive `Channel | None` in/out unions (§2.4) are the larger remaining
  union-soup, addressed structurally by Step 7's provider registry (typed absence).
