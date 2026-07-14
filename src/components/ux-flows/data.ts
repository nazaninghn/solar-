export type FlowStatus = "live" | "planned";

export type FlowStep = { label: string } | { branch: string[] };

export interface Flow {
  number: number;
  title: string;
  status: FlowStatus;
  route?: string;
  note?: string;
  steps: FlowStep[];
}

export interface FlowCategory {
  id: string;
  title: string;
  description: string;
  flows: Flow[];
}

const s = (label: string): FlowStep => ({ label });
const b = (...paths: string[]): FlowStep => ({ branch: paths });

export const flowCategories: FlowCategory[] = [
  {
    id: "acquisition",
    title: "Acquisition & Onboarding",
    description: "From a cold visitor to a fully configured factory — the highest-friction stretch of the journey, so every step earns its place.",
    flows: [
      {
        number: 1,
        title: "Landing → Sales → Invitation",
        status: "live",
        route: "/",
        note: "Marketing site is live; Book Demo → Sales handoff is a CTA link today, not a scheduling flow.",
        steps: [s("Landing Page"), s("Learn About Product"), s("Book Demo"), s("Talk with Sales"), s("Receive Invitation"), s("Create Account")],
      },
      {
        number: 2,
        title: "Account Registration",
        status: "live",
        route: "/register",
        note: "Register + email verification pages exist; org/factory creation steps are planned.",
        steps: [s("Create Account"), s("Verify Email"), s("Create Organization"), s("Create Factory"), s("Choose Industry"), s("Finish Setup")],
      },
      {
        number: 3,
        title: "Factory Setup Wizard",
        status: "planned",
        note: "No dedicated wizard yet — facility data is currently seeded, not entered by the user.",
        steps: [
          s("Factory Name"), s("Factory Address"), s("Location on Map"), s("Installed Solar Capacity"),
          s("Battery Capacity"), s("Grid Connection"), s("Electricity Tariff"), s("Working Hours"), s("Production Lines"), s("Finish"),
        ],
      },
      {
        number: 4,
        title: "Connect Energy Sources",
        status: "planned",
        note: "Integration pages don't exist yet — dashboard currently runs on demonstration data.",
        steps: [
          s("Connect Solar Inverter"), s("Connect Battery System"), s("Connect Smart Meter"),
          s("Connect Weather API"), s("Connect Electricity Market API"), s("Data Validation"), s("System Ready"),
        ],
      },
      {
        number: 5,
        title: "AI Initialization",
        status: "planned",
        note: "A one-time \"cold start\" sequence, shown once per factory before the dashboard has real signal.",
        steps: [
          s("Collect Data"), s("Analyze Consumption"), s("Analyze Weather"), s("Analyze Prices"),
          s("Generate First Prediction"), s("Generate First Recommendation"), s("Welcome Dashboard"),
        ],
      },
      {
        number: 19,
        title: "First-Time User Experience",
        status: "planned",
        note: "Product tour overlay — layers on top of the live dashboard once it exists.",
        steps: [
          s("Interactive Product Tour"), s("Feature Highlights"), s("Tooltips"), s("Quick Tips"), s("Sample Dashboard"), s("Congratulations Screen"),
        ],
      },
    ],
  },
  {
    id: "daily-usage",
    title: "Daily Usage",
    description: "What an Energy Manager actually does most mornings — the loop that has to be fast, not the funnel that has to convert.",
    flows: [
      {
        number: 6,
        title: "Daily Dashboard Session",
        status: "live",
        route: "/dashboard",
        steps: [
          s("Open Dashboard"), s("View Today's Summary"), s("Review AI Recommendation"), b("Approve", "Reject"),
          s("View Forecast"), s("Monitor Battery"), s("Check Electricity Prices"), s("Download Report"),
        ],
      },
      {
        number: 20,
        title: "Daily AI Workflow (system-side)",
        status: "live",
        route: "/dashboard/forecast",
        note: "This is the pipeline the AI itself runs each morning, surfaced via the Forecast + Insight Banner.",
        steps: [
          s("Weather Updates"), s("Solar Forecast"), s("Consumption Prediction"), s("Battery Optimization"),
          s("Price Forecast"), s("AI Decision"), s("Savings Prediction"), s("Daily Executive Summary"),
        ],
      },
    ],
  },
  {
    id: "ai-decisions",
    title: "AI & Recommendations",
    description: "Every AI output is designed to answer five questions before the user has to ask them.",
    flows: [
      {
        number: 7,
        title: "AI Recommendation Lifecycle",
        status: "live",
        route: "/dashboard/recommendations",
        steps: [
          s("Receive Recommendation"), s("Review Details"), s("View Financial Impact"), s("View Confidence Score"),
          b("Approve", "Reject"), s("Recommendation History"),
        ],
      },
    ],
  },
  {
    id: "energy-ops",
    title: "Energy Operations",
    description: "The two decisions that move money every single day: what to do with stored charge, and when to buy or sell.",
    flows: [
      {
        number: 8,
        title: "Battery Optimization",
        status: "live",
        route: "/dashboard/battery",
        steps: [s("Battery Status"), s("Charging Forecast"), s("Discharge Recommendation"), s("Savings Estimation"), s("Schedule Charging")],
      },
      {
        number: 9,
        title: "Energy Trading",
        status: "planned",
        note: "Price + trading widgets exist in the analytics system; a dedicated trading workflow page is planned.",
        steps: [
          s("Current Electricity Price"), s("Forecast Tomorrow"), s("AI Sell Recommendation"),
          s("Estimated Revenue"), s("Approve Selling Strategy"),
        ],
      },
    ],
  },
  {
    id: "reporting",
    title: "Financial Reporting",
    description: "Turning energy data into board-ready language — savings, revenue, ROI, and a document someone can forward.",
    flows: [
      {
        number: 10,
        title: "Financial Analysis",
        status: "live",
        route: "/dashboard/reports",
        steps: [s("Monthly Report"), s("Savings"), s("Revenue"), s("ROI"), s("Download PDF"), s("Share Report")],
      },
      {
        number: 13,
        title: "Report Cadences",
        status: "planned",
        note: "Monthly is live; Daily/Weekly/Annual/Custom ranges are planned extensions of the same report engine.",
        steps: [s("Daily Report"), s("Weekly Report"), s("Monthly Report"), s("Annual Report"), s("Custom Report")],
      },
    ],
  },
  {
    id: "alerts",
    title: "Alerts & Notifications",
    description: "Interrupting the user only when it's worth it, then getting out of the way.",
    flows: [
      {
        number: 11,
        title: "Alert Sources",
        status: "planned",
        note: "Alert types are defined; a unified alert-generation pipeline is planned.",
        steps: [
          s("High Electricity Price"), s("Battery Warning"), s("Low Solar Production"),
          s("Equipment Failure"), s("Weather Alert"), s("Notification Center"),
        ],
      },
      {
        number: 12,
        title: "Notification Lifecycle",
        status: "live",
        route: "/dashboard",
        note: "The Topbar notification dropdown is live; archive/resolve actions are planned.",
        steps: [s("Real-time Alerts"), s("Read"), s("Archive"), s("Resolve")],
      },
    ],
  },
  {
    id: "account-admin",
    title: "Account & Administration",
    description: "The parts of the product a Factory Owner or Administrator touches rarely, but needs to trust completely.",
    flows: [
      {
        number: 14,
        title: "User Management",
        status: "planned",
        steps: [s("Invite Team"), s("Assign Role"), s("Permissions"), s("Activity Log")],
      },
      {
        number: 15,
        title: "Factory Management",
        status: "planned",
        note: "Currently single-facility; multi-facility switching is planned as the product scales past one site.",
        steps: [s("Switch Factory"), s("View Factory"), s("Compare Factories"), s("Analytics")],
      },
      {
        number: 16,
        title: "Settings",
        status: "planned",
        note: "Sidebar link exists; the Settings pages themselves are planned.",
        steps: [s("Profile"), s("Organization"), s("Billing"), s("API Keys"), s("Notifications"), s("Security")],
      },
    ],
  },
  {
    id: "support-resilience",
    title: "Support & Resilience",
    description: "What happens when something goes wrong — a device disconnects, or the user just needs help.",
    flows: [
      {
        number: 17,
        title: "Support",
        status: "planned",
        steps: [s("Help Center"), s("Documentation"), s("Live Chat"), s("Submit Ticket")],
      },
      {
        number: 18,
        title: "Error Handling",
        status: "planned",
        note: "Component-level error/empty states exist in the design system; this end-to-end offline flow is planned.",
        steps: [s("Connection Lost"), s("Retry"), s("Offline Mode"), s("Sync Later")],
      },
    ],
  },
];

export const personas = [
  { role: "Factory Owner", goal: "Wants the 30-second version: are we saving money, and is anything on fire?", frequency: "Weekly" },
  { role: "Energy Manager", goal: "Lives in the dashboard daily — approves recommendations, watches battery and price signals.", frequency: "Daily" },
  { role: "Operations Manager", goal: "Cares about factory zones, equipment health, and load — energy is one input among many.", frequency: "Daily" },
  { role: "Financial Manager", goal: "Wants ROI, savings, and revenue in a format that drops straight into a board deck.", frequency: "Monthly" },
  { role: "Maintenance Engineer", goal: "Reacts to equipment alerts and battery health warnings — rarely opens the dashboard otherwise.", frequency: "As-needed" },
  { role: "Administrator", goal: "Manages who has access to what, across one or many factories.", frequency: "As-needed" },
];

export const sitemap = [
  {
    label: "Marketing",
    children: ["Home", "Login", "Register", "Forgot / Reset Password", "Verify Email"],
  },
  {
    label: "Dashboard",
    children: ["Overview", "Analytics", "Forecast", "AI Recommendations", "Battery Storage", "Billing & Savings", "Reports", "Settings"],
  },
  {
    label: "Reference",
    children: ["UI Design System", "Data Visualization System", "UX Flows (this page)"],
  },
];
