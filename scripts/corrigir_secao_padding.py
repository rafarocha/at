#!/usr/bin/env python3
"""
Corrige um efeito colateral do seed_demo_sheet.py antigo: ele subia as linhas com
value_input_option="USER_ENTERED", e o Google Sheets interpreta isso como se você tivesse
digitado o valor na célula — então "01" virou o número 1 (zero à esquerda cortado) nas colunas
"secao" das abas checkpoints, rondas e ocorrencias. O problema é só de formatação: o código das
páginas (index/secao/painel.html) sempre procura a seção pelo texto com 2 dígitos (ex. "01"), então
uma seção gravada como "1" nunca é encontrada — a seção aparece com todos os aspectos zerados/sem
dados, mesmo já tendo confirmações ou rondas na planilha.

Esse comportamento já foi corrigido no seed_demo_sheet.py (agora usa value_input_option="RAW",
que não sofre essa conversão). Este script aqui só arruma o que JÁ está gravado na planilha,
reescrevendo a coluna "secao" de cada aba com o texto de 2 dígitos, sem apagar ou mexer em mais
nenhuma coluna/linha (inclusive edições manuais que você já tenha feito continuam intactas).

Uso:
    cd at
    source eleicoes-bot/venv/bin/activate
    python3 scripts/corrigir_secao_padding.py
"""
import pathlib
import sys

import gspread

REPO = pathlib.Path(__file__).resolve().parent.parent
CREDS = REPO / "eleicoes-bot" / "creds.json"
PLANILHA_NOME = "checkpoints-999ze"

ABAS = ["checkpoints", "rondas", "ocorrencias"]


def corrigir_aba(ws, nome_aba):
    valores = ws.get_all_values()
    if not valores:
        print(f"  {nome_aba}: aba vazia, nada a fazer.")
        return
    header = valores[0]
    if "secao" not in header:
        print(f"  {nome_aba}: não tem coluna 'secao', pulando.")
        return
    idx = header.index("secao")  # 0-based

    atualizacoes = []
    for i, linha in enumerate(valores[1:], start=2):  # linha 1 é o cabeçalho
        if idx >= len(linha):
            continue
        valor = linha[idx].strip()
        if not valor:
            continue  # G01-G11 (gerais) não têm seção — correto ficar em branco
        if valor.isdigit() and len(valor) < 2:
            novo = valor.zfill(2)
            atualizacoes.append((i, novo, valor))

    if not atualizacoes:
        print(f"  {nome_aba}: nenhuma célula precisando de correção (já ok, ou aba não tem esse problema).")
        return

    col_letra = gspread.utils.rowcol_to_a1(1, idx + 1)[:-1]  # letra da coluna, ex. "A"
    print(f"  {nome_aba}: corrigindo {len(atualizacoes)} célula(s) na coluna {col_letra} ('secao')...")
    celulas = []
    for linha, novo, antigo in atualizacoes:
        c = gspread.cell.Cell(row=linha, col=idx + 1, value=novo)
        celulas.append(c)
    ws.update_cells(celulas, value_input_option="RAW")
    print(f"  {nome_aba}: pronto.")


def main():
    if not CREDS.exists():
        sys.exit(f"Não encontrei {CREDS} — rode este script na mesma máquina/pasta onde está o bot.")

    planilha = gspread.service_account(filename=str(CREDS)).open(PLANILHA_NOME)
    for nome_aba in ABAS:
        ws = planilha.worksheet(nome_aba)
        corrigir_aba(ws, nome_aba)

    print("Pronto. Dá uma conferida na planilha e depois recarrega o public/demo/ "
          "(o link publicado do Google pode levar alguns minutos para refletir a mudança).")


if __name__ == "__main__":
    main()
