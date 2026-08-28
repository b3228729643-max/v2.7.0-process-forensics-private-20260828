# Manual ledger index

All reviewer/decision/note fields below were written after inspecting the corresponding direct views/cards. Machine scripts did not create or overwrite manual fields.

| Ledger | Rows | Coverage |
|---|---:|---|
| `manual/object_ledger.csv` | 32 | every semantic object |
| `manual/primitive_exclusion_ledger.csv` | 28 | every PDF drawing primitive |
| `manual/critical_intersection_ledger.csv` | 24 | every critical geometry/text intersection |
| `manual/relationship_ledger.csv` | 7 | six directed relations plus fraction relation |
| `manual/role_ledger.csv` | 9 | all semantic typographic roles |
| `manual/hard_gate_ledger.csv` | 20 | all hard acceptance gates |
| `manual/peer_ledger.csv` | 25 | all peer groups under R168 |
| `manual/clip_ledger.csv` | 32 | every object against the final crop |
| `manual/glyph_ledger.csv` | 194 | every visible glyph occurrence |
| `manual/pair_ledger_01.csv` | 124 | pairs 001–124 |
| `manual/pair_ledger_02.csv` | 124 | pairs 125–248 |
| `manual/pair_ledger_03.csv` | 124 | pairs 249–372 |
| `manual/pair_ledger_04.csv` | 124 | pairs 373–496 |
| `manual/view_ledger.csv` | 72 | every render file |

Total manual decisions: **939**. Every ledger has a distinct per-ID note; read-only validation found zero duplicate notes and exact pair/glyph/view coverage.
