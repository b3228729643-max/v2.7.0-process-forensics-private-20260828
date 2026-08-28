# Isolated aborted, non-decisional material

## Scope

`relations/` is an earlier, interrupted relation-image emission from this
SA1 run.  It contains exactly **14,110** ordinary files totaling
**185,499,802 bytes** at the isolation check on 2026-08-24; no file was
zero-byte at that check.

## Reason for isolation

The first draft of the relation-selection rule was too broad and emitted a
large set before it was stopped.  Those files do not correspond to the final
selection algorithm, final pair ledger, or final terminal evidence set.

## Treatment

The directory is deliberately preserved without deletion, move, or overwrite
at the parent-agent's instruction.  It is **ABORTED_NON_DECISIONAL**.  No
terminal claim, PASS/FAIL decision, metric, or manifest reference may rely on
any file beneath `relations/`.  Terminal relation evidence is emitted only to
the separately named final relation directory and is enumerated by the final
sealed manifest.
