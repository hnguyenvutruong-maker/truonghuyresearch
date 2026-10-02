// Build-time Open Graph cards (1200×630 PNG) for every report and market note:
// satori lays out a framed panel in SVG with the real fonts, sharp rasterises it.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { APIRoute, GetStaticPaths } from 'astro';
import { getCollection } from 'astro:content';
import satori from 'satori';
import sharp from 'sharp';
import { formatOutput, outputMethodLabel, valuationModels } from '../../data/valuation-models';
import { formatDate, formatIndex, formatVndK, signedNumber, signedPct } from '../../lib/format';
import { monthlySummary, weeklySummary, type NoteSummary } from '../../lib/notes';

type Node = { type: string; props: Record<string, unknown> };
type Child = Node | string | null | false;
const h = (type: string, style: Record<string, unknown>, ...children: Child[]): Node => ({
  type,
  props: { style: { display: 'flex', ...style }, children: children.filter((child): child is Node | string => Boolean(child)) },
});

// Direction C palette (day theme): navy chrome band, white panel, one colour per section
const C = { chrome: '#0B1B33', chromeFg: '#F2F5F9', chromeMuted: '#9FB0C3', canvas: '#F6F8FB', panel: '#FFFFFF', line: '#C9D2DC', fg: '#101A2B', muted: '#4A596B', up: '#0E6B34', down: '#BE261A', value: '#086F76', market: '#9A4F04', teal: '#57D6C8' };
const font = (pkg: string, file: string) => readFileSync(join(process.cwd(), 'node_modules', pkg, 'files', file));
const fonts = [
  { name: 'Archivo', data: font('@fontsource/archivo', 'archivo-latin-800-normal.woff'), weight: 800 as const, style: 'normal' as const },
  { name: 'Archivo', data: font('@fontsource/archivo', 'archivo-latin-700-normal.woff'), weight: 700 as const, style: 'normal' as const },
  { name: 'IBM Plex Mono', data: font('@fontsource/ibm-plex-mono', 'ibm-plex-mono-latin-600-normal.woff'), weight: 600 as const, style: 'normal' as const },
];

type Card = { kicker: string; context: string; headline: string; figures: Array<{ label: string; value: string; tone?: string }>; ticker?: string; accent: string };

const label = (text: string, color = C.muted, size = 20) =>
  h('div', { fontFamily: 'IBM Plex Mono', fontWeight: 600, fontSize: size, letterSpacing: 1.6, textTransform: 'uppercase', color }, text);

const layout = (card: Card): Node =>
  h(
    'div',
    { width: 1200, height: 630, flexDirection: 'column', backgroundColor: C.canvas, color: C.fg },
    h(
      'div',
      { height: 92, padding: '0 56px', backgroundColor: C.chrome, justifyContent: 'space-between', alignItems: 'center' },
      h('div', { fontFamily: 'Archivo', fontWeight: 800, fontSize: 34, color: C.chromeFg }, 'Truong Huy', h('span', { color: C.teal, marginLeft: 10 }, 'Research')),
      label(card.context, C.chromeMuted)
    ),
    h(
      'div',
      { flexGrow: 1, margin: '32px 56px', flexDirection: 'column', backgroundColor: C.panel, border: `2px solid ${C.line}` },
      h('div', { height: 52, padding: '0 28px', backgroundColor: card.accent, alignItems: 'center' }, label(card.kicker, '#FFFFFF')),
      h(
        'div',
        { flexGrow: 1, padding: '0 28px', alignItems: 'center' },
        card.ticker
          ? h(
              'div',
              { marginRight: 28, padding: '10px 16px', backgroundColor: C.value, color: '#FFFFFF', fontFamily: 'IBM Plex Mono', fontWeight: 600, fontSize: 30 },
              card.ticker
            )
          : null,
        h(
          'div',
          { flexShrink: 1, fontFamily: 'Archivo', fontWeight: 800, fontSize: card.headline.length > 80 ? 44 : card.headline.length > 50 ? 54 : 66, lineHeight: 1.08, letterSpacing: -1.2 },
          card.headline
        )
      ),
      h(
        'div',
        { borderTop: `2px solid ${C.line}`, padding: '18px 28px', justifyContent: 'space-between', alignItems: 'flex-end' },
        h(
          'div',
          { gap: 44 },
          ...card.figures.map((figure) =>
            h('div', { flexDirection: 'column' }, label(figure.label, C.muted, 17), h('div', { fontFamily: 'IBM Plex Mono', fontWeight: 600, fontSize: 34, marginTop: 6, color: figure.tone ?? C.fg }, figure.value))
          )
        ),
        label('truonghuyresearch.xyz', C.muted, 17)
      )
    )
  );

const tone = (value: number | null) => (value == null ? C.muted : value >= 0 ? C.up : C.down);

const noteCard = (note: NoteSummary): Card => ({
  kicker: `${note.kind} market view`,
  context: note.period,
  headline: note.headline,
  accent: C.market,
  figures: [
    { label: 'VN-Index', value: formatIndex(note.close) },
    { label: note.kind === 'Weekly' ? 'Week' : 'Month', value: signedPct(note.change), tone: tone(note.change) },
    ...(note.foreignNet != null ? [{ label: 'Foreign net, bn', value: signedNumber(note.foreignNet), tone: tone(note.foreignNet) }] : []),
  ],
});

export const getStaticPaths = (async () => {
  const weekly = (await getCollection('market-views')).map(weeklySummary);
  const monthly = (await getCollection('monthly-views')).map(monthlySummary);
  return [
    ...valuationModels.map((model) => ({
      params: { path: `research/${model.slug}` },
      props: {
        card: {
          kicker: `Valuation report · ${model.sector}`,
          context: `Model ${formatDate(model.lastUpdated ?? model.referencePrice.asOf)}`,
          headline: model.company,
          ticker: model.ticker,
          accent: C.value,
          figures: [
            ...model.outputs.slice(0, 3).map((output) => ({ label: outputMethodLabel[output.method], value: formatOutput(output).replace('≈', '~') })),
            { label: 'Price used', value: formatVndK(model.referencePrice.value), tone: C.muted },
          ],
        } satisfies Card,
      },
    })),
    ...[...weekly, ...monthly].map((note) => ({ params: { path: note.href.slice(1) }, props: { card: noteCard(note) } })),
  ];
}) satisfies GetStaticPaths;

export const GET: APIRoute = async ({ props }) => {
  const svg = await satori(layout((props as { card: Card }).card) as unknown as Parameters<typeof satori>[0], { width: 1200, height: 630, fonts });
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return new Response(new Uint8Array(png), { headers: { 'Content-Type': 'image/png' } });
};
