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

### Inventário conjunto de dois mercados

O override `docker-compose.ilb-joint.yml` reúne os recortes de venda
Salvador/BA e Campinas/SP no mesmo banco e na mesma Source ILB. O responsável
confirmou esse piloto interno em 05/11/2026. Isso não cria uma segunda Fonte
nem comprova comparação entre Fontes.

```bash
docker compose -p placecheck-ilb-joint -f docker-compose.yml -f docker-compose.ilb-pilot.yml -f docker-compose.ilb-joint.yml up -d --build --wait
docker compose -p placecheck-ilb-joint -f docker-compose.yml -f docker-compose.ilb-pilot.yml -f docker-compose.ilb-joint.yml exec -T backend python manage.py setup_ilb_pilot
```

Frontend: http://127.0.0.1:25175; backend: http://127.0.0.1:28002.
O Beat usa o intervalo padrão de 15 minutos. Não carregue fixtures de aceitação
nesse banco. Os volumes desse projeto ficam separados dos outros pilotos.

`ILB_PILOT_MARKETS=BA:salvador,SP:campinas` aceita um ou dois recortes
explícitos, com até dois anúncios por mercado nesse override. Quando vazio,
preserva a configuração anterior por `ILB_PILOT_UF`/`ILB_PILOT_CITY`.
Recortes repetidos, inválidos ou mais de dois falham antes da criação da Fonte.
A ordem é canônica: `BA:salvador|SP:campinas`. Uma Fonte existente não pode
trocar seu escopo; use o novo projeto isolado para preservar inventários antigos.

Cada mercado mantém sua captura imutável e seu cache diário. Discovery precisa
validar ambos antes de enfileirar ofertas; falha de um mercado não publica meia
descoberta e não inativa anúncios existentes. A segunda descoberta consome a
mesma cota por Fonte; limite abaixo de dois é configuração inválida. Cada
execução continua parcial, mesmo com as duas páginas vazias. Ausências são
tratadas pela verificação individual já implementada, aceitando somente os
mercados configurados. Retirada pública da Fonte afeta ambos os recortes.

Imagens e descrições continuam desabilitadas. O responsável confirmou nesta
sessão o piloto conjunto e o uso interno do histórico, após ser perguntado
explicitamente sobre a interpretação de uso de preços individuais. A base é a
permissão geral de dados com atribuição nos termos §6 e os exemplos de monitoramento
da API; é uma decisão do responsável para o piloto, não uma nova declaração
específica do operador. Não há autorização de publicação aberta nem segunda Fonte.

O override conjunto define `ILB_PILOT_PRICE_HISTORY=1`; o padrão global permanece
`0`. `setup_ilb_pilot` aplica essa opção a `can_retain_price_history`, reutilizando
a persistência atômica existente: primeira captura e mudanças de valor geram
registros; repetição não duplica. Não há reconstrução retroativa de preços.
O histórico é retido somente enquanto permitido no piloto; não foi acordado
prazo numérico. Desabilitar a opção e repetir o comando remove os registros e
impede novas gravações. Retirar a publicação não apaga histórico permitido;
para revogar a retenção, desligue também essa permissão. O smoke real desse
override exige `ILB_PILOT_BROWSER=1 ILB_PILOT_PRICE_HISTORY=1`.

As evidências anteriores em bancos separados, abaixo, continuam sendo registros
históricos; não são prova de execução deste override.

Validação em 05/11/2026: **202 testes backend passaram** em PostgreSQL 18 local
temporário, Python 3.13, cache/broker/resultados em memória. Incluem os dois
mercados no mesmo inventário, repetição, falha parcial, cota compartilhada,
retirada, histórico opt-in, mudança de preço e revogação. Isso valida as regras,
não comprova execução assíncrona real. Build TypeScript/Vite, `Django check`,
compilação Python, descoberta dos 16 cenários Playwright e `compose config --quiet`
passaram. Nenhuma migration nova foi detectada; a conferência de histórico de
migrations do banco padrão não foi concluída (banco padrão indisponível).

`docker compose up --build --wait` não concluiu: o Docker Desktop encerrou antes
de criar o daemon, com erro no socket temporário `dockerInference`. Reiniciar e
tentar renomear/remover somente esse socket não resolveu; não houve reset nem
remoção de volumes. Ficam pendentes o Compose Python 3.12/PostgreSQL 16, a captura
real conjunta por Beat/Redis/worker, mudança real de preço permitida e smoke de
navegador desktop/celular desse inventário. Nenhum preço real foi modificado para
simular aceite. Os dois testes de resposta >1 MiB receberam IDs curtos para
evitar erros de preparação no Windows, preservando seus payloads e asserções.

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
Suíte completa: 101 testes backend aprovados (dois avisos de depreciação Django),
Django check sem problemas, migrations sem divergências e build TypeScript/Vite
aprovado. A mudança adiciona quatro migrations pequenas e não exige dependências.
As seis regressões Playwright existentes também passaram em desktop e celular, num
Compose separado nas portas 38000/35173 (as portas padrão de aceitação estavam
ocupadas por outro stack, preservado). O smoke CLI do piloto real é evidência
adicional; as fixtures desses seis testes continuam fictícias.

## Revisão da implementação

Base: `77ebb557c7f3e4209f654d68d73aa764f92a6137`; implementação inicial: `ef12090`.
Revisão independente segundo `mattpocock-skills:code-review`:

- **Standards:** um achado P2, releitura ausente do cache depois de adquirir o
  bloqueio. Dois workers poderiam baixar a mesma página se outro concluísse entre
  a leitura inicial e a aquisição. Corrigido com releitura sob o bloqueio e teste
  determinístico dessa intercalação, que falhou antes e passou após a correção.
  O bloqueio dura 60 s, além do limite hard de 45 s da task.
- **Spec:** nenhum achado dentro do escopo experimental limitado, sem declarar
  atendidos os critérios externos ainda pendentes de #7/#8.

Permanecem pendentes: escopo de publicação aberta, retenção/histórico autorizados,
contrato de remoção e snapshot completo, cobertura de vários mercados aprovada e
demonstrada, segunda Fonte sobreposta e aceite integral. #7/#8 permanecem abertos.

## Revalidação e aceite por critério — 04/11/2026

A [revisão das fontes primárias](ilb-contract-review.md) confirma a permissão
publicada para uso de dados com atribuição e os exemplos de monitoramento/cache.
Não há exigência publicada de parceria privada para o piloto. Isso corrige a
interpretação de que faltaria identificar ou obter qualquer fonte antes de avançar:
**a ILB já é uma Fonte real implementada e utilizável no escopo interno existente**.
Histórico individual/prazo de retenção e publicação aberta continuam sem escopo
específico aprovado no projeto; sua ausência não é prova de proibição pelo operador.

O `robots.txt` atual respondeu 200 no container, com User-Agent Placecheck;
mantém a restrição genérica a `/api/` e exceções nominais. Não usamos outro agente
para obtê-las. O piloto continua cliente da interface JSON expressamente oferecida,
sem rastreamento HTML, buscas ou contorno de bloqueios.

### Evidência operacional atual

- Ambos os stacks subiram com seis serviços. Beat configurado em 15 s para o aceite;
  o cache da consulta permanece diário, sem repetir HTTP a cada ciclo.
- Salvador/BA: novas execuções parciais processaram dois anúncios da lista de 03/11.
  Um ID novo entrou, um anterior foi atualizado e um terceiro, visto em 31/10,
  permaneceu ativo por não estar na página parcial. Duas capturas consecutivas
  não duplicaram o estoque. **Três anúncios retidos não significam três confirmados
  na última captura**, nem que o mais antigo foi vendido.
- Campinas/SP: banco novo com dois anúncios, mesma data de origem e repetição
  agendada sem duplicação. É a mesma Fonte em outro recorte isolado, não segunda
  Fonte, inventário completo, cobertura nacional ou busca conjunta entre cidades.
- O smoke Chromium passou em desktop/celular para os dois recortes: busca/detalhe,
  tipos de valor, atribuição, data de origem, ausência de descrição/histórico e
  tráfego interno excluído. O endpoint real retornou 302 para a ficha CAIXA;
  o navegador interceptou a fronteira externa, sem contato/transação.
- Uma ficha oficial correspondente a Salvador foi aberta separadamente e respondeu
  com o mesmo número CAIXA, confirmando o destino público: [ficha oficial](https://venda-imoveis.caixa.gov.br/sistema/detalhe-imovel.asp?hdnimovel=8444400798566).
  Essa checagem não garante disponibilidade futura; conteúdo pessoal, endereço,
  descrição e imagens não foram adicionados ao dataset.
- Retirada pública temporária na Source real de Salvador: busca vazia, detalhe
  e saída 404. O `finally` restaurou o estado anterior. A primeira tentativa do
  cliente interno usou Host `testserver` e foi recusada; o aceite foi repetido com
  `localhost`, sem alterar ALLOWED_HOSTS.
- Passaram os **33 testes** de `test_ilb_provider.py` e `test_ilb_pipeline.py`.
  Screenshots dos quatro cenários foram inspecionadas; os testes não inventam IDs,
  preços nem quantidades fixas. A suíte geral de 149 testes é a baseline anterior
  do mesmo código de aplicação, não uma nova execução desta revalidação.
- A inspeção descobriu uma falha de apresentação: `source_inventory_date`, uma
  data sem horário, aparecia um dia antes na tabela em America/Bahia, enquanto
  o cartão conservava o dia correto. A regressão com `2026-11-03` falhou mostrando
  `02/11/2026`; a tabela passou a preservar `03/11/2026`. Timestamps de captura
  continuam sendo convertidos para o horário local. O smoke real compara a data
  da tabela com a data do inventário retornada pela API local.
  Após a correção passaram o build no Node 22, 14 testes gerais de navegador
  (os dois smokes reais ficaram ignorados por padrão) e quatro smokes opt-in,
  desktop/celular em Salvador e Campinas, todos em America/Bahia.

### #7 — Insumos e escopo da primeira Fonte

| Critério original | Estado e evidência |
| --- | --- |
| Identidade do titular/domínio | Atendido para a fonte pública escolhida: ILB/Spartan TI, origem CAIXA, domínio e termos identificados. Não é parceria com imobiliária nem com a CAIXA. |
| Permissão abrangendo os tratamentos | Parcial: uso dos dados com atribuição é permitido. Falta decisão registrada sobre histórico/retenção e publicação aberta; não transformar silêncio em proibição ou autorização específica. |
| Amostra/IDs/entrega/completude/exclusão | Parcial: API real, amostras em dois recortes e IDs estáveis confirmados. Captura é parcial; não há contrato de snapshot atômico. Detalhe 404 é uma base técnica para futura verificação individual, ainda não implementada. |
| Cobertura acordada | Dois mercados de venda exercitados em bancos separados. Falta confirmar o escopo final; não alegar inventário conjunto ou aluguel. |
| Segredos e dados restritos | Atendido no piloto: sem credenciais, contatos, endereços, descrição ou imagens armazenados. |
| Conclusão humana | Mantida: os itens anteriores não autorizam mudar silenciosamente os critérios do ticket ou declarar aceite integral. |

### #8 — Integração da primeira Fonte

| Critério original | Estado e evidência |
| --- | --- |
| Provider específico/IDs/URLs/pipeline | Atendido. O provider existente usa RawListing/Normalizer/persistência, sem escrever em Listing. |
| Captura/idempotência/histórico/inativação | Parcial. Agendamento real e repetição passaram; atualiza preço sem histórico. Ausência de página parcial não inativa. |
| Busca/detalhes/saída/permissões/retirada | Atendido no escopo interno: dois recortes reais, 302 oficial, retirada verificada e restauração. Sem comparação entre Fontes. |
| Cobertura conforme acordo | Parcial: dois recortes comprovados, escopo final de #7 ainda pendente. |
| Fixtures/regressões | Atendido: 33 casos cobrem formato, cache, validação, erros, repetição, atualização sem histórico, captura parcial e retirada. |
| Operação/evidências/limites | Atendido para o piloto interno, com comandos reproduzíveis abaixo e sem segredos. |

Não se encerram #7/#8 com esses aceites parciais. Próximo trabalho concreto:
definir a retenção de preços no escopo interno e implementar/testar remoção
individual por resposta de detalhe validada, ou obter um snapshot completo confiável.
Um 404 deve significar apenas saída da lista da Fonte, sem inferir venda; timeout,
403, bloqueio, HTML inesperado e ausência na página jamais podem virar exclusão.
Também falta decidir como reunir os mercados no piloto final, preservando uma
única identidade da Fonte e sem enfraquecer a deduplicação.

### Repetir o smoke sem coletar mais anúncios pelo teste

Após a sincronização agendada do stack padrão, em `frontend/`:

```powershell
$env:ILB_PILOT_BROWSER = '1'
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:25173'
node node_modules/@playwright/test/cli.js test tests/ilb-pilot.spec.ts --workers=1
```

O arquivo é opt-in: fica ignorado por execução quando `ILB_PILOT_BROWSER` não é `1`.
O teste só lê a API local e intercepta o destino do redirect. Não executa ingestão,
não altera permissões e não navega automaticamente no site oficial.

Para reproduzir Campinas em projeto separado, na raiz:

```powershell
docker compose -p placecheck-ilb-campinas -f docker-compose.yml -f docker-compose.ilb-pilot.yml -f docker-compose.ilb-campinas.yml up -d --build --wait
docker compose -p placecheck-ilb-campinas -f docker-compose.yml -f docker-compose.ilb-pilot.yml -f docker-compose.ilb-campinas.yml exec -T backend python manage.py setup_ilb_pilot
```

Depois da captura, use `PLAYWRIGHT_BASE_URL=http://127.0.0.1:25174` no mesmo teste.
O override fixa SP/campinas/2, portas loopback 28001/25174 e banco/cache separados.
O padrão de Beat permanece 900 s; `ILB_PILOT_SYNC_SECONDS=15` foi usado somente para
observar o aceite. Pare esse stack com `down` e os mesmos argumentos, sem `-v`.

### Atualização posterior: ausência individual confirmada

A [verificação individual de disponibilidade](ilb-availability.md) foi implementada
e comprovada pelo Beat/Redis/worker real. O anúncio antigo descrito acima, preservado
pela captura parcial, recebeu depois um 404 JSON válido do endpoint de detalhe e
foi inativado. As duas ofertas atuais permaneceram publicáveis; a busca retornou
duas, e detalhe/redirect da oferta retirada deram 404. Isso não prova que o imóvel
foi vendido, somente que saiu da lista da ILB.

O status de captura continua parcial e `SyncRun` não recebe um sucesso completo
inventado. O último resultado individual fica separado no admin. A pendência de
remoção tem agora implementação e evidência real; a parte de histórico do segundo
critério de #8 continua pendente, assim como retenção e escopo final dos mercados
em #7. Não se altera o aceite original nem se declara encerramento integral.
