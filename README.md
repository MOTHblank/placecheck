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

### Primeira Fonte real para teste interno (#7/#8)

O [piloto Imóveis Leilão Brasil/CAIXA](docs/ilb-pilot.md) permite buscar uma amostra
real limitada por UF/cidade em um Compose isolado. Ele usa a API pública com
atribuição, cache diário e Celery, distinguindo valor mínimo de preço de venda.
Não há coleta nacional automática; descrição e imagens ficam desligadas. O piloto
legado também desliga histórico por padrão; o conjunto abaixo o habilita no escopo
confirmado. Capturas parciais não inativam ausências. O aceite da #8 segue pendente.

```bash
docker compose -p placecheck-ilb-pilot -f docker-compose.yml -f docker-compose.ilb-pilot.yml up -d --build --wait
docker compose -p placecheck-ilb-pilot -f docker-compose.yml -f docker-compose.ilb-pilot.yml exec -T backend python manage.py setup_ilb_pilot
```

Após o próximo ciclo do Beat (até 15 minutos), abra http://127.0.0.1:25173.

Para reunir os dois mercados de venda confirmados (Salvador/BA e Campinas/SP)
em **um inventário da mesma Fonte**, use o [piloto conjunto](docs/ilb-pilot.md#inventário-conjunto-de-dois-mercados)
com `docker-compose.ilb-joint.yml`, projeto `placecheck-ilb-joint` e frontend
http://127.0.0.1:25175. O escopo é explícito e imutável por Fonte; permanecem
cache diário, capturas parciais e verificação individual de ausências. O conjunto
habilita explicitamente o histórico interno confirmado pelo responsável, com
revogação e remoção pela permissão da Fonte; os pilotos antigos mantêm o padrão
desligado. Essa opção não constitui comparação entre duas Fontes.

Revalidação do conjunto em 05/11/2026: Docker recuperado preservando pastas
temporárias de IPC, sem reset de volumes. Passaram 211 testes no stack
Python 3.12/PostgreSQL 16, incluindo broker Redis real, build Node 22,
Django check/migrations, 14 cenários gerais de navegador e quatro smokes reais
das duas cidades em desktop/celular. Beat → Redis → worker importou e repetiu
quatro ofertas, preservando quatro registros iniciais de preço. A instalação
limpa revelou incompatibilidade Kombu/Redis, corrigida fixando o transporte já
transitivo. Consulte [as evidências, a revisão e a revogação](docs/ilb-joint-acceptance.md).
Falta observar mudança de preço na Fonte real para concluir #8; o ciclo com
mudança passou no stack controlado, mas não substitui essa evidência.

Os insumos e a decisão humana da [#7](https://github.com/MOTHblank/placecheck/issues/7)
foram concluídos para esse escopo interno. A implementação está no
[PR #20](https://github.com/MOTHblank/placecheck/pull/20), com correções integradas
no [PR #21](https://github.com/MOTHblank/placecheck/pull/21). A confirmação não
identifica uma segunda Fonte para #9/#10.
O padrão é uma amostra de dois imóveis de Salvador/BA; o catálogo de origem é
nacional, e o recorte pode ser configurado conforme a documentação do piloto.
As portas são locais e os volumes ficam separados dos dados de desenvolvimento.
Validação inicial da integração (baseline anterior ao conjunto): 101 testes backend, seis regressões Playwright,
Django check/migrations, build
TypeScript/Vite e smoke do piloto em desktop/celular; captura real agendada e 302
para a ficha CAIXA observados. Isso não substitui o aceite real completo de #8.

Revalidação em 04/11/2026: a Fonte existente voltou a sincronizar pelo Beat/worker,
com lista de origem de 03/11. Foram observados dois anúncios recentes em Salvador/BA
e dois em Campinas/SP, em bancos separados da **mesma Fonte**; não é comparação
entre Fontes nem busca conjunta entre os recortes. Passaram 33 regressões ILB e
o smoke real Chromium em desktop/celular em ambos os recortes. A retirada pública
também foi verificada e restaurada. O [aceite por critério](docs/ilb-pilot.md#revalidação-e-aceite-por-critério--04112026)
e a [revisão do contrato publicado](docs/ilb-contract-review.md) distinguem entregas
e pendências daquela data. Histórico/retenção e mercados foram confirmados em
05/11 e a #7 foi encerrada; na #8 falta observar mudança real de preço.
Foi corrigido também o deslocamento de um dia da data do inventário na tabela
comparativa. Build Node 22, 14 testes gerais de navegador (dois smokes reais
ignorados por padrão) e os quatro smokes reais dos dois recortes passaram.

A [verificação individual de disponibilidade](docs/ilb-availability.md) complementa
a captura parcial: consulta somente anúncios conhecidos sem captura recente,
em lotes de até dez, com cadência diária e o rate limit da Fonte. Apenas o 404
JSON validado do detalhe pode inativar uma oferta; falhas preservam os dados.
O último resultado fica no admin de ingestão, sem guardar preço ou corpo HTTP.
Validação anterior ao conjunto: 189 testes backend/PostgreSQL, Django check/migrations e smoke real
desktop/celular passaram. Beat → Redis → worker confirmou a ausência de um anúncio
antigo e o retirou da busca/detalhe/redirect, preservando duas ofertas e a última
captura. As [duas revisões e a correção de transporte](docs/ilb-availability-review.md)
estão documentadas; capturas continuam parciais.

### Estudo de entrada VRSync (#15)

A [matriz de compatibilidade VRSync](docs/vrsync-compatibility.md) confronta
documentação oficial, exemplos sintéticos e o pipeline atual. A decisão do estudo
é usar a API JSON ILB para a primeira Fonte e adiar VRSync. O estudo detalha modalidades
venda/aluguel, periodicidade de preços e IPTU, privacidade e snapshots completos.
Não há provider XML concreto, feed real configurado ou compatibilidade real
comprovada. Uma futura Fonte VRSync precisará de autorização, amostra e ticket
próprios para modalidades, privacidade e snapshots; não amplia o provider JSON da #8.

### Pesquisa da segunda Fonte (#9)

A [avaliação documental](docs/second-source-assessment.md) examina CAIXA direta e
VendasGov. Nenhuma segunda Fonte com permissão e sobreposição suficientes foi
comprovada. CAIXA e ILB compartilham a proveniência; dois canais da mesma oferta
não comprovam condições comerciais independentes. #9/#10 continuam pendentes.

A [qualificação da ImóveisFaixa](docs/imoveisfaixa-assessment.md) registra outra
candidata com API anunciada para portais, mas ainda sem permissão e contrato
verificados. A documentação indexada e as falhas de abertura direta são
distintas; nenhuma chave, assinatura ou coleta foi iniciada.

A [busca por permissões públicas](docs/public-api-candidates.md) segue a orientação
do responsável de procurar outra Fonte sem depender de autorização direta.
LeilôAI permite exibir seu widget com atribuição, mas a importação/retenção para
comparação e histórico ainda não está qualificada; Tu Lugar proíbe republicar
anúncios, e a licença Guru dos Imóveis cobre séries agregadas. Permissão pública
suficiente dispensa parceria privada. #9/#10 permanecem abertas até comprovar
o uso necessário e a sobreposição real.

A [pesquisa complementar de feeds](docs/permitted-feed-search.md) encontrou no
PNCP permissão geral de reutilização. Uma consulta limitada à CAIXA retornou dez
contratações de serviços/tecnologia, sem ofertas imobiliárias identificadas;
não comprova sobreposição. Hasta licencia relatórios, enquanto os documentos
de Katular e Pro Leilão examinados não qualificaram a importação pretendida.

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
com correções dos tickets #2–#6. A validação de 2026-10-31 passou com 68 testes
backend, build TypeScript/Vite e seis testes de navegador (desktop e celular).
O Compose isolado demonstrou Beat → Redis → worker, repetição, mudança de preço
e inativação após inventário completo vazio, usando somente dados fictícios.
Consulte [a auditoria do MVP](docs/mvp-audit.md) para a baseline anterior e as
decisões pendentes. A integração com fontes reais
depende do escopo permitido; o dataset padrão continua fictício e o piloto real
fica isolado. A jornada e o CTR da Sprint 8 estão implementados no #12 conforme
o [guia de analytics](docs/analytics.md). O [relatório de inventário](docs/inventory-report.md)
do #13 apresenta estoque publicável, agrupamentos e sincronização por Fonte.

O [contrato das métricas](docs/metrics-contract.md), aprovado em 2026-10-31 no #11,
define contagem, CTR, atribuição, exclusões, retenção e testes para #12/#13.
A instrumentação e a limpeza de 90 dias estão implementadas. Desenvolvimento e
piloto interno usam `ANALYTICS_EXCLUDE_ALL=1`; o stack de aceitação simula tráfego
elegível somente em seu banco separado.

```bash
docker compose exec -T backend python manage.py journey_report
docker compose exec -T backend python manage.py inventory_report
docker compose exec -T backend python manage.py purge_analytics
```

O relatório é restrito ao acesso autorizado ao ambiente, sem endpoint público.
Consulte o guia para período, timezone, Fonte, mercado, exclusões e limitações.
`inventory_report` mede o estado atual e aceita Fonte/mercado/timezone; não aceita
período nem interpreta redução por agrupamento como acurácia.
Validação do #12: 135 testes backend, build TypeScript/Vite, verificações Django e
12 testes Playwright em desktop/celular passaram num Compose isolado.

Revalidação de 04/11/2026: corrigida a exposição de ofertas na nova tabela do
comparador, compartilhando a contagem com o cartão da mesma oferta. O Compose
isolado subiu com os seis serviços; passaram 149 testes backend/PostgreSQL,
Django check/migrations, build no Node 22 e 14 testes Chromium desktop/celular.
O aceite comprovou CTR de 50%, estoque 28/14, limpeza via Redis/worker e ingestão
agendada com repetição, histórico e ausência completa. #12/#13 estão encerradas;
a correção da #12 foi integrada em `main` pelo [PR #16](https://github.com/MOTHblank/placecheck/pull/16).
autorizações e comparação real seguem pendentes em #7–#10/#14. Veja [as evidências e os
comandos de validação](docs/analytics.md#revalidação-em-04112026).

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
Discovery e fetch compartilham uma janela de 60 segundos no cache. Ao atingir o
limite, a task espera 60 segundos; falhas transitórias têm até três retries com
backoff. Discovery/fetch/processamento/reconciliação têm limites de 30 s (soft) e
45 s (hard). Configuração e dados inválidos falham sem retry transitório. O schema JSON está em
`/api/schema/`. O arquivo gerado `celerybeat-schedule*` é ignorado pelo Git.

### Operação de Fontes e sincronização

- `is_active=False` pausa a coleta e preserva publicação; `is_published=False`
  retira as ofertas de busca, detalhes, contagens e redirects. Para revogar também
  a coleta, desligue ambos no admin de Source.
- `can_store_description=False` remove descrições armazenadas e impede novas
  gravações pelo pipeline/admin. `can_retain_price_history=False` remove o histórico
  existente e impede novas capturas de histórico; a retirada pública, por si só,
  conserva o histórico quando permitido. Não são coletadas imagens.
- Atualize permissões usando `Source.save()` ou o admin, que serializam as mudanças
  com ingestões e recalculam Properties; não use `QuerySet.update()` para essas operações.
- Atualize preços via provider/normalização/`persist_listing`. No admin, o preço de
  um anúncio existente, sua identidade (Fonte/ID externo) e o histórico são somente leitura; um cadastro manual inicial
  registra seu preço no histórico. A persistência valida os campos do Listing antes
  de gravar, dentro da mesma transação de histórico e agrupamento.
- `SyncRun`, disponível em `/admin/ingestion/syncrun/`, registra estado, completude,
  contagens, tipo da falha e horários. Filtre por Fonte e estado `succeeded` para
  consultar a última execução completa; `partial` nunca reconcilia ausências.
- Nova execução substitui a anterior ainda aberta. Escrita e reconciliação usam
  o ID da execução sob bloqueio da Fonte; tarefas antigas deixam de alterar dados.
  Uma captura que falhou pode ter atualizado ofertas válidas antes da falha, mas
  não inativa ausências. Interrupção abrupta do worker pode deixar execução aberta;
  a próxima execução a substitui. Não há garantia de snapshot imutável de um arquivo
  modificado durante a captura: um parceiro real deve fornecer esse contrato.
- O provider manual exige configuração explícita: `MANUAL_PROVIDER_RECORDS`, por
  slug, ou `MANUAL_PROVIDER_RECORDS_FILE` apontando para JSON `{slug: {referência: payload}}`.
  Fonte ausente/arquivo inválido é erro; `{slug: {}}` confirma inventário completo
  vazio. `ManualProvider(records, complete=False)` representa uma captura parcial;
  providers futuros são parciais por padrão e devem confirmar completude.
- `DEDUP_SCORE_WEIGHTS` aceita `compatible`, `coordinates`, `area` e `title`
  (padrões 0,3/0,3/0,2/0,2), com pesos finitos não negativos somando até 1.
  Nenhum peso substitui as evidências de identidade obrigatórias. Candidatos são
  filtrados por cidade/estado, tipo, área e características conhecidas compatíveis.
  Bairro usa comparação canônica no score, preservando grafias com/sem acentos.
  Ofertas ativas retiradas da publicação ainda restringem a identidade dos grupos
  enquanto seus dados são retidos, evitando comparações incompatíveis na republicação.
- `Source.is_demo` identifica demonstração na API e interface. O dataset conhecido
  é marcado pela migration e por `seed_demo`; misturas são identificadas no card,
  e cada oferta fictícia tem sua saída desabilitada.

### Verificação

```bash
docker compose exec backend pytest -q
docker compose exec frontend npm run build
```

O frontend usa versões exatas, `package-lock.json` e `npm ci` (Node 22).
Se o lockfile mudar com um volume de dependências já existente, execute
`docker compose exec frontend npm ci` e reinicie o frontend antes de validar.

Para repetir o aceite em um projeto Compose separado, com volumes próprios e
portas 18000/15173 (Compose 2.24.4+ para `!override`):

```bash
docker compose -p placecheck-acceptance -f docker-compose.yml -f docker-compose.acceptance.yml up -d --build --wait
docker compose -p placecheck-acceptance -f docker-compose.yml -f docker-compose.acceptance.yml exec -T backend python manage.py verify_async_ingestion
docker compose -p placecheck-acceptance -f docker-compose.yml -f docker-compose.acceptance.yml exec -T backend python manage.py prepare_browser_fixtures
```

O primeiro comando de gestão observa o agendamento real (intervalo de 3 s somente
no override), sem enfileirar diretamente as capturas. O segundo prepara 14 imóveis
com duas ofertas em Testópolis e o dataset demo, apenas nesse ambiente. As fontes
`TEST` simulam publicação para testar rótulos e saída; `fixture.invalid` não é um
parceiro real. Não carregue essas fixtures no ambiente do piloto real.

```bash
cd frontend
npm ci
npx playwright install chromium
npm run test:e2e
```

Os testes usam http://127.0.0.1:15173 por padrão (`PLAYWRIGHT_BASE_URL` permite
alterar). Exercitam carregamento, erro recuperável, vazio, busca, ordenação mobile,
paginação, URL/Voltar/Avançar, comparação, histórico e demonstração. A saída executa
o endpoint real e verifica HTTP 302/Location, interrompendo a navegação na fronteira
do redirect para evitar contato externo. Screenshots/traces ficam em
`frontend/test-results/`. Health: http://localhost:18000/health/; proxy:
http://localhost:15173/api/properties/. Use `down` com os mesmos argumentos para
parar o stack isolado, sem `-v`; volumes do desenvolvimento ficam preservados.

Continuam pendentes a segunda autorização #9, aceites das integrações reais #8/#10,
aceite real integrado #14. Não há alegação
de MVP integralmente concluído nem alteração da spec pai #1.
As duas revisões independentes e suas correções estão em
[`docs/implementation-review.md`](docs/implementation-review.md).


## Busca avançada, comparação e buscas locais

O formulário da página inicial inclui filtros avançados recolhíveis para cidade, UF, bairro,
área mínima/máxima, banheiros e vagas, além dos filtros básicos. Os critérios são
combinados no mesmo anúncio ativo; URLs de busca preservam os critérios durante a
navegação, ordenação e paginação.

O diálogo de ofertas apresenta tabelas comparativas por tipo de valor
(preço anunciado, lance mínimo e valor de referência), com condomínio, IPTU, área,
R$/m², data de verificação e mudanças de preço. Atribuição das fontes e saídas
para os anúncios originais continuam disponíveis.

Em **Buscas salvas**, o usuário pode salvar a busca aplicada com nome, renomear,
reabrir, excluir e exportar/importar arquivo JSON no formato
`{"version":1,"searches":[...]}`. O armazenamento usa somente `localStorage`
do navegador (máximo de 20 buscas e 32 KB); importações são verificadas e
não são enviadas para o servidor. Alterações e limpeza dos dados do navegador
podem remover as buscas, portanto utilize a exportação para uma cópia.
