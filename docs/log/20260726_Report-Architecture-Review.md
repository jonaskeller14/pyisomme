# `pyisomme.report` — Architecture Review & Improvement Proposals

Status: review of the current state on branch `dev` (2026-07-26).
Written into `docs/` (the repo has `docs/`, not `doc/`).

Reference implementations used as "good state" baseline, as requested:

- [`pyisomme/report/euro_ncap/frontal_50kmh.py`](../../pyisomme/report/euro_ncap/frontal_50kmh.py) (1472 lines)
- [`pyisomme/report/euro_ncap/frontal_mpdb.py`](../../pyisomme/report/euro_ncap/frontal_mpdb.py) (1280 lines)

Design goals extracted from the request (used as evaluation criteria throughout):

| # | Goal |
|---|------|
| **G1** | Report definitions stay **slim** and readable — translating a requirement PDF into a `Report` should be cheap. |
| **G2** | Definitions must be **verifiable without reading framework code** — a reviewer compares the module against the PDF. |
| **G3** | **Typing + linting** must catch as many errors as possible *before* runtime. |
| **G4** | **Nesting of criteria stays** — it carries the protocol's body-region grouping and drives the PPTX visualisation. |
| **G5** | **Maximum flexibility** — special load cases must remain expressible. |
| **G6** | **Reuse of criteria across reports** (especially inside a protocol family such as Euro-NCAP). |
| **G7** | Keep existing features: protocol versions, limits→plot bars, `MetaReport` composition, `n/a` handling. |
| **G8** | **Manual inputs**: facts that cannot be read from curve data (video observations, measurements, engineering judgement) are set on the criterion tree *between* construction and `calculate()`. |
| **G9** | **NaN propagation is a deliberate policy**, not a defect: a missing input must poison the rating rather than yield a plausible-looking score. `nan`-tolerant aggregation is a rare, conscious exception. |

Regarding **G8**, the supported workflow is:

```python
report = pyisomme.report.euro_ncap.frontal_50kmh.EuroNCAP_Frontal_50kmh([v1, v2])

# Manual inputs — information not derivable from curve data (optional)
report.criterion_overall[v1].criterion_door_opening_during_impact.number_of_door_openings_during_impact = 1
report.criterion_overall[v2].criterion_driver.criterion_femur.criterion_submarining.submarining = True

report.calculate()
```

Regarding **G9**: `np.min`/`np.sum`/`np.max` (NaN-propagating) are used **134** times against **5** uses of the `nan*` family. The single `np.nanmean` (`frontal_50kmh.py:89`, occupant average) is the deliberate exception that allows a development run with only one instrumented dummy — and it is self-documenting there, because the other occupants' ratings are visibly `nan`. Any refactor must preserve this asymmetry, and should make the exceptions *more* visible, not less.

---

## 1. Current architecture (as built)

```
Report                      isomme_list, title, protocol/protocols,
 ├─ limits: {Isomme: Limits}          ← flat, per-test; feeds plot limit bars
 ├─ criterion_overall: {Isomme: Criterion_Overall}
 │    └─ Criterion (nested inner classes, arbitrarily deep)
 │         ├─ name / value / rating / color / status / na_reason
 │         ├─ limits: Limits           (also mirrored into Report.limits)
 │         ├─ channel: Channel | None
 │         └─ calculation()            ← protocol logic, hand-written
 ├─ pages: [Page]                      ← each page re-states parts of the tree
 ├─ calculate()        → criterion_overall[isomme].calculate() per test
 └─ export_pptx()      → page.construct(presentation) per page

MetaReport(Report)          reports: [Report]; composes pages of sub-reports
```

Supporting pieces: `Limit`/`Limits` ([`pyisomme/limits.py`](../../pyisomme/limits.py)) match limit curves to channels by code pattern and produce `rating`/`color`; `Page_*` ([`pyisomme/report/page.py`](../../pyisomme/report/page.py)) render tables/charts/plots via `Plot_*`; `MissingData`/`Status` ([`pyisomme/errors.py`](../../pyisomme/errors.py)) model "input absent" vs "bug".

### 1.1 What works well (keep it)

1. **Nesting via inner classes matches the domain.** The class tree *is* the assessment tree (Overall → Occupant → Body region → Criterion → Modifier). Reading `frontal_50kmh.py` top-down mirrors the AoP chapter structure. This is the right core decision and should be preserved (G4).
2. **Plain Python everywhere.** Every special case in the protocols so far was expressible: capping at `-inf`, modifiers that add negative points, cross-occupant `min()` in MPDB, downscaling in Far-Side, dynamic per-channel criteria in the correlation report. That flexibility (G5) must not be traded away.
3. **Limits are declarative and dual-purpose** — one declaration produces both the rating and the coloured bars in the plots. Good separation of "threshold data" from "logic".
4. **`Status` / `MissingData` / `require_channel`** is the right model for "n/a because the test lacks the channel" vs. "bug". The infrastructure is in place and well documented.
5. **`MetaReport`** gives a working composition mechanism for protocol families.
6. **Manual inputs need no framework at all** (G8). Because criteria are eagerly constructed plain objects with class-attribute defaults, a user can reach into the tree and override anything before `calculate()`. This is a genuinely good property — no registration, no schema, works for any new field — and any redesign must keep the tree eagerly constructed and addressable. The weaknesses are in *safety* and *discoverability* (F13–F15), not in the concept.
7. **NaN propagation as the default failure mode** (G9) is the right call for a rating tool: `np.min([4, nan])` → `nan` means "this test cannot be scored", which is exactly what should happen when a channel is mislabelled or absent. Report authors get a loud, visible hole instead of a silently optimistic number.
8. `Report`/`Criterion`/`Page` are small (114 / 112 / 362 lines) — the framework itself is not the problem; the *definition ergonomics* are.

### 1.2 Quantitative picture

Measured over `pyisomme/report/` (7619 lines total):

| Metric | Count |
|---|---|
| `class Criterion*` definitions | 257 |
| `def __init__(self, report, isomme, p)` boilerplate blocks | 180 |
| `extend_limit_list([...])` blocks | 104 |
| Individual `Limit*(...)` rows | 423 |
| Constant limits of shape `func=lambda x: <number>` | 366 |
| `self.report.criterion_overall[...]` access chains | 530 |
| Deep cross-report class references (`EuroNCAP_Frontal_50kmh.Criterion_Overall....`) | 13 |
| `require_channel` / `require_test_info` uses **in report definitions** | **0** |
| Manual-input attributes (user-settable class attrs on criteria, G8) | ~59 across 14 modules |
| NaN-propagating aggregations (`np.min`/`np.sum`/`np.max`) | 133 |
| NaN-tolerant aggregations (`np.nanmin`/`nanmax`/`nanmean`) | 5 |

In `frontal_50kmh.py`, roughly **60 % of the lines are wiring** (constructors, `self.p = p`, explicit child `.calculate()` calls, page-side path chains) and ~25 % are duplicated limit tables. The protocol content — thresholds, aggregation rules, modifiers — is maybe 15 % of the file.

---

## 2. Findings

Severity: **H** = actively causes silent wrong results or blocks G1–G3, **M** = significant friction, **L** = cleanup.

### F1 (H) — Sub-criteria are wired in four places; nothing checks consistency

For each child criterion the author must:

1. instantiate it in `__init__` (`self.criterion_neck = self.Criterion_Neck(report, isomme, p=self.p)`),
2. call `self.criterion_neck.calculate()` inside the parent's `calculation()`,
3. include `self.criterion_neck.rating` in the aggregation list,
4. repeat the full path in every `Page_*` that shows it.

Forgetting (2) yields `rating = nan`, which then propagates up the tree. The propagation itself is correct and wanted (G9) — the problem is that the resulting `nan` is **indistinguishable from the legitimate "data is missing" case**. Three very different situations produce the identical output today:

| Cause | Should be | Is |
|---|---|---|
| Channel genuinely absent from the test | `n/a`, naming the channel | bare `nan` |
| Author forgot to call `child.calculate()` | a wiring bug, must fail loudly | bare `nan` |
| Criterion raised an unexpected exception | `ERROR`, must fail loudly | bare `nan` (traceback in log only) |

Forgetting (3) — leaving a child out of the aggregation list — is worse still: it produces a *plausible* score with no `nan` anywhere, and nothing detects it. Forgetting (4) means the criterion is simply invisible in the PPTX.

None of this is detectable by a linter, a test, or a reviewer comparing against the PDF. This is the single largest obstacle to G2. Note the fix is **not** to suppress the `nan` — it is to make the *reason* for it traceable (P10) and to remove step (2) entirely (P1).

### F2 (H) — No type information on the hot path

- `Criterion.__init__(self, report, isomme: Isomme)` — `report` is untyped; all 180 subclass `__init__`s take untyped `report, isomme, p`.
- `Report.criterion_overall: dict[Isomme, Criterion]` — declared as base `Criterion`, so **all 530** accesses like
  `self.report.criterion_overall[isomme].criterion_driver.criterion_head.criterion_hic_15` are unchecked. A typo surfaces at runtime, and only when that specific page is constructed or that branch executes.
- `p` is `int` in ~10 signatures and untyped in ~170.
- No mypy/pyright configuration exists; ruff runs in CI with `continue-on-error: true`, so nothing is enforced (G3 currently unrealised).

### F3 (H) — `get_channel()` returns `Channel | None`, reports ignore it

61 sites do `self.isomme.get_channel(...).get_data(...)` directly. Consequences:

- A type checker would flag every one of them as `Optional` member access (so turning typing on today produces 61 errors).
- At runtime a missing channel raises `AttributeError`, which `Criterion.calculate()` catches in the broad `except Exception` branch → `Status.ERROR` + full traceback in the log, instead of the intended `Status.NA` + a clean "n/a (channel X missing)".
- `require_channel()` was built for exactly this and is used **zero** times outside `criterion.py`.

### F4 (H) — Channel code patterns are written twice per criterion and can drift

```python
self.extend_limit_list([
    Limit_G([f"?{self.p}NECKUP00??MOY?"], ...),   # pattern #1 (limits)
])
def calculation(self):
    self.channel = self.isomme.get_channel(f"?{self.p}NECKUP00??MOYB")   # pattern #2 (data)
```

If the two drift, `Limits.get_limits()` raises `ValueError: No limits found for channel ...` → `Status.ERROR`, or worse, matches a *different* limit set. With 104 limit blocks this is a standing risk and is invisible to review.

### F5 (H) — Limit tables contain hand-computed derived numbers

Euro-NCAP sliding scales are entered as six rows with manually interpolated intermediates:

```python
Limit_G([...], func=lambda x: 500.000, ...),   # from PDF
Limit_A([...], func=lambda x: 500.000, ...),   # from PDF
Limit_M([...], func=lambda x: 566.667, ...),   # = 500 + 1/3·(700−500)   ← derived
Limit_W([...], func=lambda x: 633.333, ...),   # = 500 + 2/3·(700−500)   ← derived
Limit_P([...], func=lambda x: 700.000, ...),   # from PDF
Limit_C([...], func=lambda x: 700.000, ...),   # capping, from PDF
```

The PDF states *two* numbers (higher-performance 500, lower-performance 700) plus a capping value; the module states *six*, four of which are typed by hand. Verifying 366 such constants against a PDF is exactly the effort the user wants to minimise (G1/G2). The same six-row block is copy-pasted per occupant, per report — the Neck `My`/`Fz`/`Fx` tables appear three times in `frontal_50kmh.py` alone, differing only in whether the capping row is present.

### F6 (M) — Discovery by `dir()` reflection is order-scrambling, partial, and untypable

`Criterion.get_subcriterion` / `get_subcriteria` / `Report.print_results` collect children via
`[getattr(self, a) for a in dir(self) if isinstance(getattr(self, a), Criterion)]`:

- `dir()` is **alphabetically sorted** → printed results and any tree walk do *not* follow protocol/definition order.
- `getattr` on every attribute name touches properties and is O(attributes) per node.
- Criteria stored in a **list** (the correlation report's `self.criteria`) are invisible to this walk — two different child mechanisms coexist.
- Reflection is opaque to type checkers by construction.

### F7 (M) — Pages restate the tree; page/criterion coupling is manual

`Page_Driver_Result_Values_Chart` and `Page_Driver_Values_Table` in `frontal_50kmh.py` contain the *same* 10-line criterion list, repeated again for front passenger and rear passenger — 6 identical-shaped blocks, 60 long chains, all unchecked. Plus `Report.export_pptx()` re-invokes `page.__init__(page.report)` before `construct()` (with a `# TODO: TEST!` comment), which forces every `Page.__init__` to be idempotent and runs page-building code twice.

### F8 (M) — Cross-report reuse is expensive, so authors copy-paste instead

Reuse currently looks like:

```python
self.criterion_hic_15 = self.report.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
# or, across modules:
EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15(report, isomme, p=self.p)
```

Two problems: (a) the first form reaches a *class* through the instance's `report` attribute — brittle and unreadable; (b) both encode a full tree path, so moving a criterion inside its home report breaks unrelated reports. This friction is why the Neck/Chest/Femur limit blocks were duplicated rather than shared (G6 unmet in practice).

### F9 (M) — Implicit contracts that only fail at runtime

- `Report.__init__` requires an inner class named exactly `Criterion_Overall`.
- `Page_Criterion_*` requires `self.criteria` to be set by the subclass `__init__`; `Page_Plot_nxn` requires `self.channels`. Neither is declared as abstract; omission = `AttributeError` during export.
- `Limit.rating` is annotated but has **no default** → `Limit([...], func=...)` without `rating=` constructs fine and explodes much later inside `get_limit_ratings()`.
- `Criterion.calculation` is decorated `@abstractmethod` but `Criterion` is not an ABC (no `ABCMeta`), so it is *not* enforced — `class Criterion_Chest(Criterion): pass` (us_ncap) instantiates happily and returns `nan`.

### F10 (M) — Status is computed but never surfaced

`Status.NA` and `Status.ERROR` are recorded, but `print_results()` and every `Page_*` render only `value`/`rating`. In the PPTX, "this test has no chest deflection channel" and "this criterion crashed" both appear as `nan`. The report author gets no feedback loop (G2).

### F11 (L) — Protocol versioning is ad-hoc

`protocol`/`protocols` exist on `Report`, but only one criterion in the whole tree actually branches on it (`un/frontal_50kmh_r137.py:357`, inline ternary inside a limit lambda). Nothing verifies that the criteria in a tree support the selected protocol version, and `MetaReport` does not propagate its `protocol` to sub-reports.

### F12 (L) — Broken / half-finished modules are invisible to CI

- `us_ncap/frontal_56kmh.py` imports `pyisomme.report.us_ncap.calculate`, which **does not exist** → the module cannot be imported at all.
- `us_ncap/` has no `__init__.py`; `us_ncap/side_mdb.py` and `side_pole.py` are 1–2 line stubs.
- `USNCAP` (`us_ncap/us_ncap.py`) reads `self.reports` in `__init__` without ever assigning it → `AttributeError` on construction.
- `EuroNCAP` meta-report requires *all five* load cases as mandatory positional lists — a partial assessment cannot be composed.
- None of this fails CI: lint and tests both run with `continue-on-error: true`.

### F13 (H) — Manual-input assignments are unchecked: a typo is a silent no-op

This is the most dangerous consequence of F2, and it hits the G8 workflow directly. Python allows arbitrary attribute creation, so:

```python
report.criterion_overall[v2].criterion_driver.criterion_femur.criterion_submarining.submarining = True   # works
report.criterion_overall[v2].criterion_driver.criterion_femur.criterion_submarining.submarinig  = True   # typo → new attribute
report.criterion_overall[v2].criterion_driver.criterion_femur.criterion_submarining.submarining = "yes"  # wrong type → truthy, −4 pts
```

The second line creates a fresh attribute nobody reads. The report calculates with `submarining = False`, produces a *clean, plausible, wrong* score, and reports no `nan`, no warning, no error. The same applies to every one of the ~59 manual inputs. Because the access path is untyped today (F2), neither mypy nor pyright nor the IDE flags any of it.

### F14 (M) — Manual inputs are undiscoverable

There is no way to ask a report "what can I fill in?". The ~59 inputs are class attributes buried across 14 modules at nesting depths of up to six; finding `number_of_door_openings_during_impact` requires grepping the source. They are also invisible in the output: a PPTX produced with `submarining = True` looks identical to one produced without it, so the reader cannot tell which manual assumptions the rating rests on — a real traceability gap for a crash-assessment document.

### F15 (M) — Some manual inputs are consumed at construction time and silently ignored

`Criterion_Overall.p_driver` (and `p_front_passenger`/`p_rear_passenger`) are read in `__init__` to build the children:

```python
self.p_driver = int(isomme.get_test_info("Driver position object 1"))       # __init__
self.criterion_driver = self.Criterion_Driver(report, isomme, p=self.p_driver)
```

So the natural override `report.criterion_overall[v1].p_driver = 3` **does nothing** to the criteria — they were already built with the old value. Worse, it is *half*-effective: `Page_Driver_*` reads `self.report.criterion_overall[isomme].p_driver` at page-construction time, and `export_pptx()` re-runs `Page.__init__` (F7), so the **plots** follow the new position while the **criteria** keep the old one — a silently inconsistent report. Any input consumed during construction has this trap; only inputs consumed inside `calculation()` behave as users expect.

---

## 3. Proposals

Each proposal is independent enough to adopt on its own, but they are designed to compose into one coherent target style. Sketches use the same running example (Euro-NCAP frontal, driver head) so they can be compared directly.

**Target definition style** (what `frontal_50kmh.py` would look like after P1–P4 + P6):

```python
class EuroNCAP_Frontal_50kmh(Report["EuroNCAP_Frontal_50kmh.Overall"]):
    name     = "Euro NCAP | Frontal-Impact against Rigid Wall with 100 % Overlap at 50 km/h"
    protocol = "9.3"
    protocols = {"9.3": "Version 9.3 (05.12.2023) [references/Euro-NCAP/...v93.pdf]"}

    class Overall(Criterion):
        name = "Overall"
        max_rating = 16

        # manual inputs — enumerable, type-checked, shown in the report (P11)
        p_driver: Manual[int] = manual(1, doc="ISO-MME position digit of the driver")

        driver          = sub(Occupant,       at=Seat.DRIVER,          name="Driver")
        front_passenger = sub(FrontOccupant,  at=Seat.FRONT_PASSENGER, name="Front Passenger")
        rear_passenger  = sub(RearOccupant,   at=Seat.REAR_PASSENGER,  name="Rear Passenger")
        door_opening    = sub(DoorOpeningDuringImpact, role=Role.MODIFIER)

        def calculation(self) -> None:
            # np.nanmean is deliberate here (development runs with a single dummy);
            # declare it so the incompleteness is visible in the output — see P10.
            self.rating = self.mean_of([self.driver, self.front_passenger, self.rear_passenger],
                                       skip_missing="single-dummy development runs") / 2
            self.rating = np.interp(self.rating, [0, 8], [0, 8], left=0, right=np.nan)
            self.rating += self.door_opening.rating       # modifiers already calculated
```

with, in `euro_ncap/criteria.py`:

```python
class HIC15(PeakCriterion):
    name   = "HIC 15"
    codes  = ("?{p}HICR0015??00RX", "?{p}HICRCG15??00RX")
    reduce = Reduce.FIRST
    unit   = 1
    limits = euro_ncap.sliding_scale(higher=500, lower=700, capping=700, points=4)
    source = "AoP v9.3 §4.3.1"       # traceability to the PDF
```

---

### P1 — Declarative sub-criteria (`sub()` descriptor) with automatic wiring

**What.** Replace manual instantiation + manual `.calculate()` with a typed descriptor declared at class level. `Criterion.calculate()` walks declared children **in declaration order**, calculates them, then calls `self.calculation()` which only does aggregation.

```python
# framework (≈60 lines)
C = TypeVar("C", bound="Criterion")

class sub(Generic[C]):
    def __init__(self, cls: type[C], *, name: str | None = None,
                 at: Seat | None = None, role: Role = Role.RESULT) -> None: ...
    def __set_name__(self, owner, attr): ...      # records declaration order
    @overload
    def __get__(self, obj: None, owner) -> sub[C]: ...
    @overload
    def __get__(self, obj: Criterion, owner) -> C: ...   # ← IDE/mypy see the real type
```

```python
# before (frontal_50kmh.py, Criterion_Neck)          # after
def __init__(self, report, isomme, p):               my_extension = sub(NeckMyExtension)
    super().__init__(report, isomme)                 fz_tension   = sub(NeckFzTension)
    self.p = p                                       fx_shear     = sub(NeckFxShear)
    self.criterion_my_extension = self.Criterion_My_extension(report, isomme, p)
    self.criterion_fz_tension   = self.Criterion_Fz_tension(report, isomme, p)      def calculation(self) -> None:
    self.criterion_fx_shear     = self.Criterion_Fx_shear(report, isomme, p)            self.rating = self.min_of_children()

def calculation(self):
    self.criterion_my_extension.calculate()
    self.criterion_fz_tension.calculate()
    self.criterion_fx_shear.calculate()
    self.rating = np.min([self.criterion_my_extension.rating,
                          self.criterion_fz_tension.rating,
                          self.criterion_fx_shear.rating])
```

Escape hatch for dynamic trees (correlation report): `self.add_child(name, criterion)` at runtime; children list = declared + dynamic, in insertion order.

Two constraints this proposal must respect:

- **Eager construction stays** (G8). `sub()` instantiates children when the parent is constructed, so the whole tree exists — and is addressable and mutable — before `calculate()`. Lazy/on-demand child creation would break the manual-input workflow and is explicitly ruled out.
- **Aggregation helpers propagate NaN by default** (G9). `min_of_children()` / `sum_of_children()` wrap `np.min`/`np.sum`, *not* the `nan*` variants. A NaN-tolerant aggregation must be requested explicitly and carries a reason string (`skip_missing="…"`) that P10 renders in the output — turning today's easily-overlooked `np.nanmean` into a visible, justified exception.

| Pro (vs. today) | Con (vs. today) |
|---|---|
| Removes ~180 `__init__` blocks and ~250 explicit `.calculate()` calls → definitions shrink by roughly a third (G1). | Introduces a small framework concept authors must learn; "where does `self.driver` come from?" needs one paragraph of docs. |
| "Forgot to call `calculate()`" becomes structurally impossible — so a `nan` in the tree once again means only one thing: *the data is missing* (F1, G9). | Descriptor magic is less obvious than an explicit constructor when debugging in a plain REPL. |
| Declaration order is authoritative → deterministic tree order for print/PPTX (fixes F6). | Children are constructed eagerly for the whole tree; a criterion whose construction depends on runtime data needs the `add_child` escape hatch. |
| Fully typed: `self.driver.head.hic15.rating` autocompletes and type-checks (G3). | Two ways to attach children (declared + dynamic) remain — but they are now unified in one ordered list, unlike today. |
| Nesting is preserved exactly; only the wiring is generated (G4). | Eager construction of the full tree is now a hard requirement rather than an accident — but that is required by G8 anyway. |
| Aggregation helpers (`min_of_children`, `sum_of_children`, `modifiers_sum`) remove the third copy of the child list — but stay optional, `calculation()` can still hand-roll anything (G5). | |
| Manual inputs keep working unchanged, on shorter and now type-checked paths: `report.overall(v1).door_opening.count = 1` (G8). | |

**Effort:** M (framework S, mechanical migration of report modules M–L). **Risk:** low, purely additive if `sub()` coexists with manual attributes during migration.

---

### P2 — A typed context object instead of threading `p`

**What.** Replace the `p` positional parameter with an immutable context carried by the base class:

```python
@dataclass(frozen=True)
class Ctx:
    report:  Report
    isomme:  Isomme
    position: int          # ISO-MME position digit
    dummy:   str | None = None
    side:    Side | None = None
    def at(self, **kw) -> Ctx: ...
```

`sub(Occupant, at=Seat.DRIVER)` resolves the seat → position **lazily, at the start of `calculate()`** (from `Isomme.get_test_info("Driver position object 1")`, or from a manual override), children inherit the parent's `Ctx` unless overridden. Code patterns become templates resolved against the context: `"?{p}NECKUP00??MOY?"`.

Deferring the resolution to `calculate()` is what fixes **F15**: `report.overall(v1).p_driver = 3` set after construction is then honoured by the criteria *and* the plots, instead of only the plots. General rule to adopt: **manual inputs are read in `calculation()`, never in `__init__`.**

| Pro | Con |
|---|---|
| Deletes `self.p = p` from ~180 classes and the untyped `p` from every signature (G1, G3). | `?{p}` templating adds one indirection between the literal in the module and the code actually queried; a `Code`-aware formatter must validate the 16-char result (mitigation: validate at construction, not at calculation). |
| The same criterion class becomes reusable for driver / passenger / rear without copy-paste — this is what makes P9's shared library possible (G6). | Position resolution moves from explicit code in `Criterion_Overall.__init__` into the framework; special seat mappings (e.g. Far-Side `p=1` fixed, MPDB trolley) need a documented override. |
| Extensible: `dummy`, `side`, `protocol` ride along the same object instead of being fetched via `self.report.criterion_overall[self.isomme]....` back-references (which today create parent→child→parent cycles). | Frozen dataclass per node is a small allocation cost — irrelevant at this scale. |
| Lazy resolution fixes the "input set after construction is ignored" trap (F15) and the criteria/plots divergence it causes. | Anything else read in `__init__` must move to `calculate()` too — a one-off audit of the existing reports. |
| Removes the awkward "driver's flag read through `report.criterion_overall[isomme].criterion_driver`" pattern seen in `Criterion_Head`/`Criterion_Neck`. | |

**Effort:** M. **Risk:** low–medium (seat→position mapping must reproduce today's `p_driver`/`p_front_passenger`/`p_rear_passenger` logic exactly; cover with a unit test per report).

---

### P3 — Limit *scales* instead of hand-written limit rows

**What.** Express a threshold set the way the PDF states it, and generate the `Limit` objects:

```python
# euro_ncap/limits.py
def sliding_scale(*, higher: float, lower: float, points: float = 4,
                  capping: float | None = None, unit: str | Unit = 1,
                  direction: Direction = Direction.UPPER_IS_WORSE) -> LimitSpec: ...

# usage
limits = sliding_scale(higher=500, lower=700, capping=700, points=4)          # HIC 15
limits = sliding_scale(higher=-18, lower=-34, capping=-34, points=4)          # Chest deflection
limits = sliding_scale(higher=-36, lower=-49, capping=-57, points=4, unit="Nm")  # Neck My
limits = pass_fail(threshold=-42, unit="mm")                                  # UN R94/R137
limits = star_scale({5: 0.67*0.15, 4: 1.00*0.15, 3: 1.33*0.15, 2: 2.67*0.15}) # US-NCAP
```

The helper computes the Marginal/Weak intermediates, the `upper`/`lower` flags, the colours and the ratings. `LimitSpec` is bound to the criterion's `codes` at construction (see P4), so the pattern is written **once**.

| Pro | Con |
|---|---|
| A 6-row, 12-argument block collapses to one line holding exactly the numbers printed in the PDF — the core of G1/G2. 366 constants shrink to roughly 120 meaningful ones. | Bespoke limit shapes (time-dependent curves, asymmetric ±shear with different capping, the `get_full_limits` machinery) still need raw `Limit(...)` — so two styles coexist. Mitigation: keep raw `Limit` fully supported; helpers are sugar, not a replacement (G5). |
| Removes the four hand-interpolated numbers per scale — a whole class of unreviewable typos disappears (F5). | The generated `upper`/`lower`/colour conventions become implicit; a reviewer must trust the helper. Mitigation: one golden test asserting the six generated `Limit`s for HIC 15 equal today's literals. |
| Sign handling (negative-is-worse for deflection/femur) is centralised instead of re-derived per block. | A wrong helper is a *systemic* error affecting many criteria, whereas today errors are local. Mitigated by the golden test + P8's dump. |
| Directly enables P9: shared criterion classes parameterised by a scale. | |

**Effort:** S–M. **Risk:** medium — must be validated against current outputs before migrating (see §4 phase 0).

---

### P4 — `PeakCriterion` base for the ~80 % standard case

**What.** Most leaf criteria are literally "get channel → reduce to a scalar → rate against limits → colour":

```python
class PeakCriterion(Criterion):
    codes:  tuple[str, ...]
    reduce: Reduce = Reduce.MAX_ABS     # MAX | MIN | MAX_ABS | FIRST
    unit:   str | Unit | None = None
    limits: LimitSpec
    interpolate: bool = True

    def calculation(self) -> None:      # provided by the framework
        self.channel = self.require_channel(*self.resolved_codes)   # ← P-F3
        self.value   = self.reduce(self.channel, unit=self.unit)
        self.rating  = self.limits.min_rating(self.channel, interpolate=self.interpolate)
        self.color   = self.limits.min_color(self.channel)
```

A leaf becomes 6 declarative lines with no `__init__` and no `calculation()`:

```python
class NeckFzTension(PeakCriterion):
    name   = "Neck Fz tension"
    codes  = ("?{p}NECKUP00??FOZA",)
    reduce = Reduce.MAX
    unit   = "kN"
    limits = sliding_scale(higher=1.700, lower=2.620, capping=2.900, points=4, unit="kN")
```

Crucially the **`codes` are used for both the limits and the channel lookup** — killing F4 — and `require_channel` is used by default, so a missing channel yields a clean `Status.NA` — killing F3.

| Pro | Con |
|---|---|
| The dominant criterion shape becomes a 5-line declaration; a reviewer checks 3 things against the PDF (channel, reduction, thresholds) (G1, G2). | Yet another base class; authors must know when to use `PeakCriterion` vs `Criterion`. Mitigation: rule of thumb in the docstring — "if you write `calculation()`, use `Criterion`". |
| Single source of truth for code patterns (F4 fixed structurally). | The `codes` for limits and for data are subtly different today (`...MOY?` vs `...MOYB` — filter-class wildcard vs. concrete). The base must express "limits match the pattern family, data requests the filtered variant" — needs an explicit `filter_class` field rather than silent magic. |
| `require_channel` becomes the default path (F3) without touching 61 call sites by hand. | Criteria that need the channel *and* extra logic must override `calculation()` and call `super()`, a slightly awkward pattern. |
| `Reduce` names the intent (`MAX_ABS` replaces `data[np.argmax(np.abs(data))]` written out 8×). | |

**Effort:** S (framework) + M (migration). **Risk:** low.

---

### P5 — Turn on typing and make lint/tests blocking for `pyisomme/report/`

**What.**
1. Make `Report` generic in its overall criterion: `class Report(Generic[C])`, `criterion_overall: dict[Isomme, C]`, plus `def overall(self, isomme: Isomme) -> C`. Then `report.overall(isomme).driver.head.hic15` is checked end-to-end — that is 530 currently-unchecked chains (F2).
2. Type `Criterion.report: Report`, `Criterion.ctx: Ctx`; annotate all remaining signatures.
3. Add `[tool.mypy]` (or pyright) config with `disallow_untyped_defs = true` **scoped to `pyisomme/report/`** first, and a `py.typed` marker.
4. Add `[tool.ruff]` config (rule set incl. `F`, `E`, `B`, `UP`, `ANN` for `report/`), and flip `continue-on-error: false` in `.github/workflows/ci.yml` for lint. Keep tests non-blocking only until fixture data is sorted.
5. Add an import-smoke test that imports **every** module under `pyisomme/report/` — that alone catches F12 today.

**The manual-input payoff.** Once `criterion_overall` is typed, mypy/pyright report *assignment to an undeclared attribute* as an error. That means the F13 typo

```python
report.overall(v2).driver.femur.submarining.submarinig = True
# error: "Submarining" has no attribute "submarinig"
report.overall(v2).driver.femur.submarining.submarining = "yes"
# error: Incompatible types in assignment (expression has type "str", variable has type "bool")
```

is caught statically — no framework needed, just types. This is the cheapest available fix for the most dangerous finding in this review, and it is the main reason P5 is ranked first.

| Pro | Con |
|---|---|
| Directly delivers G3; typos in criterion paths, page wiring **and manual inputs** (F13) become editor-time errors. | An initial burst of errors to fix (≈61 `Optional` sites + the untyped signatures). Mitigation: P4 removes most of them mechanically; scope mypy to `report/` first, widen later. |
| The generic `Report[C]` also gives autocompletion in `Page` subclasses — the place where the tree is restated most often (F7). | `Generic` + inner classes needs a forward-ref string (`Report["EuroNCAP_Frontal_50kmh.Overall"]`), slightly noisy in the class header. Alternative: define `Overall` as a module-level class and reference it directly — arguably cleaner anyway. |
| Import-smoke test costs ~10 lines and would have caught the broken `us_ncap` import that has been sitting in the tree. | Blocking CI slows merges until the baseline is clean. Mitigation: one cleanup PR, then flip. |
| `py.typed` benefits downstream users writing their own reports. | |

**Effort:** S (config) + M (fixing the baseline). **Risk:** low. **This is the highest value-per-effort item and does not depend on P1–P4.**

---

### P6 — Pages select from the tree instead of restating it

**What.** Give criteria a `role` (`RESULT` / `AGGREGATE` / `MODIFIER`) and let pages query:

```python
class Page_Driver_Values(Page_Criterion_Values_Table):
    title = "Driver Values"
    def select(self, overall: EuroNCAP_Frontal_50kmh.Overall) -> Sequence[Criterion]:
        return overall.driver.leaves(role=Role.RESULT)
```

replacing two identical 10-entry chain blocks per occupant (6 blocks, ~60 chains in `frontal_50kmh.py` alone). Explicit lists stay available for pages that need a custom order:
`def select(self, o): return [o.driver.head.hic15, o.driver.head.a3ms, ...]` — still fully typed thanks to P5.

Also: drop the `page.__init__(page.report)` re-init hack in `export_pptx()` by making pages resolve their criteria in `construct()` (they then always see calculated values, which is what the hack was working around).

| Pro | Con |
|---|---|
| Page definitions shrink from ~12 lines to ~3; adding a criterion to the tree automatically shows up in the tables (G1). | Implicit selection can silently change a slide when the tree changes — the opposite failure mode from today. Mitigation: `role` is explicit per criterion, and P8's dump shows exactly what each page will render. |
| Removes the largest single source of copy-paste in the report modules (F7). | Page layout that depends on a *specific* order still needs the explicit list — two styles again. |
| Removes the double-`__init__` hack and its `# TODO: TEST!`. | Requires `Page` to know the concrete overall-criterion type (comes free with P5). |

**Effort:** M. **Risk:** low.

---

### P7 — Make the report self-checking (`Report.validate()`)

**What.** A framework-level check runnable in a unit test *without any measurement data*:

- every `Criterion` has a `name`;
- every criterion is reachable from `Criterion_Overall` (no orphans);
- every declared child is either aggregated in the parent's `calculation()` or explicitly marked `role=INFO` (detectable by running the tree with synthetic ratings, see below);
- every criterion with limits declares `codes`, and every declared code pattern is a valid 16-char `Code` template;
- `max_rating` declared per criterion is actually achievable and not exceeded: feed each leaf its best/worst possible rating (from its `LimitSpec`) and assert the aggregated root equals the protocol's stated maximum (16 pts for MPDB, 8→16 scaling for frontal 50 km/h, 4 for Far-Side after the /3 downscale, …);
- every registered report constructs, calculates and exports against a synthetic `Isomme` (channels generated from the declared `codes` — the data to do this already exists via `create_sample`).

| Pro | Con |
|---|---|
| Turns "hard to verify if a report has errors" into a test run — the explicit ask behind G2. The max-rating propagation check in particular catches wrong aggregation (`sum` vs `min`) and dropped children, which nothing catches today. | Requires each criterion to declare `max_rating` (small extra annotation burden — but it is a number straight from the PDF, so it doubles as documentation). |
| Synthetic-data smoke test gives every report coverage without the untracked `data/` fixtures — today report tests can't run in CI at all. | Best/worst-rating propagation needs `LimitSpec` to expose its rating range → depends on P3 (raw `Limit` lists can still opt out). |
| Catches F9 (missing `criteria`/`channels`, missing `Criterion_Overall`) and F12 (broken modules) automatically. | Manual inputs are free variables, so the max-rating check must explore both branches of every declared input (all-defaults and all-worst-case). With P11 the inputs are enumerable, so this is mechanical; without it, it cannot be done at all. |
| With P11, validation can also assert that every manual input is actually *read* somewhere in a `calculation()` — catching inputs that were renamed in the logic but not in the declaration (or vice versa). | Combinatorial explosion if a criterion has many independent inputs; cap it (e.g. check defaults + each input flipped individually). |

**Effort:** M. **Risk:** low (pure addition).

---

### P8 — Requirement traceability: `report.describe()` → Markdown/table dump

**What.** Add an optional `source: str` per criterion (`"AoP v9.3 §4.3.1"`) and a dump that renders the *definition* (not the results):

```
Overall (max 16)                                        AoP v9.3 §3
└─ Driver (sum, max 16)                                 §4
   └─ Head (min, +modifiers, max 4)                     §4.3
      ├─ HIC 15        ?1HICR0015??00RX   [-]   500 → 700, cap 700, 4→0 pts   §4.3.1
      ├─ Head a3ms     ?1HEAD003C??ACRX   [g]    72 →  80, cap  80, 4→0 pts   §4.3.2
      ├─ manual: hard_contact  (bool|None, default None = derive from curve)   §4.3
      └─ Modifier: Unstable airbag/steering wheel contact       −1 pt         §4.3.6
         └─ manual: unstable_airbag_steering_wheel_contact (bool, default False)
```

Reviewing a new report against the PDF becomes reading one page of table instead of 1500 lines of Python; regressions become a diff of two dumps.

| Pro | Con |
|---|---|
| Highest-leverage item for G2 specifically: verification without digging into code, and reviewable by a non-Python colleague. | Only as truthful as the declarative parts — a criterion with hand-written `calculation()` can do things the dump doesn't show. Mitigation: mark such criteria explicitly (`custom logic`) in the dump. |
| Doubles as the manual-input catalogue (F14) — the same dump tells the user what they may fill in and what the defaults are. | Requires P11 for the input rows to be enumerable. |
| The dump can be committed as a golden file → any change to thresholds shows up in the PR diff. | Requires P3/P4 to be meaningful (with today's raw limit lists the dump would just re-print 423 rows). |
| `source` fields make the PDF↔code mapping explicit and survive protocol updates. | Small ongoing annotation burden. |

**Effort:** S–M (after P3/P4). **Risk:** none.

---

### P9 — A shared criteria library per protocol family

**What.** `pyisomme/report/euro_ncap/criteria.py` holding top-level, context-parameterised criterion classes (`HIC15`, `HeadA3ms`, `NeckMyExtension`, `NeckFzTension`, `NeckFxShear`, `ChestDeflection`, `ChestVC`, `FemurAxialForce`, `ShoulderBeltLoad`, `Submarining`, `DoorOpeningDuringImpact`, `DAMAGE`, …). Reports import them; variants are expressed by subclassing or parameters:

```python
class RearNeckMyExtension(NeckMyExtension):          # rear passenger: no capping, max 2 pts
    limits     = sliding_scale(higher=-36, lower=-49, points=4, unit="Nm")
    max_rating = 2
```

replacing `EuroNCAP_Frontal_50kmh.Criterion_Overall.Criterion_Driver.Criterion_Head.Criterion_HIC_15(...)` (13 sites) and the three copy-pasted neck blocks.

| Pro | Con |
|---|---|
| Delivers G6 properly: one definition of "Euro-NCAP HIC 15", imported by frontal 50 km/h, MPDB, Far-Side, Far-Side VTC. | Shared classes create coupling: a change for one load case can affect four. Mitigation: variants via subclassing + P7's max-rating checks per report. |
| Flat import paths survive tree refactors, unlike today's deep class paths (F8). | Requires P2 (context) — without it, shared classes still need the `p` plumbing. |
| Removes the duplicated limit blocks that are the most error-prone part of the modules (F5). | The library needs its own naming discipline to avoid becoming a dumping ground. |

**Effort:** M. **Risk:** medium (must confirm which "identical looking" blocks are actually identical — the driver/front/rear neck tables differ in capping rows and rating caps; P8's dump makes the comparison mechanical).

---

### P10 — Propagate and surface `Status`; make NaN self-explaining

**What.** `nan` should stay (G9) but stop being anonymous. Three parts:

1. **Status propagates up the tree.** A parent whose children include an `NA` becomes `NA` itself (carrying the reason), not `OK`-with-`nan`. A parent with an `ERROR` child becomes `ERROR`. So the root criterion can answer *why* the score is `nan` without anyone reading the log.
2. **Status is rendered.** Tables/charts show `n/a — 11CHST0003??DSXC missing` instead of `nan`, and a visible `ERROR` marker for `Status.ERROR`; `print_results()` gains a status column. Optionally `Report.calculate(strict=True)` re-raises on `ERROR` for CI use.
3. **Deliberate NaN-tolerance is declared and shown.** `mean_of(..., skip_missing="single-dummy development runs")` marks the result as *computed from incomplete data*; the PPTX shows an asterisk with the reason. This keeps the `np.nanmean` escape available but impossible to overlook — currently it is one character of difference (`nanmean` vs `mean`) in a 1470-line file.

**Protocol versions** (smaller, unrelated): either (a) keep the current inline ternaries but validate `protocol` against a `Literal`-typed key set and propagate `MetaReport.protocol` to sub-reports; or (b) declare per-version limit tables (`LIMITS = {"9.3": …, "9.0": …}`) selected at construction.

| Pro | Con |
|---|---|
| Distinguishing "n/a" from "bug" from "deliberately averaged over missing dummies" closes the author's feedback loop (F1, F10) — today all three look like `nan`. | Slide layout must accommodate a status/marker; small `Page_*` changes. |
| Preserves G9 exactly: nothing is silently filled in, the `nan` still propagates — it just carries its reason. | Status propagation rules need care for modifiers: a missing *modifier* arguably should not invalidate the parent (a modifier that cannot be assessed is 0 pts). Needs an explicit per-criterion policy (`na_policy = Propagate | Neutral`). |
| `strict=True` makes report errors fail a test run instead of hiding in logs. | |
| (b) is much cleaner once more than one version per protocol exists; today only one report needs it, so (a) is the proportionate choice **now**. | (b) is over-engineering at the current single-version-per-report state; defer until a second version actually lands. |

**Effort:** S–M. **Risk:** low.

---

### P11 — Manual inputs as a first-class, declared concept

**What.** Keep the workflow exactly as it is (`report.overall(v1).door_opening.count = 1`) but make the fields *declared* rather than incidental, using `Annotated` so the type checker still sees a plain `int`/`bool`:

```python
Manual = Annotated          # Manual[int, manual(...)] reads as int to mypy/pyright

class DisplacementSteeringColumn(Criterion):
    name = "Modifier for Displacement of Steering Column"
    rearwards: Manual[float, manual(0.0, unit="mm", source="measurement",
                                    doc="Rearward displacement of the steering column")]
    upwards:   Manual[float, manual(0.0, unit="mm", source="measurement")]
    lateral:   Manual[float, manual(0.0, unit="mm", source="measurement")]
```

This buys four things, none of which exist today:

- **Enumeration.** `report.print_inputs()` / `report.get_inputs()` lists every settable input with its path, default, current value, unit and docstring — the answer to "what can I fill in?" (F14). `report.set_inputs({...})` / JSON round-trip makes a run reproducible: the manual assumptions can be stored next to the ISO-MME container and replayed.
- **A runtime typo guard.** `Criterion.__setattr__` rejects assignment to names that are neither declared inputs nor framework fields. This covers the notebook/CLI users who never run mypy — a `AttributeError: 'Submarining' has no settable attribute 'submarinig'. Did you mean 'submarining'?` at the moment of assignment, instead of a wrong score twenty minutes later (F13).
- **Validation at assignment**: type, range, unit — `submarining = "yes"` fails immediately.
- **Traceability in the output.** Inputs that deviate from their default appear in the PPTX (a "Manual inputs" block on the occupant slide, and a marker on the affected criterion) and in P8's `describe()` dump. The reader of a report can then see that "Submarining: yes" was an engineer's judgement, not a measurement (F14).

Tri-state for derived-or-observed inputs: `hard_contact: Manual[bool | None, manual(None)]` with `None` = "derive from the curve", `True`/`False` = "observed in video, overrides the curve". See Appendix A2 — the current `bool` default cannot express "video shows *no* contact".

| Pro | Con |
|---|---|
| Fixes F13/F14 for all users, including those who never run a type checker, and makes manual assumptions auditable in the delivered PPTX. | A `__setattr__` guard on a hot-ish class; must whitelist framework fields (`value`, `rating`, `channel`, …) carefully or it becomes an obstacle. Keep it a simple name-set check. |
| `Annotated` is type-transparent — mypy/pyright/IDE still see `float`, so P5's checking is unaffected and no plugin is needed. Works on Python 3.9 (`typing.Annotated` + `get_type_hints(include_extras=True)`). | One more declaration idiom to learn; `Manual[float, manual(0.0, unit="mm")]` is more verbose than `rearwards: float = 0.0`. |
| Input dump/load enables a practical workflow: export a filled-in template per test, hand it to the test engineer, load it back. | Adds a mutable-state schema to maintain; renaming an input becomes a (documented) breaking change for saved input files. |
| Declared units make the `# in mm` comments in today's code machine-readable. | |

**Alternative considered:** group inputs into a per-criterion `@dataclass` (`criterion.inputs.rearwards = 0.0`). Pro: pure standard library, free `__init__`/`__repr__`, and assignment is type-checked without any framework. Con: adds an `.inputs.` level to every access path, and a dataclass instance still accepts arbitrary new attributes unless it is `slots=True` (Python ≥3.10 — the project supports 3.9), so the runtime typo guard would not come for free. Recommended only if the `Annotated` approach is felt to be too magical: it delivers ~70 % of the value with ~0 framework code.

**Effort:** S–M. **Risk:** low. Note P11 is **independent of P1–P4** and can land on today's code as-is.

---

## 4. Recommended sequencing

| Phase | Content | Why first |
|---|---|---|
| **0. Safety net** | Golden-output test for `frontal_50kmh` + `frontal_mpdb` (values/ratings for the existing fixtures, plus a `describe()`-style dump once available); import-smoke test over all report modules. | Everything below is a refactor of numeric logic; without a baseline it is unverifiable. Also immediately exposes F12. |
| **1. Typing & lint** (P5) | Generic `Report[C]`, annotate signatures, mypy scoped to `report/`, blocking ruff. | Independent of the design changes, cheapest, and it makes every later refactor safer. Also the cheapest fix for F13 (manual-input typos). |
| **1b. Manual inputs** (P11) | `Manual[...]` declarations, `__setattr__` guard, `print_inputs()`/`get_inputs()`/`set_inputs()`. | Independent of P1–P4, lands on today's code, and protects the workflow that currently has zero safety net. Pairs naturally with phase 1. |
| **2. Limits & leaf criteria** (P3, P4) | `sliding_scale`/`pass_fail`/`star_scale`, `PeakCriterion`, single-source `codes`, `require_channel` by default. | Biggest reduction in lines and in unverifiable constants; fixes F3/F4/F5 structurally. |
| **3. Tree wiring** (P1, P2) | `sub()` descriptor, `Ctx`, ordered children, aggregation helpers. | Fixes F1/F6; only sensible after leaves are slim. |
| **4. Reuse & pages** (P9, P6) | Shared `euro_ncap/criteria.py`; pages select from the tree; drop the `__init__` re-run hack. | Depends on P2/P1. |
| **5. Verification** (P7, P8, P10) | `validate()`, `describe()` dump + golden file, status propagation & rendering, visible `skip_missing` markers. | Delivers the "verify a report without reading code" goal on top of the now-declarative definitions. |

Phases 1 and 2 alone should take `frontal_50kmh.py` from ~1470 to roughly 600–700 lines; with phases 3–4, to roughly 350–450 lines, of which the large majority is protocol content.

---

## Appendix A — Concrete defects found while reading

These are independent of the architecture proposals and worth fixing regardless. Each illustrates why F1–F5 matter.

| # | Location | Issue |
|---|---|---|
| A1 | [`frontal_mpdb.py:183`](../../pyisomme/report/euro_ncap/frontal_mpdb.py#L183) | `if np.max(np.abs(...get_data(unit=g0))):` — the `> 80` comparison present in the 50 km/h version ([`frontal_50kmh.py:147`](../../pyisomme/report/euro_ncap/frontal_50kmh.py#L147)) is missing, so this tests the truthiness of a float and is true for any non-zero curve. **This silently overrides a user's manual `hard_contact = False`** — the one case the manual input exists for. Real bug. |
| A2 | `frontal_50kmh.py:130/147-149` | *Corrected from an earlier draft of this review: this is not a bug.* `hard_contact: bool = True` + `if peak > 80: self.hard_contact = True` implements `hard_contact = manual_observation or (peak > 80)` — the video observation is OR-ed with the curve evidence, and the default is the conservative assumption. Worth keeping, with two suggestions: (a) write it as an explicit `self.hard_contact = self.hard_contact or peak > 80` so the intent is readable, and (b) consider the tri-state `hard_contact: bool | None = None` (`None` = derive from curve) — the current `bool` cannot express "video clearly shows *no* contact although the curve peaks above 80 g", which is presumably a legitimate engineering call. See P11. |
| A3 | [`frontal_50kmh.py:864-872`](../../pyisomme/report/euro_ncap/frontal_50kmh.py#L864) | Rear passenger head: `if hard_contact → a3ms only; else → min(hic, a3ms)`. Driver/front passenger use `if hard_contact → min(hic, a3ms); else → 4`. The rear branch looks inverted — needs a check against AoP §4. |
| A4 | `frontal_50kmh.py:948` | Rear passenger neck aggregates with `np.sum` while driver/front use `np.min`. Plausible given the per-criterion caps (2/1/1 = 4 pts), but undocumented — exactly the kind of thing P8's dump would make reviewable. |
| A4b | `frontal_50kmh.py:63-78`, `.py:1158` etc. | `p_driver`/`p_front_passenger`/`p_rear_passenger` are consumed in `Criterion_Overall.__init__`, so overriding them after construction affects the **plots** (pages are re-`__init__`-ed in `export_pptx`) but not the **criteria** → a silently inconsistent report. See F15; fixed by P2's lazy context resolution. |
| A4c | `frontal_50kmh.py:73-74` | The passenger positions are derived as `1 if self.p_driver != 1 else 3/6` — i.e. a right-hand-drive test is inferred from the driver position alone, and `p_rear_passenger` flips between 6 and 4 as a side effect. Correct for the two standard layouts, but it is a hidden assumption a reader cannot check against the PDF; better expressed as an explicit, overridable seat map (P2 + P11). |
| A5 | `us_ncap/frontal_56kmh.py:4` | `from pyisomme.report.us_ncap.calculate import *` — module does not exist; the file cannot be imported. Also `us_ncap/` has no `__init__.py`. |
| A6 | `us_ncap/us_ncap.py:12` | `USNCAP.__init__` iterates `self.reports`, which is never assigned → `AttributeError` on construction. Sub-reports are never instantiated. |
| A7 | `us_ncap/frontal_56kmh.py:90-97` | `Criterion_Chest/Femur/Neck` are `pass` bodies, yet `Criterion_Driver.calculation()` multiplies their `.value` (nan) into the risk product. `@abstractmethod` is not enforced because `Criterion` is not an ABC. |
| A8 | [`report.py:84`](../../pyisomme/report/report.py#L84) | `page.__init__(page.report)` re-invocation with `# TODO: TEST!` — every `Page.__init__` must be idempotent, and page-building code runs twice. |
| A9 | [`limits.py:20`](../../pyisomme/limits.py#L20) | `Limit.rating: float` has no default; a `Limit(...)` without `rating=` constructs successfully and fails later inside `get_limit_ratings()` with a confusing message. |
| A10 | `euro_ncap/euro_ncap.py:18` | `EuroNCAP` requires all five load cases as mandatory arguments; a partial assessment cannot be composed. `MetaReport.protocol` is also not propagated to sub-reports. |
| A11 | `report.py:62`, `criterion.py:93/107` | `dir()`-based child discovery → alphabetical, not definition, order in `print_results()` and every tree walk. |
| A12 | `correlation/correlation.py:47` | Criteria held in `self.criteria` (a list) are invisible to `get_subcriteria()`/`print_results()` — two incompatible child mechanisms. |
| A13 | `page.py:98/105` | `Page_Criterion_Table` assumes every `Isomme` maps to an equal-length criterion list (`list(self.criteria.values())[0]`); an occupant missing in one test would produce a ragged table or an `IndexError`. |
| A14 | `.github/workflows/ci.yml` | Both lint and test steps use `continue-on-error: true`, so none of the above fails CI. |
| A15 | `frontal_50kmh.py:279-290`, `:679-690` | `Criterion_ExceedingForwardExcursionLine` declares three manual inputs (`forward_excursion`, `simulation_contact_seat_H3`, `simulation_hic_15_H3`) but `calculation()` is `self.rating = 0` — the inputs are dead for driver and front passenger, while the rear-passenger copy (`:907-930`) implements the real logic. A user setting `forward_excursion` on the driver gets no effect and no warning (F14; P7's "every input is read somewhere" check would catch it). |
| A16 | `frontal_50kmh.py:103`, `:308` | `steering_wheel_airbag_exists` lives on `Criterion_Driver` but is read via `report.criterion_overall[isomme].criterion_driver.…` from inside the driver's own Head/Neck criteria — a back-reference through the report to reach the grandparent. Harmless today, but it means the flag cannot be set per occupant, and the front-passenger tree silently does not consult it at all. |

---

## Appendix B — Alternatives considered and not recommended

### B1 — Define reports in YAML/JSON (data-driven), with a generic interpreter

| Pro | Con |
|---|---|
| Slimmest possible definition; a non-programmer could edit thresholds; trivially diffable against the PDF. | Loses G3 entirely (no typing, no linting, IDE gives nothing) and G5 largely — MPDB's cross-occupant `min()`, Far-Side's downscaling, capping-to-zero, `hard_contact` flags and the correlation report's dynamic tree all need escape hatches, which turn the YAML into a badly-typed programming language. Every escape hatch re-introduces Python anyway. Manual inputs (G8) would need a parallel schema on top. |

**Verdict:** rejected, in line with the explicit preference for staying in Python. The declarative-in-Python style of P1–P4 gets ~80 % of the slimness while keeping typing, lint warnings and full flexibility for the edge cases where logic genuinely must be written out. (The only part worth externalising is the pure threshold table, and P3 already covers that *inside* Python.)

### B2 — `dataclass`-based definitions

Given the openness to dataclasses, this deserves a differentiated answer rather than a flat rejection. Three distinct places, three verdicts:

| Where | Verdict | Reasoning |
|---|---|---|
| `Ctx` (P2), `LimitSpec` (P3), `Reduce`/`Role`/`Seat` value objects | **Recommended.** `@dataclass(frozen=True)` — immutable, hashable, free `__repr__`, perfect fit. | These are pure data with no framework injection. |
| Manual inputs grouped per criterion (P11 alternative) | **Viable fallback.** `@dataclass class HeadInputs: hard_contact: bool = True`, accessed as `criterion.inputs.hard_contact`. | Zero framework code and assignment is type-checked. Costs an extra `.inputs.` level in every path, and without `slots=True` (Python ≥3.10; project targets ≥3.9) it still accepts typo'd attributes at runtime. Choose this if `Annotated` feels too magical. |
| The `Criterion` classes themselves | **Not recommended.** | `@dataclass` generates `__init__` from fields, but the framework must inject `report`/`isomme`/`ctx` — so every field needs `field(init=False)` and the generated `__init__` is thrown away, leaving only `__repr__` as a benefit. Descriptor-typed fields (`sub()`) interact subtly with dataclass default semantics, and differently across 3.9–3.12. It also does not address the actual problem, which is *automatic child calculation and aggregation*, not object construction. |

**Verdict:** use dataclasses for the value objects (definitely) and optionally for manual-input groups; keep `Criterion` a plain class with descriptors.

### B3 — Flatten the tree (list of criteria + a separate grouping table)

| Pro | Con |
|---|---|
| Simplest possible model; no reflection; easy to render. | Contradicts G4 — the grouping *is* part of the assessment logic (body-region `min()`, occupant `sum()`, modifiers attached at a level). Splitting the tree from the aggregation would put the two halves out of sync, i.e. re-create F1 in a worse form. |

**Verdict:** rejected.

### B4 — Keep the current style, only add documentation and tests

| Pro | Con |
|---|---|
| Zero refactor risk; no new concepts. | Leaves F1–F5 and F13 in place: the boilerplate:content ratio stays ~4:1, the 366 hand-typed constants stay unverifiable, typing stays impossible on the 530 access chains, and a typo'd manual input stays a silent no-op. It does not move G1/G2/G3 at all. |

**Verdict:** rejected — but note that phase 0 of §4 (golden tests + import smoke test) is exactly this, and should happen first regardless.

### B5 — Auto-repair missing data (`nanmin`/`nanmean` everywhere, default ratings for absent channels)

| Pro | Con |
|---|---|
| Every report always produces a number; no `nan` in the PPTX; convenient during development. | Directly violates G9. A mislabelled or absent channel would yield a *plausible* rating, and the reader would have no way to know the assessment is incomplete — the worst possible failure mode for a rating tool. |

**Verdict:** rejected explicitly, and recorded here so it is not re-proposed. The correct treatment of missing data is the `nan` that already happens, made *self-explaining* by P10 — with NaN-tolerant aggregation available only as a declared, visible exception.
