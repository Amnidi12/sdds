"use client";

import { useEffect, useState } from "react";
import { api, ApiError, Beneficiary } from "@/lib/api";
import { UserPlus, User, Phone, Home } from "lucide-react";

export default function NgoBeneficiariesPage() {
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [form, setForm] = useState({ full_name: "", phone: "", household_size: 1 });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api.beneficiaries.list().then(setBeneficiaries).finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function createBeneficiary(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.beneficiaries.create(form);
      setForm({ full_name: "", phone: "", household_size: 1 });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create beneficiary");
    }
  }

  return (
    <div className="max-w-5xl w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Beneficiaries</h1>
        <p className="text-gray-500 text-sm mt-1">Manage private beneficiary records. These are never shown publicly.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Add New Beneficiary Card */}
      <div className="bg-white border border-gray-100 rounded-lg shadow-sm mb-10">
        <div className="border-b border-gray-100 px-6 py-4 flex items-center gap-2">
          <UserPlus className="w-5 h-5 text-emerald-600" />
          <h2 className="font-semibold text-gray-900">Add New Beneficiary</h2>
        </div>
        
        <div className="p-6">
          <form onSubmit={createBeneficiary} className="flex flex-col md:flex-row items-end gap-4">
            <div className="flex-1 w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Full Name</label>
              <input
                required
                placeholder="e.g. John Doe"
                className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </div>
            
            <div className="flex-1 w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Phone (optional)</label>
              <input
                placeholder="e.g. +1 555 0192"
                className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
              />
            </div>
            
            <div className="w-full md:w-32">
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Household Size</label>
              <input
                type="number"
                min={1}
                required
                className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-colors"
                value={form.household_size}
                onChange={(e) => setForm({ ...form, household_size: Number(e.target.value) })}
              />
            </div>
            
            <button
              type="submit"
              className="w-full md:w-auto rounded-md bg-[#10B981] hover:bg-emerald-600 px-6 py-2.5 text-sm font-medium text-white transition-colors"
            >
              Add Record
            </button>
          </form>
        </div>
      </div>

      <h2 className="text-lg font-semibold text-gray-900 mb-4">Beneficiary Directory</h2>
      
      {loading ? (
        <p className="text-sm text-gray-500">Loading directory...</p>
      ) : beneficiaries.length === 0 ? (
        <p className="text-sm text-gray-500 bg-white p-6 rounded-lg border border-gray-100 shadow-sm">No beneficiaries registered yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {beneficiaries.map((b) => (
            <div key={b.id} className="bg-white border border-gray-100 rounded-lg p-5 shadow-sm hover:shadow-md hover:border-emerald-100 transition-all flex gap-4 items-start">
              <div className="mt-1">
                <div className="bg-emerald-50 p-2.5 rounded-full border border-emerald-100">
                  <User className="w-5 h-5 text-emerald-600" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{b.full_name}</h3>
                
                <div className="mt-2 space-y-1.5">
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Phone className="w-3.5 h-3.5 text-gray-400" />
                    <span>{b.phone || <span className="italic">No phone on file</span>}</span>
                  </div>
                  
                  {b.household_size && (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Home className="w-3.5 h-3.5 text-gray-400" />
                      <span>Household of {b.household_size}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
