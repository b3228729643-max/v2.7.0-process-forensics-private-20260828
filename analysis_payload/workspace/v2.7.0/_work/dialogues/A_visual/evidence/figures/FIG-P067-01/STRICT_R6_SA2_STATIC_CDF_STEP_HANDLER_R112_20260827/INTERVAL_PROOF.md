# Static CDF interval proof

The ordered CDF coordinates remain byte-for-byte unchanged:

`(.5,0) (1,.15) (2,.45) (3,.80) (4,1) (4.5,1)`.

With `const plot mark left`, each horizontal segment carries the value of its left coordinate until the next support location. Therefore the intended right-continuous CDF is:

| Interval | Frozen value | PMF cumulative interpretation |
|---|---:|---|
| `[.5,1)` | `0` | no support mass accumulated before `1` |
| `[1,2)` | `.15` | mass at `1` accumulated |
| `[2,3)` | `.45` | `.15 + .30` |
| `[3,4)` | `.80` | `.15 + .30 + .35` |
| `[4,4.5]` | `1` | `.15 + .30 + .35 + .20` |

The four filled endpoints and four open endpoints remain unchanged. At every support point, the open endpoint represents the left limit and the filled endpoint represents the jump-inclusive value. The handler change thus aligns the horizontal segments with the existing endpoint semantics, PMF data, right continuity, and caption without altering any numerical coordinate.

Static preservation checks:

- CDF coordinate-list occurrence: 1 before/after.
- Filled-endpoint plot occurrence: 1 before/after.
- Open-endpoint plot occurrence: 1 before/after.
- Existing lower-PMF tick-label patch remains untouched.
- Axes, fonts, colors, strokes, annotations, labels, alt text, and caption remain untouched.
- Reverse-substituting the single new handler token reconstructs the exact 4,015-byte baseline with SHA-256 `C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0`.

This is static-only evidence. Pixel geometry, endpoints, grayscale, caption/page integration, and all-pairs regression must be measured from a newly authorized PDF; no rendered PASS is claimed here.
