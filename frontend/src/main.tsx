import { FormEvent, StrictMode, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type TransactionType = "sale" | "rent";
type SearchFilters = { query: string; location: string; transaction: TransactionType; minPrice: string; maxPrice: string; bedrooms: string; propertyType: string };
type Property = { id: number; type: string; neighborhood: string; city: string; area: number; bedrooms: number; parking: number; salePrice: number; rentPrice: number; offers: number; keywords: string; featured?: boolean };

const initialFilters: SearchFilters = { query: "", location: "", transaction: "sale", minPrice: "", maxPrice: "", bedrooms: "", propertyType: "" };
const properties: Property[] = [
  { id: 1, type: "Apartamento", neighborhood: "Buritis", city: "Belo Horizonte", area: 90, bedrooms: 3, parking: 2, salePrice: 599000, rentPrice: 3600, offers: 3, keywords: "apartamento varanda lazer", featured: true },
  { id: 2, type: "Casa", neighborhood: "São Pedro", city: "Belo Horizonte", area: 168, bedrooms: 4, parking: 3, salePrice: 1080000, rentPrice: 6200, offers: 2, keywords: "casa jardim espaço gourmet" },
  { id: 3, type: "Apartamento", neighborhood: "Funcionários", city: "Belo Horizonte", area: 72, bedrooms: 2, parking: 1, salePrice: 475000, rentPrice: 2900, offers: 4, keywords: "apartamento central varanda" },
];

const formatPrice = (price: number, transaction: TransactionType) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(price) + (transaction === "rent" ? "/mês" : "");

function Icon({ name }: { name: "search" | "pin" | "heart" }) {
  if (name === "pin") return <svg aria-hidden="true" viewBox="0 0 24 24" className="icon"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" /><circle cx="12" cy="10" r="2.25" /></svg>;
  if (name === "heart") return <svg aria-hidden="true" viewBox="0 0 24 24" className="icon"><path d="M20.8 8.8c0 5.4-8.8 10.2-8.8 10.2S3.2 14.2 3.2 8.8A4.6 4.6 0 0 1 12 6.3a4.6 4.6 0 0 1 8.8 2.5Z" /></svg>;
  return <svg aria-hidden="true" viewBox="0 0 24 24" className="icon"><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></svg>;
}

function PropertyCard({ property, transaction }: { property: Property; transaction: TransactionType }) {
  const price = transaction === "sale" ? property.salePrice : property.rentPrice;
  return <article className="property-card">
    <div className={`property-image property-image-${property.id}`}><span className="image-label">{property.featured ? "Destaque" : "Atualizado hoje"}</span><button className="favorite-button" type="button" aria-label={`Favoritar imóvel em ${property.neighborhood}`}><Icon name="heart" /></button></div>
    <div className="property-content"><div className="property-heading"><div><p className="property-type">{property.type}</p><h3>{property.neighborhood}</h3><p className="property-location">{property.city}</p></div><span className="offer-count">{property.offers} ofertas</span></div>
      <div className="property-details" aria-label="Características do imóvel"><span>{property.area} m²</span><span>{property.bedrooms} quartos</span><span>{property.parking} vagas</span></div>
      <div className="property-price"><span>A partir de</span><strong>{formatPrice(price, transaction)}</strong></div><button className="card-link" type="button">Ver ofertas <span aria-hidden="true">→</span></button>
    </div>
  </article>;
}

function App() {
  const [filters, setFilters] = useState<SearchFilters>(initialFilters);
  const [appliedFilters, setAppliedFilters] = useState<SearchFilters>(initialFilters);
  const [isMobileFiltersOpen, setIsMobileFiltersOpen] = useState(false);
  const visibleProperties = useMemo(() => {
    const queryTerms = appliedFilters.query.trim().toLocaleLowerCase("pt-BR").split(/\s+/).filter(Boolean);
    const location = appliedFilters.location.trim().toLocaleLowerCase("pt-BR");
    const minPrice = Number(appliedFilters.minPrice) || 0;
    const maxPrice = Number(appliedFilters.maxPrice) || Number.POSITIVE_INFINITY;
    const minBedrooms = Number(appliedFilters.bedrooms) || 0;
    return properties.filter((property) => {
      const price = appliedFilters.transaction === "sale" ? property.salePrice : property.rentPrice;
      const searchableText = `${property.type} ${property.neighborhood} ${property.city} ${property.bedrooms} quartos ${property.area} m² ${property.parking} vagas ${property.keywords}`.toLocaleLowerCase("pt-BR");
      const matchesQuery = queryTerms.every((term) => searchableText.includes(term));
      const matchesLocation = !location || `${property.neighborhood} ${property.city}`.toLocaleLowerCase("pt-BR").includes(location);
      const matchesType = !appliedFilters.propertyType || property.type === appliedFilters.propertyType;
      return matchesQuery && matchesLocation && matchesType && property.bedrooms >= minBedrooms && price >= minPrice && price <= maxPrice;
    });
  }, [appliedFilters]);
  const updateFilter = (field: keyof SearchFilters, value: string) => setFilters((current) => ({ ...current, [field]: value }));
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); setAppliedFilters(filters); setIsMobileFiltersOpen(false); };
  const clearFilters = () => { setFilters(initialFilters); setAppliedFilters(initialFilters); };

  return <div className="app-shell">
    <header className="site-header"><a className="brand" href="/" aria-label="Placecheck início"><span className="brand-mark">P</span><span>place<span>check</span></span></a><nav className="main-nav" aria-label="Navegação principal"><a className="active" href="#buscar">Buscar imóveis</a><a href="#como-funciona">Como funciona</a></nav><button className="header-action" type="button">Entrar</button></header>
    <main>
      <section className="hero" id="buscar"><div className="hero-copy"><p className="eyebrow">Seu próximo lugar começa aqui</p><h1>Encontre um imóvel que <em>faça sentido</em> para você.</h1><p className="hero-description">Compare anúncios de diferentes fontes em um só lugar e descubra oportunidades com mais clareza.</p></div>
        <form className="search-panel" onSubmit={handleSubmit}><div className="transaction-toggle" aria-label="Tipo de negociação"><button className={filters.transaction === "sale" ? "selected" : ""} type="button" onClick={() => updateFilter("transaction", "sale")}>Comprar</button><button className={filters.transaction === "rent" ? "selected" : ""} type="button" onClick={() => updateFilter("transaction", "rent")}>Alugar</button></div>
          <label className="free-search-field"><span>Busca livre <small>opcional</small></span><div className="input-with-icon"><Icon name="search" /><input value={filters.query} onChange={(event) => updateFilter("query", event.target.value)} placeholder="Ex.: apartamento com varanda em Belo Horizonte" /></div><small className="field-hint">Use suas próprias palavras ou combine com os filtros abaixo.</small></label>
          <div className="search-fields"><label className="location-field"><span>Onde você quer morar?</span><div className="input-with-icon"><Icon name="pin" /><input value={filters.location} onChange={(event) => updateFilter("location", event.target.value)} placeholder="Cidade, bairro ou região" /></div></label>
            <label><span>Preço mínimo</span><select value={filters.minPrice} onChange={(event) => updateFilter("minPrice", event.target.value)}><option value="">Sem mínimo</option><option value="200000">R$ 200 mil</option><option value="400000">R$ 400 mil</option><option value="600000">R$ 600 mil</option><option value="1000000">R$ 1 milhão</option></select></label>
            <label><span>Preço máximo</span><select value={filters.maxPrice} onChange={(event) => updateFilter("maxPrice", event.target.value)}><option value="">Sem máximo</option><option value="500000">R$ 500 mil</option><option value="700000">R$ 700 mil</option><option value="1000000">R$ 1 milhão</option><option value="1500000">R$ 1,5 milhão</option></select></label>
            <label><span>Quartos</span><select value={filters.bedrooms} onChange={(event) => updateFilter("bedrooms", event.target.value)}><option value="">Qualquer</option><option value="1">1 ou mais</option><option value="2">2 ou mais</option><option value="3">3 ou mais</option><option value="4">4 ou mais</option></select></label>
            <label><span>Tipo de imóvel</span><select value={filters.propertyType} onChange={(event) => updateFilter("propertyType", event.target.value)}><option value="">Todos os tipos</option><option value="Apartamento">Apartamento</option><option value="Casa">Casa</option></select></label><button className="search-button" type="submit"><Icon name="search" /> Buscar imóveis</button>
          </div>
        </form>
      </section>
      <section className="results-section" aria-labelledby="results-title"><div className="results-toolbar"><div><p className="section-kicker">Resultados para você</p><h2 id="results-title">Imóveis em destaque</h2></div><div className="results-actions"><button className="mobile-filter-button" type="button" onClick={() => setIsMobileFiltersOpen((open) => !open)}>Filtros <span>⌄</span></button><label className="sort-control">Ordenar por<select aria-label="Ordenar resultados" defaultValue="relevance"><option value="relevance">Mais relevantes</option><option value="price">Menor preço</option><option value="area">Maior área</option></select></label></div></div>
        {isMobileFiltersOpen && <div className="mobile-filter-note">Ajuste seus filtros na busca acima e toque em “Buscar imóveis”.</div>}
        {visibleProperties.length > 0 ? <div className="property-grid">{visibleProperties.map((property) => <PropertyCard key={property.id} property={property} transaction={appliedFilters.transaction} />)}</div> : <div className="empty-state"><span className="empty-icon">⌕</span><h3>Nenhum imóvel encontrado</h3><p>Tente ampliar sua região ou ajustar os filtros de preço.</p><button type="button" onClick={clearFilters}>Limpar filtros</button></div>}
      </section>
    </main>
    <footer className="site-footer" id="como-funciona"><span>placecheck</span><p>Uma forma mais simples de encontrar seu próximo lugar.</p></footer>
  </div>;
}

document.title = "Placecheck — Encontre seu próximo lugar";
createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
