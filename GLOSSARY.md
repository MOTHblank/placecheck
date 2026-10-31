# Placecheck

Vocabulário do agregador de anúncios imobiliários, conforme o plano do produto.

## Linguagem

**Imóvel (Property)**:
O imóvel físico ou conceitual ao qual uma ou mais ofertas se referem.
_Evitar_: anúncio como sinônimo de imóvel.

**Anúncio (Listing)**:
Uma oferta de um imóvel publicada por uma fonte, com preço e endereço original próprios.
_Evitar_: imóvel como sinônimo de anúncio.

**Fonte (Source)**:
A origem dos anúncios agregados pelo Placecheck.

**Fonte autorizada**:
Uma fonte cujo fornecimento e uso dos anúncios pelo Placecheck estão permitidos dentro de um escopo identificado. A existência de uma página pública ou de um feed não comprova essa permissão.

**Redirecionamento**:
A saída do Placecheck para um anúncio original. Não comprova contato, proposta ou venda.

**Histórico de preço**:
Os preços observados para um anúncio ao longo do acompanhamento, sem afirmar preços anteriores à primeira observação.

**Mercado**:
Uma combinação de cidade, UF e modalidade de negociação, venda ou aluguel.
_Evitar_: cidade isolada como sinônimo de mercado.

**Busca**:
Uma execução explícita de filtros válidos com resultados carregados, inclusive quando vazios. Paginação, ordenação e repetição técnica da mesma execução não constituem nova Busca.

**Visualização de Imóvel**:
Uma abertura de detalhe carregada com sucesso. Uma nova abertura constitui outra visualização; repetir o carregamento da mesma abertura não.

**Exposição de oferta**:
A apresentação visível de um Anúncio no comparador aberto, uma vez por oferta e contexto de abertura. Não comprova leitura ou interesse da pessoa.
_Evitar_: oferta retornada como sinônimo de exposição.

**Redirect bruto**:
Uma saída válida para um Anúncio publicável, sem exigir uma Exposição de oferta atribuível. Cliques repetidos representam saídas distintas.

**Saída atribuída**:
Um Redirect associado à Exposição de oferta que originou o clique, dentro da janela de atribuição. Repetir saídas da mesma exposição não aumenta a quantidade de exposições com saída.

**CTR por Fonte**:
A proporção de Exposições de oferta de uma Fonte que tiveram ao menos uma Saída atribuída. Não mede pessoas únicas, contato ou conversão comercial.

**Estoque publicável**:
O conjunto atual de Anúncios ativos de Fontes publicadas e não demonstrativas, dentro do recorte consultado. Pausar a coleta não equivale a retirar a publicação.

**Redução por agrupamento**:
A proporção de Anúncios do Estoque publicável que excede a quantidade de Imóveis distintos representados. Mede compressão de estoque, sem comprovar acurácia das associações.
_Evitar_: acurácia da deduplicação como sinônimo de redução por agrupamento.
