"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Building2, User, Bell, Shield, Globe, Cpu } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("factory");

  const tabs = [
    { id: "factory", label: "Factory", icon: Building2 },
    { id: "profile", label: "Profile", icon: User },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "security", label: "Security", icon: Shield },
    { id: "devices", label: "Devices", icon: Cpu },
    { id: "locale", label: "Language", icon: Globe },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your factory, profile, and system preferences</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id ? "bg-white text-ink shadow-sm" : "text-gray-500 hover:text-ink"
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Factory Settings */}
      {activeTab === "factory" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-5">
          <h2 className="text-base font-semibold text-ink">Factory Information</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Factory Name</label>
              <input defaultValue="Istanbul Solar Factory" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Address</label>
              <input defaultValue="Tuzla Industrial Zone, Istanbul" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Latitude</label>
              <input defaultValue="41.0082" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Longitude</label>
              <input defaultValue="28.9784" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Timezone</label>
              <input defaultValue="Europe/Istanbul" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Currency</label>
              <input defaultValue="EUR" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Solar Capacity (kW)</label>
              <input defaultValue="500" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Battery Capacity (kWh)</label>
              <input defaultValue="2000" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
          </div>
          <button className="px-6 py-2.5 bg-ink text-white text-sm font-semibold rounded-xl hover:bg-black transition-colors">
            Save Changes
          </button>
        </motion.div>
      )}

      {/* Profile */}
      {activeTab === "profile" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-5">
          <h2 className="text-base font-semibold text-ink">User Profile</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Full Name</label>
              <input defaultValue="Demo User" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Email</label>
              <input defaultValue="demo@solarflow.io" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Role</label>
              <input defaultValue="Energy Manager" disabled className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm bg-gray-50 text-gray-400" />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Organization</label>
              <input defaultValue="SolarFlow Turkey" disabled className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm bg-gray-50 text-gray-400" />
            </div>
          </div>
          <button className="px-6 py-2.5 bg-ink text-white text-sm font-semibold rounded-xl hover:bg-black transition-colors">
            Update Profile
          </button>
        </motion.div>
      )}

      {/* Notifications */}
      {activeTab === "notifications" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-4">
          <h2 className="text-base font-semibold text-ink">Notification Preferences</h2>
          {["Battery Low Alert", "High Grid Price Alert", "Device Offline Alert", "Daily Energy Report", "Weekly Summary", "AI Recommendations"].map((item) => (
            <div key={item} className="flex items-center justify-between py-3 border-b border-gray-50 last:border-0">
              <span className="text-sm text-ink">{item}</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked className="sr-only peer" />
                <div className="w-9 h-5 bg-gray-200 peer-checked:bg-primary-green rounded-full peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all" />
              </label>
            </div>
          ))}
        </motion.div>
      )}

      {/* Security */}
      {activeTab === "security" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-5">
          <h2 className="text-base font-semibold text-ink">Security Settings</h2>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Current Password</label>
            <input type="password" placeholder="••••••••" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">New Password</label>
            <input type="password" placeholder="••••••••" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm" />
          </div>
          <button className="px-6 py-2.5 bg-ink text-white text-sm font-semibold rounded-xl hover:bg-black transition-colors">
            Change Password
          </button>
          <div className="pt-4 border-t border-gray-100">
            <h3 className="text-sm font-semibold text-ink mb-2">Two-Factor Authentication</h3>
            <p className="text-xs text-gray-500">Add an extra layer of security to your account.</p>
            <button className="mt-3 px-4 py-2 border border-gray-200 rounded-xl text-sm font-medium text-ink hover:bg-gray-50 transition-colors">
              Enable 2FA
            </button>
          </div>
        </motion.div>
      )}

      {/* Devices */}
      {activeTab === "devices" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100">
          <h2 className="text-base font-semibold text-ink mb-4">Connected Devices</h2>
          <div className="space-y-3">
            {[
              { name: "Solar Inverter 01", type: "SMA Sunny Tripower", status: "Online" },
              { name: "Battery System 01", type: "BYD HVS 10.0", status: "Online" },
              { name: "Grid Meter 01", type: "Janitza UMG 96RM", status: "Online" },
            ].map((device) => (
              <div key={device.name} className="flex items-center justify-between py-3 px-4 rounded-xl bg-gray-50">
                <div>
                  <p className="text-sm font-semibold text-ink">{device.name}</p>
                  <p className="text-xs text-gray-400">{device.type}</p>
                </div>
                <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-primary-green/10 text-primary-green">
                  {device.status}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Language */}
      {activeTab === "locale" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-white rounded-2xl p-6 border border-gray-100 space-y-4">
          <h2 className="text-base font-semibold text-ink">Language & Region</h2>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Display Language</label>
            <select defaultValue="en" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm">
              <option value="en">English</option>
              <option value="tr">Türkçe</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Date Format</label>
            <select defaultValue="eu" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm">
              <option value="eu">DD/MM/YYYY</option>
              <option value="us">MM/DD/YYYY</option>
              <option value="iso">YYYY-MM-DD</option>
            </select>
          </div>
          <button className="px-6 py-2.5 bg-ink text-white text-sm font-semibold rounded-xl hover:bg-black transition-colors">
            Save Preferences
          </button>
        </motion.div>
      )}
    </div>
  );
}
