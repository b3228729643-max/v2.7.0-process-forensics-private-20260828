# P640 static source handoff

`P640_SOURCE_GEOMETRY_PATCH_READY_REQUEST_BUILD_SLOT`

- source after SHA256: `FFAE906011BBAD21FD1AD53997693934828394C2AE516649CCCF8DA5938D9B89`
- exact change: right-panel `ymin=0` to `ymin=-.04`
- scope: one authorized file, `1+/1-`
- `git diff --check`: `PASS`
- retained point and label: `(.99,0.0100499975)` / `(.99,.010)`
- TeX/latexmk runs: `0`
- commit: `NONE`
- build status: `NOT AUTHORIZED / NOT RUN`
- detailed evidence: `STATIC_PATCH_REPORT.md`

The source is statically frozen pending a mainline-controlled build slot.
