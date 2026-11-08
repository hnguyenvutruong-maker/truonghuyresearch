# Design system (master)

The source of truth for the site's look since the second November 2026 redesign (it replaced
"Ledger", 2026-11-08). The site is built **on the Taste kit**, not merely inspired by it: the kit's
runtime ships in `public/assets/taste/` and owns layout, nav, footer, buttons, cards, rows,
motion and the moment. `src/styles/site.css` holds only what Taste lets a page write: the dealt
`:root` block (palette, type) and CSS inside visuals (charts, tables, the note body).

## Where it comes from

- **Taste** (`Leonxlnx/taste-skill`). Kind: *service* (people hire an analyst; site-kind other).
  The deal, one value per part:

  | Part | Value |
  |---|---|
  | hero | split: copy left, the work (every model's range) as the picture |
  | nav | nav-split (links left, wordmark centre, the CV button right) |
  | footer | footer-columns, with the close-word close ("Download the CV", then the name across the wrap) |
  | rhythm | surface pairs (`#notes` and alternate doc sections on the surface ground) |
  | buttons | tonal |
  | mark | stack |
  | radius | sharp |
  | moment | word-highlight (the "How a company is valued" statement; there are no photographs) |
  | palette | Frost and slate, accent institutional navy |
  | type | source-serif: Source Serif 4 at 400 over Libre Franklin |

  The kit's scripts (dealer, gate) could not run in the cloud build sandbox, so the deal was drawn
  by hand from the libraries and the pages were checked with an equivalent script at 390, 768,
  820, 1024 and 1440 wide: no sideways scroll, no text under 13px, equal content edges, the hero
  exactly one screen with its content inside, home sections whole screens, the moment mounted,
  the entrance flag set, no console errors.
- **UI/UX Pro Max** (`nextlevelbuilder/ui-ux-pro-max-skill`) supplied the colour: institutional
  navy `#1E3A5F` from *Research Lab*, kept on Frost and slate grounds.

## Home page plan (one screen per section)

| Screen | Content |
|---|---|
| hero | notice "Passed Level II of the CFA Program", h1, lead, "Download the CV" + "See the five reports", three facts; `CoverageStrip` as the picture |
| `#research` | peek list: five report rows; pointing at a row shows its football field in the frame (frame hidden under 1024px) |
| `#approach` | word-highlight statement; "the spread is the finding" is the highlighted phrase |
| `#notes` | surface ground: weekly VN-Index chart + the latest four notes |
| `#about` | the record beside a real tear-sheet page (`/research/tear-sheets/hpg-page.png`) |
| close | close-word footer |

Inner pages wrap their content in `<div class="doc">`, which opts out of the one-section-per-screen
rule, and open with `DocHead` (back link, label, h1, lead, aside).

## Tokens (`html:root` in site.css, outranking the kit's `:root`)

| Role | Token | Value |
|---|---|---|
| Ground / surface | `--p-bg` / `--p-surface` | `#F7F9FA` / `#ECF0F2` |
| Ink / muted | `--p-ink` / `--p-muted` | `#13212E` / `#4F5D6B` |
| Accent and action | `--p-accent` / `--p-action` | `#1E3A5F` |
| Inverse (footer) | `--p-inv-bg` / `--p-inv-ink` | `#0F1E2E` / `#EEF2F5` |
| Gain / loss | `--up` / `--down` (+ `-soft`, `-mid`) | `#13703A` / `#B42318` |
| Price a model used, dated figures | `--amber` | `#94590A` |
| Method lanes | `--m-dcf` `--m-comps` `--m-prec` `--m-lbo` | navy → pale steel |

Type: `--font-display` Source Serif 4 (weight 400, tracking −0.02em), `--font-text` Libre
Franklin 400/500; figures are tabular. All self-hosted via `@fontsource`.

## Rules

- Never edit files under `public/assets/taste/`; restyle through the `:root` block or visual CSS.
- Kit markup only for layout: `.wrap`, `.grid` + `.span-N`/`.start-N`, `.section-head(--split)`,
  `.rows`, `.card`, `.btn--primary/--secondary/--sm`, `.link`, `.t-*`, `.stack-N`, `.ground-surface`.
- One primary button per view. Labels in sentence case; nothing under 13px.
- CSP: the only inline script is the `m-enter` line in `BaseLayout`, whose hash is in `vercel.json`.
  No inline `style=""`; every figure carries its sign so colour is never the only channel.
