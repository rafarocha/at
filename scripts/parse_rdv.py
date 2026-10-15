#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_rdv.py — Lê um RDV (Registro Digital do Voto) do TSE, que é um arquivo
binário ASN.1 DER, e produz um JSON com a contagem de votos por cargo.

O RDV NÃO contém dados do eleitor nem a ordem real dos votos (é embaralhado de
propósito, para garantir o sigilo). Ele contém, por cargo, a lista de votos:
cada voto é um "tipo" (nominal, branco, nulo, legenda) e, quando nominal, o
número digitado.

Mapeamento de tipo de voto (enumeração do RDV):
  1 = branco · 2 = nominal · 3 = nulo · 4 = legenda · (outros) = especiais

Uso:
  python3 scripts/parse_rdv.py <RDV_...dat> [saida.json]
"""
import sys, os, json

# ---- parser DER mínimo ----------------------------------------------------
class Node:
    __slots__ = ("tag", "cls", "constructed", "value", "children", "raw")
    def __init__(self, tag, cls, constructed):
        self.tag = tag; self.cls = cls; self.constructed = constructed
        self.value = None; self.children = []; self.raw = None


def parse_len(buf, i):
    b = buf[i]; i += 1
    if b < 0x80:
        return b, i
    n = b & 0x7F
    length = int.from_bytes(buf[i:i+n], "big"); i += n
    return length, i


def parse_tlv(buf, i, end):
    nodes = []
    while i < end:
        first = buf[i]; i += 1
        cls = (first & 0xC0) >> 6
        constructed = bool(first & 0x20)
        tag = first & 0x1F
        if tag == 0x1F:  # multi-byte tag (não usado aqui)
            tag = 0
            while True:
                b = buf[i]; i += 1; tag = (tag << 7) | (b & 0x7F)
                if not (b & 0x80): break
        length, i = parse_len(buf, i)
        content = buf[i:i+length]
        node = Node(tag, cls, constructed)
        if constructed:
            node.children = parse_tlv(content, 0, len(content))
        else:
            node.raw = content
        nodes.append(node)
        i += length
    return nodes


# tipo de voto (enum) -> rótulo
# Mapeamento confirmado por inspeção do RDV desta urna:
#   tipo 3 = BRANCO  (nunca traz número)
#   tipo 4 = NULO    (traz o número digitado — ex.: '00', '0000', nº inexistente)
#   tipos 1, 2, 7 = voto válido/nominal (trazem número de candidato/legenda)
TIPO = {1: "nominal", 2: "nominal", 3: "branco", 4: "nulo",
        5: "nominal", 6: "especial", 7: "nominal"}


def walk_votes(node, cargo_votes, cur_cargo):
    """Percorre a árvore. Cada SEQUENCE com um ENUMERATED (tag 10) + um
    NUMERICSTRING (tag 18) é um voto. Blocos de cargo trazem um INTEGER com o
    código do cargo antes da lista de votos."""
    # Detecta voto: filho ENUMERATED seguido de NUMERICSTRING
    kids = node.children
    i = 0
    while i < len(kids):
        k = kids[i]
        if (not k.constructed) and k.tag == 10:  # ENUMERATED
            # procura NUMERICSTRING logo após
            num = None
            if i+1 < len(kids) and kids[i+1].tag == 18:
                num = kids[i+1].raw.decode("latin-1")
            tipo = int.from_bytes(k.raw, "big")
            cargo_votes[cur_cargo[0]].append((tipo, num))
            i += 2 if num is not None else 1
            continue
        i += 1
    for k in kids:
        if k.constructed:
            walk_votes(k, cargo_votes, cur_cargo)


def main():
    if len(sys.argv) < 2:
        print("uso: python3 scripts/parse_rdv.py <RDV_...dat> [saida.json]", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "html-mockups", "dados-rdv.json")

    buf = open(path, "rb").read()
    root = parse_tlv(buf, 0, len(buf))

    # Encontra os blocos de cargo: cada cargo é uma SEQUENCE grande que começa
    # com cont[1]+INTEGER(codigo) e depois a lista de SEQUENCE(voto).
    cargos = []  # (codigo, [ (tipo, numero) ])

    def find_cargos(node):
        for k in node.children:
            # um bloco de cargo tem: cont[1] (tag 1 ctx), INTEGER, e muitos SEQUENCE voto
            if k.constructed:
                codigo = None
                votos = []
                for j, c in enumerate(k.children):
                    if c.cls == 2 and c.tag == 1 and not c.constructed:
                        pass
                    if (not c.constructed) and c.tag == 2 and codigo is None and j <= 2:
                        codigo = int.from_bytes(c.raw, "big")
                # é bloco de votos se tem filhos SEQUENCE com ENUMERATED+NUMERICSTRING
                voto_seqs = [c for c in k.children
                             if c.constructed and len(c.children) >= 1
                             and c.children[0].tag == 10]
                if len(voto_seqs) >= 3:
                    for vs in voto_seqs:
                        tipo = int.from_bytes(vs.children[0].raw, "big")
                        num = None
                        if len(vs.children) >= 2 and vs.children[1].tag == 18:
                            num = vs.children[1].raw.decode("latin-1")
                        votos.append((tipo, num))
                    cargos.append((codigo, votos))
                find_cargos(k)

    find_cargos(_root_wrap(root))

    # Monta resumo por cargo
    out_cargos = []
    for idx, (codigo, votos) in enumerate(cargos):
        nominais = {}
        nulos_num = {}   # números digitados que resultaram em voto NULO
        tipos = {}
        comprimentos = {}
        for tipo, num in votos:
            lab = TIPO.get(tipo, f"tipo{tipo}")
            tipos[lab] = tipos.get(lab, 0) + 1
            if lab == "nominal" and num:
                nominais[num] = nominais.get(num, 0) + 1
                comprimentos[len(num)] = comprimentos.get(len(num), 0) + 1
            elif lab == "nulo" and num is not None:
                nulos_num[num] = nulos_num.get(num, 0) + 1
        dom_len = max(comprimentos, key=comprimentos.get) if comprimentos else None
        out_cargos.append({
            "codigo": codigo,
            "idx": idx,
            "total": len(votos),
            "num_len": dom_len,
            "tipos": tipos,
            "nominais": sorted(({"numero": n, "votos": c} for n, c in nominais.items()),
                               key=lambda x: -x["votos"]),
            "nulos_numeros": sorted(({"numero": n, "votos": c} for n, c in nulos_num.items()),
                                    key=lambda x: -x["votos"]),
        })

    # --- rotular cargos pelo comprimento do número + ordem --------------------
    # Assinaturas típicas: Presidente/Governador=2 díg, Dep.Federal=4, Dep.Estadual=5,
    # Senador=3 (e normalmente 2 votos → total dobrado). O 1º bloco de 2 díg é
    # Presidente; o 2º bloco de 2 díg é Governador.
    vistos_2dig = 0
    for c in out_cargos:
        L = c["num_len"]; dobrado = c["total"] > max(x["total"] for x in out_cargos) * 0.75 and c["total"] % 2 == 0 and c["total"] > 304
        if L == 2:
            vistos_2dig += 1
            c["cargo"] = "Presidente" if vistos_2dig == 1 else "Governador"
        elif L == 3:
            c["cargo"] = "Senador"
        elif L == 4:
            c["cargo"] = "Deputado Federal"
        elif L == 5:
            c["cargo"] = "Deputado Estadual"
        else:
            c["cargo"] = f"Cargo {c['idx']+1}"

    data = {"fonte": os.path.basename(path), "cargos": out_cargos}
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"OK -> {out}")
    for c in out_cargos:
        print(f"  cargo {c['codigo']}: {c['total']} votos · tipos={c['tipos']} · "
              f"top nominal={c['nominais'][:3]}")


def _root_wrap(nodes):
    n = Node(0, 0, True); n.children = nodes; return n


if __name__ == "__main__":
    main()
