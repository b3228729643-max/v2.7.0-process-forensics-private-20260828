# Dialogue A handoff — FIG-P654-01 local SA2 evidence accepted

- HANDOFF_ID: `A-R151-P654-SA2-LOCAL-PASS-AWAIT-OFFICIAL-CANDIDATE-20260825`
- STATUS: `LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`
- FIGURE_ID: `FIG-P654-01`
- BRANCH: `v2.7.0/dialogue-a-visual`
- COMMIT: `697dce292f2c1afca7d02554c3bad987ca84f825`
- PARENT: `738e079d8e85621b23f30e71017eafde37681711`
- SOURCE_SHA256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`
- CENTRAL_ROLE_REQUEST: integrate the one-file commit, freeze a new official candidate, then dispatch a completely fresh isolated SA1
- TEX_REQUIRED_BY_A_NOW: no
- CENTRAL_INVENTORY_CHANGE_BY_A: none

## Authorized atomic source change

The commit contains exactly one source file and one line replacement:

`src/绘图源码/第05册_采样方法主题模型与图排序/V5-C05/fig_v5_c05_dependency_graph.tex`

```diff
-\node[aux,text width=28mm] (trial) at (-5.499,1.15) {类别计数\\$\boldsymbol n$};
+\node[aux,text width=28mm] (trial) at (-5.499,1.15) {类别计数\\{\fontsize{10.7pt}{12.2pt}\selectfont$\boldsymbol n$}};
```

Commit diffstat is exactly `1 insertion(+), 1 deletion(-)` in that one file. `git diff --check` passed before commit, and the worktree and index are clean after commit.

## Accepted local evidence

Mainline independently adjudicated the fresh-root dispatch scope and issued `MAIN_SCOPE_ADJUDICATION_ACCEPT_R14F_LOCAL_SA2_EVIDENCE`. The immutable `ROOT_REJECT_R14F` report remains historical and unchanged; its sole rejection condition — a sixth field in the final single-root payload manifest — is outside the authoritative Goal/schema/grant. The final manifests correctly preserve relative path, bytes, SHA-256, NTFS ticks, and 7-digit UTC display.

The sealed R14F evidence root remains permanently read-only:

`D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14F_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825`

Its accepted identity/content gates include 1059 payload + 3 controls = 1062 ordinary files, JSON 71+2=73, CSV 23+1=24, R10 base identity 1052/1052, parse/ADS/cache/write-stop closure, N116/C6670, taxonomy95→10, manual192, and zero content counterexamples.

## Boundary

This handoff does not claim `A_LOCAL_PASS`. A must not run TeX, create an official candidate, start fresh SA1/SA3, alter the sealed R14F root/report, or modify central inventory. Those steps remain mainline-controlled.

