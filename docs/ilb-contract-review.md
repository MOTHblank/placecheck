# Revisão do contrato público ILB

Consulta documental independente em 04/11/2026, usando documentação do operador.
Os smokes reais desta sessão estão registrados separadamente no piloto. Este
registro complementa [o piloto](ilb-pilot.md); não altera código, permissões
configuradas, escopo aprovado ou aceite de #7/#8.

## Declarações explícitas

- **Uso dos dados:** os termos §6 permitem usar dados imobiliários, inclusive
  pela API, com atribuição à fonte original. Proíbem sobrecarga, redistribuição
  editorial sem autorização e apresentação como serviço oficial. O §7 distingue
  dados públicos da CAIXA de textos, ilustrações, ranking e código próprios. Os
  termos têm revisão declarada em 23/10/2026. Não exigem parceria privada para
  esse uso. [Termos, §§6–7](https://www.imoveisleilaobrasil.com.br/termos).
- **Processamento e acompanhamento:** a documentação apresenta monitor diário
  comparando execuções, exportação CSV, cruzamento de bases e armazenamento de
  estatísticas ao longo dos meses. Solicita cache, filtros e identificação;
  publica 30 requisições/minuto/IP sem chave e indica chave dedicada para
  espelhamento pesado. Não oferece SLA. Não especifica duração de retenção de
  preços individuais. [API: exemplos, limites e boas práticas](https://www.imoveisleilaobrasil.com.br/api).
- **Identidade e remoção:** o OpenAPI 1.1.0 define `id` como número CAIXA estável
  enquanto o imóvel estiver à venda; o parâmetro de detalhe aceita 5–20 dígitos.
  O `404` do detalhe significa ausência na lista atual, provavelmente venda,
  sem comprovar a causa. [OpenAPI: Imovel e consultarImovel](https://www.imoveisleilaobrasil.com.br/api/openapi.json).
- **Cobertura:** há filtros UF/cidade, paginação e modalidades de venda; limite
  máximo de página 100. O esquema de busca traz `total`, `pagina`, `limite`,
  `listaGeradaEm` e `resultados`. Não declara cursor/versionamento de snapshot,
  ordem imutável, tombstones, prazo de remoção ou aluguel.
  [OpenAPI: buscarImoveis](https://www.imoveisleilaobrasil.com.br/api/openapi.json).

## Interpretação e limites

A permissão pública é evidência positiva para o uso delimitado de dados
numéricos com atribuição; não é apenas a constatação de endpoint acessível.
Cache e acompanhamento longitudinal têm exemplos expressos. Ainda assim,
**histórico de preço por anúncio e prazo de retenção não estão expressamente
definidos**. Considerá-los abrangidos pelo uso geral seria interpretação, não
uma autorização específica publicada. Tampouco há licença nominal cobrindo
todos os tratamentos futuros. Para esta avaliação, os termos do operador não
comprovam direitos adicionais de terceiros.
[Base dessa interpretação](https://www.imoveisleilaobrasil.com.br/termos).

É tecnicamente plausível testar vários mercados de venda com consultas
filtradas e cache diário, dentro da mesma cota por IP. Isso não equivale a
aprovar expansão do piloto ou provar cobertura nacional. O contrato técnico
comporta vários recortes; o piloto atual vincula cada Source ao recorte
configurado e orienta ambiente isolado para outro recorte.
[Filtros públicos](https://www.imoveisleilaobrasil.com.br/api),
[operação atual](ilb-pilot.md).

Paginar até o total ou observar a mesma data não garante captura atômica.
Um `404` validado pelo endpoint de detalhe poderia fundamentar uma futura
reconciliação individual; timeout, bloqueio, resposta inválida e ausência numa
página não podem ser convertidos em remoção. O piloto atual não faz essa
consulta individual e deve continuar tratando suas capturas como parciais.
[Contrato do detalhe e busca](https://www.imoveisleilaobrasil.com.br/api/openapi.json),
[limitação implementada](ilb-pilot.md).

Na revalidação final, `robots.txt` respondeu HTTP 200 pelo container do piloto,
com o User-Agent Placecheck. Continua contendo `Disallow: /api/` para o agente
genérico e exceções nominais para outros agentes. Não simulamos esses agentes.
A integração continua restrita ao cliente da interface JSON expressamente
documentada; isso não autoriza rastreamento HTML ou de buscas. A ferramenta web
e a primeira consulta local não haviam conseguido obter esse arquivo; a
verificação final não depende do registro histórico de 31/10.
[`robots.txt`](https://www.imoveisleilaobrasil.com.br/robots.txt),
[interface oferecida a clientes](https://www.imoveisleilaobrasil.com.br/api).

## Recomendações para o aceite pendente

1. **#7:** registrar a permissão pública como base do escopo permitido, sem
   inventar obrigação de parceria. Delimitar publicação, campos e retenção;
   resolver a interpretação de histórico antes de ampliar coleta. Manter imagens,
   editorial e dados pessoais fora do piloto.
2. **#8:** o piloto comprova um recorte, idempotência e atualização sem
   histórico; ainda não comprova ciclo real de histórico ou remoção, inventário
   completo e vários mercados. Projetar reconciliação individual por detalhe
   ou obter garantia de completude antes de reconciliar ausências. Acrescentar
   testes do contrato e evidência supervisionada somente no escopo aprovado.
3. Não declarar #7/#8 encerradas por esta pesquisa. Não exigir aluguel, segunda
   Fonte ou parceria como propriedades que esta API promete: são limitações e
   critérios do produto a avaliar separadamente, sem reescrever os tickets.

Validação desta revisão: confrontação documental com fontes primárias. As capturas,
testes, configuração adicional e a correção de apresentação estão documentadas em
[ilb-pilot.md](ilb-pilot.md#revalidação-e-aceite-por-critério--04112026).

Atualização técnica posterior: a [verificação individual](ilb-availability.md)
foi implementada e executada pelo worker real, com uma ausência validada do
catálogo e retirada pública daquela oferta. A recomendação técnica de remoção
individual acima foi atendida; isso não cria garantia de snapshot completo nem
resolve a interpretação/decisão de retenção do histórico de preços.
