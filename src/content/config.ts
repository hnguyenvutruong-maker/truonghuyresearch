import { defineCollection, z } from 'astro:content';

const marketViews = defineCollection({
  type: 'content',
  schema: z.object({
    // Core
    title: z.string(),
    date: z.coerce.date(),
    week_start: z.coerce.date(),
    week_end: z.coerce.date(),
    session_tone: z.enum(['positive', 'negative', 'neutral']),

    // VN-Index
    vn_index_open: z.number(),
    vn_index_high: z.number(),
    vn_index_low: z.number(),
    vn_index_close: z.number(),
    vn_index_weekly_change_pct: z.number(),
    avg_daily_liquidity_bn_vnd: z.number(),
    foreign_net_weekly_bn_vnd: z.number().nullable(),
    foreign_buy_weekly_bn_vnd: z.number().nullable().optional(),
    foreign_sell_weekly_bn_vnd: z.number().nullable().optional(),

    // Global macro
    dxy_close: z.number().nullable(),
    dxy_weekly_change_pct: z.number().nullable(),
    usd_vnd: z.number().nullable(),
    usd_vnd_weekly_change_pct: z.number().nullable(),

    // Crypto
    btc_close: z.number().nullable(),
    btc_weekly_change_pct: z.number().nullable(),

    // Commodities
    gold_close: z.number().nullable(),
    gold_weekly_change_pct: z.number().nullable(),
    wti_close: z.number().nullable(),
    wti_weekly_change_pct: z.number().nullable(),

    // Daily OHLCV for candlestick chart (optional — emitted by bot when data available)
    vn_index_daily: z.array(z.object({
      time: z.string(),
      open: z.number(),
      high: z.number(),
      low: z.number(),
      close: z.number(),
    })).optional(),
  }),
});

const monthlyViews = defineCollection({
  type: 'content',
  schema: z.object({
    // Core
    title: z.string(),
    date: z.coerce.date(),            // last trading day
    month_start: z.coerce.date(),
    month_end: z.coerce.date(),
    session_tone: z.enum(['positive', 'negative', 'neutral']),

    // VN-Index
    vn_index_open: z.number(),
    vn_index_high: z.number(),
    vn_index_low: z.number(),
    vn_index_close: z.number(),
    vn_index_monthly_change_pct: z.number(),
    avg_daily_liquidity_bn_vnd: z.number(),
    foreign_net_monthly_bn_vnd: z.number().nullable(),
    foreign_buy_monthly_bn_vnd: z.number().nullable().optional(),
    foreign_sell_monthly_bn_vnd: z.number().nullable().optional(),
    trading_days: z.number(),

    // Best / Worst sectors
    best_sector: z.string().nullable(),
    best_sector_change_pct: z.number().nullable(),
    worst_sector: z.string().nullable(),
    worst_sector_change_pct: z.number().nullable(),

    // Global macro
    dxy_close: z.number().nullable(),
    dxy_monthly_change_pct: z.number().nullable(),
    usd_vnd: z.number().nullable(),
    usd_vnd_monthly_change_pct: z.number().nullable(),

    // Crypto
    btc_close: z.number().nullable(),
    btc_monthly_change_pct: z.number().nullable(),

    // Commodities
    gold_close: z.number().nullable(),
    gold_monthly_change_pct: z.number().nullable(),
    wti_close: z.number().nullable(),
    wti_monthly_change_pct: z.number().nullable(),

    // Daily OHLCV for candlestick chart (optional — emitted by bot when data available)
    vn_index_daily: z.array(z.object({
      time: z.string(),
      open: z.number(),
      high: z.number(),
      low: z.number(),
      close: z.number(),
    })).optional(),
  }),
});

export const collections = { 'market-views': marketViews, 'monthly-views': monthlyViews };
