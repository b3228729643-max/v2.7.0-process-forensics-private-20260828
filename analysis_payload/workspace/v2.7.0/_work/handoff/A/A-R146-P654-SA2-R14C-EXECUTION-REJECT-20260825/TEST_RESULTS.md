# P654 R14C execution test results

- Materialization: PASS, exactly three future scripts before prepare.
- Reviewed identity binding: PASS, bytes/SHA differences 0/3.
- PowerShell host: PASS, `D:\PowerShell7\pwsh.exe -NoProfile`.
- Execution grant: PASS, new R14C token only.
- Prepare invocation: 1, exit 0.
- Prepare output: base payload 1052, current payload 1058, script identity gate 3/3 PASS.
- Validator invocation: 1, exit 1.
- First fatal: `identity duplicate source_relative_path` at validator line 22.
- Seal invocation: 0.
- Retry: 0.
- Raw JSON identity: 1052 rows, source-path duplicate groups 0.
- Raw CSV identity: 1052 rows, source-path duplicate groups 0.
- Normalized row type: `System.Collections.Specialized.OrderedDictionary`.
- Current grouping reproduction: one empty-name group with count 1052; nonunique groups 1.
- Failed-root ordinary: 1058.
- Preseal report: absent.
- Manifests/WSTOP: absent/absent.
- Controls: 0.
- Source SHA unchanged: `EA4A19FF940A177D4D754C4277896A2F38B75C1E6F252D8A374F418B84E31E6D`.
- TeX/source edit/commit/fresh role: 0/0/0/0.
- Verdict: `EXECUTION_REJECT_R14C_VALIDATOR_EXIT1_CHAIN_STOPPED`.

