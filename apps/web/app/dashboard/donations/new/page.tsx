"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { motion } from "framer-motion";
import { ArrowLeft, PackagePlus, MapPin, AlignLeft, Layers, Hash } from "lucide-react";
import Link from "next/link";

export default function NewDonationPage() {
  const router = useRouter();
  const [categories, setCategories] = useState<any[]>([]);
  const [form, setForm] = useState({
    title: "",
    description: "",
    category_id: "",
    quantity: 1,
    unit: "items",
    pickup_required: true,
    pickup_address: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetchingCategories, setFetchingCategories] = useState(true);

  useEffect(() => {
    api.categories.list()
      .then(setCategories)
      .catch(() => setError("Could not load categories"))
      .finally(() => setFetchingCategories(false));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    
    if (!form.category_id) {
      setError("Please select a category.");
      setLoading(false);
      return;
    }

    try {
      await api.donations.create(form);
      router.push("/dashboard/donor");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create donation");
    } finally {
      setLoading(false);
    }
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  } as const;

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  } as const;

  return (
    <div className="mx-auto max-w-2xl font-sans pb-20">
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <Link 
          href="/dashboard/donor" 
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
        <h1 className="text-3xl font-medium text-gray-900 tracking-tight flex items-center gap-3">
          <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl">
            <PackagePlus className="w-6 h-6" />
          </div>
          Offer a Donation
        </h1>
        <p className="mt-2 text-sm font-medium text-gray-500">Provide details about the items you wish to donate.</p>
      </motion.div>

      {error && (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-600">
          <p className="text-sm font-medium">{error}</p>
        </motion.div>
      )}

      <motion.form 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        onSubmit={onSubmit} 
        className="bg-white border border-gray-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl p-6 sm:p-8 space-y-6 relative overflow-hidden"
      >
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-teal-400"></div>

        <motion.div variants={itemVariants} className="space-y-4">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <AlignLeft className="w-4 h-4 text-gray-400" />
              Donation Title
            </label>
            <input
              required
              placeholder="e.g., Winter Jackets"
              className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500/20 transition-all font-medium placeholder:font-normal placeholder:text-gray-400"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <AlignLeft className="w-4 h-4 text-gray-400" />
              Description
            </label>
            <textarea
              required
              rows={3}
              placeholder="Describe the condition, sizes, or any other relevant details..."
              className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500/20 transition-all font-medium placeholder:font-normal placeholder:text-gray-400 resize-none"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-2">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <Layers className="w-4 h-4 text-gray-400" />
              Category
            </label>
            <select
              required
              disabled={fetchingCategories}
              className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500/20 transition-all font-medium bg-white disabled:bg-gray-50 disabled:text-gray-500"
              value={form.category_id}
              onChange={(e) => setForm({ ...form, category_id: e.target.value })}
            >
              <option value="" disabled>Select a category...</option>
              {categories.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
              <Hash className="w-4 h-4 text-gray-400" />
              Quantity & Unit
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                min="1"
                required
                className="w-1/2 rounded-xl border border-gray-200 px-4 py-2.5 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500/20 transition-all font-medium"
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: parseInt(e.target.value) || 1 })}
              />
              <select
                className="w-1/2 rounded-xl border border-gray-200 px-4 py-2.5 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500/20 transition-all font-medium bg-white"
                value={form.unit}
                onChange={(e) => setForm({ ...form, unit: e.target.value })}
              >
                <option value="items">Items</option>
                <option value="boxes">Boxes</option>
                <option value="kg">Kg</option>
                <option value="liters">Liters</option>
              </select>
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="pt-2">
          <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
            <MapPin className="w-4 h-4 text-gray-400" />
            Pickup Address
          </label>
          <input
            required
            placeholder="Where should volunteers pick this up?"
            className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-gray-900 focus:border-emerald-500 focus:ring-emerald-500/20 transition-all font-medium placeholder:font-normal placeholder:text-gray-400"
            value={form.pickup_address}
            onChange={(e) => setForm({ ...form, pickup_address: e.target.value })}
          />
        </motion.div>

        <motion.div variants={itemVariants} className="pt-6 border-t border-gray-100">
          <button
            type="submit"
            disabled={loading || fetchingCategories}
            className="w-full flex items-center justify-center py-3.5 px-4 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-medium rounded-xl hover:from-emerald-600 hover:to-teal-700 focus:ring-4 focus:ring-emerald-500/20 transition-all shadow-md shadow-emerald-500/20 disabled:opacity-50 text-sm"
          >
            {loading ? "Submitting..." : "Submit Donation"}
          </button>
        </motion.div>
      </motion.form>
    </div>
  );
}
