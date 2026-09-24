"use client";

import { useEffect, useState } from "react";
import { api, ApiError, Donation, OrgMember, PickupTask } from "@/lib/api";

const PICKUP_LABELS: Record<string, string> = {
  assigned: "Assigned",
  accepted: "Accepted",
  en_route: "En Route",
  arrived: "Arrived",
  picked_up: "Picked Up",
  failed: "Failed",
  completed: "Completed",
};

export default function NgoPickupsPage() {
  const [tasks, setTasks] = useState<PickupTask[]>([]);
  const [approvedDonations, setApprovedDonations] = useState<Donation[]>([]);
  const [volunteers, setVolunteers] = useState<OrgMember[]>([]);
  const [form, setForm] = useState({ donation_id: "", volunteer_id: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    Promise.all([
      api.pickups.list(),
      api.donations.list({ status: "approved" }),
      api.organizations.members("volunteer"),
    ])
      .then(([t, d, v]) => {
        setTasks(t);
        setApprovedDonations(d);
        setVolunteers(v);
      })
      .catch(() => setError("Could not load pickup data."))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function createTask(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.pickups.create({
        donation_id: form.donation_id,
        volunteer_id: form.volunteer_id || undefined,
      });
      setForm({ donation_id: "", volunteer_id: "" });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not schedule pickup");
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold">Pickups</h1>

      <div className="mt-6 rounded-lg border border-gray-200 p-5 dark:border-gray-800">
        <h2 className="font-medium">Schedule a new pickup</h2>
        <form onSubmit={createTask} className="mt-4 flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500">Approved donation</label>
            <select
              required
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={form.donation_id}
              onChange={(e) => setForm({ ...form, donation_id: e.target.value })}
            >
              <option value="">Select donation...</option>
              {approvedDonations.map((d) => (
                <option key={d.id} value={d.id}>{d.title} ({d.tracking_id})</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-500">Assign volunteer (optional)</label>
            <select
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={form.volunteer_id}
              onChange={(e) => setForm({ ...form, volunteer_id: e.target.value })}
            >
              <option value="">Unassigned</option>
              {volunteers.map((v) => (
                <option key={v.id} value={v.id}>{v.full_name}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Schedule
          </button>
        </form>
        {approvedDonations.length === 0 && !loading && (
          <p className="mt-2 text-xs text-gray-500">No approved donations awaiting pickup right now.</p>
        )}
        {volunteers.length === 0 && !loading && (
          <p className="mt-2 text-xs text-gray-500">No volunteers in your organization yet — tasks can still be created unassigned.</p>
        )}
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      {loading && <p className="mt-6 text-gray-500">Loading...</p>}

      <div className="mt-6 space-y-3">
        {tasks.map((t) => (
          <div key={t.id} className="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-800">
            <div>
              <p className="text-sm text-gray-500">Task {t.id.slice(0, 8)}</p>
              {t.scheduled_at && <p className="text-xs text-gray-400">Scheduled: {new Date(t.scheduled_at).toLocaleString()}</p>}
            </div>
            <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-700/20 dark:text-brand-100">
              {PICKUP_LABELS[t.status] ?? t.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
