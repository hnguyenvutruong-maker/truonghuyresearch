/** @type {import('tailwindcss').Config} */

// "Ledger" (2026-11): Tailwind is the layout layer only. Colours, type and radii point at the
// tokens in src/styles/global.css, so a utility and a component class can never disagree.
// Light grade only (Taste: dark pages are for tech sites), so there is no dark variant.
const v = (name) => `var(--${name})`;

export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        ground: { DEFAULT: v('g-main'), alt: v('g-alt'), card: v('g-card'), dark: v('g-dark') },
        ink: { DEFAULT: v('ink'), muted: v('muted') },
        line: { DEFAULT: v('line'), strong: v('line-strong') },
        action: { DEFAULT: v('action'), hover: v('action-hover') },
        amber: { DEFAULT: v('amber'), soft: v('amber-soft') },
        up: { DEFAULT: v('up'), soft: v('up-soft'), mid: v('up-mid') },
        down: { DEFAULT: v('down'), soft: v('down-soft'), mid: v('down-mid') },
        dark: { ink: v('dark-ink'), muted: v('dark-muted'), line: v('dark-line') },
      },
      fontFamily: {
        display: ['"Source Serif 4 Variable"', '"Source Serif 4"', 'Georgia', 'serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      maxWidth: { wrap: '1280px', measure: '62ch' },
      borderRadius: { none: '0px', sm: '4px', DEFAULT: '4px', md: '6px', lg: '8px', full: '9999px' },
    },
  },
  plugins: [],
};
