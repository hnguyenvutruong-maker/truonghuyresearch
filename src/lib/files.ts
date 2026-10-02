// Build-time facts about files shipped from public/ (e.g. model downloads).
import { statSync } from 'node:fs';
import { join } from 'node:path';

/** Human-readable size of a public/ file by its site path ("/research/…xlsx" → "86 KB"); null if missing. */
export const publicFileSize = (href: string): string | null => {
  try {
    const bytes = statSync(join(process.cwd(), 'public', href)).size;
    if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  } catch {
    return null;
  }
};
