# Revisão dos tickets #2–#6

Referência confirmada pelo usuário: `HEAD` antes da implementação, fixado em
`9b47aebc6029d3e318b99749512df673474d5763`.
Comparação: `git diff 9b47aeb...HEAD`. Implementação: `5830aa6`;
correções após revisão: `c8836d9`. Duas revisões independentes seguiram a skill
`mattpocock-skills:code-review`; os revisores confirmaram o fechamento dos achados.

## Standards

- **P2 — Permissões ao trocar a Fonte no admin.** A Fonte de um Listing existente
  permanecia editável; transferir um anúncio com histórico para uma Fonte que não
  permite retenção preservava esse histórico. Contrariava as permissões exigidas
  pelo AGENTS.md e documentadas no README. Corrigido tornando Fonte e ID externo
  somente leitura nos anúncios existentes, com regressão pela interface do admin.
- **P2 — Bairro com acentos na seleção de candidatos.** O filtro SQL `iexact`
  excluía `Graça`/`Graca` antes do score, embora o score considere essas grafias
  equivalentes. Contrariava o aceite de associação de ofertas equivalentes da
  Sprint 5. O filtro foi removido; cidade/estado, tipo, área e características
  continuam reduzindo candidatos, e bairro é validado canonicamente no score.

Nova revisão: ambos corrigidos; nenhum achado adicional de Standards.

## Spec

- **P2 — Republicação podia restaurar grupo incompatível.** Ignorar membros
  retirados permitia corrigir uma unidade durante a retirada e manter o mesmo
  Property ao republicar a outra Fonte. Contrariava #5: “unidades distintas [...]
  permanecem separados” e reavaliação de associação/separação. Ofertas ativas
  retidas continuam restringindo a identidade do grupo, independentemente de sua
  visibilidade. Regressão verifica retirada, correção, republicação, API e auditoria.
- **P2 — Troca de Fonte no admin preservava histórico proibido.** O mesmo problema
  identificado em Standards contrariava #3: “Retenção ou remoção do histórico
  respeita a permissão da Fonte”. Resolvido pela proteção da identidade existente.

Nova revisão: ambos corrigidos; nenhum achado acionável ou expansão de escopo.
Fontes reais, autorizações e contrato de métricas permanecem explicitamente pendentes.

Total: Standards 2, Spec 2; maior severidade original P2 em cada eixo; zero
pendências após correção. São três problemas únicos, pois um aparece nos dois eixos.
