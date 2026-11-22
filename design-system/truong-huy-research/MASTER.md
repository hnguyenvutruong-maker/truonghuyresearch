# Truong Huy Research — Design System Master (`@once-ui-system/magic-portfolio` v2.3.0)

## 1. Aesthetic & Architecture
- **Reference Benchmark**: [`once-ui-system/magic-portfolio`](https://github.com/once-ui-system/magic-portfolio) built on `@once-ui-system/core` v2.1.0 OKLCH tokens (`src/styles/once-ui-tokens.css` & `src/styles/site.css`).
- **Root Configuration (`<html>`)**:
  - `data-theme="dark"` (default) | `data-theme="light"` (toggleable via View Transitions)
  - `data-neutral="gray"` (`oklch(0.1448 0 0)` `#0a0a0a` page canvas in dark mode)
  - `data-brand="cyan"`
  - `data-accent="red"`
  - `data-solid="contrast"`
  - `data-solid-style="flat"`
  - `data-border="playful"`
  - `data-surface="translucent"` (`backdrop-filter: blur(1rem)`)
  - `data-transition="all"`
  - `data-scaling="100"`
- **Typography**:
  - `--font-heading`, `--font-body`, `--font-label`: **Geist Sans** (`@fontsource/geist-sans`)
  - `--font-code`: **Geist Mono** (`@fontsource/geist-mono`) with `font-variant-numeric: tabular-nums`

## 2. Signature Once UI Magic Portfolio Components
1. **Ambient `<Background>` & `<Fade>` (`BaseLayout.astro`)**:
   - Top & bottom fixed `<Fade>` edge blur masks (`backdrop-filter: blur(0.5rem)`).
   - Full-viewport radial-masked `<Background>` combining a top-centered cyan radial glow (`.once-bg-gradient`) and a 16px brand dot matrix (`.once-bg-dots`, `opacity: 0.42`).
2. **Floating Dock `<Header>` (`SiteHeader.astro`)**:
   - Left: `Asia/Ho_Chi_Minh` location indicator.
   - Center: Translucent pill dock (`.once-dock`) with icon+label `ToggleButton`s (`Home`, `About`, `Work`, `Blog`, `Models`), vertical dividers (`.once-dock-divider`), `⌘K` Command Search trigger, and `ThemeToggle`.
   - Right: Live ticking 24-hour clock (`[data-once-clock]`) in `Asia/Ho_Chi_Minh`.
   - Mobile (`max-width: 768px`): Dock floats at the bottom above the home indicator.
3. **Centered Display Hero & Shimmer `<Badge>` (`index.astro`)**:
   - Continuous diagonal shimmer `<Badge>` (`onceShineDefault` / `onceShineHover`).
   - `display-strong-l` (`4rem`) balanced headline + `heading-default-xl` (`1.5rem`) subline.
   - Rounded pill `<Button id="about">` with embedded circular `<Avatar>` (`TH`) and animated right arrow (`→`).
4. **Interactive Multi-Slide `<ProjectCard>` (`index.astro`, `research.astro`)**:
   - Cross-blur `<Carousel>` (`[data-once-carousel]`) with 2px horizontal line indicators (`.once-carousel-indicators`) and a 5:7 split row below (`flex: 5` title, `flex: 7` tags + summary + `SmartLink` actions).
5. **Offset `<Line>` Blog Split & `<Newsletter>` Surface (`index.astro`, `market-views/index.astro`)**:
   - 1:3 split section framed by offset horizontal `<Line>` dividers, pairing `"Latest from the blog"` with a 2-column grid of `<Post>` cards (with author `<Avatar size="s">` + date + title + tag).
   - Masked `<Newsletter>` callout surface with internal radial gradient + dot matrix.
6. **Sticky Avatar & Fixed Left `<TableOfContents>` About Page (`contact.astro`)**:
   - Fixed left `<TableOfContents>` with 16px horizontal dash indicators that slide right on hover.
   - Sticky left column with `160px` circular `<Avatar size="xl">`, timezone globe row, and language/CFA tags; right column with schedule pill, `display-strong-xl` name, social buttons, and structured experience/studies/technical sections.
