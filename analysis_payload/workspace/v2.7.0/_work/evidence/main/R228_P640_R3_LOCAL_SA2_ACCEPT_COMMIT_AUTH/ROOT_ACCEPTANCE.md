# Revision 228｜FIG-P640-01 R3 本地 SA2 验收与提交授权

- 中央裁决：`LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1`。
- 唯一源补丁：在既有右侧极限注释节点加入 `fill=white,inner sep=1pt`；一文件 1+/1-，after SHA=`A1CB852A7B433D3B3FB39EB4F4E0310FD1F76631F01F366AF9D4B1B1B2FF434B`，`git diff --check` PASS。
- 唯一 direct LuaLaTeX PID 1664，invocation 1、retry 0，自然 exit 0；PDF 40,389 bytes，SHA=`E2AE5C0DACA6C9D07B43D61D00E9FA5580E63417DE15871D8DC6BA3842F9F2D2`；post TeX 0。
- 新 PDF 分母 N40、C780、glyph160、critical76、clip40、drawing20；机器失败、人工失败、R168 hard font failure、clip failure 均为 0。
- `PAIR_0688`：中央实际打开 native 1x 与右面板，金色曲线止于极限注释首个 `N` 左下方，最终可见墨迹不融合。
- `PAIR_0779`：独立前景 shared 0，最近距离 4px，正交空白 3px，满足门值 3px；中央实际打开 native 1x，marker 与 tick 可见分离。
- sealed root ordinary64；manifest62行，path/bytes/SHA mismatch0；WSTOP后更晚文件0。
- 授权 C 恰一次单源原子提交；只允许当前 P640 源，不得夹带 P639/状态/证据/其他文件，不启 TeX/fresh 角色。
- 本地 SA2 通过不计 A_LOCAL_PASS；inventory仍为`32 SA1 / 53 SA2 / 1 SA3 / 13 A_LOCAL_PASS`，严格最终0/99。

