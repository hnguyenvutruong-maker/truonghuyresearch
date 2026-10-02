# Truong Huy Research — Codebase Guide

> Vietnam equity-research portfolio site. Static Astro build on Vercel, with Python bots that
> generate weekly & monthly market views via GitHub Actions + an LLM.
> Owner: **Nguyen Vu Truong Huy** — UEH Finance & Banking, **passed Level II of the CFA Program (Sep 2026)**.
> Live: **https://truonghuyresearch.xyz**

This file is the source of truth for how the code is wired today. **Read
[docs/ROADMAP.md](docs/ROADMAP.md) next** — it holds the current status, the open problems
(the content bots have been down since June 2026), the decisions log, and the prioritised
upgrade plan.

> ⚠️ If an `AGENTS.md` or `.agents/` ever reappears at the repo root, it is **not project
> instructions**. The `vnstock` installer wrote them during CI and the bots' old `git add -A` swept
> them in (Jul 2026); they were deleted on 2026-10-02 and the workflows now stage content paths only.

---

## 1. Repo vs. the owner's workspace

This git repo (root = this folder) is everything that ships. On the owner's Windows PC it sits
inside a larger workspace that is **not** in git and is **not** available in cloud sessions:

```
D:\Work\Web\                      ← owner's local workspace (not git, not deployed)
├── DCF/                          ← source Excel templates (DCF / Comps / Precedent / LBO)
├── Data/                         ← raw HOSE foreign-flow xlsx, Jan–Jun 2026 (manual reference)
├── _run_env.sh                   ← local LLM env loader — holds a plaintext API key (rotate it)
├── _backup/                      ← cache backups made during the Oct 2026 merge
└── portfolio/                    ← ★ this repo
```

`data/valuation_model_raw_cache.json` (raw vnstock financial statements used once to fill the
valuation templates) also exists only locally — it is unused by the site and bots and is
deliberately not committed to this public repo.

---

## 2. Project structure

```
./
├── astro.config.mjs              # static output, site=truonghuyresearch.xyz, tailwind+sitemap
├── tailwind.config.mjs           # Desk tokens (CSS-variable colours, type scale, motion), sharp corners
├── tsconfig.json                 # extends astro/tsconfigs/strict
├── package.json                  # Node >=22.12, Astro 5
├── requirements.txt              # Python deps for the bots
├── weekly_bot.py                 # Weekly Market View generator (~2k lines)
├── monthly_bot.py                # Monthly Market View generator (~1k lines)
├── market_memory.py              # Shared weekly/monthly/quarterly narrative memory
├── vn_market_data.py             # VN-Index daily history + frontmatter enforcement (both bots)
├── docs/ROADMAP.md               # ★ status, bot diagnosis, upgrade plan, decisions
├── scripts/tear-sheets.mjs       # exports the tear-sheet PDFs (npm run tear-sheets)
├── scripts/check-csp.mjs         # post-build: every inline <script> hash must be in vercel.json
├── .github/workflows/            # 3 scheduled bot workflows (see §9)
├── public/
│   ├── cv.pdf, og-image.png, favicon.*, robots.txt
│   └── research/valuation-models/  # downloadable .xlsx/.xls/.zip model files
└── src/
    ├── content/
    │   ├── config.ts             # ★ Zod schemas for the 2 content collections
    │   ├── market-views/         # WEEKLY .md posts + bot state JSON (_*.json)
    │   └── monthly-views/        # MONTHLY .md posts + _monthly_summary.json
    ├── data/valuation-models.ts  # ★ the "research"/valuation data (NOT a collection)
    ├── lib/format.ts             # shared number/date formatters (UTC dates, signed %, VND k)
    ├── lib/notes.ts              # normalises weekly + monthly entries into one NoteSummary
    ├── lib/files.ts              # build-time sizes of public/ downloads
    ├── lib/tone.ts               # Tone = neutral | profile | value | market (panel colours)
    ├── scripts/theme.ts          # day/night theme engine (auto by local hour, toggle, clock switch)
    ├── layouts/BaseLayout.astro  # shell: head/meta, fonts, header/footer, motion, mobile menu
    ├── styles/global.css         # colour tokens (day :root / night [data-theme=dark]), .u-link, reveal, print
    ├── components/               # ValuationMethodPage (see §7)
    │   └── ui/                   # Panel, header/tape/footer, SkyIntro, charts, tables, note views
    └── pages/                    # routes (see §7)
```

---

## 3. Stack & commands

- **Astro 5** (`output: 'static'`), TypeScript **strict**, **Tailwind 3.4** via `@astrojs/tailwind`,
  `@astrojs/sitemap`, `@astrojs/rss`, `@tailwindcss/typography`, `sharp`, `@vercel/analytics`.
- `lightweight-charts` renders the VN-Index chart (`VnIndexChart.astro`).
- **Python** bots use `yfinance`, `feedparser`, `requests`+`beautifulsoup4` (all optional — code
  degrades if a lib/source is missing). **`vnstock` was removed on 2026-10-02**: its PyPI project
  is quarantined (Sep 2026). Do not reinstall it from another source.

| Command | Action |
| :-- | :-- |
| `npm install` | Install JS deps |
| `npm run dev` | Dev server → http://localhost:4321 |
| `npm run build` | Production build → `dist/` (must pass with **0 errors**) |
| `npx astro check` | TypeScript / content-schema check (0 errors expected) |
| `pip install -r requirements.txt` | Install bot deps |
| `npm run tear-sheets` | Build, then export `public/research/tear-sheets/*.pdf` (needs Chrome) |
| `python weekly_bot.py` | Generate the latest Weekly Market View |
| `python monthly_bot.py` | Generate the previous Monthly Market View |

---

## 4. Design system — Desk (day / night)

Bloomberg-style desk: a dark navy header and market tape over framed panels, one colour per
section, so text always sits on a solid panel, never on the page background. Chosen 2026-10-02
(replacing Broadsheet). `BaseLayout` takes `title`, `description`, `image` (OG card path), `type`
and always renders `ui/SiteHeader`, `ui/MarketTape` (latest weekly close, foreign flow, macro),
`ui/SiteFooter`, `ui/Motion` (scroll reveal + count-up), `ui/CommandPalette` and `ui/SkyIntro`.
Fonts are self-hosted: `@fontsource-variable/archivo` (wdth), `@fontsource-variable/source-sans-3`,
`@fontsource/ibm-plex-mono` 400/500/600 (no Google Fonts). Icons are inline SVG via `ui/Icon`.

- **Day / night theme.** `<html data-theme="light|dark">` is set before first paint by the inline
  script in `BaseLayout`: **light (white) 06:00–17:59 local time, dark (black) from 18:00 to
  05:59**, unless the visitor chose one with the header toggle (`localStorage['thr-theme']`;
  `data-theme-mode="manual|auto"`). `src/scripts/theme.ts` owns the toggle (`toggleTheme`; picking
  the auto theme clears the override), switches automatically at the next 06:00/18:00
  (`scheduleClock`), and dispatches a `themechange` CustomEvent `{ theme, source:
  'load'|'toggle'|'clock' }`. Charts listen to it and repaint. Print always uses the day palette.
- **SkyIntro** (signature effect): on the first page of each visit (`sessionStorage['thr-sky-seen']`)
  and on every toggle/clock switch, a small framed toast rises under the header — a sun with
  turning rays by day, a crescent moon and twinkling stars by night — with a greeting for the
  local hour. `role="status"`, non-blocking, hides after ~5 s, closes on × or Esc.
- **Color tokens** are CSS variables of RGB channels (`--c-*` in `global.css`, light on `:root`,
  dark under `[data-theme="dark"]`) exposed as Tailwind colours with `/<alpha>` support, so one
  class set serves both themes — **never hard-code a hex for themed surfaces or text**:
  `canvas` (page), `panel` / `panel-alt` (panels, rows), `line` / `line-strong` (borders), `fg` /
  `fg-muted` (text), `link`, `up` / `up-soft` (**gains**), `down` / `down-soft` (**losses**),
  `chrome` / `chrome-deep` / `chrome-fg` / `chrome-muted` / `chrome-line` (navy header, tape,
  footer, neutral bars — dark in both themes). Section colours: `profile` violet, `value` teal,
  `market` amber; `DEFAULT` fills title bars (white text), `*-ink` is the same hue tuned for text
  on a panel in the current theme. Fixed: `tape.up/down` (on the always-dark tape), `sun`, `moon`.
  Every pair is ≥ 4.5:1 in both themes (axe: 0 violations, Oct 2026) — re-check if you add one.
- **Type:** `font-display` (Archivo — headings, h1, figures), `font-sans` (Source Sans 3 — body),
  `font-mono` (IBM Plex Mono — labels, kickers, data, ticker badges). Scale: `text-display, h1, h2,
  h3, lead, body, small, label, data, figure`. Use `tabular-nums` on figures.
- **Components** (`components/ui/`): `Panel` (the framed block: coloured title bar + solid body;
  props `title`, `meta`/meta slot, `tone`, `as`, `level`, `id`, `flush`, `reveal`, `bodyClass`),
  `PageHeader` (framed page header: back/context strip, kicker, h1, lead; `before`/`aside` slots),
  `SectionTitle` (swatch + kicker + h2, `aside` slot), `Tick` (teal ticker badge), `DatedNote`
  (amber "Dated figures" callout), `Disclaimer`, `CoverageTable` (shared coverage table, `sortable`
  adds client-side sort with `aria-sort`), `FootballField` (method ranges vs the reference price,
  inline SVG, `compact`), `SensitivityTable` (DCF grid, up/down shading around the reference
  price), `VnIndexChart`, `MarketNote` (weekly/monthly detail body + reading-progress bar),
  `NoteList` (notes by year with All/Weekly/Monthly filter synced to `?kind=`), `CommandPalette`
  (Ctrl/⌘+K, `/`, or any `[data-palette-open]`; index built at compile time), `SkyIntro`.
- **Layout idiom:** content goes in a `Panel` — never loose text on `bg-canvas`. Title bars are
  mono uppercase labels; data rows are `border-b border-line` lists with the value right-aligned;
  gains/losses use `text-up`/`text-down` (or the `*-soft` pills). Page pattern: `PageHeader` in the
  section's tone, then panels in a 12-column grid with `gap-4`/`gap-5`.
- **Motion:** `animate-rise` for above-the-fold load stagger, `data-reveal` for scroll reveal,
  `data-countup="N"` on figures inside a revealed block, `sky-rise`/`sun-spin`/`glow`/`twinkle`
  for SkyIntro. Content is fully visible without JS; `prefers-reduced-motion` drops durations.
- **CSS** (`global.css`): tokens, sharp corners, selection/focus colours, `.u-link` (underline
  drawing in on hover), scroll reveal, theme cross-fade (`html.theme-ready`), print palette.
  **Give every link an explicit `hover:text-…` class.**
- **Charts:** `VnIndexChart` (lightweight-charts, dynamically imported when the chart nears the
  viewport; reads the `--c-*` tokens and repaints on `themechange`; area for weekly closes, up/down
  candles when `vn_index_daily` exists; the TradingView logo is off because it injects inline
  CSS — the text attribution link replaces it). Hand-built charts are inline SVG with marks on a
  fixed viewBox and all text in HTML; no inline `style` (set dynamic values through CSSOM).
- **OG cards** (`og/[...path].png.ts`) use the day palette: navy band, white panel with a teal
  (report) or amber (note) title bar, Archivo + IBM Plex Mono from `@fontsource/archivo` /
  `@fontsource/ibm-plex-mono` `.woff` files (satori cannot read woff2).

### Global rules
- **CSP** (`vercel.json`) allows only same-origin scripts, styles, fonts and connections. Astro is
  set to never inline scripts/CSS (`astro.config.mjs`). The single inline script (the theme
  bootstrap in `BaseLayout`: sets `data-theme`, `data-theme-mode` and `class="js"`) is allowed by
  its SHA-256 hash — **if you change it or add another `is:inline` script, update the hash in
  `vercel.json`**; `npm run build` runs `scripts/check-csp.mjs`, which fails and prints the
  missing hash. No third-party scripts, fonts or iframes without
  widening the CSP deliberately. JSON-LD / JSON data blocks are fine (not executed).
- **Print:** `global.css` sets A4 pages and forces scroll-reveal content visible; hide chrome
  with `print:hidden`.
- **Sharp corners everywhere** (`border-radius: 0 !important`; Tailwind radius 0 except `full`).
- Tailwind utility classes only — no inline `style=""`. Arbitrary values/properties are fine.
- Mobile-first, must work at 375px with no horizontal page scroll. No `any`; props typed.
- Zero lorem ipsum / no visible placeholders; finance-accurate English copy.
- `npm run build` and `npx astro check` must pass with 0 errors before a task is done.

The rejected alternative direction, **Sơn mài** (Vietnamese lacquer: black, cinnabar, gold,
eggshell inlay; Cormorant Garamond + Be Vietnam Pro), lives on branch `redesign/son-mai` for
reference only.

---

## 5. Content collections (`src/content/config.ts`)

Two collections. **Files named by date** (`YYYY-MM-DD.md`). Files starting with `_` are **bot
state, not entries** (Astro ignores leading-underscore files).

### `market-views` = **WEEKLY** views (not daily!)
Frontmatter (Zod): `title`, `date`, `week_start`, `week_end`,
`session_tone` ∈ {positive|negative|neutral}; VN-Index `vn_index_open/high/low/close`,
`vn_index_weekly_change_pct`, `avg_daily_liquidity_bn_vnd`,
`foreign_net_weekly_bn_vnd` (nullable), `foreign_buy/sell_weekly_bn_vnd` (nullable opt);
macro `dxy_close/_weekly_change_pct`, `usd_vnd/_weekly_change_pct`,
`btc_close/_weekly_change_pct`, `gold_*`, `wti_*` (all **nullable**); optional
`vn_index_daily[]` OHLC (bots emit it from 2026-10 on; older files lack it). File date = the Friday.

### `monthly-views`
Same idea with `_monthly_` variants, plus `month_start`, `month_end`, `trading_days`,
`best_sector`/`best_sector_change_pct`, `worst_sector`/`worst_sector_change_pct`.
File date = last calendar day of the month.

The weekly bot may emit `foreign_net_estimated` in frontmatter; it's not in the schema and Zod
ignores it — don't rely on it in pages.

State JSON (managed by the bots, never hand-edit except to merge data):
`market-views/_quarterly_summary.json`, `_foreign_flow_cache.json`, `_market_memory.json`;
`monthly-views/_monthly_summary.json`.

---

## 6. The "research" / valuation data layer (`src/data/valuation-models.ts`)

The valuation section is a **typed TypeScript module, not a content collection.**

Exports: `portfolioDisclaimer`, `valuationGroups` (`dcf`, `comparable`, `transaction-lbo`),
`methodPages` (group → route), `valuationModels` (**5 companies**: `hpg`, `bid`, `fpt`, `bmp`,
`pnj`), helpers `outputCentre`, `impliedMovePct`, `formatOutput`, `outputMethodLabel`,
`STALE_AFTER_DAYS` (90), and the types (`ValuationModel`, `ValuationOutput`, `ReferencePrice`,
`SensitivityGrid`, `ValuationGroup`, `ValuationDownload`, `ValuationNote`, `ReportPoint`,
`ValuationReport`, `ValuationGroupId`, `ProjectStatus`, `OutputMethod`).

Each `ValuationModel` carries `slug`, `ticker`, `company`, `sector`, `status`, `lastUpdated`,
`outputRange`, `investmentQuestion`, `keyAssumptions[]`, `methods[]`, `summary`, `conclusion`,
`valuationNotes[]`, a `report{ headline, stance, thesis[], assumptions[], valuationResult[],
interpretation[], risks[], disclaimer }`, and `downloads[]` (→ `public/research/valuation-models/`).
Plus the numeric layer the charts and tables use:
- `referencePrice { value, asOf, source }` — the share price the model pack used as its market
  input, read from the workbooks' "Valuation Summary" / `TargetCo!E17` cells. All five are as of
  2026-06-11. **It is not a live price**; every implied move is against it, and pages show a
  "Dated figures" note once a model is older than `STALE_AFTER_DAYS`.
- `outputs[] { method, low, high, base?, approximate?, basis }` in VND per share (low = high for a
  point estimate). DCF ranges span the sensitivity grid's corners; `base` is the model output.
- `sensitivity?` — WACC × exit EV/EBITDA grid (VND thousands) for HPG and FPT, **recomputed from
  the DCF workbook** (same UFCF, mid-year discounting, net debt, shares; centre cell = model
  output). The workbooks' own Excel data tables are empty (never recalculated) — don't read them.

The homepage, `/research` (via `ui/CoverageTable`) and the report pages read `outputs`;
`report.valuationResult` is the prose list in each report's "Valuation range" panel.

**To add/edit a company report, edit this file** — pages and method pages derive from it. When a
model is refreshed, update `lastUpdated`, `referencePrice`, `outputs` and (for a DCF) regenerate
`sensitivity` from the new workbook so the centre cell matches the model output.

---

## 7. Pages & components

| Route | File | Notes |
| :-- | :-- | :-- |
| `/` | `index.astro` | Analyst panel (name, CFA line, CTAs) + Markets panel, Profile (`#about`), Coverage (`#valuation`: lead note + football field + `CoverageTable`), Market notes (`#market-views`: chart + briefs). |
| `/research` | `research.astro` | Sortable coverage table (price used, each method + implied move, low/high move; client-side sort with `aria-sort`) and the methods index. |
| `/research/[slug]` | `research/[slug]/index.astro` | Company report: fact file, dated-figures note, section index, football field + outputs table, thesis, assumptions, DCF sensitivity, conclusion, risks, model files, prev/next, Report JSON-LD. |
| `/research/dcf`, `/research/comparable-analysis`, `/research/precedent-transactions-lbo` | thin wrappers | render `<ValuationMethodPage groupId=…/>`. |
| `/market-views` | `market-views/index.astro` | All notes by year with All/Weekly/Monthly filter, weekly-close chart. |
| `/market-views/[slug]`, `/monthly-views/[slug]` | `*/[slug].astro` | Both render `ui/MarketNote` from `lib/notes.ts` summaries: data band, cross-asset strip, daily chart, sticky "In this note" index, prev/next. |
| `/monthly-views` | `monthly-views/index.astro` | Monthly notes only. |
| `/contact`, `/disclaimer`, `/404` | static | |
| `/research/[slug]/tear-sheet` | `research/[slug]/tear-sheet.astro` | One-page A4 summary; exported to `public/research/tear-sheets/<slug>.pdf` by `npm run tear-sheets` (builds, then prints with `playwright-core` + installed Chrome; `CHROME_PATH` overrides). **Re-run it whenever a model changes** and commit the PDFs; report pages link the PDF only if it exists. |
| `/og/<path>.png` | `og/[...path].png.ts` | Build-time 1200×630 OG cards (satori + sharp, fonts from `@fontsource`) for every report and note. |
| `/rss.xml` | `rss.xml.ts` | Weekly + monthly feed with full note HTML (`markdown-it` + `sanitize-html`). |

`ValuationMethodPage` sits in `components/`; everything else lives under `components/ui/` (§4).

---

## 8. Python bot pipeline

### `weekly_bot.py` — Weekly Market View
VN-Index daily OHLCV (`vn_market_data.py`: VNDirect dchart API → `yfinance ^VNINDEX.VN`; **the
run aborts with exit 1 if neither works**) + liquidity (volume × CafeF HOSE avg share price; abort
if unavailable) → foreign flow (sum of daily cache) → sector proxies (`yfinance` leading stocks) →
macro DXY/Gold/WTI/BTC + USD/VND (`yfinance`, change vs prior week's close) → news (RSS → CafeF
scrape → yfinance) → **LLM #1** writes commentary + frontmatter → **measured values overwrite the
frontmatter** (`vn_market_data.enforce_frontmatter`) → inject `vn_index_daily` → validate → write
`market-views/<friday>.md` → **LLM #2** updates `_quarterly_summary.json` → update
`_market_memory.json`.
CLI: `--week YYYY-MM-DD`, `--rebuild-summary Q2-2026`, `--skip-news`, `--skip-summary`,
`--collect-foreign-flow` (cache today's flow only, no LLM), `--deploy`.

### `monthly_bot.py` — Monthly Market View
Same sources via `vn_market_data.py` (aborts without real VN-Index data); week-by-week recap is
built from the daily rows; macro changes are vs the prior month-end close. Writes
`monthly-views/<month-end>.md`, updates `_monthly_summary.json`.
CLI: `--month YYYY-MM` (default: previous month on days 1–5, else the current month), `--skip-summary`.

### `market_memory.py`
Shared narrative state linking latest weekly, current monthly, and quarterly summaries.

### Data-quality model
- Foreign flow has **no historical API** → `--collect-foreign-flow` must run **daily** (it exits 1
  when every source fails). The cache keeps every day (no pruning since 2026-10-02; Jun–Jul days
  were restored from the file's git history). Cache starts 2026-06-15.
- **No synthetic data.** VN-Index and liquidity are required (else abort). Macro, sectors and
  foreign flow stay `null` when unavailable; pages render `null` as "—" and the LLM is told the
  field is unavailable.
- Index weekly/monthly change = period close vs period's first open (unchanged definition); macro
  change = period close vs the previous period's last close.
- Windows stdout/stderr is reconfigured to UTF-8.

---

## 9. Automation (`.github/workflows/`)

17:00 ICT = 10:00 UTC (GitHub usually starts these hours late). Jobs check out the branch tip,
commit as "Market Bot" staging **only `src/content/market-views` / `monthly-views`**, then
`git pull --rebase` + push; shared `concurrency: market-bot`; all support `workflow_dispatch`
(weekly takes a `week` input, monthly a `month` input, for backfills). On failure each workflow
opens — or comments on — a GitHub issue titled `Market bot failing: <workflow name>`; close it
once green.

| Workflow | Schedule | Does | Status (2026-10-02) |
| :-- | :-- | :-- | :-- |
| `daily_foreign_flow.yml` | `0 10 * * *` | `weekly_bot.py --collect-foreign-flow` → commit cache | fixed in code (pip) — verify first run |
| `weekly_market_view.yml` | `0 10 * * 5` | collect flow (best effort) → `weekly_bot.py` → commit | ❌ LLM 401 until the owner fixes the key/vars (§10) |
| `monthly_market_view.yml` | `0 10 28-31 * *` + ICT month-end guard | collect flow (best effort) → `monthly_bot.py` → commit | ❌ same LLM 401 |

---

## 10. LLM configuration

Provider-neutral OpenAI-compatible `/chat/completions` over `urllib`.

| Env var | Default | Notes |
| :-- | :-- | :-- |
| `LLM_API_KEY` | — (required) | falls back to `OPENAI_API_KEY` |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | any OpenAI-compatible base |
| `LLM_MODEL` | `gpt-5.2` | model override |

CI reads `secrets.LLM_API_KEY` and optional `vars.LLM_BASE_URL` / `vars.LLM_MODEL`. **No repo
variables are set**, so CI calls OpenAI — while the secret (created 2026-06-09, when the project
switched to Ollama/MiniMax) is probably not an OpenAI key → HTTP 401.

---

## 11. Deployment & security

- **Vercel** static hosting (project `portfolio`). The Vercel project was connected to this GitHub
  repo on **2026-10-02**: a push to `master` deploys production and other branches get preview
  deployments (the bots' cache commits deploy too). Before that date, deploys were made by hand
  with the Vercel CLI from the owner's PC. Domain `truonghuyresearch.xyz` (A → 76.76.21.21);
  `www` currently serves 200 instead of redirecting.
- Some `weekly_bot.py` comments mention Cloudflare Pages — stale.
- Never commit credentials. The owner's local `_run_env.sh` holds a plaintext key → rotate it.
  Keep CI keys in GitHub Secrets.

---

## 12. Content QA rubric for bot-written notes

Frontmatter numbers are the ground truth; LLM prose drifts. When reviewing or regenerating notes:
- Directional words must match the frontmatter sign (no "DXY collapsed" when the change is +).
- Never invent prior-week closes — check the previous file's frontmatter.
- Q2-2026 references (DXY 104.33, WTI 79.36, USD/VND 25,499) are quarterly baselines, not prior-week values.
- Don't claim a close below support when only the intraday low undercut it.
- Measured titles ("Falls", not "Crashes"); fix "intrawEEK"-style artifacts and lowercase run-ons.
- Monthlies: month-specific facts, not generic if/then ladders.
- Notes up to 2026-06-05 may carry synthetic cross-asset values, and their macro "weekly" changes
  were really one-day changes (Thu→Fri). Don't "correct" the numbers; make prose consistent.

---

## 13. Conventions & gotchas

- `market-views` = weekly, `monthly-views` = monthly; there is no daily collection.
- "Research" = the `valuation-models.ts` module, not a collection.
- CFA wording must follow CFA Institute guidance: **"Passed Level II of the CFA Program"** (or
  "Passed Level II, CFA Program"); never "CFA Level II" as a title, never a CFA-mark-styled badge.
  Only say "Level III Candidate" once the owner confirms registration for the Level III exam.
- `public/cv.pdf` is maintained by the owner outside the repo.
- Line endings: repo stores LF; Windows checkout uses `core.autocrlf=true`.
- `.vercelignore` keeps the Python bots out of Vercel builds. Anchor every pattern with `/` —
  an unanchored `data/` also matched `src/data/` and deleted `valuation-models.ts` from the build.
