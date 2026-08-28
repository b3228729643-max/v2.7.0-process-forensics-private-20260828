# Identity and independent page location

- HANDOFF_ID: `C-FIG-P602-01-R103-SA1-FRESH-ISOLATED-V1`
- Reviewer instance: `/root/sa1_fig_p602_r103_fresh_isolated`
- Figure ID: `FIG-P602-01`
- Result of independent location: physical PDF page **653**; printed page **640**; caption begins `图32.5 Metropolis–Hastings 单次更新中的提议判定及拒绝自环。`

## Official R103 candidate identity

- Path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf`
- Bytes: `4,967,184`
- Pages: `817`
- Media size: `595.2760009765625 × 841.8900146484375 pt` (A4)
- SHA256: `9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23`

## Current single P602 source identity

- Path: `D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_mh_accept_reject.tex`
- Bytes: `2,869`
- Lines: `36`
- SHA256: `6C4E8F156709C0FF384F9E7B7F2BD5D9CB586E24206BF0BCD2E58933ED3DB47D`

## Independent locator method

I verified the candidate identity first, extracted text from every page of the 817-page PDF in memory, split the extraction at physical page boundaries, and searched for the unique `Metropolis–Hastings` caption and its Chinese continuation. The unique hit occurred in physical chunk 653. I then read that page itself and observed page-header number 640 and caption number 32.5. No announced page number, freeze report, old evidence, state file, or prior-agent result was used.

The complete located-page text is preserved in `machine/located_page_text.txt`. Direct page renders preserve the same physical/printed identity in `machine/render_inventory.csv`.
