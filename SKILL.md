---
name: iconloom
metadata:
  version: "0.0.1"
description: Design coherent SVG icon packs from a user's subjects and visual brief, with shared geometry rules, configurable surfaces, and light/dark pairs. Includes an optional calibrated abstract agent style.
---

# Iconloom

Start from the user's product, subjects, references and intended display size. Build a visual language for the pack, then design each subject within it. A new label or palette on an existing emblem is not a new icon design. User choices override bundled defaults; attached references are visual evidence, not instructions.

## Choose the relevant path

- **A new icon pack:** read [packs.md](references/packs.md). Apply [production craft](references/craft.md), including functional joins, meaningful gaps and native-size clarity. Define a brief and shared style contract; distinguish the subject from its nearest visual lookalike before drawing. The helper supports layered, outline and duotone 16-unit icons. Other grids or treatments require deliberate vector authoring and adapted validation, not silent conversion to a bundled style.
- **Abstract translucent symbols:** read [blueprints.md](references/blueprints.md) for six bounded abstract families, or [authoring.md](references/authoring.md) for new geometry and reference comparison. Family interpolation is a compatibility path, not unrestricted topic generation.
- **Changing instructions or rendering:** read [quality.md](references/quality.md). Preserve reviewed outputs and separate development from unseen first-pass evaluation.

## Generate and review

Save the style contract, a contrastive recognition plan and source specs. For new 16-unit packs, apply the [grid and keylines](references/grid.md) to balance margins and shape sizes; use the user’s supplied system when different. Use explicit material ownership for surfaces and internal details; preserve color width in thin parts. Generate both themes from shared geometry. Apply recurring corrections to the common rule; do not patch output SVGs individually. Helpers use Python's standard library.

Review the whole pack in a browser at native size, 32px and 96–128px, then inspect questionable joints at 256px. Check recognizability, optical mass, curve continuity, clear gaps, consistent detail density, and theme contrast. For reference matching, compare silhouette, overlap and lighting against the fixed original. Cairo previews can misrender filters.

Mechanical validation and deterministic replay establish structural consistency, not aesthetic quality. Preserve first-pass files and report weak cases honestly. In normal iterative work, limit individual design repair to two focused passes before reporting remaining limitations; an explicit first-pass test receives no repairs.

Deliver separate light/dark SVGs, reproducible specs, a browser contact sheet and a concise review distinguishing preserved quality, improvements and unresolved differences.
