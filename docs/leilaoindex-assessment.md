# Leilão Index — qualificação documental

Pesquisa em 05/11/2026 para a segunda Fonte do piloto interno: venda em
Salvador/BA e Campinas/SP, no máximo dois anúncios por mercado.

**Resultado: não disponível para implementar agora.** A API anunciada ainda está
em lista de espera; não foi identificado contrato técnico público operacional nem
permissão pública suficiente para o uso pretendido. Não houve cadastro, compra,
contato, consulta ao catálogo ou coleta de amostras. Exemplos incidentais da página
institucional não foram tratados como amostras do piloto.

## Evidência primária

- [Página oficial, planos e API](https://www.leilaoindex.com.br/): a integração
  programática é apresentada como **“Em breve”**, com lista de espera para um futuro
  plano API destinado a conectar a base a sistemas e planilhas. Não apresenta nessa
  seção endpoint, autenticação, schema, paginação, limites, política de cache ou
  semântica de remoção. A exportação CSV/PDF anunciada em outro plano não estabelece
  por si só o contrato de ingestão automatizada necessário.
- [Termos oficiais](https://www.leilaoindex.com.br/termos), versão indicada de
  13/08/2026: §4 veda contornar limites, extração automatizada em massa e revenda de
  acesso; §5 vincula recursos e limites aos planos; §3 ressalva atualização e
  disponibilidade. O texto examinado não concede expressamente armazenamento,
  republicação em outro agregador ou retenção do histórico próprio de observações.
  Isso não permite concluir que a coleta limitada a quatro anúncios seja
  expressamente proibida: o limite de massa não está definido. Também não comprova
  que esse uso esteja permitido.
- A [FAQ oficial](https://www.leilaoindex.com.br/) informa atualização diária e
  inativação de ofertas que saem da base. São comportamentos do produto, sem
  contrato publicado para notificações ou respostas da futura API. A mesma FAQ
  identifica a CAIXA como origem de imóveis, valores e datas. Compartilhar essa
  proveniência com ILB é limitação de interpretação, sem desqualificar por si só
  a candidata como outro canal.

## Uso exigido pelo Placecheck

Receber e guardar campos numéricos e URLs originais; exibir comparação; manter
histórico dos preços observados pelo Placecheck; atualizar e retirar ofertas.
Nenhuma dessas permissões foi comprovada para integração externa pelos documentos
acima. Fotos, descrições, notas proprietárias e contatos não são necessários.
Cobrança ou chave de acesso também não seriam, isoladamente, impedimentos.

## Dependência externa concreta

Para retomar esta candidata, precisa existir uma API/feed efetivamente oferecido,
com documentação de acesso e termos gerais que cubram esse uso. Termos públicos
suficientes dispensam aprovação individual ou contrato negociado. Até lá, não há
base para criar provider ou buscar anúncios. Após resolver acesso e permissão,
ainda será necessário verificar dados reais limitados aos mercados e identidade
de imóveis compartilhados com ILB; essa sobreposição não foi testada.

## Limites da verificação

A página inicial abriu na ferramenta web; o texto completo dos termos veio do
resultado indexado do próprio domínio (rastreado no mês anterior). A abertura
direta de `/termos` falhou com cache miss. `/robots.txt` não pôde ser aberto;
não se presume autorização de crawler. A tentativa de leitura HTTP local também
falhou na resolução DNS. Nenhum endpoint privado foi sondado. Este documento
registra a evidência observada, não uma confirmação de disponibilidade da API.
