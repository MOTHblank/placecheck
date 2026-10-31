type Delivery = { accepted: boolean; event_id?: string; context_token?: string; redirect_token?: string };
type Metric = { event_id: string; kind: "search" | "view" | "exposure"; receipt?: string; context?: string; listing_id?: number };

// Memory only: no offline store, persistent visitor identity, raw search text or cookies.
export async function deliverMetric(event: Metric): Promise<Delivery | null> {
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const response = await fetch("/api/analytics/events/", {
        method: "POST", credentials: "same-origin", signal: AbortSignal.timeout(5000),
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(event),
      });
      if (response.ok) return await response.json();
      if (response.status < 500) return null;
    } catch { /* A delivery failure must not block search, comparison or the original link. */ }
    if (attempt < 2) await new Promise((resolve) => setTimeout(resolve, 150 * (attempt + 1)));
  }
  return null;
}
