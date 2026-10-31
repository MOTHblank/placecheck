# Auditoria do caminho até o MVP

Verificação local em 2026-10-31. Este documento registra evidências e decisões da entrevista; não substitui specs e tickets no GitHub Issues.

Especificação de conclusão publicada: [GitHub Issue #1](https://github.com/MOTHblank/placecheck/issues/1), com label `ready-for-agent`. O issue distingue decisões confirmadas de propostas ainda não respondidas e mantém a autorização da primeira fonte como dependência externa do aceite real.

## Evidências

Árvore de trabalho inicialmente limpa. Plano e prompt local lidos integralmente.
Backend: `docker compose exec -T backend pytest -q`, 43 testes passaram.
Frontend: `docker compose exec -T frontend npm run build`, TypeScript e Vite passaram.
Seis serviços Compose em execução; PostgreSQL e Redis saudáveis. Health check, frontend e proxy da API responderam HTTP 200.
Não foi executado um bootstrap limpo com `docker compose up --build` nesta auditoria.
Smoke de navegador: resultados de venda e modal de comparação com três ofertas fictícias; saída real não exercitada.

| Sprint | Verificação do aceite | Lacunas |
| --- | --- | --- |
| 0 | Stack local em execução | Bootstrap do zero não repetido; não comprova prontidão para produção. |
| 1 | Modelos, migrations, admin, factories, constraints e testes presentes; cadastro manual disponível | Edições diretas no admin não percorrem histórico/deduplicação da ingestão. |
| 2 | Provider manual percorre normalização e persistência | `R$ 650.000` vira `650.00`; deveria virar `650000.00` (§9). API/XML/crawler são bases abstratas; nenhuma fonte real autorizada demonstrada. |
| 3 | Beat a cada 15 minutos, tasks, retries, logs e limites de fetch presentes | Testes usam execução eager/mocks; sincronização real Beat → broker → worker não comprovada. Discovery sem timeout/limite por fonte. |
| 4 | Testes de idempotência, mudança de preço, last-seen, inativação e reativação passam | Configuração manual ausente equivale a snapshot vazio. Reconciliação não identifica execuções nem protege contra snapshots incompletos/sobrepostos. |
| 5 | Teste associa ofertas equivalentes de fontes diferentes; regras conservadoras e auditoria presentes | Cobertura prática depende de coordenadas, unidade explícita e títulos semelhantes. Pesos fixos; filtro de candidatos amplo. Taxa de agrupamento não comprova acurácia. |
| 6 | Busca, detalhes, filtros, paginação, ordenação e redirect cobertos por testes | Desativar Source não retira Listings ativos da busca/redirect. Verificar documentação dos parâmetros customizados no OpenAPI. |
| 7 | Busca/comparação implementadas; build e smoke parcial passam | Fluxo até anúncio real pendente. Ordenação some no mobile; rótulos de demonstração incondicionais. Sem teste automatizado do fluxo no navegador. |

Evidências principais: `backend/apps/sources/normalizers/listing.py`, `backend/apps/sources/providers/registry.py`, `backend/apps/ingestion/tasks.py`, `backend/apps/ingestion/services.py`, `backend/apps/deduplication/services.py`, `backend/apps/properties/views.py` e respectivas suítes de testes; `frontend/src/OfferDialog.tsx`, `PropertyCard.tsx` e `styles.css`.

## Bloqueios para inventário real

- Aplicar permissões de armazenamento: `Source.can_store_description` existe, mas a persistência grava a descrição independentemente da flag.
- Distinguir interrupção de coleta de retirada de publicação; definir e testar remoção/revogação.
- Corrigir normalização monetária e distinguir falha/configuração ausente de inventário completo vazio.
- Proteger reconciliação de execuções sobrepostas e exigir confirmação de completude do inventário.
- Escolher uma fonte concreta, registrar permissão e validar seu contrato de dados antes de coletar.
- Demonstrar ingestão assíncrona real, atualização de preço, remoção e busca → comparação → destino original.

## Decisões da entrevista

- O piloto atenderá vários mercados; extensão exata e critério de cobertura ainda abertos.
- Métricas devem avaliar descoberta de imóveis e saída para ofertas relevantes, além de atualização e qualidade dos agrupamentos. Contato e transação continuam na fonte.
- Priorizar parceria direta com imobiliária que forneça inventário autorizado por arquivo/feed/API. Nomes citados no README continuam candidatos, sem permissão comprovada.

## Sprint 8: estado e perguntas abertas

Existe `RedirectEvent` e registro no endpoint de saída. Não existem eventos de busca, visualização ou exposição de ofertas, nem agregação de CTR e resumo operacional.
Faltam fechar denominadores, unidade de contagem, atribuição, janela temporal, exclusão de demonstração/tráfego interno, retenção e superfície de consulta.
Proposta ainda não aprovada: separar estoque atual de eventos por período; medir CTR sobre exposições das ofertas da fonte e distinguir compressão do inventário de acurácia da deduplicação.

## Primeira fonte

Nenhuma fonte real está autorizada por evidência presente no repositório. “Ideal Imóveis” não identifica domínio único; “Quarto Andar” não deve ser convertido implicitamente para outro nome.
Uma parceria precisa identificar o titular e domínio, meio autorizado de entrega, campos permitidos, exibição/comparação, retenção do histórico, atualização, remoção e revogação.
Existência de documentação de integração de um CRM não concede acesso ou autorização ao Placecheck.
