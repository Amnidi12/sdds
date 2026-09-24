"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Donation } from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  pending_review: "Pending Review",
  approved: "Approved",
  pickup_scheduled: "Pickup Scheduled",
  picked_up: "Picked Up",
  received_at_warehouse: "Received at Warehouse",
  verified: "Verified",
  available: "Available",
  allocated: "Allocated",
  out_for_distribution: "Out for Distribution",
  delivered: "Delivered",
  completed: "Completed",
  rejected: "Rejected",
  cancelled: "Cancelled",
};

export default function DashboardPage() {
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.donations
      .list()
      .then(setDonations)
      .catch(() => setError("Could not load donations. Please log in again."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">My Donations</h1>
        <Link href="/dashboard/donations/new" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          + New Donation
        </Link>
      </div>

      {loading && <p className="mt-8 text-gray-500">Loading...</p>}
      {error && <p className="mt-8 text-red-600">{error}</p>}

      {!loading && !error && donations.length === 0 && (
        <div className="mt-12 rounded-lg border border-dashed border-gray-300 p-10 text-center dark:border-gray-700">
          <p className="text-gray-500">You haven&apos;t created any donations yet.</p>
        </div>
      )}

      <div className="mt-6 space-y-3">
        {donations.map((d) => (
          <div key={d.id} className="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-800">
            <div>
              <p className="font-medium">{d.title}</p>
              <p className="text-sm text-gray-500">
                {d.tracking_id} · {d.quantity} {d.unit}
              </p>
            </div>
            <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-700/20 dark:text-brand-100">
              {STATUS_LABELS[d.status] ?? d.status}
            </span>
          </div>
        ))}
      </div>
    </main>
  );
}
