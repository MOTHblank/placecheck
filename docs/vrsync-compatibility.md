# VRSync como entrada autorizada do Placecheck

Pesquisa inicial para o ticket #15, em 31/10/2026, concluída com a decisão registrada em 05/11/2026: **usar a API JSON ILB para a primeira Fonte e adiar VRSync**. A primeira Fonte já foi escolhida e autorizada no escopo interno da #7, com implementação nos PRs #20/#21. Não há feed VRSync autorizado nem compatibilidade real XML comprovada. Este estudo não cria parser, credenciais ou coleta XML.

## Decisão de formato — 05/11/2026

A pergunta da #15 permite escolher um provider VRSync específico, CSV/JSON/API ou
adiar. Para a primeira Fonte escolhida, a API JSON ILB já entrega o contrato
necessário e tem permissão pública de uso dos dados com atribuição, aplicada ao
recorte interno aprovado. A captura real e o histórico inicial em Salvador/BA e
Campinas/SP estão documentados no [aceite conjunto](ilb-joint-acceptance.md).
Referências: [decisão humana da #7](https://github.com/MOTHblank/placecheck/issues/7),
[API publicada](https://www.imoveisleilaobrasil.com.br/api) e
[contrato de uso revisado](ilb-contract-review.md).

| Entregável do estudo | Resultado |
| --- | --- |
| Matriz com evidência identificada | Tabelas e fixture sintética abaixo: campos, ausências, enums, URLs, preços, períodos, `Sale/Rent`, privacidade e snapshots. Não é uma amostra de parceiro. |
| Escolha com razões e custo | Usar o provider JSON ILB existente. XML acrescentaria parser seguro, perfil do parceiro, expansão de modalidades e snapshot sem resolver uma necessidade da Fonte escolhida. |
| Encaminhamento para a primeira integração | A #8 usa o contrato ILB registrado na #7; PRs #20/#21 foram integrados. O aceite real de mudança de preço ainda pertence à #8. |
| Limites do estudo | Não fornece autorização XML, não coleta feeds de terceiros e não afirma comparação real ou MVP concluído. |

Assim se conclui **o estudo e a escolha de formato para a primeira Fonte**, sem
afirmar compatibilidade VRSync real. As perguntas condicionais de licença,
amostra, namespace, completude e frequência de um parceiro XML continuam
obrigatórias **se uma futura Fonte fornecer VRSync**. Elas não bloqueiam a opção
JSON escolhida e não são marcadas como comprovadas. Uma futura integração XML
precisará de ticket com Fonte e amostra autorizadas, respeitando o máximo de duas
Fontes do piloto; não se amplia a #8 silenciosamente.

O restante preserva a investigação técnica de 31/10. Suas propostas de adaptação
VRSync não são trabalho solicitado para o provider JSON atual. A existência de
exemplos oficiais de XML continua sendo evidência de formato, não de licença de
anúncios: [exemplos Grupo ZAP](https://developers.grupozap.com/feeds/vrsync/examples.html).

## Evidências e limites

- **Verificado na documentação oficial:** o Grupo ZAP publica exemplos de venda, aluguel e oferta combinada em VRSync. A existência desses exemplos não concede direito de republicação. [Exemplos oficiais](https://developers.grupozap.com/feeds/vrsync/examples.html).
- **Verificado sobre Imobzi:** o produto permite configurar integrações, escolher imóveis/filtros e obter uma URL XML atualizada periodicamente. Não se deve presumir que a carteira inteira esteja nesse arquivo, nem que a frequência satisfaça o piloto. [Ajuda de publicação](https://help.imobzi.com/imobiliarias/support/solutions/articles/156000386836).
- **Verificado, com escopo restrito:** o artigo da integração Lais informa que a integração Viva Real gera XML VRSync. Isso demonstra uma possibilidade técnica naquele fluxo; não comprova o formato de toda exportação Imobzi nem acesso concedido ao Placecheck. O caminho terminado em `create_ticket` fornecido na pesquisa retorna esse artigo; nenhum chamado foi criado. [Ajuda Lais](https://help.imobzi.com/imobiliarias/support/solutions/articles/156000387167/create_ticket).
- **Não verificado:** parceiro concreto, contrato, preço comercial, URL, autenticação, dialecto efetivamente exportado, qualidade dos dados, completude, cidades, modalidades e volumes. Não foram consultados feeds de clientes nem contatados fornecedores.
- **Estado inicial em 31/10:** havia pipeline e provider manual. **Estado atual:** o registry também constrói o provider ILB JSON e sua composição de dois mercados. `XmlFeedProvider` continua abstrato e sem parsing. A escolha de JSON não implementa nenhuma das propostas XML abaixo. [Contrato](../backend/apps/sources/providers/base.py), [registry](../backend/apps/sources/providers/registry.py), [README](../README.md).

As tabelas distinguem regras oficiais resumidas, contrato local atual e **propostas futuras**, que exigem decisão e testes em #8. Não equivalem a uma certificação de conformidade integral com o XSD. Não se carregou o XSD remoto.

## Matriz de compatibilidade

Na coluna local, “obrigatório” significa necessário para persistência válida pelo pipeline atual; “opcional” aceita vazio ou nulo. Todos os argumentos da dataclass precisam ser fornecidos, mesmo quando seu valor pode ser `None`. [Schemas](../backend/apps/sources/schemas.py), [normalizer](../backend/apps/sources/normalizers/listing.py), [Listing](../backend/apps/listings/models.py), [persistência](../backend/apps/ingestion/services.py).

### Identidade, origem e localização

| Entrada VRSync / evidência | Contrato local atual | Proposta para #8 |
| --- | --- | --- |
| `ListingID`: único, 1–50 caracteres. [Listing](https://developers.grupozap.com/feeds/vrsync/elements/listing.html) | `source_external_id` → `external_id`, obrigatório, até 150; unicidade por Source | Preservar o ID upstream e criar identidade de oferta com modalidade, conforme seção seguinte; rejeitar IDs vazios/repetidos em vez de escolher arbitrariamente. |
| `DetailViewUrl` aparece nos exemplos. [Exemplos](https://developers.grupozap.com/feeds/vrsync/examples.html) | `url` obrigatório, URLField com tamanho padrão 200 | Exigir URL pública do anúncio original, HTTP(S) validada, dentro do limite. Confirmar sua presença na amostra; não usar URL do XML, página inicial, URL de portal inventada ou parâmetro secreto. A obrigatoriedade upstream não foi estabelecida aqui. |
| `Title`: 10–100 caracteres; `TransactionType`: `For Sale`, `For Rent`, `Sale/Rent`. [Listing](https://developers.grupozap.com/feeds/vrsync/elements/listing.html) | `title` obrigatório, até 255; `transaction_type` obrigatório: `sale` ou `rent` | Adaptador traduz explicitamente os valores; o normalizer atual não reconhece as strings VRSync. Tipo desconhecido falha, sem inferência por preço. |
| Mínimo documentado: país, estado, cidade, bairro; CEP também declarado obrigatório. [Listing](https://developers.grupozap.com/feeds/vrsync/elements/listing.html) | Cidade/UF obrigatórias; bairro opcional; não há país, CEP, rua, número ou complemento nos schemas | Exigir Brasil e UF válida, usar `State/@abbreviation`; não truncar nome de estado. Preservar acentos. Definir perfil aceito com o parceiro: o exemplo mínimo oficial omite CEP, logo exemplo isolado não resolve obrigatoriedade. |
| `displayAddress`: `Neighborhood`, `Street`, `All`; XML pode trazer endereço detalhado mesmo quando sua exibição é restrita. [Listing](https://developers.grupozap.com/feeds/vrsync/elements/listing.html) | Sem indicador de privacidade; coordenadas opcionais são expostas na API; título/descrição podem conter endereço | Não perder a restrição ao converter. Até existir política explícita, suprimir coordenadas exatas quando a exibição for restrita/desconhecida e remover informação proibida de título/descrição. Não transformar complemento privado em título para melhorar dedup. |

A publicação de coordenadas locais foi conferida em [serializers](../backend/apps/properties/serializers.py). O feed pode conter dados que o remetente não permite publicar: presença no XML não substitui permissão. Perder coordenadas ou unidade pode reduzir agrupamentos automáticos; respeitar essa restrição tem precedência sobre aumentar cobertura da deduplicação.

### Valores e características

| Entrada oficial resumida | Contrato local atual | Proposta para #8 |
| --- | --- | --- |
| `ListPrice` para venda; `RentalPrice` para aluguel; ambos na oferta combinada. Valores inteiros, `currency="BRL"`. [Details](https://developers.grupozap.com/feeds/vrsync/elements/details.html) | `price` opcional, Decimal(14,2), sem moeda/período | Validar lexicalmente antes do normalizer genérico; moeda diferente/ausente ou valor malformado falha. Não converter câmbio nem adivinhar centavos. Obrigatoriedade upstream não autoriza preencher preço ausente com zero. |
| Aluguel: ausência de `period` significa mensal; há exemplos `Monthly`, `Daily`, `Weekly`, `Quarterly`, `Yearly`; uma ocorrência por imóvel. [Details](https://developers.grupozap.com/feeds/vrsync/elements/details.html) | Não há período no domínio; comparação usa apenas preço e modalidade | Aceitar apenas mensal no piloto. Não multiplicar diária nem dividir anual para fabricar aluguel mensal. Período desconhecido ou repetição torna captura incompatível, sem reconciliação de ausências. |
| `Iptu`: BRL, inteiro, `Monthly`/`Yearly`, anual por padrão; substitui `yearlyTax`. [Details](https://developers.grupozap.com/feeds/vrsync/elements/details.html). Exemplos antigos usam `YearlyTax`. [Exemplos](https://developers.grupozap.com/feeds/vrsync/examples.html) | `iptu` opcional, Decimal(12,2), sem semântica temporal | Decidir período canônico antes de gravar; proposta: anual, mensal × 12 com proveniência e regra documentada. Confirmar casing legado na amostra; não aceitar ambos silenciosamente se divergirem. Sem decisão, não publicar IPTU ambíguo. |
| `PropertyAdministrationFee` representa condomínio, BRL; zero significa isento. [Details](https://developers.grupozap.com/feeds/vrsync/elements/details.html) | `condominium_fee` opcional, Decimal(12,2) | Confirmar periodicidade com parceiro; manter zero distinto de ausência. Não assumir equivalência de taxas diversas. |
| `PropertyType` possui enum amplo; `LivingArea`/`LotArea` usam `square metres`; escolha depende do tipo. [Details](https://developers.grupozap.com/feeds/vrsync/elements/details.html) | Listing exige texto até 30; Property aceita `apartment`, `house`, `land`, `commercial`, `other`; uma só `area`, opcional | Tabela explícita por tipo: apartamento → `apartment`, casa → `house`, terreno → `land`, escritório → `commercial`; restante precisa de decisão. Não enviar enum inglês longo ao normalizer. Escolher área útil para apartamento e de terreno para lote; não substituir uma pela outra só porque está preenchida. Guardar semântica de origem se ampliar tipos. |
| `Bedrooms`, `Bathrooms`, `Garage`, `Suites`; obrigatoriedade de quartos/banheiros varia por tipo. [Details](https://developers.grupozap.com/feeds/vrsync/elements/details.html) | Contagens opcionais, inteiros positivos incluindo zero | Mapear vagas para `parking_spaces`; validar inteiro, sinal e faixa antes do normalizer, que extrai dígitos permissivamente. Não transformar desconhecido em zero. |
| `Description`: obrigatória na validação upstream, 50–3.000 caracteres. [Details](https://developers.grupozap.com/feeds/vrsync/elements/details.html) | Texto opcional; Source pode proibir retenção | Persistir somente com autorização de descrição. Ignorar imagens, contato e campos fora do MVP. Metadados de autorização ficam separados dos campos do anúncio. |

Os modelos não definem que `iptu` ou condomínio sejam mensais/anuais, e os schemas não têm slots para moeda, período, natureza da área ou `displayAddress`. Isso é uma lacuna local real, não uma conversão já suportada. Decidir em #8 se a amostra permite um perfil estrito sem novos campos ou se exige uma pequena mudança explícita no contrato. [Schemas](../backend/apps/sources/schemas.py), [modelos](../backend/apps/listings/models.py).

**Ausências e erros — proposta:** elemento ausente/vazio opcional vira `None` para números e texto vazio para texto opcional; `0` informado permanece zero. Não inventar cidade, preço, quarto, coordenada ou URL. Rejeitar negativos, NaN/infinito, overflow, valores decimais onde o perfil exige inteiro, enum/unidade inesperados e par de coordenadas incompleto ou fora da faixa. Preservar o erro de validação de forma sanitizada. Um registro inválido impede considerar aquela execução completa, mesmo se outros registros válidos forem atualizados. A política exata de quarentena/retomada ainda deve ser desenhada.

## Oferta combinada: identidade é o principal ajuste

Hoje cada `parse(payload)` produz **um** `RawListing`, cada task normaliza/persiste **um** resultado, e a identidade de persistência é `(source, external_id)`. Reutilizar o mesmo ID para venda e aluguel sobrescreveria modalidade/preço e misturaria históricos. O normalizer também não transforma `Sale/Rent` em duas ofertas. [Contrato](../backend/apps/sources/providers/base.py), [tasks](../backend/apps/ingestion/tasks.py), [persistência](../backend/apps/ingestion/services.py).

**Proposta:** adotar desde a primeira captura IDs determinísticos para **todas** as modalidades: `SYN-42:sale`, `SYN-42:rent`. O ID original permanece dado de proveniência, associado à Source; não basta inferi-lo retirando um sufixo arbitrário de texto. Uma oferta somente de venda já usa `:sale`; depois, a oferta combinada acrescenta `:rent` sem recriar a venda. Retornar a apenas venda inativa somente o aluguel, após snapshot completo bem-sucedido; remoção do item inativa ambos. Reaparição mantém IDs/histórico quando sua retenção estiver permitida. Documentar política de IDs reaproveitados pelo parceiro e de múltiplas filiais antes do piloto.

Não basta criar dois IDs: `calculate_similarity` retorna score zero para ofertas da **mesma Source**, com razão `different-listings-same-source`. Atualmente as duas modalidades não serão reunidas automaticamente no mesmo Property. Coordenadas e títulos iguais não superam esse bloqueio. Os schemas também não carregam identidade upstream separada. [Deduplicação](../backend/apps/deduplication/services.py).

#8 precisa definir uma passagem explícita de identidade por proveniência: duas ofertas derivadas do mesmo item validado da mesma Source podem compartilhar Property sem enfraquecer as regras entre fontes ou entre itens diferentes. Exigir validação de consistência, auditoria e bloqueios compatíveis com o matcher existente. Decidir onde guardar essa relação e como revalidá-la em atualização/separação. Não usar similaridade genérica ou título fabricado como substituto.

Uma alternativa de escopo pequeno a avaliar em #8 é expandir o item combinado em referências por modalidade durante discovery, de modo que cada fetch/parse ainda entregue um RawListing. Isso exige payloads derivados da mesma captura imutável, ID original explícito e contagem/reconciliação por oferta derivada. A outra alternativa é alterar o contrato para múltiplas saídas; tem impacto maior em tasks, contagens e testes. Este documento não escolhe nem implementa um framework universal.

Casos de aceite futuros: mesma captura repetida sem novo histórico; alteração só do preço de aluguel; venda → combinado → venda; remoção/reaparição; IDs iguais em Sources diferentes; colisão/duplicação upstream; ofertas irmãs no mesmo Property; itens distintos da mesma Source separados; regras conservadoras entre fontes preservadas; restrição de endereço preservada.

## Captura imutável, completude e remoções

**Código atual:** `is_complete_snapshot=False` é o padrão. `SyncRun` controla execução vigente, referências e IDs processados; captura parcial não reconcilia ausências. Falha pode ocorrer após gravar itens válidos. `sync_source`, `fetch_listing` e `process_listing` constroem providers separadamente; memória da instância não é armazenamento de snapshot. [Base](../backend/apps/sources/providers/base.py), [tasks](../backend/apps/ingestion/tasks.py), [runs](../backend/apps/ingestion/runs.py), [reconciliação](../backend/apps/ingestion/services.py).

**Proposta obrigatória antes da integração:** baixar uma vez, validar e fixar uma captura imutável identificada por execução, com digest, escopo e referências derivadas. Todas as tasks/retries consultam a mesma versão persistida; nunca rebaixar o XML corrente para cada anúncio. Definir retenção mínima, acesso e descarte do arquivo conforme autorização, pois payload bruto pode conter dados cuja persistência não é permitida. Uma solução sem retenção bruta deve persistir apenas o subconjunto autorizado, ainda imutável. Expiração antes do fim da execução falha sem inativar.

XML bem formado, HTTP 200, `PublishDate`, tamanho plausível ou `</ListingDataFeed>` **não provam inventário completo**. O contrato do parceiro precisa declarar totalidade dentro de um escopo estável, exclusões, filtros/paginação, disponibilidade de versão e significado do vazio. Uma mudança de filtro não pode parecer remoção de todo o restante. Somente após download íntegro, parsing seguro, validação de todos os itens/modalidades e processamento completo da mesma captura autorizada poderá haver reconciliação. XML vazio só pode inativar tudo se houver confirmação contratual e operacional de inventário completo vazio; indisponibilidade ou truncamento nunca equivalem a vazio.

## Segurança e transporte propostos

Python alerta que XML não confiável pode causar consumo excessivo de recursos e acessos indevidos; suas proteções variam com parser/Expat. A documentação recomenda avaliar `defusedxml` para parsing em servidor. [Documentação Python 3.12](https://docs.python.org/3.12/library/xml.html). Esta é justificativa técnica para avaliar uma dependência pequena em #8, não uma dependência adicionada nesta pesquisa.

- Configurar parser sem DTD, entidades internas/externas, XInclude ou resolução de rede/arquivos; rejeitar declarações perigosas. Nunca buscar `schemaLocation`; se validação XSD vier a ser necessária, usar versão revisada e fixada localmente, sem imports remotos.
- Limites iniciais **propostos**, a ajustar com amostra: 10 MiB comprimidos, 25 MiB descomprimidos, 10 mil itens, profundidade 32 e texto de 64 KiB por campo. Contar bytes efetivos durante leitura, sem confiar só em Content-Length; interromper streaming ao limite. Limitar também quantidade de referências e dados enviados ao broker.
- Endpoint HTTPS previamente aprovado, TLS verificado, host/porta permitidos e bloqueio de destinos locais/privados/metadados; redirects desativados ou revalidados a cada salto. Feed autenticado não é endpoint a descobrir por tentativa. Credenciais em configuração secreta, sem URL tokenizada em logs, broker ou issue pública; validar também URLs públicas de saída.
- Proposta de timeout HTTP: conexão 3 s, leitura 10 s e orçamento total menor que os 30 s soft/45 s hard atuais. Respeitar limite por Source e frequência acordada. Usar cache/ETag quando suportado; 304 não é inventário vazio. Não é garantia de snapshot apenas ter ETag se tarefas voltarem a ler uma URL mutável.
- Traduzir timeout, 429 e falhas transitórias em erro transitório, com backoff/Retry-After e limite; 401/403, schema incompatível, excesso de limites e XML malformado falham sem retry cego. Nunca contornar CAPTCHA/login/bloqueios. As tasks já têm até três retries transitórios, mas não há transporte HTTP XML implementado. [Tasks atuais](../backend/apps/ingestion/tasks.py).

## Casos sintéticos de mapeamento

O fragmento abaixo foi criado para esta pesquisa; não é uma exportação de parceiro, não contém contatos e não foi validado como feed completo do portal. Sua forma segue os exemplos públicos, mas usa dados inventados e domínio reservado. [Estrutura de referência](https://developers.grupozap.com/feeds/vrsync/examples.html).

```xml
<ListingDataFeed xmlns="http://www.vivareal.com/schemas/1.0/VRSync">
  <Listings>
    <Listing>
      <ListingID>SYN-42</ListingID>
      <Title>Apartamento sintético para demonstração</Title>
      <TransactionType>Sale/Rent</TransactionType>
      <DetailViewUrl>https://parceiro.example/ofertas/SYN-42</DetailViewUrl>
      <Details>
        <PropertyType>Residential / Apartment</PropertyType>
        <ListPrice currency="BRL">480000</ListPrice>
        <RentalPrice currency="BRL" period="Monthly">2400</RentalPrice>
        <Iptu currency="BRL" period="Monthly">120</Iptu>
        <PropertyAdministrationFee currency="BRL">0</PropertyAdministrationFee>
        <LivingArea unit="square metres">72</LivingArea>
        <Bedrooms>2</Bedrooms>
        <Bathrooms>1</Bathrooms>
        <Garage>1</Garage>
      </Details>
      <Location displayAddress="Neighborhood">
        <Country abbreviation="BR">Brasil</Country>
        <State abbreviation="BA">Bahia</State>
        <City>Testópolis</City>
        <Neighborhood>Bairro Sintético</Neighborhood>
        <PostalCode>00000-000</PostalCode>
      </Location>
    </Listing>
  </Listings>
</ListingDataFeed>
```

**Resultados esperados da proposta, não comportamento implementado:**

| Caso sintético | Resultado futuro esperado |
| --- | --- |
| Fragmento acima | Dois RawListings: `SYN-42:sale`, `sale`, `480000.00`; `SYN-42:rent`, `rent`, `2400.00`. Ambos: `apartment`, área `72.00`, condomínio `0.00`, cidade/UF informadas, URL original. Suítes/coordenadas ausentes ficam nulas. |
| IPTU mensal 120, se aprovada a convenção anual | `iptu=1440.00` em ambos; origem/período e conversão rastreáveis. Sem convenção, não persistir valor ambíguo. |
| Substituir IPTU por `<Iptu currency="BRL" period="Yearly">1440</Iptu>` | Mesmo valor canônico proposto. Ausência do atributo deve seguir o default oficial explicitado na matriz. |
| Amostra legada contendo `<YearlyTax currency="BRL">1440</YearlyTax>` | Aceitar somente após confirmar tag/semântica no perfil do parceiro; mesma saída anual se confirmada. Novo e legado divergentes falham, sem precedência silenciosa. |
| Repetir a captura e depois mudar somente aluguel para 2300 | Primeira repetição não duplica anúncios/histórico; segunda gera histórico apenas em `:rent`, quando autorizado. |
| Remover aluguel e manter venda em captura completa | Preserva `:sale` e seu histórico; inativa `:rent`. Em captura parcial ou inválida não reconcilia ausências. |
| Retirar `DetailViewUrl` ou usar URL do XML | Falha; não fabricar destino original. |
| Trocar moeda por USD; aluguel `Daily`; área sem unidade; ID duplicado; contagem negativa | Falha de perfil/validação; captura não é completa para fins de remoção. Nenhuma conversão silenciosa. |
| Falta de preço, quarto ou área | Nulo quando opcional no perfil local acordado; se obrigatório no perfil contratado, falha. Nunca zero inventado. |
| Inserir coordenadas exatas sob `displayAddress="Neighborhood"` | Não publicar coordenadas precisas pelo simples fato de existirem no XML; aplicar a política de restrição antes de RawListing. |
| DOCTYPE/entidade, truncamento ou excesso de bytes | Rejeitar captura; não interpretar falha como inventário vazio. |

As duas ofertas do primeiro caso **ficariam separadas no código atual**. O resultado desejado de Property compartilhado depende da passagem de proveniência discutida acima e deve ser testado junto da expansão; esses exemplos não são testes executados.

## Escolha do formato e próximos passos

Comparação de esforço **qualitativa**, sem cotação ou estimativa contratual:

| Opção autorizada pelo parceiro | Custo técnico relativo e condição |
| --- | --- |
| VRSync existente e representativo | Adaptador específico, namespace, enums, períodos, expansão, snapshot e parsing seguro. Vantagem somente se o parceiro já o fornecer com direitos e escopo adequados. |
| JSON/CSV estável fornecido pelo parceiro | Pode reduzir conversões se já trouxer uma oferta por modalidade e URL original; CSV exige contrato de colunas/encoding/decimais. Mesmas obrigações de autorização, snapshot, remoções e qualidade. O provider manual não lê CSV diretamente. |
| API oficial autorizada | Pode oferecer IDs e atualizações mais explícitos; custo adicional de autenticação, paginação, quotas e consistência entre páginas. Só vale comparar após conhecer disponibilidade/contrato. |

Depois de #7, preferir o menor adaptador que cumpra o contrato real; se houver VRSync adequado, implementar um provider VRSync específico em #8, preservando `Provider → RawListing → Normalizer → NormalizedListing → upsert Listing`, Celery e deduplicação por regras. Não antecipar leitor XML universal, múltiplos CRMs, IA ou microserviços. A menor quantidade de código não compensa perder modalidade, privacidade ou histórico.

Checklist para o responsável por #7, **sem contato realizado nesta pesquisa**:

1. Identificar a imobiliária/fonte e o responsável que pode autorizar fornecimento, agregação pública, redirecionamento, retenção de histórico e eventual descrição/imagem; registrar limites, revogação e remoção. Confirmar termos aplicáveis; feed público não basta.
2. Pedir amostra mínima autorizada/sanitizada de venda, aluguel e combinado, mudanças de modalidade/preço, campos ausentes, restrição de endereço e exclusões. Confirmar IDs estáveis, reaproveitamento, filiais e URLs individuais públicas. Não anexar dados pessoais ou credenciais em issue pública.
3. Acordar cobertura e volume por cidade/modalidade, incluindo **duas combinações cidade–modalidade** para o piloto se #7 confirmar esse recorte. Não inventar cidades ou prometer cobertura com base na documentação do formato.
4. Confirmar frequência de geração e atualização desejada, atraso tolerável, limites, caching, manutenção, autenticação e canal operacional para falhas. A expressão “periodicamente” da ajuda Imobzi não define SLA. [Ajuda oficial](https://help.imobzi.com/imobiliarias/support/solutions/articles/156000386836).
5. Confirmar se o arquivo é total ou parcial dentro de quais filtros, como versionar uma captura, distinguir vazio legítimo de erro e refletir exclusões; obter regra para revogar direitos e retirar dados já retidos.
6. Usar essas respostas para fechar em #8 o perfil estrito, identidade por modalidade/proveniência, períodos, semântica de área, privacidade e armazenamento imutável. Só então implementar e executar testes sintéticos, testes da ingestão/Celery e aceite com a fonte autorizada.

**Validação histórica de 31/10:** inspeção de código e documentação primária;
`docker compose exec -T backend pytest -q` passou com 68 testes (dois avisos de
depreciação Django), e `docker compose exec -T frontend npm run build` passou
com TypeScript/Vite. Nenhum parser ou teste executável VRSync foi implementado;
os casos da tabela são expectativas. Não houve acesso a feed de parceiro ou
repetição do bootstrap, pois a alteração é documental. A compatibilidade real
permanece condicionada à amostra e às decisões acima. A #15 permanecia aberta nessa data;
não substitui a autorização de #7, a implementação de #8 ou o aceite integrado.

**Validação da conclusão em 05/11:** decisão confrontada com #7, registry atual,
documentação oficial de exemplos VRSync/API ILB e evidências dos PRs #20/#21.
Mudança documental: não se repetiram pytest, build ou bootstrap; os 211 testes e
smokes do [aceite conjunto](ilb-joint-acceptance.md) são evidência anterior da
implementação JSON, não testes de um parser XML. Não houve download de feed real,
cadastro de Fonte ou alteração do piloto nesta conclusão.
