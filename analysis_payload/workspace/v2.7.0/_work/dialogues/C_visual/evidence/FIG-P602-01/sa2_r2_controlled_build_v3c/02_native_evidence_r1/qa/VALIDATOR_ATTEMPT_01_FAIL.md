# Native-root validator attempt 01 — control-script FAIL

- The evidence content and manual judgments were not changed by this attempt.
- `qa/validation_report.json` records the natural first exit with one failed check: `peers_denominator_and_id_closure`.
- Root cause: the validator incorrectly required 28 unique `element_id` values. The peer denominator is keyed by `(element_id, role, peer_class)`; 28 rows legitimately contain 17 unique element IDs because some formula objects participate in multiple peer classes.
- Correction scope: change only that validation assertion to compare all 28 compound keys and write the next result to `qa/validation_report_r2.json`, preserving the first report.
- No ledger row, machine measurement, rendered evidence, candidate PDF, source file, or TeX process was touched.
