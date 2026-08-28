# FIG-P756-01 R12 local build audit

- Scope: local page/standalone wrappers only; no root official full-book build was run.
- Working directory: `v2.7.0/_work/source/v2.7.0/src/讲义源码/合并总册`.
- Engine: `lualatex`, two passes per wrapper, `-interaction=nonstopmode -halt-on-error -file-line-error -recorder`.
- Page wrapper log: `build/page/FIG-P756-01_R12_page.log`; hard-error/overflow/missing-glyph/font-warning scan: PASS.
- Standalone wrapper log: `build/standalone/FIG-P756-01_R12_standalone.log`; same scan: PASS.
- An initial parameter-resolution attempt produced no accepted evidence; its exact transient R12 artifacts were removed before the clean build above.
- Page PDF SHA256: `CA846B3275E99F9CCC2178D3DC6BAE9379FF433577139496565A22955F3C0B1E`.
- Standalone PDF SHA256: `0FCAB4CA10A9421BA4C2354CD9E412027CA562A4500D1E588FAB3CE98247B75F`.

## pdfinfo — page wrapper

```text
Title:           统计学习方法初学者讲义 v2.7.0——采样方法、主题模型与图排序（v2.7.0 完整解析版）
Subject:         统计学习方法初学者讲义 v2.7.0 完整解析版
Keywords:        统计学习方法, v2.7.0
Author:          
Creator:         LaTeX with hyperref
Producer:        LuaTeX-1.24.0
CreationDate:    Mon Aug 24 13:56:49 2026 �й���׼ʱ��
ModDate:         Mon Aug 24 13:56:49 2026 �й���׼ʱ��
Custom Metadata: yes
Metadata Stream: no
Tagged:          no
UserProperties:  no
Suspects:        no
Form:            none
JavaScript:      no
Pages:           1
Encrypted:       no
Page size:       595.276 x 841.89 pts (A4)
Page rot:        0
File size:       0 bytes
Optimized:       no
PDF version:     1.7
```

## pdfinfo — standalone wrapper

```text
Title:           统计学习方法初学者讲义 v2.7.0——FIG-P756-01 单图验证（v2.7.0 完整解析版）
Subject:         统计学习方法初学者讲义 v2.7.0 完整解析版
Keywords:        统计学习方法, v2.7.0
Author:          
Creator:         LaTeX with hyperref
Producer:        LuaTeX-1.24.0
CreationDate:    Mon Aug 24 13:57:01 2026 �й���׼ʱ��
ModDate:         Mon Aug 24 13:57:01 2026 �й���׼ʱ��
Custom Metadata: yes
Metadata Stream: no
Tagged:          no
UserProperties:  no
Suspects:        no
Form:            none
JavaScript:      no
Pages:           1
Encrypted:       no
Page size:       595.276 x 841.89 pts (A4)
Page rot:        0
File size:       0 bytes
Optimized:       no
PDF version:     1.7
```

## pdffonts — page wrapper

```text
name                                 type              encoding         emb sub uni object ID
------------------------------------ ----------------- ---------------- --- --- --- ---------
QBJMXD+STIXTwoText-Regular           CID Type 0C       Identity-H       yes yes yes     47  0
SVQLAV+NotoSerifSC-ExtraLight        CID TrueType      Identity-H       yes yes yes     49  0
WFTAVC+STIXTwoText-Bold              CID Type 0C       Identity-H       yes yes yes     51  0
KWYFWC+NotoSansSC-Bold               CID Type 0C       Identity-H       yes yes yes     52  0
```
