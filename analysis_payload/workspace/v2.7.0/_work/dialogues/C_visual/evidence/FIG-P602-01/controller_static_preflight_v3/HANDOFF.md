# P602 controller v3 static-only handoff

Status: `P602_CONTROLLER_STATIC_PREFLIGHT_READY_FOR_MAIN_REVIEW`.

- No controller draft was executed.
- No candidate root was created.
- No LuaLaTeX, texlua, latexmk, luatex, or luahbtex process was started.
- No business source, wrapper, central state, inventory, or prior evidence package was modified.
- The future candidate root, exact ProcessStartInfo, environment topology, containment assertions, identity gates, invocation-count gate, and fail-stop path are frozen in this package.
- The only necessary functional difference from v2 is the addition of a task-specific `TEXMFOUTPUT` parent with all three cache paths strictly contained beneath it; cwd and relative-input semantics remain unchanged, and `openout_any` is not relaxed.
- This package grants no third build invocation. Main review and a separate explicit grant remain required.

