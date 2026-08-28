# R255 — R108 official candidate freeze after controlled Resume

- Status: `OFFICIAL_CANDIDATE_FROZEN / R108_BUILD_LOCK_RELEASED`.
- Main branch: `v2.7.0/integration`.
- Main commit: `e33a3b7490ba39304181c25f775221e63a35b6a4`.
- Main worktree: clean.
- Integrated P656 source commit: main `e33a3b7` from C atomic commit `211bd3959e93379766184e8a07354c81df8536d4`.
- P656 source SHA-256: `9D404ED0694D575DE89038D3D6485C49AA4C60DCC3238AD8318CADACF810B381`.

## Controlled official build identity

- The first R108 parent chain was platform-interrupted near page 480 and permanently classified `PLATFORM_INTERRUPTED_NO_CANDIDATE`.
- Recovery used the same output root with exactly one controlled `build_v2.7.0.ps1 -Engine lualatex -OutputDir src\build\strict_current_r108_fullbook -Resume -NoPublish` parent chain. No clean, deletion, second recovery parent, or automatic retry was used.
- The Resume chain naturally exited 0; `latexmk` reported all targets up to date and the wrapper returned `PASS`.
- Terminal process gate: `latexmk/lualatex/luatex/luahbtex = NONE`.
- PDF: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r108_fullbook\main_full.pdf`.
- PDF identity: 817 pages; 4,967,161 bytes; SHA-256 `C2EC93425486A57DE4C6670E16FC7DA729649A183230C28E8A0652467D3B5B78`.
- Format: 817/817 pages A4 `595.276 x 841.890 pt`; rotation 0; PDF 1.7; unencrypted.
- Final log: 260,299 bytes.

## Final mechanical gates

- Hard TeX/package errors, undefined control sequences, emergency/fatal exits: 0.
- Missing files/I/O, memory exhaustion, undefined references/citations, missing characters: 0.
- Duplicate destinations/labels, final rerun requests, overfull and underfull hbox/vbox: 0.
- Main index: 731 accepted, 0 rejected, 0 warnings.
- Symbol index: 355 accepted, 0 rejected, 0 warnings.

## Target-page verification

- FIG-P580-01: caption text independently locates physical page 630 (printed 617, Fig. 31.6). The 300 dpi full page and figure crop were opened. Both support panels, `p`, `q_L`, `q_R`, the `24/25, 3/2, 24/25` card, caption, and surrounding page are complete and readable; no crop, broken glyph, wrong code point, illegal overlap, or page-integration regression was observed.
- FIG-P656-01: caption text independently locates physical page 705 (printed 692, Fig. 34.2). The 300 dpi full page and figure crop were opened. Three ordered sequences, count vector `(3,1,2)`, multinomial coefficient, support constraints, warning card, arrows, caption, and surrounding page are complete and readable. The new 9.5 pt source floor is visibly effective; no crop, broken glyph, wrong code point, illegal overlap, or visible imbalance was observed.
- Rendered evidence in this directory: `p580_page630_300dpi.png`, `p580_figure_crop_300dpi.png`, `p656_page705_300dpi.png`, and `p656_figure_crop_300dpi.png`.

## Routing boundary

R108 replaces R107 as the sole official candidate. P580 and P656 remain centrally `SA2` until their completely fresh isolated R108 SA1 instances return actual identities. Each fresh SA1 must use `gpt-5.6-sol/xhigh/fork_turns=none`, a nonexistent new root, only the R108 PDF/current single source/active Goal/strict protocol/schema/necessary current body, and must not read any old evidence, role, root, handoff, state, inventory, chat conclusion, or Git history for its UID. TeX, source writes, commits, second UID, and second role are forbidden. A PASS only routes to a different fresh isolated SA3.

- Inventory remains `31 SA1 / 51 SA2 / 0 SA3 / 17 A_LOCAL_PASS` pending actual role identities.
- Strict final completion remains `0/99`.
- Frozen at: `2026-08-26T18:55:57+08:00`.
