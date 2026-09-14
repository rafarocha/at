#!/usr/bin/env python3
"""
Remove da aba "checkpoints" da planilha real (checkpoints-999ze) as linhas com codigo=="RONDA"
que ficaram la de uma versao anterior do bot/seed (RONDA agora mora so na aba "rondas" -- ver
html-howto/tracking_guide.html). NAO mexe em nenhuma outra linha: tarefas T##/G## ficam
intactas, e a aba "rondas" nem e tocada por este script.

Rode isso UMA VEZ, no mesmo terminal/venv onde voce ja roda o bot.py e o
ajustar_esquema_rondas.py (mesma credencial em eleicoes-bot/creds.json). Se nao houver nenhuma
linha RONDA em checkpoints, ele avisa e nao faz nada -- pode rodar de novo sem medo.

Uso:
    cd at            # a raiz do repositorio
    python3 scripts/limpar_rondas_de_checkpoints.py
"""
import pathlib
import sys

import gspread

REPO = pathlib.Path(__file__).resolve().parent.parent
CREDS = REPO / "eleicoes-bot" / "creds.json"
PLANILHA_NOME = "checkpoints-999ze"


def main():
    if not CREDS.exists():
        sys.exit(f"Nao encontrei {CREDS} -- rode este script na mesma maquina/pasta onde esta o bot.")

    sh = gspread.service_account(filename=str(CREDS)).open(PLANILHA_NOME)
    ws = sh.worksheet("checkpoints")

    valores = ws.get_all_values()
    if not valores:
        print("Aba 'checkpoints' esta vazia. Nada a fazer.")
        return

    header = valores[0]
    if "codigo" not in header:
        sys.exit("Nao encontrei a coluna 'codigo' no cabecalho de 'checkpoints' -- confira manualmente.")
    idx_codigo = header.index("codigo")

    # linhas (1-based, contando o cabecalho como linha 1) onde codigo == "RONDA"
    linhas_ronda = [
        i + 1 for i, row in enumerate(valores)
        if i > 0 and len(row) > idx_codigo and row[idx_codigo].strip() == "RONDA"
    ]

    if not linhas_ronda:
        print("OK: nenhuma linha RONDA encontrada em 'checkpoints'. Nada a fazer.")
        return

    print(f"Encontradas {len(linhas_ronda)} linha(s) com codigo=RONDA em 'checkpoints'. Removendo...")
    # de baixo pra cima, senao os numeros de linha mudam a cada delete
    for linha in sorted(linhas_ronda, reverse=True):
        ws.delete_rows(linha)

    print(f"OK: {len(linhas_ronda)} linha(s) removida(s) de 'checkpoints'. "
          "As tarefas T##/G## e a aba 'rondas' nao foram tocadas.")


if __name__ == "__main__":
    main()
