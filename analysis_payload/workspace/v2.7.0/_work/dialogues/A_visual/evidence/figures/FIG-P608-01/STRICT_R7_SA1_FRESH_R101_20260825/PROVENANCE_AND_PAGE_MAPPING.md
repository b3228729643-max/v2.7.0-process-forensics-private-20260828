# Provenance and page mapping

This evidence package is a new, isolated SA1 reconstruction for handoff `A-R101-P608-SA1-FRESH-20260825`. It reads only the expressly permitted goal, protocol, schema, frozen R101 PDF, and current figure source. No old P608 evidence, root report, handoff, state, inventory, task packet, prior conclusion, or other figure package was read.

The initial dispatch described P608 as a physical page. Before the accepted audit evidence was built, the parent corrected that statement: P608 is the stable historical component of the figure UID, while the current R101 target is physical page 659 (one-based), printed page 646, Figure 32.8. This package independently confirmed the corrected mapping by locating the current source caption/label content in the frozen R101. The abandoned physical-page-608 path was not used in any accepted conclusion.

Frozen candidate identity: 814 A4 pages, 4,947,496 bytes, SHA-256 `0870FF226DC383875C4A1B6EABB06AAB942317DA294D90D2864B3030D46DF1A1`. Audit crop: 300 dpi integer rectangle `(292,920,2146,1875)`, corresponding to `[70.08,220.8,515.04,450.0]` pt and measuring 1854×955 px. The crop includes both panels and the complete Figure 32.8 caption natural paragraph.

Rawdict conservation is: page chars 837 = domain 120 + outside 717; domain 120 = final glyphs 112 + whitespace 8; page nonspace 778 = domain glyphs 112 + outside nonspace 666. PDF drawing conservation is 89 = preceding-equation 6 + target explicit 58 + page-corner 2 + following-prose rules 2 + following-figure 21. The two hatch layers are independently visible but absent from `get_drawings()`, so they are counted once as pattern objects and never double-counted with an explicit path.
