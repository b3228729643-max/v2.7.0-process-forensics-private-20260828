# R491 Main decision: P126 R3B V1 static reject; P687 SA2 registered

Timestamp: `2026-08-28T09:46:45+08:00`

## P126 R3B V1 static review

Main read both frozen scripts completely and independently recomputed their preinvoke inputs.

Passed static facts:

- Controller `18,006` bytes/SHA256 `598FDE0B70AE314539D69E311BE6E7D5E72D5F31010923186A4BFED43F0F1D37`, auditor `14,933` bytes/SHA256 `7D90522321A569E99074A103E58DB0CE1888752B4C79232DF269D600F682EF56`; both ReadOnly and PowerShell 7 AST errors `0`.
- Controller/auditor Move-Item sites `1/0`, New-Item `0/0`, Remove-Item `0/0`, process-management `0/0`; controller sole move is the external staged marker into the fixed root.
- Frozen old manifest SHA256 `405541B02D962FD75161DAEBB41C067955D7B99B992DD1F14A7399D3A6EB0D7E`; exact lowercase five-column schema; rows `205`; unsafe/escaping paths `0`; canonical duplicates `0`; missing material `0`; actual material `205`; ordinal set difference `0`.
- Destination, stage, controller result and auditor result are all absent; V1 invocation remains `0/0`.
- Controller's principal order is correct: copy205, add identity/provenance for payload207, write two premarker controls, freeze all files/directories/root ReadOnly, create a no-BOM future marker outside the root, perform one final move, and only then take read-only snapshots and write the external result.

Static rejection reasons:

1. The auditor checks `oldRows.Count=205` and `copyRows.Count=205` but never compares the old-manifest path set with the COPY_IDENTITY path set and never joins every copy row back to the corresponding frozen five fields. A substituted 205-row copy set is therefore not independently excluded.
2. Provenance validation covers only source root, destination root and old-manifest SHA. Seal audit is parsed but none of its semantic fields are validated.
3. The marker requires some keys to exist, but its values are checked only for handoff/operation/roots and five hashes. Verdict, counts, source snapshot, hard defect, business-rerun flag and invocation/budget fields are not validated; an exact marker key set is not enforced.
4. Controller-result identity, invocation/retry, natural exit and counts are not validated before the auditor trusts snapshot fields.
5. The old material contains ten CSV and seven JSON files, but the auditor parses only a small list of known control files rather than every final-root CSV/JSON.
6. The canonical function only changes path separators and does not itself reject rooted, absolute, empty-segment, dot, parent or escaping paths. The real manifest is safe, but the frozen control chain does not bind that safety invariant.

V1 is therefore frozen unmodified and uninvoked. Only a V2 static correction is authorized under the same HANDOFF/operation/destination/count contract. V2 must add robust canonical/path containment, old-manifest-to-copy ordinal field-by-field closure, full provenance/seal/marker/controller-result semantic validation, all-root CSV/JSON parsing, stage absence, old-controls0, old-root0 and postmarker0 checks. V2 must return frozen identities and pause with destination/stage/results absent and invocation `0/0`; execution is not authorized.

P126 remains SA2, the R3A business FAIL direction remains preserved but uncounted, and source/build/commit authority remains held.

## P687 role registration

- HANDOFF `C-FIG-P687-01-R115-SA2-R168-READONLY-ADJUDICATION-V1`.
- Actual canonical instance `/root/sa2_fig_p687_r115_r168_readonly_v1`, model/effort/fork `gpt-5.6-sol/xhigh/none`.
- Parent immediate pre-spawn and child pre-artifact gates both proved UID parent and fixed root Leaf/Container/Any `false`; one instance only, with zero artifact/root creation at child gate.
- Child independently matched official R115, current P687 source and exact V5-C06 chapter bytes/SHA and continues under the exact-file whitelist without directory search or fallback.
- P687 transitions `SA1 -> SA2`. Inventory becomes `30 SA1 / 32 SA2 / 0 SA3 / 38 local pass`; strict final remains `0/99`; B remains `66/66`.
