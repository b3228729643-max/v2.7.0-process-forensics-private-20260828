# FIG-P715-01 first R99 SA1 isolation invalidation

- `HANDOFF_ID`: `A-R99-P715-SA1-FRESH-20260824`
- `DECISION`: `INVALID_ISOLATION_DO_NOT_USE`
- Reason: the reviewer read `PROMPT_RUNTIME_CORE.md`, `CONTEXT_CAPSULE.md`, and `CURRENT_TASK.json`, which contain project state/inventory conclusions forbidden to this blind SA1.

The reviewer disclosed the incident before producing an audit conclusion or ledger. Filesystem verification nevertheless found four preliminary artifacts in `STRICT_R1_SA1_FRESH_R99_20260824`: `candidate_identity.json`, `full_page_200dpi.png`, `page_763_300dpi.png`, and `render_initial.py`. They are retained unchanged as invalid history, must not be read or reused by any later P715 role, and provide no PASS/FAIL evidence.

The replacement reviewer writes only to `STRICT_R1B_SA1_FRESH_R99_20260824` and starts from the allowed R99/source/protocol inputs.

