export interface MonthlyReport {
  month: string;
  year: string;
  solarKwh: number;
  consumptionKwh: number;
  savings: number;
  revenue: number;
  roi: number;
  gridCost: number;
  carbonTons: number;
}

export const monthly: MonthlyReport[] = [
  { month: "Aug", year: "2025", solarKwh: 5240, consumptionKwh: 3980, savings: 1840, revenue: 620, roi: 6.8, gridCost: 0.192, carbonTons: 2.9 },
  { month: "Sep", year: "2025", solarKwh: 4780, consumptionKwh: 3820, savings: 1690, revenue: 560, roi: 6.5, gridCost: 0.188, carbonTons: 2.6 },
  { month: "Oct", year: "2025", solarKwh: 3620, consumptionKwh: 3910, savings: 1320, revenue: 410, roi: 5.9, gridCost: 0.195, carbonTons: 2.0 },
  { month: "Nov", year: "2025", solarKwh: 2410, consumptionKwh: 4120, savings: 980, revenue: 260, roi: 4.8, gridCost: 0.201, carbonTons: 1.3 },
  { month: "Dec", year: "2025", solarKwh: 1980, consumptionKwh: 4480, savings: 840, revenue: 190, roi: 4.1, gridCost: 0.214, carbonTons: 1.1 },
  { month: "Jan", year: "2026", solarKwh: 2150, consumptionKwh: 4390, savings: 890, revenue: 210, roi: 4.3, gridCost: 0.219, carbonTons: 1.2 },
  { month: "Feb", year: "2026", solarKwh: 2760, consumptionKwh: 4100, savings: 1080, revenue: 290, roi: 4.9, gridCost: 0.208, carbonTons: 1.5 },
  { month: "Mar", year: "2026", solarKwh: 3690, consumptionKwh: 3860, savings: 1410, revenue: 420, roi: 5.7, gridCost: 0.197, carbonTons: 2.1 },
  { month: "Apr", year: "2026", solarKwh: 4520, consumptionKwh: 3640, savings: 1720, revenue: 540, roi: 6.4, gridCost: 0.189, carbonTons: 2.5 },
  { month: "May", year: "2026", solarKwh: 5180, consumptionKwh: 3520, savings: 1980, revenue: 640, roi: 7.1, gridCost: 0.183, carbonTons: 2.9 },
  { month: "Jun", year: "2026", solarKwh: 5610, consumptionKwh: 3610, savings: 2140, revenue: 710, roi: 7.6, gridCost: 0.181, carbonTons: 3.1 },
  { month: "Jul", year: "2026", solarKwh: 5820, consumptionKwh: 3780, savings: 2280, revenue: 760, roi: 7.9, gridCost: 0.184, carbonTons: 3.3 },
];

export const forecast = [
  { month: "Aug", year: "2026", savings: 2340, revenue: 780 },
  { month: "Sep", year: "2026", savings: 2010, revenue: 660 },
  { month: "Oct", year: "2026", savings: 1560, revenue: 480 },
  { month: "Nov", year: "2026", savings: 1120, revenue: 310 },
];

export const totals = {
  savingsYTD: monthly.reduce((s, m) => s + m.savings, 0),
  revenueYTD: monthly.reduce((s, m) => s + m.revenue, 0),
  avgRoi: monthly.reduce((s, m) => s + m.roi, 0) / monthly.length,
  avgGridCost: monthly.reduce((s, m) => s + m.gridCost, 0) / monthly.length,
  carbonYTD: monthly.reduce((s, m) => s + m.carbonTons, 0),
};

export const current = monthly[monthly.length - 1];
export const previous = monthly[monthly.length - 2];

export const executiveSummary = [
  `Facility generated €${totals.savingsYTD.toLocaleString()} in verified savings and €${totals.revenueYTD.toLocaleString()} in grid export revenue over the trailing 12 months.`,
  `July was the strongest month on record — €${current.savings.toLocaleString()} in savings, up ${(((current.savings - previous.savings) / previous.savings) * 100).toFixed(0)}% month-over-month, driven by peak summer irradiance.`,
  `Blended ROI now averages ${totals.avgRoi.toFixed(1)}% across the trailing year, tracking ahead of the original 5-year payback model.`,
  `Cumulative carbon reduction reached ${totals.carbonYTD.toFixed(1)} tons CO₂, equivalent to taking roughly 3 passenger vehicles off the road for a year.`,
];
