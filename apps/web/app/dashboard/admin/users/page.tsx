"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Users, Mail, Building2, UserCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useCurrentUser } from "@/lib/useCurrentUser";

export default function UsersPage() {
  const { user: currentUser } = useCurrentUser();
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.admin.users({ active_only: "false" })
      .then(setUsers)
      .catch((err) => console.error("Failed to load users:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleChangeRole = async (userId: string, newRole: string) => {
    try {
      await api.admin.changeUserRole(userId, newRole);
      setUsers(users.map(u => u.id === userId ? { ...u, role: newRole } : u));
    } catch (err) {
      console.error("Failed to change role:", err);
      alert("Failed to change user role.");
    }
  };

  return (
    <div className="mx-auto max-w-6xl font-sans">
      <motion.div 
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-medium text-gray-900 tracking-tight">All Users</h1>
        <p className="mt-2 text-sm font-medium text-gray-500">Manage all registered users on the platform.</p>
      </motion.div>

      <div className="bg-white rounded-2xl shadow-[0_4px_20px_rgb(0,0,0,0.03)] border border-gray-100 overflow-hidden">
        <div className="border-b border-gray-50 px-6 py-4 flex items-center gap-3 bg-gradient-to-r from-gray-50/50 to-white">
          <div className="bg-emerald-50 text-emerald-600 p-1.5 rounded-md">
            <Users className="w-4 h-4" />
          </div>
          <h2 className="font-medium text-gray-900 text-sm tracking-wide">USER DIRECTORY</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-500">
            <thead className="bg-gray-50/50 text-xs uppercase font-medium text-gray-400">
              <tr>
                <th className="px-6 py-4 tracking-wider">User</th>
                <th className="px-6 py-4 tracking-wider">Role</th>
                <th className="px-6 py-4 tracking-wider">Status</th>
                <th className="px-6 py-4 tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading && <tr><td colSpan={4} className="p-8 text-center text-gray-500">Loading...</td></tr>}
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="bg-gradient-to-br from-emerald-100 to-teal-100 p-2 rounded-full text-emerald-700 font-medium">
                        {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{user.full_name}</div>
                        <div className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                          <Mail className="w-3 h-3" />
                          {user.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-600">
                    <select
                      value={user.role}
                      disabled={user.id === currentUser?.id}
                      onChange={async (e) => {
                        const newRole = e.target.value;
                        try {
                          await api.admin.changeUserRole(user.id, newRole);
                          setUsers(users.map(u => u.id === user.id ? { ...u, role: newRole } : u));
                        } catch (err) {
                          alert(err instanceof Error ? err.message : "Failed to change user role.");
                        }
                      }}
                      className="bg-gray-50 border border-gray-200 text-gray-700 text-xs rounded-lg px-2 py-1 outline-none focus:ring-1 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <option value="donor">Donor</option>
                      <option value="volunteer">Volunteer</option>
                      <option value="ngo_admin">NGO Admin</option>
                      <option value="super_admin">Super Admin</option>
                      <option value="beneficiary">Beneficiary</option>
                    </select>
                  </td>
                  <td className="px-6 py-4">
                    {user.is_active ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-100">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                        Disabled
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {user.id !== currentUser?.id ? (
                      <button
                        onClick={async () => {
                          try {
                            await api.admin.changeUserStatus(user.id, !user.is_active);
                            setUsers(users.map(u => u.id === user.id ? { ...u, is_active: !user.is_active } : u));
                          } catch (err) {
                            alert(err instanceof Error ? err.message : "Failed to change user status.");
                          }
                        }}
                        className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                          user.is_active 
                            ? "bg-red-50 text-red-600 hover:bg-red-100" 
                            : "bg-emerald-50 text-emerald-600 hover:bg-emerald-100"
                        }`}
                      >
                        {user.is_active ? "Disable" : "Enable"}
                      </button>
                    ) : (
                      <span className="text-xs font-medium text-gray-400">Your Account</span>
                    )}
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
