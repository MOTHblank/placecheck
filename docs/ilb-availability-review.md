# Revisão da verificação individual ILB

Base: `a803dee` (merge do PR #18). Implementação inicial: `6d25824`;
correção de transporte: `7cbcc1d`. Duas revisões independentes seguiram
`mattpocock-skills:code-review`, usando `git diff main...HEAD` e as regras
do projeto, o contrato da ILB e o escopo delimitado de remoção da #8.

## Standards

- **P2 — Rejeitar corpos HTTP incompletos antes de alterar disponibilidade.**
  `HTTPResponse.read(n)` pode retornar JSON aparentemente completo mesmo com
  bytes faltando em relação a Content-Length. Um 404 com o marcador de ausência
  poderia inativar uma oferta após corte da resposta. Também havia
  `IncompleteRead` em resposta chunked fora do tratamento de transporte.
  Corrigido validando o comprimento declarado e convertendo `HTTPException`
  em falha transitória nos caminhos 200 e 404. Nenhum cheiro de código
  material foi apontado.

## Spec

- **P2 — Aplicar retry e registrar a falha final de respostas truncadas.**
  `IncompleteRead` não herda OSError nem ValueError. O erro podia escapar
  do retry e do registro sanitizado, sem cooldown diário, contrariando o
  contrato operacional. Corrigido pelo mesmo tratamento de transporte,
  preservando a oferta e registrando disponibilidade desconhecida após
  esgotar os retries. Nenhuma outra lacuna acionável no recorte implementado.

Os quatro cenários negativos com HTTPResponse real em memória reproduziram
as falhas antes da correção: 200/404 com Content-Length incompleto e com
chunks truncados. Controles positivos dos quatro enquadramentos completos
confirmam que respostas legítimas continuam aceitas. Os testes verificam
retries, falha final, preservação da oferta e cooldown, sem rede externa.

Ambas as revisões confirmaram o fechamento em `7cbcc1d`, sem achados residuais.
A suíte final passou com 189 testes backend/PostgreSQL; Django check e migrations
sem divergências. Permanecem dois avisos anteriores sobre URLField/Django 6.

Achados por eixo: Standards 1 (P2, corrigido); Spec 1 (P2, corrigido).
Há um problema de transporte comum aos dois eixos, corrigido, sem pendências
de revisão. Histórico de preços e inventário conjunto seguem fora desta entrega.
