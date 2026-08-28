# P126 R15 static handoff

`HANDOFF_ID=A-R115-P126-SA2-STATIC-FORGET-PLOT-PATCH-20260828`

`STATUS=STATIC_ONLY_NOT_RENDERED_NOT_PASS`

`SOURCE_BEFORE_BYTES=4626`

`SOURCE_BEFORE_SHA256=6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502`

`SOURCE_AFTER_BYTES=4686`

`SOURCE_AFTER_SHA256=2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405`

`INCREMENTAL_DIFF=5+/5-`

`ORDINARY_ADDPLOTS=5`

`ORDINARY_ADDPLOTS_WITH_FORGET_PLOT=5`

`MANUAL_LEGEND_IMAGES=2`

`LEGEND_ENTRIES=2`

The five ordinary plot specs are statically excluded from the legend list; the two unchanged manual legend-image specs are therefore the only candidates paired with the two entries. Render validation remains pending. Request Main acceptance and one explicit controlled standalone/direct LuaLaTeX build slot; do not infer PASS from this static handoff.
