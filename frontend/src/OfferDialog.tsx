import { useEffect, useRef, useState } from "react";
import { formatPrice, getProperty, PropertyDetail, propertyLabels, saleMethodLabels, TransactionType } from "./api";

export function OfferDialog({ id, params, transaction, onClose }: { id: number; params: string; transaction: TransactionType; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const element = dialog.current!;
    element.showModal();
    return () => element.close();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setError(false);
    setProperty(null);
    getProperty(id, params, controller.signal).then((value) => { if (!controller.signal.aborted) setProperty(value); }).catch(() => {
      if (!controller.signal.aborted) setError(true);
    });
    return () => controller.abort();
  }, [id, params, attempt]);

  return <dialog ref={dialog} className="offer-dialog" aria-labelledby="offers-title" onClose={(event) => { if (!event.currentTarget.open) onClose(); }}>
    <div className="dialog-heading"><h2 id="offers-title">Comparar ofertas</h2><button type="button" className="dialog-close" onClick={onClose} aria-label="Fechar ofertas">×</button></div>
    {error ? <div role="alert"><p>Não foi possível carregar as ofertas.</p><button className="card-link" onClick={() => setAttempt((value) => value + 1)}>Tentar novamente</button></div>
      : !property ? <p role="status">Carregando ofertas…</p>
        : <><p>{propertyLabels[property.property_type] || property.property_type} — {property.neighborhood}, {property.city}</p>
          <div className="offer-list">{property.listings.filter((offer) => offer.transaction_type === transaction).map((offer) => {
            const isDemo = offer.is_demo;
            return <article className="offer-item" key={offer.id}><h3>{offer.source}</h3><strong>{formatPrice(offer.price, transaction)}</strong><p>{offer.description}</p>
              {offer.sale_method && <p>{saleMethodLabels[offer.sale_method] || offer.sale_method} · {offer.price_kind === "minimum" ? "Lance/valor mínimo" : offer.price_kind === "reference" ? "Valor informado a confirmar no edital" : "Preço informado"}</p>}
              {offer.attribution_text && <p>{offer.attribution_text} {offer.source_url && <a href={offer.source_url} target="_blank" rel="noopener noreferrer">Fonte dos dados ↗</a>}</p>}
              {offer.source_inventory_date && <p>Lista de origem: {offer.source_inventory_date.split("-").reverse().join("/")}. Captura com cache diário; confirme a disponibilidade no site oficial.</p>}
              <p>Condomínio: {formatPrice(offer.condominium_fee, "sale")} · IPTU: {formatPrice(offer.iptu, "sale")}</p>
              <p>{offer.days_on_market} dias em acompanhamento · {formatPrice(offer.price_per_m2, "sale")}/m²</p>
              {offer.previous_price !== null && <p>Preço anterior: {formatPrice(offer.previous_price, transaction)} · Menor registrado: {formatPrice(offer.lowest_price, transaction)}</p>}
              {(offer.price_drop_percent ?? 0) > 0 && <p>Queda de {offer.price_drop_percent!.toFixed(1)}% desde a primeira captura.</p>}
              {offer.price_history.length > 0 && <details><summary>Histórico de preços</summary><ul>{offer.price_history.map((item, index) => <li key={`${item.captured_at}-${index}`}>{new Date(item.captured_at).toLocaleDateString("pt-BR")} — {formatPrice(item.price, transaction)}</li>)}</ul></details>}
              {isDemo ? <small>Anúncio fictício para testes. Não há um site de origem real.</small> : <a className="card-link" href={`/out/${offer.id}/`} target="_blank" rel="noopener noreferrer">Ver anúncio original ↗</a>}
            </article>;
          })}</div>
        </>}
  </dialog>;
}
