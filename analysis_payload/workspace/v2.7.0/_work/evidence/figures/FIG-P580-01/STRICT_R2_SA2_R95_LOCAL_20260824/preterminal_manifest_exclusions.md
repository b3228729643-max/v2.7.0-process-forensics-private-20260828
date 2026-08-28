# Pre-terminal input manifest exclusions

`machine_terminal_input_file_manifest.csv` follows the P582 non-self-referential input-manifest pattern. It inventories every file present under this SA2 evidence root immediately before the dynamic terminal products are emitted, including retained files classified `NONAUTHORITATIVE_STALE` and LaTeX build auxiliaries classified `NONAUTHORITATIVE_BUILD_AUX`. External business/source authority inputs are appended with absolute paths and hashes.

Exactly these five dynamic products are excluded:

1. `machine_terminal_input_file_manifest.csv` — the manifest itself.
2. `final_file_integrity.csv` — generated during the same terminal run from the frozen pre-terminal input set.
3. `machine_final_check.json` — dynamic terminal JSON.
4. `machine_final_check.md` — dynamic terminal Markdown.
5. `WRITE_STOPPED.md` — future stop marker, written only after the terminal JSON/Markdown report PASS.

No current evidence file is excluded because of its content or conclusion. The failed 09:28 `authoritative_final_manifest.csv` was a superseded dynamic terminal product and was removed before this final pre-terminal scan; it is not a candidate input. Retained stale packages and the six pre-final fraction/vertical-bar composite masks remain physically present, are inventoried, and carry an explicit nonauthoritative category.
