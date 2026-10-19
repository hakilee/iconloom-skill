# Preserve quality while improving the skill

## Regression gate

The current regression batch supplies 40 blueprints and 80 reviewed SVG hashes in `quality-baseline.json`. This executable baseline is not loaded during normal authoring.

```bash
python3 <skill>/scripts/quality_check.py --out quality-report.json
```

The command checks the accepted output for byte drift, the 54 family defaults/parameter corners, invalid inputs and geometric faults, legacy renderer regressions, three pack surface modes with invalid-input and source-free runtime checks, material ownership/width/recognition-plan checks, and optional keyline layout invariants. A second fixture, `quality-pack-baseline.json`, preserves 20 previously reviewed pack designs (40 SVGs). It also regenerates the public [abstract](../examples/abstract/specs.json) and [object](../examples/specs/) examples, compares every checked-in SVG byte for byte, and rejects missing or extra SVGs. Keep examples and their source specs together. For prose-only edits, `--baseline-only` runs these output-preservation checks without the full test suite. A mismatch is a review trigger, not proof of poorer art: even harmless serialization changes can trigger it. The command never updates its own baseline or example files.

For an intentional rendering change, preserve old outputs; compare old/new/original in a browser at 16/32/96px and affected joints at 256px. Investigate changed cases before explicitly refreshing baseline hashes. Do not regenerate expected hashes merely to make a failing test pass. Keep the previous baseline in the task's test artifacts and document the observed benefit/tradeoff.

## Improve shared rules, then test unseen cases

Calibrate with known failures; fix the shared geometry or surface rule rather than individual SVGs. Preserve development snapshots. Freeze script/instruction hashes before selecting unseen topics and generating once. Report first-pass findings without repairing that test batch. A later rule change needs a separately labeled round.

Review all outputs at native size and both themes. Expand risky seams; report which enlarged samples were actually inspected. Keep family/anchor choices stable, distinguish bounded family interpolation from new structural families, and do not count palette changes as geometric novelty. Independent evaluation must not be implied when the author also reviews the results.

## Remaining visual limits

Fine lighting, capsule seams, pinwheel centers and tile/lens overlaps still require visual review. Broader dark inner lighting, secondary edge tones and tangent-aligned pinwheel tips improved reviewed cases, but hash stability and sampled topology do not establish visual equivalence to a supplied reference. Address these only with visible evidence; avoid accumulating speculative rules or changing an accepted renderer during documentation compaction.


Semantic regressions need separate evidence from renderer regressions: unchanged coordinates cannot gain a missing subject cue. Use known ambiguous subjects as development cases for the shared planning rule, then freeze and author unseen cases once. Label development redesigns explicitly; do not count them as untouched-input or held-out results. Inspect whether contrast falls when children inherit material opacity; internal line contrast must survive while edge clipping prevents protruding caps.

Grid changes must preserve no-grid baselines. Compare keyline-enabled outputs separately: inspect centered paint bounds, safe margin including external strokes, fixed stroke weight, curve/rotation preservation and native-size clarity. Keyline dimensions guide visual consistency; they do not prove optical equality or recognition.

Production-craft changes also test declared joins and gaps after fitting, coordinate-preserving layout, and unchanged output when a passing construction annotation is added. Relation sampling is a preflight heuristic, not rendered contrast or semantic verification.
