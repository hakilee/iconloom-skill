# Calibrated blueprints

| Family | Relationship | Required construction |
|---|---|---|
| interlocking-tiles | agreement, comparison | Four rounded tiles; unoutlined rear pair; outlined sides; one central junction with hidden side seams masked. |
| capsule-knot | reciprocity, access | Four off-center capsules; open center; unfilled circular continuity contour. |
| tile-weave | indexing, assembly | Rear horizontal band → four diagonal tiles → front vertical band. |
| pinwheel-knot | circulation, propagation | Two blades → perforated diamond → two blades; curved inner tips preserve the intentional small star opening. |
| lens-network | integration, multi-view aggregation | Unoutlined base disc, center lens, four offset lenses; different horizontal/vertical opacities. |
| lobed-orbit | participation, shared rhythm | Four cardinal and four translucent diagonal capsules, then a central rounded tile. |

Render the chosen family in both themes and review its construction. Use user-supplied references when matching a specific visual style; this public package does not bundle third-party reference artwork.

## Input

```json
{"name":"new-concept","label":"New concept","family":"capsule-knot","meaning":"Reciprocal forms enclose a shared open space.","spread":0.3,"weight":-0.2,"phase":0}
```

A file accepts one object or a list with unique names.

- Required: `name` (lowercase ASCII slug, starting with a letter, ≤64 characters), `family`.
- Optional: `label`, `meaning`; `spread` and `weight` in [-1,1], default 0; `phase` in [-12,12] degrees, default 0.
- Spread and weight adjust family-specific spacing/extent and width/radius. Exact coupled ranges live in `FAMILIES` in `compose.py`; they are not arbitrary pixel coordinates. Prefer modest, meaningful changes. Rotation alone is not a new design.
- `palette` defaults to the family's token; optionally select a token from `palettes.json` or three related hex colors `[light, deep, dark-edge]`.
- Extra coordinates, shapes, counts and surface overrides are rejected. Use the custom route when they are genuinely required.

`compose.py` preflights the batch before writing `svg/`, `compiled-specs.json`, and `topology.json`. Keep the input too. On failure, fix the input or shared rule explicitly; do not silently clamp parameters or change families.

## Protected relationships

Family rules distinguish outlined/unoutlined layers and filled/unfilled contours. Perforated fills and clips share the even-odd rule. The tile junction hides redundant side seams before drawing its center once. A 0.5-unit inset consumes corner radius: main rounded contours must retain curvature inside that edge.

`geometry_audit.py` samples compiled fill geometry on a 128×128 grid: 0.5-unit margin, one connected fill, overlap links of at least 0.25 square units, and the expected intentional hole count. Strokes, filters and perceived seam quality are outside this test. The pinwheel's small center opening is an family-specific exception, not permission for accidental cavities.

For changes to these rules, follow [quality.md](quality.md).
