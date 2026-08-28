# Manual overlap and contact adjudication

The 33-object overlay and all critical native/nearest8x ROIs were inspected after the complete denominator and 528-pair index were generated. Bounding-box containment was never treated as pixel collision. Only reader-visible foreground semantics in the native render were adjudicated.

Intended structural contacts, not illegal collisions:

- O05--O06: the internal partition deliberately joins the decomposition bar border.
- O14--O15: x and y axes meet at their coordinate origin.
- O14--O16: tick marks deliberately attach to the x axis.
- O15--O16: the x=0 tick shares the axis origin.
- O15--O25: the dashed upper-reference line begins on the y axis.
- O15--O27 and O15--O28: the x=0 step value and its marker are plotted on the y axis by coordinate definition.
- O27--O28: markers deliberately sit on the ELBO step curve.

Potentially close but visibly separated:

- O25--O26: dashed reference to “未知全局上限” has ample vertical clearance.
- O27--O29 and O28--O29: curve/markers remain above and left of the stationary/local label; no crossing or obstruction.
- O16--O17 through O16--O23: tick ink remains separated from digit ink.
- O01/O12 to all contained text: panel borders enclose but do not touch glyph ink.
- O30--O31 and O31--O32 and O32--O33: caption label and wrapped lines have clear horizontal/vertical gaps.

No independent semantic foreground pair shares illegal visible ink. No candidate remains unresolved.

OVERLAP_CANDIDATE_PIXEL_COUNT=0
MASK_CONTAMINATION_PIXEL_COUNT=0
OVERLAP_PIXEL_COUNT=0
PIXEL_ADJUDICATION_STATUS=CLEAR
PIXEL_ARBITER_MODEL=NOT_USED
PIXEL_ARBITER_REASONING=NOT_USED
