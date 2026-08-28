# P654 R19 machine FAIL report

Status: `MACHINE_FAIL_TO_SA2_SOURCE_R4_REQUIRED`.

## Candidate identity

- Evidence root: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R19_SA2_R18_DIRECT_BUILD_20260825`
- PDF: `build\v260_FIG-P654-01_standalone.pdf`
- PDF identity: 1 A4 page, 43,967 bytes, SHA-256 `CD5BEE00763E6F7571BDDA493BC240F829D0CD7344DE5C04440888AD18E9639A`
- Source SHA-256 before/after build: `CDAD08C2FDD21B4DA1C1F67431B6743C703CA6629C5F6E346C671FC48C01DB0D`
- Wrapper SHA-256 before/after build: `FE44F2E6005D884A6916A11C6EBCB89CF40BD523A64D8F8C6BC8124DBABC0CA1`
- Unique direct LuaLaTeX invocation: parent PID 20436, child PID 14104, natural exit 0, 42.762 s, retry 0, latexmk 0. The build slot was released with all four TeX process classes absent.

## Frozen denominator and machine gates

- Taxonomy was frozen before pixel measurement from `PANEL_ID|ROLE|SCRIPT_CLASS`, PDF font metadata and current semantic parent. It did not read element ID, height, area, PASS or rank.
- Glyphs: 93; visible foreground drawings/rules: 21; total objects: 114.
- Complete unordered pairs: 6,441 expected and 6,441 actual; critical pairs: 174.
- Pair failures after the explicit seven-edge endpoint/design whitelist: 0.
- Illegal overlap failures: 0; clip failures: 0.
- The four former base-formula failures are closed: G0040/G0059/G0064 genuine U+002B plus and G0065 genuine U+004E uppercase N each measure H=25 against the frozen base-math median 25. Target G0005 mathematical n also measures H=25 and meets its absolute 22px gate.
- Both former application-label clearance failures are closed: P06198 and P06219 each measure 19px against the 3px gate.
- Source role gate is closed: all base-formula source objects use 10.7pt, max/min 1.0 and span 0pt.

## Decisive hard failure

`G0063` is the natural TeX subscript digit `0` in the predictive denominator. Its frozen key is `PANEL_MAIN|FORMULA_SUBSCRIPT|SUBSCRIPT_MATH`; the complete group is G0058 italic i H=24, G0061 italic i H=24 and G0063 digit 0 H=22. The median is 24, so G0063 has `22/24 = 0.916666666667`, below the unchanged `[0.92,1.08]` gate. Its absolute natural-script height passes, but the D/E hard gate fails. No exact-glyph regrouping or manual override is permitted.

## Evidence integrity and route

The machine generator contains no manual ledger creation and no manual reviewer/boolean/decision/note field writer. R19 contains zero MANUAL/manual files, zero `.pyc`, and zero `__pycache__`. Machine identities include `MACHINE_RESULT.json` SHA `5194822204A6758D0B094DAE5098F80ED0C478E0A4F72409AC97B487BCEAF13A`, pixel table SHA `14A4D5CE2D9ED8119488C2858AC33E2A04FD0CF06EB4017DC35F5621890907A5`, all-pair table SHA `ED438DE6005403823F474A39B76C5985D543411D320DAFF51FB342243F67C160`, critical table SHA `47D5B57AD9FE2B2B9B278DCD3BBBA6196B23475213CBCCCD5534041A082CE49D`, and generator SHA `57F0B565DA12E510DC6255C2929C71D431D597CE618806E785B3EFFE44E0E96F`.

Because a deterministic hard failure already fixes the round verdict, no artificial manual PASS ledger is created and no fresh SA1/SA3 is started. R19 is evidence of `FAIL_TO_SA2`, not LOCAL/A_LOCAL_PASS. The next source round must preserve genuine U+002B, genuine uppercase U+004E N, target n, the 19px clearances, the seven relations and the unified formula role while closing the natural subscript group without exact-glyph taxonomy or per-element manual exemption.
