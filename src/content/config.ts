import { defineCollection, z } from 'astro:content';

const marketViews = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    vn_index_close: z.number(),
    vn_index_change_pts: z.number(),
    vn_index_change_pct: z.number(),
    liquidity_bn_vnd: z.number(),
    foreign_net_bn_vnd: z.number(),
    session_tone: z.enum(['positive', 'negative', 'neutral']),
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