# SA3 denominator freeze — FIG-P634-01

- Reviewer: canonical `/root/sa3_fig_p634_r110_fresh_isolated_v1`
- Role/model: SA3 / gpt-5.6-sol / xhigh
- Freeze basis: actual inspection of physical page 684 at native 300 dpi, complete figure-with-caption crop, figure crop, grayscale crop, and object/semantic/text overlays.
- Visible semantic-object denominator: 46 objects, IDs `O001`–`O046`.
- Class partition: 30 `TEXT`, 3 `FORMULA`, 3 `LINE_ARROW`, 8 `NODE_BORDER`, 2 `PANEL_BORDER`.
- Complete unordered-pair denominator: 1,035 rows, exactly `46 × 45 / 2`; every pair appears once with lower object ID first.
- Text-span/codepoint denominator: 47 extracted visible spans, IDs `T001`–`T047`.
- Critical-ROI denominator: 5 regions; each has one native1x crop and one nearest-neighbour8x crop.

Frozen machine files:

| File | Bytes | SHA256 |
|---|---:|---|
| `data/objects_machine.csv` | 12,020 | `4A70DF8441E54232EA11B6C6223764F81105786EA5ED6380FB88AED53E15FA26` |
| `data/all_unordered_pairs_machine.csv` | 59,584 | `E7DF5A39C7B4E325EECFF507978EA12685D2FD8C8E299230CB7D180777D14046` |
| `data/text_spans_machine.csv` | 6,005 | `7AA85A6559F7E34016DB6528CD4280F657742FD0D8F1B79BE15A1688B1D44659` |

The machine files contain identifiers, labels, geometry, codepoints, and proximity data only. They contain no reviewer, decision, boolean, or adjudication fields. All such fields are authored manually in separate review files. This denominator is frozen before hard-gate adjudication and will not be regenerated.
