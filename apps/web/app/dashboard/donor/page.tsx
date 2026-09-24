"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Package, Plus, Clock, CheckCircle2, Activity } from "lucide-react";
import { api, Donation } from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  pending_review: "Pending Review",
  approved: "Approved",
  pickup_scheduled: "Pickup Scheduled",
  picked_up: "Picked Up",
  received_at_warehouse: "Received at Warehouse",
  verified: "Verified",
  available: "Available",
  allocated: "Allocated",
  out_for_distribution: "Out for Distribution",
  delivered: "Delivered",
  completed: "Completed",
  rejected: "Rejected",
  cancelled: "Cancelled",
};

const STATUS_COLORS: Record<string, string> = {
  pending_review: "bg-amber-50 text-amber-700 border-amber-100",
  completed: "bg-emerald-50 text-emerald-700 border-emerald-100",
  rejected: "bg-red-50 text-red-700 border-red-100",
  cancelled: "bg-gray-50 text-gray-600 border-gray-100",
};

export default function DonorDashboardPage() {
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.donations
      .list()
      .then(setDonations)
      .catch(() => setError("Could not load donations."))
      .finally(() => setLoading(false));
  }, []);

  const completedCount = donations.filter((d) => d.status === "completed").length;
  const activeCount = donations.filter((d) => !["completed", "rejected", "cancelled"].includes(d.status)).length;

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
          <h1 className="text-3xl font-medium text-gray-900 tracking-tight">My Donations</h1>
          <p className="mt-2 text-sm font-medium text-gray-500">Track every donation from pickup to delivery.</p>
        </div>
        <Link
          href="/dashboard/donations/new"
          className="flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-700 transition-all shadow-sm hover:shadow-md"
        >
          <Plus size={18} /> New Donation
        </Link>
      </motion.div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-6 sm:grid-cols-3"
      >
        {[
          { label: "Total Donations", value: donations.length, icon: Package, color: "blue" },
          { label: "In Progress", value: activeCount, icon: Clock, color: "amber" },
          { label: "Completed", value: completedCount, icon: CheckCircle2, color: "emerald" },
        ].map((c) => {
          const Icon = c.icon;
          const colorClass = 
            c.color === "blue" ? "bg-blue-50 border-blue-100 text-blue-600" :
            c.color === "amber" ? "bg-amber-50 border-amber-100 text-amber-600" :
            "bg-emerald-50 border-emerald-100 text-emerald-600";

          return (
            <motion.div 
              key={c.label}
              variants={itemVariants}
              whileHover={{ y: -4, scale: 1.01 }}
              className="bg-white rounded-2xl border border-gray-100 p-6 shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:shadow-lg transition-all duration-300"
            >
              <div className="flex items-start justify-between">
                <div className={`p-3 rounded-xl border ${colorClass}`}>
                  <Icon size={22} strokeWidth={2.5} />
                </div>
                <Activity className="w-4 h-4 text-gray-300" />
              </div>
              <div className="mt-5">
                <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">{c.label}</p>
                <p className="mt-1 text-3xl font-medium text-gray-900 tracking-tight">{loading ? "..." : c.value}</p>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      <div className="mt-10">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Donation History</h2>
        
        {loading && <div className="text-sm font-medium text-gray-500 flex items-center gap-2"><div className="w-4 h-4 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" /> Loading...</div>}
        {error && <div className="p-4 rounded-xl bg-red-50 text-red-600 text-sm font-semibold border border-red-100">{error}</div>}

        {!loading && !error && donations.length === 0 && (
          <div className="mt-8 rounded-2xl border border-dashed border-gray-200 bg-gray-50/50 p-12 text-center">
            <div className="bg-white p-4 rounded-full inline-block shadow-sm mb-4">
              <Package className="text-gray-400 w-8 h-8" />
            </div>
            <h3 className="text-gray-900 font-medium">No donations found</h3>
            <p className="mt-1 text-sm font-medium text-gray-500">You haven&apos;t created any donations yet.</p>
          </div>
        )}

        <div className="space-y-3">
          {donations.map((d) => (
            <motion.div 
              key={d.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-between rounded-xl border border-gray-100 bg-white p-5 shadow-sm hover:border-brand-100 hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="bg-brand-50 p-3 rounded-lg text-brand-600">
                  <Package className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{d.title}</p>
                  <p className="text-xs font-medium text-gray-500 mt-1 uppercase tracking-wider">
                    {d.tracking_id} • {d.quantity} {d.unit}
                  </p>
                </div>
              </div>
              <span className={`rounded-full px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider border ${STATUS_COLORS[d.status] ?? "bg-brand-50 text-brand-700 border-brand-100"}`}>
                {STATUS_LABELS[d.status] ?? d.status}
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
