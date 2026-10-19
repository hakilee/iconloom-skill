# Production craft for coherent packs

Read after choosing the user's visual contract. Reference systems supply methods, not a mandatory replacement style. Keep translucent tonal surfaces when requested; IBM's monochrome 32px rules are not a preset for every pack.

## Decide once for the pack

Record `native size / display context`, viewpoint (front, side or controlled perspective), stroke and corner vocabulary, gap budget, theme surfaces and the meaning of recurring components. Start with three contrasting anchors: a round mass, a rectangular mass and an asymmetric tool. Review them together before expanding. Use the same metaphor for the same action across a product. A subject's principal silhouette and one diagnostic cue should survive at native size; compare both its nearest functional neighbor and an accidental visual reading (face, umbrella, balloon, etc.). Repeated tiny marks are not a substitute for an identifying silhouette.

Choose the rendering route deliberately:

- **Crisp orthogonal UI:** construct on the native grid first. Use `layout.fit: "preserve"` to retain coordinates and pixel phase. Filled straight edges prefer integer positions; stroke centers depend on width. The helper's round live strokes remain editable, not IBM submission-ready expanded paths.
- **Soft/tonal or high-density UI:** fractional coordinates and curved caps are valid when intentional. Consistent weight, negative space and actual small-size contrast matter more than blanket integer rounding.
- **Reference reproduction:** retain calibrated coordinates and tokens. Do not run a new normalization pass merely to satisfy another system's template.

Choose a small radius vocabulary appropriate to the size (e.g. .5 / 1 / 2 on this 16-unit canvas). For concentric borders, derive the inner radius from the outer radius and border width; do not reuse the same radius blindly. Smooth joins need aligned incoming/outgoing tangents; structural corners may be sharp. Use a consistent angle vocabulary such as 15° increments when it suits the subject, without distorting recognizable proportions.

For layered/duotone packs set `style.line_contrast: "by-role"`. Parentless structural lines use the theme `ink` color; parent-owned interior marks use `detail`. Choose these tokens against the actual background and material respectively. White interior marks can disappear when reused for external handles on white; a dark detail token can vanish on a dark canvas. Existing specs without this option retain their prior rendering. Outline mode already uses ink/accent.

## Build functional structure before lighting

Draw the main mass and functional parts in a flat draft. Decide which pieces must connect, which gaps must stay open, and which layers truly sit above others. Prefer one silhouette for continuous material; overlap separate structural parts visibly rather than making point contacts. A hinge cannot float between detached handles. Put lighting and small markings on this structure afterward using explicit parents. Do not auto-bridge a declared failure: that could change the object.

Declare critical relations in each icon's optional `construction` field:

```json
"construction": {
  "joins": [["handle", "body"], ["stem", "base"]],
  "gaps": [{"parts": ["left-lens", "right-lens"], "min": 0.75}]
}
```

Use this for true physical connections and meaningful independent gaps, not every pair of shapes. Shapes need explicit IDs. Parent-owned shading/details are already clipped; don't call them separate mechanical joints. `pack.py` checks declared relations **after layout** and before emitting files. A failed check calls for revisiting source structure or the shared contract, not editing output SVGs. First-pass evaluations retain and report failed attempts rather than silently retrying them.

The checker samples geometry at 1/8 unit. A joint needs a 2×2 sample block and at least .125 square units of overlap. Gap estimates account for round structural strokes. These are conservative engineering heuristics derived for this helper, not IBM/Adobe specifications. They ignore color, alpha, occlusion order and rendered interior-edge thickness. Only declared relations are checked; passing does not prove mechanical realism. Use a larger gap budget for important separation when possible.

## Review as a product asset

Inspect native size alongside 32px and an enlarged view, with labels hidden. Include confusing neighbors and remove reliance on hue. Check optical mass and center, not only bounding boxes. A full pack must share viewpoint, detail density and metaphor conventions. Where 16px becomes illegible, simplify the design or author a separate size variant; increasing the SVG width alone does not create a newly optimized icon. Preserve both shared theme geometry and transparent exports.

An embedded SVG title is not the accessible name of every button or `<img>` using it. Deliver meaning/usage labels and let the integration expose an accessible control name. Do not imply a contrast or accessibility certification from geometry validation. This helper remains a 16-unit authoring tool; another platform's required size, stroke expansion or flattening needs its own export workflow.

Sources reviewed 2026-10-19:
- [IBM design](https://www.ibm.com/design/language/iconography/ui-icons/design/): grid, padding, consistent weight, viewpoint, corners and angles.
- [IBM production](https://www.ibm.com/design/language/iconography/ui-icons/contribute/): their 32px handoff, expanded strokes and preplanned pixel alignment. Submission approval applies to IBM's library, not local skill work.
- [Adobe Spectrum fundamentals](https://spectrum.adobe.com/page/iconography/): consistent metaphors, restrained detail, key shapes and a different balance between fractional geometry and high-density rendering.
