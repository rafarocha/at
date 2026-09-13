# Sample 4 · Pessimista — 16:30

Última etapa do cenário pessimista (veja também 10:30 e 13:30): faltando pouco mais de meia hora
para o encerramento (17h), a situação está crítica em todas as 16 seções, com filas grandes,
comparecimento muito baixo e várias seções sem contato recente.

Abra `index.html` primeiro, de preferência pelo link publicado no GitHub Pages (dados fixos deste cenário, não mudam com o horário real). Testando localmente antes de publicar? Estas páginas leem um CSV pela mesma pasta — dar duplo clique não funciona, sirva a pasta com `python3 -m http.server` (veja o `README.md` na raiz do repositório). Depois explore `secao.html` (qualquer seção) e `painel.html`.

## O que foi semeado

Mesmo mapa de seção → tipo de problema dos samples anteriores, na severidade máxima:

| Seções | Tipo de problema |
|---|---|
| 01, 09 | Fila grande — 37 e 39 pessoas, respectivamente, a menos de 1h do fechamento |
| 02, 10 | Urna parada, votação suspensa aguardando substituição |
| 03, 11 | Sem energia há mais de 20 minutos, urna no limite da bateria |
| 04, 12 | Confusão generalizada / tensão na fila, PM já no local |
| 05, 13 | Diversas tarefas do administrador ainda não confirmadas |
| 06, 14 | Seção sem contato há várias rondas — ninguém sabe o que está havendo lá |
| 07, 15 | Votação praticamente parada, eleitores desistindo da fila |
| 08 | Combo: fila grande + administrador não localizado desde a tarde |
| 16 | Combo: urna parada + votação parada por tempo prolongado |

Comparecimento médio: ~38% — com o horário de encerramento perto, é matematicamente pouco provável
que todas as seções consigam atender quem ainda está na fila sem uma ação imediata (reforço de
equipe, troca de equipamento, ou organização de senhas para quem já está na fila antes das 17h).
18 ocorrências abertas — nenhuma seção ficou de fora.

## Arquivos

- `index.html`, `secao.html`, `painel.html` — autocontidos, dados já embutidos.
- `checkpoints.csv`, `rondas.csv`, `ocorrencias.csv` — dados brutos.

## Sugestão de uso com os 3 samples juntos

Mostre os 3 (10:30 → 13:30 → 16:30) em sequência para o grupo e pergunte, a cada etapa: "o que
vocês fariam agora, com a informação que têm nesse momento?" — a ideia é treinar decisões sob
pressão crescente, e discutir o que poderia ter sido feito mais cedo (por exemplo: um leitor
biométrico lento reportado às 10:30 como "resolvido" continua sendo o mesmo problema, sem resolução
real, às 16:30).
