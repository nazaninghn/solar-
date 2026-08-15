"use client";

import { motion } from "framer-motion";
import { Check, CreditCard, Receipt, Zap } from "lucide-react";

const plans = [
  {
    name: "Starter",
    price: "€990",
    period: "/month",
    current: false,
    features: ["1 factory", "10 devices", "Basic forecasting", "Email support", "7-day data"],
  },
  {
    name: "Professional",
    price: "€2,490",
    period: "/month",
    current: true,
    features: ["5 factories", "100 devices", "AI recommendations", "Priority support", "90-day data", "Financial reports"],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    current: false,
    features: ["Unlimited factories", "Unlimited devices", "Custom AI models", "Dedicated support", "Unlimited data", "On-premise option"],
  },
];

const invoices = [
  { id: "INV-2026-08", date: "Aug 1, 2026", amount: "€2,490.00", status: "Paid" },
  { id: "INV-2026-07", date: "Jul 1, 2026", amount: "€2,490.00", status: "Paid" },
  { id: "INV-2026-06", date: "Jun 1, 2026", amount: "€2,490.00", status: "Paid" },
  { id: "INV-2026-05", date: "May 1, 2026", amount: "€990.00", status: "Paid" },
];

export default function BillingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Billing & Savings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your subscription and view energy savings</p>
      </div>

      {/* Savings Summary */}
      <div className="grid md:grid-cols-3 gap-4">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-gradient-to-br from-primary-green to-secondary-green rounded-2xl p-5 text-white">
          <Zap size={20} className="opacity-80" />
          <p className="text-sm opacity-80 mt-2">Monthly Savings</p>
          <p className="text-2xl font-bold mt-1">€4,280</p>
          <p className="text-xs opacity-70 mt-1">+18% vs last month</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white rounded-2xl p-5 border border-gray-100">
          <Receipt size={20} className="text-royal" />
          <p className="text-xs text-gray-400 mt-2">Current Plan</p>
          <p className="text-lg font-bold text-ink mt-1">Professional</p>
          <p className="text-xs text-gray-400 mt-1">€2,490/month · Renews Sep 1</p>
        </motion.div>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white rounded-2xl p-5 border border-gray-100">
          <CreditCard size={20} className="text-energy-orange" />
          <p className="text-xs text-gray-400 mt-2">Payment Method</p>
          <p className="text-lg font-bold text-ink mt-1">•••• 4242</p>
          <p className="text-xs text-gray-400 mt-1">Visa · Expires 12/28</p>
        </motion.div>
      </div>

      {/* Plans */}
      <div>
        <h2 className="text-lg font-semibold text-ink mb-4">Plans</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {plans.map((plan) => (
            <div key={plan.name} className={`rounded-2xl p-5 border ${plan.current ? "border-primary-green bg-primary-green/5 ring-1 ring-primary-green/20" : "border-gray-100 bg-white"}`}>
              {plan.current && <span className="text-[10px] font-bold text-primary-green uppercase tracking-wider">Current Plan</span>}
              <h3 className="text-base font-bold text-ink mt-1">{plan.name}</h3>
              <p className="text-2xl font-bold text-ink mt-2">{plan.price}<span className="text-sm text-gray-400 font-normal">{plan.period}</span></p>
              <ul className="mt-4 space-y-2">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
                    <Check size={14} className="text-primary-green shrink-0" /> {f}
                  </li>
                ))}
              </ul>
              <button className={`mt-4 w-full py-2.5 rounded-xl text-sm font-semibold transition-colors ${plan.current ? "bg-gray-100 text-gray-400 cursor-default" : "bg-ink text-white hover:bg-black"}`}>
                {plan.current ? "Current" : "Upgrade"}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Invoices */}
      <div>
        <h2 className="text-lg font-semibold text-ink mb-4">Invoice History</h2>
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left">
                <th className="px-5 py-3 text-xs text-gray-400 font-medium">Invoice</th>
                <th className="px-5 py-3 text-xs text-gray-400 font-medium">Date</th>
                <th className="px-5 py-3 text-xs text-gray-400 font-medium">Amount</th>
                <th className="px-5 py-3 text-xs text-gray-400 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((inv) => (
                <tr key={inv.id} className="border-b border-gray-50 hover:bg-gray-50/50">
                  <td className="px-5 py-3 font-medium text-ink">{inv.id}</td>
                  <td className="px-5 py-3 text-gray-500">{inv.date}</td>
                  <td className="px-5 py-3 font-semibold text-ink">{inv.amount}</td>
                  <td className="px-5 py-3"><span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary-green/10 text-primary-green">{inv.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
