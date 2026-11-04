import { useEffect, useRef, useState } from "react";
import { getProperty, PropertyDetail, propertyLabels, TransactionType } from "./api";
import { deliverMetric } from "./analytics";
import { OfferItem } from "./OfferItem";
import { OfferComparison } from "./OfferComparison";

export function OfferDialog({ id, params, transaction, onClose }: { id: number; params: string; transaction: TransactionType; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const viewId = useRef(crypto.randomUUID());
  const [context, setContext] = useState<string | null>(null);
  const [redirectTokens, setRedirectTokens] = useState<Record<number, string>>({});

  useEffect(() => {
    const element = dialog.current!;
    element.showModal();
    return () => element.close();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setError(false);
    setProperty(null);
    getProperty(id, params, controller.signal).then((value) => {
      if (controller.signal.aborted) return;
      setProperty(value);
      if (value.analytics_receipt) void deliverMetric({ kind: "view", event_id: viewId.current, receipt: value.analytics_receipt }).then((result) => {
        if (!controller.signal.aborted && result?.accepted && result.context_token) setContext(result.context_token);
      });
    }).catch(() => {
      if (!controller.signal.aborted) setError(true);
    });
    return () => controller.abort();
  }, [id, params, attempt]);

  useEffect(() => {
    const element = dialog.current;
    if (!element || !context || !property) return;
    const eligible = new Set(property.listings.filter((offer) => !offer.is_demo && offer.transaction_type === transaction).map((offer) => offer.id));
    const targets = Array.from(element.querySelectorAll<HTMLElement>("[data-exposure-offer]"))
      .filter((target) => eligible.has(Number(target.dataset.exposureOffer)));
    // All presentations share one identity and redirect token per offer/opening.
    const sent = new Set<number>();
    let disposed = false;
    const observer = new IntersectionObserver((entries) => {
      if (document.visibilityState !== "visible" || !element.open) return;
      for (const entry of entries) {
        const listingId = Number((entry.target as HTMLElement).dataset.exposureOffer);
        if (sent.has(listingId) || !entry.isIntersecting || entry.intersectionRect.width <= 0 || entry.intersectionRect.height <= 0) continue;
        sent.add(listingId);
        void deliverMetric({ kind: "exposure", event_id: crypto.randomUUID(), context, listing_id: listingId }).then((result) => {
          if (!disposed && result?.accepted && result.redirect_token) {
            const token = result.redirect_token;
            setRedirectTokens((current) => ({ ...current, [listingId]: token }));
          }
        });
      }
    });
    targets.forEach((target) => observer.observe(target));
    const onVisibility = () => {
      if (document.visibilityState === "visible") targets.forEach((target) => {
        if (!sent.has(Number(target.dataset.exposureOffer))) { observer.unobserve(target); observer.observe(target); }
      });
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => { disposed = true; observer.disconnect(); document.removeEventListener("visibilitychange", onVisibility); };
  }, [context, property, transaction]);

  return <dialog ref={dialog} className="offer-dialog" aria-labelledby="offers-title" onClose={(event) => { if (!event.currentTarget.open) onClose(); }}>
    <div className="dialog-heading"><h2 id="offers-title">Comparar ofertas</h2><button type="button" className="dialog-close" onClick={onClose} aria-label="Fechar ofertas">×</button></div>
    {error ? <div role="alert"><p>Não foi possível carregar as ofertas.</p><button className="card-link" onClick={() => setAttempt((value) => value + 1)}>Tentar novamente</button></div>
      : !property ? <p role="status">Carregando ofertas…</p>
        : <><p>{propertyLabels[property.property_type] || property.property_type} — {property.neighborhood}, {property.city}</p>
          <OfferComparison offers={property.listings.filter((offer) => offer.transaction_type === transaction)} transaction={transaction} />
          <div className="offer-list">{property.listings.filter((offer) => offer.transaction_type === transaction).map((offer) =>
            <OfferItem key={offer.id} offer={offer} transaction={transaction} redirectToken={redirectTokens[offer.id]} />)}</div>
        </>}
  </dialog>;
}
