"use client";

import { useEffect, useState } from "react";
import { api, ApiError, DonationCategory, BeneficiaryRequest } from "@/lib/api";
import { motion } from "framer-motion";
import { HeartHandshake, AlertCircle, Send, Clock, CheckCircle2, XCircle, Layers, FileText, Search, RefreshCw } from "lucide-react";

const STATUS_LABELS: Record<string, string> = {
  submitted: "Submitted",
  under_review: "Under Review",
  approved: "Approved",
  fulfilled: "Fulfilled",
  rejected: "Rejected",
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  submitted: <Send className="w-4 h-4 text-blue-500" />,
  under_review: <Search className="w-4 h-4 text-purple-500" />,
  approved: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
  fulfilled: <HeartHandshake className="w-4 h-4 text-teal-500" />,
  rejected: <XCircle className="w-4 h-4 text-red-500" />,
};

const STATUS_COLORS: Record<string, string> = {
  submitted: "bg-blue-50 text-blue-700 border-blue-200",
  under_review: "bg-purple-50 text-purple-700 border-purple-200",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  fulfilled: "bg-teal-50 text-teal-700 border-teal-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
};

export default function BeneficiaryDashboardPage() {
  const [beneficiaryId, setBeneficiaryId] = useState<string | null>(null);
  const [requests, setRequests] = useState<BeneficiaryRequest[]>([]);
  const [categories, setCategories] = useState<DonationCategory[]>([]);
  const [form, setForm] = useState({ category_id: "", quantity_requested: 1 });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    setLoading(true);
    setError(null);
    Promise.all([api.beneficiaries.me(), api.categories.list()])
      .then(([me, cats]) => {
        setBeneficiaryId(me.id);
        setCategories(cats);
        if (cats.length > 0) setForm((f) => ({ ...f, category_id: cats[0].id }));
        return api.beneficiaries.myRequests(me.id);
      })
      .then((reqs) => reqs && setRequests(reqs))
      .catch((err) => {
        // Handle 404 cleanly since generic missing profile throws it
        if (err.message?.includes("404") || (err instanceof ApiError && err.code === "NOT_FOUND")) {
          setError("Your account isn't linked to a beneficiary profile yet. Please contact your NGO to have your profile set up.");
        } else {
          setError("Could not load your profile data.");
        }
      })
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function submitRequest(e: React.FormEvent) {
    e.preventDefault();
    if (!beneficiaryId) return;
    setError(null);
    setSubmitting(true);
    try {
      await api.beneficiaries.submitRequest(beneficiaryId, form);
      // reload requests
      const reqs = await api.beneficiaries.myRequests(beneficiaryId);
      setRequests(reqs);
      setForm((f) => ({ ...f, quantity_requested: 1 })); // reset quantity
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not submit request");
    } finally {
      setSubmitting(false);
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

  if (loading) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-emerald-600">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <p className="text-sm font-medium">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl font-sans pb-20">
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-medium text-gray-900 tracking-tight flex items-center gap-3">
          <div className="p-2.5 bg-brand-50 text-brand-600 rounded-xl">
            <HeartHandshake className="w-6 h-6" />
          </div>
          My Requests
        </h1>
        <p className="mt-2 text-sm font-medium text-gray-500">Request essential items and track their delivery status.</p>
      </motion.div>

      {error && (
        <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="mb-8 p-5 bg-red-50 border border-red-100 rounded-2xl flex items-start gap-3 text-red-600 shadow-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium">Access Restricted</h3>
            <p className="text-sm mt-1 text-red-500">{error}</p>
          </div>
        </motion.div>
      )}

      {beneficiaryId && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* LEFT: SUBMIT FORM */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="lg:col-span-1"
          >
            <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-[0_4px_20px_rgb(0,0,0,0.04)] relative overflow-hidden sticky top-8">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-400 to-emerald-400"></div>
              
              <h2 className="text-lg font-medium text-gray-900 mb-6 flex items-center gap-2">
                <Send className="w-5 h-5 text-brand-500" />
                Submit New Request
              </h2>

              <form onSubmit={submitRequest} className="space-y-5">
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                    <Layers className="w-4 h-4 text-gray-400" />
                    Category
                  </label>
                  <select
                    required
                    className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-gray-900 focus:border-brand-500 focus:ring-brand-500/20 transition-all font-medium bg-white"
                    value={form.category_id}
                    onChange={(e) => setForm({ ...form, category_id: e.target.value })}
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-1.5">
                    <FileText className="w-4 h-4 text-gray-400" />
                    Quantity Needed
                  </label>
                  <input
                    type="number"
                    min={1}
                    required
                    className="w-full rounded-xl border border-gray-200 px-4 py-2.5 text-gray-900 focus:border-brand-500 focus:ring-brand-500/20 transition-all font-medium"
                    value={form.quantity_requested}
                    onChange={(e) => setForm({ ...form, quantity_requested: Number(e.target.value) })}
                  />
                </div>

                <button 
                  type="submit" 
                  disabled={submitting || categories.length === 0}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-brand-500 to-emerald-600 text-white font-medium rounded-xl hover:from-brand-600 hover:to-emerald-700 focus:ring-4 focus:ring-brand-500/20 transition-all shadow-md shadow-brand-500/20 disabled:opacity-50 text-sm mt-2"
                >
                  {submitting ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      Submit Request
                      <Send className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </div>
          </motion.div>

          {/* RIGHT: REQUEST HISTORY */}
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="lg:col-span-2 space-y-4"
          >
            <h2 className="text-lg font-medium text-gray-900 mb-2 px-1">Request History</h2>
            
            {requests.length === 0 ? (
              <motion.div variants={itemVariants} className="bg-gray-50/50 border border-dashed border-gray-200 rounded-2xl p-10 text-center flex flex-col items-center justify-center">
                <Clock className="w-10 h-10 text-gray-300 mb-3" />
                <p className="text-sm font-medium text-gray-500">No requests submitted yet.</p>
                <p className="text-xs text-gray-400 mt-1">Submit a request on the left to get started.</p>
              </motion.div>
            ) : (
              requests.map((r) => {
                const category = categories.find(c => c.id === r.category_id);
                return (
                  <motion.div 
                    variants={itemVariants}
                    key={r.id} 
                    className="flex items-center justify-between rounded-2xl border border-gray-100 bg-white p-5 shadow-[0_4px_20px_rgb(0,0,0,0.02)] hover:shadow-md transition-all duration-300 group"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-xl border ${STATUS_COLORS[r.status] || 'bg-gray-50 text-gray-500 border-gray-200'}`}>
                        {STATUS_ICONS[r.status] || <Clock className="w-5 h-5" />}
                      </div>
                      <div>
                        <h3 className="font-medium text-gray-900 text-base">{category?.name || "Item"} Request</h3>
                        <p className="text-sm text-gray-500 mt-0.5">Quantity: <span className="font-medium text-gray-700">{r.quantity_requested}</span></p>
                      </div>
                    </div>
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[r.status] || 'bg-gray-100 text-gray-700'}`}>
                      {STATUS_LABELS[r.status] ?? r.status}
                    </span>
                  </motion.div>
                );
              })
            )}
          </motion.div>

        </div>
      )}
    </div>
  );
}
