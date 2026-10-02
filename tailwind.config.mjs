/** @type {import('tailwindcss').Config} */

// Direction C ("Desk"): dark navy chrome, framed light panels, one colour per section.
// Every colour is a CSS variable (RGB channels) defined in src/styles/global.css for the
// day theme and redefined under [data-theme="dark"] for the night theme, so the same
// utility classes work in both themes and keep Tailwind's /<alpha> modifiers.
const v = (name) => `rgb(var(--c-${name}) / <alpha-value>)`;

export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: ['selector', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        canvas: v('canvas'), // page background: near-white by day, black by night
        panel: { DEFAULT: v('panel'), alt: v('panel-alt') },
        line: { DEFAULT: v('line'), strong: v('line-strong') },
        fg: { DEFAULT: v('fg'), muted: v('fg-muted') },
        link: v('link'),
        up: { DEFAULT: v('up'), soft: v('up-soft') },
        down: { DEFAULT: v('down'), soft: v('down-soft') },
        chrome: { DEFAULT: v('chrome'), deep: v('chrome-deep'), fg: v('chrome-fg'), muted: v('chrome-muted'), line: v('chrome-line') },
        // Section colours: DEFAULT fills panel title bars (white text on top), `ink` is the
        // same hue tuned for text on a panel in the current theme.
        profile: { DEFAULT: v('profile'), ink: v('profile-ink') },
        value: { DEFAULT: v('value'), ink: v('value-ink') },
        market: { DEFAULT: v('market'), ink: v('market-ink') },
        tape: { up: '#5FE0A2', down: '#FF8A8A' }, // on the always-dark market tape
        sun: '#F5B83D',
        moon: '#DCE6F5',
      },
      fontFamily: {
        display: ['"Archivo Variable"', 'Archivo', 'system-ui', 'sans-serif'],
        sans: ['"Source Sans 3 Variable"', '"Source Sans 3"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      fontSize: {
        display: ['clamp(2.25rem, 5vw, 3.5rem)', { lineHeight: '1.04', letterSpacing: '-0.02em', fontWeight: '800' }],
        h1: ['clamp(1.875rem, 3.6vw, 2.625rem)', { lineHeight: '1.1', letterSpacing: '-0.015em', fontWeight: '800' }],
        h2: ['clamp(1.375rem, 2.4vw, 1.75rem)', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '700' }],
        h3: ['1.1875rem', { lineHeight: '1.3', fontWeight: '700' }],
        lead: ['1.1875rem', { lineHeight: '1.55' }],
        body: ['1.0625rem', { lineHeight: '1.65' }],
        small: ['0.9375rem', { lineHeight: '1.55' }],
        label: ['0.75rem', { lineHeight: '1.3', letterSpacing: '0.06em', fontWeight: '600' }],
        data: ['0.9375rem', { lineHeight: '1.35', fontWeight: '500' }],
        figure: ['2.25rem', { lineHeight: '1', letterSpacing: '-0.02em', fontWeight: '700' }],
      },
      spacing: {
        'margin-desktop': '32px',
        'margin-mobile': '16px',
        'container-max': '1240px',
      },
      boxShadow: {
        panel: '0 1px 2px rgb(var(--c-shadow) / 0.06), 0 1px 0 rgb(var(--c-shadow) / 0.04)',
        lift: '0 12px 32px rgb(var(--c-shadow) / 0.18)',
      },
      keyframes: {
        rise: { '0%': { opacity: '0', transform: 'translateY(10px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        'sky-rise': {
          '0%': { opacity: '0', transform: 'translateY(48px) scale(0.85)' },
          '60%': { opacity: '1', transform: 'translateY(-4px) scale(1.02)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'sun-spin': { '0%': { transform: 'rotate(0deg)' }, '100%': { transform: 'rotate(360deg)' } },
        glow: { '0%, 100%': { opacity: '0.55' }, '50%': { opacity: '0.95' } },
        twinkle: { '0%, 100%': { opacity: '0.2' }, '50%': { opacity: '1' } },
        'toast-in': { '0%': { opacity: '0', transform: 'translateY(-8px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
      },
      animation: {
        rise: 'rise 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) both',
        'sky-rise': 'sky-rise 1.1s cubic-bezier(0.2, 0.8, 0.2, 1) both',
        'sun-spin': 'sun-spin 18s linear infinite',
        glow: 'glow 3s ease-in-out infinite',
        twinkle: 'twinkle 2.4s ease-in-out infinite',
        'toast-in': 'toast-in 0.4s cubic-bezier(0.2, 0.8, 0.2, 1) both',
      },
      // Sharp corners — 0px everywhere except full
      borderRadius: {
        none: '0px',
        DEFAULT: '0px',
        sm: '0px',
        md: '0px',
        lg: '0px',
        xl: '0px',
        '2xl': '0px',
        '3xl': '0px',
        full: '9999px',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
