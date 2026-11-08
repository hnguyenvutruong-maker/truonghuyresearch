# Ledger: design system (master)

The source of truth for the site's look since the November 2026 redesign. Tokens live in
`src/styles/global.css`; this file records why they are what they are. Page-specific deviations
go in `pages/<page>.md` beside this file (none yet).

## Where it comes from

Two design skills, applied by hand to this site (their scripts were not run in the build
environment; their rules and data were read):

- **UI/UX Pro Max** (`nextlevelbuilder/ui-ux-pro-max-skill`, v2.15). Query: "financial research
  publication portfolio", dials variance 5, motion 3, density 7. Result used: pattern
  *Portfolio Grid*, style *Swiss Modernism 2.0* (12-column grid, rational spacing, hairline rules),
  colours *Research Lab* (institutional navy `#1E3A5F`, research amber, serif headings), the
  *Financial Trust* pairing for data (IBM Plex). A first query ("equity research analyst
  portfolio fintech") returned *Enterprise Gateway* / Dark OLED and was rejected as off-topic,
  as the skill's query contract asks.
- **Taste** (`Leonxlnx/taste-skill`, v2.5). Kind: *service* (people hire an analyst; site-kind
  other). Its rules decide the shell: one system, 90–95% neutral with one accent, light grade only
  (dark pages are for tech sites), a fixed opaque header with a hairline, equal content edges,
  the hero alone on the first screen and one section per screen on the home page, sentence-case
  labels (no tracked capitals), nothing under 13px, a hero entrance once, hover answers on every
  link and card, no scroll-reveal, and copy that names the category first.
  Dealt by hand from its libraries: palette family *Frost and slate* (trades: fintech, law),
  type *source-serif* (law, finance), radius *sharp* (fintech), buttons *solid*, footer
  *columns on the dark ground*, close *type*, rhythm *surface pairs*, mark *wordmark*,
  hero *split* with the work as the picture, moment *type* (the name set large in About).

## Tokens

| Role | Token | Value | Contrast on `#F7F9FA` |
|---|---|---|---|
| Ground | `--g-main` / `--g-alt` / `--g-card` | `#F7F9FA` / `#ECF0F2` / `#FFFFFF` | |
| Dark ground (footer only) | `--g-dark` | `#0F1E2E` | |
| Ink | `--ink` | `#13212E` | 15.5:1 |
| Muted (labels, meta) | `--muted` | `#4F5D6B` | 6.4:1 |
| Hairline / control border | `--line` / `--line-strong` | `#C9D1D8` / `#7C8996` | |
| Accent (buttons, links, focus) | `--action` | `#1E3A5F` | 10.9:1 |
| Price a model used, dated figures | `--amber` | `#94590A` | 5.4:1 |
| Gain / loss | `--up` / `--down` | `#13703A` / `#B42318` | 5.8:1 / 6.2:1 |

Type: Source Serif 4 (display, 500–600), IBM Plex Sans (text 400/500/600), IBM Plex Mono
(figures, tabular). Scale: `.t-display`, `.t-h1`, `.t-h2`, `.t-h3`, `.t-lead` 20, `.t-body` 17,
`.t-small` 15, `.t-label` 13 (the floor), `.t-figure`, `.t-data`. Radius 4 / 6 / 8. Spacing on
the 4-point scale; `.wrap` is 1280 wide with an 80 / 48 / 20 px gutter.

## Components

`.btn--primary` (one filled button per view: the main action, "Download the CV") and
`.btn--secondary`; `.link` (underline draws in on hover); `.card` (white, 1px hairline, lifts
2px when linked); `.rows` (hairline-ruled lists); `.ticker`; `.pill--up/down`; `.tag`; `.note`
(amber, dated figures). Data visuals: `CoverageStrip` (home hero: every model's method lanes in
implied-move terms), `FootballField`, `SensitivityTable`, `CoverageTable`, `VnIndexChart`.

## Rules kept from before

CSP stays `'self'`-only (no inline scripts now, so no hash); no inline `style=""`; fonts
self-hosted; every figure carries its sign so colour is never the only channel.
