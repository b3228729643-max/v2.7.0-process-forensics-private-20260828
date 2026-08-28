# R5 SA1 mathematical and semantic review

Canonical evidence directory: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P602-01\STRICT_R5_REQUAL_R96_SA1_CONT_20260824`.

The inspection used the frozen physical PDF page 651 (printed page 638), including its surrounding equations (32.7)--(32.9), rather than relying on a prior figure audit.

- The current state is `X_t=x`, followed by a candidate `Y=y` proposed from `q(x,\cdot)`.
- Under the displayed positive-flow condition `g(x,y)>0`, the acceptance rule is exactly `\alpha(x,y)=\min\{1,\widetilde\pi(y)q(y,x)/(\widetilde\pi(x)q(x,y))\}`.  It agrees with equation (32.7) immediately above the figure.
- The page separately specifies `\alpha(x,y)=0` when `g(x,y)=0`; the figure explicitly scopes its ratio box to the positive-flow branch and does not contradict that zero-flow branch.
- Drawing `U\sim\mathrm U(0,1)` and accepting when `U\le\alpha(x,y)` is the standard MH realization.
- The accept branch correctly writes `X_{t+1}=y`.  The reject branch correctly retains and records `X_{t+1}=x`; the dashed self-loop correctly represents the rejection mass `r(x)\delta_x`, consistent with equation (32.9) and the prose immediately above the figure.

**Math/semantic result: PASS.**  No formula, variable-flow, branch, or caption contradiction was found.
