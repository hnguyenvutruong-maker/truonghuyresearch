import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  const weeklyViews = await getCollection('market-views');
  const monthlyViews = await getCollection('monthly-views');

  const allItems = [
    ...weeklyViews.map((entry) => ({
      title: entry.data.title,
      pubDate: entry.data.date,
      link: `/market-views/${entry.slug}/`,
      description: `Weekly VN-Index market view for the week ending ${entry.data.week_end.toISOString().slice(0, 10)}. Close: ${entry.data.vn_index_close.toLocaleString('en-US', { minimumFractionDigits: 2 })}, Change: ${entry.data.vn_index_weekly_change_pct >= 0 ? '+' : ''}${entry.data.vn_index_weekly_change_pct.toFixed(2)}%.`,
    })),
    ...monthlyViews.map((entry) => ({
      title: entry.data.title,
      pubDate: entry.data.date,
      link: `/monthly-views/${entry.slug}/`,
      description: `Monthly VN-Index market view for ${entry.data.month_start.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}. Close: ${entry.data.vn_index_close.toLocaleString('en-US', { minimumFractionDigits: 2 })}, Change: ${entry.data.vn_index_monthly_change_pct >= 0 ? '+' : ''}${entry.data.vn_index_monthly_change_pct.toFixed(2)}%.`,
    })),
  ].sort((a, b) => b.pubDate.valueOf() - a.pubDate.valueOf());

  return rss({
    title: 'Truong Huy Research — Market Views',
    description: 'Weekly and monthly Vietnam equity market notes by Nguyen Vu Truong Huy, CFA Level II Candidate.',
    site: context.site,
    items: allItems,
    customData: '<language>en</language>',
  });
}
