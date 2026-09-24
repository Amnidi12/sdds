"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import { Package, ShieldCheck, Activity, Users, Truck } from "lucide-react";
import { api } from "@/lib/api";
import { motion } from "framer-motion";

export default function HomePage() {
  const [trackingId, setTrackingId] = useState("");
  const [stats, setStats] = useState({ processed_kg: 0, active_ngos: 0, beneficiaries: 0, active_fleets: 0 });

  useEffect(() => {
    api.public.stats()
      .then((res) => setStats(res))
      .catch(() => {
        // Backend unavailable — keep default zeros, no error shown to user
      });
  }, []);

  const handleTrack = (e: React.FormEvent) => {
    e.preventDefault();
    if (trackingId) {
      window.location.href = `/track?id=${encodeURIComponent(trackingId.trim())}`;
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  } as const;

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  } as const;

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F8FAFC] to-white flex flex-col font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Top Navbar */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-100 h-16 flex items-center justify-between px-6 lg:px-12 sticky top-0 z-50 transition-all duration-300">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-3 group">
            <motion.div 
              whileHover={{ rotate: 5, scale: 1.05 }}
              className="bg-gradient-to-br from-emerald-500 to-teal-600 p-2 rounded-lg shadow-md group-hover:shadow-emerald-500/30 transition-all duration-300"
            >
              <Package className="w-5 h-5 text-white" />
            </motion.div>
            <div className="flex flex-col pt-1">
              <span className="font-medium text-gray-900 text-2xl tracking-tighter leading-none">SDDS</span>
              <span className="text-[9px] font-medium text-gray-500 uppercase tracking-widest mt-0.5 hidden sm:block">SMART DONATION DISTRIBUTION SYSTEM</span>
            </div>
          </Link>
          <nav className="hidden md:flex gap-6">
            <Link href="/" className="text-gray-900 font-medium text-sm border-b-2 border-emerald-500 pb-1">Portal</Link>
            <Link href="/track" className="text-gray-500 hover:text-gray-900 font-medium text-sm transition-colors pb-1 border-b-2 border-transparent hover:border-gray-300">Tracking</Link>
          </nav>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/login" className="text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors">Sign In</Link>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link href="/register" className="bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white px-5 py-2.5 rounded-lg font-medium text-sm transition-all shadow-md shadow-emerald-500/20">
              Create Account
            </Link>
          </motion.div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-12">
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 tracking-tight">Public Portal</h1>
          <p className="text-gray-500 mt-2 text-base font-medium">Smart Donation Distribution System operational interface.</p>
        </motion.div>

        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 lg:grid-cols-3 gap-6"
        >
          {/* Left Column */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Track Donation Card */}
            <motion.div variants={itemVariants} className="bg-white rounded-2xl overflow-hidden shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/50 hover:shadow-[0_8px_30px_rgb(16,185,129,0.05)] transition-shadow duration-300">
              <div className="border-b border-gray-50 px-6 py-4 flex items-center gap-3 bg-gradient-to-r from-gray-50/50 to-white">
                <div className="bg-emerald-100 text-emerald-600 p-1.5 rounded-md">
                  <Activity className="w-4 h-4" />
                </div>
                <h2 className="font-medium text-gray-900 text-sm tracking-wide">TRACK DONATION</h2>
              </div>
              <div className="p-8">
                <p className="text-gray-500 text-sm mb-5 font-medium">Enter a tracking ID to verify the real-time location and status of a contribution.</p>
                <form onSubmit={handleTrack} className="flex gap-4">
                  <input
                    type="text"
                    value={trackingId}
                    onChange={(e) => setTrackingId(e.target.value)}
                    placeholder="e.g. TRK-ABC-123"
                    className="flex-1 border-2 border-gray-100 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-4 focus:ring-emerald-500/10 focus:border-emerald-500 font-mono transition-all"
                  />
                  <motion.button 
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    type="submit" 
                    className="bg-emerald-100 hover:bg-emerald-200 text-emerald-800 px-8 py-3 rounded-xl font-medium text-sm transition-colors shadow-sm"
                  >
                    Track
                  </motion.button>
                </form>
              </div>
            </motion.div>

            {/* Two Action Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <motion.div 
                variants={itemVariants}
                whileHover={{ y: -5, scale: 1.01 }}
                className="bg-white rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/50 hover:border-emerald-200 hover:shadow-[0_8px_30px_rgb(16,185,129,0.08)] transition-all duration-300 cursor-pointer group" 
                onClick={() => window.location.href='/login'}
              >
                <div className="flex gap-4 items-start">
                  <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-100 group-hover:bg-emerald-500 group-hover:text-white transition-colors duration-300 text-emerald-600">
                    <ShieldCheck className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 text-base group-hover:text-emerald-700 transition-colors">Access Dashboard</h3>
                    <p className="text-gray-500 text-sm mt-1.5 leading-relaxed font-medium">For NGOs, Volunteers, and Administrators.</p>
                  </div>
                </div>
              </motion.div>

              <motion.div 
                variants={itemVariants}
                whileHover={{ y: -5, scale: 1.01 }}
                className="bg-white rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/50 hover:border-emerald-200 hover:shadow-[0_8px_30px_rgb(16,185,129,0.08)] transition-all duration-300 cursor-pointer group" 
                onClick={() => window.location.href='/register'}
              >
                <div className="flex gap-4 items-start">
                  <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-100 group-hover:bg-emerald-500 group-hover:text-white transition-colors duration-300 text-emerald-600">
                    <Package className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 text-base group-hover:text-emerald-700 transition-colors">Donate Resources</h3>
                    <p className="text-gray-500 text-sm mt-1.5 leading-relaxed font-medium">Create an account to submit new donations.</p>
                  </div>
                </div>
              </motion.div>
            </div>
          </div>

          {/* Right Column (Metrics) */}
          <motion.div variants={itemVariants} className="bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100/50 overflow-hidden">
            <div className="border-b border-gray-50 px-6 py-4 flex items-center gap-3 bg-gradient-to-r from-gray-50/50 to-white">
              <div className="bg-blue-100 text-blue-600 p-1.5 rounded-md">
                <Activity className="w-4 h-4" />
              </div>
              <h2 className="font-medium text-gray-900 text-sm tracking-wide">SYSTEM METRICS</h2>
            </div>
            <div className="divide-y divide-gray-50/80">
              <motion.div whileHover={{ backgroundColor: "rgba(248, 250, 252, 1)" }} className="px-6 py-5 flex items-center gap-5 transition-colors">
                <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-100/50 text-emerald-600">
                  <Package className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">PROCESSED</p>
                  <p className="text-xl font-medium text-gray-900 mt-0.5">{stats.processed_kg.toLocaleString()} <span className="text-sm font-medium text-gray-500">kg</span></p>
                </div>
              </motion.div>
              
              <motion.div whileHover={{ backgroundColor: "rgba(248, 250, 252, 1)" }} className="px-6 py-5 flex items-center gap-5 transition-colors">
                <div className="bg-blue-50 p-3 rounded-xl border border-blue-100/50 text-blue-600">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">ACTIVE NGOS</p>
                  <p className="text-xl font-medium text-gray-900 mt-0.5">{stats.active_ngos.toLocaleString()}</p>
                </div>
              </motion.div>
              
              <motion.div whileHover={{ backgroundColor: "rgba(248, 250, 252, 1)" }} className="px-6 py-5 flex items-center gap-5 transition-colors">
                <div className="bg-purple-50 p-3 rounded-xl border border-purple-100/50 text-purple-600">
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">BENEFICIARIES</p>
                  <p className="text-xl font-medium text-gray-900 mt-0.5">{stats.beneficiaries.toLocaleString()}<span className="text-emerald-500">+</span></p>
                </div>
              </motion.div>
              
              <motion.div whileHover={{ backgroundColor: "rgba(248, 250, 252, 1)" }} className="px-6 py-5 flex items-center gap-5 transition-colors">
                <div className="bg-amber-50 p-3 rounded-xl border border-amber-100/50 text-amber-600">
                  <Truck className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-[11px] font-medium text-gray-400 tracking-widest uppercase">ACTIVE FLEETS</p>
                  <p className="text-xl font-medium text-gray-900 mt-0.5">{stats.active_fleets.toLocaleString()}</p>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row items-center justify-center gap-8">
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500 font-medium">
            <span>© All rights reserved by Smart Donation System</span>
            <span className="hidden md:inline text-gray-300">|</span>
            <span>Designed by amndy</span>
            <span className="hidden md:inline text-gray-300">|</span>
            <Link href="/track" className="hover:text-emerald-600 transition-colors font-medium">Track a Donation</Link>
            <Link href="/login" className="hover:text-emerald-600 transition-colors font-medium">Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
