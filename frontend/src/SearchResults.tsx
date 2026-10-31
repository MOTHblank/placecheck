import { Property, TransactionType } from "./api";
import { PropertyCard } from "./PropertyCard";
import { pageSize } from "./search";

export function SearchResults({ properties, count, offset, transaction, ordering, loading, error, onOrder, onPage, onOpen, onClear, onRetry }: {
  properties: Property[]; count: number; offset: number; transaction: TransactionType; ordering: string; loading: boolean; error: boolean;
  onOrder: (value: string) => void; onPage: (offset: number) => void; onOpen: (id: number) => void; onClear: () => void; onRetry: () => void;
}) {
  return <section className="results-section" aria-labelledby="results-title">
    <div className="results-toolbar"><div><p className="section-kicker">Resultados para você</p><h2 id="results-title">Imóveis encontrados</h2><p className="results-count" role="status">{loading ? "Carregando imóveis…" : error ? "Busca indisponível" : `${count} imóveis encontrados`}</p></div>
      <label className="sort-control">Ordenar por<select aria-label="Ordenar resultados" value={ordering} onChange={(event) => onOrder(event.target.value)}>
        <option value="-updated_at">Mais recentes</option><option value="price">Menor preço</option><option value="-price">Maior preço</option><option value="-area">Maior área</option><option value="price_per_m2">Menor preço/m²</option><option value="-price_drop">Maior queda de preço</option>
      </select></label>
    </div>
    {loading ? <div className="property-grid" aria-busy="true" aria-label="Carregando imóveis">{[1, 2, 3].map((id) => <div className="loading-card" key={id} />)}</div>
      : error ? <div className="empty-state" role="alert"><h3>Não foi possível carregar os imóveis</h3><p>Confira os filtros ou tente novamente em instantes.</p><button type="button" onClick={onRetry}>Tentar novamente</button> <button type="button" onClick={onClear}>Limpar filtros</button></div>
        : properties.length > 0 ? <div className="property-grid">{properties.map((property) => <PropertyCard key={property.id} property={property} transaction={transaction} onOpen={() => onOpen(property.id)} />)}</div>
          : <div className="empty-state"><h3>Nenhum imóvel encontrado</h3><p>Tente ampliar sua região ou ajustar os filtros de preço.</p><button type="button" onClick={onClear}>Limpar filtros</button></div>}
    {!loading && !error && count > pageSize && <nav className="pagination" aria-label="Páginas de resultados">
      <button type="button" disabled={offset === 0} onClick={() => onPage(Math.max(0, offset - pageSize))}>Anterior</button>
      <span>Página {Math.floor(offset / pageSize) + 1} de {Math.ceil(count / pageSize)}</span>
      <button type="button" disabled={offset + pageSize >= count} onClick={() => onPage(offset + pageSize)}>Próxima</button>
    </nav>}
  </section>;
}
