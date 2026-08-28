# Fresh SA1 rerun review — FIG-P602-01 / R101

## Reviewer and freshness

- Reviewer: /root/sa1_fig_p602_r101_rerun, fresh read-only SA1, GPT-5 family.
- It did not read SA1_REVIEW.md, any earlier SA1 output, or prior PASS/FAIL conclusion.
- It wrote no file, changed no source/state/manifest/macro, launched no subagent, and ran no TeX/build.
- Machine fields were evidence only. Every required ID received an independent manual decision.
- Review used the corrected current ledger: P297 B04/E06 is distinct geometry and P310 B06/E06 is the self-loop endpoint.

## Identity and denominators

- UID FIG-P602-01; scope row B52; branch denominator 46.
- Candidate SHA-256: 0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1; 4,947,496 bytes; 814 pages.
- Target: PDF page 651, printed page 638, figure 32.5.
- Native page PNG SHA-256: 8E0DCE21A10BFCAAA5A5BE40627110E262459C0BE586626C9AF4EC8CAEC03C71.
- Source SHA-256: 18B88F4BC48A21D3FD1A246AC5B6909DEEB19900A3D0721C65F9A44369444084.
- Coverage: objects 26/26; glyphs 175/175; pairs 325/325; critical 8/8; peers 27/27; roles 50/50; clipping 26/26.
- WRITE_STOPPED=true; source writer none; TeX slot disabled.
- Full glyph decisions: SA1_RERUN_GLYPH_LEDGER.md.
- Full pair decisions: SA1_RERUN_PAIR_LEDGER.md.

## OBJECT_LEDGER

- T01 — PASS — current-state text complete and source-consistent; 1x/8x masks 2207/99535, uncontaminated.
- T02 — PASS — proposal text and Y=y complete and correctly ordered; masks 3477/164028.
- T03 — PASS — acceptance-rate label and positive-flow condition complete; masks 3647/169439.
- T04 — PASS — entire ratio formula, fraction, braces, tilde-pi terms and arguments intact; masks 8171/422308.
- T05 — PASS — two-line uniform draw and comparison, including ∼, ≤ and ？, intact; masks 4879/232464.
- T06 — PASS — accept outcome and X_(t+1)=y complete and centered; masks 2774/127107.
- T07 — PASS — reject outcome and X_(t+1)=x complete and centered; masks 3980/180879.
- T08 — PASS — 提议 intact after 81/4473 owned-edge candidate pixels were removed; final masks isolate the label.
- T09 — PASS — 计算 complete and isolated; masks 768/33956.
- T10 — PASS — 判定 complete and isolated; masks 827/34394.
- T11 — PASS — 接受 branch label complete and separated; masks 906/40403.
- T12 — PASS — 拒绝 branch label complete and separated; masks 913/40072.
- T13 — PASS — 自环：保留 x complete, including colon and mathematical x; masks 1827/82169.
- T14 — PASS — caption number, English name and Chinese description complete and source-matching; masks 11257/546143.
- B01 — PASS — current-state rounded border continuous at 1x/8x; masks 4963/277165.
- B02 — PASS — proposal rounded border continuous and distinct; masks 4188/208823.
- B03 — PASS — ratio rounded border continuous with ample T03/T04 inset; masks 13547/684793.
- B04 — PASS — decision diamond continuous with four proper vertices; masks 9169/493839.
- B05 — PASS — accept rounded border continuous; masks 5086/277650.
- B06 — PASS — reject double rounded border complete and visibly double; masks 12398/744626.
- E01 — PASS — dashed proposal arrow complete from B01 toward B02; masks 239/13681.
- E02 — PASS — calculation arrow complete from B02 toward B03; masks 293/18046.
- E03 — PASS — decision arrow complete from B03 toward B04; masks 266/16290.
- E04 — PASS — solid accept branch and arrowhead complete; masks 1433/78121.
- E05 — PASS — patterned reject branch and arrowhead complete; masks 1116/59835.
- E06 — PASS — patterned rejection self-loop complete, returns to B06, and does not connect to B04; masks 3616/192357.

## CRITICAL_LEDGER

- P265 B01/E01 — PASS — 1x shows E01 starting at B01 lower border; 8x confines 212 overlap pixels to the line-cap/border junction; illegal 0/0.
- P276 B02/E02 — PASS — 1x shows E02 departing B02 centrally; 8x confines 226 pixels to the endpoint; illegal 0/0.
- P286 B03/E03 — PASS — 1x shows E03 departing the ratio box; 8x confines 229 pixels to the intended endpoint; illegal 0/0.
- P295 B04/E04 — PASS — 1x shows the accept branch attached to the diamond; 8x confines 555 pixels to the rounded cap/sloped-border junction; illegal 0/0.
- P296 B04/E05 — PASS — 1x shows the reject branch attached to the opposite diamond side; 8x confines 500 pixels to that endpoint; illegal 0/0.
- P302 B05/E04 — PASS — accept arrowhead lands on B05; 8x shows 843 contact pixels without crossing the border; illegal 0/0.
- P309 B06/E05 — PASS — reject arrowhead lands on B06 outer top border; 8x confines 4433 pixels to the arrowhead footprint without entering text/inner border; illegal 0/0.
- P310 B06/E06 — PASS — loop returns at B06 lower-left corner; 8x confines 98 pixels to the curved-border endpoint; illegal 0/0.

## PEER_LEDGER

- G007 — PASS — equals, STIX Math 9.56414 bp; 4 peers; h12/A173; ratios 1.0/1.0.
- G013 — PASS — comma; 4 peers; h11/A45; ratios 1.0/1.0.
- G014 — PASS — centered dot h5/A25; complete and source-metric appropriate for \cdot.
- G021 — PASS — equals; 4 peers; h12/A173; ratios 1.0/1.0.
- G032 — PASS — comma; 4 peers; h11/A45; ratios 1.0/1.0.
- G035 — PASS — greater-than h23/A151; both diagonals complete.
- G041 — PASS — 11.2-pt comma; 4 peers; h12/A57; ratios 1.0/1.0.
- G044 — PASS — 11.2-pt equals h14/A230; both bars complete.
- G050 — PASS — 11.2-pt comma; h12/A56; ratios 1.0/0.982456; antialias-only one-pixel area variation.
- G059 — PASS — 11.2-pt comma; h12/A57; ratios 1.0/1.0.
- G070 — PASS — 11.2-pt comma; h12/A57; ratios 1.0/1.0.
- G077 — PASS — ∼ h9/A101; complete wave agrees with \sim.
- G081 — PASS — comma; 4 peers; h11/A45; ratios 1.0/1.0.
- G088 — PASS — ≤ h30/A240; diagonals and lower bar complete.
- G092 — PASS — comma; 4 peers; h11/A45; ratios 1.0/1.0.
- G095 — PASS — full-width question mark h32/A125; hook and dot present.
- G102 — PASS — script plus; 2 peers; h19/A105; ratios 1.0/1.0.
- G104 — PASS — equals; 4 peers; h12/A173; ratios 1.0/1.0.
- G116 — PASS — script plus; 2 peers; h19/A105; ratios 1.0/1.0.
- G118 — PASS — equals; 4 peers; h12/A173; ratios 1.0/1.0.
- G132 — PASS — full-width colon h21/A39; both dots present.
- G139 — PASS — caption decimal point h7/A41; complete.
- G151 — PASS — en dash h3/A57; continuous and source-matching.
- G160 — PASS — CJK 一 h5/A87; complete single horizontal stroke in 一步.
- G164 — PASS — caption colon h22/A42; both dots complete.
- G167 — PASS — ideographic comma h10/A43; descending stroke complete.
- G175 — PASS — ideographic full stop h13/A74; complete ring.

## ROLE_LEDGER

- T01/CJK_FULL — PASS — medians 35/35, ratio 1.0; four ideographs consistent.
- T01/LATIN_UPPER_DIGIT — PASS — 27/27, 1.0; X complete.
- T01/NATURAL_SCRIPT — PASS — 20/20, 1.0; script t naturally smaller.
- T01/LOW_PROFILE_MATH_SYMBOL — PASS — 12/12, 1.0; equals peer-verified.
- T01/LATIN_GREEK_XHEIGHT — PASS — 20/20, 1.0; x complete.
- T02/CJK_FULL — PASS — 35/35, 1.0.
- T02/LATIN_GREEK_XHEIGHT — PASS — 28/28, 1.0; q/x/y differences are character-specific.
- T02/MATH_BASE — PASS — 38/38, 1.0; delimiters complete.
- T02/LOW_PROFILE_PUNCTUATION — PASS — 11/11, 1.0; comma peer-verified.
- T02/LOW_PROFILE_MATH_SYMBOL — PASS — 8.5/8.5, 1.0; dot and equals source-natural.
- T02/LATIN_UPPER_DIGIT — PASS — 27/27, 1.0.
- T03/CJK_FULL — PASS — 35/35, 1.0.
- T03/MATH_BASE — PASS — 36.5/36.5, 1.0; delimiters complete.
- T03/LATIN_GREEK_XHEIGHT — PASS — 28/28, 1.0; g/x/y complete.
- T03/LOW_PROFILE_PUNCTUATION — PASS — 11/11, 1.0.
- T03/LOW_PROFILE_MATH_SYMBOL — PASS — 23/23, 1.0; greater-than complete.
- T03/LATIN_UPPER_DIGIT — PASS — 27/27, 1.0.
- T04/LATIN_GREEK_XHEIGHT — PASS — 32.5/32.5, 1.0; larger 11.2-pt formula style.
- T04/MATH_BASE — PASS — 43/43, 1.0; braces and parentheses complete.
- T04/LOW_PROFILE_PUNCTUATION — PASS — 12/12, 1.0.
- T04/LOW_PROFILE_MATH_SYMBOL — PASS — 14/14, 1.0; equals complete.
- T04/LATIN_UPPER_DIGIT — PASS — 30/30, 1.0.
- T05/CJK_FULL — PASS — 35/35, 1.0.
- T05/LATIN_UPPER_DIGIT — PASS — 28/28, 1.0.
- T05/LOW_PROFILE_MATH_SYMBOL — PASS — 19.5/19.5, 1.0; ∼ and ≤ individually complete.
- T05/MATH_BASE — PASS — 38/38, 1.0.
- T05/LOW_PROFILE_PUNCTUATION — PASS — 11/11, 1.0; comma/question mark individually verified.
- T05/LATIN_GREEK_XHEIGHT — PASS — 20/20, 1.0.
- T06/CJK_FULL — PASS — 35/35, 1.0.
- T06/LATIN_UPPER_DIGIT — PASS — 27/27, 1.0.
- T06/NATURAL_SCRIPT — PASS — 20/20, 1.0.
- T06/LOW_PROFILE_MATH_SYMBOL — PASS — 15.5/15.5, 1.0; plus/equals peer-verified.
- T06/LATIN_GREEK_XHEIGHT — PASS — 29/24.5, 1.183673; descender-bearing y explains height with identical font/size.
- T07/CJK_FULL — PASS — 35/35, 1.0.
- T07/LATIN_UPPER_DIGIT — PASS — 27/27, 1.0.
- T07/NATURAL_SCRIPT — PASS — 20/20, 1.0.
- T07/LOW_PROFILE_MATH_SYMBOL — PASS — 15.5/15.5, 1.0.
- T07/LATIN_GREEK_XHEIGHT — PASS — 20/24.5, 0.816327; x-height versus y-descender explains ratio with identical font/size.
- T08/CJK_FULL — PASS — 36/35.5, 1.014085; complete after decontamination.
- T09/CJK_FULL — PASS — 35/35.5, 0.985915.
- T10/CJK_FULL — PASS — 36/35.5, 1.014085.
- T11/CJK_FULL — PASS — 35/35.25, 0.992908.
- T12/CJK_FULL — PASS — 35.5/35.25, 1.007092.
- T13/CJK_FULL — PASS — 35/35.5, 0.985915.
- T13/LOW_PROFILE_PUNCTUATION — PASS — 21/21, 1.0; colon complete.
- T13/LATIN_GREEK_XHEIGHT — PASS — 20/20, 1.0.
- T14/CJK_FULL — PASS — 37/37, 1.0; caption CJK intact.
- T14/LATIN_UPPER_DIGIT — PASS — 28/28, 1.0.
- T14/LOW_PROFILE_PUNCTUATION — PASS — 8.5/8.5, 1.0; each punctuation reviewed.
- T14/LATIN_GREEK_XHEIGHT — PASS — 22/22, 1.0; expected character-level height variation.

## CLIPPING_LEDGER

- T01 — PASS — page/crop margins 990/227 px.
- T02 — PASS — 908/410 px.
- T03 — PASS — 848/609 px.
- T04 — PASS — 778/558 px; fraction and braces complete.
- T05 — PASS — 872/652 px.
- T06 — PASS — 491/271 px.
- T07 — PASS — 761/540 px.
- T08 — PASS — 1095/344 px.
- T09 — PASS — 1095/533 px.
- T10 — PASS — 1095/806 px.
- T11 — PASS — 590/370 px.
- T12 — PASS — 940/719 px.
- T13 — PASS — 617/409 px.
- T14 — PASS — 540/332 px; caption complete.
- B01 — PASS — 816/203 px; full border.
- B02 — PASS — 816/386 px; full border.
- B03 — PASS — 402/182 px; full wide border.
- B04 — PASS — 596/376 px; four vertices.
- B05 — PASS — 319/99 px; nearest crop object still has 99 px margin.
- B06 — PASS — 666/445 px; double border complete.
- E01 — PASS — 1057/335 px; shaft/arrowhead complete.
- E02 — PASS — 1057/518 px.
- E03 — PASS — 1057/796 px.
- E04 — PASS — 573/353 px.
- E05 — PASS — 922/701 px.
- E06 — PASS — 615/394 px; full self-loop and arrowhead.

## VIEW_AND_HARD_GATES

- SOURCE_IDENTITY — PASS — actual source SHA matches identity and WRITE_STOPPED.
- PDF_IDENTITY — PASS — actual R101 SHA, size, 814 pages and A4 dimensions match.
- PAGE_IDENTITY — PASS — page 651 extraction starts at printed page 638 and contains figure 32.5 and caption.
- NATIVE_RENDER_IDENTITY — PASS — page PNG SHA matches.
- WRITE_STOPPED_SEAL — PASS — write_stopped true; source writer none; TeX disabled.
- SEMANTIC_TRUTH — PASS — source/context agree on proposal, positive-flow MH ratio, uniform draw, accept, reject and rejection self-loop.
- TEXT_CONSISTENCY — PASS — views, source map and PDF text agree.
- READING_ORDER — PASS — B01→E01→B02→E02→B03→E03→B04, then separated accept/reject branches and B06 self-loop.
- CAPTION_MATCH — PASS — visible/extracted caption matches source.
- PAGE_FIT — PASS — figure, loop, caption and reading-order paragraph fit above footer.
- FONT_DECLARATIONS — PASS — T01–T03/T05–T13 9.6 pt, T04 11.2 pt, T14 10.0 pt; all exceed 9.5 pt; scale 1.0 and no shrinking transform.
- COLOR_VIEW — PASS — restrained color encoding; arrow types and double reject border unambiguous.
- GRAYSCALE — PASS — borders, dash patterns, labels, formula, diamond, double border and loop distinguishable.
- OBJECT_COMPLETENESS — PASS — 26/26 cards and both mask scales inspected.
- GLYPH_COMPLETENESS — PASS — 15/15 sheets and 175/175 rows inspected.
- PAIR_COMPLETENESS — PASS — 325/325 pairs explicitly decided.
- INTERSECTION_CLASSIFICATION — PASS — eight raw intersections are legal endpoints at both scales.
- DENOMINATORS — PASS — 26, 175, 325, 8, 27, 50 and 26 individually completed.

RESULT: PASS
NEEDS_SOURCE_WRITER: no
NEEDS_TEX_SLOT: no
NEXT_ACTION: Persist this review and issue a readable mainline handoff; no source-writer or TeX-slot request is needed.
