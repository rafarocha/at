#!/usr/bin/env python3
"""
Ajusta a aba "rondas" da planilha real (checkpoints-999ze) pro novo esquema de 9 colunas
(com tempo_espera_min e atividades, usadas pelo checklist R01-R05 do bot).

NAO apaga nenhuma linha existente -- nem os testes semeados por seed_demo_sheet.py, nem
entradas reais que voce ja tenha confirmado pelo celular. Ele so insere 2 colunas novas
("tempo_espera_min" e "atividades") logo depois de "bateria_ok", deixando em branco o
valor dessas colunas para as linhas que ja existiam (afinal, essa informacao nao existia
ainda quando elas foram gravadas). Todo o resto da linha (fila, votados, observacao,
confirmado_por) continua na mesma linha, so desloca de coluna.

Rode isso UMA VEZ, no mesmo terminal/venv onde voce ja roda o bot.py (esse script usa o
mesmo creds.json). Se a aba ja estiver no formato novo, ele avisa e nao faz nada -- pode
rodar de novo sem medo.

Uso:
    cd at            # a raiz do repositorio
    python3 scripts/ajustar_esquema_rondas.py
"""
import pathlib
import sys

import gspread

REPO = pathlib.Path(__file__).resolve().parent.parent
CREDS = REPO / "eleicoes-bot" / "creds.json"
PLANILHA_NOME = "checkpoints-999ze"

NOVAS_COLUNAS = ["tempo_espera_min", "atividades"]


def main():
    if not CREDS.exists():
        sys.exit(f"Nao encontrei {CREDS} -- rode este script na mesma maquina/pasta onde esta o bot.")

    sh = gspread.service_account(filename=str(CREDS)).open(PLANILHA_NOME)
    ws = sh.worksheet("rondas")

    header = ws.row_values(1)
    print("Cabecalho atual:", header)

    if "tempo_espera_min" in header and "atividades" in header:
        print("OK: a aba 'rondas' ja esta no formato novo (9 colunas). Nada a fazer.")
        return

    if "bateria_ok" not in header:
        sys.exit(
            "Nao encontrei a coluna 'bateria_ok' no cabecalho -- o formato da aba e "
            "diferente do esperado. Ajuste manualmente ou avise para eu conferir."
        )

    todas_as_linhas = ws.get_all_values()
    total_linhas = len(todas_as_linhas)
    idx_bateria = header.index("bateria_ok")  # 0-based
    posicao_insercao = idx_bateria + 2  # 1-based, logo depois de bateria_ok

    print(f"Inserindo colunas {NOVAS_COLUNAS} na posicao {posicao_insercao} "
          f"(logo apos 'bateria_ok'), preservando as {total_linhas - 1} linhas existentes...")

    coluna_tempo = ["tempo_espera_min"] + [""] * (total_linhas - 1)
    coluna_atividades = ["atividades"] + [""] * (total_linhas - 1)

    ws.insert_cols([coluna_tempo, coluna_atividades], posicao_insercao)

    print("OK: pronto. Novo cabecalho:", ws.row_values(1))
    print("As linhas antigas ficaram com 'tempo_espera_min' e 'atividades' em branco -- "
          "e esperado, porque essa informacao so passa a ser coletada a partir de agora, "
          "com o checklist R01-R05 do bot.")


if __name__ == "__main__":
    main()
