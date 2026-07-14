export interface ColorToken {
  name: string;
  varName: string;
  hex: string;
  className: string;
  usage: string;
}

export interface ColorGroup {
  title: string;
  description: string;
  tokens: ColorToken[];
}

export const colorGroups: ColorGroup[] = [
  {
    title: "Ink & Neutrals",
    description: "Text, surfaces, and structural backgrounds used across every page.",
    tokens: [
      { name: "Ink", varName: "--color-ink", hex: "#293234", className: "bg-ink", usage: "Primary text, dark surfaces, sidebar" },
      { name: "Surface", varName: "--color-surface", hex: "#FFFFFF", className: "bg-surface", usage: "Card backgrounds" },
      { name: "Warm Background", varName: "--color-warm-bg", hex: "#F7F6F1", className: "bg-warm-bg", usage: "Marketing page background" },
      { name: "Background", varName: "--color-background", hex: "#F8FAFC", className: "bg-background", usage: "App background (legacy)" },
      { name: "Mist", varName: "--color-mist", hex: "#E8E8EC", className: "bg-mist", usage: "Subtle fills, dividers, hover states" },
      { name: "Steel", varName: "--color-steel", hex: "#879DBA", className: "bg-steel", usage: "Muted text, secondary icons" },
    ],
  },
  {
    title: "Brand Accent",
    description: "The chartreuse family — primary interactive color across the product.",
    tokens: [
      { name: "Lime", varName: "--color-lime", hex: "#D5F332", className: "bg-lime", usage: "Primary buttons, active states" },
      { name: "Lime Light", varName: "--color-lime-light", hex: "#DBF554", className: "bg-lime-light", usage: "Hover/highlight tint" },
      { name: "Lime Dark", varName: "--color-lime-dark", hex: "#ADC825", className: "bg-lime-dark", usage: "Text-on-light accent, chart lines" },
      { name: "Olive", varName: "--color-olive", hex: "#9EA561", className: "bg-olive", usage: "Muted accent, illustration tones" },
      { name: "Sage", varName: "--color-sage", hex: "#B9C080", className: "bg-sage", usage: "Secondary illustration tones" },
    ],
  },
  {
    title: "Data & Semantic",
    description: "Blues used for informational states and secondary chart series.",
    tokens: [
      { name: "Royal", varName: "--color-royal", hex: "#305293", className: "bg-royal", usage: "Battery, grid price series" },
      { name: "Azure", varName: "--color-azure", hex: "#4A70BE", className: "bg-azure", usage: "Consumption series, links" },
      { name: "Danger", varName: "--color-danger", hex: "#EF4444", className: "bg-danger", usage: "Errors, destructive actions" },
    ],
  },
  {
    title: "Legacy Brand",
    description: "Original SolarFlow palette — still used for data-viz semantics and select marketing accents.",
    tokens: [
      { name: "Primary Navy", varName: "--color-primary-navy", hex: "#1D1C3B", className: "bg-primary-navy", usage: "Legacy dark surface" },
      { name: "Primary Green", varName: "--color-primary-green", hex: "#3CB54A", className: "bg-primary-green", usage: "Savings, positive trend" },
      { name: "Secondary Green", varName: "--color-secondary-green", hex: "#88C857", className: "bg-secondary-green", usage: "CO₂ / carbon metrics" },
      { name: "Solar Yellow", varName: "--color-solar-yellow", hex: "#F8F66A", className: "bg-solar-yellow", usage: "Ratings, highlights" },
      { name: "Energy Orange", varName: "--color-energy-orange", hex: "#FDB94C", className: "bg-energy-orange", usage: "Battery/consumption charts" },
    ],
  },
  {
    title: "Semantic & Text",
    description: "Status colors and text hierarchy used consistently across forms, alerts, and tables.",
    tokens: [
      { name: "Success", varName: "--color-success", hex: "#16A34A", className: "bg-success", usage: "Success states, confirmations" },
      { name: "Info", varName: "--color-info", hex: "#2563EB", className: "bg-info", usage: "Informational alerts, links" },
      { name: "Warning", varName: "--color-warning", hex: "#F59E0B", className: "bg-warning", usage: "Warning states, caution" },
      { name: "Border", varName: "--color-border", hex: "#E5E7EB", className: "bg-border", usage: "Default border color" },
      { name: "Text Primary", varName: "--color-text-primary", hex: "#111827", className: "bg-text-primary", usage: "Body copy, headings" },
      { name: "Text Secondary", varName: "--color-text-secondary", hex: "#64748B", className: "bg-text-secondary", usage: "Muted / supporting text" },
    ],
  },
];

export const typeScale = [
  { label: "Display XL", sample: "Renewable Energy", className: "text-6xl font-bold tracking-tight", specs: "60px / Bold / -0.02em" },
  { label: "Display Large", sample: "Renewable Energy", className: "text-5xl font-bold tracking-tight", specs: "48px / Bold / -0.02em" },
  { label: "H1", sample: "Financial Reports", className: "text-3xl font-bold tracking-tight", specs: "30px / Bold / -0.02em" },
  { label: "H2", sample: "Monthly Savings Trend", className: "text-2xl font-bold tracking-tight", specs: "24px / Bold / -0.01em" },
  { label: "H3", sample: "Battery Health & Lifespan", className: "text-lg font-semibold", specs: "18px / Semibold" },
  { label: "H4", sample: "Charging Strategy", className: "text-base font-semibold", specs: "16px / Semibold" },
  { label: "H5", sample: "Next Scheduled Action", className: "text-sm font-semibold", specs: "14px / Semibold" },
  { label: "Body Large", sample: "Real-time dashboards designed for energy managers.", className: "text-base text-gray-600", specs: "16px / Regular" },
  { label: "Body Medium", sample: "Real-time dashboards designed for energy managers.", className: "text-sm text-gray-600", specs: "14px / Regular" },
  { label: "Body Small", sample: "Real-time dashboards designed for energy managers.", className: "text-xs text-gray-600", specs: "12px / Regular" },
  { label: "Caption", sample: "TRAILING 12 MONTHS", className: "text-xs font-semibold uppercase tracking-widest text-gray-400", specs: "12px / Semibold / uppercase" },
  { label: "Overline", sample: "SOLARFLOW · AI ENERGY", className: "text-[11px] font-bold uppercase tracking-[0.15em] text-gray-400", specs: "11px / Bold / 0.15em" },
  { label: "Button Text", sample: "Book a Demo", className: "text-sm font-semibold text-ink", specs: "14px / Semibold" },
  { label: "Table Text", sample: "€2,280.00", className: "text-sm font-mono text-ink", specs: "14px / Mono / Regular" },
  { label: "Metric Numbers", sample: "€2,280", className: "text-3xl font-bold tracking-tight text-ink tabular-nums", specs: "30px / Bold / tabular-nums" },
];

export const spacingScale = [
  { token: "space-1", px: 4 },
  { token: "space-2", px: 8 },
  { token: "space-3", px: 12 },
  { token: "space-4", px: 16 },
  { token: "space-5", px: 20 },
  { token: "space-6", px: 24 },
  { token: "space-8", px: 32 },
  { token: "space-10", px: 40 },
  { token: "space-12", px: 48 },
  { token: "space-16", px: 64 },
];

export const breakpoints = [
  { token: "sm", px: 640, usage: "Large phones" },
  { token: "md", px: 768, usage: "Tablets" },
  { token: "lg", px: 1024, usage: "Small laptops — sidebar appears" },
  { token: "xl", px: 1280, usage: "Desktops — 3-4 col grids" },
  { token: "2xl", px: 1536, usage: "Wide monitors" },
];

export const radiusScale = [
  { token: "rounded-lg", px: 8 },
  { token: "rounded-xl", px: 12 },
  { token: "rounded-2xl", px: 16 },
  { token: "rounded-3xl", px: 24 },
  { token: "rounded-full", px: 9999 },
];

export const deviceFrames = [
  { token: "Desktop", px: 1440, cols: 12 },
  { token: "Laptop", px: 1280, cols: 12 },
  { token: "Tablet", px: 768, cols: 8 },
  { token: "Mobile", px: 390, cols: 4 },
];

export const shadowScale = [
  { token: "shadow-sm", css: "0 1px 2px rgba(41,50,52,0.06)", usage: "Inputs, subtle separation" },
  { token: "shadow-md", css: "0 4px 12px rgba(41,50,52,0.08)", usage: "Cards on hover" },
  { token: "shadow-lg", css: "0 12px 24px rgba(41,50,52,0.10)", usage: "Dropdowns, popovers" },
  { token: "shadow-xl", css: "0 24px 48px rgba(41,50,52,0.14)", usage: "Modals, drawers" },
];

export const zIndexScale = [
  { token: "z-content", value: 0, usage: "Page content" },
  { token: "z-sticky", value: 30, usage: "Sticky headers, topbar" },
  { token: "z-dropdown", value: 40, usage: "Dropdowns, popovers, tooltips" },
  { token: "z-overlay", value: 45, usage: "Modal / drawer backdrop" },
  { token: "z-modal", value: 50, usage: "Modals, drawers, command palette" },
  { token: "z-toast", value: 60, usage: "Toasts, snackbars — always on top" },
];

export const motionScale = [
  { token: "duration-fast", value: "120ms", usage: "Hover, focus, toggle" },
  { token: "duration-base", value: "180ms", usage: "Dropdowns, accordions" },
  { token: "duration-slow", value: "280ms", usage: "Modals, drawers" },
  { token: "ease-standard", value: "cubic-bezier(0.4, 0, 0.2, 1)", usage: "Default easing" },
  { token: "ease-out", value: "cubic-bezier(0, 0, 0.2, 1)", usage: "Entrances" },
  { token: "ease-in", value: "cubic-bezier(0.4, 0, 1, 1)", usage: "Exits" },
];

export const iconSizes = [
  { token: "icon-xs", px: 12 },
  { token: "icon-sm", px: 16 },
  { token: "icon-md", px: 20 },
  { token: "icon-lg", px: 24 },
  { token: "icon-xl", px: 32 },
];
