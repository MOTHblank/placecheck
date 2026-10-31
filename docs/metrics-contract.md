# Contrato proposto das métricas — #11

**Estado: proposta para decisão do responsável pelo produto; não aprovado.**
Preparado em 31/10/2026 para [#11](https://github.com/MOTHblank/placecheck/issues/11).
Os tickets [#12](https://github.com/MOTHblank/placecheck/issues/12) e
[#13](https://github.com/MOTHblank/placecheck/issues/13) dependem desse contrato.
Não altera a spec pai #1, autoriza coleta ou comprova cobertura real.

## Objetivo e contagens

Medir descoberta e saída para ofertas, atualização e agrupamento. Contato,
negociação e venda ocorrem na Fonte e não são inferidos dos eventos.

| Medida | Unidade proposta |
| --- | --- |
| Busca | Uma execução explícita de filtros válidos que recebeu resultados com sucesso, inclusive resultado vazio. Novo envio, mesmo com filtros iguais, conta novamente. Abrir diretamente uma URL com filtros conta uma vez; carregamento inicial sem filtros não conta. Paginação, ordenação, Voltar/Avançar, rerender e retry da mesma execução não geram busca adicional. |
| Visualização de Imóvel | Uma abertura de detalhe carregada com sucesso. Fechar e reabrir ou recarregar a página conta nova abertura. Retry ou rerender da mesma abertura não conta novamente. Alterar filtros enquanto o detalhe está aberto cria novo contexto somente após carregar o novo detalhe com sucesso. |
| Exposição de oferta | Uma oferta real no comparador aberto cujo artigo intercepte a área visível da página, com documento visível. Uma vez por Anúncio/contexto de abertura. Ofertas só retornadas pela API, ocultas por modalidade ou fora da área visível não contam. Rolar pode revelar novas ofertas; voltar à mesma oferta não a conta novamente naquela abertura. Não exige tempo mínimo e não comprova leitura. |
| Redirect bruto | Cada resposta de saída HTTP 302 válida para Anúncio ativo de Fonte publicada, após exclusões. Cliques repetidos contam saídas brutas distintas. Saída inválida/404 não conta. |
| Exposição com saída atribuída | Uma exposição elegível que teve ao menos uma saída atribuível. Repetir cliques nessa exposição não aumenta essa contagem. |

Cada busca, abertura e exposição tem identidade opaca própria. A retransmissão do
mesmo evento é idempotente. Reutilizar essa identidade com conteúdo diferente é
erro, sem sobrescrever o evento original. As identidades duram o contexto de
navegação necessário, sem identificar uma pessoa entre visitas.

Eventos de UI são recebidos pelo backend, que valida a identidade, referências e
elegibilidade; o timestamp usado para relatório, retenção e atribuição é o horário
do servidor ao aceitar o evento. O cliente não pode retroagir o horário. Uma
exposição só fica atribuível depois de aceita; falhas de entrega podem causar
subcontagem e devem ser documentadas. A saída não deve depender de disponibilidade
da instrumentação de UI.

## Atribuição e CTR por Fonte

O link de saída identifica a exposição de origem de forma opaca e validável pelo
servidor, vinculada ao mesmo contexto de navegação, Anúncio e Fonte. Não atribuir
por igualdade de IP, referer ou pela última exposição de outra aba. Saída sem essa
identidade, inválida ou incompatível fica somente no bruto; não escolher outra
exposição por aproximação.

A janela proposta é **[exposição, exposição + 30 minutos)**. Um clique exatamente
aos 30 minutos fica fora. A oferta precisa continuar elegível na saída.

**CTR = exposições com ao menos uma saída atribuída / exposições elegíveis × 100.**
O denominador zero resulta em **sem dados**, não 0%. O numerador pertence ao período
da exposição; bruto pertence ao período do clique. Relatórios recentes podem mudar
até fechar a janela e devem indicar esse fato. Essa medida é CTR de exposições de
ofertas, não de usuários únicos nem taxa de conversão comercial.

| Sequência conhecida | Resultado |
| --- | --- |
| Duas ofertas da mesma Fonte expostas; três cliques em uma delas dentro da janela | 2 exposições, 1 com saída, 3 redirects brutos; CTR 50%. |
| Retransmitir as duas exposições com as mesmas identidades | Continua 2 exposições; CTR não muda. |
| Nova abertura expõe novamente ambas, sem cliques | Total 4 exposições, 1 com saída; CTR 25%. |
| Saída sem exposição ou após o limite | Aumenta somente o bruto. |
| Exposição às 23:55; clique às 00:05 do dia seguinte | Numerador do dia da exposição; bruto do dia do clique. |

## Períodos, mercados e relatório restrito

Eventos usam intervalos **[início, fim)**, com timezone IANA explícito; padrão do
piloto: `America/Bahia`. Armazenamento temporal em UTC. Horários locais ambíguos ou
inexistentes devem ser rejeitados em vez de corrigidos silenciosamente. Informar
período, timezone, horário da extração e eventual janela de atribuição ainda aberta.

Mercado significa **cidade + UF + modalidade** (`sale` ou `rent`). Comparações
separam modalidades; nome da cidade sem UF não identifica mercado. Eventos de
oferta guardam o mercado e a Fonte no momento da ocorrência, sem reclassificação
retroativa por alteração de Anúncio ou agrupamento.

O relatório será um comando de gestão executável pela equipe com acesso autorizado
ao ambiente, sem endpoint público nem dashboard. Filtros: período, timezone, Fonte
e mercado. Fonte inválida ou parâmetros inconsistentes são erro explícito.

Buscas e visualizações são medidas da jornada, sem Fonte única. Com filtro de
Fonte, esses totais aparecem como **não se aplica**, sem atribuí-los arbitrariamente
a todas as Fontes do resultado. Filtro de mercado aplica-se às medidas com mercado
conhecido; buscas amplas sem mercado completo aparecem num total separado, sem
distribuição inventada. Exposições e saídas permitem filtro de Fonte/mercado.

Cobertura: relatar somente mercados presentes no inventário autorizado. A proposta
de pelo menos duas combinações cidade/modalidade permanece condicionada ao acordo
de #7; o contrato de métricas não aprova mercados nem promete cobertura nacional.

## Estoque atual e agrupamentos

Estoque é medido **no instante da consulta**, separado dos eventos do período.
Publicação exige Fonte publicada e não demonstrativa; pausa de coleta não retira
publicação. Aplicar Fonte/mercado antes das contagens, na mesma população de ofertas.

| Contagem | Regra proposta |
| --- | --- |
| Fontes publicáveis | Fontes publicadas não demo, mesmo sem estoque; com filtro de mercado, somente as que têm oferta ativa nesse mercado. |
| Anúncios ativos publicáveis (L) | Anúncios ativos dessas Fontes, dentro do mercado selecionado quando houver. |
| Imóveis representados (P) | Properties distintos dos Anúncios contados em L. Anúncio sem Property é inconsistência explícita; não fabricar indicador com esse estoque. |
| Imóveis com múltiplas ofertas | Properties com pelo menos dois Anúncios em L. |
| Históricos retidos | Registros de preço ainda permitidos das Fontes publicáveis e mercado selecionados, incluindo Anúncios inativos; distinguir essa população do estoque ativo. |

**Redução por agrupamento = (L − P) / L × 100.** L=0 resulta em sem dados.
Exemplo: 6 Anúncios representando 4 Imóveis → 33,33%. Isso mede compressão de
estoque, não acurácia. Falsos agrupamentos e duplicidades perdidas precisam de
amostra revisada e não são inferidos dessa fórmula. Eventos passados não mudam por
reagrupamento; o estoque atual pode mudar.

Por Fonte, apresentar última SyncRun completa bem-sucedida e suas quantidades
processadas/inativadas, além da falha mais recente e horários. Execução parcial não
substitui sucesso completo; coleta pausada e retirada pública ficam identificadas.
Não apresentar essas contagens como série histórica de estoque.

## Exclusões, minimização e retenção

Excluir demo, tráfego interno/teste explicitamente identificado e automação conhecida
de todas as medidas da jornada. Fixtures continuam disponíveis em ambiente de teste,
sem contaminar o relatório real. Classificação de tráfego interno deve vir de
configuração controlada pela equipe; não confiar em um sinal arbitrário do cliente
para classificar tráfego como real. Detecção de bots é limitada, sem fingerprint.

Proposta: **90 dias de retenção dos eventos individuais**, a partir da aceitação.
Sem IP, referer completo, user agent persistido, texto livre de busca, contato ou
identificador pessoal. Classificar automação em memória e descartar os cabeçalhos.
Guardar somente identidades opacas, tipo/horário e referências mínimas necessárias
à atribuição e aos filtros. Não copiar descrição, endereço ou URL privada para eventos.

Guardar a identidade histórica da Fonte e o mercado independentemente da existência
futura do Listing. Retirada de publicação não reescreve eventos anteriores quando
a retenção ainda é permitida; revogação que exija remoção elimina os dados atingidos.
Não depender do cascade atual de RedirectEvent para esse comportamento.

Limpeza agendada e comando manual verificável removem eventos com idade de pelo
menos 90 dias e suas identidades/atribuições auxiliares. Não manter agregados ou
cópias individuais paralelas para contornar esse limite. O relatório recusa intervalos
anteriores à janela disponível e informa o início da instrumentação; não apresenta
ausência de coleta ou dados expirados como zero observado. Backups e logs não podem
ser usados como uma segunda base de eventos fora da política acordada.

## Implementação, testes e decisão pendente

Reutilizar analytics, API, frontend e Celery existentes; não criar plataforma de
analytics. O código atual só registra RedirectEvent com sessão/referer/user agent,
FK de Listing em cascade e sem atribuição. Não satisfaz este contrato.

Interfaces propostas para testes em #12/#13:

- Navegador → API → PostgreSQL → redirect: comprova exposição efetiva, sequência
  determinística, CTR, retransmissão e mobile; não comprova atenção humana ou feed real.
- API de eventos e saída: cobre validação, identidade, limites temporais, exclusões
  e idempotência; não comprova visibilidade no navegador.
- Comandos de relatório/limpeza, com fixtures de ingestão e agrupamento: comprovam
  aritmética, filtros, estoque, retirada, retenção e estado operacional; não comprovam
  acurácia da deduplicação em inventário real.

Essas interfaces e regras **aguardam confirmação**. Após a decisão, registrar o
contrato no #11 e os termos resolvidos no GLOSSARY, antes de implementar #12/#13.
Não há mudança de comportamento, nova coleta de eventos ou alegação de aceite neste
rascunho. Autorização de Fontes e cobertura real continuam pendentes em #7/#9.
