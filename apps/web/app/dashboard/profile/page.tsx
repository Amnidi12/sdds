"use client";

import { useEffect, useState } from "react";
import { useCurrentUser } from "@/lib/useCurrentUser";
import { api } from "@/lib/api";
import { motion } from "framer-motion";
import { User, Phone, Check, Loader2 } from "lucide-react";

export default function ProfilePage() {
  const { user, loading: userLoading } = useCurrentUser();
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || "");
      // We don't have phone in useCurrentUser context yet, so we could fetch /me again
      api.auth.me().then((me: any) => {
        if (me.phone) setPhone(me.phone);
      });
    }
  }, [user]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    setError(null);

    try {
      await api.auth.updateProfile({ full_name: fullName, phone });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to update profile");
    } finally {
      setSaving(false);
    }
  }

  if (userLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-medium text-gray-900 tracking-tight">Your Profile</h1>
        <p className="mt-2 text-sm font-medium text-gray-500">Update your personal information and contact details.</p>
      </motion.div>

      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <form onSubmit={handleSave} className="p-6 md:p-8 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-red-50 text-red-600 text-sm font-semibold border border-red-100">
              {error}
            </div>
          )}
          
          {success && (
            <div className="p-4 rounded-xl bg-emerald-50 text-emerald-600 text-sm font-semibold border border-emerald-100 flex items-center gap-2">
              <Check className="w-4 h-4" />
              Profile updated successfully
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
            <input 
              type="text" 
              value={user?.email} 
              disabled 
              className="w-full bg-gray-50 border border-gray-200 text-gray-500 text-sm rounded-xl px-4 py-3 focus:outline-none cursor-not-allowed" 
            />
            <p className="mt-1.5 text-xs text-gray-400 font-medium">Your email address cannot be changed.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="w-4 h-4 text-gray-400" />
              </div>
              <input 
                type="text" 
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-white border border-gray-300 text-gray-900 text-sm rounded-xl pl-10 pr-4 py-3 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all" 
                placeholder="Enter your full name"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Phone className="w-4 h-4 text-gray-400" />
              </div>
              <input 
                type="tel" 
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full bg-white border border-gray-300 text-gray-900 text-sm rounded-xl pl-10 pr-4 py-3 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all" 
                placeholder="Enter your phone number (optional)"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-gray-100 flex justify-end">
            <button 
              type="submit" 
              disabled={saving}
              className="bg-brand-600 hover:bg-brand-700 text-white font-medium py-3 px-8 rounded-xl shadow-sm transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
