# Candidatas com permissão pública para a segunda Fonte

Pesquisa documental em **05/11/2026**, pelo fluxo `mattpocock-skills:research`.
Uma licença pública expressa pode fundamentar a integração sem parceria privada;
API acessível ou catálogo público, isoladamente, não demonstram republicação permitida.
Nenhuma candidata abaixo foi qualificada para importação de amostra nesta verificação.
O responsável confirmou que somente a ILB está implementada e delegou a busca
de outra Fonte com permissão pública suficiente, sem exigir contato direto.
Não se exige parceria privada nem acesso anônimo como condição de qualificação.

## LeilôAI

- A [página de números](https://leiloai.com/leiloai-em-numeros) concede CC BY 4.0
  **aos números daquela página**, com atribuição, link e data. Não estende essa
  licença aos Anúncios individuais. A referência a API/MCP não amplia a concessão.
- O [manifesto de descoberta](https://leiloai.com/.well-known/mcp.json) declara
  licença `proprietary`, autenticação obrigatória por bearer e chave a partir do
  plano Investidor Pro. Documenta `/api/v1/items`, filtros por UF/cidade e limites
  por plano; não oferece servidor MCP remoto nem entrega anônima de Anúncios.
- A [documentação REST](https://leiloai.com/api) confirma a chave obrigatória,
  listagem/detalhe/exportação e cotas. A palavra “pública” no rodapé significa
  API documentada para assinantes, não acesso gratuito sem autenticação.
- Os [termos, §§6–7](https://leiloai.com/termos) permitem painel pessoal/profissional
  e compartilhamento moderado com parceiros/clientes; proíbem redistribuição em
  massa, revenda sem autorização expressa e scraping automatizado do painel.
  São usos permitidos, mas não esclarecem retenção de registros individuais e
  histórico no catálogo agregador pretendido. Não interpretar uma API paga como
  proibida ou exigir acordo privado se seus termos gerais cobrirem o uso.
- As [instruções do widget](https://leiloai.com/embed/instrucoes) permitem
  incorporar gratuitamente a vitrine em qualquer site/blog, sem cadastro,
  mantendo a atribuição visível. Essa é uma permissão expressa de exibição;
  não documenta extração, armazenamento, normalização ou histórico dos registros.
  Um iframe isolado não permite associar as ofertas pelo pipeline do Placecheck
  nem satisfaz o aceite de comparação entre Fontes da #10.
- Os [feeds RSS/Atom/JSON](https://leiloai.com/feeds) são apresentados como guias,
  análises e notícias; a documentação não os descreve como feed de Anúncios.
- A [transparência de cobertura](https://leiloai.com/numeros) informa acervo nacional
  e ressalva que acervo sem encerramento informado não equivale a pregão marcado.
  Esses agregados não comprovam estoque válido nem pares com ILB nos dois mercados.

**Decisão:** exibição por widget está permitida, mas a integração necessária
à #9 ainda não foi qualificada. Cadastro/chave não são impedimentos de licença;
a [API](https://leiloai.com/api) exige assinatura a partir de Investidor Pro.
Não contratar para testar direitos ainda não comprovados. Não confundir licença
dos indicadores ou do iframe com licença de importação de ofertas individuais.

## LanceMapa

- A [página da Fonte CAIXA](https://lancemapa.com/fonte/caixa-imoveis), recuperada
  pelo índice de primeira parte, informa coleta em 04/11/2026 e catálogo CAIXA.
  É evidência declarada de proveniência, não autorização para nossa republicação.
- A [metodologia](https://lancemapa.com/metodologia) descreve coleta automática,
  deduplicação e retirada de lotes com data passada. Não concede licença de uso
  dos Anúncios a terceiros nem documenta API de distribuição.
- A página [Dados](https://lancemapa.com/dados) permite citar seus **números** com
  link. Não se trata de licença publicada para reutilizar registros individuais.
- O link oficial de termos aponta para
  [termos-de-uso](https://lancemapa.com/termos-de-uso), cuja recuperação retornou
  falha de cache. A tentativa de `robots.txt` também não produziu documento
  verificável. Essas falhas não demonstram proibição nem permissão.

**Decisão:** permissão de integração não estabelecida; sem base para coletar
amostra ou inferir sobreposição atual com Salvador/BA e Campinas/SP.

## Outras candidatas verificadas

- [Tu Lugar — documentação](https://tulugar.com/pt/api-docs): leitura pública
  gratuita sem chave, mas a seção de limites proíbe copiar ou exibir os anúncios
  em outro portal/site. Não atende à exibição pretendida; não foi consultado catálogo.
- [Guru dos Imóveis — dados abertos](https://gurudosimoveis.com.br/dados):
  CC BY 4.0 para séries mensais por bairro, com mediana, percentis e contagens.
  Inclui Salvador e Campinas, mas são indicadores agregados, sem IDs/URLs de
  ofertas individuais; não demonstra pares comparáveis nem licencia os anúncios.
  Nenhum CSV ou catálogo foi baixado. `robots.txt` não foi recuperado.

## Limites da pesquisa e próximo passo

Somente documentos, descoberta de API e buscas de fontes primárias foram usados.
Resultados de busca incidentais incluíram trechos de catálogo; não foram abertos
catálogos ou fichas, chamados endpoints de dados, retidos registros individuais,
criados cadastros ou enviadas mensagens. Não houve contorno de bloqueios.
Robots LeilôAI também não foi recuperado pela ferramenta web.

Não exigir contato privado quando outra candidata publicar licença suficiente:
seguir diretamente por sua documentação, verificar robots/limites e só então
observar uma amostra limitada de Anúncios atuais nos mercados do piloto.
Este estudo não comprovou pares, não implementou provider e não altera o aceite
da segunda Fonte. Apenas Markdown foi criado; testes de aplicação não se aplicam.
