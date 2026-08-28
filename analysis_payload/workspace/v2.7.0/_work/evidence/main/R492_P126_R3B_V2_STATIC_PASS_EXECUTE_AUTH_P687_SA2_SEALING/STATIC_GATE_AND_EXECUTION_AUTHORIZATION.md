# R492 Main decision: P126 R3B V2 static pass and one-shot execution authorization

Timestamp: `2026-08-28T10:01:16+08:00`

## P126 R3B V2 static acceptance

Main read the frozen V2 controller and auditor completely and independently recomputed the executable preconditions.

- Controller: `22,117` bytes/SHA256 `77DC115B6156AB778D4C9042AEF821C1D05E12D9DE1846417BA34C02AAB2DD0D`; auditor: `28,387` bytes/SHA256 `9A2D81ED080E94CC9849E37390DCA55AB96F160BCDC60CA0F1242163F5A10F04`. Both are ReadOnly and parse with PowerShell 7.6.4 AST errors `0`.
- Controller/auditor command sites are respectively Move-Item `1/0`, New-Item `0/0`, Remove-Item `0/0`, process-management `0/0`, while/do loops `0/0`, TeX-family tokens `0/0`, and Split-Path `0/0`. The sole move is the external staged marker into the fixed destination as the final root operation.
- Destination, both V1/V2 stages and both V1/V2 controller/auditor results are absent; destination parent exists. V1 remains frozen and uninvoked; V2 invocation is `0/0` before this authorization.
- Frozen old manifest SHA256 is `405541B02D962FD75161DAEBB41C067955D7B99B992DD1F14A7399D3A6EB0D7E`; exact lowercase five-column schema, rows `205`, blank fields `0`, canonical duplicates `0`, missing files `0`, identity mismatches `0`, actual material `205`, ordinal case-sensitive set difference `0`. The old root remains `208` files and `12` directories including root, all ReadOnly.
- Main extracted only `Get-CanonicalRelative` and `Resolve-UnderRoot` from each frozen script for no-write tests: three valid cases pass, eight invalid/rooted/dot/parent cases accepted `0`, escape accepted `0`.
- V2 closes every R491 defect: ordinal old205-to-copy205 path/five-field equality and live source/destination recomputation; complete provenance, seal-audit, marker and controller-result semantics; exact 22-key marker; all final-root CSV/JSON parsing with expected counts; robust canonical containment; old-controls0, stage absence, old-root0 and destination postmarker0.

Main therefore authorizes exactly one V2 controller invocation with retry `0`. Only if that frozen controller returns natural success/exit `0` may exactly one frozen V2 auditor invocation run with retry `0`. Any first error stops the chain without script modification, retry, repair, reseal, replacement, cleanup, source action, TeX/build, Git, role migration or second UID. P126 remains SA2 and its source scope remains inactive until Main independently accepts the sealed R3B result.

## P687 concurrent status

The same fresh P687 SA2 instance independently localized the current caption at physical page `737`, froze `N=19` and `C=171`, opened the required page/figure/overlay/mask and six native1x+NN8x ROI pairs, completed manual objects `19/19` and pair rows `171/171`, and reports `159 CLEAR + 12 ALLOWED_TOPOLOGY_CONTACT`, illegal visible-ink overlap `0`, clip `0`, unresolved `0`. This is a nonterminal checkpoint only. P687 remains SA2 and continues to one seal with no boundary expansion.

Inventory remains `30 SA1 / 32 SA2 / 0 SA3 / 38 local pass`; strict final remains `0/99`; B remains `66/66`.
