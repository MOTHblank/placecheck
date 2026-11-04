# Estoque, atualização e agrupamento — #13

Segue o [contrato aprovado das métricas](metrics-contract.md). É uma consulta
operacional restrita à equipe com acesso autorizado ao ambiente; não há endpoint
público, dashboard ou série histórica de estoque.

```bash
docker compose exec -T backend python manage.py inventory_report
docker compose exec -T backend python manage.py inventory_report --source 1
docker compose exec -T backend python manage.py inventory_report --city Salvador --state BA --transaction sale --timezone America/Bahia
```

`--source` usa o ID de uma Fonte existente. Um ID desconhecido é erro; selecionar
uma Fonte demo retorna estoque vazio, pois demonstração fica sempre excluída.
Cidade/UF/modalidade devem ser fornecidas juntas. O timezone IANA padrão é
America/Bahia e controla a apresentação dos horários. `--start`/`--end` não são
aceitos: `snapshot_at` identifica o estado atual, não um período retrospectivo.
Para eventos por período, use `journey_report` conforme o [guia de analytics](analytics.md).

## Populações e fórmula

O comando consulta uma única transação PostgreSQL REPEATABLE READ, READ ONLY.
Contagens, associações, permissões e estados de sincronização usam o mesmo snapshot,
sem bloquear Source/Property para escrita. Ao chamar pelo código, execute fora de
outra transação; o comando não altera dados, permissões ou ingestão.

`stock` contém:

- `publishable_sources`: Fontes publicadas não demo, inclusive sem ofertas quando
  não há filtro de mercado. Com mercado, somente as que têm oferta ativa nesse recorte.
- `active_listings` (L): anúncios ativos dessas Fontes, após filtros de Fonte/mercado.
- `represented_properties` (P): Properties distintos representados por esses anúncios.
- `properties_with_multiple_offers`: Properties com pelo menos dois anúncios nessa
  mesma população; duas ofertas fora do recorte não criam um agrupamento dentro dele.
- `retained_price_histories`: registros de preço ainda permitidos das Fontes publicáveis
  e mercado selecionados, incluindo anúncios inativos. Não é a população de estoque ativo.
- `unassigned_active_listings`: anúncios ativos do recorte sem Property; sinalizam
  inconsistência de dados.

**Redução por agrupamento = (L − P) / L × 100**, arredondada a seis casas decimais.
Seis anúncios em quatro Properties resultam em 33,333333%. L=0 produz null com
motivo `empty_stock`. Se houver anúncio sem Property, o indicador também é null,
com motivo `unassigned_listings`; os demais números continuam disponíveis.

Essa redução mede compressão do estoque agrupado, sem avaliar acurácia. Falsos
agrupamentos e duplicidades perdidas exigem revisão de amostra; não há meta
comercial ou inferência automática de qualidade nesse percentual.

Filtros de mercado usam os campos dos Listings, sem depender da projeção do
Property, que pode representar ofertas de modalidades ou Fontes diferentes.
Os totais por Fonte aplicam a mesma população. Properties compartilhados entre
Fontes são contados uma vez no total global: não some os totais individuais de P.

## Publicação e atualização

Pausar coleta (`is_active=False`) preserva estoque publicado. Retirar publicação
(`is_published=False`) exclui anúncios e históricos das contagens deste relatório.
Os históricos podem permanecer fisicamente retidos quando permitidos, sem entrar
no estoque publicável. Negar `can_retain_price_history` exclui esses registros da
contagem, mesmo se houver dados indevidamente retidos fora do pipeline.
`can_retain_analytics` e `ANALYTICS_EXCLUDE_ALL` regulam os eventos da jornada;
não removem o estoque operacional publicável.

`sources` contém linhas operacionais de Fontes não demo, incluindo retiradas, com
seus números publicáveis (zero quando retiradas) e flags de publicação/pausa.
Com mercado, aparecem Fontes que tenham anúncios retidos nesse mercado, inclusive
inativos. Uma Fonte explicitamente selecionada continua observável mesmo sem
anúncios no recorte. Fontes vazias sem evidência daquele mercado não são inferidas
como integrantes dele.

Cada linha mostra `latest_run`, `latest_complete_success` e `latest_failure`, com
estado, completude, horários, contagens e classe da falha. Uma execução parcial ou
falha não substitui o último sucesso completo. Ausência de evidência aparece como
null; não se inventa uma sincronização bem-sucedida. Uma captura completa vazia
pode apresentar zero processados e anúncios inativados.

As contagens de SyncRun são da **Fonte inteira**, explicitadas por
`synchronization_scope=whole_source`; não são distribuídas por mercado. O filtro de
mercado afeta o estoque e a seleção das linhas, não transforma totais operacionais
em contagens daquele mercado. Falhas podem ocorrer depois de atualizar algumas
ofertas: o estoque reflete o estado atual, enquanto o estado da execução registra
essa limitação. Data de processamento também não garante que a Fonte tenha gerado
dados novos; observe os limites/cache do provider.

## Verificação e limites

```bash
docker compose exec -T backend pytest -q apps/analytics/tests/test_inventory.py
```

Fixtures pelo comando real verificam estoque 6/4, múltiplas ofertas, história de
anúncio inativo, demonstração, retirada, pausa, permissão negada, filtros de
Fonte/mercado, estoque zero e anúncio sem Property. Fixtures pelo pipeline existente
verificam captura completa, parcial, falha, completo vazio e reagrupamento após
correção de unidade. Um teste concorrente reconcilia a Fonte durante a leitura e
comprova que estoque e SyncRun permanecem coerentes no snapshot, sem bloquear a ingestão.

O smoke no banco isolado do piloto real retornou uma Fonte, dois anúncios e dois
Properties, zero históricos e execuções parciais; `latest_complete_success=null`
reflete a ausência de inventário completo. Nenhuma nova consulta externa foi feita.
Isso descreve a amostra local, sem comprovar estoque completo/atualizado do parceiro,
cobertura nacional, comparação real entre Fontes ou o aceite integrado #14.

### Revalidação de 04/11/2026

O Compose isolado de aceitação subiu com seis serviços e a suíte completa passou
com 149 testes backend/PostgreSQL, incluindo os 14 casos deste relatório. Django
check/migrations, build no Node 22 e 14 testes Chromium também passaram.

O comando real com `--city Testópolis --state BA --transaction sale` retornou duas
Fontes simuladas, 28 anúncios ativos, 14 imóveis representados e 14 imóveis com
múltiplas ofertas, sem anúncios sem Property. A redução foi 50%; os históricos
retidos foram 112, acumulados pelas execuções das fixtures existentes. Por Fonte,
14 anúncios/14 imóveis e redução de 0%, demonstrando por que não somar Properties
entre Fontes. Coleta pausada e ausência de SyncRun dessas fontes manuais apareceram
explicitamente. `verify_async_ingestion` comprovou separadamente os estados de
captura agendada, repetição, preço e inativação completa no worker real.

O aceite técnico de #13 está concluído. Esses dados são sintéticos e não encerram
autorizações, revisão de associações reais ou aceite integrado #14.
