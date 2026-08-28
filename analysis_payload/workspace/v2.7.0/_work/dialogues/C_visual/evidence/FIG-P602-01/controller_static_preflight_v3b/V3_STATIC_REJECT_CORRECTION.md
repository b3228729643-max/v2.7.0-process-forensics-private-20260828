# v3 static rejection and v3B correction map

The old `controller_static_preflight_v3` package is retained byte-for-byte as historical `STATIC_REJECT`. It was not executed and is not an authorized controller. At v3B design start its five identities were:

- controller: `F15449C911D53AC8E792432DD94A7B528CE9AFE29B88E74F0C8ED3B733F35187`
- handoff: `0F844CF2FE3701FAB9D798002225B01885AB0CAD79A5591B88E1E082A70EE5C0`
- dry run: `21036278C510B1069E07A372D2710F4CB29E2235EDFF8F576AC354FF021F37A7`
- freeze marker: `5C8DE9B254B47B24F65A6F7A915A93D89F3AA453A20F60B8F4E6B91571F471AE`
- v2/v3 difference: `41AEE0B222D3DCBD1F5C587CA895AF81A5E9183D3218C158E2EE6535FE29C9F1`

v3B preserves the accepted cache-containment design and corrects only the rejected controller-evidence gaps:

| Rejected v3 behavior | v3B correction |
|---|---|
| Claim only; no durable start identity | Atomic `DIRECT_INVOCATION_START.json` immediately after successful Process.Start, before output waiting |
| Nonzero/no-PDF throws without durable outcome | `DIRECT_INVOCATION_RESULT.json` is atomically written in finally before every post-start throw/return |
| Start exception not recoverably recorded | RESULT records `started=false`, exception, timing, PDF identity and post-process scan |
| Only parent Environment override inspected | Five independent kpsewhich queries verify effective `openout_any=p` and all four normalized TEXMF values |
| kpse failure evidence unspecified | Preclaim gate JSON is atomically written in cache root while candidate root is absent; PASS bytes are copied into candidate control root before claim |
| Freeze was content-only | All five v3B files, including the latest freeze marker, are set to OS `IsReadOnly=true` after content freeze |

There is no third build authorization in this package.

