import type { ReactNode } from "react";
import { formatPrice, Offer, saleMethodLabels, TransactionType } from "./api";

const kinds: { kind: Offer["price_kind"]; title: string; explanation: string }[] = [
  { kind: "asking", title: "Preços anunciados", explanation: "Valores pedidos pelos anunciantes." },
  { kind: "minimum", title: "Lances e valores mínimos", explanation: "O valor final pode mudar conforme as regras de venda." },
  { kind: "reference", title: "Valores de referência", explanation: "Consulte as condições e o edital na fonte original." },
];

function money(value: string | null, transaction: TransactionType) {
  return value === null ? "Não informado" : formatPrice(value, transaction);
}

function date(value: string | null) {
  if (!value) return "Não informada";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "Não informada" : parsed.toLocaleDateString("pt-BR");
}

function area(value: string | null) {
  if (value === null) return "Não informada";
  const number = Number(value);
  return Number.isFinite(number) ? new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(number) + " m²" : "Não informada";
}

function change(offer: Offer, transaction: TransactionType) {
  if (offer.previous_price === null || offer.price === null) return "Sem variação anterior registrada";
  const previous = Number(offer.previous_price);
  const current = Number(offer.price);
  if (!Number.isFinite(previous) || !Number.isFinite(current)) return "Sem variação anterior registrada";
  const difference = current - previous;
  const comparison = previous > 0 ? " (" + Math.abs(difference / previous * 100).toFixed(1) + "%)" : "";
  return (difference === 0 ? "Sem alteração" : difference > 0 ? "Alta de " + money(String(difference), transaction) + comparison : "Queda de " + money(String(-difference), transaction) + comparison)
    + " · antes " + money(offer.previous_price, transaction);
}

export function OfferComparison({ offers, transaction }: { offers: Offer[]; transaction: TransactionType }) {
  if (!offers.length) return <p>Nenhuma oferta ativa encontrada para esta negociação.</p>;
  const rows: { label: string; render: (offer: Offer) => ReactNode }[] = [
    { label: "Valor informado", render: (offer) => money(offer.price, transaction) },
    { label: "Condomínio", render: (offer) => money(offer.condominium_fee, "sale") },
    { label: "IPTU", render: (offer) => money(offer.iptu, "sale") },
    { label: "Área anunciada", render: (offer) => area(offer.area) },
    { label: "Valor por m²", render: (offer) => money(offer.price_per_m2, "sale") },
    { label: "Última verificação", render: (offer) => date(offer.last_seen_at) },
    { label: "Inventário da fonte", render: (offer) => date(offer.source_inventory_date) },
    { label: "Mudança anterior", render: (offer) => change(offer, transaction) },
  ];
  return <section className="offer-comparison" aria-label="Quadro comparativo de ofertas">
    <h3>Comparação lado a lado</h3>
    <p>Preços anunciados, lances mínimos e referências têm significados diferentes e são apresentados separadamente. Confirme valores, taxas e disponibilidade na fonte.</p>
    {kinds.map(({ kind, title, explanation }) => {
      const group = offers.filter((offer) => offer.price_kind === kind);
      if (!group.length) return null;
      return <section key={kind} className="comparison-group" aria-label={title}>
        <h4>{title}</h4><p>{explanation}</p>
        <div className="comparison-scroll" role="region" tabIndex={0} aria-label={"Tabela: " + title}>
          <table className="comparison-table"><thead><tr><th scope="col">Critério</th>{group.map((offer) =>
            <th scope="col" key={offer.id}><strong>{offer.source}</strong><small>{offer.sale_method ? (saleMethodLabels[offer.sale_method] || offer.sale_method) : "Oferta"} · #{offer.id}</small></th>
          )}</tr></thead><tbody>{rows.map((row) =>
            <tr key={row.label}><th scope="row">{row.label}</th>{group.map((offer) => <td key={offer.id}>{row.render(offer)}</td>)}</tr>
          )}
          <tr><th scope="row">Fonte e atribuição</th>{group.map((offer) =>
            <td key={offer.id}>{offer.attribution_text || offer.source}{offer.source_url && <> · <a href={offer.source_url} target="_blank" rel="noopener noreferrer">Site da fonte</a></>}<div><a href={"#oferta-" + offer.id}>Detalhes e anúncio original</a></div></td>
          )}</tr></tbody></table>
        </div>
      </section>;
    })}
  </section>;
}
