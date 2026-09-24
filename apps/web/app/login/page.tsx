"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import Link from "next/link";
import { Package } from "lucide-react";
import { motion } from "framer-motion";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.auth.login(form);
      const user = await api.auth.me();
      
      switch (user.role) {
        case "super_admin": router.push("/dashboard/admin"); break;
        case "ngo_admin": router.push("/dashboard/ngo"); break;
        case "donor": router.push("/dashboard/donor"); break;
        case "volunteer": router.push("/dashboard/volunteer"); break;
        case "beneficiary": router.push("/dashboard/beneficiary"); break;
        default: router.push("/dashboard");
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#F8FAFC] to-emerald-50 flex flex-col justify-center items-center p-6 font-sans">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Link href="/" className="mb-8 flex items-center gap-3 hover:scale-105 transition-transform duration-300 group">
          <div className="bg-gradient-to-br from-emerald-500 to-teal-600 p-2.5 rounded-xl shadow-lg group-hover:shadow-emerald-500/30 transition-all">
            <Package className="w-6 h-6 text-white" />
          </div>
          <div className="flex flex-col pt-1">
            <span className="font-medium text-gray-900 text-2xl tracking-tighter leading-none group-hover:text-emerald-700 transition-colors">SDDS</span>
            <span className="text-[9px] font-medium text-emerald-600 uppercase tracking-widest mt-0.5">SMART DONATION DISTRIBUTION SYSTEM</span>
          </div>
        </Link>
      </motion.div>

      <motion.main 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="w-full max-w-md bg-white/80 backdrop-blur-xl border border-white/50 rounded-2xl shadow-xl overflow-hidden"
      >
        <div className="p-8">
          <h1 className="text-3xl font-medium bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">Welcome back</h1>
          <p className="text-gray-500 text-sm mt-2 font-medium">Enter your credentials to access your account</p>
          
          <form onSubmit={onSubmit} className="mt-8 space-y-5">
            <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email address</label>
              <input
                required
                type="email"
                placeholder="name@example.com"
                className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all bg-gray-50/50 focus:bg-white"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </motion.div>
            
            <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
              <div className="flex justify-between items-center mb-1.5">
                <label className="block text-sm font-semibold text-gray-700">Password</label>
                <Link href="#" className="text-xs font-medium text-emerald-600 hover:text-emerald-700">Forgot password?</Link>
              </div>
              <input
                required
                type="password"
                placeholder="••••••••"
                className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all bg-gray-50/50 focus:bg-white"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </motion.div>

            {error && (
              <motion.p 
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="text-sm text-red-500 font-medium p-3 bg-red-50 rounded-lg border border-red-100"
              >
                {error}
              </motion.p>
            )}
            
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 py-3 font-semibold text-white hover:from-emerald-600 hover:to-teal-700 disabled:opacity-50 transition-all shadow-md shadow-emerald-500/20 mt-4"
            >
              {loading ? "Signing in..." : "Sign In"}
            </motion.button>
          </form>
        </div>
        
        <div className="border-t border-gray-100 p-6 text-center bg-gray-50/50">
          <p className="text-sm text-gray-600 font-medium">
            Don't have an account? <Link href="/register" className="text-emerald-600 font-medium hover:text-emerald-700 hover:underline decoration-emerald-500/30 underline-offset-4 transition-all">Create an account</Link>
          </p>
        </div>
      </motion.main>
    </div>
  );
}
