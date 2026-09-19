export type Product = {
  name: string;
  price: string;
  image: string;
};

export type DashboardPhase = "mismatch" | "recovered" | "cached";

export type AdapterMapping = {
  label: string;
  app_action: string;
  semantic_intent: string;
  highlight: "error" | null;
};

export type DashboardState = {
  phase: DashboardPhase;
  skill: {
    name: string;
    title: string;
    steps: string[];
  };
  app: {
    app_id: string;
    label: string;
    unseen: boolean;
  };
  adapter: {
    skill_name: string;
    mappings: AdapterMapping[];
  };
  status: {
    skill_loaded: boolean;
    adapter_learned: boolean;
    product_live: boolean;
    message: string;
  };
};

/** Wrapper for GET /api/live-dashboard. Does not change fixture phases. */
export type LiveDashboardPayload = {
  source: "live" | "fixture";
  state: DashboardState | null;
};

export function formatPrice(price: string): string {
  const trimmed = price.trim();
  if (!trimmed) return "";
  return trimmed.startsWith("£") ? trimmed : `£${trimmed}`;
}
