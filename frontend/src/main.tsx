import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { getProperties, PropertyPage } from "./api";
import { OfferDialog } from "./OfferDialog";
import { SearchForm } from "./SearchForm";
import { SearchResults } from "./SearchResults";
import { initialFilters, offerParams, readSearchState, resultParams, SearchFilters, SearchState, searchUrl } from "./search";
import "./styles.css";

function App() {
  const [search, setSearch] = useState(readSearchState);
  const [filters, setFilters] = useState(search.filters);
  const [data, setData] = useState<PropertyPage>({ count: 0, results: [], next: null });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const query = resultParams(search).toString();
  const detailQuery = offerParams(search.filters).toString();

  useEffect(() => {
    const onPopState = () => setSearch(readSearchState());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);
  useEffect(() => setFilters(search.filters), [search.filters]);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(false);
    getProperties(query, controller.signal).then((page) => {
      if (!controller.signal.aborted) { setData(page); setLoading(false); }
    }).catch(() => {
      if (!controller.signal.aborted) { setError(true); setLoading(false); }
    });
    return () => controller.abort();
  }, [query, attempt]);

  const navigate = (next: SearchState) => {
    window.history.pushState(null, "", searchUrl(next));
    setSearch(next);
  };
  const updateFilter = (field: keyof SearchFilters, value: string) => setFilters((current) => ({
    ...current, [field]: value, ...(field === "transaction" ? { minPrice: "", maxPrice: "" } : {}),
  }));
  const clearFilters = () => navigate({ filters: initialFilters, ordering: "-updated_at", offset: 0, propertyId: null });

  return <div className="app-shell">
    <header className="site-header"><a className="brand" href="/" aria-label="Placecheck início"><span className="brand-mark">P</span><span>place<span>check</span></span></a><nav className="main-nav" aria-label="Navegação principal"><a className="active" href="#buscar">Buscar imóveis</a><a href="#como-funciona">Como funciona</a></nav></header>
    <main>
      <SearchForm filters={filters} updateFilter={updateFilter} onSubmit={() => navigate({ ...search, filters, offset: 0, propertyId: null })} />
      <SearchResults properties={data.results} count={data.count} offset={search.offset} transaction={search.filters.transaction} ordering={search.ordering} loading={loading} error={error}
        onOrder={(ordering) => navigate({ ...search, ordering, offset: 0 })}
        onPage={(offset) => navigate({ ...search, offset })}
        onOpen={(propertyId) => navigate({ ...search, propertyId })}
        onClear={clearFilters} onRetry={() => setAttempt((value) => value + 1)} />
    </main>
    {search.propertyId !== null && <OfferDialog id={search.propertyId} params={detailQuery} transaction={search.filters.transaction} onClose={() => navigate({ ...search, propertyId: null })} />}
    <footer className="site-footer" id="como-funciona"><span>placecheck</span><p>Busque por cidade, compare ofertas e acompanhe preços. Contato e negociação acontecem na fonte original.</p></footer>
  </div>;
}

document.title = "Placecheck — Encontre seu próximo lugar";
createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
