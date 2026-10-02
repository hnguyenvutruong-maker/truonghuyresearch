// Day/night theme engine. The inline script in BaseLayout picks the first theme before
// paint (same rule as autoTheme); this module handles everything after that: the header
// toggle, the 06:00 / 18:00 automatic switch, and the `themechange` event that the sky
// intro and the chart listen to.

export type Theme = 'light' | 'dark';
export type ThemeSource = 'load' | 'toggle' | 'clock';
export type ThemeChangeDetail = { theme: Theme; source: ThemeSource };

const KEY = 'thr-theme';
const root = document.documentElement;

/** Night from 18:00 to 05:59 in the viewer's local time. */
export const isNight = (date = new Date()): boolean => date.getHours() >= 18 || date.getHours() < 6;
export const autoTheme = (date = new Date()): Theme => (isNight(date) ? 'dark' : 'light');
export const currentTheme = (): Theme => (root.dataset.theme === 'dark' ? 'dark' : 'light');

const readOverride = (): Theme | null => {
  try {
    const value = localStorage.getItem(KEY);
    return value === 'light' || value === 'dark' ? value : null;
  } catch {
    return null;
  }
};

const writeOverride = (value: Theme | null) => {
  try {
    if (value) localStorage.setItem(KEY, value);
    else localStorage.removeItem(KEY);
  } catch {
    /* storage blocked: the choice lasts for this page view only */
  }
};

export const applyTheme = (theme: Theme, source: ThemeSource) => {
  root.dataset.theme = theme;
  root.dataset.themeMode = readOverride() ? 'manual' : 'auto';
  window.dispatchEvent(new CustomEvent<ThemeChangeDetail>('themechange', { detail: { theme, source } }));
};

/** Flip the theme. Choosing what the clock would pick anyway returns to automatic mode. */
export const toggleTheme = () => {
  const next: Theme = currentTheme() === 'dark' ? 'light' : 'dark';
  writeOverride(next === autoTheme() ? null : next);
  applyTheme(next, 'toggle');
  scheduleClock();
};

let timer: number | undefined;

/** In automatic mode, switch at the next 06:00 or 18:00 boundary while the page stays open. */
export const scheduleClock = () => {
  window.clearTimeout(timer);
  if (readOverride()) return;
  const now = new Date();
  const next = new Date(now);
  next.setHours(isNight(now) && now.getHours() >= 18 ? 30 : isNight(now) ? 6 : 18, 0, 5, 0);
  timer = window.setTimeout(() => {
    if (!readOverride()) applyTheme(autoTheme(), 'clock');
    scheduleClock();
  }, Math.min(next.getTime() - now.getTime(), 2 ** 31 - 1));
};

/** Enable cross-fade transitions after the first paint, then start the clock. */
export const initTheme = () => {
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.add('theme-ready')));
  scheduleClock();
};
