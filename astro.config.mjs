// @ts-check
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({
  site: 'https://truonghuyresearch.xyz',
  output: 'static',
  integrations: [tailwind(), sitemap()],
  // Emit every script and stylesheet as a file under /_astro/ instead of inlining small ones,
  // so the Content-Security-Policy in vercel.json can stay 'self'-only (see the one hashed
  // inline script in BaseLayout).
  build: { inlineStylesheets: 'never' },
  vite: { build: { assetsInlineLimit: 0 } },
});
