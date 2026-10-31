# Placecheck — Agregador de Imóveis

MVP de um buscador e agregador de anúncios imobiliários. O projeto segue o plano em [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md) e começa como um monólito Django modular.

## Desenvolvimento local

1. Copie `.env.example` para `.env`.
2. Suba o ambiente:

   ```bash
   docker compose up --build
   ```

3. Acesse:
   - API: http://localhost:8000/health/
   - Frontend: http://localhost:5173

O backend executa as migrations automaticamente ao iniciar. Para executar os testes sem Docker, instale as dependências de `backend/requirements.txt` em um ambiente Python 3.12.

Possíveis sources:
- Ideal Imóveis
- Quarto Andar

## Banco fictício para testes

Com os serviços em execução, carregue o dataset local:

```bash
docker compose exec backend python manage.py seed_demo
```

São 30 imóveis e 60 anúncios de três fontes fictícias, em Belo Horizonte,
Salvador, São Paulo, Rio de Janeiro e Curitiba. Inclui venda e aluguel,
apartamentos, casas, terrenos e salas comerciais, ofertas duplicadas,
históricos de queda/aumento de preço, preço não informado e anúncios inativos.
O comando utiliza o pipeline de normalização e deduplicação. Pode ser executado
novamente: anúncios existentes (inclusive alterações manuais) são preservados.
As fontes `demo-fonte-*` ficam fora da sincronização automática, e os links
usam domínios `.example`, sem anúncios reais no destino.

Exemplos para testar no navegador:

- Lista paginada: http://localhost:8000/api/properties/
- Salvador: http://localhost:8000/api/properties/?city=Salvador
- Venda até R$ 700 mil: http://localhost:8000/api/properties/?transaction_type=sale&max_price=700000
- Menor preço primeiro: http://localhost:8000/api/properties/?ordering=price
- Comparar ofertas: abra `/api/properties/{id}/` com um ID retornado pela lista.

O frontend em http://localhost:5173 consulta estes dados pela API: filtre por cidade,
tipo, preço e quartos, alterne entre compra/aluguel e clique em “Ver ofertas”
para comparar fontes. O proxy do Vite usa o backend do Docker Compose.


## Estado atual

Domínio e ingestão (Sprints 1–4), deduplicação conservadora (Sprint 5), API
(Sprint 6) e busca/comparação no frontend (Sprint 7) possuem implementação e testes,
mas ainda há lacunas de aceite e operação com dados reais. A auditoria de
2026-10-31 registrou 43 testes backend aprovados e build frontend aprovado;
sincronização assíncrona real e fluxo até anúncio real ainda precisam de validação.
Consulte [a auditoria do MVP](docs/mvp-audit.md) para os defeitos de normalização,
permissões e reconciliação e as decisões em andamento. A integração com fontes reais
depende de autorização; o dataset local é inteiramente fictício. Sprint 8 tem
registro de redirects, mas as demais métricas ainda não foram implementadas.

### Correção dos dados

- A persistência é atômica, incluindo atualização, histórico e associação. A fonte
  é bloqueada durante a escrita para serializar inserções/atualizações concorrentes.
- Uma associação automática exige coordenadas a até 25 m, área com diferença de
  no máximo 2%, título com similaridade de pelo menos 90% e identificador explícito
  `unidade`/`apto` igual. Cidade, estado, tipo e características conhecidas não podem
  conflitar. Características genéricas ou coordenadas de um prédio não bastam.
- `DEDUP_MAX_AUTO_DISTANCE_METERS` e `DEDUP_AUTO_THRESHOLD` podem ser definidos nas
  configurações Django. O limiar padrão de score é 0,90, além das evidências obrigatórias.
- Casos possíveis ficam separados. `MatchDecision` registra candidato, score,
  razões e Property anterior/nova, consultáveis no admin. Grupos ambíguos não são
  unidos automaticamente. Correções podem separar associações antigas; dados
  melhores podem permitir associações antes impossíveis.
- Cada ingestão reavalia a associação. Para reavaliar o inventário existente:
  `docker compose exec backend python manage.py reevaluate_matches`.
  Properties sem ofertas ficam fora da busca; seus IDs são preservados para auditoria.
- Inativar outra oferta não troca o ID do imóvel durante a reingestão da oferta
  restante. Ofertas inativas não obrigam a criação de outro Property.
- Associações e separações bloqueiam os Properties envolvidos em ordem de ID e
  revalidam os membros ativos antes de decidir. Ingestões concorrentes só compartilham
  um grupo quando todas as ofertas são compatíveis. Os bloqueios permitem referências
  de auditoria sem impedir atualizações concorrentes de anúncios do mesmo grupo.
- A projeção do Property usa valores mais frequentes entre anúncios ativos. Empates
  favorecem o anúncio mais recente com valor informado. Coordenadas são escolhidas
  como par; valores ausentes não substituem informações conhecidas. Inativar uma
  fonte pelo pipeline recalcula os imóveis afetados.

### Busca e inteligência de preços

Filtros de uma requisição devem ser satisfeitos pelo mesmo anúncio ativo.
`min_price`, quantidade de ofertas e detalhes são calculados sobre essa população.
Os filtros aceitos são `city`, `state`, `neighborhood`, `location`, `q`,
`transaction_type`, `property_type`, `min_price`, `max_price`, `min_area`, `max_area`,
`bedrooms`, `bathrooms` e `parking_spaces`. Valores numéricos inválidos e intervalos
invertidos retornam HTTP 400.

`ordering` aceita `price`, `-price`, `area`, `-area`, `price_per_m2`, `-price_per_m2`,
`price_drop`, `-price_drop`, `city`, `-city`, `updated_at` e `-updated_at`.
Datas representam a última captura dos anúncios correspondentes. Valores ausentes
ficam no fim da ordenação. Paginação usa `limit`/`offset`.

Detalhes expõem histórico, preço anterior, inicial, mínimo e máximo registrados,
preço/m², dias desde a primeira captura e percentual de queda desde o preço inicial
(zero em caso de aumento). Sem histórico/preço/área suficientes, métricas ficam nulas.
O frontend conserva filtros, ordenação, página e imóvel aberto na URL, com suporte
à atualização da página e aos botões Voltar/Avançar. Links reais passam por `/out/{id}/`;
fontes fictícias são identificadas e não apontam para ofertas reais.

`Source.rate_limit_per_minute` configura o limite por fonte (padrão 60, mínimo 1).
O limite usa uma janela de 60 segundos no cache compartilhado. O schema JSON está em
`/api/schema/`. O arquivo gerado `celerybeat-schedule*` é ignorado pelo Git.

### Verificação

```bash
docker compose exec backend pytest -q
docker compose exec frontend npm run build
```
