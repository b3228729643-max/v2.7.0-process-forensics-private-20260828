# Reader-visible denominator freeze

The collision denominator is semantic-object based. Text, formulas, border, and fill inside a card form one reader-visible card object because their internal containment is intentional; each external badge and connector remains separate. This avoids falsely counting a node's own background/container as an illegal overlap while still exposing every possible inter-object collision.

Objects O01--O20 are frozen in `semantic_object_denominator.csv`:

- five composite cards: O01, O03, O05, O07, O09;
- five numbered badges: O02, O04, O06, O08, O10;
- six directed connectors: O11--O16;
- return-loop annotation: O17;
- leave-one-out explanatory footnote: O18;
- caption label and caption body: O19--O20.

`N=20`, so the complete unordered denominator is `C(20,2)=190`. `pair_skeleton.csv` mechanically fixes only pair identities. `manual_pair_ledger.csv` supplies the genuine post-observation judgment for exactly those same 190 identities; it has no missing, duplicate, extra, or unresolved row.

DENOMINATOR_STATUS=FROZEN_COMPLETE
