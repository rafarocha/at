#!/usr/bin/env python3
"""
Sobe scripts/seed_demo/{checkpoints,ocorrencias,rondas}.csv pra planilha REAL (checkpoints-150ze)
— um preenchimento breve (até por volta das 10:30, todas as 16 seções, mistura de boas/médias/
ruins) só para você conseguir testar o /start pelo celular e ver o public/demo/ com alguma coisa
na tela, em vez de tudo vazio.

Usa a mesma credencial do bot (eleicoes-bot/creds.json) — rode com o venv do bot já ativo:

    cd eleicoes-bot
    source venv/bin/activate
    python3 ../scripts/seed_demo_sheet.py

Isso ACRESCENTA linhas nas 3 abas (append) — nunca apaga o que já estiver lá. Rodar duas vezes
duplica as linhas de teste; se quiser recomeçar do zero, apague as linhas de teste manualmente na
planilha antes de rodar de novo (mantendo a linha de cabeçalho).

Para gerar (ou regenerar, com outra mistura) os CSVs de novo antes de subir, rode primeiro:
    python3 scripts/gerar_seed_demo.py
"""
import csv
import pathlib
import sys

try:
    import gspread
except ImportError:
    sys.exit("gspread não encontrado — rode isto com o venv do bot ativo (veja o cabeçalho deste arquivo).")

REPO = pathlib.Path(__file__).resolve().parent.parent
SEED_DIR = REPO / "scripts" / "seed_demo"
PLANILHA_NOME = "checkpoints-150ze"
CREDS = REPO / "eleicoes-bot" / "creds.json"

ABAS = [("checkpoints", "checkpoints.csv"), ("ocorrencias", "ocorrencias.csv"), ("rondas", "rondas.csv")]


def ler_csv(caminho):
    with open(caminho, newline="", encoding="utf-8") as f:
        linhas = list(csv.reader(f))
    return linhas[0], linhas[1:]


def main():
    if not CREDS.exists():
        sys.exit(f"Não encontrei {CREDS} — rode isto na mesma máquina onde o bot está configurado.")

    planilha = gspread.service_account(filename=str(CREDS)).open(PLANILHA_NOME)

    for aba, arquivo in ABAS:
        cabecalho, linhas = ler_csv(SEED_DIR / arquivo)
        ws = planilha.worksheet(aba)
        existentes = ws.get_all_values()
        if not existentes:
            ws.append_row(cabecalho)
        ws.append_rows(linhas, value_input_option="USER_ENTERED")
        print(f"  {aba}: +{len(linhas)} linhas (total agora: {len(existentes) + len(linhas) + (0 if existentes else 1)})")

    print("Pronto — confira a planilha e depois public/demo/ (pode levar até 30s pra aparecer).")


if __name__ == "__main__":
    main()
