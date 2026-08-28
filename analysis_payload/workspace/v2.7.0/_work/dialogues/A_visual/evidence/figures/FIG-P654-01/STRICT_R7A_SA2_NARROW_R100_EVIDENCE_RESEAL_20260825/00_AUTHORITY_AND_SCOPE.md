# P654 R7A authority and scope

- `TASK`: P654 R7A evidence-only reseal after `P654_R7_ROOT_MECHANICAL_AUDIT.md` returned `ROOT_REJECTED` for G1--G5.
- `MODEL_ROUTE`: `SA2=gpt-5.6-sol/max`.
- `WRITE_ROOT`: this R7A directory only.
- `SEALED_R7`: permanently read-only; no script import/execution, no file/cache creation.
- `SOURCE`: read-only; expected SHA256 `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`.
- `WRAPPER`: read-only; expected SHA256 `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`.
- `PDF`: expected 43,385 bytes and SHA256 `A7DBDECEA7B54C1649CD341112B7BB37FF379600CB6A61B54EDDBAF154E9E5D6`.
- `BUILD_POLICY`: all TeX/LuaLaTeX/latexmk prohibited; no source edits, commits, fresh SA1 or SA3.
- `ALLOWED_REUSE`: R7 build/PDF/native300dpi/masks/object/pair/inventory machine facts only, after source/destination identity binding.
- `BANNED_REUSE`: every R7 manual ledger/decision/note, finalizer-authored manual conclusion, terminal/result/report acceptance conclusion.
- `FINAL_TOKEN`: `LOCAL_SA2_PATCH_VERIFIED_AWAIT_R7A_ROOT` or a truthful failure.

