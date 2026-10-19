# Exploratory vector authoring

Use this route for structures outside the six [blueprint families](blueprints.md). Start with the user's brief and select a relevant light/dark reference pair when available. Inspect its SVG construction and browser rendering; distinguish observed contours, overlap, edge hierarchy and lighting from inferred rules. Compare references and candidates on the same surfaces, keeping backgrounds out of exported SVGs.

The [abstract examples](../examples/abstract/svg/) and their [source specs](../examples/abstract/specs.json) demonstrate custom geometry. The [object examples](../examples/svg/) and [source specs](../examples/specs/) demonstrate the [pack helper](packs.md). These are examples, not a fixed vocabulary or another designer's official rules. Preserve a distinct diagnostic cue for the requested subject. Use [packs.md](packs.md) and [craft.md](craft.md) for material ownership, width budgets, functional joins and visual review.

## Geometry and surface

Use transparent `viewBox="0 0 16 16"`, width/height 16. Center optical weight near (8,8); typical bounds are 1–15. Preserve broad semantic masses rather than matching the source's exported path count. Change one or two meaningful geometric relationships while preserving the anchor's construction.

- Match actual overlap area and center space. Sparse forms need width/intersection; crowded forms need fewer redundant edges. Adding a center circle does not solve both.
- A concave lobe needs a broad convex exterior and a smooth returning curve that receives its neighbor. Check path closures and inner turns, not only outer corners.
- Woven bands need readable width and purposeful crossings. True alternating over/under requires segmentation or masks; one painter's order cannot produce it automatically.
- Avoid almost-tangent lens outlines and thin slivers; deliberately inset or redesign the intersection.
- Use one chromatic hue family, component-local gradients, and planned opacity. Repeated rotated components rotate their gradient and edge together. Typical overlapping layers alternate roughly .8/.6; follow the anchor rather than applying this universally.
- By default, outlined shapes use a 1-unit stroke clipped to the silhouette, yielding a .5-unit inside edge. Reduce `edge_width` when the color-width budget requires it. Keep sufficient inner corner radius. Light edges are white; dark edges are hue-related. Unoutlined rear layers may be necessary.
- Group opacity composites fill and edge together. Interior relief defaults to .07 light / .16 dark; 0 suits plain bands. Dark relief uses a broader inner light and compensates for component rotation, keeping the illumination direction coherent. Use `edge_tone` [0,1] to blend a dark edge toward the palette’s second tone for secondary surfaces; it does not change light edges. It provides a controlled tonal treatment; matching a supplied reference may require different lighting. Never judge final filter quality with CairoSVG alone.

## JSON schema

```json
{"name":"woven-example","palette":"lavender","shapes":[
  {"tag":"rect","x":2,"y":4,"width":12,"height":3,"rx":1.5,"opacity":0.67},
  {"tag":"rect","x":4,"y":2,"width":3,"height":12,"rx":1.5,"opacity":0.6}
]}
```

Pass one object or a list to `generate.py --spec designs.json --out output/svg`, then run `validate.py output/svg`. Names follow the blueprint slug rules. `shapes` contains 1–24 components in painting order:

| tag | Geometry |
|---|---|
| circle | cx, cy, r |
| ellipse | cx, cy, rx, ry |
| rect | x, y, width, height; optional rx, ry |
| path | d; optional fill-rule: evenodd or nonzero |

Optional per shape: `rotate` [-360,360] about (8,8), `opacity` [.35,1], `gradient` [x1,y1,x2,y2] in local normalized coordinates (each [-2,3]), `relief` [0,.3]. Opacity, gradient and relief also accept spec-level defaults.

`edge` and `paint` are booleans, default true. `edge_opacity` is [0,1]. `edge_width` is the doubled, silhouette-clipped stroke width [0,1], default 1; use the pack planner to budget it for narrow parts. Use `paint:false` for outline-only contours. `edge_cutout` is a local path suppressing hidden seam segments via a luminance mask while retaining the silhouette clip. Apply it to a planned junction, not as an ad hoc defect eraser.

`palette` accepts a token from [palettes.json](palettes.json) or three #RRGGBB colors. Sunbeam adds an intermediate stop. Geometry is shared across the generated theme pair.

Legacy `form` presets (petal, disc, leaf, capsule, tile, arc), `count` 3–8 and `phase` remain available as scaffolding when `shapes` is absent. They do not automatically create interlocks. The renderer checks path character safety, not complete path grammar or clipping. Extend validation deliberately for unsupported features.

IDs include name/theme; use img elements or additional instance prefixes for repeated inline SVGs. Follow the visual checks in SKILL.md; retain first-pass output and the same anchor through repairs.
