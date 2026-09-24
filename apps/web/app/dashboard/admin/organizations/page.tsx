"use client";

import { useEffect, useState } from "react";
import { Building2, Globe } from "lucide-react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.admin.organizations()
      .then(setOrgs)
      .catch((err) => console.error("Failed to load organizations:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleVerify = async (id: string) => {
    try {
      await api.admin.verifyOrganization(id);
      setOrgs(orgs.map(o => o.id === id ? { ...o, is_verified: true } : o));
    } catch (err) {
      console.error("Failed to verify:", err);
      alert("Failed to verify organization.");
    }
  };

  return (
    <div className="mx-auto max-w-6xl font-sans">
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-medium text-gray-900 tracking-tight">Organizations</h1>
        <p className="mt-2 text-sm font-medium text-gray-500">Manage participating NGOs and verify their profiles.</p>
      </motion.div>

      <div className="bg-white rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-gray-100 overflow-hidden">
        <div className="border-b border-gray-50 px-6 py-4 flex items-center gap-3 bg-gradient-to-r from-gray-50/50 to-white">
          <div className="bg-teal-50 text-teal-600 p-1.5 rounded-md">
            <Building2 className="w-4 h-4" />
          </div>
          <h2 className="font-medium text-gray-900 text-sm tracking-wide">NGO DIRECTORY</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-500">
            <thead className="bg-gray-50/50 text-xs uppercase font-medium text-gray-400">
              <tr>
                <th className="px-6 py-4 tracking-wider">Organization</th>
                <th className="px-6 py-4 tracking-wider">Contact</th>
                <th className="px-6 py-4 tracking-wider">Status</th>
                <th className="px-6 py-4 tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading && <tr><td colSpan={4} className="p-8 text-center text-gray-500">Loading...</td></tr>}
              {orgs.map((org) => (
                <tr key={org.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900 text-base">{org.name}</div>
                    <div className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                      <Globe className="w-3 h-3" />
                      {org.slug}
                    </div>
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-600">
                    {org.contact_email || "N/A"}
                  </td>
                  <td className="px-6 py-4">
                    {org.is_verified ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        Verified
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                        Pending
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={() => handleVerify(org.id)}
                      disabled={org.is_verified}
                      className={`font-medium text-xs px-3 py-1.5 rounded-lg transition-colors ${org.is_verified ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-teal-50 text-teal-600 hover:bg-teal-100 hover:text-teal-800'}`}
                    >
                      {org.is_verified ? "Verified" : "Verify"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
