# Paint order and occlusion-reversal scope

The source and R95 vector drawing order were independently read for this figure.

1. The pale fitted background is emitted on TikZ `background layer`, before every card, text, and arrow.
2. Each stage card emits its opaque pale fill and border before that card's title/body text.
3. The three blue transition arrows are emitted after the cards, but their shortened endpoints do not cross any card foreground.
4. The gray return arrow is emitted with a real `fill=white` return-label node later in the same draw path. This is the only opaque textual ground that can possibly overpaint an already-emitted graphic foreground.

For item 4, `occlusion_ledger.csv` supplies separate native masks for the pre-occlusion return shaft, the true opaque white ground derived from PDF drawing index 22, the final-visible shaft, and their intersection. The raw result is `pre=3134`, `ground=35750`, `pre∩ground=0`, `final=3134`, and `missing_after_opaque_paint=0`; the direct 1× and 8× overlay is also retained. Thus this is a real ground-object reversal, not an assumed or synthetic halo.

Items 1–3 are background-before-foreground operations rather than foreground occlusion. They have no pre-existing text/data foreground to invert, so no unobserved `pre` layer is claimed for them.
