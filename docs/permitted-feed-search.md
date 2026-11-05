# Pesquisa complementar de fonte com permissão pública

Consulta em 05/11/2026. Escopo: uma **nova** fonte brasileira de ofertas de venda,
com permissão geral publicada para integração, sem cadastro, pagamento ou contato
com operador; preferencialmente Salvador/BA ou Campinas/SP e imóvel também
presente na fonte ILB/CAIXA. Pesquisa documental; nenhum catálogo individual foi
de anúncios imobiliários foi coletado e nenhum provider foi implementado.
Uma página de contratações públicas foi consultada conforme descrito abaixo.

## Resultado

**Não foi confirmada uma segunda fonte que satisfaça o conjunto de requisitos.**
Isso descreve o resultado desta pesquisa, não uma afirmação de inexistência.
O PNCP oferece uma alternativa pública com declaração expressa de reutilização,
mas faltam evidências de ofertas equivalentes às da CAIXA nesses mercados.
Hasta oferece licença aberta para relatórios, não demonstradamente para seu
inventário de anúncios. A existência de uma API ou o caráter público do dado não
foi tratado como licença automática de republicação.

## PNCP — permissão geral de reutilização, compatibilidade por demonstrar

A [FAQ oficial](https://www.gov.br/pncp/pt-br/pncp/perguntas-e-respostas/),
atualizada em 24/09/2026, informa acesso público e gratuito e declara no item 12:
“dados para consulta, reutilização e acompanhamento”. O conteúdo é enviado pelos
órgãos responsáveis por suas contratações, que respondem pela atualização.
Isso é evidência positiva de permissão geral, sem necessidade de pedir aprovação
individual para simples consulta/reutilização dos dados abertos.

A [página oficial de dados abertos](https://www.gov.br/pncp/pt-br/acesso-a-informacao/dados-abertos)
explica consultas sem cadastro/login e download para manipulação em aplicativos.
Limite da verificação: o texto foi recuperado pelo índice de busca; uma abertura
direta posterior retornou HTTP 401. Não houve tentativa de contornar o erro.

Os [manuais oficiais](https://www.gov.br/pncp/pt-br/pncp/manuais) publicam o
Manual da API de Consultas v1.0. A [apresentação técnica oficial do MGI](https://www.gov.br/transferegov/pt-br/noticias/eventos/fntu/ixfntu/apresentacoes/evento-29-equipe-delog-pncp.pdf)
documenta a base `/api/consulta`, incluindo
`GET /v1/contratacoes/publicacao` e `GET /v1/contratacoes/proposta`.

**Inferência e pendências:** editais de alienação de bens públicos podem fornecer
ofertas imobiliárias, mas uma contratação não equivale automaticamente a um
imóvel: um edital pode conter vários lotes, bens móveis ou contratação de serviços.
Não foi demonstrada nesta rodada presença de oferta de venda ativa de Salvador
ou Campinas, nem identidade com um imóvel do ILB. Não há justificativa para criar
uma segunda Fonte operacional apenas para obter dois nomes de origem. Antes de
implementar, seria necessário validar documentação de consulta atual, regras de
acesso/robots, campos de lote, URL original, disponibilidade e coincidência física.
Não se estende a declaração do PNCP a imagens ou documentos externos vinculados.

### Verificação limitada da API CAIXA

O [Manual de Consultas oficial v1.0](https://www.gov.br/pncp/pt-br/central-de-conteudo/manuais/versoes-anteriores/ManualPNCPAPIConsultasVerso1.0.pdf)
documenta filtros por `cnpj`, `codigoMunicipioIbge`, `uf`, modalidade e paginação.
Município/UF referem-se à **unidade administrativa**, portanto não garantem a
localização física de cada lote. O [Swagger oficial](https://pncp.gov.br/api/consulta/swagger-ui/index.html)
identifica o endpoint de propostas abertas e o serviço de detalhe por
órgão/ano/sequencial. A página carregou sem conteúdo textual extraível.

Após confirmar a permissão geral, foi tentada apenas esta consulta filtrada:

```text
GET https://pncp.gov.br/api/consulta/v1/contratacoes/proposta?dataFinal=20261231&cnpj=00360305000104&pagina=1&tamanhoPagina=10
```

Na primeira tentativa, o terminal falhou na resolução DNS de `pncp.gov.br` e a
ferramenta web informou URL inacessível. Posteriormente, a mesma consulta por
PowerShell com acesso de rede autorizado retornou HTTP 200: `totalRegistros=16`,
com dez registros na primeira página. Seus objetos tratavam de serviços,
engenharia, transporte de valores e projetos tecnológicos, sem oferta imobiliária
identificada. A menção a Campinas no registro `00360305000104-1-000845/2026`
era abrangência de instalação de ar-condicionado, não localização de imóvel à venda.
`linkSistemaOrigem` veio nulo nos dez registros. Não houve consulta aos anexos.

Isso não exclui ofertas em outros registros ou períodos e não comprova pares com
ILB. A tentativa de consultar a segunda página não foi executada: a revisão
automática de aprovação falhou por limite de uso, sem avaliar a segurança da ação.
Não houve contorno desse controle. Restam seis registros não examinados dessa
resposta; não há amostra suficiente para aprovar um provider ou alegar sobreposição.

## Hasta — licença aberta restrita a relatórios

A [sala de imprensa do operador](https://hasta.com.br/imprensa) declara que reúne
editais de leiloeiros e CAIXA. Oferece relatórios de desconto por estado/cidade e
histórico de arrematações sob CC BY 4.0; permite reproduzir tabelas e gráficos,
inclusive comercialmente, mediante crédito e link. Isso fundamenta uso dos
relatórios abrangidos, mas **não demonstra autorização para copiar anúncios
individuais, reter seu histórico ou criar catálogo concorrente**. Não foi
localizado nessa página contrato de API de inventário. Não foram acessados lotes.

## Katular — catálogo relevante, licença de reutilização não encontrada

Os [termos publicados pelo Katular](https://katular.com.br/termos) descrevem
agregação de listas CAIXA, Bradesco, Santander, BB, Banrisul, BNB e governos,
além de feeds enviados por anunciantes. A coleta automática declarada é feita
pelo próprio Katular; não constitui concessão de direito aos consumidores do site.
O documento consultado não oferece licença geral de extração/republicação nem
contrato público de API para terceiros. **Candidato não aprovado.** Não foi
examinado seu inventário e não se presume autorização a partir de sua prática.

## Pro Leilão — restrição explícita

Os [termos oficiais da API](https://developer.proleilao.com.br/termos), recuperados
no índice de busca, exigem autorização prévia para reprodução, distribuição ou
comercialização das informações. A abertura direta posterior falhou com
`Cache miss`. Mesmo sem nova leitura direta, o texto disponível não sustenta o
requisito de integração sem autorização individual. Nenhum endpoint foi chamado.

## CAIXA e dados abertos de imóveis — não assumir licença por ser público

A [página oficial de dados abertos CAIXA](https://www.caixa.gov.br/acesso-a-informacao/Paginas/dados-abertos.aspx)
informa que a empresa não está abrangida pelo objetivo do Decreto 8.777/2016.
Isso não prova proibição de usar sua lista, mas impede adotar esse decreto como
fundamento automático de uma licença de feed. Não foi estabelecida nesta pesquisa
uma permissão publicada específica para uma nova integração direta.

O [dataset oficial de ITBI de Porto Alegre](https://dadosabertos.poa.br/dataset/itbi)
tem licença Creative Commons Attribution e arquivos anuais. Trata de transmissões
tributadas, não de anúncios ativos. Não serve como segunda oferta de venda para
comparação no MVP; nenhum arquivo de transações foi baixado.

## Decisão prática

- Manter ILB como única fonte operacional já examinada no projeto.
- PNCP é uma pista concreta de reutilização pública, mas não resolve a exigência
  de sobreposição sem investigação adicional do produto/dados.
- Não habilitar Hasta, Katular ou Pro Leilão com base nas evidências acima.
- Não é necessária aprovação privada quando houver permissão geral suficiente;
  nesta rodada faltou comprovar tal permissão para um **catálogo compatível**.

Esta nota não substitui as avaliações anteriores de LeilôAI, LanceMapa,
ImóveisFaixa, TuLugar ou Guru. Não foram repetidas suas consultas individuais.
Validação realizada: leitura de documentação e termos primários e uma página da
API oficial, sem mudança no stack, sem ingestão, sem contas criadas e sem contato externo. Testes de aplicação
e Docker não se aplicam à inclusão desta nota documental.
