// Build-time Open Graph cards (1200×630 PNG) in the Research Terminal style: the site card, one per
// valuation report (with range bars) and one per market note. satori lays out the card with the real
// fonts (static .woff — satori cannot read the variable .woff2 the site uses), sharp rasterises it.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { APIRoute, GetStaticPaths } from 'astro';
import { getCollection } from 'astro:content';
import satori from 'satori';
import sharp from 'sharp';
import { formatOutput, impliedMovePct, outputMethodLabel, valuationModels, type ValuationModel } from '../../data/valuation-models';
import { formatDate, formatIndex, formatNumber, formatVndK, signedNumber, signedPct } from '../../lib/format';
import { monthlySummary, weeklySummary, type NoteSummary } from '../../lib/notes';

type Node = { type: string; props: Record<string, unknown> };
type Child = Node | string | null | false;
const h = (type: string, style: Record<string, unknown>, ...children: Child[]): Node => ({
  type,
  props: { style: { display: 'flex', ...style }, children: children.filter((child): child is Node | string => Boolean(child)) },
});

// Research Terminal tokens (design-system/truong-huy-research/DESIGN.md)
const C = {
  canvas: '#0A0C10',
  l1: '#12151D',
  l2: '#1A1F2C',
  rule: '#262E3D',
  ink: '#F8FAFC',
  ink2: '#C2C6D6',
  ink3: '#94A3B8',
  ink4: '#64748B',
  cobalt: '#3B82F6',
  cobaltSoft: '#ADC6FF',
  cobaltBg: 'rgba(59,130,246,0.14)',
  spread: 'rgba(59,130,246,0.28)',
  up: '#4EDEA3',
  down: '#F87171',
  amber: '#FFB95F',
  amberSolid: '#F59E0B',
};
const font = (pkg: string, file: string) => readFileSync(join(process.cwd(), 'node_modules', pkg, 'files', file));
const fonts = [
  { name: 'Newsreader', data: font('@fontsource/newsreader', 'newsreader-latin-600-normal.woff'), weight: 600 as const, style: 'normal' as const },
  { name: 'Inter', data: font('@fontsource/inter', 'inter-latin-400-normal.woff'), weight: 400 as const, style: 'normal' as const },
  { name: 'JetBrains Mono', data: font('@fontsource/jetbrains-mono', 'jetbrains-mono-latin-500-normal.woff'), weight: 500 as const, style: 'normal' as const },
];

const mono = (text: string, size = 18, color = C.ink4, extra: Record<string, unknown> = {}) =>
  h('div', { fontFamily: 'JetBrains Mono', fontWeight: 500, fontSize: size, color, ...extra }, text);
const label = (text: string, color = C.ink4) => mono(text.toUpperCase(), 15, color, { letterSpacing: 1.2 });
const tone = (value: number | null) => (value == null ? C.ink4 : value >= 0 ? C.up : C.down);
const serifSize = (text: string, big = 64) => (text.length > 90 ? big - 22 : text.length > 60 ? big - 14 : text.length > 36 ? big - 6 : big);

type Fact = { label: string; value: string; color?: string };
const factStrip = (facts: Fact[]) =>
  h(
    'div',
    { border: `1px solid ${C.rule}`, borderRadius: 4, backgroundColor: C.l2 },
    ...facts.map((f, i) =>
      h(
        'div',
        { flexDirection: 'column', flexGrow: 1, flexBasis: 0, padding: '14px 18px', borderLeft: i === 0 ? 'none' : `1px solid ${C.rule}` },
        label(f.label),
        mono(f.value, 28, f.color ?? C.ink, { marginTop: 6 })
      )
    )
  );

const frame = (context: string, ...body: Child[]): Node =>
  h(
    'div',
    { width: 1200, height: 630, flexDirection: 'column', backgroundColor: C.canvas, color: C.ink },
    h(
      'div',
      { height: 64, padding: '0 48px', backgroundColor: C.l1, borderBottom: `1px solid ${C.rule}`, alignItems: 'center', justifyContent: 'space-between' },
      h(
        'div',
        { alignItems: 'center', gap: 14 },
        h(
          'div',
          { width: 26, height: 26, border: `2px solid ${C.cobalt}`, borderRadius: 6, alignItems: 'flex-end', justifyContent: 'center', gap: 3, padding: '0 0 5px' },
          h('div', { width: 4, height: 7, backgroundColor: C.cobalt }),
          h('div', { width: 4, height: 11, backgroundColor: C.cobalt }),
          h('div', { width: 4, height: 6, backgroundColor: C.cobalt })
        ),
        mono('TRUONG HUY', 20, C.ink, { letterSpacing: 2 }),
        mono('RESEARCH', 20, C.ink4, { letterSpacing: 2 })
      ),
      mono(context, 18, C.ink3)
    ),
    h('div', { flexGrow: 1, flexDirection: 'column', padding: '34px 48px 0' }, ...body),
    h(
      'div',
      { height: 44, padding: '0 48px', borderTop: `1px solid ${C.rule}`, alignItems: 'center', justifyContent: 'space-between' },
      mono('Nguyen Vu Truong Huy · Passed Level II of the CFA Program', 15, C.ink4),
      mono('truonghuyresearch.xyz', 15, C.ink3)
    )
  );

// Range bars for a report card: track, cobalt spread with edges, white pip at the price used,
// amber diamond at the base case. Positions are percentages of the bar width.
const rangeBars = (model: ValuationModel) => {
  const ref = model.referencePrice.value;
  const pct = (v: number) => (v / ref - 1) * 100;
  const lows = model.outputs.map((o) => pct(Math.min(o.low, o.high)));
  const highs = model.outputs.map((o) => pct(Math.max(o.low, o.high)));
  const MIN = Math.min(-10, Math.floor((Math.min(...lows, 0) - 4) / 10) * 10);
  const MAX = Math.max(10, Math.ceil((Math.max(...highs, 0) + 4) / 10) * 10);
  const x = (p: number) => ((Math.max(MIN, Math.min(MAX, p)) - MIN) / (MAX - MIN)) * 100;
  const zero = x(0);
  return h(
    'div',
    { flexDirection: 'column', gap: 12 },
    ...model.outputs.map((o) => {
      const a = x(pct(Math.min(o.low, o.high)));
      const b = Math.max(x(pct(Math.max(o.low, o.high))), a + 0.8);
      const move = impliedMovePct(o, model.referencePrice);
      return h(
        'div',
        { alignItems: 'center', height: 30 },
        mono(outputMethodLabel[o.method], 19, C.ink2, { width: 150 }),
        h(
          'div',
          { position: 'relative', flexGrow: 1, height: 22 },
          h('div', { position: 'absolute', left: 0, right: 0, top: 9, height: 4, borderRadius: 2, backgroundColor: C.rule }),
          h('div', {
            position: 'absolute',
            left: `${a}%`,
            width: `${b - a}%`,
            top: 3,
            height: 16,
            backgroundColor: C.spread,
            borderLeft: `2px solid ${C.cobalt}`,
            borderRight: `2px solid ${C.cobalt}`,
          }),
          o.base !== undefined
            ? h('div', { position: 'absolute', left: `${x(pct(o.base))}%`, top: 6, width: 10, height: 10, marginLeft: -5, backgroundColor: C.amberSolid, transform: 'rotate(45deg)' })
            : null,
          h('div', { position: 'absolute', left: `${zero}%`, top: 0, width: 2, height: 22, marginLeft: -1, backgroundColor: C.ink })
        ),
        h(
          'div',
          { width: 260, justifyContent: 'flex-end', gap: 12 },
          mono(formatOutput(o).replace('≈', '~'), 20, C.ink),
          mono(signedPct(move, 1), 20, tone(move))
        )
      );
    })
  );
};

const reportCard = (model: ValuationModel): Node => {
  const moves = model.outputs.map((o) => impliedMovePct(o, model.referencePrice));
  return frame(
    `VALUATION REPORT · MODEL ${formatDate(model.lastUpdated ?? model.referencePrice.asOf).toUpperCase()}`,
    h(
      'div',
      { alignItems: 'center', gap: 18 },
      h(
        'div',
        { padding: '6px 14px', border: `1px solid ${C.cobalt}`, borderRadius: 4, backgroundColor: C.cobaltBg },
        mono(model.ticker, 30, C.cobaltSoft, { letterSpacing: 1 })
      ),
      h('div', { fontFamily: 'Newsreader', fontWeight: 600, fontSize: 58, letterSpacing: -1, lineHeight: 1 }, model.company)
    ),
    mono(`${model.sector.toUpperCase()} · ${model.methods.join(' · ').toUpperCase()}`, 16, C.ink4, { marginTop: 14, letterSpacing: 1 }),
    h(
      'div',
      { flexDirection: 'column', marginTop: 30, padding: '20px 22px', border: `1px solid ${C.rule}`, borderRadius: 4, backgroundColor: C.l1 },
      rangeBars(model)
    ),
    h(
      'div',
      { marginTop: 22, flexDirection: 'column' },
      factStrip([
        { label: 'Price used', value: `VND ${formatVndK(model.referencePrice.value)}`, color: C.amber },
        { label: 'Price date', value: formatDate(model.referencePrice.asOf) },
        { label: 'Implied move', value: `${signedPct(Math.min(...moves), 0)} / ${signedPct(Math.max(...moves), 0)}` },
      ])
    ),
    h('div', { marginTop: 18, fontFamily: 'Inter', fontWeight: 400, fontSize: 20, lineHeight: 1.4, color: C.ink3 }, model.report.stance)
  );
};

const noteCard = (note: NoteSummary): Node =>
  frame(
    `${note.kind.toUpperCase()} MARKET VIEW · ${note.period.toUpperCase()}`,
    h(
      'div',
      { alignItems: 'center', gap: 10 },
      h('div', { padding: '4px 10px', border: `1px solid ${C.cobalt}`, borderRadius: 4, backgroundColor: C.cobaltBg }, mono(note.kind.toUpperCase(), 16, C.cobaltSoft, { letterSpacing: 1 })),
      mono(`Published ${formatDate(note.date)}`, 16, C.ink4)
    ),
    h(
      'div',
      { flexGrow: 1, alignItems: 'center' },
      h('div', { fontFamily: 'Newsreader', fontWeight: 600, fontSize: serifSize(note.headline, 60), lineHeight: 1.12, letterSpacing: -0.8 }, note.headline)
    ),
    h(
      'div',
      { marginBottom: 30, flexDirection: 'column' },
      factStrip([
        { label: 'VN-Index close', value: formatIndex(note.close), color: C.amber },
        { label: note.kind === 'Weekly' ? 'Week change' : 'Month change', value: signedPct(note.change), color: tone(note.change) },
        { label: 'Avg liquidity, bn', value: formatNumber(note.liquidity, 0) },
        { label: 'Foreign net, bn', value: note.foreignNet != null ? signedNumber(note.foreignNet) : '—', color: tone(note.foreignNet) },
      ])
    )
  );

const siteCard = (noteCount: number): Node =>
  frame(
    'EQUITY RESEARCH DESK · VIETNAM · HOSE',
    h(
      'div',
      { flexGrow: 1, flexDirection: 'column', justifyContent: 'center' },
      h('div', { fontFamily: 'Newsreader', fontWeight: 600, fontSize: 66, lineHeight: 1.06, letterSpacing: -1.2, maxWidth: 980 }, 'Vietnam equities, valued as ranges across methods'),
      mono('Nguyen Vu Truong Huy · UEH Finance & Banking · Passed Level II of the CFA Program', 19, C.ink3, { marginTop: 22 })
    ),
    h(
      'div',
      { marginBottom: 30, flexDirection: 'column' },
      factStrip([
        { label: 'Companies', value: String(valuationModels.length) },
        { label: 'Excel workbooks', value: String(valuationModels.reduce((t, m) => t + m.downloads.length, 0)) },
        { label: 'Market notes', value: String(noteCount) },
        { label: 'Prices used as of', value: formatDate(valuationModels[0].referencePrice.asOf), color: C.amber },
      ])
    )
  );

type Props = { kind: 'site'; noteCount: number } | { kind: 'report'; slug: string } | { kind: 'note'; note: NoteSummary };

export const getStaticPaths = (async () => {
  const weekly = (await getCollection('market-views')).map(weeklySummary);
  const monthly = (await getCollection('monthly-views')).map(monthlySummary);
  const notes = [...weekly, ...monthly];
  return [
    { params: { path: 'site' }, props: { kind: 'site', noteCount: notes.length } satisfies Props },
    ...valuationModels.map((model) => ({ params: { path: `research/${model.slug}` }, props: { kind: 'report', slug: model.slug } satisfies Props })),
    ...notes.map((note) => ({ params: { path: note.href.slice(1) }, props: { kind: 'note', note } satisfies Props })),
  ];
}) satisfies GetStaticPaths;

export const GET: APIRoute = async ({ props }) => {
  const p = props as Props;
  const model = p.kind === 'report' ? valuationModels.find((m) => m.slug === p.slug) : undefined;
  const node = p.kind === 'site' ? siteCard(p.noteCount) : p.kind === 'note' ? noteCard(p.note) : model ? reportCard(model) : siteCard(0);
  const svg = await satori(node as unknown as Parameters<typeof satori>[0], { width: 1200, height: 630, fonts });
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return new Response(new Uint8Array(png), { headers: { 'Content-Type': 'image/png' } });
};
