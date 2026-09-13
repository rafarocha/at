#!/usr/bin/env python3
"""
Gera tudo que fica em public/ (site do GitHub Pages) e em teste-local/,
a partir de:
  - html-mockups/index.html, secao.html, painel.html   (código-fonte real)
  - scripts/dados/<cenario>/{checkpoints,rondas,ocorrencias}.csv  (dados fictícios)

Rode isto sempre que mexer em html-mockups/ ou em scripts/dados/ e quiser
que public/ e teste-local/ reflitam a mudança:

    python3 scripts/build_public.py

Isso é exatamente o que o workflow do GitHub Actions (.github/workflows/pages.yml)
roda sozinho antes de publicar — então rodar isso manualmente é só para
conferir localmente antes de dar push.
"""
import csv
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATES = REPO / "html-mockups"
DADOS = REPO / "scripts" / "dados"
PUBLIC = REPO / "public"
TESTE_LOCAL = REPO / "teste-local"

SRC_INDEX = TEMPLATES / "index.html"
SRC_SECAO = TEMPLATES / "secao.html"
SRC_PAINEL = TEMPLATES / "painel.html"

# cada cenário: pasta de dados (em scripts/dados/), pasta de saída (em public/samples/),
# horário congelado (minutos desde 00:00) e título mostrado na aba do navegador
CENARIOS = [
    {"dados": "sample-1-otimista", "saida": PUBLIC / "samples" / "sample-1-otimista",
     "now_min": 972, "titulo": "Sample 1 · Otimista 16:12"},
    {"dados": "sample-2-pessimista-1030", "saida": PUBLIC / "samples" / "sample-2-pessimista-1030",
     "now_min": 630, "titulo": "Sample 2 · Pessimista 10:30"},
    {"dados": "sample-3-pessimista-1330", "saida": PUBLIC / "samples" / "sample-3-pessimista-1330",
     "now_min": 810, "titulo": "Sample 3 · Pessimista 13:30"},
    {"dados": "sample-4-pessimista-1630", "saida": PUBLIC / "samples" / "sample-4-pessimista-1630",
     "now_min": 990, "titulo": "Sample 4 · Pessimista 16:30"},
]

# a demonstração pública ("o atual em uso", pra teste de navegação) reaproveita
# os dados do cenário otimista (é o mais "normal", sem crise nenhuma)
DEMO = {"dados": "sample-1-otimista", "saida": PUBLIC / "demo", "now_min": 972}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def freeze_now(js, now_min):
    js2 = js.replace(
        'function nowMinutes() { const d = new Date(); return d.getHours() * 60 + d.getMinutes(); }',
        f'function nowMinutes() {{ return {now_min}; }}'
    )
    js2 = re.sub(
        r'function nowMinutes\(\) \{\s*const d = new Date\(\);\s*return d\.getHours\(\) \* 60 \+ d\.getMinutes\(\);\s*\}',
        f'function nowMinutes() {{ return {now_min}; }}',
        js2
    )
    return js2


def mock_block(checkpoints_json, ocorrencias_json, rondas_json, last_sync_msg, com_rondas=True):
    rondas_linhas = (
        f'  const MOCK_RONDAS = {rondas_json};\n'
        if com_rondas else ''
    )
    indexar_rondas = '    indexarRondasNumericas(MOCK_RONDAS);\n' if com_rondas else ''
    all_occ = '    allOcorrenciaRows = MOCK_OCORRENCIAS;\n' if com_rondas else ''
    return f"""
  // ===================== DADOS DE EXEMPLO (fixos, gerados por scripts/build_public.py) =====================
  const MOCK_CHECKPOINTS = {checkpoints_json};
  const MOCK_OCORRENCIAS = {ocorrencias_json};
{rondas_linhas}
  function atualizarExemplo() {{
    indexarCheckpoints(MOCK_CHECKPOINTS);
{indexar_rondas}    ocorrencias = MOCK_OCORRENCIAS;
{all_occ}    if (typeof ocorrenciasHabilitadas !== "undefined") ocorrenciasHabilitadas = true;
    document.getElementById("errorBanner").style.display = "none";
    document.getElementById("lastSync").textContent = "{last_sync_msg}";
    render();
  }}
"""


def bake(path_in, path_out, checkpoints_json, ocorrencias_json, rondas_json, now_min,
         last_sync_msg, title_old, title_new, com_rondas=True):
    html = path_in.read_text(encoding="utf-8")

    block = mock_block(checkpoints_json, ocorrencias_json, rondas_json, last_sync_msg, com_rondas)
    marker = ("  // --------------------------------------------------------------- carregamento\n"
               "  async function atualizar(manual) {")
    assert marker in html, f"marker de carregamento não encontrado em {path_in}"
    html = html.replace(marker, block + "\n" + marker)

    old_boot = """  atualizar(false);
  setInterval(() => atualizar(false), REFRESH_MS);
  setInterval(() => { document.getElementById("clockDisplay").textContent = "🕐 " + fmt(nowMinutes()); }, 15000);
})();"""
    new_boot = """  atualizarExemplo();
})();"""
    assert old_boot in html, f"bloco de boot não encontrado em {path_in}"
    html = html.replace(old_boot, new_boot)

    html = freeze_now(html, now_min)
    if title_old and title_new:
        html = html.replace(title_old, title_new)

    path_out.parent.mkdir(parents=True, exist_ok=True)
    path_out.write_text(html, encoding="utf-8")
    print("  escrito:", path_out.relative_to(REPO))


def build_cenario(dados_dir, saida_dir, now_min, titulo):
    checkpoints = read_csv(dados_dir / "checkpoints.csv")
    rondas = read_csv(dados_dir / "rondas.csv")
    ocorrencias = read_csv(dados_dir / "ocorrencias.csv")

    checkpoints_json = json.dumps(checkpoints, ensure_ascii=False)
    rondas_json = json.dumps(rondas, ensure_ascii=False)
    ocorrencias_json = json.dumps(ocorrencias, ensure_ascii=False)

    label = f'{now_min // 60:02d}:{now_min % 60:02d}'
    last_sync_msg = (f'Dados de exemplo (fixos) — cenário \\"{titulo}\\", congelado às {label}. '
                      f'Não faz nenhuma requisição de rede.')

    bake(SRC_INDEX, saida_dir / "index.html", checkpoints_json, ocorrencias_json, rondas_json, now_min,
         last_sync_msg,
         "<title>🛰️ Visão Geral — Mapa &amp; Indicadores em Tempo Real</title>",
         f"<title>🛰️ [Exemplo] Visão Geral — {titulo}</title>")
    bake(SRC_SECAO, saida_dir / "secao.html", checkpoints_json, ocorrencias_json, rondas_json, now_min,
         last_sync_msg,
         "<title>🔍 Detalhe por Seção — Indicadores em Tempo Real</title>",
         f"<title>🔍 [Exemplo] Detalhe por Seção — {titulo}</title>")
    bake(SRC_PAINEL, saida_dir / "painel.html", checkpoints_json, ocorrencias_json, rondas_json, now_min,
         last_sync_msg,
         "<title>🛰️ Painel — Mapa de Atividades em Tempo Real</title>",
         f"<title>📊 [Exemplo] Painel Gestor — {titulo}</title>",
         com_rondas=False)


def build_demo(dados_dir, saida_dir, now_min):
    checkpoints = read_csv(dados_dir / "checkpoints.csv")
    rondas = read_csv(dados_dir / "rondas.csv")
    ocorrencias = read_csv(dados_dir / "ocorrencias.csv")

    checkpoints_json = json.dumps(checkpoints, ensure_ascii=False)
    rondas_json = json.dumps(rondas, ensure_ascii=False)
    ocorrencias_json = json.dumps(ocorrencias, ensure_ascii=False)

    last_sync_msg = ('Página de demonstração (dados fictícios, fixos) — mostra como o sistema fica '
                      'quando conectado à planilha real. Não faz nenhuma requisição de rede.')

    bake(SRC_INDEX, saida_dir / "index.html", checkpoints_json, ocorrencias_json, rondas_json, now_min,
         last_sync_msg,
         "<title>🛰️ Visão Geral — Mapa &amp; Indicadores em Tempo Real</title>",
         "<title>🛰️ [Demonstração] Visão Geral — 150ª ZE</title>")
    bake(SRC_SECAO, saida_dir / "secao.html", checkpoints_json, ocorrencias_json, rondas_json, now_min,
         last_sync_msg,
         "<title>🔍 Detalhe por Seção — Indicadores em Tempo Real</title>",
         "<title>🔍 [Demonstração] Detalhe por Seção — 150ª ZE</title>")
    bake(SRC_PAINEL, saida_dir / "painel.html", checkpoints_json, ocorrencias_json, rondas_json, now_min,
         last_sync_msg,
         "<title>🛰️ Painel — Mapa de Atividades em Tempo Real</title>",
         "<title>📊 [Demonstração] Painel Gestor — 150ª ZE</title>",
         com_rondas=False)


def build_teste_local(dados_dir):
    """Copia os templates reais (sem embutir nada) apontando CSV_URL_* pros 3 CSVs
    locais dessa mesma pasta — pra testar o fluxo real de fetch() sem planilha."""
    TESTE_LOCAL.mkdir(parents=True, exist_ok=True)
    subs = [
        ("index.html", "🛰️ Visão Geral — Mapa &amp; Indicadores em Tempo Real", "🛰️ [Teste Local] Visão Geral"),
        ("secao.html", "🔍 Detalhe por Seção — Indicadores em Tempo Real", "🔍 [Teste Local] Detalhe por Seção"),
        ("painel.html", "🛰️ Painel — Mapa de Atividades em Tempo Real", "📊 [Teste Local] Painel Gestor"),
    ]
    for fname, title_old, title_new in subs:
        html = (TEMPLATES / fname).read_text(encoding="utf-8")
        html = html.replace('CSV_URL_CHECKPOINTS = "COLE_AQUI_O_LINK_CSV_DA_ABA_CHECKPOINTS"',
                             'CSV_URL_CHECKPOINTS = "checkpoints.csv"')
        html = html.replace('CSV_URL_OCORRENCIAS = "COLE_AQUI_O_LINK_CSV_DA_ABA_OCORRENCIAS"',
                             'CSV_URL_OCORRENCIAS = "ocorrencias.csv"')
        html = html.replace('CSV_URL_RONDAS = "COLE_AQUI_O_LINK_CSV_DA_ABA_RONDAS"',
                             'CSV_URL_RONDAS = "rondas.csv"')
        html = html.replace(f"<title>{title_old}</title>", f"<title>{title_new}</title>")
        (TESTE_LOCAL / fname).write_text(html, encoding="utf-8")
        print("  escrito:", (TESTE_LOCAL / fname).relative_to(REPO))

    for csvname in ("checkpoints.csv", "rondas.csv", "ocorrencias.csv"):
        shutil.copyfile(dados_dir / csvname, TESTE_LOCAL / csvname)
        print("  copiado:", (TESTE_LOCAL / csvname).relative_to(REPO))


def main():
    print("Construindo public/samples/ ...")
    for c in CENARIOS:
        print(f"- {c['dados']}")
        build_cenario(DADOS / c["dados"], c["saida"], c["now_min"], c["titulo"])

    print("Construindo public/demo/ ...")
    build_demo(DADOS / DEMO["dados"], DEMO["saida"], DEMO["now_min"])

    print("Construindo teste-local/ ...")
    build_teste_local(DADOS / "sample-1-otimista")

    print("Pronto.")


if __name__ == "__main__":
    main()
