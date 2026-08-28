# C0114 U+0031 manual component resegmentation

Reviewer: `SA2_P547`

I opened the native 1x original overlay and mask-only views and the 8x card for `C0114`, and compared them with pristine peers `C0023`, `C0030`, and `C0109`. All four are `U+0031`, `STIXTwoMath-Regular`, emitted at `8.0896 pt`, in the same `NATURAL_SCRIPT` role.

The GEN3 mask for C0114 was visibly contaminated by disconnected rule/edge pixels and measured `H=33 px`, `area=164 px`. Exact connected-component ownership retains the unique 122 px digit component and excludes the exact 42 foreign pixels. The corrected GEN4 mask measures `H=23 px`, `area=122 px`, exactly matching all three pristine peers. The current mask-only image contains only the digit and no geometric equals rule, subscript neighbor, or border pixel.

Manual decision: `PASS` for the corrected GEN4 mask; GEN3 remains `SUPERSEDED` and cannot support acceptance.
