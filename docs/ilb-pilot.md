# Primeira Fonte experimental: Imóveis Leilão Brasil

Implementação interna em 31/10/2026, a partir da solução registrada pelo responsável
em [#7](https://github.com/MOTHblank/placecheck/issues/7#issuecomment-6539495357).
Este piloto exercita o início de #8; não conclui as autorizações de #7 ou o aceite
real completo de #8/#14. Não é parceria com a CAIXA ou com o operador da API.

## Base de uso e recorte

O operador é Spartan TI (Spartan Tecnologia e Soluções Inteligentes Ltda). A
[documentação da API](https://www.imoveisleilaobrasil.com.br/api) e os
[termos, seção 6](https://www.imoveisleilaobrasil.com.br/termos) permitem usar os
dados de imóveis com citação da origem. Essa é a base publicada usada para o teste
interno limitado; não se presume licença para conteúdo editorial, ranking, imagens,
dados pessoais ou todos os tratamentos comerciais futuros. Os termos consultados
informam atualização em 23/10/2026. Não foram contatadas empresas.

`robots.txt` foi consultado em 31/10/2026: contém `Disallow: /api/` para o agente
genérico e permissões específicas para alguns agentes. Isso restringe rastreamento;
a implementação usa exclusivamente a interface JSON que a documentação oferece
expressamente a clientes de API. Não rastreia HTML/busca, não simula outro agente
e não contorna bloqueios. Identifica-se como
`Placecheck/0.1 (+https://github.com/MOTHblank/placecheck)`.

A API declara 30 requisições/minuto/IP sem chave, recomenda filtros e cache e não
oferece SLA. O provider faz **uma consulta filtrada de uma página**, com até 20 itens
(padrão do Compose: dois), por UF/cidade configuradas. Mantém o resultado por 24 h
no Redis compartilhado; reiniciar/perder esse cache permite nova consulta.
Discovery e fetch continuam submetidos ao limite por Source; falhas transitórias
usam os retries das tasks existentes. Não há paginação nacional ou coleta de
contatos, endereços, descrições, imagens, avaliação ou ranking.

O campo `collection_scope` vincula a Source ao recorte UF/cidade. Alterar esse
recorte em uma Fonte já configurada falha; use outro projeto Compose isolado para
outro recorte. Aumentar/reduzir o limite não remove itens já observados. O catálogo
de origem é nacional, mas o piloto demonstra somente o recorte efetivamente testado.

## Contrato e limites

Referência: [OpenAPI publicado](https://www.imoveisleilaobrasil.com.br/api/openapi.json).
O retorno real foi validado, não apenas o exemplo da documentação.

| Entrada | Mapeamento |
| --- | --- |
| `id` | ID CAIXA estável, 5–20 dígitos; identidade `(Source, external_id)`. |
| `linkOficial` | HTTPS, host e caminho exatos da ficha CAIXA, `hdnimovel` correspondente ao ID; não usar a URL do intermediário como destino original. |
| `tipoSlug` | Tabela explícita para os tipos atuais; rural/outros → `other`. Enum desconhecido falha. |
| `preco` | Decimal em reais, preservando centavos; ausência fica nula, nunca zero inventado. |
| `modalidade` / `modalidadeSlug` | Preservadas em `sale_method`, com validação de consistência quando ambas presentes. Algumas respostas não trazem o slug; o texto conhecido pode identificá-lo. |
| Leilão SFI / Licitação Aberta | `transaction_type=sale`, `price_kind=minimum`; a UI identifica valor/lance mínimo. |
| Venda Direta Online | `sale`, `asking`; não inferir que outras modalidades tenham preço final. |
| Venda Online | `sale`, `reference`; natureza do valor deve ser confirmada no edital, sem tratá-lo automaticamente como preço final. |
| `areaPrivativa` / `areaTerreno` | Área privativa para edificações; área de terreno somente para terreno. Não substituir área privativa ausente por total genérica. |
| `quartos`, `vagas` | Contagens opcionais, inteiros não negativos; vagas ausentes continuam nulas. Banheiros, suítes e coordenadas não são inventados. |
| `cidade`, `uf`, `bairro` | Cidade/UF devem corresponder ao recorte; bairro opcional. |
| `listaGeradaEm` | `source_inventory_date`, mostrada no detalhe. `last_seen_at` é observação pelo pipeline e pode vir do cache; não é data de atualização na CAIXA. |

O provider valida todos os itens antes de publicar a captura no cache. O snapshot
contém somente os campos necessários e dura 25 h, permitindo concluir tarefas
disparadas perto do vencimento do cache diário. Referências incluem uma identidade
de snapshot; providers reconstruídos por outros workers leem a mesma versão, sem
consultar de novo o anúncio corrente. Expiração, erro, duplicação de IDs ou perda de
cache falham explicitamente. O transporte não segue redirects, usa TLS, timeout
de 8 s e limite de resposta de 1 MiB. Dados/configuração inválidos não viram vazio.

**Toda captura é parcial**, mesmo se o total informado couber na página. A data da
lista não prova snapshot completo imutável de toda a origem. Assim, desaparecimento
da página, página vazia ou erro nunca inativam anúncios antigos. `SyncRun` termina
como `partial`, com contagens, e não como sucesso completo. Disponibilidade real
precisa ser confirmada na Fonte; não há SLA de remoção automática neste piloto.

Descrição, imagens e histórico ficam desabilitados na Source. Atualizar o preço
muda o valor atual, sem gravar ListingPriceHistory. Cache, broker e backend de
resultados são intermediários de processamento; não constituem um arquivo histórico.
O Celery omite o conteúdo de retornos nos logs de ingestão. Não habilite retenção
de histórico sem registrar seu escopo permitido.

Sem endereço/unidade/coordenadas, não há evidência suficiente para agrupamento
automático. Os dois anúncios reais testados ficaram separados. Isso não demonstra
comparação entre Fontes, aluguel, precisão da deduplicação ou negociação comum de
imobiliárias. A regra conservadora existente foi preservada.

## Operação local

Requer `.env` do projeto e Docker Compose 2.24.4+ (`!override`). O override cria
volumes próprios e expõe backend/frontend somente em `127.0.0.1`:

```bash
docker compose -p placecheck-ilb-pilot -f docker-compose.yml -f docker-compose.ilb-pilot.yml up -d --build --wait
docker compose -p placecheck-ilb-pilot -f docker-compose.yml -f docker-compose.ilb-pilot.yml exec -T backend python manage.py setup_ilb_pilot
```

O comando cria/atualiza a Source e suas permissões; não faz HTTP. Beat enfileira a
captura no próximo intervalo (padrão 900 s). Para um aceite supervisionado rápido,
defina `ILB_PILOT_SYNC_SECONDS=15` antes do `up`; o cache diário continua valendo.
`ILB_PILOT_UF`, `ILB_PILOT_CITY` (slug) e `ILB_PILOT_LIMIT` permitem escolher o
recorte antes de criar a Source. Padrão: BA/salvador/2, escolhido apenas para o smoke,
sem prioridade regional para a seleção nacional de Fontes.

- Interface: http://127.0.0.1:25173
- API: http://127.0.0.1:28000/api/properties/
- Health: http://127.0.0.1:28000/health/
- Admin de execuções: `/admin/ingestion/syncrun/` (exige conta local autorizada).

Para observar sem enfileirar manualmente:

```bash
docker compose -p placecheck-ilb-pilot -f docker-compose.yml -f docker-compose.ilb-pilot.yml logs --tail 50 celery
```

Para retirar, no admin da Source desligue **publicação e coleta** e salve:
`is_published=False`, `is_active=False`. Pausa só da coleta mantém os dados visíveis.
Desligar apenas a flag de configuração também não equivale a retirada pública.
`setup_ilb_pilot` habilita novamente a Source e restaura as permissões restritas;
não o execute durante uma retirada que precisa permanecer em vigor.

Para parar o ambiente, preserve os volumes:

```bash
docker compose -p placecheck-ilb-pilot -f docker-compose.yml -f docker-compose.ilb-pilot.yml down
```

Não reutilize banco/volumes deste piloto numa publicação aberta. A flag
`ILB_PILOT_ENABLED` é desligada por padrão e o provider também exige `DEBUG=True`;
isso protege a ativação da coleta, enquanto o isolamento da interface depende das
portas loopback deste override. O restante do MVP e suas Fontes demo não são
ativados nesse banco.

## Evidência e trabalho restante

Em 31/10/2026, o stack novo subiu com seis serviços; Beat → Redis → worker importou
dois registros reais de Salvador/BA, lista de origem 29/10/2026, e repetiu a captura
com os mesmos IDs sem duplicar o estoque. SyncRuns parciais registraram dois
processados e zero inativados. Valores observados: licitação aberta e venda online.
Navegador desktop e 390×844 confirmou rótulos, atribuição, data e ausência de
histórico. O endpoint real respondeu 302 para a ficha CAIXA; não foi seguida a
navegação externa nem houve contato/transação.

Fixtures de contrato são sintéticas, no formato observado, sem endereço/descrição
retidos. Cobrem erros de transporte, validação, cache, modalidades, idempotência,
atualização sem histórico, vazio parcial e retirada. Screenshots locais estão em
`output/playwright/ilb-pilot-desktop.png` e `ilb-pilot-mobile.png`, ignorados pelo Git.
Suíte completa: 100 testes backend aprovados (dois avisos de depreciação Django),
Django check sem problemas, migrations sem divergências e build TypeScript/Vite
aprovado. A mudança adiciona quatro migrations pequenas e não exige dependências.

Permanecem pendentes: escopo de publicação aberta, retenção/histórico autorizados,
contrato de remoção e snapshot completo, cobertura de vários mercados aprovada e
demonstrada, segunda Fonte sobreposta e aceite integral. #7/#8 permanecem abertos.
