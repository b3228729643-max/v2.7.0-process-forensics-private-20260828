# FIG-P033-01 R111 fresh isolated SA1 report

- HANDOFF_ID: `A-R111-P033-SA1-FRESH-ISOLATED-20260827`
- canonical task: `/root/p033_r111_fresh_sa1`
- model_effort: `gpt-5.6-sol/xhigh`
- fork_turns: `none`
- role: fresh isolated SA1, read-only business scope
- result: `PASS`
- route: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`

## Scope and identity

Only the official R111 PDF, the current single P033 source, GOAL/direct strict evidence requirements, and the necessary current V1-C02 context were used. No R1-R4 or old P033 evidence/report/state/inventory/handoff/chat/Git history/main acceptance/other-UID conclusion was read. No source, main, PDF, Git, or central state file was modified; no TeX build and no further agent were started.

- Official PDF: 817 pages; 4,967,076 bytes; SHA-256 `DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6`.
- P033 source SHA-256: `D3C1D38ECB8468EC3294F7D18BD886316829F14690A516000189CE853A07BC05`.
- Independent location: physical page 29, printed page 16, Figure 2.1.
- Evidence root pre-write proof: directory=false and file=false at `2026-08-27T07:55:49.884+08:00`.

## Denominator and evidence

- The provisional semantic N=14/C=91 was transparently discarded before manual review.
- Frozen atomic visible denominator: N=99 = 85 glyph + 5 line + 2 rect + 7 curve objects.
- Exhaustive unordered pairs: C(99,2)=4,851.
- Three nonempty support-background paths remain included in N; only their fill is excluded from illegal semantic-foreground counts. The visible equation-box border was manually reviewed.
- Machine-disposed pairs: 4,770.
- Manually opened and individually decided pairs: 81/81, with exact pair-ID set equality and no default/template-generated manual fields.
- Native evidence: official full page at 300 dpi, frozen body+caption native1x crop, atomic and semantic overlays, seven native1x ROIs, seven nearest-neighbor 8x ROIs, both review sheets, and grayscale crop.

Core evidence hashes:

- `machine/atomic_visible_denominator.csv`: `958FAA823187F184598E8FC62B0D621EF30C70C5C5856B4FAF80D30AC63F2419`
- `machine/all_unordered_pairs.csv`: `A15A2122D129EABBF0F922A5ECAC4CAA096D2535782C2A6CBBBC33DE9B094369`
- `manual/manual_pair_resolution.md`: `2785FB306E52999AD1DDA17A50B3BECB594A7CD4AB55244C4EC182739404A249`
- `manual/final_hard_gate.json`: `DAC696D17078B9FAA4642A361D81B5F21D2BEB78CB50D5DAE4F4AD8CC1B17449`
- `render/p033_body_caption_300dpi_native1x.png`: `EE5DFFDAC93BCD89C93060C529E35B6D15737B9204169CB1380538C2DB42A6B2`
- `roi/p033_manual_review_nearest8x_sheet.png`: `5D81D634C31A0BCA52FD06618964E5A08D1AC66507ECE18A4D2BE8C243F4523E`

## Hard decision under R168

- Missing/tofu/wrong codepoint: 0; all eight text groups match exactly and all 85 glyph rasters are nonempty.
- Wrong math meaning: none.
- Actually unreadable or obviously unbalanced: none.
- Real clipping: 0.
- Real illegal overlap pixels: 0; intended O/P/X endpoint contacts and projection/distance constructions remain semantically clear.
- Geometry/semantics: PASS. With O=(0,0), P=(3.2,0.8), X=(2.7,2.8), r=X-P=(-0.5,2.0), `p dot r=0`, and `||x||^2-(||p||^2+||r||^2)=0`.
- Caption/text consistency, grayscale, and page integration: PASS.
- Advisory only: 9.2 pt / 9.4 pt source-local declarations are below the older 9.5 pt target, but the actually opened native 300 dpi and nearest8x views are readable and balanced.

## Conclusion

Fresh isolated SA1 returns `PASS` and routes only to `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`. It does not claim `A_LOCAL_PASS`, final acceptance, or SA3 completion, and it does not start SA3.

The evidence root is closed by its single final sentinel `seal/WRITE_STOPPED.md`; that sentinel is the final evidence-root write and every file/directory is read-only afterward.
