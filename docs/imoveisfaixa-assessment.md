# ImóveisFaixa — candidata a segunda Fonte (#9)

Pesquisa documental em **05/11/2026**, usando a skill `mattpocock-skills:research`.
Escopo: qualificar a candidata, sem cadastro, contratação, contato ou coleta.

## Resultado

**Candidata plausível para diligência documental; ainda não qualificada para #9.**
Não foram comprovados permissão aplicável ao Placecheck, amostra autorizada
nem sobreposição observada suficiente. A pesquisa não desbloqueia #10.
O recorte vigente continua interno, venda em Salvador/BA e Campinas/SP,
até dois Anúncios por mercado da mesma Fonte ILB, sem imagens, descrições ou
contatos; sua permissão não se estende à candidata.
[Contexto e pendências](second-source-assessment.md).

## Evidência primária localizada e qualidade da recuperação

Os resultados abaixo vieram do **índice das próprias páginas primárias**,
incluindo texto estruturado, não de documentos contratuais obtidos diretamente.
A abertura direta de `/api-de-dados` retornou 404, com e sem `www`;
`/termos` e `/privacidade` falharam por cache/acessibilidade da ferramenta.
O índice informou atualização há dois meses para a API e há uma semana para
termos/privacidade. Portanto, não se confirmou a vigência operacional da oferta.
Esses erros não demonstram proibição, permissão nem inexistência do serviço.

Os [termos indexados](https://www.imoveisfaixa.com.br/termos) identificam a
marca como pertencente à **IB Labs**, agregadora do que a CAIXA publica, sem
vínculo com o banco. Remetem a compra à CAIXA/leiloeiro e alertam para mudanças
de preço e retirada de imóveis. Não apareceu, no texto recuperado, concessão
de reutilização, retenção, comparação ou histórico pelo Placecheck.
A [privacidade indexada](https://www.imoveisfaixa.com.br/privacidade) confirma
IB Labs como responsável e `support@iblabs.io` como contato.
Não se comprovou razão social/CNPJ nem autoridade contratual para sublicenciar
todos os dados; o domínio e a autodeclaração da marca não resolvem isso.

O [robots.txt recuperado](https://www.imoveisfaixa.com.br/robots.txt) contém
`User-agent: *` e `Disallow:` vazio, mas a ferramenta indica captura antiga
(há 1,6 ano). Não valida política atual nem concede licença de armazenamento.

## Oferta e contrato técnico anunciados, ainda não testados

A [página de API indexada](https://www.imoveisfaixa.com.br/api-de-dados) anuncia:

- JSON nacional CAIXA/leilões; `X-API-Key` em `api.imoveisfaixa.com.br`.
- Sandbox grátis, sem cartão, chave self-service, 100 requisições/dia;
  planos pagos ativados pela equipe. Segredo exibido uma vez.
- `GET /api/imoveis/`, paginação `count/next/previous/results`, valores em
  string e cidade/UF aninhadas; exemplo com `id`, tipo e valor mínimo.
- Histórico premium por `id_externo`; Sandbox descrito como dado público
  estruturado sem histórico, sem esclarecer explicitamente se é live ou sintético.
- Eventos de novo imóvel/preço/status anunciados, sem contrato de entrega.
- Marketing para alimentar portais; Enterprise anuncia uso comercial licenciado.

Isso sugere adequação funcional, **não constitui licença**. A contratação
precisa esclarecer quais direitos pertencem a cada plano. Não se presume que
comprar acesso ao histórico autorize republicá-lo, nem que sua cobrança proíba
guardar preços observados; são tratamentos distintos a confirmar.

## Lacunas para o aceite

| Tema | Evidência que falta obter antes de coletar/implementar |
| --- | --- |
| Permissão | Documento vigente, concedente identificado e escopo Placecheck: recebimento automatizado, armazenamento numérico/URLs, exibição interna/pública, comparação e atribuição. |
| Histórico | Direito de guardar observações próprias e, separadamente, usar histórico fornecido; prazos, cache, retirada, revogação e eliminação. |
| Entrega | Esquema versionado, filtros exatos Salvador/BA e Campinas/SP, limites por minuto/dia, identificação, timestamps, completude e acesso real no plano escolhido. |
| Identidade | Estabilidade e relação entre `id`, `id_externo`, imóvel e modalidade; republicação/reutilização de IDs e URL original por Anúncio. |
| Retirada | Sinal documentado de exclusão/inativação; distinção entre ausência, erro e resposta parcial; autenticação/repetição dos eventos se utilizados. |
| Sobreposição | Amostra real autorizada, pares com ILB, data, unidade, modalidade, preço e destino; quantidade suficiente aceita pelo responsável. |

**Inferência de proveniência:** como os termos atribuem os dados à CAIXA,
eventuais pares podem representar a mesma oferta em dois canais. Confirmar
isso na amostra; divergência de captura não demonstra oportunidade comercial.
Não foram contados pares, consultados IDs reais nem afirmada cobertura atual
das duas cidades. Exemplo de documentação não equivale a Anúncio observado.

## Continuação conforme orientação do responsável

O responsável delegou procurar outra Fonte que permita o uso sem autorização
direta. Não é obrigatório obter acordo privado se documentação pública vigente
cobrir o uso. Esta candidata continua sem qualificação porque a oferta não pôde
ser verificada diretamente e faltam os direitos/contrato descritos acima.

1. Procurar documentação vigente cobrindo as lacunas, com escopo inicial
   numérico/URLs e uso interno. Esta pesquisa não autoriza mensagens a terceiros.
2. Se houver permissão suficiente, verificar acesso e natureza dos dados do
   Sandbox antes de preparar amostra; não confundir cadastro/chave com licença.
   Não houve cadastro, chave, compra ou aceitação de termos nesta sessão.
3. Observar amostra limitada nos mercados autorizados, registrar pares efetivos
   e validar o aceite de #9 antes de especificar o provider de #10.

## Validação e limites

Lidos plano, prompt local, domínio, glossário, README e avaliação anterior;
verificados git status, registro de providers e permissões de Source existentes.
Não há diretório `docs/adr/`. A pesquisa alterou somente este Markdown.
Buscas documentais devolveram incidentalmente páginas de catálogo/anúncios;
elas foram excluídas da evidência e não houve abertura dirigida desses anúncios,
chamada à API, feed, endpoint interno ou download de dataset.
Não houve contorno de falhas de acesso. Testes de aplicação/Docker não executados:
nenhum comportamento, configuração ou stack foi alterado.
