"use client";

import { useState } from "react";
import Sidebar from "@/components/dashboard/Sidebar";
import Topbar from "@/components/dashboard/Topbar";
import { AuthProvider } from "@/lib/auth/AuthContext";
import { FactoryProvider } from "@/lib/factory/FactoryContext";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <AuthProvider>
      <FactoryProvider>
        <div className="flex min-h-screen bg-mist/30">
          <Sidebar mobileOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />

          <div className="flex-1 flex flex-col min-w-0">
            <Topbar onMenuClick={() => setMobileNavOpen(true)} />

            <main className="flex-1 px-5 lg:px-8 py-6 lg:py-8 space-y-6 lg:space-y-8">
              {children}
            </main>
          </div>
        </div>
      </FactoryProvider>
    </AuthProvider>
  );
}
