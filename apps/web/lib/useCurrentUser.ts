"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, User, ApiError } from "@/lib/api";

export function useCurrentUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.auth
      .me()
      .then(setUser)
      .catch((err) => {
        if (err instanceof ApiError) router.replace("/login");
      })
      .finally(() => setLoading(false));
  }, [router]);

  return { user, loading };
}
