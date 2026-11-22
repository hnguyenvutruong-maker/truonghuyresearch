# Truong Huy Research — "Folio" research design system (2026-11)

Replaces the Institutional Editorial / Once UI systems. Modelled on the layout language of the
Folio (Ruixen UI) landing template the owner supplied — dark workspace, floating pill nav,
app-window product surfaces, bento cards, tabbed showcase, FAQ with side nav, closing horizon
band and a rounded footer card — rebuilt from scratch for a research site. No template code,
fonts or photos were copied: Tiempos Headline (commercial) is replaced by Source Serif 4, and
the landscape photos by a CSS/SVG dusk sky whose horizon is the VN-Index weekly-close series.

## Tokens (`src/styles/site.css`, `:root` + `:root[data-theme='light']`)
- Dark first (`data-theme="dark"` default, persisted in `localStorage.theme`, set before paint by
  the one hashed inline script in `BaseLayout`). Light theme mirrors every token.
- Surfaces: `--bg #0b0b0c`, `--bg-raised`, `--surface`, `--surface-2/3`; hairlines `--border`,
  `--border-soft`, `--border-strong`; text `--fg`, `--fg-2`, `--fg-3`.
- Primary button = inverted (`--primary-bg` near-white on dark, near-black on light).
- Semantic: `--up`, `--down`, `--amber` (price used / reference), `--blue`, `--violet`, `--teal`,
  each with `-bg` and `-line` tints for pills. Method lanes: `--m-dcf` blue, `--m-comp` teal,
  `--m-prec` violet, `--m-lbo` amber.
- Type: Source Serif 4 Variable 700 (`.display-*` headings), Geist Sans 400/500/600 (UI, prose),
  Geist Mono 400/500/600 (all figures, `.num`, `.mono`, `.eyebrow`).

## Components (classes)
- Nav: `.site-nav > .nav-bar` floating pill, `.nav-links`, `.nav-search` (⌘K), `.theme-switch`
  (sun/moon segmented), `.nav-cta`, `.nav-drawer` (mobile).
- Buttons: `.btn` + `--primary | --secondary | --ghost`, sizes `--sm | --lg`; `.chip`, `.seg`
  (segmented control for in-window tabs/filters), `.tag` (+ colour modifiers), `.signal`, `.kbd`,
  `.announce` (hero pill).
- App window: `.window`, `.window__bar`, `.window__side` (+ `.side-link`), `.window__head`,
  `.toolbar`, `.window__pad`, `.window__foot`; tables `.dtable` inside `.table-scroll`.
- Landing: `.hero` + `Sky.astro`, `.marquee`, `.feature-row`, `.bento` (`.b-2/.b-3/.b-4/.b-6`),
  `.pipe`, `.qlist`, `.timeline`, `.tabs`/`.tab`, `.masonry` + `.note-card`, `.faq` +
  `.faq-item` (`<details>`), `.cta`, `.footer-card`.
- Inner pages: `PageHeader.astro` (`.page-head`, `.crumbs`, `.facts`), `.subnav` (coverage),
  `.report` (sticky `.side-nav[data-spy]` + `.report__main` sections), `.kv`, `.stats`,
  `.quote`, `.prose-list`, `.files`/`.file`, `.pager`, `.dated`, `.disclosure`, `.prose`.
- Charts: football field (`.ff*`), VN-Index (`.vni-svg`, `.c-*` classes), flow (`.flow-*`),
  levels ruler (`.r-*`, `.level`), sensitivity grid (`.sens`, `.s-up2…s-dn2`). All colours come
  from CSS classes so both themes work; no inline `style=""` (CSP `style-src 'self'`).
- Tear sheet `.ts` is always light and prints on one A4 page.

## Rules
- Mobile first; no horizontal page scroll at 375px (wide tables scroll inside `.table-scroll`;
  single-column grids use `minmax(0, 1fr)`).
- Motion: `[data-reveal]` fade-up (only when `html.js`), marquee, tab panels; all disabled under
  `prefers-reduced-motion`.
- Generic behaviours live in `BaseLayout`: theme switch, nav drawer, reveal, `[data-tabs]` tablists
  (arrow keys), `[data-spy]` scroll-spy.
