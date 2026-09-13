# Sample 3 · Pessimista — 13:30

Continuação do cenário pessimista (veja também 10:30 e 16:30): agora no **meio do dia**, os
mesmos tipos de problema de cada seção pioraram — filas maiores, mais ocorrências abertas, e o
comparecimento continua muito abaixo do esperado para o horário.

Abra `index.html` primeiro (duplo clique — só os 3 gráficos da home precisam de internet; o resto
funciona offline). Depois `secao.html` e `painel.html`.

## O que foi semeado

Mesmo mapa de seção → tipo de problema do sample 10:30, com severidade maior:

| Seções | Tipo de problema |
|---|---|
| 01, 09 | Fila grande, já bem maior que de manhã |
| 02, 10 | Urna com problema técnico persistente |
| 03, 11 | Energia/bateria — segunda ocorrência do dia |
| 04, 12 | Confusão/segurança mais séria, PM acionada preventivamente |
| 05, 13 | Tarefas do administrador acumulando, poucas confirmadas |
| 06, 14 | Seção sem contato há mais de uma ronda |
| 07, 15 | Votação continua muito lenta, causa ainda não identificada |
| 08 | Combo: fila grande + administrador não localizado |
| 16 | Combo: urna parada + votação parada há tempo |

Comparecimento médio: ~29% (bem abaixo do esperado para 13:30). 14 ocorrências abertas — a maioria
segue sem solução desde a manhã.

## Arquivos

- `index.html`, `secao.html`, `painel.html` — autocontidos, dados já embutidos.
- `checkpoints.csv`, `rondas.csv`, `ocorrencias.csv` — dados brutos.
