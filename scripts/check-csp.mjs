// Fails the build when an inline <script> in dist/ is not allowed by the CSP in vercel.json.
// The production CSP has no 'unsafe-inline', so an unlisted inline script would be blocked
// by browsers silently (e.g. the theme picker would stop working).
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const root = join(process.cwd(), 'dist');
const csp = JSON.parse(readFileSync('vercel.json', 'utf8'))
  .headers.flatMap((rule) => rule.headers)
  .find((header) => header.key === 'Content-Security-Policy').value;

const files = [];
const walk = (dir) => {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) walk(path);
    else if (entry.name.endsWith('.html')) files.push(path);
  }
};
walk(root);

const missing = new Map();
for (const file of files) {
  const html = readFileSync(file, 'utf8');
  for (const match of html.matchAll(/<script(?![^>]*\bsrc=)([^>]*)>([\s\S]*?)<\/script>/g)) {
    if (/type="application\/(ld\+)?json"/.test(match[1])) continue; // data blocks are not executed
    const hash = `'sha256-${createHash('sha256').update(match[2]).digest('base64')}'`;
    if (!csp.includes(hash)) missing.set(hash, file.replace(root, ''));
  }
}

if (missing.size > 0) {
  for (const [hash, file] of missing) console.error(`CSP: inline script in ${file} needs ${hash} in vercel.json script-src`);
  process.exit(1);
}
console.log(`CSP: ${files.length} pages checked, every inline script is allowed.`);
