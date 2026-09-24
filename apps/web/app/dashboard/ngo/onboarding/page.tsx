"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { api, ApiError } from "@/lib/api";
import { Building2 } from "lucide-react";
import { useCurrentUser } from "@/lib/useCurrentUser";

export default function NgoOnboardingPage() {
  const router = useRouter();
  const { user } = useCurrentUser();
  const [form, setForm] = useState({ name: "", description: "", contact_email: "", contact_phone: "", address: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (user?.organization_id) {
    router.push("/dashboard/ngo");
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.organizations.create(form);
      // Force reload to grab the new user profile with organization_id
      window.location.href = "/dashboard/ngo";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to register NGO");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl font-sans mt-10">
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 text-center"
      >
        <div className="bg-emerald-50 text-emerald-600 p-4 rounded-full inline-block mb-4 shadow-sm">
          <Building2 size={32} />
        </div>
        <h1 className="text-3xl font-medium text-gray-900 tracking-tight">Register Your NGO</h1>
        <p className="mt-2 text-sm font-medium text-gray-500">Welcome to SDDS! Please set up your organization profile to continue.</p>
      </motion.div>

      <div className="bg-white rounded-2xl border border-gray-100 p-8 shadow-[0_4px_20px_rgb(0,0,0,0.03)]">
        {error && (
          <div className="mb-6 p-4 bg-red-50 text-red-600 rounded-lg text-sm font-medium border border-red-100">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Organization Name <span className="text-red-500">*</span></label>
            <input
              required
              className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              placeholder="e.g. Hope Foundation"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
            <textarea
              rows={3}
              className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all resize-none"
              placeholder="Briefly describe your NGO's mission..."
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Contact Email</label>
              <input
                type="email"
                className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="contact@ngo.org"
                value={form.contact_email}
                onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Contact Phone</label>
              <input
                className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                placeholder="+1 234 567 8900"
                value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Headquarters Address</label>
            <input
              className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
              placeholder="123 Main St, City, Country"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-4 py-3 text-sm font-medium transition-colors shadow-sm shadow-emerald-600/20 disabled:opacity-50"
          >
            {loading ? "Registering..." : "Complete Registration"}
          </button>
        </form>
      </div>
    </div>
  );
}
