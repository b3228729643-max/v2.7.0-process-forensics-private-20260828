# Current authoritative pair evidence

Authoritative failure/critical IDs are exactly the `critical_pair_ids` in `machine_terminal_check.json` and the FAIL rows in `after_overlap_report.csv`. Every other pair directory, if present from an interrupted regeneration, is non-authoritative and must not be read as a current failure classification.
