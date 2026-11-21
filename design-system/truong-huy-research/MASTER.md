# Design System (Master): Institutional Editorial / Sovereign Research

The source of truth for the visual architecture of **Truong Huy Research** (`truonghuyresearch.xyz`), replacing the previous Taste-kit service template.

## 1. Visual Direction & Philosophy

- **Aesthetic Persona:** Institutional Equity Research & Financial Editorial (inspired by *Financial Times*, *Goldman Sachs Global Investment Research*, and *Stripe Press*).
- **Core Principles:**
  - **Natural Document Flow:** Zero forced `100svh` screen slides or scroll-jacked gimmicks. Every section sizes naturally to its analytical content, separated by crisp `1px` structural hairlines.
  - **True Tabular Numerics:** Every ticker, share price, WACC input, sensitivity matrix cell, date, and implied upside/downside badge is set in **IBM Plex Mono** (`tabular-nums`), visually distinct from editorial commentary in **Source Serif 4** and **Libre Franklin**.
  - **Archival Warmth & High Contrast:** Warm alabaster paper (`#F7F6F2`) paired with elevated crisp white data sheets (`#FFFFFF`), `2px solid #0F1A2A` institutional top rules (`.sheet--accent`, `.card--rule`), and deep institutional navy (`#16325B`).
  - **Strict CSP Compliance:** Zero inline `style=""` attributes and zero inline executable scripts. Dynamic visual states use SVG presentation/geometry attributes, `<progress value max>`, `hidden`, `aria-*`, `data-*`, and bundled external Astro `<script>` modules.

## 2. Tokens (`:root` in `src/styles/site.css`)

| Role | Token | Value |
| :--- | :--- | :--- |
| Primary Paper Canvas | `--bg-paper` | `#F7F6F2` |
| Inset Surface / Band | `--bg-subtle` | `#EFECE6` |
| Elevated Data Sheet / Card | `--bg-elevated` | `#FFFFFF` |
| Sticky Header Glass | `--bg-glass` | `rgba(247, 246, 242, 0.92)` |
| Inverse Colophon / Tape | `--bg-navy` | `#0F1A2A` |
| Primary Ink | `--ink-primary` | `#0F1A2A` |
| Secondary Prose Ink | `--ink-secondary` | `#2D3B4E` |
| Muted Caption / Label Ink | `--ink-muted` | `#56657A` |
| Institutional Navy Action | `--accent-navy` / `--accent-navy-hover` | `#16325B` / `#0E2240` |
| Implied Upside / Gain | `--up` / `--up-soft` / `--up-mid` | `#0E6F3C` / `#E3F3EA` / `#C2E5D1` |
| Implied Downside / Loss | `--down` / `--down-soft` / `--down-mid` | `#B42318` / `#FBE9E7` / `#F5C6C2` |
| Reference Price / Dated Notice | `--amber` / `--amber-soft` | `#9A5B0A` / `#F9EFE0` |
| Method Lanes | `--m-dcf`, `--m-comps`, `--m-prec`, `--m-lbo` | `#16325B`, `#2B5B84`, `#5B82A6`, `#8FAABF` |

## 3. Typography (Self-Hosted via `@fontsource`)

- **Display (`--font-display`):** `Source Serif 4 Variable` (weight 400, `-0.02em` tracking) for headlines (`h1`–`h3`) and core analytical questions.
- **Sans (`--font-sans`):** `Libre Franklin` (weights 400, 500, 600) for body prose, navigation, buttons, and table descriptions.
- **Monospace (`--font-mono`):** `IBM Plex Mono` (weights 400, 500, 600) for `.eyebrow` labels, `.ticker` badges, `.num` figures, financial tables, sensitivity matrices, and telemetry bars.

## 4. Interactive Feature Architecture

1. **Global Command Palette (`CommandPalette.astro`, `Ctrl+K` / `⌘K` / `/`):** Instant diacritic-insensitive search across all 5 company valuation reports, 3 methodology hubs, 5 A4 tear sheets, and all 27+ weekly/monthly market notes.
2. **Interactive Company Valuation Desk (`index.astro` `#research`):** Desktop split selector + mobile/desktop ticker tabs (`HPG`, `BID`, `FPT`, `BMP`, `PNJ`) revealing each company's Football Field, executive stance, core analytical question, top 4 calibrated inputs, and direct workbook/PDF downloads.
3. **Interactive DCF Scenario Inspector (`SensitivityTable.astro`):** Live 5×5 WACC × Exit EV/EBITDA crosshair inspector showing selected inputs, implied share price, move vs. reference price, and delta vs. DCF base case.
4. **Method Spread & Divergence Comparator (`ValuationComparator.astro`) & Open Workbook Vault (`WorkbookVault.astro`):** Full coverage analytics and 14-file repository matrix on `/research`.
5. **HOSE Foreign Flow Monitor (`ForeignFlowMonitor.astro`):** Interactive 20-day / 60-day / All-session SVG bar and cumulative flow tracker powered by `_foreign_flow_cache.json`.
6. **Active Macro & Technical Framework Tracker (`MacroThesisTracker.astro`):** Visual SVG VN-Index Support/Resistance Ruler (`1,750`–`1,880`) and 3-tab narrative synthesis powered by `_quarterly_summary.json` and `_monthly_summary.json`.
7. **Market Note Reader (`MarketNote.astro`):** CSP-safe `<progress>` reading progress bar, diverging SVG cross-asset cards, sticky section spy TOC with word count & reading time, and `←`/`→` keyboard pagination.
