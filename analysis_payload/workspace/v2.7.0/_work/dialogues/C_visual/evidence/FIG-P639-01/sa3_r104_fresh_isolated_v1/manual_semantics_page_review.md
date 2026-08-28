# Independent mathematics, content, grayscale, and page review

REVIEWER_TYPE=`AI_SA3_VISUAL_REVIEW`; HUMAN_CERTIFICATION=`false`.

## Mathematics and object content

For a standardized bivariate normal target with correlation `rho=0.6`,

- `X1 | X2=b` has mean `rho*b = 0.6*0.75 = 0.45` and variance `1-rho^2 = 0.64`;
- `X2 | X1=a` has mean `rho*a = 0.6*1 = 0.60` and the same variance `0.64`;
- a `N(mu,0.64)` density has peak `1/sqrt(2*pi*0.64) = 0.4986778505...` and exponent coefficient `1/(2*0.64)=0.78125`.

The two source expressions use `0.498678*exp(-0.78125*(x-.45)^2)` and `0.498678*exp(-0.78125*(x-.60)^2)`. The rendered peak heights, mean guides, labels, note, caption, and neighboring derivation therefore agree. No normalization, variance/standard-deviation, coordinate-direction, or parameter-role error was found.

## Reading and grayscale

The figure itself reads from direct labels to the two shifted curves, then to the mean guides and common-variance note. Blue is solid with a light fill; gold is dashed; the two mean guides also have different dash patterns. The grayscale crop retains the solid-versus-dashed and filled-versus-unfilled distinctions. Labels and note remain outside the curve ink.

## Caption and neighboring text

The caption is identical to the current source and states one numerical reading result. Chapter lines 408–412 introduce figure 33.6, input this figure, and then introduce figure 33.7.

## Hard page-integration failure

On official R104 physical page 689, the next paragraph is visibly split around this float:

1. above FIG-P639-01: `图 33.7 使用上述解析自相关而非伪造轨迹，比较不同 |rho|`
2. FIG-P639-01 and its two-line caption
3. below the caption: `下的混合速度。`

Thus a single sentence about figure 33.7 is interrupted by figure 33.6 and its caption. The isolated fragment is followed by a large unused lower-page region. This breaks the reading order and page integration; R168 does not relax geometry, reading sequence, or page integration. It is the sole hard blocker found in this SA3.

Required SA2 repair: contain/place FIG-P639-01 so the line-411 figure-33.7 sentence remains contiguous and FIG-P639-01 stays with its own introduction/caption. Use a source-local float-placement or barrier repair within the allowed figure source, then rebuild the official candidate and regenerate the complete native-300-dpi, pair, clip, grayscale, and page-integration evidence.

