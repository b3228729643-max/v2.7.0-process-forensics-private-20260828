# FIG-P049-01 R110 R3 source-static audit

- HANDOFF_ID: `A-R110-P049-SA2-GUIDE1-STATIC-R3-20260827`
- verdict: `P049_SOURCE_STATIC_READY_REQUEST_BUILD_SLOT`
- status: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`
- evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R3_SA2_GUIDE1_STATIC_R110_20260827`

The worktree diff is exactly one source and one changed line, 1 insertion/1 deletion, with an empty index and `git diff --check` PASS. Source SHA-256 changes from `F9D4040ABB708F8043C619FB8C59B9CCCFDB2938E1BBD54B03B1E5D940F2999C` to `27BF53A0673A2D57308A836827CC8F0463BE725A11D6826E6BB94CAA91A9BB7E`.

Guide 1 changes from `(s1.west)--(3.72,2.66)--(2.75,1.36)` to `(s1.west)--(1.20,2.45)--(.84,1.728)`. Bend count remains one. The endpoint is exactly on `c3`: `(.84)^2/9=49/625`, `(1.728)^2/3.24=576/625`, sum `1`. Segment 1 remains strictly outside `c3`; segment 2 has its sole in-range `c3` root at the final endpoint.

Analytical segment tests give zero intersections with Guide 2/3, gradient, tangent, right-angle/P cluster, axes, unrelated contours, labels, note 2/3, caption, and page boundary. Limiting projected clearance is 19.83px to the gradient label; limiting nontext centerline clearance is 60.36px to the tangent. The note-1 start is the intentional `s1.west` connection. No forbidden source token changed.

Static root audit: manifest payload rows 3; duplicate/missing/bytes/SHA/ticks mismatches 0; ordinary 5; files read-only 5/5; root read-only 1/1; WSTOP strictly latest by 210,389,774 ticks; at-or-after excluding marker 0; TeX processes 0.

This audit does not claim rendered PASS. One explicitly granted direct/standalone LuaLaTeX build and a fresh new-PDF geometry/all-pairs/manual evidence round remain required.
