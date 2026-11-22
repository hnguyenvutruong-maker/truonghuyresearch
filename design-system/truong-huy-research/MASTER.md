# Design System (Master): Fey × Mercury × Koyfin Financial UI & `transitions.dev` Motion

The source of truth for the visual and interaction architecture of **Truong Huy Research** (`truonghuyresearch.xyz`).

## 1. Benchmarks & Skills Applied

1. **Fey (`fey.com`) & Koyfin (`DIXI 10 Rules`):**
   - **Obsidian Dark Mode Default (`html[data-theme="dark"]`):** Deep obsidian canvas (`#070A10`), glass-lit elevated bento surfaces (`#0F1522` with `inset 0 1px 0 rgba(255, 255, 255, 0.07)` top inner rim light and `1px solid rgba(255, 255, 255, 0.09)` borders), radial ambient sapphire glow behind the hero stage, and luminous signal colors (`#10B981` emerald gain, `#F43F5E` rose loss, `#F59E0B` amber reference marker).
2. **Mercury (`mercury.com` / `getdesign.md/mercury`):**
   - **Mercury Daylight Mode (`html[data-theme="light"]`):** Instant theme switcher in the floating glass navbar (`startViewTransition` theme morphing) switching to `#F5F7FB` cool alabaster canvas and `#FFFFFF` cards with multi-layered material shadows.
   - **Floating Pill Navigation & Tactile Controls:** Pill-shaped navigation track (`.nav__links`), electric cobalt primary action pill (`#3B6BFF`), and tactile press scaling (`scale(0.975)`).
3. **`transitions.dev` (`Jakubantalik/transitions.dev`) Motion Architecture:**
   - **Motion Tokens:** `--duration-stagger: 45ms`, `--duration-micro: 90ms`, `--duration-quick: 160ms`, `--duration-fast: 250ms`, `--duration-medium: 340ms`, `--duration-slow: 440ms`, `--ease-smooth-out: cubic-bezier(0.22, 1, 0.36, 1)`, `--ease-spring: cubic-bezier(0.34, 1.36, 0.64, 1)`.
   - **Cross-Document View Transitions (`@view-transition { navigation: auto; }`):** Smooth cross-blur + vertical glide (`::view-transition-old(page-stage)` / `::view-transition-new(page-stage)`) across page navigations, paired with hover link prefetching and a top route progress indicator.
   - **Cross-Blur Panel Morphing (`.panel-stack > .panel-item`, `07-panel-reveal`):** Tabbed views (Home Company Valuation Desk, HOSE Foreign Flow windows, Macro Thesis tabs) overlap in a CSS grid stack and cross-blur smoothly (`opacity`, `filter: blur(4px)`, `translateY(8px)`) with animated SVG bar scaling instead of harsh `display: none` snapping.
   - **Staggered Scroll-Reveal (`[data-reveal]`, `18-texts-reveal`):** Cards, charts, and sections glide into focus via `IntersectionObserver`.
4. **`unslop-ui` (`felipebasurto/unslop-ui`) Anti-Slop Discipline:**
   - Zero decorative `01 ·`, `02 ·` section numbering (Rule U2).
   - Zero redundant stacked uppercase eyebrows over every heading and card (Rule U1).
   - Zero botsplaining or reading instructions ("Hover or click any cell...", Rule U4/U13).
   - Zero fake pulsing "LIVE" dots (Rule U10) or heavy `2px` black top bars on every card (Rule U15).
