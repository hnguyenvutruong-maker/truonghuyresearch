# Truong Huy Research — "Research Terminal" (2026-11)

The source specification is [DESIGN.md](DESIGN.md), supplied by the owner. This file records how it
is implemented in `src/styles/site.css` and where the build deliberately differs.

## Implementation
- **Dark only.** The theme switch, light tokens and the inline theme script were removed.
  `vercel.json` is back to `script-src 'self'` with no hashes.
- **Surfaces** follow the prose palette in DESIGN.md: canvas `#0A0C10`, Level 1 `#12151D` (docks,
  sidebars, table headers), Level 2 `#1A1F2C` (active modules, table rows), hover `#22293A`,
  hairlines `#262E3D`. Ink is `#F8FAFC` / `#C2C6D6` / `#94A3B8` / `#64748B`.
  The front-matter Material tokens (`#051424`…) are not used, because they conflict with the prose
  values.
- **Semantic colours:** emerald `#10B981`, crimson `#EF4444` and amber `#F59E0B` (base case and
  price focus), each with 0.12 fills and 0.3 borders on pills. Cobalt `#3B82F6` marks controls,
  active tabs and the command palette.
- **Type:** Newsreader (titles: `.display` 36/44, `.h-lg`, `.h-md`, `.h-sm`), Inter (prose 15/13/11)
  and JetBrains Mono (every figure, label, table cell and button). All self-hosted through
  `@fontsource-variable`.
- **Shape:** 4px radii everywhere, no consumer shadows. The only overlay shadow is
  `0 8px 24px rgba(0,0,0,.65)` on the command palette and mobile drawer.
- **Shell:**
  - A fixed 48px command bar: brand, nav tabs with a cobalt underline, status pips for the model
    date and the last foreign-flow session, and the ⌘K trigger.
  - A 30px quote tape: VN-Index weekly close, each ticker's price used and implied-move band, and
    the latest HOSE foreign net.
  - A compact footer.
- **Grid:** `.ws` is 1 column below 1024px, 12 columns at 1024–1439px and 24 columns at ≥1440px,
  using `.col-24/16/14/12/10/8/7/6`. Gutter is 12px, margin 16px.
- **Panels:** `.panel` (Level 1 dock) with `.panel__head` (mono uppercase title, meta, actions),
  `.panel__body` and `.panel__foot`.
- **Tables:** `.dtable` has a 28px uppercase mono header and 30px Level 2 rows, with numbers
  right-aligned. `.dtable--pin` makes the first column sticky below 1024px, and `tr.subtotal`
  draws a double rule.
- **Range bar** (`FootballField.astro`):
  - Track, spread and markers: a 4px track, a cobalt 25% spread with 2px edges, a white pip at the
    price used and an amber diamond at the base case.
  - The outer SVG has no viewBox, so x positions are percentages and heights stay in px.
- **Sensitivity:** the base cell has a 1px amber halo and an amber tint. The other cells shade
  from crimson to emerald against the price used.
- **Report page:**
  - Three panes at ≥1440px: a sticky contents rail, the main column, and a sticky right rail with
    the valuation box and model files.
  - Two panes at 1024–1439px. On mobile the panes stack as nav chips, then the rail, then the main
    column.
- **Tear sheet:**
  - Print inversion to white, `#0F172A` ink and `#CBD5E1` rules.
  - The header carries the credential lockup (Nguyen Vu Truong Huy · UEH Finance & Banking ·
    Passed Level II of the CFA Program), the ticker and model date, and a valuation box in place
    of the spec's "target price box".

## Deliberate deviations from DESIGN.md (factual accuracy)
- **No BUY/HOLD/SELL ratings, target prices or 52-week ranges.** The research publishes valuation
  ranges against a dated price used, not ratings. The rating-pill styles are reused for implied
  moves and range signals ("All methods above / Straddles price / All methods below").
- **Sensitivity axes are WACC × exit EV/EBITDA, not WACC × terminal growth.** That is what the HPG
  and FPT workbooks compute.
- **The analyst lockup reads "UEH Finance & Banking"**, matching the owner record in CLAUDE.md.
