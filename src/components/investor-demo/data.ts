export const scenes = [
  { id: "landing", title: "Landing" },
  { id: "login", title: "Sign In" },
  { id: "dashboard", title: "Executive Dashboard" },
  { id: "recommendation", title: "AI Recommendation" },
  { id: "battery", title: "Battery" },
  { id: "forecast", title: "Energy Forecast" },
  { id: "market", title: "Electricity Market" },
  { id: "financial", title: "Financial Report" },
  { id: "portfolio", title: "Multi-Factory View" },
  { id: "control-center", title: "AI Control Center" },
  { id: "summary", title: "Executive Summary" },
  { id: "cta", title: "Final CTA" },
] as const;

export type SceneId = (typeof scenes)[number]["id"];

export const investorMoments = [
  { value: 18, suffix: "%", label: "Reduction in Electricity Costs" },
  { value: 32, suffix: "%", label: "Increase in Self-Consumption" },
  { value: 92, suffix: "%", label: "AI Prediction Accuracy" },
  { value: 2.1, prefix: "$", suffix: "M", label: "Annual Savings", decimals: 1 },
  { value: 34, suffix: "%", label: "Less Grid Dependency" },
  { value: 28, suffix: "%", label: "Better Battery Utilization" },
];

export const executiveSummaryStats = [
  { value: 12400, prefix: "$", label: "Today's Savings" },
  { value: 185000, prefix: "$", label: "Monthly Savings" },
  { value: 2.1, prefix: "$", suffix: "M", label: "Annual Savings", decimals: 1 },
  { value: 1200, suffix: " Tons", label: "Carbon Reduction" },
  { value: 91, suffix: "%", label: "Battery Health" },
  { value: -34, suffix: "%", label: "Grid Dependency" },
];

export const portfolioFactories = [
  { name: "Munich HQ", x: 58, y: 38, solar: "5.8 MWh", battery: 84, savings: "$4,120", risk: "Low" },
  { name: "Lyon Plant", x: 28, y: 55, solar: "3.9 MWh", battery: 62, savings: "$2,640", risk: "Low" },
  { name: "Turin Depot", x: 46, y: 68, solar: "2.7 MWh", battery: 41, savings: "$1,180", risk: "Medium" },
  { name: "Rotterdam Hub", x: 42, y: 22, solar: "3.1 MWh", battery: 76, savings: "$2,460", risk: "Low" },
];
