# SUPERSEDED — nonterminal integer-lattice quantisation correction

R6 correctly changed the gate to relative local-background effective
foreground contrast, but initially compared the replay blend in floating
point against an 8-bit official raster.  At the exact 20/255 boundary this
can falsely reject a real pixel (for example 235.45 rounds to official RGB
235, contrast 20).  R6 is nonterminal.  R7 rebuilds all evidence using the
same final 8-bit lattice quantisation before applying the >=20 gate and still
requires coordinate-wise direct/baseline/replay XOR=0.
