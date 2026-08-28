# R311 — P049 static patch acceptance and direct-build authorization

- Accepted static handoff: `A-R110-P049-SA2-GUIDE1-STATIC-R3-20260827`.
- Authorized build handoff: `A-R110-P049-SA2-DIRECT-BUILD-R4-20260827`.
- Authorized new root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R4_SA2_R3_GUIDE1_DIRECT_BUILD_R110_20260827`; startup existence gate is false.
- Unique source: `src/绘图源码/第01册_数学基础与统计学习基本理论/V1-C03/fig_v1_c03_gradient_contour.tex`.
- Source before SHA-256: `F9D4040ABB708F8043C619FB8C59B9CCCFDB2938E1BBD54B03B1E5D940F2999C`.
- Source after SHA-256: `27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E`.
- Main verified an exact one-file 1+/1- diff and `git diff --check` PASS. The only changed line is Guide1:
  - before: `(s1.west)--(axis cs:3.72,2.66)--(axis cs:2.75,1.36)`
  - after: `(s1.west)--(axis cs:1.20,2.45)--(axis cs:.84,1.728)`
- The endpoint lies exactly on c3: with x=21/25 and y=216/125, `x^2/9=49/625`, `y^2/3.24=576/625`, sum 1.
- Static analysis reports no interior intersections with Guide2/3, gradient, tangent, right-angle/P cluster, axes, unrelated contours, labels, note2/note3, caption, or page. Minimum projected centerline clearances are 60.36px to tangent, 74.49px to Guide2, and 80.90px to gradient; minimum projected text clearance is 19.83px to the gradient label.
- All other source tokens are unchanged. Static evidence is not a PASS and a new PDF is required.
- Global process check immediately before authorization found no `latexmk`, `lualatex`, `luatex`, or `luahbtex` process.

Build authorization:

- Exactly one PowerShell7 controller invocation may start exactly one direct LuaLaTeX child against a standalone wrapper bound to the patched P049 source.
- `latexmk`, retry, automatic second start, parallel TeX, and interruption are forbidden.
- `TEXMFVAR`, `TEXMFCACHE`, and `TEXMFCONFIG` must all bind to a new cache under the authorized R4 root.
- The source and wrapper identities must be recorded before and after and remain unchanged; exactly one output PDF is allowed.
- On natural exit, report the controller/child identities, timing, exit, invocation/retry counts, PDF path/bytes/SHA, source/wrapper identities, terminal TeX process count, and release the slot before any non-TeX review.
- After release, rebuild all native object/pair/manual evidence from the new PDF, explicitly retesting Guide1 endpoint semantics, Guide1/Guide2 crossing, Guide1 clearances, gradient/tangent/right-angle geometry, contours, labels, grayscale, caption, and page integration.
- No commit, fresh role, second source, second UID, or central write is authorized.

P641 fresh SA1 continues read-only in parallel. Inventory remains `32 SA1 / 43 SA2 / 0 SA3 / 24 local pass`.
