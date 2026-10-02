# Roadmap & handoff

_Status as of 2026-10-02. Keep this file current: tick items, add dates, log decisions._

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

## Deployment

- [x] **2026-10-02:** the owner connected Vercel project `portfolio` to
      `hnguyenvutruong-maker/truonghuyresearch`. Pushes to `master` now deploy production.
      Before that, the live site had stayed on the old version even after the 2026-10-01 merge,
      because deploys were manual Vercel CLI runs from the owner's PC.

## Recommended next steps (in order)

1. ~~Roll the Broadsheet theme out~~ — done 2026-10-02; the terminal theme is deleted.
2. **Finish P0**: the owner fixes the LLM key/vars, merges the bot fixes to `master`, then backfills.
3. **Refresh the valuation models** (P1 leftover): new prices and estimates, then update
   `referencePrice`, `outputs` and `sensitivity` in `valuation-models.ts`.
4. Work through what is left of P2 → P3.

---

## P0 — Content bots are down (no new notes since 05 Jun 2026)

Latest weekly: 2026-06-05. Latest monthly: 2026-05-31. Diagnosis from CI logs; code fixes landed
2026-10-02 (branch `claude/busy-einstein-75w6kn`) and take effect once merged to `master`, because
scheduled workflows run from the default branch.

- [x] **vnstock is not installable from PyPI** — its PyPI project is **quarantined**, not just
      yanked, so it was removed rather than installed from another source. VN-Index now comes from
      `vn_market_data.py` (VNDirect dchart API → yfinance `^VNINDEX.VN`). ⚠️ Neither source could be
      tested from the cloud sandbox (Yahoo and Vietnamese hosts are blocked there); the first CI run
      confirms which one works. If both fail, the run aborts and opens an issue — nothing fake is
      published.
- [ ] **Weekly LLM call returns HTTP 401** (every Friday since 2026-06-13). Confirmed from the
      2026-09-18 log: OpenAI rejects the key ("Incorrect API key provided"); it is not an OpenAI key.
      **Owner action:** either set repo variables `LLM_BASE_URL` / `LLM_MODEL` to the provider the
      key belongs to, or replace `secrets.LLM_API_KEY` with a key for the configured provider.
- [x] **Synthetic VN-Index can be published undisclosed** → the synthesizer is gone; no index data
      (or no liquidity) = exit 1 before any file is written.
- [x] **Synthetic macro (DXY/WTI/Gold/BTC) shows as real** → macro and sectors stay `null` ("—" on
      the site). Also fixed: the "weekly" macro change was a one-day change (Thu→Fri); it is now vs
      the prior week's close (monthly: vs prior month-end).
- [x] **LLM can drift frontmatter numbers** → measured values are written over the LLM's
      frontmatter after generation (`enforce_frontmatter`), with no thousands separators.
- [x] **Cache prunes to 60 days** → pruning removed; 29 days (15 Jun–24 Jul) restored from the
      cache file's git history. Cache now covers 2026-06-15 → 2026-09-30 (with gaps where CI failed).
- [x] **No failure alerting** → each workflow opens or comments on an issue
      `Market bot failing: <workflow>` when a run fails.
- [x] **Workflows use `git add -A`** → stage only `src/content/market-views` / `monthly-views`,
      check out the branch tip, `git pull --rebase` before push. `AGENTS.md` and `.agents/` deleted.
      `weekly_bot.py --deploy` narrowed the same way.
- [x] vnstock sector API changed → vnstock path removed; sectors use yfinance leading-stock proxies
      (worked in CI on 2026-09-18: 9 sectors).
- [x] Monthly bot only summed foreign flow on the vnstock path → now always summed from the cache.
- [ ] **Backfill** once the LLM key works: Actions → *Weekly Market View* → Run workflow with
      `week` = each Friday 2026-06-12 → latest; *Monthly Market View* with `month` = 2026-06 …
      2026-09. Foreign flow exists only for cached days (none before 15 Jun). Liquidity for old
      periods uses today's CafeF average share price, so it is approximate.

## P1 — Visible impact and research credibility

- [x] Homepage redesign (Broadsheet) with hierarchy, motion, and a real section structure
- [x] Broadsheet on every page (2026-10-02); terminal tokens, CSS, header/footer and six unused
      components deleted
- [x] Valuation: `referencePrice` (the price each workbook used, 11 Jun 2026), implied move per
      method, and a "Dated figures" note on stale models. ⚠️ These are **model-date prices, not
      live prices** — no live price feed was available. Refreshing the models is the real fix.
- [x] **Football-field chart** per company (method ranges vs the reference price), inline SVG
- [x] Placeholders removed. HPG and FPT get a real WACC × exit-multiple table, recomputed from
      the DCF workbooks (centre cell = model output to the dong); BID's "metrics needed" chips
      are gone (the limitation note already lists them)
- [ ] Unify weekly title format (currently three styles); the bot prompt should enforce one —
      deferred with the bot work
- [x] Sortable coverage table on `/research` (price used, each method, low/high implied move)

## P2 — UX and navigation

- [ ] Command palette (`Ctrl+K` / `/`): jump to tickers, method pages, notes, CV
- [x] `/market-views`: All/Weekly/Monthly filter (synced to `?kind=`), grouped by year
- [x] Note detail pages: H1 above the data card, per-page meta descriptions, sticky TOC
- [ ] Note detail pages: reading progress bar
- [x] Report pages: section index, sensitivity table (HPG, FPT)
- [x] ~~`/research` tabs~~ — replaced by one page (table + methods index); no tabs left
- [x] Mobile menu closes on link click or Esc
- [x] Missing foreign flow now reads "not collected for this week/month"

## P3 — Technical, SEO, polish

- [ ] Dynamic OG images per note and report (build-time, satori)
- [ ] `vercel.json`: security headers (CSP, `X-Content-Type-Options`, `Referrer-Policy`) and a
      `www` → apex redirect
- [ ] Load `lightweight-charts` (~160 KB) lazily when the chart scrolls into view
- [x] Refactor: shared `src/lib/format.ts` + `src/lib/notes.ts`; weekly and monthly detail pages
      share `broadsheet/MarketNote`; hard-coded `'2026-06-11'` fallbacks gone
- [x] JSON-LD for report pages
- [ ] RSS with full content
- [ ] One-page PDF per company; convert `.xls` to `.xlsx`; show file sizes on download cards
- [x] Contact page title fixed
- [ ] Contact page: phone number is public — owner to decide whether to keep it
- [ ] Lighthouse and a11y pass at 375px

---

## Decisions log

- **2026-10-01 — Design direction: Broadsheet.** Four directions were mocked up: A Broadsheet
  (paper and ink, Fraunces + Geist Mono), B Sơn mài (Vietnamese lacquer), C Swiss poster,
  D Blueprint. The owner picked **A**; its cinnabar ticker seal (borrowed from B) is the
  signature accent. B was built on branch `redesign/son-mai` and is kept for reference only.
- **2026-10-01 — CFA wording** follows CFA Institute guidance ("Passed Level II of the CFA Program").
- **2026-10-01 — Foreign-flow merge:** CI values win where the PC and CI disagree.
- **2026-10-02 — Valuation prices:** pages compare against each workbook's own market-input
  price (11 Jun 2026), labelled as such, rather than a live price; no live feed is available and
  inventing one is not an option. Methods are never blended into a single target.
- **2026-10-02 — Weekly macro changes:** notes before Oct 2026 may show one-day moves as
  "weekly"; the note pages say so instead of rewriting stored figures.
