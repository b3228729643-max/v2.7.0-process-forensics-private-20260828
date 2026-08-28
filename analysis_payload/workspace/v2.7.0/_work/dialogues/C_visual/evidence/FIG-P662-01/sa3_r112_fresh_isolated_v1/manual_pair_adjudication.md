# Manual unordered-pair adjudication

Reviewer identity: `C-FIG-P662-01-R112-SA3-FRESH-ISOLATED-V1`  
Frozen denominator: 26 authored visible objects (`O01`--`O26`)  
Expected unordered pairs: `26*25/2 = 325`  
Machine enumeration: `P001`--`P325` in `machine_pairs.csv`

I opened the native semantic overlay and every native/nearest risk ROI before assigning the decisions below. No decision was copied from another reviewer or role. Codes are manual decisions, not machine PASS defaults:

- `CD`: clear disjoint pair; native ink is spatially separate and the pair has zero raster-mask intersection.
- `CT`: close pair manually confirmed distinct in native/NN8x pixels; no visible-ink intersection or obstruction.
- `EP`: intended connector endpoint/adjacency; the line joins or approaches a node border as authored and does not touch reader text.
- `IC_MC`: intended containment with mask contamination; one semantic object lies inside another object's bbox but their foreground boundaries do not collide.
- `CT_MC`: close but visibly separate; the nonzero candidate comes from bbox/composite-mask capture, not shared semantic foreground.
- `EP_MC`: intended structural endpoint; duplicated composite-mask pixels are not an illegal collision.

## Per-ID decisions

O01 pairs: P001:CD, P002:CD, P003:CD, P004:CD, P005:CD, P006:CD, P007:CD, P008:CD, P009:CD, P010:CD, P011:CD, P012:CD, P013:CD, P014:CD, P015:CD, P016:CD, P017:CD, P018:CD, P019:CD, P020:CD, P021:CD, P022:CD, P023:CD, P024:CD, P025:CD.

O02 pairs: P026:CD, P027:CD, P028:CD, P029:CD, P030:CD, P031:CD, P032:CD, P033:CD, P034:CD, P035:CD, P036:CD, P037:CD, P038:CD, P039:CD, P040:CD, P041:EP, P042:CD, P043:CD, P044:CD, P045:CD, P046:CD, P047:CD, P048:CD, P049:CD.

O03 pairs: P050:CT, P051:CD, P052:CD, P053:CD, P054:CD, P055:CD, P056:CD, P057:CD, P058:CD, P059:CD, P060:CD, P061:CD, P062:CD, P063:CD, P064:CT, P065:EP, P066:CD, P067:CD, P068:CD, P069:CD, P070:CD, P071:CD, P072:CD.

O04 pairs: P073:CD, P074:CD, P075:CD, P076:CD, P077:CD, P078:CD, P079:CD, P080:CD, P081:CD, P082:CD, P083:CD, P084:CD, P085:CD, P086:CD, P087:CD, P088:CD, P089:CD, P090:CD, P091:CD, P092:CD, P093:CD, P094:CD.

O05 pairs: P095:CD, P096:CD, P097:CD, P098:CD, P099:CD, P100:CD, P101:CD, P102:CD, P103:CD, P104:CD, P105:CD, P106:CD, P107:CD, P108:CD, P109:EP, P110:CD, P111:CD, P112:CD, P113:CD, P114:CD, P115:CD.

O06 pairs: P116:CD, P117:CD, P118:CD, P119:CD, P120:CD, P121:CD, P122:CD, P123:CD, P124:CD, P125:CD, P126:CD, P127:CD, P128:CD, P129:CD, P130:CD, P131:CD, P132:CD, P133:CD, P134:CD, P135:CD.

O07 pairs: P136:CD, P137:CD, P138:CD, P139:CD, P140:CD, P141:CD, P142:CD, P143:CD, P144:CD, P145:CD, P146:CD, P147:CD, P148:CD, P149:CD, P150:CD, P151:CD, P152:CD, P153:CD, P154:CD.

O08 pairs: P155:CD, P156:CD, P157:CD, P158:CD, P159:CD, P160:CD, P161:CD, P162:CD, P163:CD, P164:EP, P165:EP, P166:EP, P167:EP, P168:CD, P169:CD, P170:EP, P171:CD, P172:CD.

O09 pairs: P173:CD, P174:CD, P175:CD, P176:CD, P177:CD, P178:CD, P179:CD, P180:CD, P181:CD, P182:CD, P183:CD, P184:EP, P185:EP, P186:CD, P187:CD, P188:CD, P189:CD.

O10 pairs: P190:CD, P191:CD, P192:CD, P193:CD, P194:CD, P195:CD, P196:CD, P197:CD, P198:CD, P199:CD, P200:CD, P201:CD, P202:CD, P203:CD, P204:CD, P205:CD.

O11 pairs: P206:CD, P207:CD, P208:CD, P209:CD, P210:CD, P211:CD, P212:CD, P213:CD, P214:CD, P215:CD, P216:EP, P217:EP, P218:CD, P219:EP, P220:CD.

O12 pairs: P221:CD, P222:CD, P223:CD, P224:CD, P225:CD, P226:CD, P227:CD, P228:CD, P229:CD, P230:CD, P231:EP, P232:CD, P233:CD, P234:CD.

O13 pairs: P235:IC_MC, P236:CT_MC, P237:CD, P238:CD, P239:CD, P240:CD, P241:CD, P242:CD, P243:CD, P244:CD, P245:CD, P246:CD, P247:CD.

O14 pairs: P248:CD, P249:CD, P250:CD, P251:CD, P252:CD, P253:CD, P254:CD, P255:CD, P256:CD, P257:CD, P258:CD, P259:CD.

O15 pairs: P260:CD, P261:CD, P262:CD, P263:CD, P264:CD, P265:CD, P266:CD, P267:CD, P268:CD, P269:CD, P270:CD.

O16 pairs: P271:CD, P272:CD, P273:CD, P274:CD, P275:CD, P276:CD, P277:CD, P278:EP_MC, P279:EP, P280:CD.

O17 pairs: P281:CD, P282:CD, P283:CD, P284:CD, P285:CD, P286:CD, P287:CD, P288:CD, P289:CD.

O18 pairs: P290:CD, P291:CD, P292:CD, P293:CD, P294:CD, P295:CD, P296:CD, P297:CD.

O19 pairs: P298:CD, P299:CD, P300:CD, P301:CD, P302:CD, P303:CD, P304:CD.

O20 pairs: P305:CD, P306:CD, P307:CD, P308:CD, P309:CD, P310:CD.

O21 pairs: P311:CD, P312:CD, P313:CD, P314:CD, P315:CD.

O22 pairs: P316:CD, P317:CD, P318:CD, P319:CD.

O23 pairs: P320:CD, P321:CD, P322:CD.

O24 pairs: P323:CD, P324:CD.

O25 pair: P325:CD.

## Close/structural pair reasons

| Pair ID | Objects | Manual native-pixel reason |
|---|---|---|
| P041 | O02--O18 | The Y1 arrow originates just outside the node's right border; no node text or border ink is obscured. |
| P050 | O03--O04 | The ellipsis begins below the second input node; native ink remains distinct despite the conservative bbox gap. |
| P064 | O03--O18 | The descending Y1 arrow passes to the right of O03; NN8x fan-in view shows a white separator and no shared ink. |
| P065 | O03--O19 | The Y2 arrow originates at the right-side structural port and does not touch formula ink. |
| P109 | O05--O20 | The YK arrow originates at the right-side structural port and does not touch formula ink. |
| P164 | O08--O18 | The Y1 arrowhead terminates at the total-node border; its direction remains visible and it does not enter the formula. |
| P165 | O08--O19 | The Y2 arrowhead terminates at the total-node border; the horizontal route is clear. |
| P166 | O08--O20 | The YK arrowhead terminates at the total-node border; it does not enter the lower formula line. |
| P167 | O08--O21 | Main-flow arrow leaves the total-node right border and remains clear of both title and summation. |
| P170 | O08--O24 | Dashed auxiliary path leaves the total-node bottom border; the port is below the formula. |
| P184 | O09--O21 | Main arrow enters the division circle at its left boundary and does not touch the centered divide-by-S glyph. |
| P185 | O09--O22 | Main arrow leaves the division circle at its right boundary and does not touch the centered formula. |
| P216 | O11--O22 | Main arrow enters the ratio node at the left boundary, below/aside from reader text. |
| P217 | O11--O23 | Main arrow leaves the ratio node at the right boundary, clear of the ratio formula. |
| P219 | O11--O25 | Dashed auxiliary path leaves the ratio-node bottom border at a clear structural port. |
| P231 | O12--O23 | Main arrow terminates at the Dirichlet-node left border without entering formula ink. |
| P235 | O13--O14 | The point is strictly inside the triangle. The 185 machine pixels arise because O13's rectangular extraction also captures the point; triangle edges and point do not touch. |
| P236 | O13--O15 | NN8x shows a white gap between triangle edge and label. The 6 machine pixels are bbox/composite-mask antialias capture, not shared semantic foreground. |
| P278 | O16--O24 | Five duplicated pixels occur where the dashed path meets the independence-node top border; this is an intended connector-border junction and does not obscure text. |
| P279 | O16--O25 | The second dashed path terminates at the independence-node top border with no measured shared ink and no text contact. |

## Candidate reconciliation

- Machine nonzero candidate pairs: P235 = 185 px, P236 = 6 px, P278 = 5 px.
- `OVERLAP_CANDIDATE_PIXEL_COUNT = 196`.
- All 196 candidate pixels are classified as confirmed composite/bbox mask contamination or intended structural endpoint duplication.
- `MASK_CONTAMINATION_PIXEL_COUNT = 196`.
- `OVERLAP_PIXEL_COUNT = 0` because no candidate is a true illegal visible-ink collision.
- `UNRESOLVED_PAIR_COUNT = 0`.

Pair conclusion: every one of P001--P325 has an explicit manual decision; no illegal visible-ink overlap or obstructive adjacency was found.
