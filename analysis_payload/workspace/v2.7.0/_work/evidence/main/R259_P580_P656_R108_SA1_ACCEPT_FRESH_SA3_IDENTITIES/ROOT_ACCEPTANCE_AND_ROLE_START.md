# Revision 259 — P580/P656 R108 SA1 acceptance and fresh SA3 identities

Recorded at: 2026-08-26T19:59:40+08:00

## P580 SA1 acceptance

- R2 content PASS direction is preserved; R2 itself remains rejected and immutable because its WSTOP tied the SHA manifest timestamp.
- R2A evidence-only reseal passed independent main audit: source/destination copy identity 45/45 with path, bytes, SHA-256 and NTFS ticks mismatch 0; new payload 47; dual manifests 47/47; payload/manifest/filesystem set and identity mismatch 0.
- Final root has 50 ordinary files, 50/50 read-only, non-default ADS/cache/pyc/reparse 0. WSTOP is strictly latest by 20,426,637 ticks and no file is at or after it.
- Accepted status: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.

## P656 replacement-v2 SA1 acceptance

- Business evidence: N=48 semantic objects, C=1,128 unordered pairs, manual objects 48, critical relations 12, R168 hard failures 0.
- Root audit: ordinary/accounted 89/89, content entries 87, manifest/filesystem set, bytes and SHA-256 mismatch 0; 89/89 read-only; ADS/cache/pyc/reparse 0; WSTOP strictly last with postmarker writes 0.
- Main opened the 300-dpi figure/caption, grayscale, object overlay, arrow 8x ROI and warning-clearance 8x ROI. No true clipping, illegal overlap, semantic error, unreadability or obvious font imbalance was observed.
- Original V1 usage-limit root remains `UNSEALED_INTERRUPTED`, forbidden for reuse.
- Accepted status: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.

## Fresh isolated SA3 actual identities

- P580: `A-R108-P580-SA3-FRESH-ISOLATED-20260826`; instance `/root/p580_r108_fresh_sa3`; `gpt-5.6-sol/xhigh`; `fork_turns=none`; new root `A_visual/evidence/figures/FIG-P580-01/STRICT_R3_SA3_FRESH_ISOLATED_R108_20260826` absent before launch.
- P656: `C-FIG-P656-01-R108-SA3-FRESH-ISOLATED-V1`; instance `/root/sa3_fig_p656_r108_fresh_isolated_v1`; `gpt-5.6-sol/xhigh`; `fork_turns=none`; new root `C_visual/evidence/FIG-P656-01/sa3_r108_fresh_isolated_v1` absent before launch.
- Both roles are read-only, from-zero, and explicitly forbidden from reading their SA1/older UID evidence or conclusions. TeX, source writes, commits, duplicate roles and central-state writes are prohibited.

Central transition: P580 and P656 `SA1 -> SA3`.

Inventory: `31 SA1 / 49 SA2 / 2 SA3 / 17 A_LOCAL_PASS`. Strict final remains `0/99`.
