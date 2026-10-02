/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        // Broadsheet palette
        'paper': {
          DEFAULT: '#F2E8DA',
          deep: '#E9DCC7',
          light: '#F8F2E8',
        },
        'ink': {
          DEFAULT: '#191714',
          soft: '#3D3731',
          muted: '#6B6259',
        },
        'oxblood': {
          DEFAULT: '#8E1B1B',
          deep: '#6E1414',
        },
        'ledger': '#1E6B52',
        'seal': '#B8321C',
      },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        // Seal pressed onto the page; ends on the seal's resting -5deg tilt
        stamp: {
          '0%': { opacity: '0', transform: 'scale(1.4) rotate(-16deg)' },
          '55%': { opacity: '1', transform: 'scale(0.92) rotate(-3deg)' },
          '100%': { opacity: '1', transform: 'scale(1) rotate(-5deg)' },
        },
        // Printed rule drawn outward from the centre
        rule: {
          '0%': { transform: 'scaleX(0)' },
          '100%': { transform: 'scaleX(1)' },
        },
      },
      animation: {
        rise: 'rise 0.9s cubic-bezier(0.2, 0.8, 0.2, 1) both',
        stamp: 'stamp 0.55s cubic-bezier(0.2, 0.8, 0.2, 1) both',
        rule: 'rule 1.1s cubic-bezier(0.65, 0, 0.35, 1) both',
      },
      // Sharp corners — 0px everywhere except full
      borderRadius: {
        'none': '0px',
        DEFAULT: '0px',
        'sm': '0px',
        'md': '0px',
        'lg': '0px',
        'xl': '0px',
        '2xl': '0px',
        '3xl': '0px',
        'full': '9999px',
      },
      spacing: {
        'margin-desktop': '40px',
        'margin-mobile': '16px',
        'container-max': '1200px',
      },
      fontFamily: {
        'news': ['"Fraunces Variable"', 'Fraunces', 'Georgia', 'serif'],
        'news-mono': ['"Geist Mono"', 'ui-monospace', 'monospace'],
      },
      fontSize: {
        'news-masthead': ['clamp(3rem, 10.5vw, 8.5rem)', { lineHeight: '0.9', letterSpacing: '-0.035em', fontWeight: '600' }],
        'news-hero': ['clamp(2.75rem, 6.5vw, 5.25rem)', { lineHeight: '0.98', letterSpacing: '-0.025em', fontWeight: '600' }],
        'news-h2': ['clamp(2.25rem, 4.5vw, 3.5rem)', { lineHeight: '1', letterSpacing: '-0.02em', fontWeight: '600' }],
        'news-h3': ['clamp(1.5rem, 2.6vw, 2.125rem)', { lineHeight: '1.12', letterSpacing: '-0.015em', fontWeight: '600' }],
        'news-h4': ['1.3125rem', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '600' }],
        'news-dek': ['1.25rem', { lineHeight: '1.5', fontWeight: '400' }],
        'news-body': ['1.0625rem', { lineHeight: '1.7', fontWeight: '400' }],
        'news-small': ['0.9375rem', { lineHeight: '1.6', fontWeight: '400' }],
        'news-figure': ['2.75rem', { lineHeight: '1', letterSpacing: '-0.02em', fontWeight: '400' }],
        'news-label': ['0.6875rem', { lineHeight: '1.35', letterSpacing: '0.12em', fontWeight: '500' }],
        'news-data': ['0.8125rem', { lineHeight: '1.4', fontWeight: '400' }],
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
};
