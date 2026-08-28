# FIG-P608-01 SA2 source geometry static review

- Status: `P608_SOURCE_GEOMETRY_PATCH_READY_REQUEST_BUILD_SLOT`
- Scope: one authorized source file; no TeX, build, commit, or second UID
- Source before SHA-256: `78C30F4A934F63E0EF1BBACF400A24F22477D38589F99503AE468F7024A35C05`
- Source after SHA-256: `49A683AEEC94AFD71AE33E95D4DF51BA3CC722F10B432B065FDBD2E45898635E`
- Diffstat: one file, one insertion, one deletion
- `git diff --check`: PASS

## Minimal patch

The shared two-panel x domain changes from `[1,20]` to `[0.5,20.5]`. No other token changes.

```diff
-  width=11.4cm,height=3.55cm,xmin=1,xmax=20,xtick={1,5,10,15,20},
+  width=11.4cm,height=3.55cm,xmin=0.5,xmax=20.5,xtick={1,5,10,15,20},
```

## Closure mechanism

- The first upper-panel sample remains at the exact data coordinate `(1,3.8)`.
- The independent y-axis moves to `x=0.5`; therefore the first marker is no longer x-coincident with the y-axis or its arrowhead base.
- The final sample remains at `x=20`; the symmetric upper bound `20.5` gives the rightmost sample the same half-step margin.
- At the declared 11.4 cm width, the nominal half-step offset is about 33.66 px at 300 dpi before pgfplots outer-label allocation. The rendered candidate must measure the actual native clearance.

## Preserved invariants

- Upper trace: 20/20 coordinates unchanged, including `(1,3.8)` and `(20,1.9)`.
- Lower running means: 15/15 coordinates unchanged; `(20,2.0000)` remains present.
- All data values, the 15 running means, final mean 2.0000, labels, caption, panel structure, y domains, ticks `{1,5,10,15,20}`, warm-up boundary `x=5.5`, target line, fonts, marks, strokes, and annotations are unchanged.
- Both panels inherit the same new domain, preserving vertical alignment.
- No `scale`, `resizebox`, `scalebox`, coordinate move, label move, or semantic substitution is introduced.

## Static risk ledger

1. Horizontal interval spacing becomes `19/20 = 0.95` of the prior spacing. This is a controlled 5% compression and needs native render confirmation for curve/marker separation.
2. The rightmost sample gains a symmetric half-step margin; confirm no new relationship with the target label or page boundary.
3. The warm-up hatch and dashed boundary remain anchored at data coordinates 1 and 5.5; confirm their visible hierarchy after domain expansion.
4. The exact marker-to-axis and marker-to-arrowhead clearance cannot be certified without the authorized direct LuaLaTeX render and native 300 dpi evidence.

No source conclusion beyond this static projection is claimed.
