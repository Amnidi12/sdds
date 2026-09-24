"use client";

import { useEffect, useState } from "react";
import { api, ApiError, Distribution, PickupTask } from "@/lib/api";
import { motion } from "framer-motion";
import { Truck, Package, Clock, CheckCircle2, ArrowRight, MapPin, AlertCircle, RefreshCw } from "lucide-react";

const PICKUP_LABELS: Record<string, string> = {
  assigned: "Assigned",
  accepted: "Accepted",
  en_route: "En Route",
  arrived: "Arrived",
  picked_up: "Picked Up",
  failed: "Failed",
  completed: "Completed",
};

const PICKUP_NEXT: Record<string, string> = {
  assigned: "accepted",
  accepted: "en_route",
  en_route: "arrived",
  arrived: "picked_up",
  picked_up: "completed",
};

const DIST_LABELS: Record<string, string> = {
  reserved: "Reserved",
  dispatched: "Dispatched",
  delivered: "Delivered",
};

const DIST_NEXT: Record<string, string> = {
  dispatched: "delivered",
};

export default function VolunteerDashboardPage() {
  const [pickups, setPickups] = useState<PickupTask[]>([]);
  const [distributions, setDistributions] = useState<Distribution[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  function load() {
    setLoading(true);
    Promise.all([api.pickups.list(), api.distributions.list()])
      .then(([p, d]) => {
        setPickups(p.filter((t) => t.status !== "completed" && t.status !== "failed"));
        setDistributions(d.filter((dist) => ["dispatched", "delivered"].includes(dist.status)));
      })
      .catch(() => setError("Could not load your tasks."))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function advancePickup(id: string, newStatus: string) {
    setBusyId(id);
    setError(null);
    try {
      await api.pickups.updateStatus(id, newStatus);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update task");
    } finally {
      setBusyId(null);
    }
  }

  async function advanceDistribution(id: string, newStatus: string) {
    setBusyId(id);
    setError(null);
    try {
      await api.distributions.updateStatus(id, newStatus);
      if (newStatus === "delivered") {
        await api.distributions.submitProof(id, { note: "Delivered by volunteer via app" });
      }
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update distribution");
    } finally {
      setBusyId(null);
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="mx-auto max-w-5xl font-sans">
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
      >
        <div>
          <h1 className="text-3xl font-medium text-gray-900 tracking-tight">My Tasks</h1>
          <p className="mt-2 text-sm font-medium text-gray-500">Pickups and deliveries assigned to you.</p>
        </div>
        <button 
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-xl text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 disabled:opacity-50 transition-all shadow-sm"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-500' : ''}`} />
          Refresh Tasks
        </button>
      </motion.div>

      {error && (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="mb-8 p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-600">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm font-medium">{error}</p>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* PICKUPS COLUMN */}
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="flex flex-col gap-4">
          <div className="flex items-center gap-3 pb-2 border-b border-gray-100">
            <div className="bg-amber-50 text-amber-600 p-2 rounded-lg">
              <Package className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-medium text-gray-900">Active Pickups</h2>
            <span className="ml-auto bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full text-xs font-medium">{pickups.length}</span>
          </div>

          {!loading && pickups.length === 0 && (
            <motion.div variants={itemVariants} className="bg-gray-50/50 border border-dashed border-gray-200 rounded-2xl p-10 text-center flex flex-col items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-sm font-medium text-gray-500">No active pickup tasks.</p>
              <p className="text-xs text-gray-400 mt-1">You're all caught up!</p>
            </motion.div>
          )}

          {pickups.map((t) => {
            const next = PICKUP_NEXT[t.status];
            return (
              <motion.div 
                variants={itemVariants}
                key={t.id} 
                className="bg-white rounded-2xl border border-gray-100 p-5 shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:shadow-lg transition-all duration-300 relative overflow-hidden group"
              >
                <div className="absolute top-0 left-0 w-1 h-full bg-amber-400"></div>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100/50 mb-3">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                      {PICKUP_LABELS[t.status] ?? t.status}
                    </span>
                    <h3 className="font-medium text-gray-900 text-base">Pickup #{t.id.slice(0, 8)}</h3>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-gray-500 font-medium mb-5 bg-gray-50/50 p-3 rounded-xl border border-gray-100">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span>Updated Recently</span>
                  </div>
                </div>

                {next && (
                  <button
                    disabled={busyId === t.id}
                    onClick={() => advancePickup(t.id, next)}
                    className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 px-4 py-3 text-sm font-medium text-white hover:from-amber-600 hover:to-orange-600 focus:ring-4 focus:ring-amber-500/20 disabled:opacity-50 transition-all shadow-md shadow-amber-500/20 group-hover:shadow-amber-500/30"
                  >
                    {busyId === t.id ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        Mark as {PICKUP_LABELS[next]}
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                )}
              </motion.div>
            );
          })}
        </motion.div>

        {/* DELIVERIES COLUMN */}
        <motion.div variants={containerVariants} initial="hidden" animate="show" className="flex flex-col gap-4">
          <div className="flex items-center gap-3 pb-2 border-b border-gray-100">
            <div className="bg-emerald-50 text-emerald-600 p-2 rounded-lg">
              <Truck className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-medium text-gray-900">Active Deliveries</h2>
            <span className="ml-auto bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full text-xs font-medium">{distributions.length}</span>
          </div>

          {!loading && distributions.length === 0 && (
            <motion.div variants={itemVariants} className="bg-gray-50/50 border border-dashed border-gray-200 rounded-2xl p-10 text-center flex flex-col items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-gray-300 mb-3" />
              <p className="text-sm font-medium text-gray-500">No active deliveries.</p>
              <p className="text-xs text-gray-400 mt-1">Pending items will appear here.</p>
            </motion.div>
          )}

          {distributions.map((d) => {
            const next = DIST_NEXT[d.status];
            return (
              <motion.div 
                variants={itemVariants}
                key={d.id} 
                className="bg-white rounded-2xl border border-gray-100 p-5 shadow-[0_4px_20px_rgb(0,0,0,0.03)] hover:shadow-lg transition-all duration-300 relative overflow-hidden group"
              >
                <div className="absolute top-0 left-0 w-1 h-full bg-emerald-400"></div>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100/50 mb-3">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      {DIST_LABELS[d.status] ?? d.status}
                    </span>
                    <h3 className="font-medium text-gray-900 text-base">Delivery #{d.id.slice(0, 8)}</h3>
                  </div>
                </div>
                
                <div className="flex items-center gap-4 text-sm text-gray-500 font-medium mb-5 bg-gray-50/50 p-3 rounded-xl border border-gray-100">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    <span>Awaiting Drop-off</span>
                  </div>
                </div>

                {next && (
                  <button
                    disabled={busyId === d.id}
                    onClick={() => advanceDistribution(d.id, next)}
                    className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 px-4 py-3 text-sm font-medium text-white hover:from-emerald-600 hover:to-teal-700 focus:ring-4 focus:ring-emerald-500/20 disabled:opacity-50 transition-all shadow-md shadow-emerald-500/20 group-hover:shadow-emerald-500/30"
                  >
                    {busyId === d.id ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <>
                        Mark as {DIST_LABELS[next]}
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                )}
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </div>
  );
}
