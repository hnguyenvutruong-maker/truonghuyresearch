# Roadmap & handoff

_Status as of 2026-10-01. Keep this file current: tick items, add dates, log decisions._

The owner is continuing on a different machine (possibly via Claude Code cloud sessions).
Everything needed to pick up the work is in this repo: [CLAUDE.md](../CLAUDE.md) for how the
code works, this file for where things stand.

---

## Done on 2026-10-01

- [x] **CFA credential** → "Passed Level II of the CFA Program" on the homepage, JSON-LD
      (`hasCredential`), RSS description, and the weekly bot persona. **`public/cv.pdf` still says
      "Candidate" — the owner must replace the PDF.** Ask whether they registered for Level III
      before ever writing "Level III Candidate".
- [x] **Homepage redesigned in the Broadsheet theme** (merge `259317d`). Theme infrastructure is in
      place (`BaseLayout theme="broadsheet"`, tokens, `components/broadsheet/`); every other page is
      still on the terminal theme.
- [x] Market-view **prose fixes** (sign-consistent wording, measured titles, condensed monthlies)
      and **prev/next navigation** on weekly/monthly detail pages.
- [x] Foreign-flow cache: added 25, 28, 29, 30 Sep 2026, which only the owner's PC had captured
      (CI was down). On the 21 overlapping days the PC and CI values disagree; CI values were kept.
      The PC's original file is backed up locally at `D:\Work\Web\_backup\`.

## Recommended next steps (in order)

1. **Roll the Broadsheet theme out** to `/research`, `/research/[slug]`, the three method pages,
   `/market-views`, `/monthly-views` and their detail pages, `/contact`, `/disclaimer`, `/404`.
   Then delete the terminal tokens, `.stich-*` classes, and the terminal header/footer markup in
   `BaseLayout`, and update CLAUDE.md §4.
2. **Fix the bot pipeline (P0 below)** so content resumes, then backfill.
3. Work through P1 → P3.

---

## P0 — Content bots are down (no new notes since 05 Jun 2026)

Latest weekly: 2026-06-05. Latest monthly: 2026-05-31. Diagnosis from CI logs:

- [ ] **vnstock is not installable from PyPI** (`No matching distribution found for vnstock>=4.0.0`)
      since 2026-09-25, so all three workflows die at `pip install`, including the daily
      foreign-flow collection (and foreign-flow days that aren't collected are lost for good).
      The code already runs without vnstock (`HAS_VNSTOCK`): drop it from `requirements.txt` and
      install it in a separate non-fatal step (or from source).
- [ ] **Weekly LLM call returns HTTP 401** (every Friday since 2026-06-13). No `vars.LLM_BASE_URL` /
      `vars.LLM_MODEL` are set, so CI calls `api.openai.com` with `gpt-5.2`, but `secrets.LLM_API_KEY`
      (set 2026-06-09, when the project moved to Ollama/MiniMax) is probably not an OpenAI key. Set
      the repo variables to match the key's provider, or replace the key. The owner has to do the
      secrets part.
- [ ] **Synthetic VN-Index can be published undisclosed.** `_synthesize_vnindex()` sets
      `_estimated: True`, but nothing reads that flag. Abort the run instead of publishing when the
      index data is synthetic. This matters more now that vnstock is gone.
- [ ] **Synthetic macro (DXY/WTI/Gold/BTC) shows as real** on the cross-asset strip (e.g. WTI
      67→91 in one week). Leave fields `null` and render "—", as is already done for foreign flow.
- [ ] **Cache prunes to 60 days** (`collect_foreign_flow_today`): stop pruning or archive old days.
      Older days can be rebuilt from the git history of `_foreign_flow_cache.json`.
- [ ] **No failure alerting**: 16 weeks of failures went unnoticed. Add an `if: failure()` step that
      opens or updates a GitHub issue.
- [ ] **Workflows use `git add -A`** (that's how vnstock's `AGENTS.md` and `.agents/` got committed)
      and push without rebasing. Add only content paths, and run `git pull --rebase` before
      `git push`. Delete `AGENTS.md` and `.agents/`.
- [ ] vnstock sector API changed: `'function' object has no attribute 'symbols'`.
- [ ] **Backfill** once fixed: weekly 2026-06-12 → latest Friday (`--week`), monthly Jun–Sep 2026
      (`--month`). Foreign flow is only available for days in the cache.

---

## P1 — Visible impact and research credibility

- [x] Homepage redesign (Broadsheet) with hierarchy, motion, and a real section structure
- [ ] Broadsheet on every page (see "Recommended next steps")
- [ ] Valuation: add `currentPrice`, `priceDate`, implied upside/downside per model; show staleness
      (all models are dated 2026-06-11)
- [ ] **Football-field chart** per company (method ranges vs current price), inline SVG
- [ ] Remove the visible placeholders on report pages: HPG "Sensitivity Needed — Placeholder"
      boxes (`research/[slug].astro`) and BID's "Metrics needed" list. Build the WACC × exit-multiple
      table from the workbook, or hide the sections
- [ ] Unify weekly title format (currently three styles); the bot prompt should enforce one
- [ ] Coverage table on `/research` that can be sorted

## P2 — UX and navigation

- [ ] Command palette (`Ctrl+K` / `/`): jump to tickers, method pages, notes, CV
- [ ] `/market-views`: Weekly/Monthly filter tabs, group by year (it'll pass 50 entries a year)
- [ ] Note detail pages: H1 above the data card, per-page meta descriptions, sticky TOC, reading
      progress bar
- [ ] Report pages: section TOC, sensitivity heatmap
- [ ] `/research` tabs: `role="tab"`, keyboard support, state kept in the URL hash
- [ ] Mobile menu closes on link click or Esc (terminal header; the broadsheet header needs the same)
- [ ] Replace the "tracking from Jun 2026" label shown when foreign flow is missing

## P3 — Technical, SEO, polish

- [ ] Dynamic OG images per note and report (build-time, satori)
- [ ] `vercel.json`: security headers (CSP, `X-Content-Type-Options`, `Referrer-Policy`) and a
      `www` → apex redirect
- [ ] Load `lightweight-charts` (~160 KB) lazily when the chart scrolls into view
- [ ] Refactor: shared `src/lib/format.ts` (date and number formatters are duplicated in 5+ files),
      merge the near-identical weekly and monthly `[slug]` pages, drop the hard-coded `'2026-06-11'`
      fallbacks
- [ ] JSON-LD for report pages, RSS with full content
- [ ] One-page PDF per company; convert `.xls` to `.xlsx`; show file sizes on download cards
- [ ] Contact page: phone number is public; page title still says "NVTH Capital Markets"
- [ ] Lighthouse and a11y pass at 375px

---

## Decisions log

- **2026-10-01 — Design direction: Broadsheet.** Four directions were mocked up: A Broadsheet
  (paper and ink, Fraunces + Geist Mono), B Sơn mài (Vietnamese lacquer), C Swiss poster,
  D Blueprint. The owner picked **A**; its cinnabar ticker seal (borrowed from B) is the
  signature accent. B was built on branch `redesign/son-mai` and is kept for reference only.
- **2026-10-01 — CFA wording** follows CFA Institute guidance ("Passed Level II of the CFA Program").
- **2026-10-01 — Foreign-flow merge:** CI values win where the PC and CI disagree.
