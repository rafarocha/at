# Sample 2 · Pessimista — 10:30

Dados de demonstração, totalmente fictícios e aleatórios, retratando uma **manhã já em crise** —
"início pessimista": o dia começa mal e, sem ação, só piora (veja também os samples 13:30 e 16:30).

Abra `index.html` primeiro (funciona com duplo clique — os 3 gráficos da home só carregam com
internet, pois usam uma biblioteca externa; o resto funciona 100% offline). Depois explore
`secao.html` (qualquer seção) e `painel.html`.

## O que foi semeado

Todas as 16 seções têm pelo menos um problema em aberto às 10:30 — a ideia é treinar o olho para
reconhecer **tipos diferentes** de problema, não só "muita gente na fila":

| Seções | Tipo de problema |
|---|---|
| 01, 09 | Fila grande se formando cedo |
| 02, 10 | Urna com problema técnico (reiniciando) |
| 03, 11 | Energia/bateria oscilando |
| 04, 12 | Início de confusão/segurança na fila |
| 05, 13 | Tarefas do administrador atrasadas |
| 06, 14 | Ronda sem confirmação recente (equipe some) |
| 07, 15 | Votação com ritmo muito lento |
| 08 | Combo: fila grande + sem administrador confirmando tarefas |
| 16 | Combo: urna com problema + votação parada |

Comparecimento médio da manhã: ~20% (bem abaixo do normal para o horário). 8 ocorrências abertas
registradas — nenhuma delas ainda resolvida a essa hora.

## Arquivos

- `index.html`, `secao.html`, `painel.html` — autocontidos, dados já embutidos.
- `checkpoints.csv`, `rondas.csv`, `ocorrencias.csv` — dados brutos, caso queira reaproveitar como
  massa de teste numa cópia real do painel.
