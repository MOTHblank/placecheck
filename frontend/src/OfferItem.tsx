import { useEffect, useRef, useState } from "react";
import { formatPrice, Offer, saleMethodLabels, TransactionType } from "./api";
import { deliverMetric } from "./analytics";


export function OfferItem({ offer, transaction, context }: { offer: Offer; transaction: TransactionType; context: string | null }) {
  const article = useRef<HTMLElement>(null);
  const eventId = useRef(crypto.randomUUID());
  const [redirectToken, setRedirectToken] = useState<string | null>(null);

  useEffect(() => {
    const element = article.current;
    if (!element || !context || offer.is_demo) return;
    let sent = false;
    let disposed = false;
    const observer = new IntersectionObserver((entries) => {
      if (sent || document.visibilityState !== "visible" || !element.closest("dialog")?.open) return;
      if (!entries.some((entry) => entry.isIntersecting && entry.intersectionRect.width > 0 && entry.intersectionRect.height > 0)) return;
      sent = true;
      void deliverMetric({ kind: "exposure", event_id: eventId.current, context, listing_id: offer.id }).then((result) => {
        if (!disposed && result?.accepted && result.redirect_token) setRedirectToken(result.redirect_token);
      });
    });
    observer.observe(element);
    const onVisibility = () => { if (!sent && document.visibilityState === "visible") { observer.unobserve(element); observer.observe(element); } };
    document.addEventListener("visibilitychange", onVisibility);
    return () => { disposed = true; observer.disconnect(); document.removeEventListener("visibilitychange", onVisibility); };
  }, [context, offer.id, offer.is_demo]);

  const out = `/out/${offer.id}/${redirectToken ? `?exposure=${encodeURIComponent(redirectToken)}` : ""}`;
  return <article id={`oferta-${offer.id}`} ref={article} className="offer-item"><h3>{offer.source}</h3><strong>{formatPrice(offer.price, transaction)}</strong><p>{offer.description}</p>
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
