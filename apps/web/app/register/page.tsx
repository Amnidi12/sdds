"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import Link from "next/link";
import { Package, CheckCircle2, XCircle, Eye, EyeOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

function PasswordStrength({ password }: { password: string }) {
  const checks = useMemo(() => ({
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    digit: /[0-9]/.test(password),
    special: /[^a-zA-Z0-9]/.test(password),
  }), [password]);

  if (!password) return null;

  const passed = Object.values(checks).filter(Boolean).length;
  const strengthLabel = ["", "Weak", "Fair", "Good", "Strong"][passed];
  const strengthColor = ["", "text-red-500", "text-amber-500", "text-blue-500", "text-emerald-500"][passed];
  const barColors = ["", "bg-red-400", "bg-amber-400", "bg-blue-400", "bg-emerald-400"][passed];

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-2 space-y-2"
    >
      {/* strength bar */}
      <div className="flex gap-1 h-1">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={`flex-1 rounded-full transition-all duration-300 ${i <= passed ? barColors : "bg-gray-200"}`}
          />
        ))}
      </div>
      <p className={`text-xs font-semibold ${strengthColor}`}>{strengthLabel}</p>

      {/* requirement checklist */}
      <ul className="space-y-1">
        {[
          { label: "At least 8 characters", ok: checks.length },
          { label: "One uppercase letter (A-Z)", ok: checks.uppercase },
          { label: "One number (0-9)", ok: checks.digit },
          { label: "One special character (!@#...)", ok: checks.special },
        ].map(({ label, ok }) => (
          <li key={label} className={`flex items-center gap-1.5 text-xs font-medium ${ok ? "text-emerald-600" : "text-gray-400"}`}>
            {ok ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
            {label}
          </li>
        ))}
      </ul>
    </motion.div>
  );
}

const ROLE_LABELS: Record<string, { label: string; desc: string }> = {
  donor: { label: "Donor", desc: "Offer items or funds to help NGOs" },
  volunteer: { label: "Volunteer", desc: "Pick up and deliver donations" },
  ngo_admin: { label: "NGO Administrator", desc: "Manage donations, inventory & distribution" },
  beneficiary: { label: "Beneficiary", desc: "Request items you need" },
};

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", full_name: "", role: "donor" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const passwordValid = useMemo(() => {
    const p = form.password;
    return p.length >= 8 && /[A-Z]/.test(p) && /[0-9]/.test(p) && /[^a-zA-Z0-9]/.test(p);
  }, [form.password]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!passwordValid) {
      setError("Your password does not meet the requirements listed below.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await api.auth.register(form);
      router.push("/login?registered=true");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed");
    } finally {
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
          <h1 className="text-3xl font-medium bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600">
            Create an account
          </h1>
          <p className="text-gray-500 text-sm mt-2 font-medium">Enter your details to get started</p>

          <form onSubmit={onSubmit} className="mt-8 space-y-5">
            {/* Full Name */}
            <motion.div whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Full Name</label>
              <input
                required
                minLength={2}
                placeholder="Jane Doe"
                className="w-full rounded-xl border border-gray-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all bg-gray-50/50 focus:bg-white"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </motion.div>

            {/* Email */}
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

            {/* Password */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Password</label>
              <div className="relative">
                <input
                  required
                  type={showPassword ? "text" : "password"}
                  placeholder="Min. 8 chars with uppercase, number & symbol"
                  className="w-full rounded-xl border border-gray-200 px-4 py-3 pr-11 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all bg-gray-50/50 focus:bg-white"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <AnimatePresence>
                {form.password && <PasswordStrength password={form.password} />}
              </AnimatePresence>
            </div>

            {/* Role */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Register as</label>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(ROLE_LABELS).map(([value, { label, desc }]) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setForm({ ...form, role: value })}
                    className={`text-left p-3 rounded-xl border-2 transition-all duration-200 ${
                      form.role === value
                        ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                        : "border-gray-100 bg-gray-50/50 text-gray-600 hover:border-gray-200"
                    }`}
                  >
                    <p className="text-xs font-semibold">{label}</p>
                    <p className="text-[10px] mt-0.5 opacity-70 leading-tight">{desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <AnimatePresence>
              {error && (
                <motion.p
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="text-sm text-red-500 font-medium p-3 bg-red-50 rounded-lg border border-red-100"
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 py-3 font-semibold text-white hover:from-emerald-600 hover:to-teal-700 disabled:opacity-50 transition-all shadow-md shadow-emerald-500/20 mt-2"
            >
              {loading ? "Creating account..." : "Create Account"}
            </motion.button>
          </form>
        </div>

        <div className="border-t border-gray-100 p-6 text-center bg-gray-50/50">
          <p className="text-sm text-gray-600 font-medium">
            Already have an account?{" "}
            <Link
              href="/login"
              className="text-emerald-600 font-medium hover:text-emerald-700 hover:underline decoration-emerald-500/30 underline-offset-4 transition-all"
            >
              Sign in
            </Link>
          </p>
        </div>
      </motion.main>
    </div>
  );
}
