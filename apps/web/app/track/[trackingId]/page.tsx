"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";

interface TrackingResult {
  tracking_id: string;
  category_name: string;
  status: string;
  created_at: string;
}

export default function TrackingResultPage() {
  const params = useParams<{ trackingId: string }>();
  const [result, setResult] = useState<TrackingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.donations
      .track(params.trackingId)
      .then(setResult)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not find this tracking ID"));
  }, [params.trackingId]);

  return (
    <main className="mx-auto mt-16 max-w-md px-6 text-center">
      {error && <p className="text-red-600">{error}</p>}
      {result && (
        <div className="rounded-lg border border-gray-200 p-6 dark:border-gray-800">
          <p className="text-sm text-gray-500">{result.tracking_id}</p>
          <h1 className="mt-1 text-xl font-semibold">{result.category_name}</h1>
          <span className="mt-4 inline-block rounded-full bg-brand-50 px-4 py-1 text-sm font-medium text-brand-700 dark:bg-brand-700/20 dark:text-brand-100">
            {result.status.replace(/_/g, " ")}
          </span>
          <p className="mt-4 text-xs text-gray-400">Submitted {new Date(result.created_at).toLocaleDateString()}</p>
        </div>
      )}
    </main>
  );
}
