# Source-only validation

- `git diff --check -- <target>`: PASS, exit 0, no output.
- Worktree tracked diff scope: exactly one file, the authorized P654 target source.
- `git diff --numstat -- <target>`: `1 insertion / 1 deletion`.
- Delimiter/static balance: braces `52/52`; dollar signs `6`; figure begin/end `1/1`; tikzpicture begin/end `1/1`.
- Provenance uniqueness: one trial node and one exact local `10.7pt` wrapper around `\boldsymbol n`.
- Forbidden resizing/down-style constructs in the target (`resizebox`, `scalebox`, `transform shape`, manual `scriptstyle`/`scriptscriptstyle`): none.
- After-patch SHA-256: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`.
- TeX/LuaLaTeX/latexmk/build execution: not run.
- Git commit: not created.

Result: `SOURCE_STATIC_PASS_BUILD_NOT_RUN`.

This result does not establish `H_INK>=22px` and must not be treated as SA2 PASS.
