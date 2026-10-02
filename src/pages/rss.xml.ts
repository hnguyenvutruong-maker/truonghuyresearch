import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { getCollection } from 'astro:content';
import MarkdownIt from 'markdown-it';
import sanitizeHtml from 'sanitize-html';
import { formatIndex, signedPct } from '../lib/format';
import { monthlySummary, weeklySummary } from '../lib/notes';

const parser = new MarkdownIt();

// Full note bodies, rendered from markdown and sanitised (tables kept), so feed readers show the whole note.
const render = (markdown: string) =>
  sanitizeHtml(parser.render(markdown), { allowedTags: sanitizeHtml.defaults.allowedTags.concat(['img']) });

export async function GET(context: APIContext) {
  const weekly = await getCollection('market-views');
  const monthly = await getCollection('monthly-views');

  const items = [
    ...weekly.map((entry) => ({ entry, note: weeklySummary(entry) })),
    ...monthly.map((entry) => ({ entry, note: monthlySummary(entry) })),
  ]
    .sort((a, b) => b.note.date.valueOf() - a.note.date.valueOf())
    .map(({ entry, note }) => ({
      title: entry.data.title,
      pubDate: note.date,
      link: `${note.href}/`,
      categories: [note.kind === 'Weekly' ? 'Weekly market view' : 'Monthly market view'],
      description: `${note.kind} VN-Index note for ${note.period}. Close ${formatIndex(note.close)} (${signedPct(note.change)}).`,
      content: render(entry.body),
    }));

  return rss({
    title: 'Truong Huy Research — Market Views',
    description: 'Weekly and monthly Vietnam equity market notes by Nguyen Vu Truong Huy.',
    site: context.site ?? 'https://truonghuyresearch.xyz',
    items,
    customData: '<language>en</language>',
  });
}
