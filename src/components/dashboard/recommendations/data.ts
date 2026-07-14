import {
  BatteryCharging,
  ArrowRightLeft,
  Car,
  TrendingUp,
  Wrench,
  FileSignature,
  LucideIcon,
} from "lucide-react";

export type RecCategory = "Battery" | "Grid" | "Load" | "Maintenance" | "Billing";
export type RecStatus = "pending" | "approved" | "rejected";

export interface Recommendation {
  id: string;
  icon: LucideIcon;
  category: RecCategory;
  title: string;
  summary: string;
  confidence: number;
  savings: number | null;
  timeline: string;
  details: string[];
}

export const impactHistory = [
  { week: "Wk 1", savings: 62 },
  { week: "Wk 2", savings: 84 },
  { week: "Wk 3", savings: 71 },
  { week: "Wk 4", savings: 105 },
  { week: "Wk 5", savings: 96 },
  { week: "Wk 6", savings: 128 },
  { week: "Wk 7", savings: 142 },
  { week: "Wk 8", savings: 137 },
];

export const recommendations: Recommendation[] = [
  {
    id: "rec-1",
    icon: BatteryCharging,
    category: "Battery",
    title: "Charge battery from solar surplus",
    summary: "Production is exceeding demand by 38% right now — an ideal window to charge at zero marginal cost.",
    confidence: 94,
    savings: 45,
    timeline: "Today, 12:00–14:00",
    details: [
      "Current solar output (847 kW) exceeds facility demand (612 kW) by 235 kW.",
      "Battery SOC is at 68%, with 32% headroom before reaching target reserve.",
      "Charging now avoids drawing 47 kWh from the grid during tonight's peak.",
      "Confidence based on 14-day historical accuracy of solar forecasting model.",
    ],
  },
  {
    id: "rec-2",
    icon: ArrowRightLeft,
    category: "Grid",
    title: "Sell 120 kWh surplus at evening peak",
    summary: "Day-ahead pricing shows a sharp peak at 18:00 (€0.31/kWh) — export stored surplus before the drop.",
    confidence: 91,
    savings: 22,
    timeline: "Today, 18:00–19:00",
    details: [
      "Day-ahead market price forecast peaks at €0.31/kWh at 18:00, 68% above daily average.",
      "Battery will hold 95% SOC by 16:00, well above the 40% backup reserve threshold.",
      "Selling 120 kWh at peak vs. average price nets an additional €14 over a flat-rate sale.",
      "Recommendation expires at 17:30 if not acted on — price window closes quickly.",
    ],
  },
  {
    id: "rec-3",
    icon: Car,
    category: "Load",
    title: "Shift EV fleet charging to off-peak",
    summary: "Delaying fleet charging to 00:00–05:00 avoids current peak pricing and reduces demand charges.",
    confidence: 87,
    savings: 12.5,
    timeline: "Tonight, 00:00–05:00",
    details: [
      "5 fleet vehicles are scheduled to charge starting at 19:00 under the default policy.",
      "Off-peak window (00:00–05:00) averages €0.12/kWh vs. €0.19/kWh during evening hours.",
      "Vehicles are not required until 07:00, leaving ample buffer to complete charging.",
      "Demand charge exposure is reduced by avoiding overlap with evening building peak load.",
    ],
  },
  {
    id: "rec-4",
    icon: TrendingUp,
    category: "Grid",
    title: "Pre-charge ahead of Thursday's price spike",
    summary: "Forecast shows Thursday's grid price reaching €0.31/kWh — build battery reserve on Wednesday.",
    confidence: 78,
    savings: 31,
    timeline: "Wednesday, all day",
    details: [
      "Wednesday forecast: 47.5 kWh solar production, well above the 30.9 kWh consumption estimate.",
      "Thursday's price forecast is the highest of the 7-day window at €0.31/kWh average.",
      "Building reserve on Wednesday reduces reliance on expensive grid import Thursday afternoon.",
      "Confidence is moderate due to 2-day-ahead weather forecast uncertainty (~15% margin).",
    ],
  },
  {
    id: "rec-5",
    icon: Wrench,
    category: "Maintenance",
    title: "Schedule battery inverter inspection",
    summary: "Minor efficiency drift detected on inverter unit 2 — a routine check now can prevent output loss.",
    confidence: 65,
    savings: null,
    timeline: "Within the next 2 weeks",
    details: [
      "Inverter unit 2 conversion efficiency has drifted from 97.8% to 96.4% over the past 30 days.",
      "Pattern is consistent with early-stage capacitor wear seen in similar installations.",
      "No immediate safety risk — this is a preventive, not urgent, recommendation.",
      "Deferring beyond 4-6 weeks increases risk of a larger, costlier repair.",
    ],
  },
  {
    id: "rec-6",
    icon: FileSignature,
    category: "Billing",
    title: "Switch to dynamic day-ahead tariff",
    summary: "Your usage pattern qualifies for a dynamic tariff plan projected to save €280/month vs. your current flat rate.",
    confidence: 82,
    savings: 280,
    timeline: "Next billing cycle",
    details: [
      "Analysis of 90 days of consumption shows 61% of usage already falls in off-peak hours.",
      "Your solar + battery setup further shifts effective grid draw toward cheaper windows.",
      "Projected savings account for the dynamic plan's small monthly service fee.",
      "Switching requires utility provider confirmation — SolarFlow can initiate on approval.",
    ],
  },
];
