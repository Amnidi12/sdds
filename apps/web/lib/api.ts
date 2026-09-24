const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export class ApiError extends Error {
  code: string;
  requestId?: string;
  constructor(code: string, message: string, requestId?: string) {
    super(message);
    this.code = code;
    this.requestId = requestId;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (typeof document !== "undefined") {
    const match = document.cookie.match(/(^|;)\s*xsrf-token\s*=\s*([^;]+)/);
    if (match) {
      headers["x-xsrf-token"] = match[2];
    }
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include", // send/receive HttpOnly auth cookies
    headers,
  });

  if (!res.ok) {
    let body: Record<string, any> = {};
    try {
      body = await res.json();
    } catch {
      /* ignore parse errors */
    }
    const err = body?.error || {};
    throw new ApiError(err.code || "UNKNOWN", err.message || "Something went wrong", err.request_id);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ─── Shared Types ──────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "super_admin" | "ngo_admin" | "donor" | "volunteer" | "beneficiary";
  organization_id: string | null;
  is_email_verified: boolean;
}

export interface Donation {
  id: string;
  tracking_id: string;
  title: string;
  description: string | null;
  quantity: number;
  unit: string;
  status: string;
  condition: string;
  pickup_required: boolean;
  pickup_address: string | null;
  organization_id: string | null;
  created_at: string;
}

export interface DonationCategory {
  id: string;
  name: string;
  slug: string;
  description: string | null;
}

export interface PickupTask {
  id: string;
  donation_id: string;
  volunteer_id: string | null;
  scheduled_at: string | null;
  status: "assigned" | "accepted" | "en_route" | "arrived" | "picked_up" | "failed" | "completed";
  note: string | null;
  created_at: string;
}

export interface Distribution {
  id: string;
  organization_id: string;
  beneficiary_id: string;
  volunteer_id: string | null;
  request_id: string | null;
  status: "created" | "reserved" | "dispatched" | "delivered" | "verified" | "completed" | "cancelled";
  created_at: string;
}

export interface OrgMember {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

export interface InventoryBatch {
  id: string;
  warehouse_id: string;
  donation_id: string;
  category_id: string;
  quantity_available: number;
  quantity_reserved: number;
  storage_location: string | null;
  expiry_date: string | null;
}

export interface Warehouse {
  id: string;
  organization_id: string;
  name: string;
  address: string | null;
  is_active: boolean;
}

export interface Beneficiary {
  id: string;
  organization_id: string;
  full_name: string;
  phone: string | null;
  household_size: number | null;
}

export interface BeneficiaryRequest {
  id: string;
  beneficiary_id: string;
  category_id: string;
  quantity_requested: number;
  status: "submitted" | "under_review" | "approved" | "fulfilled" | "rejected";
}

export interface AdminStats {
  organizations: number;
  active_users: number;
  total_donations: number;
  pending_review: number;
  completed_donations: number;
  completed_distributions: number;
}

export interface UserAdminOut {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id: string | null;
  is_active: boolean;
  is_email_verified: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  contact_email: string | null;
  is_verified: boolean;
  is_active: boolean;
}

export interface AppNotification {
  id: string;
  title: string;
  body: string | null;
  event_type: string;
  is_read: boolean;
  link: string | null;
  created_at: string;
}

// ─── API Client ────────────────────────────────────────────────────────────────

export const api = {
  auth: {
    register: (data: { email: string; password: string; full_name: string; role?: string }) =>
      request<User>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      request<User>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(data) }),
    logout: () => request<{ message: string }>("/api/v1/auth/logout", { method: "POST" }),
    me: () => request<User>("/api/v1/auth/me"),
    updateProfile: (data: { full_name?: string; phone?: string }) =>
      request<User>("/api/v1/auth/me", { method: "PATCH", body: JSON.stringify(data) }),
    forgotPassword: (email: string) =>
      request<{ message: string }>("/api/v1/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
  },
  donations: {
    list: (params?: Record<string, string>) =>
      request<Donation[]>("/api/v1/donations" + (params ? "?" + new URLSearchParams(params).toString() : "")),
    create: (data: Record<string, unknown>) =>
      request<Donation>("/api/v1/donations", { method: "POST", body: JSON.stringify(data) }),
    get: (id: string) => request<Donation>(`/api/v1/donations/${id}`),
    track: (trackingId: string) =>
      request<{ tracking_id: string; category_name: string; status: string; created_at: string }>(
        `/api/v1/donations/track/${trackingId}`
      ),
    updateStatus: (id: string, new_status: string, note?: string, rejection_reason?: string) =>
      request<Donation>(`/api/v1/donations/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ new_status, note, rejection_reason }),
      }),
  },
  admin: {
    stats: () => request<AdminStats>("/api/v1/admin/stats"),
    organizations: () => request<Organization[]>("/api/v1/admin/organizations"),
    verifyOrganization: (id: string) =>
      request<Organization>(`/api/v1/admin/organizations/${id}/verify`, { method: "PATCH" }),
    users: (params?: Record<string, string>) =>
      request<UserAdminOut[]>("/api/v1/admin/users" + (params ? "?" + new URLSearchParams(params).toString() : "")),
    changeUserRole: (id: string, new_role: string) =>
      request<UserAdminOut>(`/api/v1/admin/users/${id}/role`, {
        method: "PATCH",
        body: JSON.stringify({ new_role }),
      }),
    changeUserStatus: (id: string, is_active: boolean) =>
      request<UserAdminOut>(`/api/v1/admin/users/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ is_active }),
      }),
  },
  pickups: {
    list: () => request<PickupTask[]>("/api/v1/pickups"),
    create: (data: { donation_id: string; volunteer_id?: string; scheduled_at?: string }) =>
      request<PickupTask>("/api/v1/pickups", { method: "POST", body: JSON.stringify(data) }),
    updateStatus: (id: string, new_status: string, note?: string) =>
      request<PickupTask>(`/api/v1/pickups/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ new_status, note }),
      }),
  },
  distributions: {
    list: () => request<Distribution[]>("/api/v1/distributions"),
    create: (data: {
      beneficiary_id: string;
      request_id?: string;
      volunteer_id?: string;
      items: { inventory_batch_id: string; quantity: number }[];
    }) => request<Distribution>("/api/v1/distributions", { method: "POST", body: JSON.stringify(data) }),
    updateStatus: (id: string, new_status: string) =>
      request<Distribution>(`/api/v1/distributions/${id}/status`, {
        method: "PATCH",
        body: JSON.stringify({ new_status }),
      }),
    submitProof: (id: string, data: { recipient_confirmation_name?: string; note?: string }) =>
      request<{ message: string; proof_id: string }>(`/api/v1/distributions/${id}/proof`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  inventory: {
    list: () => request<InventoryBatch[]>("/api/v1/inventory"),
    receive: (donationId: string, data: { warehouse_id: string; quantity: number; storage_location?: string; expiry_date?: string }) =>
      request<InventoryBatch>(`/api/v1/inventory/receive/${donationId}`, { method: "POST", body: JSON.stringify(data) }),
    reserve: (batchId: string, data: { quantity: number }) =>
      request<InventoryBatch>(`/api/v1/inventory/${batchId}/reserve`, { method: "POST", body: JSON.stringify(data) }),
    release: (batchId: string, data: { quantity: number }) =>
      request<InventoryBatch>(`/api/v1/inventory/${batchId}/release`, { method: "POST", body: JSON.stringify(data) }),
    dispatch: (batchId: string, data: { quantity: number }) =>
      request<InventoryBatch>(`/api/v1/inventory/${batchId}/dispatch`, { method: "POST", body: JSON.stringify(data) }),
  },
  warehouses: {
    list: () => request<Warehouse[]>("/api/v1/warehouses"),
    create: (data: { name: string; address?: string }) =>
      request<Warehouse>("/api/v1/warehouses", { method: "POST", body: JSON.stringify(data) }),
  },
  organizations: {
    create: (data: { name: string; description?: string; contact_email?: string; contact_phone?: string; address?: string }) =>
      request<Organization>("/api/v1/organizations", { method: "POST", body: JSON.stringify(data) }),
    members: (role: string) => request<OrgMember[]>(`/api/v1/organizations/members?role=${role}`),
  },
  beneficiaries: {
    list: () => request<Beneficiary[]>("/api/v1/beneficiaries"),
    create: (data: { full_name: string; phone?: string; address?: string; household_size?: number; notes?: string }) =>
      request<Beneficiary>("/api/v1/beneficiaries", { method: "POST", body: JSON.stringify(data) }),
    me: () => request<Beneficiary>("/api/v1/beneficiaries/me"),
    myRequests: (id: string) => request<BeneficiaryRequest[]>(`/api/v1/beneficiaries/${id}/requests`),
    submitRequest: (id: string, data: { category_id: string; quantity_requested: number; notes?: string }) =>
      request<BeneficiaryRequest>(`/api/v1/beneficiaries/${id}/requests`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  categories: {
    list: () => request<DonationCategory[]>("/api/v1/donation-categories"),
  },
  notifications: {
    list: (unreadOnly?: boolean) =>
      request<AppNotification[]>(`/api/v1/notifications${unreadOnly ? "?unread_only=true" : ""}`),
    markRead: (id: string) =>
      request<AppNotification>(`/api/v1/notifications/${id}/read`, { method: "PATCH" }),
    markAllRead: () =>
      request<{ message: string }>("/api/v1/notifications/read-all", { method: "POST" }),
  },
  uploads: {
    uploadImage: (file: File): Promise<{ url: string; storage_key: string }> => {
      const formData = new FormData();
      formData.append("file", file);
      const headers: Record<string, string> = {};
      if (typeof document !== "undefined") {
        const match = document.cookie.match(/(^|;)\s*xsrf-token\s*=\s*([^;]+)/);
        if (match) headers["x-xsrf-token"] = match[2];
      }
      return fetch(`${API_URL}/api/v1/uploads`, {
        method: "POST",
        credentials: "include",
        headers,
        body: formData,
      }).then(async (res) => {
        if (!res.ok) throw new ApiError("UPLOAD_FAILED", "Upload failed");
        return res.json();
      });
    },
  },
  reports: {
    downloadDonationsCsv: (status?: string) => {
      const params = status ? `?status=${status}` : "";
      window.open(`${API_URL}/api/v1/reports/donations${params}`, "_blank");
    },
    downloadReceipt: (donationId: string) => {
      window.open(`${API_URL}/api/v1/reports/donations/${donationId}/receipt`, "_blank");
    },
  },
  public: {
    stats: () => request<{ processed_kg: number; active_ngos: number; beneficiaries: number; active_fleets: number }>(
      "/api/v1/public/stats"
    ),
  },
};
