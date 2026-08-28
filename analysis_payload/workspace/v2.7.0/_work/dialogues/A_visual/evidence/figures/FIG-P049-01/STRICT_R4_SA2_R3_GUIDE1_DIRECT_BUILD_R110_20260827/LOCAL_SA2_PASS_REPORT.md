# FIG-P049-01 R4 local SA2 result

Verdict: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`.

The one authorized direct LuaLaTeX invocation ended naturally with exit 0 and produced one 43,378-byte PDF, SHA-256 `DF2418922BA64F670443F509194588764D760E193B306D445E5EEFC78A5752D9`. Source and wrapper identities were unchanged across the build. No TeX process remained after release.

Fresh non-TeX reconstruction froze 27 visible semantic objects, all 351 unordered pairs and 45 focused relations. Guide1 ends exactly on `c3`, has no internal `c3` crossing, and is disjoint from Guide2, Guide3, the gradient, tangent, right-angle marker, P, axes, c1/c2, labels and note text. The former Guide1/Guide2 crossing is absent with 72.591 px clearance. The single raw four-pixel `c3`/`c2-label` mask alert was preserved and independently rejected after native 1x and nearest 8x inspection showed a continuous white gap.

Actual visual review covered the full colour and grayscale figure, Guide1 route and endpoint at native 1x/8x, the former crossing, the gradient/tangent/right-angle cluster, the mask-alert ROI and the 27-object contact sheet. Manual ledgers close 27 objects and 45 focused relations with object- and relation-specific notes. R168 hard failures are zero.

The standalone wrapper suppresses caption rendering. Caption and page preservation are therefore recorded through unchanged source/wrapper identity and unchanged figure bounds against the frozen R110 integration reference; this report does not declare a new official full-book candidate.

No commit was created. The worktree remains a single-source 1+/1- change pending main authorization.
