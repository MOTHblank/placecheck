import { Icon } from "./Icon";
import { SearchFilters } from "./search";

export function SearchForm({ filters, updateFilter, onSubmit }: {
  filters: SearchFilters; updateFilter: (field: keyof SearchFilters, value: string) => void; onSubmit: () => void;
}) {
  return (      <section className="hero" id="buscar"><div className="hero-copy"><p className="eyebrow">Seu próximo lugar começa aqui</p><h1>Encontre um imóvel que <em>faça sentido</em> para você.</h1><p className="hero-description">Compare anúncios de diferentes fontes em um só lugar e descubra oportunidades com mais clareza.</p></div>
        <form className="search-panel" onSubmit={(event) => { event.preventDefault(); onSubmit(); }}><div className="transaction-toggle" aria-label="Tipo de negociação"><button className={filters.transaction === "sale" ? "selected" : ""} type="button" onClick={() => updateFilter("transaction", "sale")}>Comprar</button><button className={filters.transaction === "rent" ? "selected" : ""} type="button" onClick={() => updateFilter("transaction", "rent")}>Alugar</button></div>
          <label className="free-search-field"><span>Busca livre <small>opcional</small></span><div className="input-with-icon"><Icon name="search" /><input value={filters.query} onChange={(event) => updateFilter("query", event.target.value)} placeholder="Ex.: apartamento com varanda em Belo Horizonte" /></div><small className="field-hint">Use suas próprias palavras ou combine com os filtros abaixo.</small></label>
          <div className="search-fields"><label className="location-field"><span>Onde você quer morar?</span><div className="input-with-icon"><Icon name="pin" /><input value={filters.location} onChange={(event) => updateFilter("location", event.target.value)} placeholder="Cidade, bairro ou região" /></div></label>
            <label><span>Preço mínimo</span><select value={filters.minPrice} onChange={(event) => updateFilter("minPrice", event.target.value)}><option value="">Sem mínimo</option>{(filters.transaction === "rent" ? [[1000, "R$ 1 mil"], [2000, "R$ 2 mil"], [4000, "R$ 4 mil"], [6000, "R$ 6 mil"]] : [[200000, "R$ 200 mil"], [400000, "R$ 400 mil"], [600000, "R$ 600 mil"], [1000000, "R$ 1 milhão"]]).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <label><span>Preço máximo</span><select value={filters.maxPrice} onChange={(event) => updateFilter("maxPrice", event.target.value)}><option value="">Sem máximo</option>{(filters.transaction === "rent" ? [[2000, "R$ 2 mil"], [4000, "R$ 4 mil"], [6000, "R$ 6 mil"], [10000, "R$ 10 mil"]] : [[500000, "R$ 500 mil"], [700000, "R$ 700 mil"], [1000000, "R$ 1 milhão"], [1500000, "R$ 1,5 milhão"]]).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <label><span>Quartos</span><select value={filters.bedrooms} onChange={(event) => updateFilter("bedrooms", event.target.value)}><option value="">Qualquer</option><option value="1">1 ou mais</option><option value="2">2 ou mais</option><option value="3">3 ou mais</option><option value="4">4 ou mais</option></select></label>
            <label><span>Tipo de imóvel</span><select value={filters.propertyType} onChange={(event) => updateFilter("propertyType", event.target.value)}><option value="">Todos os tipos</option><option value="apartment">Apartamento</option><option value="house">Casa</option><option value="land">Terreno</option><option value="commercial">Comercial</option><option value="other">Outro</option></select></label><button className="search-button" type="submit"><Icon name="search" /> Buscar imóveis</button>
          </div>
          <details className="advanced-filters" open={Boolean(filters.city || filters.state || filters.neighborhood || filters.minArea || filters.maxArea || filters.bathrooms || filters.parkingSpaces)}>
            <summary>Filtros avançados</summary>
            <div className="advanced-filter-grid">
              <label><span>Cidade específica</span><input maxLength={120} value={filters.city} onChange={(event) => updateFilter("city", event.target.value)} placeholder="Ex.: Belo Horizonte" /></label>
              <label><span>UF</span><input maxLength={2} value={filters.state} onChange={(event) => updateFilter("state", event.target.value.toUpperCase().replace(/[^A-Z]/g, ""))} placeholder="MG" /></label>
              <label><span>Bairro específico</span><input maxLength={120} value={filters.neighborhood} onChange={(event) => updateFilter("neighborhood", event.target.value)} placeholder="Ex.: Savassi" /></label>
              <label><span>Área mínima (m²)</span><input type="number" min="0" step="0.01" inputMode="decimal" value={filters.minArea} onChange={(event) => updateFilter("minArea", event.target.value)} placeholder="Sem mínimo" /></label>
              <label><span>Área máxima (m²)</span><input type="number" min="0" step="0.01" inputMode="decimal" value={filters.maxArea} onChange={(event) => updateFilter("maxArea", event.target.value)} placeholder="Sem máximo" /></label>
              <label><span>Banheiros (mínimo)</span><select value={filters.bathrooms} onChange={(event) => updateFilter("bathrooms", event.target.value)}><option value="">Qualquer</option>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value} ou mais</option>)}</select></label>
              <label><span>Vagas (mínimo)</span><select value={filters.parkingSpaces} onChange={(event) => updateFilter("parkingSpaces", event.target.value)}><option value="">Qualquer</option>{[1, 2, 3, 4, 5].map((value) => <option key={value} value={value}>{value} ou mais</option>)}</select></label>
            </div>
            <p className="field-hint">Os critérios devem ser atendidos por um mesmo anúncio ativo. Cidade, UF e bairro são específicos; o campo de localização continua opcional.</p>
          </details>
        </form>
      </section>);
}
