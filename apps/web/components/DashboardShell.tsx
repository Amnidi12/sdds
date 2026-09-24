"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  Truck,
  Warehouse,
  Users,
  HandHeart,
  BarChart3,
  LogOut,
  Loader2,
  Building2,
  UserCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { useCurrentUser } from "@/lib/useCurrentUser";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ size?: number }>;
}

interface NavGroup {
  title?: string;
  items: NavItem[];
}

const NAV_BY_ROLE: Record<string, NavGroup[]> = {
  donor: [{ items: [{ label: "My Donations", href: "/dashboard/donor", icon: LayoutDashboard }] }],
  volunteer: [{ items: [{ label: "My Tasks", href: "/dashboard/volunteer", icon: Truck }] }],
  beneficiary: [{ items: [{ label: "My Requests", href: "/dashboard/beneficiary", icon: HandHeart }] }],
  ngo_admin: [
    {
      title: "OVERVIEW",
      items: [{ label: "Overview", href: "/dashboard/ngo", icon: LayoutDashboard }],
    },
    {
      title: "PLATFORM DATA",
      items: [
        { label: "Donations", href: "/dashboard/ngo/donations", icon: Package },
        { label: "Inventory", href: "/dashboard/ngo/inventory", icon: Warehouse },
        { label: "Distributions", href: "/dashboard/ngo/distributions", icon: HandHeart },
        { label: "Beneficiaries", href: "/dashboard/ngo/beneficiaries", icon: Users },
        { label: "Pickups", href: "/dashboard/ngo/pickups", icon: Truck },
      ],
    },
  ],
  super_admin: [
    {
      title: "OVERVIEW",
      items: [{ label: "Dashboard", href: "/dashboard/admin", icon: BarChart3 }],
    },
    {
      title: "USER MANAGEMENT",
      items: [
        { label: "All Users", href: "/dashboard/admin/users", icon: Users },
        { label: "Organizations", href: "/dashboard/admin/organizations", icon: Building2 },
      ],
    },
    {
      title: "PLATFORM DATA",
      items: [
        { label: "Donations", href: "/dashboard/ngo/donations", icon: Package },
        { label: "Inventory", href: "/dashboard/ngo/inventory", icon: Warehouse },
        { label: "Distributions", href: "/dashboard/ngo/distributions", icon: HandHeart },
        { label: "Beneficiaries", href: "/dashboard/ngo/beneficiaries", icon: Users },
        { label: "Pickups", href: "/dashboard/ngo/pickups", icon: Truck },
      ],
    },
  ],
};

const ROLE_LABELS: Record<string, string> = {
  donor: "Donor",
  ngo_admin: "NGO Admin",
  volunteer: "Volunteer",
  beneficiary: "Beneficiary",
  super_admin: "Super Admin",
};

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useCurrentUser();
  const pathname = usePathname();
  const router = useRouter();

  const shouldRedirectOnboarding = user?.role === "ngo_admin" && !user?.organization_id && !pathname.includes("/dashboard/ngo/onboarding") && !pathname.includes("/dashboard/profile");

  useEffect(() => {
    if (shouldRedirectOnboarding) {
      router.push("/dashboard/ngo/onboarding");
    }
  }, [shouldRedirectOnboarding, router]);

  async function handleLogout() {
    await api.auth.logout();
    router.push("/login");
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="animate-spin text-brand-600" size={32} />
      </div>
    );
  }

  if (!user) return null; // useCurrentUser already redirects to /login

  if (shouldRedirectOnboarding) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="animate-spin text-brand-600" size={32} />
      </div>
    );
  }

  const navGroups = NAV_BY_ROLE[user.role] ?? [];

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-950 sm:flex">
        <Link href="/" className="flex items-center gap-3 border-b border-gray-200 px-6 py-5 dark:border-gray-800 hover:bg-gray-50 transition-colors">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 shadow-sm text-white">
            <Package size={20} />
          </div>
          <div className="flex flex-col pt-1">
            <span className="font-medium text-gray-900 text-2xl tracking-tighter leading-none group-hover:text-emerald-700 transition-colors">SDDS</span>
            <span className="text-[9px] font-medium text-gray-500 uppercase tracking-widest mt-0.5">SMART DONATION<br/>DISTRIBUTION SYSTEM</span>
          </div>
        </Link>

        <div className="flex-1 overflow-y-auto">
          <nav className="flex flex-col gap-6 px-3 py-6">
            {navGroups.map((group, idx) => (
              <div key={idx} className="flex flex-col gap-1">
                {group.title && (
                  <span className="px-3 text-[10px] font-medium uppercase tracking-widest text-gray-400 mb-1">
                    {group.title}
                  </span>
                )}
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition ${
                        active
                          ? "bg-brand-50 text-brand-700 dark:bg-brand-700/20 dark:text-brand-100"
                          : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-900"
                      }`}
                    >
                      <Icon size={18} />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            ))}
          </nav>
        </div>

        <div className="border-t border-gray-200 p-4 dark:border-gray-800">
          <Link 
            href="/dashboard/profile"
            className="flex items-center gap-3 hover:bg-gray-50 p-2 rounded-xl transition-colors cursor-pointer group"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 font-medium">
              {user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div className="flex flex-col">
              <span className="truncate text-sm font-medium text-gray-900 group-hover:text-emerald-700 transition-colors">{user.full_name}</span>
              <span className="text-xs font-medium text-gray-500">{ROLE_LABELS[user.role] ?? user.role}</span>
            </div>
          </Link>
          <div className="mt-2">
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            >
              <LogOut size={16} className="text-gray-400" />
              Log out
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1">
        {/* Mobile top bar */}
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-800 sm:hidden">
          <span className="text-sm font-semibold">SDDS — {ROLE_LABELS[user.role]}</span>
          <button onClick={handleLogout} className="text-sm text-gray-500">
            Log out
          </button>
        </div>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
