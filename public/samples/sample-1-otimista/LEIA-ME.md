# Sample 1 · "Otimista" — exercício de leitura de painel

Este é um pacote de **dados de demonstração**, totalmente fictícios e aleatórios, para treinar
administradores e supervisores a lerem os painéis da 150ª ZE antes do dia da eleição de verdade.
Nenhum dos nomes, horários ou números aqui é real.

## Como usar com o grupo

1. Abra os 3 arquivos com as pessoas que vão analisar (dê a cada uma um notebook ou celular, ou
   projete na tela): **`index.html`** primeiro, depois **`secao.html`** e **`painel.html`** — os
   três já vêm com os dados fixos embutidos, então basta dar duplo clique para abrir (funciona
   offline, exceto pelos gráficos, que carregam uma biblioteca (D3) da internet — se não houver
   internet no momento do treino, os 3 gráficos da home não aparecem, mas o resto funciona normalmente).
2. Peça para o grupo responder, só olhando os painéis (sem ler o `GABARITO.md` ainda):
   - "Na sua opinião, está tudo bem neste local de votação agora, às 16:12?"
   - "Se você tivesse que agir em cima de UMA coisa agora mesmo, qual seria?"
3. Depois da discussão, abra o `GABARITO.md` com o grupo e compare com o que eles encontraram.

## O que este cenário tenta ensinar

a leitura rápida por cima passa a impressão de que está tudo indo bem: 100% das tarefas do
administrador concluídas, quase todas as seções em verde, comparecimento médio de ~85%, e nenhuma
ocorrência formal grave registrada. É fácil bater o olho, ver "15 de 16 seções em dia" e seguir em
frente.

O problema real está escondido dentro dos números de **uma única seção**, que só aparece se você
olhar linha por linha ou abrir o detalhe dela — e é exatamente esse hábito (checar cada seção, não
só o resumo) que este exercício quer treinar.

Arquivos incluídos:
- `index.html`, `secao.html`, `painel.html` — as 3 páginas do painel, com os dados deste cenário
  já embutidos (não precisam de planilha nem de CSV publicado).
- `checkpoints.csv`, `rondas.csv`, `ocorrencias.csv` — os mesmos dados "crus", caso queira carregar
  numa cópia real do painel (editando `CSV_URL_CHECKPOINTS` etc. para apontar pra esses arquivos
  publicados, ou usar como massa de teste ao configurar sua própria planilha).
- `GABARITO.md` — a resposta comentada (não abra antes de discutir com o grupo).
