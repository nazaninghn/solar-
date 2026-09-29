// The factory the dashboard shows. Until factory selection is wired into
// the UI, it comes from NEXT_PUBLIC_FACTORY_ID (e.g. the demo factory id
// printed by backend/scripts/seed_demo_site.py) and falls back to 1.
export const FACTORY_ID = Number(process.env.NEXT_PUBLIC_FACTORY_ID) || 1;
