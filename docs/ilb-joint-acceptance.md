# Aceite do inventário conjunto ILB — 05/11/2026

O piloto conjunto está em execução com quatro ofertas reais da mesma Fonte:
duas de Salvador/BA e duas de Campinas/SP. O escopo está na
[#7](https://github.com/MOTHblank/placecheck/issues/7); a implementação está no
[PR #20](https://github.com/MOTHblank/placecheck/pull/20). A #8 permanece aberta:
ainda não foi observada mudança real de preço após habilitar o histórico.

## Evidências reais

O Compose isolado `placecheck-ilb-joint` subiu seis serviços com Python 3.12,
PostgreSQL 16, Redis 7 e Node 22. `setup_ilb_pilot` apenas configurou a Fonte;
o Beat disparou a captura e o worker a processou via Redis.

As duas primeiras execuções (`SyncRun` 1 e 2) terminaram como `partial`, com quatro
ofertas processadas cada e nenhuma inativação. A repetição preservou quatro
Listings e quatro registros iniciais de preço. A lista de origem é de 03/11/2026;
o horário da captura não representa atualização na CAIXA.

| Mercado de venda | IDs da amostra | Preços observados em reais |
| --- | --- | --- |
| Salvador/BA | `8555510770382`, `8444400798566` | 32.113,78; 33.398,37 |
| Campinas/SP | `8444408919605`, `8787717568753` | 104.992,75; 106.667,03 |

A natureza do valor continua determinada pela modalidade, sem tratar lance mínimo
ou referência como preço final. Não há aluguel ou segunda Fonte. Os quatro
anúncios ficam separados por falta de evidência suficiente para agrupamento.

Quatro smokes reais Chromium passaram: cada mercado em desktop e celular, com
busca, detalhe, atribuição, data da lista, histórico inicial e saída HTTP 302.
O teste verifica o destino original CAIXA e intercepta a navegação externa, sem
contato ou transação. Retirada temporária retornou busca vazia e 404 nos quatro
detalhes/redirects; a restauração em `finally` recuperou quatro ofertas, destinos
302 e histórico inalterado. Beat usou 15 segundos na validação, preservando cache
diário e cota compartilhada; ao final voltou ao padrão de 900 segundos.

## Regressões e revisão

- **211 testes backend passaram**, incluindo round trip JSON no broker Redis
  real. Banco Django de teste e Redis DB 2 ficaram separados do inventário e do
  broker/cache DB 0 do piloto. Restam dois avisos anteriores de URLField.
- Build TypeScript/Vite no Node 22, `pip check`, Django check e migrations sem
  divergências passaram. Nenhuma migration ou biblioteca nova foi introduzida.
- A suíte geral passou com 14 cenários de navegador; os dois smokes ILB foram
  ignorados no stack fictício e executados separadamente nos quatro casos reais.
- No projeto `placecheck-acceptance`, `verify_async_ingestion` observou captura
  agendada, repetição, mudança de preço com exatamente um registro adicional e
  ausência completa com inativação. São fixtures, não mudança na Fonte real.

A revisão independente motivou correções reproduzidas primeiro com testes
falhando: setup preserva pausa/retirada ao revogar histórico; escopo é conferido
sob bloqueio e nunca sobrescrito; primeira captura autorizada de preço estável
cria observação atual, sem reconstrução retroativa. Coleta conjunta e histórico
ficam limitados aos mercados aprovados e a dois itens por mercado, inclusive
quando configuração do worker e permissão no banco divergem. O modo legado de
um único mercado sem histórico conserva sua configuração anterior.

Experimento isolado inverteu em memória a condição do limite: duas regressões
falharam como esperado. Nenhum arquivo ou worker do piloto foi alterado pela
mutação; o processo de teste foi encerrado.

## Falha de instalação corrigida

A instalação limpa resolveu Kombu 5.7.0, que rejeitava redis-py 5.2.1 ao criar
o canal, encerrando worker e Beat. O teste com broker em memória não detectava
essa incompatibilidade. A nova regressão reproduziu o erro antes da correção.
`kombu[redis]==5.4.2` fixa uma dependência já transitiva e declara o transporte,
compatível com os pins existentes: Celery 5.4 aceita Kombu >=5.3.4,<6 e essa
versão de Kombu aceita redis-py 5.2.1. Sem upgrade de Celery ou Redis.
[Contrato Celery](https://github.com/celery/celery/blob/v5.4.0/requirements/default.txt),
[contrato Redis do Kombu](https://github.com/celery/kombu/blob/v5.4.2/requirements/extras/redis.txt)
e [changelog revisado](https://github.com/celery/kombu/blob/v5.4.2/Changelog.rst).

Antes disso, Docker Desktop 4.73 não conseguia remover sockets AF_UNIX antigos em
`%LOCALAPPDATA%\Docker\run` e `%LOCALAPPDATA%\docker-secrets-engine`. Preservar
as pastas temporárias com outro nome, com os processos parados, permitiu ao Docker
recriá-las e iniciar Engine 29.4.3/WSL. Sem reset, prune, exclusão de volumes,
desregistro WSL ou alteração de discos persistentes. Recuperação baseada em
[relatos no rastreador do Docker](https://github.com/docker/desktop-feedback/issues/554)
e comprovada neste ambiente; não é alteração no Placecheck.

## Operação e revogação

O [guia do piloto](ilb-pilot.md#inventário-conjunto-de-dois-mercados) traz o setup.
Para repetir os smokes reais em PowerShell:

```powershell
$env:ILB_PILOT_BROWSER = "1"
$env:ILB_PILOT_PRICE_HISTORY = "1"
$env:ILB_PILOT_BROWSER_CITIES = "Salvador,Campinas"
$env:PLAYWRIGHT_BASE_URL = "http://127.0.0.1:25175"
cd frontend
npx playwright test tests/ilb-pilot.spec.ts
```

Para revogar o histórico de forma persistente, defina `ILB_JOINT_PRICE_HISTORY=0`
no `.env`, recrie backend/worker com o mesmo `compose up -d --wait` do guia e
repita `setup_ilb_pilot`. Aplica `can_retain_price_history=False`, remove os
registros e impede novas gravações, preservando os controles atuais de pausa e
publicação. Alterar apenas o `.env` não muda a permissão já salva na Fonte.
O admin também permite revogar diretamente; mantenha a configuração coerente antes
de repetir setup. Reabilitar retenção começa pela próxima observação permitida,
sem recuperar dados apagados. Revogar histórico é irreversível para os registros;
retirada pública, por si só, preserva a retenção ainda permitida.

## Aceite restante

A amostra real não mudou de preço nesta sessão: existem quatro observações
iniciais, não uma série de variações. O comportamento de mudança passou em testes
e no fluxo assíncrono controlado, mas falta observá-lo pela Fonte real para
concluir o critério conjunto da #8. Remoção individual real foi comprovada no
PR #19. Duas páginas não comprovam snapshot completo. #9/#10 dependem de segunda
Fonte autorizada e sobreposta; #14 depende desses aceites. Nenhum preço real foi
alterado ou inventado para fechar issue. O estudo VRSync #15 não constitui amostra
autorizada nem provider XML.
