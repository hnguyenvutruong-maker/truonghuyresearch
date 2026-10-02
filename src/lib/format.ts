// Shared number and date formatting. Dates from content collections are UTC midnight,
// so every date formatter pins timeZone: 'UTC' to avoid off-by-one days.

const UTC = { timeZone: 'UTC' } as const;

export const toDate = (value: Date | string): Date => (value instanceof Date ? value : new Date(`${value}T00:00:00Z`));

/** 11 Jun 2026 */
export const formatDate = (value: Date | string): string =>
  toDate(value).toLocaleDateString('en-GB', { ...UTC, day: '2-digit', month: 'short', year: 'numeric' });

/** June 2026 */
export const formatMonth = (value: Date | string): string =>
  toDate(value).toLocaleDateString('en-GB', { ...UTC, month: 'long', year: 'numeric' });

/** 01–05 Jun 2026, or 29 May–02 Jun 2026 across months */
export const formatWeek = (start: Date, end: Date): string => {
  const part = (date: Date, opts: Intl.DateTimeFormatOptions) => date.toLocaleDateString('en-GB', { ...UTC, ...opts });
  const sDay = part(start, { day: '2-digit' });
  const sMon = part(start, { month: 'short' });
  const eDay = part(end, { day: '2-digit' });
  const eMon = part(end, { month: 'short' });
  const eYear = part(end, { year: 'numeric' });
  return sMon === eMon ? `${sDay}–${eDay} ${eMon} ${eYear}` : `${sDay} ${sMon}–${eDay} ${eMon} ${eYear}`;
};

/** 1,838.90 */
export const formatIndex = (value: number): string =>
  value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** Fixed decimals with thousands separators; null → em dash */
export const formatNumber = (value: number | null | undefined, decimals = 2): string =>
  value == null ? '—' : value.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

/** True minus sign and explicit plus: +1.53% / −1.53% */
export const signedPct = (value: number | null | undefined, decimals = 2): string =>
  value == null ? '—' : `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(decimals)}%`;

/** +1,234 / −1,234 (bn VND and similar) */
export const signedNumber = (value: number | null | undefined, decimals = 0): string =>
  value == null ? '—' : `${value >= 0 ? '+' : '−'}${Math.abs(value).toLocaleString('en-US', { maximumFractionDigits: decimals })}`;

/** VND per share in thousands: 22260 → 22.3k */
export const formatVndK = (value: number): string => `${(Math.round(value / 100) / 10).toFixed(1)}k`;

/** Text colour for a signed figure: gains green, losses red (theme-aware tokens). */
export const toneClass = (value: number | null | undefined): string =>
  value == null ? 'text-fg-muted' : value >= 0 ? 'text-up' : 'text-down';

/** Whole days from `from` to `to`. */
export const daysBetween = (from: Date | string, to: Date | string): number =>
  Math.floor((toDate(to).valueOf() - toDate(from).valueOf()) / 86_400_000);
