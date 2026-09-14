#!/usr/bin/env python3
"""
Diagnóstico rápido pro erro "SpreadsheetNotFound" ao abrir "checkpoints-999ze": lista TODAS as
planilhas que a conta de serviço do bot (creds.json) enxerga no Google Drive, com o nome exato de
cada uma. Se "checkpoints-999ze" não aparecer nessa lista, o problema não é o nome — é que essa
conta de serviço não tem acesso ao arquivo (mais comum quando ele foi renomeado por meio de
"Arquivo > Fazer uma cópia" em vez de um rename de verdade: uma cópia nova não herda o
compartilhamento do arquivo original).

Uso:
    cd at
    source eleicoes-bot/venv/bin/activate
    python3 scripts/listar_planilhas_do_bot.py
"""
import json
import pathlib
import sys

import gspread

REPO = pathlib.Path(__file__).resolve().parent.parent
CREDS = REPO / "eleicoes-bot" / "creds.json"


def main():
    if not CREDS.exists():
        sys.exit(f"Não encontrei {CREDS} — rode este script na mesma máquina/pasta onde está o bot.")

    # pega o e-mail direto do arquivo de credencial (mais confiável do que inspecionar o objeto
    # gspread.Client, cujos atributos internos mudam entre versões da lib)
    email_servico = json.loads(CREDS.read_text(encoding="utf-8")).get("client_email", "(não encontrado no creds.json)")
    print(f"Conta de serviço usada: {email_servico}\n")

    gc = gspread.service_account(filename=str(CREDS))

    planilhas = gc.list_spreadsheet_files()
    if not planilhas:
        print("❌ Essa conta de serviço não enxerga NENHUMA planilha no Drive.")
        print("   Isso confirma que o compartilhamento se perdeu — abra a planilha certa no Google")
        print("   Sheets, clique em 'Compartilhar' e adicione o e-mail da conta de serviço acima")
        print("   como Editor.")
        return

    print(f"Planilhas visíveis para essa conta de serviço ({len(planilhas)}):")
    for p in planilhas:
        marcador = "  👉" if "checkpoints" in p["name"].lower() else "    "
        print(f"{marcador} {p['name']!r}  (id: {p['id']})")

    nomes = [p["name"] for p in planilhas]
    if "checkpoints-999ze" not in nomes:
        print("\n❌ 'checkpoints-999ze' NÃO está nessa lista — por isso o .open() falha.")
        print("   Prováveis causas:")
        print("   1) Foi feita uma CÓPIA (Arquivo > Fazer uma cópia) em vez de renomear a original —")
        print("      a cópia é um arquivo novo e não herda o compartilhamento. Abra a planilha certa,")
        print(f"      clique em 'Compartilhar' e adicione {email_servico} como Editor.")
        print("   2) O nome tem uma diferença sutil (espaço extra, maiúscula, acento) — compare com")
        print("      a lista acima, letra por letra.")
    else:
        print("\n✅ 'checkpoints-999ze' está na lista — o nome e o compartilhamento estão OK.")
        print("   Se mesmo assim o erro persistir, pode ser propagação lenta do Drive após o rename —")
        print("   espera 1-2 min e roda de novo.")


if __name__ == "__main__":
    main()
