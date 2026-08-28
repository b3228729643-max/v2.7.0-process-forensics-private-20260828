# P126 R13 static report

The sole current x2 legend declaration was replaced by one adjacent figure-local pgfplots style that directly installs a custom legend-image handler. The handler issues four separate SLTeal horizontal `\draw` commands over the 0--0.60cm legend sample. Its three nominal gaps are 0.12cm each; a conservative round-cap allowance at line width 1.05pt leaves 0.0830967cm, or 9.8146px at 300dpi, for every gap.

Installed pgfplots source confirms that `\addlegendimage` stores its argument as the plot specification, the stored plot style is applied before `/pgfplots/legend image code` is invoked, and this scope is intentionally designed to allow plot styles to change that handler. The new mechanism therefore bypasses the default continuous line-legend path rather than styling it.

The incremental source change is exactly 7 insertions and 2 deletions within the current x2 legend image region. An ordinal in-memory reverse replacement restores the authorized 4,373-byte source and SHA-256 `81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD` exactly. The static after-source is 4,626 bytes with SHA-256 `6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502`. Git name-only remains the sole P126 source, the index is empty, and `git diff --check` passes.

No TeX or build was run. Verdict: `STATIC_ONLY_NOT_RENDERED_NOT_PASS`.
