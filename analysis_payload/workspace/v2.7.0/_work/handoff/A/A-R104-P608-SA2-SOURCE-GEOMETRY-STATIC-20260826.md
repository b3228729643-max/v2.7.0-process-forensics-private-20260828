# A-R104-P608-SA2-SOURCE-GEOMETRY-STATIC-20260826

- UID: `FIG-P608-01`
- Role: SA2 static-only geometry source writer
- Status: `P608_SOURCE_GEOMETRY_PATCH_READY_REQUEST_BUILD_SLOT`
- Authorized source: `src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex`
- Before SHA-256: `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`
- After SHA-256: `49A683AEEC94AFD71AE33E95D4DF51BA3CC722F10B432B065FDBD2E45898635E`
- Exact diff: shared domain `xmin=1,xmax=20` to `xmin=0.5,xmax=20.5`; one file, 1+/1-
- Closure mechanism: the first sample remains at x=1 while the independent y-axis moves to x=0.5, giving native horizontal separation from the axis and arrowhead; the symmetric x=20.5 bound preserves balanced margins.
- Preserved: all 20 trace values, all 15 running means, t20=2.0000, tick values, labels, caption, two-panel structure, x=5.5 warm-up boundary, target line, fonts, marks, and strokes.
- Static risk: 5% horizontal compression plus exact native clearance must be checked in the authorized direct build and native 300 dpi evidence.
- Validation: `git diff --check` PASS; only the authorized source is modified.
- TeX/build/commit/second UID: 0/0/0/0.
- Next action: main may grant one controlled P608 build slot; until then no TeX or commit.
