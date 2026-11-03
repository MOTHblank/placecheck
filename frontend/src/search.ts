import { TransactionType } from "./api";

export type SearchFilters = { query: string; location: string; city: string; state: string; neighborhood: string; transaction: TransactionType; minPrice: string; maxPrice: string; minArea: string; maxArea: string; bedrooms: string; bathrooms: string; parkingSpaces: string; propertyType: string };
export type SearchState = { filters: SearchFilters; ordering: string; offset: number; propertyId: number | null };
export const pageSize = 12;
export const initialFilters: SearchFilters = { query: "", location: "", city: "", state: "", neighborhood: "", transaction: "sale", minPrice: "", maxPrice: "", minArea: "", maxArea: "", bedrooms: "", bathrooms: "", parkingSpaces: "", propertyType: "" };
const fields = { query: "q", location: "location", city: "city", state: "state", neighborhood: "neighborhood", minPrice: "min_price", maxPrice: "max_price", minArea: "min_area", maxArea: "max_area", bedrooms: "bedrooms", bathrooms: "bathrooms", parkingSpaces: "parking_spaces", propertyType: "property_type" } as const;
export const filterParamNames = ["transaction_type", ...Object.values(fields)];
const orderings = ["-updated_at", "price", "-price", "-area", "price_per_m2", "-price_drop"];

export function readSearchState(): SearchState {
  const params = new URLSearchParams(window.location.search);
  const filters = { ...initialFilters };
  for (const [field, param] of Object.entries(fields)) filters[field as keyof typeof fields] = params.get(param) || "";
  filters.transaction = params.get("transaction_type") === "rent" ? "rent" : "sale";
  const offset = Number(params.get("offset"));
  const propertyId = Number(params.get("property"));
  return {
    filters,
    ordering: orderings.includes(params.get("ordering") || "") ? params.get("ordering")! : "-updated_at",
    offset: Number.isSafeInteger(offset) && offset >= 0 ? offset : 0,
    propertyId: Number.isSafeInteger(propertyId) && propertyId > 0 ? propertyId : null,
  };
}

export function offerParams(filters: SearchFilters): URLSearchParams {
  const params = new URLSearchParams({ transaction_type: filters.transaction });
  for (const [field, param] of Object.entries(fields)) if (filters[field as keyof typeof fields]) params.set(param, filters[field as keyof typeof fields]);
  return params;
}

export function resultParams(state: SearchState): URLSearchParams {
  const params = offerParams(state.filters);
  params.set("ordering", state.ordering);
  params.set("limit", String(pageSize));
  params.set("offset", String(state.offset));
  return params;
}

export function searchUrl(state: SearchState): string {
  const params = resultParams(state);
  if (state.propertyId !== null) params.set("property", String(state.propertyId));
  return `${window.location.pathname}?${params}${window.location.hash}`;
}
