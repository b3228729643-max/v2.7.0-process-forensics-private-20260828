# Non-terminal / superseded machine output

The first two machine passes in this directory used a PDF character-bbox-local
colour-delta candidate before traceable glyph-path isolation.  In patterned
cards that candidate can absorb underlying hatch pixels.  Therefore all
pre-existing numerical H-ink, D/E, texture relationship, overlap and
clearance conclusions from those passes are **non-terminal and superseded**.

The replacement pass will construct every glyph mask from its mapped SVG/PDF
glyph shape, then intersect it only with the final official R95 300dpi pixel
foreground.  It will regenerate the contact sheets, inventories, measurements,
relations and terminal consistency check.  Do not use a pre-replacement result
as a PASS or FAIL conclusion.
