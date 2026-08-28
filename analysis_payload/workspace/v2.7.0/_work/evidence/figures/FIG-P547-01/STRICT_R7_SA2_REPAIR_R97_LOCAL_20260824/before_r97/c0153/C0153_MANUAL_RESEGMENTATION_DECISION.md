# C0153 manual resegmentation decision

Reviewer: `SA2_P547`

I opened the R97 native 1x original overlay pure-mask and foreign-mask views plus both 8x candidate/calibration cards. The candidate semicolon has exactly two intended components with `H=28 px` and `area=57 px`; the independent calibration has `H=28 px` and `area=58 px`. The height ratio is `1.0000` and area ratio is `0.9828`.

The 45 px neighboring component and 1 px edge singleton are visibly foreign and remain only in the separate blue/exclusion evidence. Neither is included in the pure target mask. The clean candidate therefore passes its low-profile calibration and no source change is justified from the contaminated legacy mask.

Calibration identity: PDF SHA256 `7DE754DBA9059C5FD69EA580C1CD388B2EBB9B2E99379BC4359E513A39D8149B`; TeX SHA256 `3B795A17656792563770FCCA31AAE61A42BE3961920FEB6EFBBD315E506FBC54`; 300 dpi render SHA256 `C160BD013B1070D1A62352E59E92054D0D7B70475082D4093772E19E58570A86`.
