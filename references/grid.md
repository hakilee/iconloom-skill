# Grid and keylines for 16-unit packs

Read when defining a new pack contract or checking spacing. Enable `style.grid: "keyline-16"` for the 16-unit helper. Existing specs without it retain their exact output. For a supplied design system or another native size, use its own grid rather than silently applying this preset.

## Author inside a frame

Use a 16×16 canvas, 1-unit construction grid, center axes at x/y=8 and a 1-unit outer safe margin. The padding includes visible centered stroke extents; internal clipped borders do not add outside size. Guides are review overlays, never geometry in production SVGs. [keyline-16.svg](../assets/keyline-16.svg) is an editable construction sheet.

Choose the keyline by the intended silhouette before drawing:

| Keyline | Bounds (left, top, right, bottom) | Purpose |
|---|---|---|
| square | 2, 2, 14, 14 | Compact block-like mass |
| circle | 1.5, 1.5, 14.5, 14.5 | Round mass; slight size compensation |
| horizontal | 1, 3, 15, 13 | Broad silhouette |
| vertical | 3, 1, 13, 15 | Tall silhouette |
| free | 1, 1, 15, 15 | Diagonal/irregular silhouette requiring more space |

These are this skill's starting dimensions; a user's design system may define different ones. Equal optical size does not mean all four margins must have the same numerical value for every shape. Preserve distinctive proportions, negative space and attachment structure. Don't widen a narrow tool merely to fill its keyline, and don't enlarge tiny functional indicators to match primary icons; separate those roles in the contract.

For crisp orthogonal elements, design fill edges on integer coordinates where appropriate. A centered 1-unit stroke usually uses half-integer centers; a 2-unit stroke uses integer centers. Fractional stroke widths and soft translucent edges still need native-size review. Never round every Bézier point or automatically snap diagonal/curved contours. Fit-to-keyline preserves curves and aspect ratio, not guaranteed pixel-phase alignment.

## Preserve intentionally authored coordinates

Use `"layout": {"keyline":"square", "fit":"preserve"}` for designs already constructed on the intended grid. This mode keeps coordinates exactly (unless an explicit optical offset is given), enforces the 1-unit safety area, and reports keyline overshoot without clipping. It does not automatically center the icon. The existing default, `"fit":"contain"`, remains useful for fitting rough authored silhouettes but may change pixel phase; review the native rendering afterward.

## Helper behavior

```json
"style": {"mode": "layered", "palette": "sky", "grid": "keyline-16"}
```

Each icon can include `"layout": {"keyline": "circle"}`. Omission selects `auto`: wide/tall bounding-box proportions, with a dominant circle primitive used as a round hint. This is a geometric suggestion, not a semantic or optical classifier. Explicitly choose another keyline if the metaphor requires it.

The helper fits the whole outer silhouette uniformly and centers its sampled paint bounds. It includes fixed-width external strokes and excludes parent-clipped surfaces/details from outer bounds. It transforms all component coordinates together, including rotated shapes and local cutout masks; stroke tokens remain unchanged. Material-width checks run after fitting. A .01-unit inset guards sampling error. The output is fitted geometry, not a group-scale transform that also scales all stroke weights.

For justified optical balance, use `"layout": {"keyline":"square", "offset":[0.25,0], "reason":"left-heavy silhouette looks centered after a small right shift"}`. Each offset is limited to ±.5 units and may not violate the outer safe margin. Review the reason against the actual icon; do not invent offsets to game a numeric test. The helper neither estimates perceptual mass nor repairs mechanical joints or ambiguous meaning.

Run `pack.py --spec pack.json --out svg --audit layout-audit.json`. The audit records chosen keyline, uniform scale, translation, before/after bounds and margins in L/T/R/B order. Bounds sample curves and include nominal strokes, not exact raster alpha, blur or perceptual weight. Export both themes from the same layout; compare 16/32px and a grid overlay with an ungridded view. If fitting makes a distinctive part disappear, revise the shared contract or source design, rather than accepting the bbox result as proof of quality.

Design reference: [IBM UI icon design](https://www.ibm.com/design/language/iconography/ui-icons/design/) describes grids, padding, key shapes and allowed optical adjustments. Its native 32px dimensions and stylistic conventions are not imposed on this 16-unit translucent preset.
