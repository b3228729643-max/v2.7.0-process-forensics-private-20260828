# Post-observation pair codebook

This codebook was written only after opening the 200/300 dpi full page, the native 300 dpi figure plus caption, grayscale, semantic-class/object-ID/text overlays, and all five selected ROI pairs at native 1x and nearest-neighbor 8x.

- `CLEAR_DISJOINT`: the two reader-visible ink regions are spatially distinct; no contact, occlusion, or clipping was observed.
- `CONTAINMENT_CLEAR`: one semantic object is intentionally inside a plate or a plate is nested inside another plate; their visible ink remains distinct.
- `ENDPOINT_TOUCH_LEGAL`: a directed edge intentionally starts or terminates at a node boundary. The contact is required topology, does not enter label ink, and is not an illegal overlap.
- `PLATE_CROSSING_LEGAL`: a conditional-dependency edge intentionally crosses a dashed plate boundary to connect objects across replication scope. The crossing is semantically required, remains legible, and touches no text.
- `LEGEND_ASSOCIATION_CLEAR`: marker/sample and label are associated by row but separated by visible whitespace.
- `CAPTION_SEPARATE`: caption ink is fully below the diagram object and separated from it.

Every pair row records `NO_ILLEGAL_OVERLAP`; none relies on a bounding-box intersection alone. Dashed-border crossings and node-edge endpoint contacts were inspected in original pixels and in the corresponding 8x nearest-neighbor ROI.
