// Export every /research/<slug>/tear-sheet page from dist/ to public/research/tear-sheets/<slug>.pdf.
// Usage: npm run tear-sheets   (builds first). Uses installed Google Chrome by default;
// set CHROME_PATH to use another Chromium binary.
import { chromium } from 'playwright-core';
import { createServer } from 'node:http';
import { createReadStream, existsSync, mkdirSync, readdirSync, statSync } from 'node:fs';
import { extname, join } from 'node:path';

const root = join(process.cwd(), 'dist');
const out = join(process.cwd(), 'public', 'research', 'tear-sheets');
const types = { '.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2', '.woff': 'font/woff', '.svg': 'image/svg+xml', '.png': 'image/png' };

const slugs = readdirSync(join(root, 'research')).filter((name) => existsSync(join(root, 'research', name, 'tear-sheet', 'index.html')));
if (slugs.length === 0) throw new Error('No tear sheets in dist/ — run `npm run build` first.');

const server = createServer((req, res) => {
  let file = join(root, decodeURIComponent((req.url ?? '/').split('?')[0]));
  if (existsSync(file) && statSync(file).isDirectory()) file = join(file, 'index.html');
  if (!existsSync(file)) return res.writeHead(404).end();
  res.writeHead(200, { 'content-type': types[extname(file)] ?? 'application/octet-stream' });
  createReadStream(file).pipe(res);
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: 'chrome' });
const page = await browser.newPage();
mkdirSync(out, { recursive: true });
for (const slug of slugs) {
  await page.goto(`http://localhost:${port}/research/${slug}/tear-sheet/`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: join(out, `${slug}.pdf`), format: 'A4', printBackground: true, preferCSSPageSize: true });
  console.log(`tear sheet → public/research/tear-sheets/${slug}.pdf`);
}
await browser.close();
server.close();
