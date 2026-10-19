# Author a user's icon pack

## Brief → contract → geometry

Record the use context, exact subjects, native size, literal/abstract preference, background and any supplied reference. Infer sensible defaults when the brief leaves room. Match the user's visual language; do not map every topic onto six abstract emblems.

For a new pack, set `strict: true` and save a recognition plan before drawing: primary silhouette, one diagnostic cue, nearest confusable object, and the visible difference. Tie `cue_ids` to real shapes. A label, generic horizontal line or cosmetic badge is not a subtype cue. If the cue is too small, simplify the silhouette or use a more direct metaphor; do not add more miniature details. Consider proportion (long tool versus balloon), structural arrangement and negative space before decoration. This is an authoring gate, not a machine guarantee of recognition.

For new 16-unit packs, read [grid.md](grid.md) and set `style.grid: "keyline-16"`. Choose a silhouette keyline before drawing; uniform fitting preserves aspect ratio and stroke tokens, while optical balance still needs review. Existing reference reproductions can retain their calibrated coordinates.

Fix one contract per pack: grid, safe margin, stroke width, corner treatment, optical bounds, surface mode, palette/theme tokens and detail budget. Keep a clear primary silhouette plus one or two identifying details. Different objects need different geometry, but similar visual weight. Use a semantic rationale such as “boarding pass: notched ticket + perforation”, not “travel: six petals”.

- Draw curves from their intended tangent directions. At a smooth curve-to-line join, align the last control point, endpoint and following segment. Sharp structural corners can be intentional; do not round every corner equally.
- Closed filled parts need explicit closures; open lines use round caps/joins. Keep important gaps at least roughly one stroke wide at native size. A technically valid subpixel gap may still disappear.
- Treat attached parts of the same object as a continuous outer contour when feasible; tangent-only contacts between separately outlined pieces create false seams. True separate translucent layers may retain their own edges.
- Put distinguishing details inside the silhouette. Use separate components only for meaningful handles, wheels, lenses or apertures; decorative fragments increase noise.
- Outline packs share stroke weight, cap style and corner rhythm. Duotone packs assign consistent body/accent/detail roles. Layered packs share translucency, local gradients and light direction. Do not force reference-style interlocks into ordinary objects.
- Design dark tokens for the actual dark surface; do not merely invert colors. Geometry remains identical. Specify the expected backgrounds in the preview, while keeping SVGs transparent.

For new layered/duotone packs set `style.line_contrast: "by-role"`: external structural lines use `ink`, parent-owned details use `detail`. For a new pack, follow [craft.md](craft.md): choose a small set of contrasting anchors, then declare functional joins and important gaps with `construction`. These relations are checked after layout, without changing rendered geometry. Preserve pixel-aligned authored coordinates with `layout.fit: "preserve"`; use automatic fitting when intentional.

## Pack helper

```bash
python3 <skill>/scripts/pack.py --spec pack.json --out output/svg
python3 <skill>/scripts/validate.py output/svg --profile pack
python3 <skill>/scripts/gallery.py output/svg --out output/preview.html
```

`pack.py` renders authored geometry; it does not infer icon semantics from text. The agent authors the spec using the brief and visual review. Its 16-unit scope is a convenience, not a restriction on the skill's future designs.

```json
{
  "name": "equipment",
  "strict": true,
  "brief": "Rounded outline tools; 16px toolbar on white and #202124",
  "style": {
    "mode": "outline", "grid": "keyline-16", "stroke_width": 0.85,
    "light": {"ink": "#334155", "accent": "#347DB4"},
    "dark": {"ink": "#E2E8F0", "accent": "#80BCED"}
  },
  "icons": [{
    "name": "carry-case", "label": "Carry case",
    "scenario": "Select a portable kit", "meaning": "Case with carry handle",
    "recognition": {"silhouette":"broad rectangular case", "cue":"external raised handle", "confusable":"plain storage box", "difference":"handle visible above body", "cue_ids":["handle"]},
    "shapes": [
      {"id":"handle", "tag":"path", "role":"line", "d":"M5 5 L5 3 Q5 2 6 2 L10 2 Q11 2 11 3 L11 5"},
      {"id":"body", "tag":"rect", "x":2, "y":5, "width":12, "height":9, "rx":1.5}
    ]
  }]
}
```

Contract fields: `mode` = layered / outline / duotone; `stroke_width` [.35,1.5], default .8; `palette` = bundled token or three hex colors; `relief` [0,.3], default .18. Each theme accepts `ink`, `accent`, `detail` hex tokens. Pack name/brief and per-icon label/scenario/meaning are descriptive; they do not change geometry.

Shapes use circle, ellipse, rounded rect, or absolute M/L/Q/C/Z paths from [authoring.md](authoring.md). Each has an `id`, `role` body (default), accent, surface or line, plus optional rotation/opacity. `surface` requires a preceding body/accent `parent` id; an interior `line` also names its parent. Surface children are clipped in world coordinates, including rotated parents. Use parentless lines for external handles or supports. Parents cannot be surfaces or lines. Non-layered shapes and lines reject gradient/edge/relief attributes. Filled paths close explicitly. Coordinates plus centered strokes must stay in .5–15.5; rectangular corner radii must match. Stroke containment is sampled, not a proof of arbitrary curve correctness.

Rendering roles:

| Mode | Body | Accent | Line |
|---|---|---|---|
| layered | calibrated gradient/edge | same tonal material | theme detail stroke; parent masks preserve edge |
| outline | theme ink stroke | theme accent stroke | theme ink stroke |
| duotone | theme ink fill | theme accent fill | theme detail stroke |

Layered fills accept the authoring surface controls. Common width rules estimate filled-part width (primitive dimensions, or 2 × sampled area / perimeter for paths). An outlined component reserves .9 units of color; below 1.4 units, its outline is omitted. This heuristic is not a local minimum-width proof, especially for shapes with necks. Strict mode rejects filled parts below .85 estimated units and strokes below .75; inspect actual 16px rendering. Prefer a broad capsule or structural stroke over a tiny outlined sliver. Explicit edge widths can reduce the shared budget, never enlarge it.

For legacy specs without `strict`, largely contained `edge:false` fills are inferred as surfaces, and line subpaths are assigned to a containing material when coverage is at least 90%. Standalone shapes remain independent. Save the `--audit` output; inference is compatibility behavior, not a replacement for explicit ownership in new designs. Do not expect `accent` to create another hue in layered mode. Material-owned surfaces paint inside the parent before its single edge. Internal lines are masked to the color region and retain their own contrast, independent of parent translucency. Unparented lines remain structural strokes. IDs use icon name/theme: use images or add an instance prefix for repeated inline instances.

## Acceptance

Inspect every subject without relying only on its label. Record weak recognition and details that merge at native size. Compare consistency within the contract; a successful outline pack is not evidence of matching the translucent reference. Report which styles and sizes were actually tested. A single author's visual review is not an independent recognition study.


Run `pack.py --spec pack.json --out output/svg --audit output/rules.json` to record applied common rules. `strict` requires the contrastive plan and rejects duplicate shape designs; it does not inspect whether the stated meaning is true. New packs do not inherit legacy inference. Use real `surface`/`parent` fields so the intended topology is reviewable.
