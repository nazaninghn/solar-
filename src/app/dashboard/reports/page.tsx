"use client";

import ExecutiveSummaryCard from "@/components/dashboard/reports/ExecutiveSummaryCard";
import ReportsKPIs from "@/components/dashboard/reports/ReportsKPIs";
import MonthlyTrendChart from "@/components/dashboard/reports/MonthlyTrendChart";
import MonthComparison from "@/components/dashboard/reports/MonthComparison";
import ForecastSavingsChart from "@/components/dashboard/reports/ForecastSavingsChart";
import ReportsTable from "@/components/dashboard/reports/ReportsTable";

export default function ReportsPage() {
  return (
    <>
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">Financial Reports</h1>
        <p className="text-sm text-gray-500 mt-1">
          Savings, revenue, ROI, and carbon impact across your facility.
        </p>
      </div>

      <ExecutiveSummaryCard />

      <ReportsKPIs />

      <div className="grid xl:grid-cols-3 gap-6 lg:gap-8">
        <div className="xl:col-span-2">
          <MonthlyTrendChart />
        </div>
        <MonthComparison />
      </div>

      <ForecastSavingsChart />

      <ReportsTable />
    </>
  );
}
