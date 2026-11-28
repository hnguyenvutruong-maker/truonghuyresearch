---
name: Truong Huy Research Terminal
colors:
  surface: '#051424'
  surface-dim: '#051424'
  surface-bright: '#2c3a4c'
  surface-container-lowest: '#010f1f'
  surface-container-low: '#0d1c2d'
  surface-container: '#122131'
  surface-container-high: '#1c2b3c'
  surface-container-highest: '#273647'
  on-surface: '#d4e4fa'
  on-surface-variant: '#c2c6d6'
  inverse-surface: '#d4e4fa'
  inverse-on-surface: '#233143'
  outline: '#8c909f'
  outline-variant: '#424754'
  surface-tint: '#adc6ff'
  primary: '#adc6ff'
  on-primary: '#002e6a'
  primary-container: '#4d8eff'
  on-primary-container: '#00285d'
  inverse-primary: '#005ac2'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#ca8100'
  on-tertiary-container: '#3e2400'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#adc6ff'
  on-primary-fixed: '#001a42'
  on-primary-fixed-variant: '#004395'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#051424'
  on-background: '#d4e4fa'
  surface-variant: '#273647'
typography:
  display:
    fontFamily: Newsreader
    fontSize: 36px
    fontWeight: '500'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Newsreader
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Newsreader
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Newsreader
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Newsreader
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
  label-mono-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: -0.01em
  label-mono-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: -0.005em
  label-mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.75rem
  margin: 1rem
  space-xs: 0.25rem
  space-sm: 0.375rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 1.75rem
---

## Brand & Style

This design system delivers an institutional-grade equity research environment tailored for professional buy-side analysts, portfolio managers, and rigorous valuation modeling. The visual atmosphere fuses the precision of an ultra-low-latency financial workstation with the prestige of a legacy research publication. 

The aesthetic is anchored in an authoritative **Financial Modernist / High-Density Technical** ethos:
- **Tone:** Authoritative, mathematically rigorous, unembellished, and uncompromisingly credible.
- **Audience:** Institutional equity analysts, asset managers, and corporate valuation specialists requiring instantaneous data ingestion and deep-dive financial disclosure.
- **Visual Weight:** Dark obsidian surfaces preserve ocular stamina during intensive 14-hour modeling sessions. Micro-hairlines replace heavy card drop-shadows, creating clean structural registers where tabular data and valuation sensitivities take paramount visual hierarchy.

## Colors

The palette employs deep chromatic dark-space calibration to maintain exceptional typographic contrast while avoiding eye fatigue. Semantic indicators adhere strictly to financial conventions without aggressive neon oversaturation.

### Canvas & Surface Hierarchy
- **Base Terminal Canvas:** `#0A0C10` — The foundational viewport backdrop.
- **Surface Layer 1 (Workspaces / Sidebars):** `#12151D` — Recessed utility modules, docking trays, and secondary analytical navigation.
- **Surface Layer 2 (Active Cards & Tables):** `#1A1F2C` — Primary analytical surfaces, tear-sheet modules, and active data tables.
- **Surface Interactive / Hover:** `#22293A` — Row highlight states and button hover feedback.
- **Structural Dividers & Rules:** `#262E3D` — Hairline 1px grid alignments, table borders, and split-pane dividers.

### Semantic Financial Accents
- **Positive / Outperform / Delta (+):** `#10B981` (Subdued Emerald). Paired with `rgba(16, 185, 129, 0.12)` for range fills and status tags.
- **Negative / Underperform / Risk (-):** `#EF4444` (Controlled Crimson). Paired with `rgba(239, 68, 68, 0.12)` for impairment marks and downside buffers.
- **Neutral / Target / Highlight:** `#F59E0B` (Institutional Amber). Applied for base-case targets, pending ratings, and sensitivity focal points.
- **Primary Interface / Action:** `#3B82F6` (Terminal Cobalt). Reserved for terminal controls, active tab indicators, and primary command inputs.
- **Print / High-Contrast Tear-Sheet Inversion:** `#FFFFFF` ground with `#0F172A` ink and `#CBD5E1` borders for physical A4 exports.

## Typography

The typographic hierarchy establishes clear editorial authority while safeguarding quantitative accuracy.

1. **Research Editorial Titles (`Newsreader`):** Emulates top-tier macro and equity research journals. Used for company coverage initiating notes, rating updates, executive investment thesis headlines, and target price narratives.
2. **Body & Prose Analysis (`Inter`):** Clean, neutral sans-serif rendering macro commentary, earnings notes, and disclosure statements with zero visual distortion across multi-column layouts.
3. **Data & Numerical Metrics (`JetBrains Mono`):** All tabular listings, forward multiples (EV/EBITDA, P/E), DCF discount rates, WACC matrices, and timestamps mandate monospaced typography with tabular numerical alignment (`font-variant-numeric: tabular-nums`). Decimal points across financial statements must align perfectly along vertical axes.

## Layout & Spacing

The terminal layout utilizes an institutional ultra-dense grid designed to maximize screen real estate and reduce vertical scroll distance.

- **Grid Architecture:** 24-column flexible grid system allowing micro-modular financial docks (e.g., 4 cols for financial summary badges, 12 cols for interactive DCF sensitivities, 8 cols for consensus revisions).
- **Density Tier:** High-density baseline. Standard table rows sit at `28px` to `32px` vertical height to present 25+ rows of audited financial data above the standard fold.
- **Breakpoints:**
  - **Desktop / Bloomberg Dual-Display (`>= 1440px`):** 24 columns, full workspace multi-panel dock, fixed 48px global command bar, split horizontal sensitivity desks.
  - **Laptop / Compact (`1024px - 1439px`):** 12 columns, secondary telemetry docks collapsed into collapsible tabs.
  - **Mobile Research Desk (`< 1024px`):** Single column fluid stack. Complex tabular models convert to horizontal-scroll viewports with the company metric column pinned (`position: sticky; left: 0`).

## Elevation & Depth

Visual hierarchy is maintained through precise dark-surface stratification and razor-thin slate dividers, completely eschewing standard consumer drop-shadows.

- **Level 0 (Canvas):** Pure base (`#0A0C10`). Hosts non-interactive terminal backgrounds and canvas gutters.
- **Level 1 (Dock Container):** Elevated surface (`#12151D`) bounded by a 1px solid hairline (`#262E3D`). Houses contextual navigation, table containers, and chart toolbars.
- **Level 2 (Active Modules & Overlays):** Interactive panels (`#1A1F2C`) framed with `#262E3D`. When elevated as an analyst flyout or valuation parameter modal, depth is defined by a subtle 1px border shift to `#3B82F6` and an ambient tint shadow: `0 8px 24px rgba(0, 0, 0, 0.65)`.
- **Level 3 (Focused Cells & Command Palette):** Command palette floating overlay with backdrop filter `blur(12px)` and solid border `1px solid #3B82F6`.

## Shapes

The design system enforces an engineered, precise geometry. Radii are kept tightly bounded to maintain structural discipline:
- Inputs, analytical chips, and data buttons use a strict `0.25rem` (`4px`) radius.
- Analytical docking cards and tear-sheet module frames adhere to `0.25rem` (`4px`).
- Circular indicators are restricted solely to operational status pips (e.g., Live Market Open, API Feeds).

## Components

### Buttons & Interactive Controls
- **Terminal Primary:** Background `#3B82F6`, text `#FFFFFF`, 4px border radius. Padding: `6px 12px`. Typographic scale: `label-mono-md`.
- **Ghost Utility:** Transparent background, `1px solid #262E3D`, text `#94A3B8`. Hover: background `#1A1F2C`, text `#F8FAFC`, border `#3B82F6`.
- **Rating Pills:** Structured badges with subdued fills:
  - *BUY / OUTPERFORM:* Background `rgba(16, 185, 129, 0.12)`, text `#10B981`, border `1px solid rgba(16, 185, 129, 0.3)`.
  - *HOLD / NEUTRAL:* Background `rgba(245, 158, 11, 0.12)`, text `#F59E0B`, border `1px solid rgba(245, 158, 11, 0.3)`.
  - *SELL / UNDERPERFORM:* Background `rgba(239, 68, 68, 0.12)`, text `#EF4444`, border `1px solid rgba(239, 68, 68, 0.3)`.

### Tabular Financial Statements
- **Headers:** Background `#12151D`, height `28px`, bottom hairline `1px solid #262E3D`. Text: `label-mono-sm`, uppercase, color `#64748B`.
- **Data Rows:** Background `#1A1F2C`, height `28px`, border-bottom `1px solid #1E2533`. Text: `label-mono-md`. Numeric cells right-aligned. Hover row: `#22293A`.
- **Section Subtotals / CAGRs:** Font weight `600`, top border `1px solid #334155`, bottom border `1px double #334155`, background `rgba(255, 255, 255, 0.02)`.

### Valuation Methodology Range Bar
- A compact horizontal comparative spread bar displaying 52-week Range, DCF Value, Historical EV/EBITDA, and Target Price.
- **Track Base:** Height `4px`, color `#262E3D`, radius `2px`.
- **Valuation Spread Range:** Background `rgba(59, 130, 246, 0.25)`, border-left and right `2px solid #3B82F6`.
- **Current Price Marker:** Vertical pip `10px` high, `2px` wide, color `#F8FAFC`.
- **Target Price Marker:** Diamond indicator (`6px x 6px`), color `#F59E0B`.

### 5x5 Valuation Sensitivity Matrix
- **Row Axis:** Cost of Capital (WACC: e.g., 8.0% to 10.0% in 50 bps increments).
- **Column Axis:** Terminal Growth Rate (g: e.g., 2.0% to 4.0% in 50 bps increments).
- **Base Case Center Cell (3,3):** Highlighted with a `1px solid #F59E0B` halo and amber tinted background `rgba(245, 158, 11, 0.08)`.
- **Dynamic Gradient Fill:** Cells dynamically color-shift from muted red (`rgba(239, 68, 68, 0.15)`) for downside intrinsic values to muted emerald (`rgba(16, 185, 129, 0.15)`) for premium intrinsic values relative to current stock price.

### A4 Institutional Tear-Sheet Mode
- Media print layout resets background to `#FFFFFF`, text to `#0F172A`, borders to `#CBD5E1`.
- Header introduces institutional research metadata: analyst credential lockup (*Nguyen Vu Truong Huy, UEH Finance, Passed Level II of the CFA Program*), coverage date, ticker index, and target price box.