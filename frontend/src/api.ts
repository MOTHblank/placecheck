export type TransactionType = "sale" | "rent";
export type Property = {
  id: number;
  property_type: string;
  neighborhood: string;
  city: string;
  state: string;
  area: string | null;
  bedrooms: number | null;
  parking_spaces: number | null;
  min_price: string | null;
  listing_count: number;
  has_demo_offers: boolean;
  price_per_m2: string | null;
  price_drop_percent: number | null;
};
export type Offer = {
  is_demo: boolean;
  id: number;
  source: string;
  title: string;
  description: string;
  transaction_type: TransactionType;
  price: string | null;
  condominium_fee: string | null;
  iptu: string | null;
  url: string;
  previous_price: string | null;
  lowest_price: string | null;
  price_drop_percent: number | null;
  price_per_m2: string | null;
  days_on_market: number;
  price_history: { price: string; captured_at: string }[];
};
export type PropertyDetail = Property & { listings: Offer[] };
export type PropertyPage = { count: number; results: Property[]; next: string | null };

async function getJson<T>(url: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal, headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

export function getProperties(params: string, signal: AbortSignal): Promise<PropertyPage> {
  return getJson(`/api/properties/?${params}`, signal);
}

export function getProperty(id: number, params: string, signal: AbortSignal): Promise<PropertyDetail> {
  return getJson(`/api/properties/${id}/?${params}`, signal);
}

export const propertyLabels: Record<string, string> = {
  apartment: "Apartamento", house: "Casa", land: "Terreno", commercial: "Comercial", other: "Outro",
};
export const formatPrice = (price: string | number | null, transaction: TransactionType) => price === null
  ? "Preço sob consulta"
  : new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(Number(price)) + (transaction === "rent" ? "/mês" : "");
