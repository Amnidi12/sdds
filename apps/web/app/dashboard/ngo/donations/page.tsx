"use client";

import { useEffect, useState } from "react";
import { api, ApiError, Donation } from "@/lib/api";

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

const FILTERS = ["all", "pending_review", "approved", "available", "completed"];

export default function NgoDonationsPage() {
  const [donations, setDonations] = useState<Donation[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  function load() {
    setLoading(true);
    api.donations
      .list(filter === "all" ? undefined : { status: filter })
      .then(setDonations)
      .finally(() => setLoading(false));
  }

  useEffect(load, [filter]);

  async function act(id: string, newStatus: string, rejectionReason?: string) {
    setActionError(null);
    setBusyId(id);
    try {
      await api.donations.updateStatus(id, newStatus, undefined, rejectionReason);
      load();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="text-2xl font-semibold">Donations</h1>

      <div className="mt-4 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-3 py-1 text-sm font-medium ${
              filter === f
                ? "bg-brand-600 text-white"
                : "border border-gray-300 text-gray-600 hover:bg-gray-100 dark:border-gray-700 dark:text-gray-400 dark:hover:bg-gray-900"
            }`}
          >
            {f === "all" ? "All" : STATUS_LABELS[f]}
          </button>
        ))}
      </div>

      {actionError && <p className="mt-4 text-sm text-red-600">{actionError}</p>}
      {loading && <p className="mt-6 text-gray-500">Loading...</p>}
      {!loading && donations.length === 0 && <p className="mt-6 text-sm text-gray-500">No donations found.</p>}

      <div className="mt-6 space-y-3">
        {donations.map((d) => (
          <div key={d.id} className="rounded-lg border border-gray-200 p-4 dark:border-gray-800">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium">{d.title}</p>
                <p className="text-sm text-gray-500">{d.tracking_id} · {d.quantity} {d.unit} · {d.condition}</p>
                {d.description && <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{d.description}</p>}
              </div>
              <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-700/20 dark:text-brand-100">
                {STATUS_LABELS[d.status] ?? d.status}
              </span>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              {d.status === "pending_review" && (
                <>
                  <button
                    disabled={busyId === d.id}
                    onClick={() => act(d.id, "approved")}
                    className="rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                  >
                    Approve
                  </button>
                  <button
                    disabled={busyId === d.id}
                    onClick={() => act(d.id, "rejected", "Does not meet current NGO needs")}
                    className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 dark:border-red-900 dark:hover:bg-red-950"
                  >
                    Reject
                  </button>
                </>
              )}
              {d.status === "received_at_warehouse" && (
                <a href="/dashboard/ngo/inventory" className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700">
                  Receive into Inventory →
                </a>
              )}
              {d.status === "approved" && (
                <a href="/dashboard/ngo/pickups" className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700">
                  Schedule Pickup →
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
