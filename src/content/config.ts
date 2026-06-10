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
    foreign_net_weekly_bn_vnd: z.number(),

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
  }),
});

const research = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    ticker: z.string(),
    sector: z.string(),
    recommendation: z.enum(['BUY', 'HOLD', 'SELL', 'NEUTRAL']),
    target_price_vnd: z.number().optional(),
    pdf_path: z.string().optional(),
    summary: z.string().max(200),
  }),
});

export const collections = { 'market-views': marketViews, research };
