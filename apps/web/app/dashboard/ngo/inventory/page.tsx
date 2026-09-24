"use client";

import { useEffect, useState } from "react";
import { api, ApiError, Donation, InventoryBatch, Warehouse } from "@/lib/api";
import { PackageOpen, MapPin, Building2, PackageCheck } from "lucide-react";

export default function NgoInventoryPage() {
  const [batches, setBatches] = useState<InventoryBatch[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [receivable, setReceivable] = useState<Donation[]>([]);
  const [newWarehouseName, setNewWarehouseName] = useState("");
  const [receiveForm, setReceiveForm] = useState({ donation_id: "", warehouse_id: "", quantity: 1 });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    Promise.all([api.inventory.list(), api.warehouses.list(), api.donations.list({ status: "received_at_warehouse" })])
      .then(([b, w, d]) => {
        setBatches(b);
        setWarehouses(w);
        setReceivable(d);
      })
      .catch(() => setError("Could not load inventory data."))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function createWarehouse(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.warehouses.create({ name: newWarehouseName });
      setNewWarehouseName("");
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create warehouse");
    }
  }

  async function receiveDonation(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.inventory.receive(receiveForm.donation_id, {
        warehouse_id: receiveForm.warehouse_id,
        quantity: receiveForm.quantity,
      });
      setReceiveForm({ donation_id: "", warehouse_id: "", quantity: 1 });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not receive donation into inventory");
    }
  }

  return (
    <div className="max-w-6xl w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">Inventory Management</h1>
        <p className="text-gray-500 text-sm mt-1">Track stock levels across all warehouse locations.</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
        
        {/* Receive Donation Box (Takes up 2 columns) */}
        <div className="lg:col-span-2 bg-white border border-gray-100 rounded-lg shadow-sm">
          <div className="border-b border-gray-100 px-6 py-4 flex items-center gap-2">
            <PackageOpen className="w-5 h-5 text-emerald-600" />
            <h2 className="font-semibold text-gray-900">Receive Donation to Stock</h2>
          </div>
          
          <div className="p-6">
            <form onSubmit={receiveDonation} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Pending Receipt Donation</label>
                <select
                  required
                  className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
                  value={receiveForm.donation_id}
                  onChange={(e) => setReceiveForm({ ...receiveForm, donation_id: e.target.value })}
                >
                  <option value="" disabled>Select verified donation...</option>
                  {receivable.map((d) => (
                    <option key={d.id} value={d.id}>{d.title} ({d.tracking_id})</option>
                  ))}
                </select>
                {receivable.length === 0 && !loading && (
                  <p className="mt-2 text-xs text-amber-600">No pending donations waiting to be received.</p>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Target Warehouse</label>
                  <select
                    required
                    className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
                    value={receiveForm.warehouse_id}
                    onChange={(e) => setReceiveForm({ ...receiveForm, warehouse_id: e.target.value })}
                  >
                    <option value="" disabled>Select location...</option>
                    {warehouses.map((w) => (
                      <option key={w.id} value={w.id}>{w.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Received Quantity</label>
                  <input
                    type="number"
                    min={1}
                    required
                    className="w-full rounded-md border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    value={receiveForm.quantity}
                    onChange={(e) => setReceiveForm({ ...receiveForm, quantity: Number(e.target.value) })}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full rounded-md bg-[#10B981] hover:bg-emerald-600 py-2.5 text-sm font-medium text-white transition-colors mt-2"
                disabled={warehouses.length === 0 || receivable.length === 0}
              >
                Confirm Receipt
              </button>
            </form>
          </div>
        </div>

        {/* New Warehouse Box */}
        <div className="bg-white border border-gray-100 rounded-lg shadow-sm flex flex-col">
          <div className="border-b border-gray-100 px-6 py-4 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-emerald-600" />
            <h2 className="font-semibold text-gray-900">New Warehouse</h2>
          </div>
          <div className="p-6">
            <form onSubmit={createWarehouse} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Location Name</label>
                <input
                  required
                  placeholder="e.g. Central Facility"
                  className="w-full rounded-md border border-gray-200 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  value={newWarehouseName}
                  onChange={(e) => setNewWarehouseName(e.target.value)}
                />
              </div>
              <button
                type="submit"
                className="w-full rounded-md bg-gray-50 hover:bg-gray-100 border border-gray-200 py-2 text-sm font-medium text-gray-700 transition-colors"
              >
                Add Location
              </button>
            </form>

            <div className="mt-8">
              <h3 className="text-xs font-semibold text-gray-400 tracking-wider uppercase mb-3">Active Locations</h3>
              {warehouses.length === 0 ? (
                <p className="text-sm text-gray-500">No locations added yet.</p>
              ) : (
                <ul className="space-y-2">
                  {warehouses.map((w) => (
                    <li key={w.id} className="flex items-center gap-2 text-sm text-gray-700">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                      {w.name}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>

      <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Stock on Hand</h2>
      <div className="bg-white border border-gray-100 rounded-lg shadow-sm overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-gray-50 text-xs uppercase tracking-wider text-gray-500 font-semibold border-b border-gray-100">
            <tr>
              <th className="px-6 py-4">Storage Location</th>
              <th className="px-6 py-4">Available</th>
              <th className="px-6 py-4">Reserved</th>
              <th className="px-6 py-4">Expiry</th>
              <th className="px-6 py-4 text-right">Options</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={5} className="px-6 py-4 text-gray-500 text-center">Loading...</td></tr>
            ) : batches.length === 0 ? (
              <tr><td colSpan={5} className="px-6 py-4 text-gray-500 text-center">No inventory yet.</td></tr>
            ) : (
              batches.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4 flex items-center gap-2">
                    <PackageCheck className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-900 font-medium">{b.storage_location ?? "—"}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                      {b.quantity_available}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500">{b.quantity_reserved}</td>
                  <td className="px-6 py-4 text-gray-500">{b.expiry_date ?? "—"}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button 
                        onClick={() => api.inventory.dispatch(b.id, { quantity: 1 }).then(load)}
                        className="text-xs font-medium px-2 py-1 bg-blue-50 text-blue-600 rounded-md hover:bg-blue-100"
                        title="Dispatch 1 Unit"
                      >
                        Dispatch
                      </button>
                      <button 
                        onClick={() => api.inventory.reserve(b.id, { quantity: 1 }).then(load)}
                        className="text-xs font-medium px-2 py-1 bg-amber-50 text-amber-600 rounded-md hover:bg-amber-100"
                        title="Reserve 1 Unit"
                      >
                        Reserve
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
