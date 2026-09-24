"use client";

import { useEffect, useState } from "react";
import { Building2, Users, Package, Clock, CheckCircle2, Truck, BarChart3, Activity } from "lucide-react";
import { api, AdminStats } from "@/lib/api";
import { motion } from "framer-motion";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.admin
      .stats()
      .then(setStats)
      .catch(() => setError("Could not load platform stats."))
      .finally(() => setLoading(false));
  }, []);

  const cards = stats
    ? [
        { label: "Organizations", value: stats.organizations, icon: Building2, color: "emerald" },
        { label: "Active Users", value: stats.active_users, icon: Users, color: "blue" },
        { label: "Total Donations", value: stats.total_donations, icon: Package, color: "teal" },
        { label: "Pending Review", value: stats.pending_review, icon: Clock, color: "amber" },
        { label: "Completed Donations", value: stats.completed_donations, icon: CheckCircle2, color: "emerald" },
        { label: "Completed Distributions", value: stats.completed_distributions, icon: Truck, color: "indigo" },
      ]
    : [];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="mx-auto max-w-6xl font-sans">
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex items-center justify-between"
      >
        <div>
          <h1 className="text-3xl font-medium text-gray-900 tracking-tight">Platform Overview</h1>
          <p className="mt-2 text-sm font-medium text-gray-500">Real-time counts across the entire Smart Donation Distribution System.</p>
        </div>
        <div className="bg-emerald-50 border border-emerald-100 px-4 py-2 rounded-lg flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-600 animate-pulse" />
          <span className="text-sm font-medium text-emerald-700">Live Status</span>
        </div>
      </motion.div>

      {error && (
        <div className="mb-8 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-medium flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-2xl h-36 border border-gray-100 shadow-sm animate-pulse" />
          ))}
        </div>
      ) : (
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {cards.map((c) => {
            const Icon = c.icon;
            // Map colors to tailwind classes since dynamic concatenation can break PurgeCSS
            const bgColors = {
              emerald: "bg-emerald-50 border-emerald-100 text-emerald-600",
              blue: "bg-blue-50 border-blue-100 text-blue-600",
              teal: "bg-teal-50 border-teal-100 text-teal-600",
              amber: "bg-amber-50 border-amber-100 text-amber-600",
              indigo: "bg-indigo-50 border-indigo-100 text-indigo-600",
            };
            const colorClass = bgColors[c.color as keyof typeof bgColors] || bgColors.emerald;

            return (
              <motion.div 
                key={c.label} 
                variants={itemVariants}
                whileHover={{ y: -4, scale: 1.01 }}
                className="bg-white rounded-2xl border border-gray-100 p-6 shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:shadow-[0_8px_30px_rgb(16,185,129,0.06)] hover:border-emerald-100 transition-all duration-300"
              >
                <div className="flex items-start justify-between">
                  <div className={`p-3 rounded-xl border ${colorClass}`}>
                    <Icon size={22} strokeWidth={2.5} />
                  </div>
                  <BarChart3 className="w-4 h-4 text-gray-300" />
                </div>
                <div className="mt-5">
                  <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">{c.label}</p>
                  <p className="mt-1 text-3xl font-medium text-gray-900 tracking-tight">{c.value.toLocaleString()}</p>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </div>
  );
}
