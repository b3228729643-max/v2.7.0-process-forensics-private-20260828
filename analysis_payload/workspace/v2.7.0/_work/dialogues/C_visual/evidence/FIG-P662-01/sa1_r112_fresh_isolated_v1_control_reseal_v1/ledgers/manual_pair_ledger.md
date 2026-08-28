# Manual adjudication of all 300 unordered visible-object pairs

Reviewer: fresh isolated SA1 (`gpt-5.6-sol`, `xhigh`). Evidence actually opened before this ledger: official page at 300 dpi, 200 dpi page-integration view, subject native1x, grayscale, text/object/semantic overlays, and all six native1x plus six nearest-neighbor8x risk ROIs. `LEGAL_ENDPOINT` means the two semantic objects intentionally meet at a connector endpoint; `CLEAR_BBOX_ONLY` means machine bboxes touch/overlap while native foreground does not. Neither category is an illegal collision. Every other row was manually checked as `CLEAR` in the final native evidence.

## O01 against later objects

- P001 O01-O02 — CLEAR: stacked input nodes retain an 18 px bbox gap and distinct borders.
- P002 O01-O03 — CLEAR: ellipsis is well below the first input node.
- P003 O01-O04 — CLEAR: first and final input nodes are vertically separated.
- P004 O01-O05 — CLEAR: badge 1 floats above the first node without contact.
- P005 O01-O06 — CLEAR: common-rate note is far below O01.
- P006 O01-O07 — CLEAR: arrow corridor separates input node from sum node.
- P007 O01-O08 — CLEAR: badge 2 is above/right of O01.
- P008 O01-O09 — CLEAR: divide node is remote to the right.
- P009 O01-O10 — CLEAR: ratio node is remote to the right.
- P010 O01-O11 — CLEAR: badge 3 is remote to the right.
- P011 O01-O12 — CLEAR: Dirichlet node is remote to the right.
- P012 O01-O13 — CLEAR: simplex icon is remote upper-right.
- P013 O01-O14 — CLEAR: simplex note is remote upper-right.
- P014 O01-O15 — CLEAR: independence result lies well below/right.
- P015 O01-O16 — CLEAR: Beta node is remote lower-right.
- P016 O01-O17 — LEGAL_ENDPOINT: Y1 arrow begins at the east border of its source node; no text is touched.
- P017 O01-O18 — CLEAR: Y2 arrow is below O01.
- P018 O01-O19 — CLEAR: YK arrow is below O01.
- P019 O01-O20 — CLEAR: sum-to-divide arrow is well right.
- P020 O01-O21 — CLEAR: divide-to-ratio arrow is well right.
- P021 O01-O22 — CLEAR: ratio-to-result arrow is well right.
- P022 O01-O23 — CLEAR: dashed sum evidence path is below/right.
- P023 O01-O24 — CLEAR: dashed ratio evidence path is remote.
- P024 O01-O25 — CLEAR: caption is far below the first input node.

## O02 against later objects

- P025 O02-O03 — CLEAR_BBOX_ONLY: vector bboxes meet, but the first ellipsis dot has visible native white clearance below O02.
- P026 O02-O04 — CLEAR: middle and final input nodes are separated by ellipsis space.
- P027 O02-O05 — CLEAR: badge 1 is well above O02.
- P028 O02-O06 — CLEAR: common-rate note is below with ample space.
- P029 O02-O07 — CLEAR: arrow corridor separates middle input from sum node.
- P030 O02-O08 — CLEAR: badge 2 is upper-right and separate.
- P031 O02-O09 — CLEAR: divide node is remote right.
- P032 O02-O10 — CLEAR: ratio node is remote right.
- P033 O02-O11 — CLEAR: badge 3 is remote right.
- P034 O02-O12 — CLEAR: Dirichlet result is remote right.
- P035 O02-O13 — CLEAR: simplex icon is remote upper-right.
- P036 O02-O14 — CLEAR: simplex note is remote upper-right.
- P037 O02-O15 — CLEAR: independence result is below/right.
- P038 O02-O16 — CLEAR: Beta node is remote lower-right.
- P039 O02-O17 — CLEAR_BBOX_ONLY: the descending Y1 arrow bbox nears O02's corner, but native foreground remains separate.
- P040 O02-O18 — LEGAL_ENDPOINT: Y2 arrow begins at O02's east border; no text contact.
- P041 O02-O19 — CLEAR: YK arrow passes below O02 with visible clearance.
- P042 O02-O20 — CLEAR: sum-to-divide arrow is right of the middle input.
- P043 O02-O21 — CLEAR: divide-to-ratio arrow is remote right.
- P044 O02-O22 — CLEAR: final main arrow is remote right.
- P045 O02-O23 — CLEAR: dashed sum path is below/right.
- P046 O02-O24 — CLEAR: dashed ratio path is remote.
- P047 O02-O25 — CLEAR: caption is below with substantial clearance.

## O03 against later objects

- P048 O03-O04 — CLEAR: ellipsis ends above O04 with 13 px bbox clearance and no ink contact.
- P049 O03-O05 — CLEAR: badge 1 is well above.
- P050 O03-O06 — CLEAR: note lies below the final input, not beside ellipsis ink.
- P051 O03-O07 — CLEAR: sum node is right with open white space.
- P052 O03-O08 — CLEAR: badge 2 is remote upper-right.
- P053 O03-O09 — CLEAR: divide node is remote right.
- P054 O03-O10 — CLEAR: ratio node is remote right.
- P055 O03-O11 — CLEAR: badge 3 is remote right.
- P056 O03-O12 — CLEAR: Dirichlet node is remote right.
- P057 O03-O13 — CLEAR: simplex icon is remote upper-right.
- P058 O03-O14 — CLEAR: simplex note is remote upper-right.
- P059 O03-O15 — CLEAR: independence result is lower-right.
- P060 O03-O16 — CLEAR: Beta node is remote lower-right.
- P061 O03-O17 — CLEAR: Y1 arrow is above/right of ellipsis.
- P062 O03-O18 — CLEAR: Y2 arrow is right of ellipsis with white separation.
- P063 O03-O19 — CLEAR: YK arrow is right/below; no ellipsis contact.
- P064 O03-O20 — CLEAR: main chain arrow is remote right.
- P065 O03-O21 — CLEAR: main chain arrow is remote right.
- P066 O03-O22 — CLEAR: main chain arrow is remote right.
- P067 O03-O23 — CLEAR: dashed path is right/below.
- P068 O03-O24 — CLEAR: dashed path is remote right.
- P069 O03-O25 — CLEAR: caption is below and distinct.

## O04 against later objects

- P070 O04-O05 — CLEAR: badge 1 is far above O04.
- P071 O04-O06 — CLEAR: final input border and note retain 25 px bbox clearance; no glyph clipping.
- P072 O04-O07 — CLEAR: arrow corridor separates O04 from sum node.
- P073 O04-O08 — CLEAR: badge 2 is above/right.
- P074 O04-O09 — CLEAR: divide node is remote right.
- P075 O04-O10 — CLEAR: ratio node is remote right.
- P076 O04-O11 — CLEAR: badge 3 is remote upper-right.
- P077 O04-O12 — CLEAR: Dirichlet node is remote right.
- P078 O04-O13 — CLEAR: simplex icon is remote upper-right.
- P079 O04-O14 — CLEAR: simplex note is remote upper-right.
- P080 O04-O15 — CLEAR: independence result is right with open space.
- P081 O04-O16 — CLEAR: Beta node is remote right.
- P082 O04-O17 — CLEAR: Y1 arrow is above O04.
- P083 O04-O18 — CLEAR: Y2 arrow is above O04.
- P084 O04-O19 — LEGAL_ENDPOINT: YK arrow begins at O04's east border; text remains untouched.
- P085 O04-O20 — CLEAR: sum-to-divide arrow is remote right.
- P086 O04-O21 — CLEAR: divide-to-ratio arrow is remote right.
- P087 O04-O22 — CLEAR: final main arrow is remote right.
- P088 O04-O23 — CLEAR: dashed sum path is right/above note region.
- P089 O04-O24 — CLEAR: dashed ratio path is remote right.
- P090 O04-O25 — CLEAR: caption begins below O04; no page-integration collision.

## O05 against later objects

- P091 O05-O06 — CLEAR: badge 1 and bottom-left note are far apart.
- P092 O05-O07 — CLEAR: badge 1 is above/left of sum node.
- P093 O05-O08 — CLEAR: badges 1 and 2 are separately centered over different stages.
- P094 O05-O09 — CLEAR: divide node is remote right/below.
- P095 O05-O10 — CLEAR: ratio node is remote right/below.
- P096 O05-O11 — CLEAR: badges 1 and 3 are widely separated.
- P097 O05-O12 — CLEAR: Dirichlet node is remote right.
- P098 O05-O13 — CLEAR: simplex icon is remote right.
- P099 O05-O14 — CLEAR: simplex note is remote right.
- P100 O05-O15 — CLEAR: independence result is far lower-right.
- P101 O05-O16 — CLEAR: Beta result is far lower-right.
- P102 O05-O17 — CLEAR: Y1 arrow lies below/right of badge 1.
- P103 O05-O18 — CLEAR: Y2 arrow lies well below/right.
- P104 O05-O19 — CLEAR: YK arrow lies far below/right.
- P105 O05-O20 — CLEAR: main chain arrow is remote right.
- P106 O05-O21 — CLEAR: main chain arrow is remote right.
- P107 O05-O22 — CLEAR: main chain arrow is remote right.
- P108 O05-O23 — CLEAR: dashed path is far below/right.
- P109 O05-O24 — CLEAR: dashed path is remote.
- P110 O05-O25 — CLEAR: caption is far below badge 1.

## O06 against later objects

- P111 O06-O07 — CLEAR: common-rate note lies left/below the sum node.
- P112 O06-O08 — CLEAR: badge 2 is far above/right.
- P113 O06-O09 — CLEAR: divide node is upper-right and separate.
- P114 O06-O10 — CLEAR: ratio node is remote right.
- P115 O06-O11 — CLEAR: badge 3 is far upper-right.
- P116 O06-O12 — CLEAR: Dirichlet node is remote right.
- P117 O06-O13 — CLEAR: simplex icon is remote upper-right.
- P118 O06-O14 — CLEAR: simplex note is remote upper-right.
- P119 O06-O15 — CLEAR: independence result is right with white separation.
- P120 O06-O16 — CLEAR: Beta result is remote right.
- P121 O06-O17 — CLEAR: Y1 arrow is above/right.
- P122 O06-O18 — CLEAR: Y2 arrow is above/right.
- P123 O06-O19 — CLEAR: YK arrow ends above/right; it does not cover the note.
- P124 O06-O20 — CLEAR: sum-to-divide arrow is remote upper-right.
- P125 O06-O21 — CLEAR: divide-to-ratio arrow is remote.
- P126 O06-O22 — CLEAR: ratio-to-result arrow is remote.
- P127 O06-O23 — CLEAR: dashed path is right; no note glyph contact.
- P128 O06-O24 — CLEAR: dashed ratio path is remote right.
- P129 O06-O25 — CLEAR: note and caption retain a visible 22 px bbox gap.

## O07 against later objects

- P130 O07-O08 — CLEAR: badge 2 is centered above O07 with open vertical space.
- P131 O07-O09 — CLEAR: sum and divide nodes are separated by O20's arrow corridor.
- P132 O07-O10 — CLEAR: ratio node lies beyond the divide stage.
- P133 O07-O11 — CLEAR: badge 3 is above/right and separate.
- P134 O07-O12 — CLEAR: Dirichlet node is remote right.
- P135 O07-O13 — CLEAR: simplex icon is remote upper-right.
- P136 O07-O14 — CLEAR: simplex note is remote upper-right.
- P137 O07-O15 — CLEAR: lower result node has visible vertical separation from sum node.
- P138 O07-O16 — CLEAR: Beta node is lower-right and separate.
- P139 O07-O17 — LEGAL_ENDPOINT: Y1 fan-in arrow terminates at the sum node border; formula ink is clear.
- P140 O07-O18 — LEGAL_ENDPOINT: Y2 fan-in arrow terminates at the sum node border; formula ink is clear.
- P141 O07-O19 — LEGAL_ENDPOINT: YK fan-in arrow terminates at the sum node border; formula ink is clear.
- P142 O07-O20 — LEGAL_ENDPOINT: outgoing sum arrow starts at O07's east border; node text is untouched.
- P143 O07-O21 — CLEAR: divide-to-ratio arrow lies beyond O09.
- P144 O07-O22 — CLEAR: final main arrow is remote right.
- P145 O07-O23 — LEGAL_ENDPOINT: dashed evidence path starts at O07's south border, below all text.
- P146 O07-O24 — CLEAR: ratio evidence path is remote right.
- P147 O07-O25 — CLEAR: caption lies well below the sum node.

## O08 against later objects

- P148 O08-O09 — CLEAR: badge 2 is above/left of divide node.
- P149 O08-O10 — CLEAR: badge 2 is above/left of ratio node.
- P150 O08-O11 — CLEAR: stage badges 2 and 3 are separately spaced.
- P151 O08-O12 — CLEAR: Dirichlet node is remote right.
- P152 O08-O13 — CLEAR: simplex icon is remote right.
- P153 O08-O14 — CLEAR: simplex note is remote right.
- P154 O08-O15 — CLEAR: independence node is below/right.
- P155 O08-O16 — CLEAR: Beta node is remote lower-right.
- P156 O08-O17 — CLEAR: Y1 fan-in arrow is left/below badge 2.
- P157 O08-O18 — CLEAR: Y2 fan-in arrow is left/below badge 2.
- P158 O08-O19 — CLEAR: YK fan-in arrow is left/below badge 2.
- P159 O08-O20 — CLEAR: outgoing sum arrow is below/right of badge 2.
- P160 O08-O21 — CLEAR: divide-to-ratio arrow is remote right.
- P161 O08-O22 — CLEAR: final main arrow is remote right.
- P162 O08-O23 — CLEAR: dashed sum path is below badge 2.
- P163 O08-O24 — CLEAR: dashed ratio path is remote right.
- P164 O08-O25 — CLEAR: caption is far below badge 2.

## O09 against later objects

- P165 O09-O10 — CLEAR: divide and ratio nodes have a 48 px bbox gap occupied only by O21.
- P166 O09-O11 — CLEAR: badge 3 is above O09 with visible space.
- P167 O09-O12 — CLEAR: Dirichlet node is beyond ratio stage.
- P168 O09-O13 — CLEAR: simplex icon is remote upper-right.
- P169 O09-O14 — CLEAR: simplex note is remote upper-right.
- P170 O09-O15 — CLEAR: independence result lies below with open space.
- P171 O09-O16 — CLEAR: Beta node is lower-right.
- P172 O09-O17 — CLEAR: Y1 fan-in arrow is far left.
- P173 O09-O18 — CLEAR: Y2 fan-in arrow is far left.
- P174 O09-O19 — CLEAR: YK fan-in arrow is far left.
- P175 O09-O20 — LEGAL_ENDPOINT: sum-to-divide arrow terminates at O09's west border; operator ink is clear.
- P176 O09-O21 — LEGAL_ENDPOINT: divide-to-ratio arrow begins at O09's east border; operator ink is clear.
- P177 O09-O22 — CLEAR: final main arrow is remote right.
- P178 O09-O23 — CLEAR: dashed sum path passes below/left with 24 px bbox clearance.
- P179 O09-O24 — CLEAR: dashed ratio path is lower-right.
- P180 O09-O25 — CLEAR: caption lies well below the divide node.

## O10 against later objects

- P181 O10-O11 — CLEAR: badge 3 sits above/left with visible separation.
- P182 O10-O12 — CLEAR: ratio and Dirichlet nodes have a 52 px gap occupied only by O22.
- P183 O10-O13 — CLEAR: simplex icon is above/right.
- P184 O10-O14 — CLEAR: simplex note is above/right.
- P185 O10-O15 — CLEAR: independence result is below with open vertical space.
- P186 O10-O16 — CLEAR: Beta node is below/right with open space.
- P187 O10-O17 — CLEAR: Y1 arrow is far left.
- P188 O10-O18 — CLEAR: Y2 arrow is far left.
- P189 O10-O19 — CLEAR: YK arrow is far left.
- P190 O10-O20 — CLEAR: sum-to-divide arrow is left of O09.
- P191 O10-O21 — LEGAL_ENDPOINT: divide-to-ratio arrow terminates at O10's west border; formula ink is clear.
- P192 O10-O22 — LEGAL_ENDPOINT: ratio-to-result arrow begins at O10's east border; formula ink is clear.
- P193 O10-O23 — CLEAR: dashed sum path is below/left.
- P194 O10-O24 — LEGAL_ENDPOINT: dashed evidence path starts at O10's south border, below all text.
- P195 O10-O25 — CLEAR: caption lies well below the ratio node.

## O11 against later objects

- P196 O11-O12 — CLEAR: badge 3 is well left/above the final node.
- P197 O11-O13 — CLEAR: simplex icon is remote right.
- P198 O11-O14 — CLEAR: simplex note is remote right.
- P199 O11-O15 — CLEAR: independence result lies below.
- P200 O11-O16 — CLEAR: Beta node lies lower-right.
- P201 O11-O17 — CLEAR: Y1 arrow is far left.
- P202 O11-O18 — CLEAR: Y2 arrow is far left.
- P203 O11-O19 — CLEAR: YK arrow is far left.
- P204 O11-O20 — CLEAR: sum-to-divide arrow is below/left.
- P205 O11-O21 — CLEAR: divide-to-ratio arrow is below/right.
- P206 O11-O22 — CLEAR: final arrow is farther right.
- P207 O11-O23 — CLEAR: dashed sum path lies below/left.
- P208 O11-O24 — CLEAR: dashed ratio path lies below/right.
- P209 O11-O25 — CLEAR: caption is far below badge 3.

## O12 against later objects

- P210 O12-O13 — CLEAR: simplex icon is above O12 with 34 px bbox separation.
- P211 O12-O14 — CLEAR: simplex note remains above O12 with 53 px bbox separation.
- P212 O12-O15 — CLEAR: independence result is lower-left and separate.
- P213 O12-O16 — CLEAR: Beta node is directly below with 93 px bbox separation.
- P214 O12-O17 — CLEAR: Y1 arrow is far left.
- P215 O12-O18 — CLEAR: Y2 arrow is far left.
- P216 O12-O19 — CLEAR: YK arrow is far left.
- P217 O12-O20 — CLEAR: sum-to-divide arrow is far left.
- P218 O12-O21 — CLEAR: divide-to-ratio arrow is left.
- P219 O12-O22 — LEGAL_ENDPOINT: ratio-to-Dirichlet arrow terminates at O12's west border; result text is untouched.
- P220 O12-O23 — CLEAR: dashed sum path is far lower-left.
- P221 O12-O24 — CLEAR: dashed ratio path ends before the lower result and does not reach O12.
- P222 O12-O25 — CLEAR: caption lies well below the result node.

## O13 against later objects

- P223 O13-O14 — CLEAR_BBOX_ONLY: icon and label bboxes meet, but NN8x shows a clean white foreground gap.
- P224 O13-O15 — CLEAR: independence result is far below/left.
- P225 O13-O16 — CLEAR: Beta node is below with ample space.
- P226 O13-O17 — CLEAR: Y1 arrow is far left.
- P227 O13-O18 — CLEAR: Y2 arrow is far left.
- P228 O13-O19 — CLEAR: YK arrow is far left.
- P229 O13-O20 — CLEAR: main arrow is far left.
- P230 O13-O21 — CLEAR: main arrow is far left.
- P231 O13-O22 — CLEAR: final main arrow is below/left and does not touch the icon.
- P232 O13-O23 — CLEAR: dashed sum path is far lower-left.
- P233 O13-O24 — CLEAR: dashed ratio path is below/left.
- P234 O13-O25 — CLEAR: caption is far below the simplex icon.

## O14 against later objects

- P235 O14-O15 — CLEAR: simplex note is far above/right of independence result.
- P236 O14-O16 — CLEAR: simplex note is above Beta node with ample separation.
- P237 O14-O17 — CLEAR: Y1 arrow is far left.
- P238 O14-O18 — CLEAR: Y2 arrow is far left.
- P239 O14-O19 — CLEAR: YK arrow is far left.
- P240 O14-O20 — CLEAR: sum-to-divide arrow is far left.
- P241 O14-O21 — CLEAR: divide-to-ratio arrow is far left.
- P242 O14-O22 — CLEAR: final arrow is below/left; no label contact.
- P243 O14-O23 — CLEAR: dashed sum path is far lower-left.
- P244 O14-O24 — CLEAR: dashed ratio path is lower-left.
- P245 O14-O25 — CLEAR: caption is far below the simplex note.

## O15 against later objects

- P246 O15-O16 — CLEAR: lower result nodes retain a 54 px horizontal bbox gap.
- P247 O15-O17 — CLEAR: Y1 arrow is far upper-left.
- P248 O15-O18 — CLEAR: Y2 arrow is far upper-left.
- P249 O15-O19 — CLEAR: YK arrow is upper-left.
- P250 O15-O20 — CLEAR: sum-to-divide arrow is above/left.
- P251 O15-O21 — CLEAR: divide-to-ratio arrow is above.
- P252 O15-O22 — CLEAR: ratio-to-result arrow is above/right.
- P253 O15-O23 — LEGAL_ENDPOINT: dashed sum evidence path terminates on O15's top border, away from formula ink.
- P254 O15-O24 — LEGAL_ENDPOINT: dashed ratio evidence path terminates on O15's top border, away from formula ink.
- P255 O15-O25 — CLEAR: independence node and caption retain a 25 px bbox gap.

## O16 against later objects

- P256 O16-O17 — CLEAR: Y1 arrow is far upper-left.
- P257 O16-O18 — CLEAR: Y2 arrow is far upper-left.
- P258 O16-O19 — CLEAR: YK arrow is far upper-left.
- P259 O16-O20 — CLEAR: sum-to-divide arrow is above/left.
- P260 O16-O21 — CLEAR: divide-to-ratio arrow is above/left.
- P261 O16-O22 — CLEAR: final main arrow is above.
- P262 O16-O23 — CLEAR: dashed sum path ends at O15, not O16.
- P263 O16-O24 — CLEAR: dashed ratio path also terminates at O15, left of O16.
- P264 O16-O25 — CLEAR: Beta node and caption retain a 25 px bbox gap.

## O17 against later objects

- P265 O17-O18 — CLEAR: upper and middle fan-in arrows are distinct strokes with 28 px bbox gap.
- P266 O17-O19 — CLEAR: upper and lower fan-in arrows are distinctly separated.
- P267 O17-O20 — CLEAR: fan-in and main-chain arrows meet only through O07, not each other.
- P268 O17-O21 — CLEAR: divide-to-ratio arrow is remote right.
- P269 O17-O22 — CLEAR: final arrow is remote right.
- P270 O17-O23 — CLEAR: dashed evidence path is below/right.
- P271 O17-O24 — CLEAR: dashed ratio path is remote.
- P272 O17-O25 — CLEAR: caption is far below the upper fan-in arrow.

## O18 against later objects

- P273 O18-O19 — CLEAR: middle and lower fan-in arrows are distinct with 39 px bbox separation.
- P274 O18-O20 — CLEAR: arrows connect through O07, with no direct stroke collision.
- P275 O18-O21 — CLEAR: divide-to-ratio arrow is remote right.
- P276 O18-O22 — CLEAR: final arrow is remote right.
- P277 O18-O23 — CLEAR: dashed path is below/right.
- P278 O18-O24 — CLEAR: dashed path is remote.
- P279 O18-O25 — CLEAR: caption is far below the middle fan-in arrow.

## O19 against later objects

- P280 O19-O20 — CLEAR: arrows connect through O07, not by direct overlap.
- P281 O19-O21 — CLEAR: divide-to-ratio arrow is remote right.
- P282 O19-O22 — CLEAR: final arrow is remote right.
- P283 O19-O23 — CLEAR: dashed sum path is right with visible separation.
- P284 O19-O24 — CLEAR: dashed ratio path is remote right.
- P285 O19-O25 — CLEAR: caption is below with substantial separation.

## O20 against later objects

- P286 O20-O21 — CLEAR: main arrows are separated by the divide node; their shafts do not meet.
- P287 O20-O22 — CLEAR: final main arrow is remote right.
- P288 O20-O23 — CLEAR: dashed path begins below O07; it does not cross O20.
- P289 O20-O24 — CLEAR: dashed ratio path is remote lower-right.
- P290 O20-O25 — CLEAR: caption is far below O20.

## O21 against later objects

- P291 O21-O22 — CLEAR: main arrows are separated by the ratio node.
- P292 O21-O23 — CLEAR: dashed sum path is lower-left.
- P293 O21-O24 — CLEAR: dashed ratio path starts below O10 and does not cross O21.
- P294 O21-O25 — CLEAR: caption is far below O21.

## O22 against later objects

- P295 O22-O23 — CLEAR: dashed sum path is far lower-left.
- P296 O22-O24 — CLEAR: dashed ratio path is below/left and does not touch O22.
- P297 O22-O25 — CLEAR: caption is far below the final main arrow.

## O23 against later objects

- P298 O23-O24 — CLEAR: two dashed evidence paths are spatially separated and terminate at different top-border positions.
- P299 O23-O25 — CLEAR: dashed sum path ends above O15, leaving 143 px bbox clearance to caption.

## O24 against later objects

- P300 O24-O25 — CLEAR: dashed ratio path ends above O15, leaving 143 px bbox clearance to caption.

## Manual totals

- Total pair IDs manually adjudicated: **300**.
- `LEGAL_ENDPOINT`: **16** intended connector contacts.
- `CLEAR_BBOX_ONLY`: **3** bbox-only proximity candidates (`P025`, `P039`, `P223`) with no native foreground contact.
- Remaining `CLEAR`: **281**.
- Hard illegal collisions: **0 pairs / 0 pixels**.
- Unresolved pairs: **0**.
