#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_desempenho.py — Monta a página de desempenho pronta para uso.

Pega o template html-mockups/desempenho.html (com o marcador __DADOS_JSON__ e a
tag <script src="desempenho.js">), injeta:
  - o JSON gerado por parse_logd.py (html-mockups/dados-desempenho.json) no lugar
    do marcador;
  - o conteúdo de html-mockups/desempenho.js inline.

Resultado: um ÚNICO arquivo HTML autossuficiente, que abre por duplo-clique
(sem precisar de servidor, porque não faz fetch()).

Saídas:
  - html-mockups/desempenho.html  (reescrito com dados+JS embutidos — é o que você edita? NÃO:
        edite o template .tmpl + .js; este script regenera o .html)
  - public/desempenho.html        (cópia publicável no GitHub Pages)

Fluxo completo:
  python3 scripts/parse_logd.py logs/zone/150/logd.dat
  python3 scripts/build_desempenho.py
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MOCK = REPO / "html-mockups"
TMPL = MOCK / "desempenho.tmpl.html"
HTML = MOCK / "desempenho.html"
JS = MOCK / "desempenho.js"
JSON_DATA = MOCK / "dados-desempenho.json"
# tudo que é "após a eleição" (desempenho + guias de leitura dos arquivos de urna) fica aqui:
APOS = REPO / "public" / "apos"
PUBLIC = APOS / "desempenho-328.html"   # página padrão (seção 0328)
ZONA_DIR = REPO / "logs" / "zone" / "150"


def secoes_disponiveis():
    """Lista (pasta_da_secao, arquivo_html) de todas as seções com dados, ordenadas.
    A pasta pode ser '328'/'329'/'330'; o arquivo de saída é desempenho-<secao>.html."""
    out = []
    if ZONA_DIR.is_dir():
        for p in sorted(ZONA_DIR.iterdir()):
            if p.is_dir() and (p / "dados-desempenho.json").exists():
                out.append((p.name, f"desempenho-{p.name}.html"))
    return out


def montar(data_json, rdv_json, saida_html, tambem_mockup=True):
    """Monta uma página de desempenho autossuficiente a partir de um JSON de dados
    (parse_logd.py) e, opcionalmente, um JSON de RDV (parse_rdv.py), gravando em
    saida_html dentro de public/apos/."""
    if not TMPL.exists():
        TMPL.write_text(HTML.read_text(encoding="utf-8"), encoding="utf-8")
        print("  criado template:", TMPL.relative_to(REPO))

    tmpl = TMPL.read_text(encoding="utf-8")
    data_obj = json.loads(Path(data_json).read_text(encoding="utf-8"))

    rdv_path = Path(rdv_json)
    if rdv_path.exists():
        try:
            data_obj["rdv"] = json.loads(rdv_path.read_text(encoding="utf-8"))
            print("  mesclado RDV:", rdv_path)
        except Exception as e:  # pragma: no cover
            print("  aviso: não foi possível mesclar o RDV:", e)

    data = json.dumps(data_obj, ensure_ascii=False, indent=1)
    js = JS.read_text(encoding="utf-8")
    html = tmpl.replace("__DADOS_JSON__", data)
    html = html.replace('<script src="desempenho.js"></script>',
                        "<script>\n" + js + "\n</script>")

    # --- navegação entre seções: uma aba por seção (todas), a atual marcada como ativa,
    # para permitir ir e voltar facilmente (geral <-> seção <-> outra seção). ---
    nome_saida = Path(saida_html).name
    secao = (data_obj.get("boletim") or {}).get("secao")
    secao_disp = (str(secao).lstrip("0") or str(secao)) if secao else None
    tabs = []
    for sdir, arquivo in secoes_disponiveis():
        disp = sdir.lstrip("0") or sdir
        ativo = " active" if arquivo == nome_saida else ""
        tabs.append(f'<a href="{arquivo}" class="nav-item{ativo}">📈 Seção {disp}</a>')
    # fallback: se nada foi descoberto, mantém ao menos a própria seção
    if not tabs:
        tabs.append(f'<a href="{nome_saida}" class="nav-item active">📈 Desempenho</a>')
    html = html.replace("__SECAO_TABS__", "\n    ".join(tabs))

    # carimba o nº da seção no <title> e no <h1> (para a aba/arquivo ficar inequívoco).
    # remove zeros à esquerda para exibição: "0329" -> "329".
    if secao:
        html = html.replace(
            "<title>📈 Desempenho da Seção — Aprendizado a partir do Log de Urna</title>",
            f"<title>📈 Desempenho da Seção {secao_disp} — Aprendizado a partir do Log de Urna</title>")
        html = html.replace(
            "<h1>📈 Desempenho da Seção — Aprendizado pós-eleição</h1>",
            f"<h1>📈 Desempenho da Seção {secao_disp} — Aprendizado pós-eleição</h1>")

    if tambem_mockup:
        HTML.write_text(html, encoding="utf-8")
        print("  escrito:", HTML.relative_to(REPO))

    out = Path(saida_html)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("  escrito:", out)

    howto_src = REPO / "html-howto" / "rdv-e-log-de-urna.html"
    if howto_src.exists():
        howto_dst = APOS / "rdv-e-log-de-urna.html"
        howto_dst.write_text(howto_src.read_text(encoding="utf-8"), encoding="utf-8")
        print("  escrito:", howto_dst.relative_to(REPO))


def main():
    # Uso padrão (seção 0328): sem argumentos.
    #   python3 scripts/build_desempenho.py
    # Uso parametrizado (outra seção):
    #   python3 scripts/build_desempenho.py <dados.json> <dados-rdv.json> <saida.html>
    if len(sys.argv) >= 4:
        montar(sys.argv[1], sys.argv[2], sys.argv[3], tambem_mockup=False)
        print("Pronto.")
        return
    montar(JSON_DATA, MOCK / "dados-rdv.json", PUBLIC, tambem_mockup=True)
    print("Pronto. Abra public/apos/desempenho-328.html por duplo-clique.")


if __name__ == "__main__":
    main()
