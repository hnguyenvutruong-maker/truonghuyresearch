// Build-time Open Graph cards (1200×630 PNG) for every report and market note:
// satori lays out a broadsheet front in SVG with the real fonts, sharp rasterises it.
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

const C = { paper: '#F2E8DA', ink: '#191714', soft: '#3D3731', muted: '#6B6259', oxblood: '#8E1B1B', ledger: '#1E6B52', seal: '#B8321C' };
const font = (pkg: string, file: string) => readFileSync(join(process.cwd(), 'node_modules', pkg, 'files', file));
const fonts = [
  { name: 'Fraunces', data: font('@fontsource/fraunces', 'fraunces-latin-600-normal.woff'), weight: 600 as const, style: 'normal' as const },
  { name: 'Fraunces', data: font('@fontsource/fraunces', 'fraunces-latin-400-italic.woff'), weight: 400 as const, style: 'italic' as const },
  { name: 'Geist Mono', data: font('@fontsource/geist-mono', 'geist-mono-latin-500-normal.woff'), weight: 500 as const, style: 'normal' as const },
];

type Card = { kicker: string; context: string; headline: string; figures: Array<{ label: string; value: string; tone?: string }>; seal?: string };

const label = (text: string, color = C.muted) =>
  h('div', { fontFamily: 'Geist Mono', fontSize: 20, letterSpacing: 2.4, textTransform: 'uppercase', color }, text);

const layout = (card: Card): Node =>
  h(
    'div',
    { width: 1200, height: 630, flexDirection: 'column', backgroundColor: C.paper, padding: '48px 64px', color: C.ink },
    h(
      'div',
      { justifyContent: 'space-between', alignItems: 'center', borderBottom: `2px solid ${C.ink}`, paddingBottom: 14 },
      h('div', { fontFamily: 'Fraunces', fontSize: 34, fontWeight: 600 }, 'Truong Huy ', h('span', { fontStyle: 'italic', fontWeight: 400, color: C.oxblood, marginLeft: 8 }, 'Research')),
      label(card.context)
    ),
    h(
      'div',
      { flexGrow: 1, flexDirection: 'column', justifyContent: 'center' },
      h(
        'div',
        { alignItems: 'center' },
        card.seal
          ? h(
              'div',
              { width: 72, height: 72, marginRight: 24, backgroundColor: C.seal, color: C.paper, alignItems: 'center', justifyContent: 'center', fontFamily: 'Geist Mono', fontSize: 22, transform: 'rotate(-5deg)', border: `3px solid ${C.paper}`, boxShadow: `0 0 0 2px ${C.seal}` },
              card.seal
            )
          : null,
        label(card.kicker, C.oxblood)
      ),
      h(
        'div',
        { marginTop: 22, fontFamily: 'Fraunces', fontWeight: 600, fontSize: card.headline.length > 80 ? 50 : card.headline.length > 50 ? 60 : 72, lineHeight: 1.06, letterSpacing: -1.5 },
        card.headline
      )
    ),
    h(
      'div',
      { borderTop: `3px solid ${C.ink}`, paddingTop: 18, justifyContent: 'space-between', alignItems: 'flex-end' },
      h(
        'div',
        { gap: 48 },
        ...card.figures.map((figure) =>
          h('div', { flexDirection: 'column' }, label(figure.label), h('div', { fontFamily: 'Fraunces', fontWeight: 600, fontSize: 40, marginTop: 4, color: figure.tone ?? C.ink }, figure.value))
        )
      ),
      label('truonghuyresearch.xyz')
    )
  );

const tone = (value: number | null) => (value == null ? C.muted : value >= 0 ? C.ledger : C.oxblood);

const noteCard = (note: NoteSummary): Card => ({
  kicker: `${note.kind} market view`,
  context: note.period,
  headline: note.headline,
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
          seal: model.ticker,
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
