# Verificação individual de disponibilidade da ILB

Complementa o [piloto existente](ilb-pilot.md) e a lacuna de remoção de #8.
Capturas de busca continuam **parciais**: ausência numa página nunca inativa
ofertas. A nova verificação só consulta IDs que já existem no banco da Fonte.

## Contrato aceito

O [OpenAPI do operador](https://www.imoveisleilaobrasil.com.br/api/openapi.json)
documenta `GET /api/imovel/{id}` e 404 para ausência na lista atual. Uma consulta
pontual de contrato em 04/11/2026 retornou `application/json` com
`{"erro":"nao encontrado"}` para um ID inexistente. Esse ID não foi persistido
nem inserido como oferta. A verificação usa exclusivamente a API pública com
User-Agent Placecheck; não consulta a página da CAIXA nem segue redirects.

Para confirmar ausência são necessários HTTP 404, tipo JSON e esse marcador
exato. HTML, corpo vazio/truncado, JSON inesperado, 403, 429, 5xx, timeout e erro
de transporte não constituem ausência. Mudança do contrato falha preservando
o anúncio. Um 200 precisa conter os dados esperados do mesmo ID/mercado e passar
pela validação do provider. Não é suficiente receber qualquer JSON.

Ausência significa **fora da lista da ILB**, sem inferir venda ou sua causa.
O código não declara snapshot completo, disponibilidade em tempo real ou SLA
de retirada. Histórico de preços, imagens e descrições continuam desabilitados.

## Agendamento e limites

Celery Beat agenda `apps.sources.tasks.queue_ilb_availability_checks` no mesmo
intervalo configurado para sincronização (900 s normalmente). O scheduler só
atua com DEBUG e piloto explicitamente habilitados, sobre a Source ILB ativa,
publicada e não demo, respeitando tipo de provider e escopo imutável configurado.

Por ciclo, seleciona no máximo dez anúncios ativos sem captura nas últimas 24 h
e sem verificação individual registrada nesse intervalo. Os não verificados
e os resultados mais antigos vêm primeiro. Anúncios da página recentemente
capturada não geram consultas de detalhe adicionais.

Cada anúncio usa a task `check_ilb_listing_availability`, com timeout de rede de
8 s, corpo de até 1 MiB, limites Celery de 30 s soft/45 s hard e lock Redis de
60 s. Discovery/fetch/verificações compartilham o rate limit por Source.
Ao esgotá-lo, a task espera 60 s para tentar novamente, sem HTTP nem inativação.
Falhas transitórias recebem até três retries com backoff; depois, disponibilidade
fica desconhecida e o anúncio é preservado. Sucesso ou falha final registrados
impedem nova consulta por 24 h. Falha de worker/infra antes do registro pode
ser retomada num ciclo seguinte; não se promete uma única tentativa em falhas.

Depois de adquirir o lock, a task relê a elegibilidade para evitar baixar de
novo uma checagem que outro worker acabou de concluir. Antes da gravação, a
camada de ingestão bloqueia a Fonte e revalida a versão da Source, publicação,
coleta, mercado, atividade do Listing, `last_seen_at` e resultados mais novos.
Resultados obsoletos são descartados, inclusive se outra ingestão corrigiu ou
reagrupou a oferta durante o HTTP. O provider nunca grava em Listing.

## Persistência e operação

`ListingAvailabilityCheck`, no admin de ingestão, guarda **somente o último
resultado por Listing**: status, horário e classe sanitizada da falha, se houver.
É consulta operacional, sem endpoint público, preço, URL, corpo HTTP, endereço,
contato ou cópia de conteúdo da Fonte. Não constitui histórico de preços nem
série de disponibilidade. Registros anteriores são substituídos.

- `available`: detalhe válido confirmou presença, sem atualizar preço,
  `source_inventory_date` ou `last_seen_at`; não é uma nova captura de preços.
- `missing`: ausência individual confirmada; inativa só aquela oferta, atualiza
  a projeção do Property e a retira de busca/detalhe/redirect. Ofertas de outras
  Fontes permanecem publicáveis. `last_seen_at` continua sendo a última captura.
- `failed`: a tentativa não confirmou disponibilidade nem ausência; preserva
  a oferta. A classe da falha aparece no admin e em logs sem payload.

Uma ingestão futura pode reativar o mesmo Listing se ele reaparecer na página,
preservando sua identidade. O resultado individual anterior permanece identificado
pelo horário; não deve ser interpretado como posterior à nova captura.

Essas verificações são independentes de `SyncRun`: não mudam sua completude,
contagens de captura ou último sucesso completo. O relatório de estoque reflete
o estado atual; resultados individuais são consultados em
`/admin/ingestion/listingavailabilitycheck/`. Pausar coleta ou retirar publicação
impede novas verificações. Alterações da Fonte durante HTTP descartam o resultado.

Ao atualizar um stack existente, aplique migrations **antes** de reiniciar Beat
e worker, para que a tabela de resultados exista:

```bash
docker compose -p placecheck-ilb-pilot -f docker-compose.yml -f docker-compose.ilb-pilot.yml exec -T backend python manage.py migrate --noinput
docker compose -p placecheck-ilb-pilot -f docker-compose.yml -f docker-compose.ilb-pilot.yml up -d --build --wait
```

Não é necessário executar task manual nem recriar a Source. O fluxo normal do
Beat selecionará os anúncios elegíveis. `setup_ilb_pilot` continua configurando
o piloto e pode restaurar publicação; não o use para uma simples atualização
durante uma retirada em vigor.

## Verificação

```bash
docker compose -p placecheck-acceptance -f docker-compose.yml -f docker-compose.acceptance.yml exec -T backend pytest -q apps/sources/tests/test_ilb_availability.py
```

Os testes exercitam tasks reais em modo eager com a fronteira HTTP controlada,
API local e PostgreSQL: ausência válida, preservação de outra Fonte, projeção,
falhas/retries, cadência, lote limitado, restrições do piloto, respostas obsoletas,
concorrência na aquisição do lock e reativação. Eager não substitui a evidência
operacional de Beat/Redis/worker, registrada separadamente após o smoke.

Esta entrega fecha a implementação de confirmação individual; não habilita
histórico/retenção de preços, inventário conjunto dos mercados ou segunda Fonte,
e não encerra silenciosamente #7/#8 ou o aceite integrado #14.
