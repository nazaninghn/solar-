export const battery = {
  health: 96,
  capacityRated: 120,
  capacityUsable: 115.2,
  soc: 68,
  chargeRateKw: 12.4,
  isCharging: true,
  temperatureC: 28,
  cycles: 842,
  ratedCycles: 6000,
  lifespanYearsRemaining: 7.4,
  replacementYear: 2033,
};

export const chargeHistory = [
  { time: "00:00", soc: 42 },
  { time: "02:00", soc: 38 },
  { time: "04:00", soc: 34 },
  { time: "06:00", soc: 30 },
  { time: "08:00", soc: 41 },
  { time: "10:00", soc: 58 },
  { time: "12:00", soc: 74 },
  { time: "14:00", soc: 68 },
  { time: "16:00", soc: 61 },
  { time: "18:00", soc: 55 },
  { time: "20:00", soc: 63 },
  { time: "22:00", soc: 68 },
];

export const chargeForecast = [
  { time: "Now", soc: 68, action: "hold" },
  { time: "+2h", soc: 79, action: "charge" },
  { time: "+4h", soc: 91, action: "charge" },
  { time: "+6h", soc: 95, action: "hold" },
  { time: "+8h", soc: 88, action: "discharge" },
  { time: "+10h", soc: 76, action: "discharge" },
  { time: "+12h", soc: 64, action: "discharge" },
  { time: "+14h", soc: 52, action: "hold" },
  { time: "+16h", soc: 45, action: "hold" },
  { time: "+18h", soc: 40, action: "charge" },
  { time: "+20h", soc: 55, action: "charge" },
  { time: "+22h", soc: 66, action: "charge" },
  { time: "+24h", soc: 72, action: "hold" },
];

export const degradation = [
  { year: "2026", capacityPct: 100 },
  { year: "2027", capacityPct: 98.2 },
  { year: "2028", capacityPct: 96.1 },
  { year: "2029", capacityPct: 93.8 },
  { year: "2030", capacityPct: 91.2 },
  { year: "2031", capacityPct: 88.4 },
  { year: "2032", capacityPct: 85.3 },
  { year: "2033", capacityPct: 82.0 },
];

export const strategies = [
  {
    id: "self-consumption",
    label: "Self-Consumption",
    description:
      "Prioritizes storing solar surplus to cover your own demand before drawing from or exporting to the grid.",
  },
  {
    id: "cost-optimization",
    label: "Cost Optimization",
    description:
      "Charges when grid prices are lowest and discharges or sells during peak pricing windows to maximize savings.",
  },
  {
    id: "backup-reserve",
    label: "Backup Reserve",
    description:
      "Maintains a minimum 40% reserve at all times for outage protection, optimizing only with remaining capacity.",
  },
];

export const activeStrategyId = "cost-optimization";

export const nextAction =
  "Charging scheduled 13:00–15:00 from solar surplus — adds an estimated 18% SOC before the evening price peak.";
