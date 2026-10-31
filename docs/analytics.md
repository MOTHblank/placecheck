# Jornada e CTR — implementação do #12

Segue o [contrato aprovado no #11](metrics-contract.md). Não implementa o relatório
de estoque/agrupamento do #13 nem declara concluído o aceite real integrado #14.

## Operação

Atualize o stack com `docker compose up -d --build`. As migrations removem
`session_id`, referer e user agent dos redirects; não há cópia desses campos.
Os redirects legados recebem a identidade da Fonte ainda conhecida pelo Anúncio.
O marco da nova instrumentação começa na migration; tráfego anterior não é
comparável e não é oferecido pelo relatório. As antigas sessões Django deixam
de ser usadas pela medição; o acesso ao admin continua com sua autenticação normal.

Desenvolvimento e piloto interno usam `ANALYTICS_EXCLUDE_ALL=1`. O exemplo de `.env`
e o override do piloto indicam essa exclusão. Para medir tráfego elegível num
ambiente apropriado, configure explicitamente `ANALYTICS_EXCLUDE_ALL=0`. O override
de aceitação usa zero somente para simular a medição em seu banco isolado.
Não transforme a autorização de teste interno de uma Fonte em publicação aberta.

Relatório JSON, somente para equipe com acesso autorizado ao ambiente:

```bash
docker compose exec -T backend python manage.py journey_report
docker compose exec -T backend python manage.py journey_report --source 1
docker compose exec -T backend python manage.py journey_report --city Salvador --state BA --transaction sale --timezone America/Bahia
```

`--source` é o ID estável da Fonte, inclusive quando seus eventos permitidos
permanecerem após exclusão do cadastro. Fonte desconhecida falha. Cidade/UF/modalidade
devem ser fornecidas juntas. Sem período, consulta o intervalo disponível até agora.
`--start` e `--end` aceitam ISO com offset ou horário local no `--timezone` IANA
(padrão America/Bahia). Horários locais ambíguos/inexistentes falham; offset explícito
resolve a ambiguidade. O intervalo é [início,fim), e datas anteriores ao marco inicial
ou à janela disponível de 90 dias são rejeitadas. `observed_until` distingue o que
já foi observado caso o fim escolhido esteja no futuro.

`sources` apresenta exposições, exposições com saída, redirects brutos e atribuídos,
e `ctr_percent`; null significa sem dados no denominador. Buscas/visualizações são
globais da jornada; com filtro de Fonte retornam null (não se aplica). Com mercado,
contam somente atribuições conhecidas; `unattributed_searches/views` informa à parte
o subconjunto sem mercado completo, sem distribuí-lo artificialmente. Sem mercado,
esses subconjuntos já estão incluídos nos totais globais, não devem ser somados de
novo. A política atual de exclusão aparece em `current_traffic_exclusion`, sem
pretender reconstruir políticas antigas.

O CTR pertence ao período da exposição, enquanto o bruto pertence ao instante da
saída. `attribution_window_open` sinaliza que períodos recentes podem mudar. Duas
exposições e três cliques em uma delas resultam em 50%, não em 150%. Saídas sem
atribuição válida só aumentam o bruto. Esses números não comprovam contato/venda.

## Interfaces e identidade

GET de busca/detalhe retorna `analytics_receipt` assinado, ou null para tráfego/
ofertas excluídos. Ler a API não cria evento. A UI envia POST JSON para
`/api/analytics/events/` depois de uma execução explícita bem-sucedida ou abertura
carregada. O endpoint valida UUID, comprovante e elegibilidade. Respostas: 201 novo,
200 retransmissão idempotente, 202 excluído, 400 inválido e 409 identidade usada com
conteúdo diferente. O OpenAPI documenta esse contrato.
Uma segunda identidade para a mesma oferta/abertura também recebe 409; reutilize
a identidade original para retransmitir. Bloqueio da Fonte e constraint no banco
impedem inflação por submissões simultâneas.

Uma abertura aceita recebe `context_token`. Somente ofertas retornadas nesse detalhe
podem ser registradas como exposição, e precisam continuar ativas/publicadas e com
retenção permitida. Cada artigo não demo é observado por IntersectionObserver:
interseção positiva com a área visível, modal aberto e documento visível. A primeira
interseção conta; voltar ao artigo na mesma abertura não conta de novo. Ofertas
fora da área visível, filtradas ou meramente retornadas pela API não contam.

Exposição aceita recebe `redirect_token`; a UI o usa em `/out/{id}/?exposure=...`.
Ele vincula Fonte, Anúncio, exposição e contexto de abertura, sem cookie de visitante,
IP ou associação pela última aba. É uma capacidade opaca por abertura, não identidade
de pessoa. A janela é [exposição, exposição+30 minutos); o limite exato fica fora.
Repetir cliques não altera o numerador. Link sem token, adulterado, vencido ou
incompatível mantém a saída válida, mas não recebe atribuição.

Uma nova submissão dos mesmos filtros conta nova Busca. Paginação, ordenação e
Voltar/Avançar não contam. URL inicial com filtros conta uma vez; home sem filtros
não conta. Rerender/StrictMode/retry reutilizam a identidade da execução. Nova
abertura, recarga ou mudança do contexto de filtros do detalhe recebe nova identidade.
Uma visualização usa cidade/UF do Imóvel e modalidade explícita; sem modalidade
única, não tem mercado completo. A busca livre/localização textual da UI não é
interpretada como cidade+UF; buscas amplas ficam sem mercado completo. Chamadas
com cidade/UF/modalidade explícitas só atribuem a cidade canônica conhecida.

Os tokens têm finalidades separadas e assinatura do servidor. Comprovantes de
resposta têm validade de 30 minutos; contextos permanecem verificáveis dentro da
retenção, mas exigem a abertura ainda retida. Tokens de saída nunca estendem a janela
de 30 minutos da exposição original. Não há tabela/cache paralelo de tokens.
Conteúdo é comparado por HMAC, incluindo a identidade opaca do evento; não se guarda
texto livre nem um hash estável da consulta que permita agrupar visitantes.

Falhas de entrega recebem até duas retransmissões em memória com a mesma identidade;
não há fila persistente/offline. A UI continua utilizável e o link original não
aguarda medição. Isso pode subcontar exposições/atribuições após falhas ou mudanças
de disponibilidade. A visibilidade é declarada pelo cliente, sem prova de atenção
ou mecanismo antifraude. Detecção de automação usa somente padrões conhecidos no
User-Agent em memória; não se procura identificar pessoas ou criar fingerprint.

## Permissões, minimização e limpeza

Equipe autenticada, ambiente interno identificado, demonstração e automação conhecida
ficam excluídos, inclusive de saídas brutas. Origem HTTP incompatível não cria evento.
O proxy local preserva Host; proxies futuros precisam preservar a origem correta.
O cliente não pode declarar a si mesmo como tráfego real para vencer uma exclusão
configurada no servidor.

`Source.can_retain_analytics=False`, aplicado por `Source.save()`/admin, interrompe
eventos daquela Fonte e remove exposições/redirects já armazenados sob seu ID.
Usa o bloqueio da Fonte para serializar revogação com escrita. Retirada de publicação
impede novas exposições/saídas, mas preserva eventos históricos quando sua retenção
continua permitida. Deletar Listing ou Source não apaga silenciosamente seus snapshots
de Fonte/mercado. Buscas e visualizações são eventos gerais da jornada, sem Fonte
única; não contêm nomes ou conteúdo de ofertas. Não use QuerySet.update para revogar
essas permissões.

Não se gravam IP, referer, user agent, texto de busca, descrição, contato ou URL de
destino nos novos eventos. Logs Django e erros do proxy Vite omitem queries de busca/detalhe e tokens de
saída; não faça cópias desses dados em proxies/logs externos. API e redirects usam
no-store; saídas também usam no-referrer. O admin de redirects é de consulta.

```bash
docker compose exec -T backend python manage.py purge_analytics
```

O comando elimina eventos e redirects com idade >=90 dias, rompe atribuições
expiradas e avança o marco disponível, mesmo num período sem eventos. Uma saída mais
recente conserva apenas sua classificação booleana de atribuição, sem manter ID ou
cópia da exposição já expirada. Beat agenda
`apps.analytics.tasks.purge_expired_analytics` a cada hora; mantenha Beat e worker
ativos. A execução física depende desse agendamento: monitore falhas e execute o
comando manual se necessário. O relatório aplica a janela mesmo antes da limpeza,
sem apresentar períodos expirados como zero. Não se guardam agregados de negócio
persistentes ou arquivos de eventos fora dessa política. Resultados de limpeza só
contêm contagens e cutoff; backups seguem a mesma política e não devem ser usados
como um arquivo alternativo de eventos individuais.

## Validação reproduzível

Backend: `docker compose exec -T backend pytest -q`.
Frontend: `docker compose exec -T frontend npm run build`.
No stack isolado de aceitação, execute os dois comandos:

```bash
docker compose -p placecheck-acceptance -f docker-compose.yml -f docker-compose.acceptance.yml exec -T backend python manage.py prepare_browser_fixtures
docker compose -p placecheck-acceptance -f docker-compose.yml -f docker-compose.acceptance.yml exec -T backend python manage.py prepare_analytics_fixtures
```

Depois, em `frontend/`, execute `npm run test:e2e`. As fixtures de analytics marcam
explicitamente publicação simulada: não são Fontes reais nem evidência de associação
correta. Se usar outro projeto/portas, defina `PLAYWRIGHT_BASE_URL`,
`ANALYTICS_COMPOSE_PROJECT` e, se necessário, `ANALYTICS_COMPOSE_OVERRIDE` (caminho
do override relativo à pasta frontend) para o teste consultar o comando nesse stack.
O dataset real do piloto não é usado nesse aceite determinístico.

Validação em 31/10/2026: 135 testes backend (dois avisos de depreciação Django),
Django check e migrations sem divergências, build TypeScript/Vite e 12 testes
Playwright desktop/mobile aprovados. O Compose de aceitação foi construído e
iniciado com volumes próprios nas portas 38000/35173, preservando o stack que já
ocupava as portas padrão. O teste de CTR consulta o comando real de relatório.
A limpeza também foi enfileirada no Redis e executada pelo worker real; retornou
somente contagens/cutoff. Desenvolvimento carregou a exclusão interna explicitamente.
Revisão e correções estão em [analytics-review.md](analytics-review.md).

Os testes verificam aritmética de 50%, oferta retornada mas não visível, retransmissão,
submissão repetida, navegação, falha de instrumentação, janelas temporais/meia-noite,
zero denominador, exclusões, perda de Listing/Source, revogação e limpeza. A saída
real do endpoint é exercitada, interceptando somente a fronteira externa do 302.
