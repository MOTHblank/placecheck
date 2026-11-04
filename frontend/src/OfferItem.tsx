import { formatPrice, Offer, saleMethodLabels, TransactionType } from "./api";


export function OfferItem({ offer, transaction, redirectToken }: { offer: Offer; transaction: TransactionType; redirectToken?: string }) {
  const out = `/out/${offer.id}/${redirectToken ? `?exposure=${encodeURIComponent(redirectToken)}` : ""}`;
  return <article id={`oferta-${offer.id}`} data-exposure-offer={offer.id} className="offer-item"><h3>{offer.source}</h3><strong>{formatPrice(offer.price, transaction)}</strong><p>{offer.description}</p>
    {offer.sale_method && <p>{saleMethodLabels[offer.sale_method] || offer.sale_method} · {offer.price_kind === "minimum" ? "Lance/valor mínimo" : offer.price_kind === "reference" ? "Valor informado a confirmar no edital" : "Preço informado"}</p>}
    {offer.attribution_text && <p>{offer.attribution_text} {offer.source_url && <a href={offer.source_url} target="_blank" rel="noopener noreferrer">Fonte dos dados ↗</a>}</p>}
    {offer.source_inventory_date && <p>Lista de origem: {offer.source_inventory_date.split("-").reverse().join("/")}. Captura com cache diário; confirme a disponibilidade no site oficial.</p>}
    <p>Condomínio: {formatPrice(offer.condominium_fee, "sale")} · IPTU: {formatPrice(offer.iptu, "sale")}</p>
    <p>{offer.days_on_market} dias em acompanhamento · {formatPrice(offer.price_per_m2, "sale")}/m²</p>
    {offer.previous_price !== null && <p>Preço anterior: {formatPrice(offer.previous_price, transaction)} · Menor registrado: {formatPrice(offer.lowest_price, transaction)}</p>}
    {(offer.price_drop_percent ?? 0) > 0 && <p>Queda de {offer.price_drop_percent!.toFixed(1)}% desde a primeira captura.</p>}
    {offer.price_history.length > 0 && <details><summary>Histórico de preços</summary><ul>{offer.price_history.map((item, index) => <li key={`${item.captured_at}-${index}`}>{new Date(item.captured_at).toLocaleDateString("pt-BR")} — {formatPrice(item.price, transaction)}</li>)}</ul></details>}
    {offer.is_demo ? <small>Anúncio fictício para testes. Não há um site de origem real.</small> : <a className="card-link" href={out} target="_blank" rel="noopener noreferrer">Ver anúncio original ↗</a>}
  </article>;
}
