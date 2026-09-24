"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import Link from "next/link";
import { Package } from "lucide-react";

interface TrackingResult {
  tracking_id: string;
  category_name: string;
  status: string;
  created_at: string;
}

export default function TrackLandingPage() {
  const [trackingId, setTrackingId] = useState("");
  const [result, setResult] = useState<TrackingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!trackingId.trim()) return;
    
    setError(null);
    setResult(null);
    setLoading(true);
    
    try {
      const res = await api.donations.track(trackingId.trim());
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not find this tracking ID");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="bg-white border-b border-gray-100 h-16 flex items-center justify-between px-6 lg:px-12 sticky top-0 z-50">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="bg-gradient-to-br from-emerald-500 to-teal-600 p-2 rounded-lg shadow-md group-hover:shadow-lg transition-all duration-300">
              <Package className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col pt-1">
              <span className="font-medium text-gray-900 text-2xl tracking-tighter leading-none">SDDS</span>
              <span className="text-[9px] font-medium text-gray-500 uppercase tracking-widest mt-0.5 hidden sm:block">SMART DONATION DISTRIBUTION SYSTEM</span>
            </div>
          </Link>
          <nav className="hidden md:flex gap-6">
            <Link href="/" className="text-gray-500 hover:text-gray-900 font-medium text-sm transition-colors">Portal</Link>
            <Link href="/track" className="text-gray-900 font-medium text-sm">Tracking</Link>
          </nav>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/login" className="text-gray-600 hover:text-gray-900 font-medium text-sm">Sign In</Link>
          <Link href="/register" className="bg-[#10B981] hover:bg-emerald-600 text-white px-5 py-2 rounded-md font-medium text-sm transition-colors">
            Create Account
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 w-full max-w-2xl mx-auto text-center pt-24 px-6 pb-20">
        <h1 className="text-2xl font-semibold text-[#1F2937]">Track a Donation</h1>
        <p className="mt-2 text-sm text-gray-500">Enter the tracking ID from your donation confirmation (e.g. SDDT-2026-X7K29P)</p>
        
        <form onSubmit={onSubmit} className="mt-8 flex justify-center gap-3">
          <input
            className="w-full max-w-sm rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 text-gray-700 bg-white"
            placeholder="SDDT-2026-X7K29P"
            value={trackingId}
            onChange={(e) => setTrackingId(e.target.value)}
          />
          <button 
            type="submit" 
            disabled={loading}
            className="rounded-md bg-[#166534] px-6 py-2.5 font-medium text-white hover:bg-[#14532d] disabled:opacity-50 transition-colors"
          >
            {loading ? "Tracking..." : "Track"}
          </button>
        </form>

        {error && (
          <div className="mt-8 p-4 bg-red-50 border border-red-100 rounded-lg max-w-md mx-auto text-red-600 text-sm">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-8 mx-auto max-w-md rounded-lg border border-gray-100 bg-white p-8 shadow-sm text-left">
            <p className="text-sm font-medium text-gray-500">Tracking ID: {result.tracking_id}</p>
            <h2 className="mt-2 text-xl font-medium text-gray-900">{result.category_name}</h2>
            <div className="mt-6">
              <span className="inline-block rounded-full bg-emerald-50 px-4 py-1.5 text-sm font-semibold text-emerald-700 border border-emerald-100">
                {result.status.replace(/_/g, " ").toUpperCase()}
              </span>
            </div>
            <p className="mt-6 text-xs text-gray-400 font-medium">Submitted {new Date(result.created_at).toLocaleDateString()}</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col md:flex-row items-center justify-center gap-8">
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500">
            <span>© All rights reserved by Smart Donation System</span>
            <span className="hidden md:inline text-gray-300">|</span>
            <span>Designed by amndy</span>
            <span className="hidden md:inline text-gray-300">|</span>
            <Link href="/" className="hover:text-gray-900 transition-colors font-medium">Portal</Link>
            <Link href="/login" className="hover:text-gray-900 transition-colors font-medium">Sign In</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
