# Avaliação documental de segunda Fonte — #9

Verificado em **05/11/2026**. Pesquisa de fontes primárias, sem coleta de catálogo,
consulta a anúncios individuais, contato com terceiros ou alteração da ingestão.

## Resultado

**Nenhuma segunda Fonte autorizada e com sobreposição real suficiente foi
comprovada nesta pesquisa. #9 permanece aberta; #10 não está desbloqueada.**
A lista oficial da CAIXA é candidata para investigar proveniência ou substituir
o canal de entrega da ILB, mas sua duplicação como outra Fonte não demonstra,
por si, comparação entre ofertas independentes. O VendasGov possui exportação
documentada, porém não foi identificada licença específica suficiente para o
uso pretendido nem evidência de imóveis compartilhados com o piloto.

O recorte vigente é interno: venda em Salvador/BA e Campinas/SP, até dois
Anúncios por cidade da mesma Fonte ILB; dados numéricos e URLs com atribuição,
sem imagens, descrições ou contatos. Histórico interno depende da permissão
vigente e é removido na revogação. A confirmação desse piloto não se estende a
outra origem. [Decisão e limites locais](ilb-contract-review.md#decisão-do-responsável--05112026),
[aceite observado](ilb-joint-acceptance.md).

## CAIXA: publicação comprovada, autorização de reutilização pendente

A página oficial de venda oferece o download da lista completa por estado.
A tela oficial de download confirma essa finalidade e a seleção de UF.
Isso comprova um canal público de entrega; não comprova licença para agregação,
republicação ou retenção histórica pelo Placecheck.
[CAIXA: Downloads](https://www.caixa.gov.br/voce/habitacao/imoveis-venda/paginas/default.aspx),
[tela de download](https://venda-imoveis.caixa.gov.br/sistema/download-lista.asp).

A ILB declara que organiza os arquivos CSV estaduais da CAIXA e acrescenta
normalização de municípios e campos derivados. É uma declaração primária do
operador sobre sua própria cadeia de dados, não uma concessão de direitos pela
CAIXA. [ILB: origem dos dados](https://www.imoveisleilaobrasil.com.br/sobre).

Sua documentação apresenta a API como esses dados em JSON, identifica o `id`
como número CAIXA e fornece
`linkOficial` para o portal do banco. Recomenda cache, filtros e identificação
do cliente; o limite publicado sem chave é 30 requisições/minuto/IP. Essas
condições pertencem à API ILB e **não podem ser transplantadas para o download
CAIXA**. [ILB: contrato e boas práticas](https://www.imoveisleilaobrasil.com.br/api).

Os termos ILB §6 permitem uso dos dados imobiliários com atribuição e impõem
restrições de sobrecarga e conteúdo editorial. Essa base sustenta o piloto
existente; não é uma autorização publicada pela CAIXA para outro provider.
[ILB: termos §§6–7](https://www.imoveisleilaobrasil.com.br/termos).

Não foi localizada, nas páginas oficiais recuperadas e buscas documentais, uma
licença CAIXA ou cláusula específica cobrindo o conjunto de tratamentos exigido:
coleta automatizada, armazenamento dos campos selecionados, comparação,
redirecionamento, histórico individual e retenção após retirada. Isso é uma
**lacuna da verificação**, não conclusão de proibição nem prova de inexistência
de autorização em outro documento. O acesso público e a expressão “lista
completa” não resolvem essa lacuna.

### Sobreposição e valor para o produto

**Inferência de proveniência:** se o mesmo número CAIXA aparecer no CSV e na ILB
com o mesmo destino oficial, a hipótese inicial é uma oferta distribuída por
dois canais. Eventual preço divergente pode refletir defasagem de captura,
modalidade ou transformação; não comprova duas condições comerciais
independentes. A inferência decorre da origem declarada pela
[ILB](https://www.imoveisleilaobrasil.com.br/sobre) e do
[contrato de identidade/destino](https://www.imoveisleilaobrasil.com.br/api).

A seleção por estado torna plausível uma investigação futura dos dois mercados;
não foram baixados os arquivos BA/SP, contados resultados ou confrontados IDs.
Não há pares observados, taxa de sobreposição, garantia de estoque atual nas duas
cidades ou quantidade suficiente de exemplos. Dados reais do piloto existente
não demonstram disponibilidade simultânea numa segunda origem.

Cadastrar uma Source adicional só para elevar a quantidade de ofertas distorceria
a leitura do comparador se ambas representarem a mesma oferta. Se CAIXA direta
vier a ser autorizada e a sobreposição for observada, documentar essa proveniência
e distinguir comparação entre canais de concorrência comercial; uma diferença
de captura não demonstra economia disponível. Isso é uma limitação a comunicar,
não um novo critério de independência acrescentado à #9. Os critérios ainda não
comprovados continuam sendo a permissão e os pares efetivamente observados.

## Alternativa pública investigada: VendasGov/SPU

O tutorial oficial de Venda Direta documenta filtros por UF/município e download
dos resultados em tabela eletrônica, com acesso à ficha e edital. É evidência de
uma função de exportação destinada ao usuário, não de licença de reutilização
automatizada ou contrato de feed para terceiros.
[VendasGov: como buscar imóveis](https://www.imoveis.vendasgov.serpro.gov.br/demonstracao/html/demo_13.html).

O painel de transparência da SPU descreve dados patrimoniais extraídos de sistemas
administrativos e informa adaptação à plataforma SPUnet. Um cadastro de imóveis
públicos não equivale a um catálogo de ofertas atuais com preço, modalidade,
destino e disponibilidade. Sua eventual abertura não demonstra sobreposição
com ofertas CAIXA.
[SPU: escopo e situação do painel](https://qlik-publico.paineis.gov.br/extensions/transparencia-ativa/transparencia-ativa.html).

Não foram encontrados nessa documentação licença específica para o uso proposto,
garantias de IDs/retirada ou prova de ofertas comuns aos mercados do piloto.
Não se inspecionaram endpoints internos, editais individuais ou cadastros reais.
A pesquisa não pretende excluir a existência de outros catálogos públicos
adequados: nenhum foi **qualificado** no escopo documental examinado.

## Caminho prático antes de implementar

1. Priorizar uma Fonte com oferta própria ou distribuição expressamente
   autorizada e possibilidade documentada de compartilhar imóveis do piloto.
   Se o responsável quiser seguir com CAIXA direta, esclarecer primeiro se o
   objetivo é substituir o transporte ou validar canais da mesma oferta.
2. Registrar em #9 a evidência de permissão aplicável ao Placecheck: documento,
   titular/concedente, campos, modalidade de uso interno/publicação, atribuição,
   cadência, cache, retenção/histórico e procedimento de revogação/remoção.
   Este estudo não enviou mensagens nem registrou alterações no tracker.
3. Após comprovar permissão pública suficiente no escopo delegado pelo responsável,
   observar uma amostra limitada
   para confrontar identidade do imóvel, unidade, modalidade, preço e destino
   com a ILB nas mesmas cidades. Registrar pares efetivamente observados,
   datas de referência, divergências e limites. Não presumir pares nem definir
   unilateralmente uma quantidade como suficiente para o aceite.
4. Com amostra e critérios aceitos, especificar o contrato e então implementar
   #10 pelo pipeline existente. A permissão de uma Fonte não se herda de outra.

O responsável delegou a pesquisa e a continuação por outra Fonte que permita o
uso sem autorização direta. Uma licença pública suficiente dispensa nova parceria
privada ou confirmação para uma amostra dentro desse escopo. Solicitações de
contratação, contato com terceiros ou expansão do piloto permanecem ações distintas.
[Pesquisa posterior e permissões delimitadas](public-api-candidates.md).

Para essa futura especificação, ainda faltam evidências próprias da candidata:

| Tema | Evidência necessária / restrição do projeto |
| --- | --- |
| Identidade | ID estável por Anúncio e regra para republicação, nova modalidade e reutilização de ID; número do imóvel isolado pode não distinguir ofertas sucessivas. |
| Entrega | Formato, encoding, esquema, data de referência, escopo e completude documentados; CSV não foi inspecionado nesta sessão. |
| Retirada | Sinal explícito de indisponibilidade ou snapshot completo comprovado; falha, resposta parcial e ausência de página não significam exclusão. |
| URL | Destino original autorizado por Anúncio, sem transformar o Placecheck em intermediador de contato/transação. |
| Histórico | Permissão de guardar preços observados, duração, uso e remoção na revogação; não fabricar preços anteriores à primeira captura. |
| Operação | Robots/termos aplicáveis, limites, cache, identificação e suporte a remoção da Fonte antes da coleta. |

## Limitações e validação

Foram lidos os documentos locais de plano, sessão, domínio, glossário e piloto,
e consultadas apenas páginas documentais de primeira parte como evidência.
Buscas também retornaram projetos de terceiros; eles não fundamentam permissões
ou contratos deste relatório. Não houve download de datasets, leitura de ofertas
individuais, configuração de Source, implementação, migração ou coleta.

A ferramenta web recuperou a tela oficial CAIXA de download. A página institucional
de imóveis foi localizada no índice oficial, mas algumas aberturas diretas
retornaram loop de redirecionamento. Tentativas de recuperar termos gerais e
`https://venda-imoveis.caixa.gov.br/robots.txt` não produziram conteúdo verificável.
O tutorial VendasGov foi localizado no índice da própria página; sua abertura
direta retornou falha de cache. Essas falhas limitam a verificação; não foram
contornadas e não representam permissão, bloqueio confirmado ou arquivo vazio.

A consulta documental não valida licença por parecer jurídico nem valida o
contrato técnico real. Não foram executados testes de aplicação ou Docker: o
único artefato desta investigação é este Markdown. Permanecem necessárias a
decisão humana, a evidência de permissão e a amostra autorizada de sobreposição.
