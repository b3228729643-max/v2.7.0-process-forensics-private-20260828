# MODEL_ROUTING_LOG

| role | model / effort | mode | result |
|---|---|---|---|
| Coordinator | root Codex agent | single active source writer; final one-token R3 correction and atomic commit | commit `933fe1d` |
| SA1 | gpt-5.6-sol / xhigh | independent read-only math/content and full visual review | R1/R2 findings routed; R3 final PASS, findings NONE |
| SA2 | gpt-5.6-terra / high | targeted sequential writer for the sole 22.1 overflow | inserted first local break; no TeX/commit; coordinator applied final `\newline` token under main authorization |
| Mechanical | gpt-5.6-luna / medium | read-only static checks plus authorized serial R1/R2/R3 build/render | 9 tests/PDF/log/18-page final visual metrics PASS |
| SA3 | gpt-5.6-sol / xhigh | blind read-only; did not read SA1/mechanical/state/handoff conclusions | FINAL_DECISION=PASS, findings NONE |

源码写者始终串行而非并发。R1/R2 的排版发现均在进入下一轮前冻结、路由并获得主线授权；R3 后没有 R4。PDF 技能用于逐张检查十题的全部目标/续页。
