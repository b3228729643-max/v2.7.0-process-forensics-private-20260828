# P049 R1A evidence-only control reseal handoff

- route: `P049_R1A_EVIDENCE_ONLY_CONTROL_RESEAL_READY_FOR_MAIN`
- HANDOFF_ID: `A-R110-P049-SA2-R168-READONLY-R1A-CONTROL-RESEAL-20260827`
- UID: `FIG-P049-01`
- role/status: `SA2 / ROOT_ACCEPT_R1A_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1`
- business conclusion rerun: `0`; retained direction is R168 hard-defect count 0 / no source change
- controller invocation: `1`; retry: `0`; TeX/source/Git/role/second UID/central writes: `0`
- frozen rejected source root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R1_SA2_R168_READONLY_R110_20260827`
- accepted reseal root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R1A_SA2_R168_READONLY_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827`
- copied material payload: `7/7`; relative path/bytes/SHA/NTFS ticks mismatches: `0`
- new payload: `9` (seven copied + COPY_IDENTITY + COPY_PROVENANCE)
- controls: `3` (PAYLOAD_MANIFEST + SEAL_AUDIT + WSTOP)
- ordinary: `12`; manifest rows: `9`; manifest↔FS path/bytes/SHA/ticks mismatch: `0`
- read-only files: `12/12`; read-only directories: `1/1`
- JSON/CSV/PNG parse failures: `0/0/0`; ADS/pyc/pycache/reparse: `0/0/0/0`
- WSTOP strictly latest margin: `1,366,735 ticks`; files at/after marker excluding marker: `0`; postmarker root writes: `0`
- COPY_IDENTITY SHA-256: `400150EA2FFBA51F0C8DE0CE49470491F3E41902F181082EF69223D27FEEF625`
- COPY_PROVENANCE SHA-256: `C4BE39853181D94588AC853B692D0FC1D6D6D945D0D9670F5C1C1A18121783C3`
- PAYLOAD_MANIFEST SHA-256: `53DE5B83D38E52DA71F225F63E5E2CF63CCAB35B8666949A441DCDD8DD84D2B1`
- SEAL_AUDIT SHA-256: `3EEAD569B20793BF9694ADF96D64FD2795EF12A5FF300779994E640CC494087B`
- WSTOP SHA-256: `E6CEB8DACBE2CBC493C43D74CC3DD7CE766E21E4B85F079DFD293ED67382F4CE`
- root-external audit: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P049-01_R110_R1A_CONTROL_RESEAL_EXTERNAL_AUDIT_20260827.json`
- next action: main independently accepts R1A, then dispatches one completely fresh isolated SA1; A does not self-dispatch.

The old R1 root remained byte-for-byte untouched; its WSTOP SHA is still `127BD075C989AA1E4932B1BAE98867E3D4339C1555BC5F06EE5D231765DB4006`.
