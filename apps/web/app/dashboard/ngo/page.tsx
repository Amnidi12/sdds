"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Package, Truck, Warehouse, Users, Activity } from "lucide-react";
import { api, Donation } from "@/lib/api";

export default function NgoOverviewPage() {
  const [pending, setPending] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.donations
      .list({ status: "pending_review" })
      .then(setPending)
      .finally(() => setLoading(false));
  }, []);

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
        className="mb-8"
      >
        <h1 className="text-3xl font-medium text-gray-900 tracking-tight">NGO Overview</h1>
        <p className="mt-2 text-sm font-medium text-gray-500">Everything that needs your attention today.</p>
      </motion.div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4"
      >
        <Link href="/dashboard/ngo/donations" className="block group">
          <motion.div variants={itemVariants} whileHover={{ y: -4, scale: 1.01 }} className="bg-white rounded-2xl border border-gray-100 p-6 shadow-[0_4px_20px_rgb(0,0,0,0.03)] group-hover:shadow-lg transition-all duration-300">
            <div className="flex items-start justify-between">
              <div className="bg-amber-50 border border-amber-100 text-amber-600 p-3 rounded-xl">
                <Package size={22} strokeWidth={2.5} />
              </div>
            </div>
            <div className="mt-5">
              <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">Pending Review</p>
              <p className="mt-1 text-3xl font-medium text-gray-900 tracking-tight">{loading ? "..." : pending.length}</p>
            </div>
          </motion.div>
        </Link>
        
        <Link href="/dashboard/ngo/pickups" className="block group">
          <motion.div variants={itemVariants} whileHover={{ y: -4, scale: 1.01 }} className="bg-white rounded-2xl border border-gray-100 p-6 shadow-[0_4px_20px_rgb(0,0,0,0.03)] group-hover:shadow-lg transition-all duration-300">
            <div className="flex items-start justify-between">
              <div className="bg-blue-50 border border-blue-100 text-blue-600 p-3 rounded-xl">
                <Truck size={22} strokeWidth={2.5} />
              </div>
            </div>
            <div className="mt-5">
              <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">Pickups</p>
              <p className="mt-1 text-sm font-medium text-gray-500">Manage tasks</p>
            </div>
          </motion.div>
        </Link>

        <Link href="/dashboard/ngo/inventory" className="block group">
          <motion.div variants={itemVariants} whileHover={{ y: -4, scale: 1.01 }} className="bg-white rounded-2xl border border-gray-100 p-6 shadow-[0_4px_20px_rgb(0,0,0,0.03)] group-hover:shadow-lg transition-all duration-300">
            <div className="flex items-start justify-between">
              <div className="bg-teal-50 border border-teal-100 text-teal-600 p-3 rounded-xl">
                <Warehouse size={22} strokeWidth={2.5} />
              </div>
            </div>
            <div className="mt-5">
              <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">Inventory</p>
              <p className="mt-1 text-sm font-medium text-gray-500">Stock & warehouses</p>
            </div>
          </motion.div>
        </Link>

        <Link href="/dashboard/ngo/beneficiaries" className="block group">
          <motion.div variants={itemVariants} whileHover={{ y: -4, scale: 1.01 }} className="bg-white rounded-2xl border border-gray-100 p-6 shadow-[0_4px_20px_rgb(0,0,0,0.03)] group-hover:shadow-lg transition-all duration-300">
            <div className="flex items-start justify-between">
              <div className="bg-indigo-50 border border-indigo-100 text-indigo-600 p-3 rounded-xl">
                <Users size={22} strokeWidth={2.5} />
              </div>
            </div>
            <div className="mt-5">
              <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">Beneficiaries</p>
              <p className="mt-1 text-sm font-medium text-gray-500">Manage records</p>
            </div>
          </motion.div>
        </Link>
      </motion.div>

      <div className="mt-10">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Donations Awaiting Review</h2>
        
        {loading && <div className="text-sm font-medium text-gray-500 flex items-center gap-2"><div className="w-4 h-4 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" /> Loading...</div>}
        
        {!loading && pending.length === 0 && (
          <div className="mt-8 rounded-2xl border border-dashed border-gray-200 bg-gray-50/50 p-12 text-center">
            <div className="bg-white p-4 rounded-full inline-block shadow-sm mb-4">
              <Activity className="text-gray-400 w-8 h-8" />
            </div>
            <h3 className="text-gray-900 font-medium">You're all caught up!</h3>
            <p className="mt-1 text-sm font-medium text-gray-500">There are no pending donations to review right now.</p>
          </div>
        )}

        <div className="space-y-3">
          {pending.slice(0, 5).map((d) => (
            <motion.div 
              key={d.id} 
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-between rounded-xl border border-gray-100 bg-white p-5 shadow-sm hover:border-brand-100 hover:shadow-md transition-all"
            >
              <div className="flex items-center gap-4">
                <div className="bg-amber-50 p-3 rounded-lg text-amber-600 border border-amber-100">
                  <Package className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{d.title}</p>
                  <p className="text-xs font-medium text-gray-500 mt-1 uppercase tracking-wider">{d.tracking_id} · {d.quantity} {d.unit}</p>
                </div>
              </div>
              <Link href="/dashboard/ngo/donations" className="text-xs font-medium text-brand-600 bg-brand-50 hover:bg-brand-100 px-4 py-2 rounded-lg transition-colors">
                Review →
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
