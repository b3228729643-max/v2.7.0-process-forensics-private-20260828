# FIG-P033-01 R111 SA3 manual near/intersection pair ledger

Reviewer: `/root/p033_r111_fresh_sa3` (`gpt-5.6-sol/xhigh`)

The machine enumerated all 4,560 unordered atom pairs without adjudication. Exactly 131 pairs had intersecting PDF bboxes or a bbox gap no greater than 4 native-300-dpi pixels; those 131 IDs are manually adjudicated below after opening the native 1× and nearest-neighbour 8× ROIs. The other 4,429 pair IDs have disjoint conservative bboxes separated by more than 4 pixels and therefore cannot share rendered foreground pixels.

| PAIR_ID | Atoms | Observed at native/NN8x | Decision | Note | PASS |
|---|---|---|---|---|---|
| PAIR-001 | GLYPH-001 / GLYPH-002 | Adjacent Chinese glyphs have distinct ink | NO_ILLEGAL_OVERLAP | Normal word spacing in `子空间` | PASS |
| PAIR-096 | GLYPH-002 / GLYPH-003 | Adjacent Chinese glyphs have distinct ink | NO_ILLEGAL_OVERLAP | Normal word spacing in `子空间` | PASS |
| PAIR-457 | GLYPH-005 / PATH-003 | `x` label ink is separate from blue shaft | NO_ILLEGAL_OVERLAP | Diagonal shaft bbox overreaches actual ink | PASS |
| PAIR-545 | GLYPH-006 / PATH-001 | `p` glyph is visually clear of upper edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-546 | GLYPH-006 / PATH-002 | `p` glyph is visually clear of lower edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-547 | GLYPH-006 / PATH-003 | `p` glyph is visually clear of blue shaft | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-549 | GLYPH-006 / PATH-005 | `p` glyph is visually clear of teal shaft | NO_ILLEGAL_OVERLAP | Label sits below the shaft | PASS |
| PAIR-634 | GLYPH-007 / PATH-001 | equals sign is clear of upper edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-635 | GLYPH-007 / PATH-002 | equals sign is clear of lower edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-636 | GLYPH-007 / PATH-003 | equals sign is clear of blue shaft | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-638 | GLYPH-007 / PATH-005 | equals sign is clear of teal shaft | NO_ILLEGAL_OVERLAP | Label sits below the shaft | PASS |
| PAIR-645 | GLYPH-008 / GLYPH-009 | `P` and its subscript `S` form a lawful math attachment | INTENDED_MATH_ATTACHMENT | Glyph inks remain distinguishable | PASS |
| PAIR-722 | GLYPH-008 / PATH-001 | `P` glyph is clear of upper edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-723 | GLYPH-008 / PATH-002 | `P` glyph is clear of lower edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-724 | GLYPH-008 / PATH-003 | `P` glyph is clear of blue shaft | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-726 | GLYPH-008 / PATH-005 | `P` glyph is clear of teal shaft | NO_ILLEGAL_OVERLAP | Label sits below the shaft | PASS |
| PAIR-733 | GLYPH-009 / GLYPH-010 | subscript `S` and following `x` are visibly separated | NO_ILLEGAL_OVERLAP | Lawful compact math spacing | PASS |
| PAIR-809 | GLYPH-009 / PATH-001 | subscript `S` is clear of upper edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-810 | GLYPH-009 / PATH-002 | subscript `S` is clear of lower edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-811 | GLYPH-009 / PATH-003 | subscript `S` is clear of blue shaft | NO_ILLEGAL_OVERLAP | Positive pixel gap remains | PASS |
| PAIR-813 | GLYPH-009 / PATH-005 | subscript `S` is clear of teal shaft | NO_ILLEGAL_OVERLAP | Label sits below the shaft | PASS |
| PAIR-895 | GLYPH-010 / PATH-001 | formula `x` is clear of upper edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-896 | GLYPH-010 / PATH-002 | formula `x` is clear of lower edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-899 | GLYPH-010 / PATH-005 | formula `x` is clear of teal shaft | NO_ILLEGAL_OVERLAP | Label sits below the shaft | PASS |
| PAIR-980 | GLYPH-011 / PATH-001 | membership sign is clear of upper edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-981 | GLYPH-011 / PATH-002 | membership sign is clear of lower edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-984 | GLYPH-011 / PATH-005 | membership sign is clear of teal shaft | NO_ILLEGAL_OVERLAP | Label sits below the shaft | PASS |
| PAIR-1064 | GLYPH-012 / PATH-001 | terminal `S` is clear of upper edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-1065 | GLYPH-012 / PATH-002 | terminal `S` is clear of lower edge | NO_ILLEGAL_OVERLAP | Coarse diagonal bbox only | PASS |
| PAIR-1153 | GLYPH-013 / PATH-007 | residual `r` label ink is clear of dashed shaft | NO_ILLEGAL_OVERLAP | White knockout and actual placement preserve separation | PASS |
| PAIR-1156 | GLYPH-013 / PATH-010 | residual `r` label ink is clear of brace | NO_ILLEGAL_OVERLAP | Bbox overlap only; native ink is separate | PASS |
| PAIR-1238 | GLYPH-014 / PATH-010 | residual equals sign is clear of brace | NO_ILLEGAL_OVERLAP | Bbox overlap only | PASS |
| PAIR-1558 | GLYPH-019 / GLYPH-020 | `S` and superscript orthogonal marker are distinct | INTENDED_MATH_ATTACHMENT | Correct `S^perp` notation | PASS |
| PAIR-1711 | GLYPH-021 / GLYPH-022 | `最` and `短` have distinct ink | NO_ILLEGAL_OVERLAP | Normal CJK adjacency | PASS |
| PAIR-1775 | GLYPH-021 / PATH-001 | `最` is clear of upper band edge | NO_ILLEGAL_OVERLAP | White knockout visibly separates text and line | PASS |
| PAIR-1786 | GLYPH-022 / GLYPH-023 | `短` and `距` have distinct ink | NO_ILLEGAL_OVERLAP | Normal CJK adjacency | PASS |
| PAIR-1849 | GLYPH-022 / PATH-001 | `短` is clear of upper band edge | NO_ILLEGAL_OVERLAP | White knockout visibly separates text and line | PASS |
| PAIR-1860 | GLYPH-023 / GLYPH-024 | `距` and `离` have distinct ink | NO_ILLEGAL_OVERLAP | Normal CJK adjacency | PASS |
| PAIR-1922 | GLYPH-023 / PATH-001 | `距` is clear of upper band edge | NO_ILLEGAL_OVERLAP | White knockout visibly separates text and line | PASS |
| PAIR-1994 | GLYPH-024 / PATH-001 | `离` is clear of upper band edge | NO_ILLEGAL_OVERLAP | White knockout visibly separates text and line | PASS |
| PAIR-2005 | GLYPH-025 / GLYPH-026 | norm bar and `x` remain distinct | INTENDED_MATH_SPACING | Compact norm notation, no ink collision | PASS |
| PAIR-2075 | GLYPH-025 / PATH-011 | opening norm bar is contained clear of note border | INTENDED_CONTAINMENT | No border-to-glyph contact | PASS |
| PAIR-2076 | GLYPH-026 / GLYPH-027 | `x` and closing norm bar remain distinct | INTENDED_MATH_SPACING | Compact norm notation | PASS |
| PAIR-2145 | GLYPH-026 / PATH-011 | `x` is contained clear of note border | INTENDED_CONTAINMENT | Ample interior clearance | PASS |
| PAIR-2146 | GLYPH-027 / GLYPH-028 | norm bar and exponent form lawful attachment | INTENDED_MATH_ATTACHMENT | Superscript is legible | PASS |
| PAIR-2214 | GLYPH-027 / PATH-011 | closing norm bar is contained clear of note border | INTENDED_CONTAINMENT | No border contact | PASS |
| PAIR-2282 | GLYPH-028 / PATH-011 | exponent `2` is contained clear of note border | INTENDED_CONTAINMENT | Top clearance remains | PASS |
| PAIR-2349 | GLYPH-029 / PATH-011 | equality sign is contained clear of note border | INTENDED_CONTAINMENT | Ample interior clearance | PASS |
| PAIR-2350 | GLYPH-030 / GLYPH-031 | norm bar and `p` remain distinct | INTENDED_MATH_SPACING | Compact norm notation | PASS |
| PAIR-2415 | GLYPH-030 / PATH-011 | opening `p` norm bar is clear of note border | INTENDED_CONTAINMENT | No border contact | PASS |
| PAIR-2416 | GLYPH-031 / GLYPH-032 | `p` and closing norm bar are visually distinct | INTENDED_MATH_SPACING | Bboxes touch; inks do not merge | PASS |
| PAIR-2480 | GLYPH-031 / PATH-011 | `p` is contained clear of note border | INTENDED_CONTAINMENT | Ample interior clearance | PASS |
| PAIR-2481 | GLYPH-032 / GLYPH-033 | norm bar and exponent form lawful attachment | INTENDED_MATH_ATTACHMENT | Superscript is legible | PASS |
| PAIR-2544 | GLYPH-032 / PATH-011 | closing `p` norm bar is clear of border | INTENDED_CONTAINMENT | No border contact | PASS |
| PAIR-2607 | GLYPH-033 / PATH-011 | `p` exponent is clear of note border | INTENDED_CONTAINMENT | Top clearance remains | PASS |
| PAIR-2669 | GLYPH-034 / PATH-011 | plus sign is clear of note border | INTENDED_CONTAINMENT | Centered with ample clearance | PASS |
| PAIR-2670 | GLYPH-035 / GLYPH-036 | norm bar and `r` remain distinct | INTENDED_MATH_SPACING | Compact norm notation | PASS |
| PAIR-2730 | GLYPH-035 / PATH-011 | opening `r` norm bar is clear of border | INTENDED_CONTAINMENT | No border contact | PASS |
| PAIR-2731 | GLYPH-036 / GLYPH-037 | `r` and closing norm bar remain distinct | INTENDED_MATH_SPACING | Compact norm notation | PASS |
| PAIR-2790 | GLYPH-036 / PATH-011 | `r` is contained clear of note border | INTENDED_CONTAINMENT | Ample interior clearance | PASS |
| PAIR-2791 | GLYPH-037 / GLYPH-038 | norm bar and exponent form lawful attachment | INTENDED_MATH_ATTACHMENT | Superscript is legible | PASS |
| PAIR-2849 | GLYPH-037 / PATH-011 | closing `r` norm bar is clear of border | INTENDED_CONTAINMENT | No border contact | PASS |
| PAIR-2907 | GLYPH-038 / PATH-011 | `r` exponent is clear of note border | INTENDED_CONTAINMENT | Top clearance remains | PASS |
| PAIR-2965 | GLYPH-040 / GLYPH-041 | digit `2` and decimal point are distinct | NO_ILLEGAL_OVERLAP | Correct figure number | PASS |
| PAIR-3021 | GLYPH-041 / GLYPH-042 | decimal point and digit `1` are distinct | NO_ILLEGAL_OVERLAP | Correct figure number | PASS |
| PAIR-3130 | GLYPH-043 / GLYPH-044 | Caption glyphs `向/量` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3183 | GLYPH-044 / GLYPH-045 | Caption glyphs `量/的` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3235 | GLYPH-045 / GLYPH-046 | Caption glyphs `的/正` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3286 | GLYPH-046 / GLYPH-047 | Caption glyphs `正/交` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3336 | GLYPH-047 / GLYPH-048 | Caption glyphs `交/分` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3385 | GLYPH-048 / GLYPH-049 | Caption glyphs `分/解` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3433 | GLYPH-049 / GLYPH-050 | `解` and full stop remain distinct | NO_ILLEGAL_OVERLAP | Normal punctuation spacing | PASS |
| PAIR-3480 | GLYPH-050 / GLYPH-051 | Full stop and following `投` remain distinct | NO_ILLEGAL_OVERLAP | Bboxes touch due punctuation sidebearing; inks are clear | PASS |
| PAIR-3526 | GLYPH-051 / GLYPH-052 | Caption glyphs `投/影` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3571 | GLYPH-052 / GLYPH-053 | Caption glyphs `影/向` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3615 | GLYPH-053 / GLYPH-054 | Caption glyphs `向/量` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3658 | GLYPH-054 / GLYPH-055 | Caption glyphs `量/属` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3700 | GLYPH-055 / GLYPH-056 | Caption glyphs `属/于` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3741 | GLYPH-056 / GLYPH-057 | Caption glyphs `于/子` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3781 | GLYPH-057 / GLYPH-058 | Caption glyphs `子/空` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3820 | GLYPH-058 / GLYPH-059 | Caption glyphs `空/间` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3858 | GLYPH-059 / GLYPH-060 | `间` and comma remain distinct | NO_ILLEGAL_OVERLAP | Normal punctuation spacing | PASS |
| PAIR-3895 | GLYPH-060 / GLYPH-061 | Comma and following `残` remain distinct | NO_ILLEGAL_OVERLAP | Bboxes touch; inks remain clear | PASS |
| PAIR-3931 | GLYPH-061 / GLYPH-062 | Caption glyphs `残/差` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-3966 | GLYPH-062 / GLYPH-063 | Caption glyphs `差/属` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4000 | GLYPH-063 / GLYPH-064 | Caption glyphs `属/于` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4033 | GLYPH-064 / GLYPH-065 | Caption glyphs `于/其` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4065 | GLYPH-065 / GLYPH-066 | Caption glyphs `其/正` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4096 | GLYPH-066 / GLYPH-067 | Caption glyphs `正/交` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4126 | GLYPH-067 / GLYPH-068 | Caption glyphs `交/补` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4155 | GLYPH-068 / GLYPH-069 | `补` and comma remain distinct | NO_ILLEGAL_OVERLAP | Normal punctuation spacing | PASS |
| PAIR-4183 | GLYPH-069 / GLYPH-070 | Comma and following `虚` remain distinct | NO_ILLEGAL_OVERLAP | Bboxes touch; inks remain clear | PASS |
| PAIR-4210 | GLYPH-070 / GLYPH-071 | Caption glyphs `虚/线` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4236 | GLYPH-071 / GLYPH-072 | Caption glyphs `线/残` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4261 | GLYPH-072 / GLYPH-073 | Caption glyphs `残/差` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4285 | GLYPH-073 / GLYPH-074 | Caption glyphs `差/给` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4308 | GLYPH-074 / GLYPH-075 | Caption glyphs `给/出` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4330 | GLYPH-075 / GLYPH-076 | Caption glyphs `出/到` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4351 | GLYPH-076 / GLYPH-077 | Caption glyphs `到/子` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4371 | GLYPH-077 / GLYPH-078 | Caption glyphs `子/空` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4390 | GLYPH-078 / GLYPH-079 | Caption glyphs `空/间` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4408 | GLYPH-079 / GLYPH-080 | Caption glyphs `间/的` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4425 | GLYPH-080 / GLYPH-081 | Caption glyphs `的/最` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4441 | GLYPH-081 / GLYPH-082 | Caption glyphs `最/短` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4456 | GLYPH-082 / GLYPH-083 | Caption glyphs `短/距` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4470 | GLYPH-083 / GLYPH-084 | Caption glyphs `距/离` remain distinct | NO_ILLEGAL_OVERLAP | Normal CJK setting | PASS |
| PAIR-4483 | GLYPH-084 / GLYPH-085 | `离` and final full stop remain distinct | NO_ILLEGAL_OVERLAP | Final punctuation is not clipped | PASS |
| PAIR-4506 | PATH-001 / PATH-002 | Band edges are parallel and visibly separated | NO_ILLEGAL_OVERLAP | Large diagonal bboxes overlap only | PASS |
| PAIR-4507 | PATH-001 / PATH-003 | Blue vector crosses upper band edge once | INTENDED_GEOMETRY_CONTACT | Vector leaves subspace field; crossing carries meaning | PASS |
| PAIR-4509 | PATH-001 / PATH-005 | Upper edge and teal projection shaft are distinct | NO_ILLEGAL_OVERLAP | Shaft runs inside the band | PASS |
| PAIR-4510 | PATH-001 / PATH-006 | Upper edge and projection arrowhead are distinct | NO_ILLEGAL_OVERLAP | Projection point remains inside band | PASS |
| PAIR-4511 | PATH-001 / PATH-007 | Residual crosses upper band edge once | INTENDED_GEOMETRY_CONTACT | Residual leaves S toward S-perp | PASS |
| PAIR-4513 | PATH-001 / PATH-009 | Right-angle marker meets/crosses local edge region | INTENDED_GEOMETRY_CONTACT | Marker certifies orthogonality at projection point | PASS |
| PAIR-4514 | PATH-001 / PATH-010 | Brace crosses the upper band edge | INTENDED_GEOMETRY_CONTACT | Brace endpoint is anchored at projected point inside band | PASS |
| PAIR-4516 | PATH-002 / PATH-003 | Lower edge and blue shaft are visibly separate | NO_ILLEGAL_OVERLAP | Coarse diagonal bboxes overlap only | PASS |
| PAIR-4518 | PATH-002 / PATH-005 | Lower edge and teal shaft are visibly separate | NO_ILLEGAL_OVERLAP | Parallel-ish objects retain clear gap | PASS |
| PAIR-4519 | PATH-002 / PATH-006 | Lower edge and teal arrowhead are separate | NO_ILLEGAL_OVERLAP | Projection point is above lower edge | PASS |
| PAIR-4520 | PATH-002 / PATH-007 | Lower edge and residual shaft are separate | NO_ILLEGAL_OVERLAP | Residual rises from point inside band | PASS |
| PAIR-4522 | PATH-002 / PATH-009 | Lower edge and right-angle marker are separate | NO_ILLEGAL_OVERLAP | Marker remains near projection point | PASS |
| PAIR-4523 | PATH-002 / PATH-010 | Lower edge and brace are separate | NO_ILLEGAL_OVERLAP | Coarse bbox only | PASS |
| PAIR-4525 | PATH-003 / PATH-004 | Blue shaft joins blue arrowhead | INTENDED_GEOMETRY_CONTACT | Required arrow construction at X | PASS |
| PAIR-4526 | PATH-003 / PATH-005 | Blue and teal vector shafts share origin | INTENDED_GEOMETRY_CONTACT | Common tail O is mathematically required | PASS |
| PAIR-4540 | PATH-005 / PATH-006 | Teal shaft joins teal arrowhead | INTENDED_GEOMETRY_CONTACT | Required arrow construction at P | PASS |
| PAIR-4541 | PATH-005 / PATH-007 | Teal shaft and residual shaft remain narrowly separate | NO_ILLEGAL_OVERLAP | Connection is mediated by the teal arrowhead; no confusing merge | PASS |
| PAIR-4543 | PATH-005 / PATH-009 | Projection shaft and right-angle marker meet at P | INTENDED_GEOMETRY_CONTACT | Required orthogonality certificate | PASS |
| PAIR-4546 | PATH-006 / PATH-007 | Teal head and residual start are endpoint-adjacent | INTENDED_GEOMETRY_CONTACT | Shows decomposition `x=p+r`; no ambiguity | PASS |
| PAIR-4548 | PATH-006 / PATH-009 | Teal head and right-angle marker meet at P | INTENDED_GEOMETRY_CONTACT | Shared projection point is required | PASS |
| PAIR-4551 | PATH-007 / PATH-008 | Residual shaft joins residual arrowhead | INTENDED_GEOMETRY_CONTACT | Required arrow construction at X | PASS |
| PAIR-4552 | PATH-007 / PATH-009 | Residual shaft and right-angle marker meet at P | INTENDED_GEOMETRY_CONTACT | Required perpendicular relationship | PASS |
| PAIR-4553 | PATH-007 / PATH-010 | Residual and brace remain parallel with visible separation | NO_ILLEGAL_OVERLAP | Brace measures the residual without covering it | PASS |
| PAIR-4558 | PATH-009 / PATH-010 | Right-angle marker and brace remain distinguishable near P | NO_ILLEGAL_OVERLAP | Their strokes do not merge into a misleading symbol | PASS |

Manual candidate result: 131/131 PASS; zero TRUE_COLLISION pairs. Together with the 4,429 bbox-separated machine-clear pairs, all 4,560 unordered pairs are resolved.
