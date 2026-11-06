# Aceite do piloto com fonte única ILB

## Decisão do responsável

Em 05/11/2026, o responsável escolheu **concluir o piloto com ILB e adiar a
comparação entre fontes**. A #14 avalia esse recorte interno; #9/#10 permanecem
abertas como adiadas, com seus critérios preservados. A spec pai #1 não é
alterada nem declarada integralmente concluída.

A #8 já foi aceita pelo responsável, dispensando aguardar variação natural de
preço. Não há novas verificações dessa espera nem alegação de variação real.
O histórico de mudança foi validado em testes e no fluxo controlado. As
[evidências anteriores](ilb-joint-acceptance.md) continuam identificadas como tal.

## Escopo operacional

- Fonte ILB/Spartan TI, dados públicos CAIXA com atribuição; piloto local interno.
- Venda em Salvador/BA e Campinas/SP, até dois anúncios por mercado; sem aluguel.
- Apenas campos numéricos e URLs, sem imagens, descrições ou contatos.
- Histórico interno permitido enquanto vigente; revogação remove os registros.
- Capturas parciais, cache diário e sincronização a cada 15 minutos; ausência de
  página não significa retirada. O detalhe individual validado pode confirmá-la.
- Uma Fonte e quatro ofertas separadas: não há comparação real entre Fontes,
  economia comercial demonstrada ou qualidade de deduplicação real medida.

## Revalidação desta entrega

O Docker estava parado e iniciou pelo comando normal, sem reset ou remoção de
volumes. Os dois projetos Compose isolados subiram com os volumes existentes.
O piloto real permanece separado das fixtures de aceitação.

Build Node 22 reproduzido com `npm ci` e `npm run build`: aprovado, auditoria npm
sem vulnerabilidades. Django check, ausência de novas migrations e `pip check`
aprovados. Quatro smokes ILB aprovados, dois mercados em desktop/celular, com
busca, detalhe, atribuição, histórico disponível e HTTP 302; navegação externa
interceptada, sem contato ou transação. Capturas em
`output/playwright/ilb-final-single-source/`.

O relatório atual retornou uma Fonte publicável, quatro anúncios ativos, quatro
Properties representados, quatro registros de histórico retidos, nenhuma oferta
sem Property e nenhum grupo de múltiplas ofertas. Redução por agrupamento: 0%;
isso não é medida de acurácia. A execução agendada 51 foi parcial, processou
quatro ofertas sem falha, sem inativar ausências da página.

A primeira execução de pytest herdou `ILB_PILOT_MARKETS` e histórico habilitado
do container conjunto: cinco testes de outro recorte falharam. A suíte deve ser
executada com configuração neutra e Redis separado, sem alterar o piloto:

```bash
docker compose -p placecheck-acceptance -f docker-compose.yml -f docker-compose.acceptance.yml exec -T -e REDIS_URL=redis://redis:6379/2 -e ILB_PILOT_MARKETS= -e ILB_PILOT_PRICE_HISTORY=0 backend pytest -q
```

Nessa configuração, **211 testes passaram**, com dois avisos anteriores de
URLField. Nenhum código ou asserção foi alterado para obter esse resultado.

A retirada temporária foi reexecutada na Fonte real, com pausa/publicação
restauradas em `finally`: busca vazia e 404 nos quatro detalhes/redirects durante
a retirada; quatro ofertas, detalhes 200 e destinos 302 corretos na restauração.
Permissões preservadas. Contagens de eventos e redirects internos antes/depois:
0/0 e 0/0, confirmando exclusão, sem inflar métricas de uso comercial.

Na primeira passagem de navegador, 12 testes gerais passaram e dois testes CTR
atingiram o timeout de 15 segundos na chamada do Docker enquanto outras
validações pesadas rodavam. Os smokes reais foram ignorados nessa suíte de
fixtures e executados separadamente, como descrito acima. A repetição com
`npx playwright test --workers=1`, sem carga pesada concorrente, passou:
**14 aprovados e dois smokes reais ignorados nessa suíte**, sem ampliar timeouts
ou alterar asserções. Os quatro smokes reais passaram em sua execução separada.
Artefatos em `output/playwright/acceptance-final-single-source-serial/`.

O cenário aritmético aprovou, em desktop e celular: duas exposições visíveis,
uma exposição com redirect, três redirects brutos e CTR de 50%; retransmissão
e cliques repetidos não inflaram o numerador. As buscas explícitas repetidas
contaram, enquanto ordenação/paginação não criaram novas buscas. Esses resultados
são fixtures controladas, não uso comercial do piloto real. A exclusão de
tráfego interno foi conferida na Fonte real, como descrito acima.

## Situação

**Critérios do piloto de fonte única atendidos.** A #14 pode ser encerrada nesse
escopo, conforme decisão do responsável. A implementação operacional já está em
main; este relatório e o README atualizado são publicados no PR #22. Nenhum
resultado comercial foi inferido. A comparação entre Fontes permanece adiada
em #9/#10, sem aceite fictício desses tickets nem conclusão integral da spec #1.
Não há segunda Fonte a procurar ou integrar nesta entrega. Setup e revogação
continuam no [guia ILB](ilb-pilot.md).
