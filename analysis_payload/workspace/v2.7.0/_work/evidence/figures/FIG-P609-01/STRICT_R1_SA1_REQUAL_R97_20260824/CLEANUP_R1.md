# Scoped R1 cleanup record

One self-generated, non-evidence Python bytecode cache is removed before final manifesting.

| Exact absolute path | Bytes | SHA-256 before removal | Reason |
| --- | ---: | --- | --- |
| `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P609-01\STRICT_R1_SA1_REQUAL_R97_20260824\__pycache__\p609_r1_audit.cpython-311.pyc` | 166252 | `F08C5525F51F7243A248351C74AA0A7D6116142E1D7B7965C8E251E7C4A40251` | Interpreter cache from this R1 generator; no final CSV/JSON/PNG/MD references it. The source `p609_r1_audit.py` remains. |

Precondition: `Resolve-Path -LiteralPath` resolved this exact item beneath the P609 R1 evidence root. The deletion used one literal, non-recursive command:

`Remove-Item -LiteralPath 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P609-01\STRICT_R1_SA1_REQUAL_R97_20260824\__pycache__\p609_r1_audit.cpython-311.pyc' -Force`

Postcondition verified: `Test-Path -LiteralPath` returned false and the cache directory had no remaining files. No other evidence file was targeted or removed.
