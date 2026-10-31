# Revisão do #12 — jornada e CTR

Base: `60510a996cecc3898be8222836ea4f1a8a55ae12`. Implementação inicial: `3cdd2ef`.
Duas revisões independentes seguiram `mattpocock-skills:code-review`, confrontando
o diff com as regras do projeto e o contrato aprovado de métricas.

## Standards

- **P2 — Fonte excluída com relatório vazio.** Resolver metadados somente na
  população filtrada terminava tentando buscar uma Source já excluída. A consulta
  agora usa snapshots ainda retidos fora do filtro para identificar a Fonte, sem
  buscar dados expirados. Regressão cobre período vazio e outro mercado, com
  contagens zero e CTR sem dados.
- **P2 — Elegibilidade lida antes do bloqueio.** Uma reconciliação concorrente
  podia inativar ou reagrupar a oferta enquanto a exposição aguardava o bloqueio
  da Fonte. A leitura de atividade, associação e mercado ocorre após adquirir o
  bloqueio. Regressão reproduz essa intercalação na fronteira de armazenamento.
- **P2 — Outra identidade para oferta já exposta.** Só o UUID era único. Agora,
  constraint parcial no banco e bloqueio da Fonte garantem uma exposição por
  oferta/contexto. Outra identidade recebe 409; retransmissão da identidade
  original continua idempotente. Dois testes simultâneos verificam ambas as regras.
  A migration consolida possíveis duplicatas anteriores, preservando saídas e a
  exposição original.

## Spec

- **P2 — Relatório de Fonte histórica em população vazia.** Mesmo problema do
  primeiro achado Standards, contra a preservação de identidade histórica e
  tratamento de denominador zero do contrato. Corrigido com snapshots retidos.
- **P2 — Unicidade de exposição incompleta.** Mesmo problema do terceiro achado
  Standards, contra “uma vez por Anúncio/contexto de abertura”. Corrigido com
  validação, serialização e constraint, sem inflar denominador/numerador.

Os três casos falharam antes da correção e passaram depois. A suíte final passou
com 132 testes backend, Django check/migrations sem divergências, build
TypeScript/Vite e 12 testes de navegador. Dados externos reais não foram necessários
para o aceite aritmético; o relatório de estoque #13 e o aceite integrado #14
permanecem pendentes. Achados originais: Standards 3 e Spec 2, maior severidade P2
em cada eixo; três problemas únicos, corrigidos.
