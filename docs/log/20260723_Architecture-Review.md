# pyisomme — Architecture Review & Improvement Proposal

*Generated 2026-07-23. Temporary working document — safe to delete.*

This review focuses on the two things you called out: (1) the code is "messy and not
very robust", with functions carrying multiple parameter/return types, and (2) how to
handle **incomplete / invalid / convention-divergent data** when building reports. The
second question gets its own section with a concrete recommendation, because it's a
design decision, not just a cleanup.

---

## 1. Executive summary

The domain model (`Isomme` → `Channel` → `Code`) is sound and the lazy-synthesis idea
in `get_channel` is genuinely clever. The problems are concentrated in a few places and
are mostly *structural*, not *conceptual*:

| # | Issue | Severity | Where |
|---|-------|----------|-------|
| A | `get_channel` is a ~670-line god-method mixing lookup, synthesis, and biomechanics | **High** | [isomme.py:491-1162](pyisomme/isomme.py#L491-L1162) |
| B | No coherent error strategy: `None`, `raise Exception`, `assert`, blanket `try/except`, and silent `NaN` all coexist and get conflated | **High** | everywhere; esp. [criterion.py:33-40](pyisomme/report/criterion.py#L33-L40), [parsing.py](pyisomme/parsing.py) |
| C | Union parameter/return types (`X \| None`, `int \| str`, `list \| Channel \| None`) push type-dispatch onto every caller | **High** | `get_data`, `__getitem__`, `cfc`, all `calculate_*` |
| D | `assert` used for validation *and* control flow — breaks under `python -O` | **Med** | [code.py:17](pyisomme/code.py#L17), [isomme.py:516](pyisomme/isomme.py#L516), [limits.py:47](pyisomme/limits.py#L47) |
| E | `channel_codes.xml` re-parsed from disk on **every** `Code.get_info/get_default_unit/is_valid` call | **Med** (perf) | [code.py:71,87,138](pyisomme/code.py#L71) |
| F | Read logic duplicated 3× (folder/zip/tar) with 6× copy-pasted encoding fallback | **Med** | [isomme.py:117-328](pyisomme/isomme.py#L117-L328) |
| G | `integrate`/`differentiate` mutate the *source* channel's `.info` (aliasing bug) | **Med** (bug) | [channel.py:368,386](pyisomme/channel.py#L368) |
| H | Criterion tree = 1472-line file of nested inner classes discovered by `dir()` reflection | **Med** | [frontal_50kmh.py](pyisomme/report/euro_ncap/frontal_50kmh.py), [criterion.py:49-72](pyisomme/report/criterion.py#L49-L72) |
| I | Copy-paste bugs in operator "Calculation History" strings (`+` logged as `-`, `*` as `/`) | **Low** | [channel.py:472-542](pyisomme/channel.py#L472-L542) |

Recommended order of attack (details in §7): **B/§4 first** (it answers your question and
de-risks everything else), then **C** (typing discipline), then **A** (split the
god-method), then the rest opportunistically.

---

## 2. The union-type / multiple-return-type problem (your "messy" complaint)

This is the concrete thing that makes the code feel slippery. A few representative cases:

```python
# isomme.py:475 — return type depends on the *type* of the argument
def __getitem__(self, index) -> list[Channel] | Channel | None:
    if isinstance(index, str):   return self.get_channels(index)   # list
    elif isinstance(index, int): return self.channels[index]       # Channel
    elif isinstance(index, slice): ...                             # list
    # falls through to None for anything else

# channel.py:307 — return is float OR ndarray depending on whether t is scalar
def get_data(self, t=None, ...) -> np.ndarray | float: ...

# channel.py:95 — one param is int XOR str, disambiguated by isinstance inside
def cfc(self, value: int | str, ...): ...

# calculate.py — pervasive: input Channel|None, output Channel|None or tuple|tuple-of-None
def calculate_neck_MOCx(...) -> tuple[Channel, Channel] | tuple[None, None]: ...
```

**Why it hurts:** every caller must re-discover the runtime type. `get_channel` returns
`Channel | None`, so the *entire* 670-line method and every criterion is written as
`x = get_channel(...); if x is not None: ...`. The `None` then flows into `calculate_*`,
which re-checks `if channel is None: return None`, which flows back into `get_channel`'s
`if all(c is not None ...)`. The None-plumbing *is* most of the code volume.

**Recommendations (low-risk, incremental):**

1. **Split by return type instead of overloading it.** `__getitem__` is the worst
   offender — string lookup returning a list while int returns a scalar is a footgun.
   Keep `iso[0]`/`iso[0:3]` as sequence access only; route code-pattern lookup through
   the already-existing `get_channel`/`get_channels`. (Or at minimum, make the string
   case return a single `Channel` to match `get_channel`, and document it.)

2. **`get_data` — give scalar and vector their own names.** `get_value(t) -> float` and
   `get_data() -> np.ndarray`. The `@overload` stubs already admit the type is
   context-dependent; splitting removes the union at the source. (Lower priority — the
   overloads at least make it tolerable today.)

3. **`cfc(value: int | str)` — accept one type.** Filter class is the domain concept
   ("A"/"B"/"C"/"D"); make `cfc(filter_class: str)` and add a separate
   `cfc_hz(freq: float)` if the numeric path is actually used. The `int↔str` cross-mapping
   table (channel.py:116-142) then collapses to one direction.

4. **The big one — replace `Channel | None` with a typed "absent channel".** See §4;
   this single change removes most of the union noise in `calculate.py` and `get_channel`.

---

## 3. `get_channel`: the god-method

[isomme.py:491-1162](pyisomme/isomme.py#L491-L1162) does **three unrelated jobs** in one
680-line `for`/`if` cascade:

1. **Lookup & matching** (fnmatch against existing channels).
2. **Lazy synthesis policy** (filter → calculate → differentiate → integrate, in order).
3. **The biomechanics themselves** — BrIC, HIC, DAMAGE, NIJ, VC, tibia index, IR-TRACC
   geometry, THOR PCA, min/max-of-left-right, etc. Each is a hand-inlined `if
   code_pattern.main_location == "..." and ...:` block.

Problems:
- **Domain knowledge is embedded in a lookup method.** Adding a criterion means editing
  this cascade *and* `calculate.py`. The CLAUDE.md even documents this as the intended
  extension point — which is exactly the smell.
- **Massive duplication.** The `filter_class == "X"` vs. `else` branches (e.g. VC at
  isomme.py:674-835) are near-identical, differing only in "take single peak value" vs
  "take max-abs over time". The min/max-of-left-and-right pattern is copy-pasted ~10×
  (SHLD, ACTB, FEMR, KNSL, TIBI, TIIN, FOOT, ABDO...).
- **Ordering is implicit.** Which synthesis wins is encoded purely by source order.

**Recommendation — a registry of "channel providers":**

Turn each synthesis block into a small, self-describing provider object and iterate a
registry instead of a 680-line `if`-cascade:

```python
class ChannelProvider:
    """Knows how to synthesize one derived channel from others."""
    def matches(self, code: Code) -> bool: ...
    def required(self, code: Code) -> list[str]:   # the code patterns it needs
        ...
    def build(self, iso: "Isomme", code: Code) -> Channel:  # raises Absent if inputs missing
        ...

PROVIDERS: list[ChannelProvider] = [
    ResultantProvider(), BricProvider(), HicProvider(), DamageProvider(),
    MinMaxPairProvider("SHLD", ..., agg="max_abs"),   # the ~10 copies collapse to config
    MinMaxPairProvider("FEMR", ..., agg="min"),
    ...
]
```

`get_channel` then becomes ~30 lines: try existing → try filter → walk `PROVIDERS` for
the first whose `matches` is true → differentiate/integrate. Benefits:
- The min/max-of-pair duplication becomes **one parameterized provider** with a config
  row per body region.
- Each provider's `required()` gives you the "what inputs does this need" list *for free*
  — which is the key to §4 (missing-data handling) without writing redundant requirements.
- New criteria = append a provider; no surgery on a giant method.

This is a big refactor; do it **after** §4, and do it provider-by-provider so the test
suite stays green throughout.

---

## 4. The core question: incomplete / invalid / convention-divergent data

You framed the choice as:
> *define requirements (redundant, disliked) — or — fail hard and catch the errors.*

**There's a third option, and it's the right one here: model "data not available" as a
typed value that flows through the calculation, not as an exception and not as a
separately-declared requirement.** Below is why, and how.

### 4.1 What the code does today (the hidden third thing — done badly)

Right now missing data is represented **three incompatible ways at once**, and they get
conflated:

- `get_channel` returns **`None`** when a signal is absent.
- `calculate_*` re-propagates `None`, or raises on bad input.
- `Criterion.calculate()` wraps everything in a **blanket `except Exception`**, sets
  `status = False`, logs, and moves on ([criterion.py:33-40](pyisomme/report/criterion.py#L33-L40)):

```python
def calculate(self) -> None:
    try:
        self.calculation()
        self.status = True
    except Exception as error_message:      # swallows EVERYTHING
        logger.exception(...)
        self.status = False
```

- The unset `value`/`rating` stay **`np.nan`** and render silently in the report.

So a missing channel, a genuine bug (typo, unit mismatch, `argmax` of empty array), and a
legitimately-NaN result **all look identical downstream**: `status=False`, `NaN` in the
slide. You cannot tell "we didn't have the chest deflection sensor" from "the chest
criterion has a bug". That's the real robustness problem — not that errors happen, but
that *you can't distinguish them*.

### 4.2 The idea: three outcomes, not two

Classify every criterion/channel result into exactly one of three states:

| State | Meaning | Where it comes from | Report shows |
|-------|---------|---------------------|--------------|
| **OK** | value computed | normal path | the value + rating |
| **N/A** | a *required input was absent* — expected, not a bug | a needed channel/info missing | "n/a — missing `?3CHST...`" |
| **ERROR** | an *unexpected* failure — a bug or corrupt input | any real exception | loud red marker + traceback |

The trap today is that N/A and ERROR are collapsed. Separating them gives you the
graceful degradation of "fail soft" for the genuinely-incomplete case **and** the
fail-hard visibility for real bugs — simultaneously. No redundant requirement lists.

### 4.3 Why "requirements" feel redundant — and how to get them for free

Your objection to declaring requirements is correct: a requirement list like
`needs = ["?3HEAD...ACRA", ...]` just *duplicates* the `get_channel(...)` calls the
calculation already makes. So don't declare them — **derive them from the act of
fetching**. Introduce a `require()` accessor that records the request and short-circuits
to N/A when the channel is absent:

```python
class MissingData(Exception):
    """Expected absence of an input. NOT a bug. Carries what was missing."""
    def __init__(self, code_pattern): self.code_pattern = code_pattern

class Criterion:
    def require(self, *code_patterns) -> Channel:
        ch = self.isomme.get_channel(*code_patterns)
        if ch is None:
            raise MissingData(code_patterns)     # names the exact missing input
        return ch

    def calculate(self):
        try:
            self.calculation()
            self.status = Status.OK
        except MissingData as m:
            self.status = Status.NA               # expected — render "n/a"
            self.na_reason = m.code_pattern
            logger.info(f"{self}: n/a, missing {m.code_pattern}")
        except Exception:
            self.status = Status.ERROR            # unexpected — surface loudly
            logger.exception(f"{self}: computation error")
```

Then a criterion body reads naturally, and its "requirements" *are* the code:

```python
def calculation(self):
    head = self.require(f"?{p}HEAD??00??ACRA")    # if absent -> N/A, names the channel
    self.value = np.max(np.abs(head.get_data(unit=g0)))
    ...
```

The requirement can never drift out of sync with the calculation, because it **is** the
calculation. This is essentially a lightweight `Maybe`/short-circuit pattern — the "third
idea" you were reaching for.

> If you later adopt the provider registry (§3), `provider.required(code)` gives the same
> information one level lower, so `get_channel` itself can return a *typed absence that
> knows which sub-input was missing* rather than a bare `None`.

### 4.4 Separate the two failure *classes* cleanly

Adopt a tiny exception hierarchy and a rule for each:

```python
class PyisommeError(Exception): ...            # base
class MalformedFileError(PyisommeError): ...   # structurally broken input  -> fail hard
class InvalidCodeError(PyisommeError): ...     # a 16-char code was required -> fail hard
class UnitError(PyisommeError): ...            # incompatible physical types -> fail hard
class MissingData(PyisommeError): ...          # expected absence            -> N/A, soft
```

- **Structural / programmer errors** (`MalformedFileError`, `InvalidCodeError`,
  `UnitError`) → raise, and **never blanket-catch**. The bulk reader
  ([isomme.py:1289-1292](pyisomme/isomme.py#L1289)) currently does
  `except Exception: logger.critical(e)` — that hides corrupt files as "one warning line".
  Catch a *specific* set there and let the rest crash, or at least count failures and
  report them at the end.
- **Expected absence** (`MissingData`) → the only thing the criterion loop soft-catches.

This is the concrete answer to *"fail hard and catch those errors"*: **fail hard on bugs,
never catch them; catch exactly one, well-named, expected condition.**

### 4.5 Handle "conventions slightly differ" at the boundary, once

"Data conventions differ" (implicit vs explicit reference channel, missing
`Time of first sample`, `g` vs `g0`, `NOVALUE`, ES-2 vs WorldSID naming) should be
normalized **once at ingest**, not re-discovered inside every criterion. `parsing.py`
already does this half-heartedly and *well* where it does — e.g.
[parsing.py:88-100](pyisomme/parsing.py#L88-L100) logs
`Assume 'Reference channel' = 'implicit'` and reconstructs the time axis. Make that a
deliberate, centralized **normalization layer**:

- One `normalize(isomme)` pass after read that: resolves the time axis, canonicalizes
  units, and records every assumption it made into `test_info` (an auditable
  "normalization log").
- Downstream, `Channel`/criteria may then assume a **known-normalized shape** and stop
  each re-handling convention drift.
- **Fail hard** on "structurally unparseable"; **normalize + log** on "parseable but
  non-canonical"; **N/A** on "canonical but absent". Three layers, three policies.

Note the current fall-through in `parse_xxx`: if no reference-channel info matches, it
returns a `Channel` with a **plain integer index** (isomme.py-equivalent
[parsing.py:113-118](pyisomme/parsing.py#L113-L118)) — a silently-wrong time axis. That's
exactly a case that should either normalize-with-a-logged-assumption or raise
`MalformedFileError`, not quietly produce a bad channel.

### 4.6 Net recommendation

> Stop treating missing data as *either* a requirement-to-declare *or* an
> error-to-catch. Treat it as a **typed value** (`MissingData` / a typed absent channel)
> that (a) is produced automatically by the act of fetching an input, (b) renders as
> "n/a — missing X" in the report, and (c) is kept strictly separate from real
> exceptions, which you fail hard on and never blanket-catch. Normalize convention
> differences once, at the ingest boundary, logging every assumption.

This gives you robustness *and* graceful degradation with **zero redundant requirement
declarations**.

---

## 5. Other robustness issues (smaller, mostly local fixes)

**D — `assert` for validation & control flow.** `Code.__new__` validates via `assert`
([code.py:17](pyisomme/code.py#L17)); `get_channel` then does
`try: Code(...) except AssertionError: continue` ([isomme.py:514-517](pyisomme/isomme.py#L514)).
Under `python -O` assertions are stripped, so **both the validation and this control flow
silently vanish** — invalid codes would sail through. Replace with a raised
`InvalidCodeError` and catch that. Same for `Limit.__init__` argcount assert
([limits.py:47](pyisomme/limits.py#L47)) and `Limits.get_limits` empty-check
([limits.py:129](pyisomme/limits.py#L129)).

**E — XML re-parsed every call.** `Code.get_info`, `get_default_unit`, and `is_valid`
each `ET.parse(channel_codes.xml)` on every invocation
([code.py:71,87,138](pyisomme/code.py#L71)). In a report these run thousands of times.
Parse once at import into a module-level cached structure (or `@functools.lru_cache` on a
loader). Pure win, no API change.

**G — info aliasing bug.** `Channel.differentiate`/`integrate` do `new_info = self.info`
then `new_info.update(...)`; since `Info.update` mutates in place and returns self
([info.py:29-41](pyisomme/info.py#L29)), this **mutates the source channel's info**.
`cfc` gets this right with `copy.deepcopy(self.info)` — the two derivation methods should
too. ([channel.py:368,386](pyisomme/channel.py#L368))

**I — wrong Calculation-History strings.** `__add__` logs `f"{self.code} - {other.code}"`
(should be `+`), `__mul__` and `__truediv__` both log `/`
([channel.py:472-542](pyisomme/channel.py#L472)). Cosmetic, but it lands in exported
metadata, so it's misleading provenance. Also `__mul__`/`__truediv__` skip the
`physical_type` compatibility check that `__add__`/`__sub__` perform — intentional for
mul/div, but worth a comment.

**F — read/write duplication.** `read_from_mme` / `read_from_zip` / `read_from_tarfile`
are ~90% identical, differing only in the file-access primitive (fs glob vs
`zipfile.namelist` vs `tarfile.getnames`) and the open call. The utf-8→iso-8859-1
fallback is copy-pasted 6 times. Extract a tiny `ArchiveSource` interface
(`list() -> names`, `open(name) -> bytes`) with three implementations, plus one
`read_text_with_fallback(bytes) -> str` helper. Collapses ~210 lines to ~70 and means a
parser fix lands everywhere at once.

**Bulk-read swallows everything.** `read(*paths)` at
[isomme.py:1289-1292](pyisomme/isomme.py#L1289) does `except Exception: logger.critical`.
At minimum, collect `(path, exception)` pairs and return/print a summary so a user reading
50 files learns that 7 failed and why — rather than scrolling logs.

**`export_pptx` infinite retry.** [report.py:82-88](pyisomme/report/report.py#L82) loops
forever on `PermissionError` (file open in PowerPoint) with `time.sleep(3)`. Fine for
interactive use, but give it a max-retries + clear message so a locked file in CI doesn't
hang a pipeline.

---

## 6. Report / Criterion architecture

The criterion tree is expressive but pays for it: **`frontal_50kmh.py` is 1472 lines** of
deeply nested inner classes, and the tree is discovered *reflectively* by scanning
`dir(self)` for `Criterion` instances ([criterion.py:49-72](pyisomme/report/criterion.py#L49),
[report.py:58](pyisomme/report/report.py#L58)). Consequences:

- **Traversal logic is re-implemented three times** (`get_subcriterion`,
  `get_subcriteria`, `print_results`) — each re-derives children via `dir()`. Give
  `Criterion` an explicit `children: list[Criterion]` (populated in `__init__`) and write
  traversal once.
- **`dir()`-based discovery is order-nondeterministic and fragile** — any stray attribute
  that happens to be a `Criterion` joins the tree. Explicit children remove the surprise.
- **Position/occupant boilerplate is duplicated** (the `p_driver`/`p_front_passenger`
  logic in [frontal_50kmh.py:67-78](pyisomme/report/euro_ncap/frontal_50kmh.py#L67) recurs
  across protocols). Pull "occupant at position p" into a shared mixin/helper.
- **Consider data-driven criteria.** Many leaf criteria are "fetch channel X, take
  max/HIC/a3ms, rate against limit set L". Those could be table/config rows rather than a
  class each — reserving hand-written `calculation()` for the genuinely bespoke ones.
  Combined with §4's `require()`, a leaf becomes ~3 lines.

`MetaReport.calculate` ([report.py:96-99](pyisomme/report/report.py#L96)) doesn't return
`self` while `Report.calculate` does — small consistency nit in a fluent API.

---

## 7. Suggested roadmap (incremental, test-green throughout)

1. **Error taxonomy + three-state outcomes (§4).** Add `PyisommeError` hierarchy +
   `MissingData` + `Status{OK,NA,ERROR}` + `Criterion.require()`. Migrate the criterion
   loop off blanket-catch. *Highest value, answers your question, low blast radius.* Do
   this first — everything else gets easier once absence is typed.
2. **Normalization boundary (§4.5).** Centralize the convention-handling already scattered
   in `parsing.py`; log assumptions; make `parse_xxx`'s integer-index fall-through either
   normalize-with-log or raise.
3. **Kill `assert`-as-validation + cache the XML (§5 D, E).** Tiny, high-safety, and E is
   a free speedup for every report.
4. **Fix the aliasing + history-string bugs (§5 G, I).** One-liners.
5. **De-duplicate the readers behind an `ArchiveSource` (§5 F).**
6. **Tighten union types (§2):** `__getitem__`, `cfc`, `get_data` split.
7. **Refactor `get_channel` into a provider registry (§3)** — biggest structural win,
   done provider-by-provider once absence is typed (step 1) so each move is verifiable.
8. **Explicit `Criterion.children` + shared occupant helper (§6).**

Steps 1–4 are a few days and remove most of the "not robust" feeling. 5–8 are the deeper
"messy" cleanup and can proceed opportunistically as you touch each area.

---

### One-line takeaway
The architecture isn't wrong — it's *under-typed and under-layered*. Give "missing data"
a type (not an exception, not a redundant requirement), give errors a hierarchy you never
blanket-catch, normalize conventions once at the edge, and the god-method plus the union
soup become mechanical follow-on cleanups.
