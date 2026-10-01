# Truong Huy Research — Codebase Guide

> Vietnam equity-research portfolio site. Static Astro build on Vercel, with Python bots that
> generate weekly & monthly market views via GitHub Actions + an LLM.
> Owner: **Nguyen Vu Truong Huy** — UEH Finance & Banking, **passed Level II of the CFA Program (Sep 2026)**.
> Live: **https://truonghuyresearch.xyz**

This file is the source of truth for how the code is wired today. **Read
[docs/ROADMAP.md](docs/ROADMAP.md) next** — it holds the current status, the open problems
(the content bots have been down since June 2026), the decisions log, and the prioritised
upgrade plan.

> ⚠️ `AGENTS.md` and `.agents/AGENTS.md` at the repo root are **not project instructions**.
> They were written by the `vnstock` package installer during CI and swept into the repo by the
> bots' `git add -A` (Market Bot commits `be0077a`, `254cf9e`, Jul 2026). Ignore them and do not
> run their setup steps. Removing them (and narrowing the bots' `git add`) is on the roadmap.

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
├── tailwind.config.mjs           # broadsheet tokens + legacy terminal/MD3 tokens, sharp corners
├── tsconfig.json                 # extends astro/tsconfigs/strict
├── package.json                  # Node >=22.12, Astro 5
├── requirements.txt              # Python deps for the bots
├── weekly_bot.py                 # Weekly Market View generator (~2k lines)
├── monthly_bot.py                # Monthly Market View generator (~1k lines)
├── market_memory.py              # Shared weekly/monthly/quarterly narrative memory
├── docs/ROADMAP.md               # ★ status, bot diagnosis, upgrade plan, decisions
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
    ├── layouts/BaseLayout.astro  # shell: head/meta, theme switch, header/footer
    ├── styles/stichui.css        # global reset, terminal base styles, broadsheet theme block
    ├── components/               # shared components (see §7)
    │   └── broadsheet/           # broadsheet-theme header/footer/seal/section head/motion
    └── pages/                    # routes (see §7)
```

---

## 3. Stack & commands

- **Astro 5** (`output: 'static'`), TypeScript **strict**, **Tailwind 3.4** via `@astrojs/tailwind`,
  `@astrojs/sitemap`, `@astrojs/rss`, `@tailwindcss/typography`, `sharp`, `@vercel/analytics`.
- `lightweight-charts` renders the VN-Index chart (`VnIndexChart.astro`).
- **Python** bots use `vnstock`, `yfinance`, `feedparser`, `requests`+`beautifulsoup4`
  (all optional — code degrades if a lib/source is missing). **`vnstock` is currently not
  installable from PyPI** — see ROADMAP P0.

| Command | Action |
| :-- | :-- |
| `npm install` | Install JS deps |
| `npm run dev` | Dev server → http://localhost:4321 |
| `npm run build` | Production build → `dist/` (must pass with **0 errors**) |
| `npx astro check` | TypeScript / content-schema check (0 errors expected) |
| `pip install -r requirements.txt` | Install bot deps (fails today because of vnstock) |
| `python weekly_bot.py` | Generate the latest Weekly Market View |
| `python monthly_bot.py` | Generate the previous Monthly Market View |

---

## 4. Design system — two themes, migrating to Broadsheet

`BaseLayout` takes `theme?: 'terminal' | 'broadsheet'` (default `terminal`) and sets
`<html data-theme=…>`. **Broadsheet is the chosen direction (Oct 2026); only the homepage uses
it so far.** Next step is rolling it out page by page, then deleting the terminal theme.

### 4a. Broadsheet (new — use for all new work)
Financial-newspaper front page: newsprint paper, ink rules, oxblood accent, a cinnabar seal.

- **Opt in:** `<BaseLayout theme="broadsheet" …>`. This swaps in `components/broadsheet/SiteHeader`
  + `SiteFooter`, loads Fraunces + Geist Mono, adds `<html class="js">`, and mounts
  `broadsheet/Motion` (scroll reveal + count-up).
- **Color tokens** (`tailwind.config.mjs`):
  `paper` #F2E8DA (`paper-deep` #E9DCC7 hover rows, `paper-light`), `ink` #191714
  (`ink-soft` #3D3731 secondary text, `ink-muted` #6B6259 labels/captions),
  `oxblood` #8E1B1B (accent, kickers, **losses**; `oxblood-deep` hover), `ledger` #1E6B52
  (**gains**), `seal` #B8321C (ticker seals only). Hairlines = `border-ink/15–25`; strong rules =
  `border-ink`; double rules = `border-t-4 border-double` or a 5px `border-y` strip.
- **Type:** `font-news` (Fraunces, variable opsz — display, headlines, body) and `font-news-mono`
  (Geist Mono — labels, kickers, data only). Pair with the `text-news-*` scale:
  `masthead, hero, h2, h3, h4, dek, body, small, figure, label, data`.
  Use `lining-nums tabular-nums` on figures.
- **Components:** `Seal` (square cinnabar con dấu; `motion="hover"` stamps on `group-hover`,
  `"load"` stamps on page load), `SectionHead` (double rule + "Section N · Label" + h2, has an
  `aside` slot), `SiteHeader` (wordmark hidden on `/` until the element marked `data-masthead`
  scrolls away), `SiteFooter`, `Motion`.
- **Motion:** `animate-rise` (+ `[animation-delay:…]`) for above-the-fold load stagger,
  `animate-rule` for rules drawing in, `animate-stamp` for seals, `data-reveal` for scroll reveal,
  `data-countup="N"` on figures inside a revealed block. Content is fully visible without JS;
  `prefers-reduced-motion` is respected.
- **CSS** (`stichui.css`, "Broadsheet theme" block): `:where()` resets so headings/p/a inherit and
  never outrank utilities; `.news-link` (ink underline drawing in on hover); paper grain on body.
  Because a global `a:hover` rule exists, **give every link an explicit `hover:text-…` class.**
- **Variants on shared components:** `VnIndexChart theme="broadsheet"` (ink area chart,
  transparent bg), `DisclaimerBox variant="broadsheet"` (ruled disclosure strip).
- **Layout idiom:** columns separated by vertical `border-l/border-r border-ink/25` rules, not
  boxed cards; kickers in mono uppercase oxblood; dotted leaders for data rows
  (`after:border-dotted` on `dt`); one fact box (`border border-ink` + ink header band) per section max.

### 4b. Terminal (legacy — every page except `/`)
Bloomberg-style dark: `terminal-bg` #0d1117, `terminal-card` #161b22, `terminal-border` #30363d,
`terminal-text` #e6edf3, `terminal-muted` #8b949e, `terminal-accent` #f0a500 (amber), plus an
MD3 dark palette (`tertiary` = gains, `error` = losses, `on-surface-variant`/`outline-variant`
muted). JetBrains Mono + Inter, `font-*`/`text-*` token pairs, 2px amber top border on cards.
Letter-spacing is locked to 0 **only** in this theme.

### 4c. Global rules (both themes)
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
`vn_index_daily[]` OHLC (no file has it yet). File date = the Friday.

### `monthly-views`
Same idea with `_monthly_` variants, plus `month_start`, `month_end`, `trading_days`,
`best_sector`/`best_sector_change_pct`, `worst_sector`/`worst_sector_change_pct`.
File date = last trading day of the month.

The weekly bot may emit `foreign_net_estimated` in frontmatter; it's not in the schema and Zod
ignores it — don't rely on it in pages.

State JSON (managed by the bots, never hand-edit except to merge data):
`market-views/_quarterly_summary.json`, `_foreign_flow_cache.json`, `_market_memory.json`;
`monthly-views/_monthly_summary.json`.

---

## 6. The "research" / valuation data layer (`src/data/valuation-models.ts`)

The valuation section is a **typed TypeScript module, not a content collection.**

Exports: `portfolioDisclaimer`, `valuationGroups` (`dcf`, `comparable`, `transaction-lbo`),
`valuationModels` (**5 companies**: `hpg`, `bid`, `fpt`, `bmp`, `pnj`), and types
`ValuationModel`, `ValuationGroup`, `ValuationDownload`, `ValuationNote`, `ReportPoint`,
`ValuationReport`, `ValuationGroupId`, `ProjectStatus`.

Each `ValuationModel` carries `slug`, `ticker`, `company`, `sector`, `status`, `lastUpdated`,
`outputRange`, `investmentQuestion`, `keyAssumptions[]`, `methods[]`, `summary`, `conclusion`,
`valuationNotes[]`, a `report{ headline, stance, thesis[], assumptions[], valuationResult[],
interpretation[], risks[], disclaimer }`, and `downloads[]` (→ `public/research/valuation-models/`).
The homepage coverage table reads `report.valuationResult` entries whose label ends in "output".

**To add/edit a company report, edit this file** — pages and method pages derive from it.
All models are dated 2026-06-11 and carry no current market price yet (see ROADMAP P1).

---

## 7. Pages & components

| Route | File | Theme | Notes |
| :-- | :-- | :-- | :-- |
| `/` | `index.astro` | broadsheet | Masthead, analyst profile + markets box, Profile (`#about`), Coverage (`#valuation`: lead note + table), Market notes (`#market-views`: chart + briefs). |
| `/research` | `research.astro` | terminal | Valuation hub, client-side Company ⇄ Method toggle. |
| `/research/[slug]` | `research/[slug].astro` | terminal | Company report; `getStaticPaths` from `valuationModels`. |
| `/research/dcf`, `/research/comparable-analysis`, `/research/precedent-transactions-lbo` | thin wrappers | terminal | render `<ValuationMethodPage groupId=…/>`. |
| `/market-views`, `/market-views/[slug]` | `market-views/*` | terminal | Combined weekly+monthly list; weekly detail with prev/next links. |
| `/monthly-views`, `/monthly-views/[slug]` | `monthly-views/*` | terminal | Monthly equivalents. |
| `/contact`, `/disclaimer`, `/404` | static | terminal | |
| `/rss.xml` | `rss.xml.js` | — | Weekly + monthly feed. |

Shared components: `ValuationMethodPage`, `ProjectCard`, `DownloadCard`, `AssumptionTable`,
`ValuationSnapshot`, `RiskList`, `StatusBadge`, `DisclaimerBox`, `VnIndexChart`; broadsheet-only
components under `components/broadsheet/` (§4a).

---

## 8. Python bot pipeline

### `weekly_bot.py` — Weekly Market View
VN-Index OHLCV (`vnstock` VCI → `yfinance ^VNINDEX.VN` → deterministic synthetic fallback) →
foreign flow (HSX API → CafeF → sum of daily cache) → sector performance → macro DXY/Gold/WTI/BTC
+ USD/VND (`yfinance`) → news (RSS → CafeF scrape → yfinance) → **LLM #1** writes commentary +
frontmatter → validate → write `market-views/<friday>.md` → **LLM #2** updates
`_quarterly_summary.json` → update `_market_memory.json`.
CLI: `--week YYYY-MM-DD`, `--rebuild-summary Q2-2026`, `--skip-news`, `--skip-summary`,
`--collect-foreign-flow` (cache today's flow only, no LLM), `--deploy`.

### `monthly_bot.py` — Monthly Market View
Writes `monthly-views/<last-trading-day>.md`, updates `_monthly_summary.json`.
CLI: `--month YYYY-MM` (default previous month), `--skip-summary`.

### `market_memory.py`
Shared narrative state linking latest weekly, current monthly, and quarterly summaries.

### Data-quality model
- Foreign flow has **no historical API** → `--collect-foreign-flow` must run **daily**; the cache
  currently prunes to 60 days (older days survive only in git history of the cache file).
- Missing live data is filled with deterministic synthetic values flagged as `estimated_fields`;
  foreign flow is left `null`. Known gaps: the synthetic **VN-Index** flag is never read, and
  synthetic macro numbers render as if real (ROADMAP P0).
- Windows stdout/stderr is reconfigured to UTF-8.

---

## 9. Automation (`.github/workflows/`)

17:00 ICT = 10:00 UTC (GitHub usually starts these hours late). Jobs commit as "Market Bot" with
`git add -A` and `git push`; shared `concurrency: market-bot`; all support `workflow_dispatch`.

| Workflow | Schedule | Does | Status (2026-10-01) |
| :-- | :-- | :-- | :-- |
| `daily_foreign_flow.yml` | `0 10 * * *` | `weekly_bot.py --collect-foreign-flow` → commit cache | ❌ failing since 25 Sep (pip: vnstock) |
| `weekly_market_view.yml` | `0 10 * * 5` | collect flow → `weekly_bot.py` → commit | ❌ every run since 13 Jun (LLM 401), then pip |
| `monthly_market_view.yml` | `0 10 28-31 * *` + ICT month-end guard | collect flow → `monthly_bot.py` → commit | ❌ no monthly since May 2026 |

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

- **Vercel** static hosting (project `portfolio`, team in `.vercel/project.json` on the owner's PC).
  ⚠️ **The Vercel project is not connected to this GitHub repo** — no commit has ever received a
  Vercel status/check, and pushing `master` on 2026-10-01 did not change the live site. Deploys
  so far were made manually with the Vercel CLI from the owner's PC (its CLI token has since
  expired). Until the owner connects the repo in Vercel (Project → Settings → Git, production
  branch `master`), **a push does not deploy**. Domain `truonghuyresearch.xyz` (A → 76.76.21.21);
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
- Cross-asset values may be synthetic fallbacks — don't "correct" the numbers; make prose consistent.

---

## 13. Conventions & gotchas

- `market-views` = weekly, `monthly-views` = monthly; there is no daily collection.
- "Research" = the `valuation-models.ts` module, not a collection.
- CFA wording must follow CFA Institute guidance: **"Passed Level II of the CFA Program"** (or
  "Passed Level II, CFA Program"); never "CFA Level II" as a title, never a CFA-mark-styled badge.
  Only say "Level III Candidate" once the owner confirms registration for the Level III exam.
- `public/cv.pdf` is maintained by the owner outside the repo.
- Line endings: repo stores LF; Windows checkout uses `core.autocrlf=true`.
