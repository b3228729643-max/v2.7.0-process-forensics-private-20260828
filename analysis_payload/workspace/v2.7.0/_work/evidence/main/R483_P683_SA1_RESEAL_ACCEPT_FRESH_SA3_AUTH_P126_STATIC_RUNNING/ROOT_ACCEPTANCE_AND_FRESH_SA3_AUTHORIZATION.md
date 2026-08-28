# R483 — P683 SA1 reseal acceptance and fresh isolated SA3 authorization

Timestamp: `2026-08-28T08:21:11+08:00`

## Main acceptance

Main independently accepts the P683 V2 evidence-only control reseal and therefore accepts the already-reviewed fresh-SA1 content result as `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`.

Accepted root:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa1_r115_fresh_isolated_v1_control_reseal_v1`

The controller and separate auditor each ran exactly once, retry 0, and returned natural exit 0. Their frozen identities remain:

- controller 22,726 bytes/SHA-256 `B14AD45E31670A8BFB79EEF8BB1C689976C7BA4A4911C43D8BC31815ACF28CD6`;
- auditor 19,145 bytes/SHA-256 `E6577AF3AA949C96C782EA5DF5955BC55196D14CE357E493D1EA18E0E9E6ECA7`.

## Independent mechanical recomputation

Main did not invoke the frozen auditor a second time. An independent inline read-only recomputation established:

- ordinary files 40; directories including root 4; payload files 37;
- PAYLOAD_MANIFEST rows 37, case-sensitive duplicates 0, manifest-versus-payload set difference 0, full bytes/SHA-256/Creation+LastWrite FILETIME mismatch 0;
- COPY_IDENTITY rows 35, duplicates 0, source/destination identity mismatch 0;
- provenance canonical paths 35, `CONTROL_ONLY=true`, `BUSINESS_RERUN=false`;
- writable files 0 and writable directories/root 0;
- WSTOP physical lines 13, unique keys 13, bad lines 0, duplicates 0, BOM false, required field mismatches 0;
- WSTOP FILETIME `134323498521366330`, maximum other file/directory/root FILETIME `134323497921490960`, strict-latest margin `599875370` ticks, at-or-after excluding marker 0;
- PAYLOAD_MANIFEST SHA-256 `68AA4F6D5C4C76281C463B373883923E503777063A1F60A270EB1AEE65E399C1`;
- SEAL_AUDIT SHA-256 `B1F24D2A8B47835DF3C417F23B3B8763D632EC5F76280EA953C70C1474A4E505`;
- WRITE_STOPPED SHA-256 `2049252990E8CD5FB610E083924D695D2A3F5CA4C42B031C96A9EB53B27D83B8`;
- source-root recorded/current rows 41/41 with state mismatch 0;
- postmarker recorded/current rows 44/44 with state mismatch 0;
- JSON parse, CSV parse, ADS, cache/pyc, and reparse failures all 0;
- rejected old root remains 37 files/4 directories, all ReadOnly, with original MANIFEST/WSTOP hashes exact.

The four root-external result files match the returned bytes and SHA-256 values, and controller/auditor result JSON each binds invocation 1 and success true. They are writable external observations, not sealed-root material; Main does not rely on their immutability and has independently persisted the acceptance facts here. No mutation of those external files is authorized or needed.

One first Main audit command accidentally used `H` and `R`, names reserved by PowerShell History aliases. It failed read-only without any filesystem write and was discarded. The corrected independent recomputation with nonconflicting function names produced the accepted values above.

## Preserved business result

The previously accepted fresh-SA1 content remains physical 732/printed 719/Fig35.2, N24/C276, manual objects 24/24 and pairs 276/276, views 17, glyph count 156, and hard/clip/illegal/unresolved all 0. No PDF/render/business/manual/math/semantic work was rerun by the reseal.

## One fresh isolated SA3 authorization

C is authorized to start exactly one different fresh isolated SA3:

- HANDOFF_ID: `C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-V1`;
- requested canonical actual: `/root/sa3_fig_p683_r115_fresh_isolated_v1`;
- model/effort/fork: `gpt-5.6-sol/xhigh/none`;
- fixed new root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1`.

Main's immediate gate is Leaf false, Container false, Any false, Parent true. Before any artifact/root creation, the child must independently repeat the exact LiteralPath gate; then only that same instance may create the root once and run to one sealed PASS/FAIL.

Fresh inputs are exact-only:

- R115 PDF 4,967,161 bytes/SHA-256 `93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F`;
- current P683 source 3,119 bytes/SHA-256 `6C26EB8DE73F26D37078C03D82A27A45E32BECFD6E71C091BD96F9571562DFFF`;
- exact V5-C06 chapter 120,809 bytes/SHA-256 `7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029`;
- current Goal/direct section 9.2.1 protocol and schema only.

The prompt must expose none of the SA1/SA2/reseal/old-P683 page, denominator, pair, pixel, manual, verdict, acceptance, or evidence paths. Directory-level search/enumeration/glob/fallback, agent/thread/task status tools, all old P683 and other UID materials, TeX/build, source/PDF/Git/central/process actions, second UID, and second P683 role are forbidden. The role must independently locate the current figure, freeze its own complete reader-visible denominator and all unordered pairs, open required native/grayscale/page/overlay/critical 1x+NN8x views before manual judgments, and return one honest sealed result without self-counting local/global/final PASS.

P683 remains counted at SA1 until the exact actual identity and child pre-artifact gate return. Inventory therefore remains `32 SA1 / 31 SA2 / 0 SA3 / 37 local pass`; strict-final remains `0/99`. A/P126 continues only its already-authorized STATIC_ONLY single-source patch and has no TeX/build/commit/fresh-role authorization.
