// Normalises weekly (market-views) and monthly (monthly-views) entries into one shape,
// so list and detail pages share components instead of duplicating markup.
import type { CollectionEntry } from 'astro:content';
import { formatMonth, formatWeek } from './format';

export type NoteKind = 'Weekly' | 'Monthly';

export type MacroRow = { label: string; value: number | null; decimals: number; change: number | null };

export type NoteSummary = {
  kind: NoteKind;
  slug: string;
  href: string;
  title: string;
  /** Title without the "Weekly Market View: 25/05 – 29/05 —" prefix; the kicker carries the period. */
  headline: string;
  period: string;
  date: Date;
  tone: 'positive' | 'negative' | 'neutral';
  open: number;
  high: number;
  low: number;
  close: number;
  change: number;
  liquidity: number;
  foreignNet: number | null;
  foreignBuy: number | null;
  foreignSell: number | null;
  macro: MacroRow[];
  extras: Array<{ label: string; value: string }>;
  daily: Array<{ time: string; open: number; high: number; low: number; close: number }>;
};

// Monthly titles keep their "May 2026 —" dateline: without it the headline has no subject.
export const headlineOf = (title: string): string =>
  title
    .replace(/^(Weekly|Monthly) Market View:\s*/i, '')
    .replace(/^\d{2}\/\d{2}\s*[–-]\s*\d{2}\/\d{2}\s*—\s*/, '')
    .replace(/^([A-Z][a-z]+ \d{4})\s+[—–-]\s+/, '$1 — ');

export const weeklySummary = (entry: CollectionEntry<'market-views'>): NoteSummary => {
  const d = entry.data;
  return {
    kind: 'Weekly',
    slug: entry.slug,
    href: `/market-views/${entry.slug}`,
    title: d.title,
    headline: headlineOf(d.title),
    period: formatWeek(d.week_start, d.week_end),
    date: d.date,
    tone: d.session_tone,
    open: d.vn_index_open,
    high: d.vn_index_high,
    low: d.vn_index_low,
    close: d.vn_index_close,
    change: d.vn_index_weekly_change_pct,
    liquidity: d.avg_daily_liquidity_bn_vnd,
    foreignNet: d.foreign_net_weekly_bn_vnd,
    foreignBuy: d.foreign_buy_weekly_bn_vnd ?? null,
    foreignSell: d.foreign_sell_weekly_bn_vnd ?? null,
    macro: [
      { label: 'DXY', value: d.dxy_close, decimals: 2, change: d.dxy_weekly_change_pct },
      { label: 'USD/VND', value: d.usd_vnd, decimals: 0, change: d.usd_vnd_weekly_change_pct },
      { label: 'Gold', value: d.gold_close, decimals: 0, change: d.gold_weekly_change_pct },
      { label: 'WTI', value: d.wti_close, decimals: 2, change: d.wti_weekly_change_pct },
      { label: 'BTC', value: d.btc_close, decimals: 0, change: d.btc_weekly_change_pct },
    ],
    extras: [],
    daily: d.vn_index_daily ?? [],
  };
};

export const monthlySummary = (entry: CollectionEntry<'monthly-views'>): NoteSummary => {
  const d = entry.data;
  const sector = (name: string | null, change: number | null) =>
    name ? `${name}${change != null ? ` ${change >= 0 ? '+' : '−'}${Math.abs(change).toFixed(2)}%` : ''}` : '—';
  return {
    kind: 'Monthly',
    slug: entry.slug,
    href: `/monthly-views/${entry.slug}`,
    title: d.title,
    headline: headlineOf(d.title),
    period: formatMonth(d.month_start),
    date: d.date,
    tone: d.session_tone,
    open: d.vn_index_open,
    high: d.vn_index_high,
    low: d.vn_index_low,
    close: d.vn_index_close,
    change: d.vn_index_monthly_change_pct,
    liquidity: d.avg_daily_liquidity_bn_vnd,
    foreignNet: d.foreign_net_monthly_bn_vnd,
    foreignBuy: d.foreign_buy_monthly_bn_vnd ?? null,
    foreignSell: d.foreign_sell_monthly_bn_vnd ?? null,
    macro: [
      { label: 'DXY', value: d.dxy_close, decimals: 2, change: d.dxy_monthly_change_pct },
      { label: 'USD/VND', value: d.usd_vnd, decimals: 0, change: d.usd_vnd_monthly_change_pct },
      { label: 'Gold', value: d.gold_close, decimals: 0, change: d.gold_monthly_change_pct },
      { label: 'WTI', value: d.wti_close, decimals: 2, change: d.wti_monthly_change_pct },
      { label: 'BTC', value: d.btc_close, decimals: 0, change: d.btc_monthly_change_pct },
    ],
    extras: [
      { label: 'Trading days', value: String(d.trading_days) },
      { label: 'Best sector', value: sector(d.best_sector, d.best_sector_change_pct) },
      { label: 'Worst sector', value: sector(d.worst_sector, d.worst_sector_change_pct) },
    ],
    daily: d.vn_index_daily ?? [],
  };
};
