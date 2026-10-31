import { formatPrice, Property, propertyLabels, TransactionType } from "./api";

export function PropertyCard({ property, transaction, onOpen }: { property: Property; transaction: TransactionType; onOpen: () => void }) {
  return <article className="property-card">
    <div className={`property-image property-image-${property.id % 3 + 1}`}><span className="image-label">{property.has_demo_offers ? "Inclui dados de demonstração" : "Imagem ilustrativa"}</span></div>
    <div className="property-content"><div className="property-heading"><div><p className="property-type">{propertyLabels[property.property_type] || property.property_type}</p><h3>{property.neighborhood}</h3><p className="property-location">{property.city} · {property.state}</p></div><span className="offer-count">{property.listing_count} {property.listing_count === 1 ? "oferta" : "ofertas"}</span></div>
      <div className="property-details" aria-label="Características do imóvel"><span>{property.area === null ? "Área não informada" : `${Number(property.area)} m²`}</span><span>{property.bedrooms ?? "—"} quartos</span><span>{property.parking_spaces ?? "—"} vagas</span></div>
      <div className="property-price"><span>A partir de</span><strong>{formatPrice(property.min_price, transaction)}</strong></div><button className="card-link" type="button" onClick={onOpen}>Ver ofertas <span aria-hidden="true">→</span></button>
    </div>
  </article>;
}
