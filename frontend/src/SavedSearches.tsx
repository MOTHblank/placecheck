import { useState } from "react";
import { propertyLabels } from "./api";
import { initialFilters, orderings, SearchFilters, SearchState } from "./search";

export type SavedSearch = {
  id: string;
  name: string;
  filters: SearchFilters;
  ordering: string;
};

const key = "placecheck.saved-searches.v1";
const version = 1;
const maxSearches = 20;
const maxBytes = 32 * 1024;

function documentFor(searches: SavedSearch[]) {
  return JSON.stringify({ version, searches }, null, 2);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validFilters(raw: unknown): SearchFilters | null {
  if (!isRecord(raw)) return null;
  const filters = { ...initialFilters };
  for (const field of Object.keys(initialFilters) as (keyof SearchFilters)[]) {
    const value = raw[field];
    if (typeof value !== "string" || value.length > 300) return null;
    // Validated below against the supported search vocabulary.
    filters[field] = value as never;
  }
  if (filters.transaction !== "sale" && filters.transaction !== "rent") return null;
  if (!["", "apartment", "house", "land", "commercial", "other"].includes(filters.propertyType)) return null;
  if (filters.location.length > 240 || filters.city.length > 120 || filters.neighborhood.length > 120) return null;
  if (filters.state && !/^[A-Z]{2}$/.test(filters.state)) return null;
  for (const field of ["minPrice", "maxPrice", "minArea", "maxArea"] as const) {
    const value = filters[field];
    if (value && (!/^\d+(?:\.\d{1,2})?$/.test(value) || value.length > 16 || Number(value) > 999999999999)) return null;
  }
  for (const field of ["bedrooms", "bathrooms", "parkingSpaces"] as const) {
    const value = filters[field];
    if (value && (!/^\d+$/.test(value) || Number(value) > 100)) return null;
  }
  return filters;
}

function parseSearch(raw: unknown): SavedSearch | null {
  if (!isRecord(raw) || typeof raw.id !== "string" || !/^[\w-]{1,80}$/.test(raw.id)) return null;
  if (typeof raw.name !== "string" || !raw.name.trim() || raw.name.trim().length > 60) return null;
  if (typeof raw.ordering !== "string" || !orderings.includes(raw.ordering)) return null;
  const filters = validFilters(raw.filters);
  return filters ? { id: raw.id, name: raw.name.trim(), filters, ordering: raw.ordering } : null;
}

function parseDocument(raw: unknown): SavedSearch[] | null {
  if (!isRecord(raw) || raw.version !== version || !Array.isArray(raw.searches) || raw.searches.length > maxSearches) return null;
  const searches = raw.searches.map(parseSearch);
  if (searches.some((search) => search === null)) return null;
  return searches as SavedSearch[];
}

function readLocal(): SavedSearch[] {
  try {
    const value = localStorage.getItem(key);
    if (!value || new TextEncoder().encode(value).length > maxBytes) return [];
    return parseDocument(JSON.parse(value)) || [];
  } catch {
    return [];
  }
}

function summary(filters: SearchFilters) {
  const parts = [filters.transaction === "sale" ? "Compra" : "Aluguel", filters.query,
    filters.location, filters.city, filters.state, filters.neighborhood,
    filters.propertyType && propertyLabels[filters.propertyType],
    filters.minPrice && "a partir de R$ " + Number(filters.minPrice).toLocaleString("pt-BR"),
    filters.maxPrice && "até R$ " + Number(filters.maxPrice).toLocaleString("pt-BR"),
    filters.minArea && "mín. " + filters.minArea + " m²",
    filters.maxArea && "máx. " + filters.maxArea + " m²",
    filters.bedrooms && filters.bedrooms + "+ quartos",
    filters.bathrooms && filters.bathrooms + "+ banheiros",
    filters.parkingSpaces && filters.parkingSpaces + "+ vagas"];
  return parts.filter(Boolean).join(" · ");
}

export function SavedSearches({ activeSearch, onOpen }: {
  activeSearch: SearchState;
  onOpen: (search: SavedSearch) => void;
}) {
  const [saved, setSaved] = useState<SavedSearch[]>(readLocal);
  const [name, setName] = useState("");
  const [draftNames, setDraftNames] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState("");

  function persist(next: SavedSearch[], message: string): boolean {
    const payload = documentFor(next);
    if (next.length > maxSearches || new TextEncoder().encode(payload).length > maxBytes) {
      setNotice("Limite de 20 buscas ou 32 KB atingido. Remova uma busca antes de continuar.");
      return false;
    }
    try {
      localStorage.setItem(key, payload);
      setSaved(next);
      setNotice(message);
      return true;
    } catch {
      setNotice("O navegador bloqueou o armazenamento local ou está sem espaço.");
      return false;
    }
  }

  function saveCurrent() {
    const title = name.trim();
    if (!title || title.length > 60) {
      setNotice("Informe um nome com até 60 caracteres.");
      return;
    }
    if (saved.length >= maxSearches) {
      setNotice("Limite de 20 buscas salvas atingido.");
      return;
    }
    const entry: SavedSearch = { id: crypto.randomUUID(), name: title, filters: { ...activeSearch.filters }, ordering: activeSearch.ordering };
    if (persist([entry, ...saved], "Busca salva neste navegador.")) setName("");
  }

  function rename(item: SavedSearch) {
    const updated = (draftNames[item.id] ?? item.name).trim();
    if (!updated || updated.length > 60) {
      setNotice("O nome deve conter de 1 a 60 caracteres.");
      return;
    }
    if (persist(saved.map((entry) => entry.id === item.id ? { ...entry, name: updated } : entry), "Nome atualizado.")) {
      setDraftNames((current) => {
        const next = { ...current };
        delete next[item.id];
        return next;
      });
    }
  }

  function exportJson() {
    const objectUrl = URL.createObjectURL(new Blob([documentFor(saved)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = "placecheck-buscas.json";
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
  }

  async function importJson(file: File) {
    if (file.size > maxBytes) {
      setNotice("O arquivo deve ter no máximo 32 KB.");
      return;
    }
    try {
      const entries = parseDocument(JSON.parse(await file.text()));
      if (!entries) {
        setNotice("Arquivo inválido ou versão incompatível. Use uma exportação do Placecheck.");
        return;
      }
      const signatures = new Set(saved.map((item) => JSON.stringify([item.name, item.filters, item.ordering])));
      const next = [...saved];
      let added = 0;
      for (const entry of entries) {
        const signature = JSON.stringify([entry.name, entry.filters, entry.ordering]);
        if (signatures.has(signature)) continue;
        if (next.length >= maxSearches) break;
        next.push({ ...entry, id: crypto.randomUUID() });
        signatures.add(signature);
        added++;
      }
      if (!added) {
        setNotice("Nenhuma busca nova para importar.");
        return;
      }
      persist(next, added + " busca(s) importada(s) localmente.");
    } catch {
      setNotice("Não foi possível ler o arquivo JSON.");
    }
  }

  return <section className="saved-searches" aria-labelledby="saved-search-title">
    <div className="saved-search-heading"><div><p className="section-kicker">Seu espaço</p><h2 id="saved-search-title">Buscas salvas</h2></div><small>Somente neste navegador · sem cadastro</small></div>
    <form className="save-current-search" onSubmit={(event) => { event.preventDefault(); saveCurrent(); }}>
      <label htmlFor="saved-search-name">Nome para a busca atual</label>
      <input id="saved-search-name" maxLength={60} value={name} onChange={(event) => setName(event.target.value)} placeholder="Ex.: apartamentos na Savassi" required />
      <button type="submit">Salvar busca</button>
    </form>
    <p className="saved-current-summary">{summary(activeSearch.filters)}</p>
    <details className="saved-search-list">
      <summary>Ver buscas salvas ({saved.length})</summary>
      {saved.length ? <ul>{saved.map((item) => <li key={item.id}>
        <div className="saved-search-item">
          <input aria-label={"Nome da busca " + item.name} maxLength={60} value={draftNames[item.id] ?? item.name}
            onChange={(event) => setDraftNames((current) => ({ ...current, [item.id]: event.target.value }))} />
          <button type="button" onClick={() => rename(item)}>Salvar nome</button>
          <button type="button" className="saved-primary" onClick={() => onOpen(item)}>Abrir busca</button>
          <button type="button" onClick={() => persist(saved.filter((entry) => entry.id !== item.id), "Busca removida.")}>Excluir</button>
        </div><small>{summary(item.filters)}</small>
      </li>)}</ul> : <p>Nenhuma busca salva ainda.</p>}
      <div className="saved-search-transfer">
        <button type="button" onClick={exportJson} disabled={!saved.length}>Exportar JSON</button>
        <label>Importar JSON <input aria-label="Arquivo JSON de buscas salvas" type="file" accept=".json,application/json"
          onChange={(event) => {
            const file = event.currentTarget.files?.[0];
            event.currentTarget.value = "";
            if (file) void importJson(file);
          }} /></label>
      </div>
    </details>
    {notice && <p className="saved-search-notice" role="status">{notice}</p>}
  </section>;
}
