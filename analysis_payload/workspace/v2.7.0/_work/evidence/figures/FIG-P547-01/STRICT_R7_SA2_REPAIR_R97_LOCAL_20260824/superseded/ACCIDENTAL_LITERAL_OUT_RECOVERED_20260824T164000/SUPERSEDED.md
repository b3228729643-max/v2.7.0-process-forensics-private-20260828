# Recovered literal-output-directory artifacts — SUPERSEDED

A PowerShell interpolation error passed the literal token `$out` to the local
wrapper compiler.  The exact directory was immediately resolved, verified,
and moved intact from the read-only wrapper directory into this evidence-only
superseded location.  None of these files participates in the active audit or
acceptance join.  The wrapper source itself was not modified.

The active local page and standalone PDFs are rebuilt separately in the
authorized `build/page` and `build/standalone` directories.
