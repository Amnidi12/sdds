"use client";

import { useEffect, useState } from "react";
import { api, ApiError, Beneficiary, Distribution, InventoryBatch } from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  created: "Created",
  reserved: "Reserved",
  dispatched: "Dispatched",
  delivered: "Delivered",
  verified: "Verified",
  completed: "Completed",
  cancelled: "Cancelled",
};

const NEXT_STATUS: Record<string, string> = {
  reserved: "dispatched",
  dispatched: "delivered",
  delivered: "verified",
  verified: "completed",
};

export default function NgoDistributionsPage() {
  const [distributions, setDistributions] = useState<Distribution[]>([]);
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [batches, setBatches] = useState<InventoryBatch[]>([]);
  const [form, setForm] = useState({ beneficiary_id: "", batch_id: "", quantity: 1 });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);

  function load() {
    setLoading(true);
    Promise.all([api.distributions.list(), api.beneficiaries.list(), api.inventory.list()])
      .then(([d, b, inv]) => {
        setDistributions(d);
        setBeneficiaries(b);
        setBatches(inv.filter((batch) => batch.quantity_available > 0));
      })
      .catch(() => setError("Could not load distribution data."))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function createDistribution(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.distributions.create({
        beneficiary_id: form.beneficiary_id,
        items: [{ inventory_batch_id: form.batch_id, quantity: form.quantity }],
      });
      setForm({ beneficiary_id: "", batch_id: "", quantity: 1 });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create distribution");
    }
  }

  async function advance(id: string, newStatus: string) {
    setBusyId(id);
    setError(null);
    try {
      await api.distributions.updateStatus(id, newStatus);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update distribution");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-semibold">Distributions</h1>
      <p className="mt-1 text-sm text-gray-500">Match available stock to beneficiary need, then track delivery through to completion.</p>

      <div className="mt-6 rounded-lg border border-gray-200 p-5 dark:border-gray-800">
        <h2 className="font-medium">Create a distribution</h2>
        <form onSubmit={createDistribution} className="mt-4 flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[160px]">
            <label className="block text-xs font-medium text-gray-500">Beneficiary</label>
            <select
              required
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={form.beneficiary_id}
              onChange={(e) => setForm({ ...form, beneficiary_id: e.target.value })}
            >
              <option value="">Select...</option>
              {beneficiaries.map((b) => (
                <option key={b.id} value={b.id}>{b.full_name}</option>
              ))}
            </select>
          </div>
          <div className="flex-1 min-w-[160px]">
            <label className="block text-xs font-medium text-gray-500">Inventory batch</label>
            <select
              required
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={form.batch_id}
              onChange={(e) => setForm({ ...form, batch_id: e.target.value })}
            >
              <option value="">Select...</option>
              {batches.map((b) => (
                <option key={b.id} value={b.id}>{b.storage_location ?? b.id.slice(0, 8)} ({b.quantity_available} available)</option>
              ))}
            </select>
          </div>
          <div className="w-24">
            <label className="block text-xs font-medium text-gray-500">Quantity</label>
            <input
              type="number"
              min={1}
              required
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              value={form.quantity}
              onChange={(e) => setForm({ ...form, quantity: Number(e.target.value) })}
            />
          </div>
          <button type="submit" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Create
          </button>
        </form>
        {batches.length === 0 && !loading && (
          <p className="mt-2 text-xs text-gray-500">No available stock right now — receive donations into inventory first.</p>
        )}
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      {loading && <p className="mt-6 text-gray-500">Loading...</p>}

      <div className="mt-6 space-y-3">
        {distributions.map((d) => {
          const next = NEXT_STATUS[d.status];
          return (
            <div key={d.id} className="flex items-center justify-between rounded-lg border border-gray-200 p-4 dark:border-gray-800">
              <div>
                <p className="text-sm text-gray-500">Distribution {d.id.slice(0, 8)}</p>
                <span className="mt-1 inline-block rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700 dark:bg-brand-700/20 dark:text-brand-100">
                  {STATUS_LABELS[d.status] ?? d.status}
                </span>
              </div>
              {next && (
                <button
                  disabled={busyId === d.id}
                  onClick={() => advance(d.id, next)}
                  className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                >
                  Mark {STATUS_LABELS[next]} →
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
