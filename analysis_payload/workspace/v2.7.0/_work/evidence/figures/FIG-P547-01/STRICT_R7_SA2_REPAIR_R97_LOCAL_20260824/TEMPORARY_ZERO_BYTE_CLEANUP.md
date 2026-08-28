# Zero-byte temporary-file cleanup

Before sealing, SA2 enumerated exactly 12 zero-byte LaTeX index intermediates. Four belonged to the active directed local wrapper builds and eight belonged to the isolated accidental-output superseded directory. They contained no evidence bytes and were not cited by any acceptance table. All 12 were explicitly removed before manifest generation so the package contains no ambiguous zero-byte artifact.

Removed active wrapper intermediates:

- `build/page/symbols.idx`
- `build/page/v260_FIG-P547-01_page.idx`
- `build/standalone/symbols.idx`
- `build/standalone/v260_FIG-P547-01_standalone.idx`

Removed isolated superseded intermediates:

- `superseded/ACCIDENTAL_LITERAL_OUT_RECOVERED_20260824T164000/current_page.idx`
- `superseded/ACCIDENTAL_LITERAL_OUT_RECOVERED_20260824T164000/current_page.ind`
- `superseded/ACCIDENTAL_LITERAL_OUT_RECOVERED_20260824T164000/current_standalone.idx`
- `superseded/ACCIDENTAL_LITERAL_OUT_RECOVERED_20260824T164000/current_standalone.ind`
- `superseded/ACCIDENTAL_LITERAL_OUT_RECOVERED_20260824T164000/symbols.idx`
- `superseded/ACCIDENTAL_LITERAL_OUT_RECOVERED_20260824T164000/symbols.ind`
- `superseded/ACCIDENTAL_LITERAL_OUT_RECOVERED_20260824T164000/v260_FIG-P547-01_page.idx`
- `superseded/ACCIDENTAL_LITERAL_OUT_RECOVERED_20260824T164000/v260_FIG-P547-01_standalone.idx`
