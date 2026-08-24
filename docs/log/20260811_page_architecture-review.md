# Composition-First Page Architecture

## Summary

The current inheritance hierarchy is reasonable as a small rendering implementation, but it is not a good report-definition API.

Across `pyisomme.report`, 226 page classes occupy about 3,093 lines; 164 implement constructors, 56 are configuration-only, and roughly 50 inherit pages nested inside another concrete report. This shows that inheritance is mostly carrying titles, selectors, channel patterns, and layout options rather than true substitutable behavior.

Adopt a composition-first architecture:

- Ordinary pages are immutable specifications composed from layout, content, data-selection, and formatting objects.
- A single renderer turns those specifications into PowerPoint slides.
- Complex content implements a small protocol or callback; it does not require a new `Page` subclass.
- Legacy inheritance remains temporarily through adapters, but all repository reports migrate to composition.
- One page specification always produces one slide; a multi-slide feature returns several specifications.

### Architecture alternatives

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| Composition-first specifications | Short report definitions; reusable components; supports multiple content regions; avoids concrete-report coupling; easy to validate | Introduces several small specification objects and a render context | **Recommended** |
| Improve the current inheritance tree | Familiar and direct to override; fewer framework changes | Continues class proliferation, constructor contracts, cross-report inheritance, and rigid single-figure layouts | Reject as target |
| Add factory functions over existing subclasses | Quick syntax reduction | Hides rather than fixes eager resolution, inheritance coupling, and layout rigidity | Useful only as a compatibility adapter |

Inheritance remains appropriate only where there is a genuine behavioral contract. In the new design, structural `Protocol`s are preferable for content extensions; a named implementation class can still be used for complex HIC15-style rendering.

## Target API and Declaration Style

Introduce these primary types:

- `PageSpec[C]`: frozen, unbound definition containing a stable key, layout, blocks, and footer policy.
- `BoundPage[C]`: binds a `PageSpec` to its owning report and implements selection/rendering behavior.
- `BlockSpec[C]`: content plus a named layout slot.
- `LayoutSpec`: semantic PowerPoint layout and named slots, with explicit-coordinate escape hatches.
- `RenderContext[C]`: owning report, presentation, slide, theme, export metadata, and slot geometry.
- `Content[C]` protocol: `render(context, bounds) -> None`.
- `CriterionSelection[C]` and `ChannelGridProvider[C]`: typed, lazily evaluated data providers.

Common factories:

```python
cover()
criterion_table(key, *, subtree=..., select=..., metric=...)
criterion_chart(key, *, subtree=..., select=...)
signal_plot(key, *, at=..., channels=..., grid=..., axes=...)
line_table(key, *, channels=..., table=..., grid=...)
figure_page(key, *, figure=...)
page(key, *, layout=..., blocks=...)
```

A report binds specifications without repeating `self`:

```python
driver = subtree(lambda overall: overall.criterion_driver)
driver_values = occupant_value_selection(driver)

self.set_pages(
    cover(),
    criterion_chart("driver_result", selection=driver_values),
    criterion_table("driver_values", selection=driver_values, metric=Metric.VALUE),
    signal_plot(
        "driver_head_acceleration",
        at=driver,
        channels=[["?{p}HEAD??????ACXA"],
                  ["?{p}HEAD??????ACYA"],
                  ["?{p}HEAD??????ACZA"],
                  ["?{p}HEAD??????ACRA"]],
        grid=(2, 2),
        share_y=True,
    ),
    figure_page("driver_hic15", figure=Hic15Figure(at=driver)),
)
```

The stable key is used by `select_pages`; its humanized form is the default title. A distinct title can be supplied without breaking saved page selections.

Protocol-specific helpers may return groups of specifications, for example `occupant_pages(...)`. Such helpers belong beside the report family rather than in the generic framework.

## Improvement List

| Improvement | Benefits | Costs / risks | Decision |
|---|---|---|---|
| Replace configuration subclasses with `PageSpec` composition | Removes most page classes and constructors; makes the entire slide visible at its declaration | Report authors learn factories/specifications | Implement |
| Resolve selectors and channel grids during rendering | Removes export-time `page.__init__` calls; honors manual inputs and lazy criterion context consistently | Provider failures move to render time unless prevalidated | Implement with `validate_pages()` |
| Typed criterion selection with defaults and overrides | Common value pages can select result leaves automatically; exact typed selectors remain available | Roles alone cannot reproduce every page—shoulder-belt load is a modifier but appears in value pages | Default to result leaves; reuse one explicit selector where required |
| Reusable selections | Chart and table share one declaration instead of repeating criterion paths | Adds a small selection abstraction | Implement |
| Reusable signal-plot components | Reuse head, neck, chest, femur, and belt plot definitions across Euro NCAP and UN without inheriting from concrete reports | Shared components must be parameterized carefully | Implement as top-level functions/specifications |
| Named layout slots | Supports body-only, two-column, summary, text-plus-chart, and custom layouts; isolates template details | More machinery than hard-coded placeholder 1 | Implement with semantic `cover`/`content` defaults and an absolute-position escape hatch |
| Separate theme from content | Centralizes layout indices, fonts, footer, colors, margins, and figure fit behavior | Theme compatibility must be validated per template | Implement |
| Multiple blocks per page | Enables mixed text, figures, native tables, images, and annotations | Slot collision and overflow require validation | Implement; common factories continue to create one body block |
| Content protocol for custom rendering | HIC15 and future special pages remain fully flexible without extending the page hierarchy | Custom content is less declarative and needs focused tests | Implement and mark custom content in `describe()` |
| Centralized figure lifecycle | Consistent sizing, transparent background, contain/fill policy, stream handling, and `plt.close()` | Existing figures may shift slightly if current bounding-box behavior is corrected | Preserve current appearance initially; add explicit fit modes |
| Stable page identity | Selection and golden files stop depending on nested class names or translated titles | Requires aliases for existing selection names | Add key plus legacy aliases |
| Explicit empty/ragged-data policy | Replaces index errors and divide-by-zero behavior with predictable output | Authors must choose policy for dynamic pages | Default strict alignment; allow `UNION`, `RENDER_NA`, or `OMIT_PAGE` explicitly |
| Composable formatting/status policies | Rating/value/status rendering becomes reusable and can later surface `NA` and `ERROR` consistently | Slightly enlarges the content API | Implement metric and missing-value formatters now; status rendering can land with the status phase |
| Page validation and description | Detects duplicate keys, unknown slots, empty selections, inconsistent rows, and oversized grids before export | Some providers require a constructed report tree | Integrate with `Report.validate()` after binding |

Do not attach presentation-specific visibility or ordering metadata to `Criterion` merely to automate pages. Scoring roles and presentation requirements differ, as demonstrated by shoulder-belt load. Exact presentation choices should remain in reusable page selections.

## Implementation Sequence

1. **Safety baseline**
   - Add slide inventories for `frontal_50kmh`, `frontal_mpdb`, FMVSS 208, and one MetaReport.
   - Record page keys, titles, layouts, shape types, text, chart/table row labels, and figure count.
   - Preserve calculation and definition goldens unchanged.

2. **Composition core**
   - Add specifications, render context, named layouts, content protocol, bound-page wrapper, and `BaseReport.set_pages()`.
   - Capture export timestamp/user once and pass it through the render context.
   - Allow legacy `Page` objects and composed specifications in the same report.

3. **Built-in content**
   - Implement cover, Matplotlib figure, signal plot, line-table, criterion-table, and criterion-chart content.
   - Consolidate values/rating table subclasses into `Metric` and formatter policies.
   - Encapsulate PowerPoint placeholder manipulation inside the renderer.

4. **Pilot migration**
   - Migrate `frontal_50kmh.py`.
   - Define reusable driver/front/rear selections once.
   - Convert HIC15 to a composed custom figure provider.
   - Remove all page-data work from constructors and delete the export-time reinitialization.

5. **Shared presets and full migration**
   - Extract context-parameterized head, neck, chest, femur, belt, Nij, and OLC page components.
   - Migrate MPDB, side-impact, UN, IIHS, FMVSS, and correlation reports.
   - Eliminate inheritance from pages nested in another concrete report.
   - Keep protocol-specific page-group helpers local to their report family.

6. **Compatibility and cleanup**
   - Adapt legacy `Page_Content`, `Page_Figure`, `Page_Plot_nxn`, and table classes to the new renderer and deprecate them.
   - Preserve old page names as selection aliases.
   - Change description/golden identity from `type(page).__name__` to stable page keys.
   - Update the architecture progress document when the page step is complete.

## Test Plan

- Unit-test every built-in content type using a synthetic report and deterministic render context.
- Verify selectors are evaluated after calculation/manual-input changes and no page constructor is rerun.
- Test default result-leaf selection, exact selection, modifier inclusion, custom ordering, empty selections, and ragged dynamic trees.
- Validate duplicate keys, missing layout slots, invalid grid dimensions, and incompatible per-test selections.
- Compare pilot PPTX shape/text inventories before and after migration; do not compare binary PPTX bytes.
- Render and reopen the full reference decks, asserting one slide per selected page and unchanged page order/content.
- Exercise custom HIC15 content, OLC missing-channel behavior, multiple-block layouts, template overrides, and MetaReport-qualified page selection.
- Keep `ruff`, `mypy`, fixture-free report tests, and opt-in PowerPoint exports clean.

## Assumptions

- PowerPoint remains the only required output backend; the content protocol should not introduce a generic multi-backend abstraction yet.
- Python 3.9 support remains, so frozen dataclasses are used without relying on newer `slots=True` features.
- Criterion scoring roles remain domain metadata, not presentation metadata.
- Default selectors are conveniences, never mandatory; explicit typed selectors are the authoritative escape hatch.
- Migration is staged for compatibility, but every in-repository report ultimately moves to the composition API.
