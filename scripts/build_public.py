#!/usr/bin/env python3
"""
Gera tudo que fica em public/ (site do GitHub Pages) e em teste-local/,
a partir de:
  - html-mockups/index.html, secao.html, painel.html   (código-fonte real)
  - scripts/dados/<cenario>/{checkpoints,rondas,ocorrencias}.csv  (dados fictícios, usados nos samples)

Todas as páginas geradas (samples, demo e teste-local) são os templates REAIS de
html-mockups/ fazendo fetch() de verdade — a única coisa que muda entre elas é de
onde vem o CSV_URL_* (um arquivo .csv publicado ao lado da própria página, ou a URL
real da planilha do Google) e se o relógio (nowMinutes()) fica congelado num horário
fixo (samples, pra "fotografia" do cenário não mudar) ou correndo em tempo real (demo).

A URL da planilha publicada como CSV ("Publicar na Web") é só de LEITURA — o Google não
permite editar a planilha por ela, só ler. Quem edita é o bot (eleicoes-bot/bot.py), por
uma credencial de serviço completamente separada (creds.json, nunca commitada). Por isso
não tem problema publicar o link de leitura junto com o site.

Rode isto sempre que mexer em html-mockups/ ou em scripts/dados/ e quiser
que public/ e teste-local/ reflitam a mudança:

    python3 scripts/build_public.py

Isso é exatamente o que o workflow do GitHub Actions (.github/workflows/pages.yml)
roda sozinho antes de publicar — então rodar isso manualmente é só para
conferir localmente antes de dar push.
"""
import os
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATES = REPO / "html-mockups"
DADOS = REPO / "scripts" / "dados"
PUBLIC = REPO / "public"
TESTE_LOCAL = REPO / "teste-local"

# título original (como está em html-mockups/*.html) de cada página — usado para localizar
# e trocar pelo título "com tag" (ex.: "[Exemplo] ...", "[Ao Vivo] ...") em cada saída
TITULOS_ORIGINAIS = {
    "index.html": "🛰️ Visão Geral — Mapa &amp; Indicadores em Tempo Real",
    "secao.html": "🔍 Detalhe por Seção — Indicadores em Tempo Real",
    "painel.html": "🛰️ Painel — Mapa de Atividades em Tempo Real",
}

# cada cenário fictício: pasta de dados (em scripts/dados/), pasta de saída (em public/samples/),
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


def freeze_now(html, now_min):
    """Substitui a função nowMinutes() (que lê o relógio real) por uma que sempre devolve o
    mesmo horário — usado só nos samples fictícios, pra a "fotografia" do cenário não mudar
    dependendo de quando alguém abre a página."""
    return re.sub(
        r'function nowMinutes\(\) \{\s*const d = new Date\(\);\s*return d\.getHours\(\) \* 60 \+ d\.getMinutes\(\);\s*\}',
        f'function nowMinutes() {{ return {now_min}; }}',
        html,
    )


def escrever_pagina(fname, saida_dir, csv_checkpoints, csv_ocorrencias, csv_rondas,
                     titulo_novo, freeze_min=None):
    """Copia um template real de html-mockups/<fname>, aponta CSV_URL_* pros valores dados
    (uma URL do Google, ou o nome de um .csv publicado ao lado da própria página), troca o
    título da aba e, se freeze_min for informado, congela o relógio nesse horário."""
    html = (TEMPLATES / fname).read_text(encoding="utf-8")
    html = html.replace('CSV_URL_CHECKPOINTS = "COLE_AQUI_O_LINK_CSV_DA_ABA_CHECKPOINTS"',
                         f'CSV_URL_CHECKPOINTS = "{csv_checkpoints}"')
    html = html.replace('CSV_URL_OCORRENCIAS = "COLE_AQUI_O_LINK_CSV_DA_ABA_OCORRENCIAS"',
                         f'CSV_URL_OCORRENCIAS = "{csv_ocorrencias}"')
    html = html.replace('CSV_URL_RONDAS = "COLE_AQUI_O_LINK_CSV_DA_ABA_RONDAS"',
                         f'CSV_URL_RONDAS = "{csv_rondas}"')
    html = html.replace(f"<title>{TITULOS_ORIGINAIS[fname]}</title>", f"<title>{titulo_novo}</title>")
    if freeze_min is not None:
        html = freeze_now(html, freeze_min)

    saida_dir.mkdir(parents=True, exist_ok=True)
    out = saida_dir / fname
    out.write_text(html, encoding="utf-8")
    print("  escrito:", out.relative_to(REPO))


def build_cenario(dados_dir, saida_dir, now_min, titulo):
    """Um sample fictício: os templates reais fazendo fetch() de verdade nos 3 CSVs copiados
    para dentro da própria pasta de saída (mesmo mecanismo do teste-local/, só que publicado
    em public/samples/), com o relógio congelado no horário do cenário."""
    novos_titulos = {
        "index.html": f"🛰️ [Exemplo] Visão Geral — {titulo}",
        "secao.html": f"🔍 [Exemplo] Detalhe por Seção — {titulo}",
        "painel.html": f"📊 [Exemplo] Painel Gestor — {titulo}",
    }
    for fname in ("index.html", "secao.html", "painel.html"):
        escrever_pagina(fname, saida_dir, "checkpoints.csv", "ocorrencias.csv", "rondas.csv",
                         novos_titulos[fname], freeze_min=now_min)
    for csvname in ("checkpoints.csv", "rondas.csv", "ocorrencias.csv"):
        shutil.copyfile(dados_dir / csvname, saida_dir / csvname)
        print("  copiado:", (saida_dir / csvname).relative_to(REPO))


def build_demo():
    """public/demo/ — a versão real, conectada à planilha ao vivo (fetch() de verdade, relógio
    correndo normal). Os 3 CSV_URL_* vêm de variáveis de ambiente — o workflow do GitHub Actions
    injeta a partir de Settings → Secrets and variables → Actions → Variables do repositório
    (veja html-howto/publicar.html). Sem essas variáveis configuradas, sai com o placeholder de
    sempre (a própria página avisa que falta configurar)."""
    saida = PUBLIC / "demo"
    url_checkpoints = os.environ.get("CSV_URL_CHECKPOINTS", "").strip() or "COLE_AQUI_O_LINK_CSV_DA_ABA_CHECKPOINTS"
    url_ocorrencias = os.environ.get("CSV_URL_OCORRENCIAS", "").strip() or "COLE_AQUI_O_LINK_CSV_DA_ABA_OCORRENCIAS"
    url_rondas = os.environ.get("CSV_URL_RONDAS", "").strip() or "COLE_AQUI_O_LINK_CSV_DA_ABA_RONDAS"

    novos_titulos = {
        "index.html": "🛰️ [Ao Vivo] Visão Geral — 999ª ZE",
        "secao.html": "🔍 [Ao Vivo] Detalhe por Seção — 999ª ZE",
        "painel.html": "📊 [Ao Vivo] Painel Gestor — 999ª ZE",
    }
    for fname in ("index.html", "secao.html", "painel.html"):
        escrever_pagina(fname, saida, url_checkpoints, url_ocorrencias, url_rondas, novos_titulos[fname])

    if url_checkpoints.startswith("COLE_AQUI"):
        print("  aviso: variáveis CSV_URL_* não configuradas nos secrets/variables do repositório — "
              "public/demo/ ficou com o placeholder de sempre (a página vai pedir configuração).")


def build_teste_local(dados_dir):
    """teste-local/ — mesma ideia de build_cenario, mas sem congelar o relógio (serve pra testar
    o refresh de 30s de verdade enquanto você edita os CSVs à mão), e fora de public/ — não é
    publicado no GitHub Pages, só para você rodar localmente."""
    novos_titulos = {
        "index.html": "🛰️ [Teste Local] Visão Geral",
        "secao.html": "🔍 [Teste Local] Detalhe por Seção",
        "painel.html": "📊 [Teste Local] Painel Gestor",
    }
    for fname in ("index.html", "secao.html", "painel.html"):
        escrever_pagina(fname, TESTE_LOCAL, "checkpoints.csv", "ocorrencias.csv", "rondas.csv",
                         novos_titulos[fname])
    for csvname in ("checkpoints.csv", "rondas.csv", "ocorrencias.csv"):
        shutil.copyfile(dados_dir / csvname, TESTE_LOCAL / csvname)
        print("  copiado:", (TESTE_LOCAL / csvname).relative_to(REPO))


def main():
    print("Construindo public/samples/ ...")
    for c in CENARIOS:
        print(f"- {c['dados']}")
        build_cenario(DADOS / c["dados"], c["saida"], c["now_min"], c["titulo"])

    print("Construindo public/demo/ (conectado à planilha real, via variáveis de ambiente) ...")
    build_demo()

    print("Construindo teste-local/ ...")
    build_teste_local(DADOS / "sample-1-otimista")

    print("Pronto.")


if __name__ == "__main__":
    main()
