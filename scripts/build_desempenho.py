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
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MOCK = REPO / "html-mockups"
TMPL = MOCK / "desempenho.tmpl.html"
HTML = MOCK / "desempenho.html"
JS = MOCK / "desempenho.js"
JSON_DATA = MOCK / "dados-desempenho.json"
# tudo que é "após a eleição" (desempenho + guias de leitura dos arquivos de urna) fica aqui:
APOS = REPO / "public" / "apos"
PUBLIC = APOS / "desempenho.html"


def main():
    # na primeira execução, o template ainda não existe: cria a partir do .html atual
    if not TMPL.exists():
        TMPL.write_text(HTML.read_text(encoding="utf-8"), encoding="utf-8")
        print("  criado template:", TMPL.relative_to(REPO))

    tmpl = TMPL.read_text(encoding="utf-8")
    data_obj = json.loads(JSON_DATA.read_text(encoding="utf-8"))

    # se houver dados do RDV (gerados por parse_rdv.py), embute junto
    rdv_path = MOCK / "dados-rdv.json"
    if rdv_path.exists():
        try:
            data_obj["rdv"] = json.loads(rdv_path.read_text(encoding="utf-8"))
            print("  mesclado RDV:", rdv_path.relative_to(REPO))
        except Exception as e:  # pragma: no cover
            print("  aviso: não foi possível mesclar o RDV:", e)

    data = json.dumps(data_obj, ensure_ascii=False, indent=1)
    js = JS.read_text(encoding="utf-8")

    # injeta o JSON no marcador (sem interpretar \ ou grupos de regex)
    html = tmpl.replace("__DADOS_JSON__", data)
    # troca a referência externa pelo JS inline
    html = html.replace('<script src="desempenho.js"></script>',
                        "<script>\n" + js + "\n</script>")

    HTML.write_text(html, encoding="utf-8")
    print("  escrito:", HTML.relative_to(REPO))

    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC.write_text(html, encoding="utf-8")
    print("  escrito:", PUBLIC.relative_to(REPO))

    # copia o guia do RDV/Log para public/apos/ (fica ao lado de desempenho.html, para o
    # link da navegação funcionar tanto local quanto no GitHub Pages)
    howto_src = REPO / "html-howto" / "rdv-e-log-de-urna.html"
    if howto_src.exists():
        howto_dst = APOS / "rdv-e-log-de-urna.html"
        howto_dst.write_text(howto_src.read_text(encoding="utf-8"), encoding="utf-8")
        print("  escrito:", howto_dst.relative_to(REPO))

    print("Pronto. Abra public/apos/desempenho.html por duplo-clique.")


if __name__ == "__main__":
    main()
