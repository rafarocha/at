#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_logd.py — Transforma um Log de Urna (logd.dat) do TSE em um JSON de
indicadores de produtividade para o painel `desempenho.html`.

Entrada : logs/zone/<zona>/logd.dat   (texto ISO-8859-1, separado por TAB)
Formato : data\tseveridade\tid_urna\tsubsistema\tmensagem\thash

Saída   : html-mockups/dados-desempenho.json  (também é copiado p/ public via build)

O parser reconstrói a "sessão" de cada eleitor:
  Aguardando identificador -> identificador digitado -> foto -> digitais ->
  Eleitor habilitado -> Voto confirmado (xN) -> O voto foi computado

e extrai métricas de execução, espera, biometria, falhas e alertas.

Uso:
  python3 scripts/parse_logd.py logs/zone/150/logd.dat
"""
import sys, os, re, json
from datetime import datetime

FMT = "%d/%m/%Y %H:%M:%S"

def parse_line(line):
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 5:
        return None
    ts, sev, urn, sub, msg = parts[0], parts[1], parts[2], parts[3], parts[4]
    try:
        dt = datetime.strptime(ts, FMT)
    except ValueError:
        return None
    return {"dt": dt, "sev": sev, "urn": urn, "sub": sub, "msg": msg}


def main():
    if len(sys.argv) < 2:
        print("uso: python3 scripts/parse_logd.py <logd.dat> [saida.json]", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "html-mockups", "dados-desempenho.json")

    with open(path, "r", encoding="latin-1") as f:
        events = [e for e in (parse_line(l) for l in f) if e]

    if not events:
        print("nenhum evento válido", file=sys.stderr)
        sys.exit(1)

    # --- metadados da urna -------------------------------------------------
    meta = {"urna": events[0]["urn"], "versao": None, "municipio_secao": None,
            "ligada": None, "pronta": None, "encerramento": None,
            "primeiro_voto": None, "ultimo_voto": None,
            # identificadores extraídos do próprio log (subsistema SCUE):
            "municipio": None, "zona": None, "local": None, "secao": None,
            "modelo": None, "turno": None}
    # contagem de tipos de habilitação (p/ o resumo tipo Boletim de Urna)
    hab_tipos = {}
    for e in events:
        m = e["msg"]
        if meta["versao"] is None and m.startswith("Versão da aplicação:"):
            meta["versao"] = m.split(":", 1)[1].strip()
        if meta["ligada"] is None and "Urna ligada em" in m:
            meta["ligada"] = m
        if meta["pronta"] is None and m == "Urna pronta para receber votos":
            meta["pronta"] = e["dt"].strftime(FMT)
        if m == "Inicio do Encerramento":
            meta["encerramento"] = e["dt"].strftime(FMT)
        if meta["municipio"] is None and m.startswith("Município:"):
            meta["municipio"] = m.split(":", 1)[1].strip()
        if meta["zona"] is None and m.startswith("Zona Eleitoral:"):
            meta["zona"] = m.split(":", 1)[1].strip()
        if meta["local"] is None and m.startswith("Local de Votação:"):
            meta["local"] = m.split(":", 1)[1].strip()
        if meta["secao"] is None and m.startswith("Seção Eleitoral:"):
            meta["secao"] = m.split(":", 1)[1].strip()
        if meta["modelo"] is None and m.startswith("Identificação do Modelo de Urna:"):
            meta["modelo"] = m.split(":", 1)[1].strip()
        if meta["turno"] is None and "Iniciando aplicação" in m:
            tm = re.search(r"(\d+)[ºo]?\s*turno", m)
            if tm:
                meta["turno"] = tm.group(1) + "º turno"
        if m.startswith("Tipo de habilitação do eleitor"):
            mm = re.search(r"\[([^\]]+)\]", m)
            if mm:
                hab_tipos[mm.group(1)] = hab_tipos.get(mm.group(1), 0) + 1

    # --- reconstrução das sessões de eleitor -------------------------------
    sessions = []
    cur = None

    def flush(end_dt):
        nonlocal cur
        if cur and cur.get("habilitado"):
            cur["fim"] = end_dt
            sessions.append(cur)
        cur = None

    re_tent = re.compile(r"Tentativa \[(\d+)\] de \[(\d+)\]")
    re_score = re.compile(r"score (\d+)")

    pending_aguardando = None  # "Aguardando digitação do identificador" mais recente (antes do próx. eleitor)
    for e in events:
        m, dt = e["msg"], e["dt"]
        if m.startswith("Aguardando digitação do identificador"):
            # urna liberou a tela de identificação para o PRÓXIMO eleitor;
            # guarda o 1º "aguardando" que aparecer até o mesário digitar
            if pending_aguardando is None:
                pending_aguardando = dt
        if m == "Identificador do eleitor digitado pelo mesário":
            # novo eleitor começa a ser identificado
            flush(dt)
            cur = {"ident": dt, "habilitado": None, "computado": None,
                   "capturas": 0, "solicitacoes": 0, "timeout": 0,
                   "tipo_hab": None, "cargos": [], "score": None,
                   "tecla_indevida": 0, "primeiro_voto": None,
                   "teclas_dt": [], "aguardando": pending_aguardando}
            pending_aguardando = None
        if cur is None:
            continue
        if m.startswith("Solicita digital"):
            cur["solicitacoes"] += 1
        elif m.startswith("Capturada a digital"):
            cur["capturas"] += 1
        elif m.startswith("Timeout de reconhecimento"):
            cur["timeout"] += 1
        elif m.startswith("Tipo de habilitação do eleitor"):
            mm = re.search(r"\[([^\]]+)\]", m)
            cur["tipo_hab"] = mm.group(1) if mm else None
        elif m.startswith("Batimento de digitais retornou o score"):
            sc = re_score.search(m)
            if sc:
                cur["score"] = int(sc.group(1))
        elif m == "Eleitor foi habilitado":
            cur["habilitado"] = dt
        elif m.startswith("Voto confirmado para"):
            mm = re.search(r"\[([^\]]+)\]", m)
            if mm:
                cur["cargos"].append({"cargo": mm.group(1),
                                      "t": dt.strftime(FMT)})
                if cur["primeiro_voto"] is None:
                    cur["primeiro_voto"] = dt
        elif m == "Tecla indevida pressionada":
            cur["tecla_indevida"] += 1
            cur["teclas_dt"].append(dt)
            if cur["primeiro_voto"] is None:
                # a 1ª interação do eleitor também pode ser uma tecla antes do 1º voto
                cur.setdefault("primeira_tecla", dt)
        elif m == "O voto do eleitor foi computado":
            cur["computado"] = dt

    flush(events[-1]["dt"])

    # --- métricas por sessão ----------------------------------------------
    voters = []
    prev_comp = None
    teclas_dt_all = []   # todos os eventos de "Tecla indevida" (datetime), p/ timeline global
    for idx, s in enumerate(sessions):
        hab = s["habilitado"]
        comp = s["computado"] or s.get("fim")
        ident = s["ident"]
        exec_s = (comp - hab).total_seconds() if (hab and comp) else None
        id_s = (hab - ident).total_seconds() if (hab and ident) else None  # identificação+biometria
        # espera entre eleitores = do voto computado anterior até este eleitor ser identificado
        wait_s = (ident - prev_comp).total_seconds() if (prev_comp and ident) else None
        # tempo de reação: da habilitação até a 1ª interação do eleitor na cabine
        # (1º voto confirmado, ou a 1ª tecla, o que vier primeiro)
        primeira_acao = s.get("primeiro_voto")
        if s.get("primeira_tecla") and (primeira_acao is None or s["primeira_tecla"] < primeira_acao):
            primeira_acao = s["primeira_tecla"]
        reacao_s = (primeira_acao - hab).total_seconds() if (hab and primeira_acao) else None
        # --- tempos do PRESIDENTE/MESÁRIO (operação da mesa) ---
        aguardando = s.get("aguardando")
        # A) tempo até o presidente COMEÇAR a digitar o identificador do próximo eleitor
        #    (urna liberou a tela de identificação -> mesário digitou o identificador)
        pres_inicio_s = (ident - aguardando).total_seconds() if (ident and aguardando) else None
        # B) tempo que o presidente levou para HABILITAR (digitou identificador -> eleitor habilitado;
        #    inclui a captura da digital/biometria)
        pres_habilita_s = (hab - ident).total_seconds() if (hab and ident) else None
        teclas_dt_all.extend(s["teclas_dt"])
        voters.append({
            "n": idx + 1,
            "ident": ident.strftime(FMT) if ident else None,
            "aguardando": aguardando.strftime(FMT) if aguardando else None,
            "habilitado": hab.strftime(FMT) if hab else None,
            "primeiro_voto": s["primeiro_voto"].strftime(FMT) if s.get("primeiro_voto") else None,
            "computado": comp.strftime(FMT) if comp else None,
            "exec_s": round(exec_s) if exec_s is not None else None,
            "ident_s": round(id_s) if id_s is not None else None,
            "reacao_s": round(reacao_s) if (reacao_s is not None and reacao_s >= 0) else None,
            "pres_inicio_s": round(pres_inicio_s) if (pres_inicio_s is not None and pres_inicio_s >= 0) else None,
            "pres_habilita_s": round(pres_habilita_s) if (pres_habilita_s is not None and pres_habilita_s >= 0) else None,
            "wait_s": round(wait_s) if (wait_s is not None and wait_s >= 0) else None,
            "capturas": s["capturas"], "solicitacoes": s["solicitacoes"],
            "timeout": s["timeout"], "tipo_hab": s["tipo_hab"],
            "n_cargos": len(s["cargos"]), "score": s["score"],
            "tecla_indevida": s["tecla_indevida"],
        })
        if comp:
            prev_comp = comp

    if voters:
        meta["primeiro_voto"] = voters[0]["computado"]
        meta["ultimo_voto"] = voters[-1]["computado"]

    # --- alertas -----------------------------------------------------------
    alertas = [{"t": e["dt"].strftime(FMT), "hora": e["dt"].hour,
                "sub": e["sub"], "msg": e["msg"]}
               for e in events if e["sev"] == "ALERTA"]

    # --- throughput por hora (dia da votação) ------------------------------
    voting_day = None
    for v in voters:
        if v["computado"]:
            voting_day = datetime.strptime(v["computado"], FMT).date()
            break
    por_hora = {}
    for v in voters:
        if not v["computado"]:
            continue
        d = datetime.strptime(v["computado"], FMT)
        if d.date() != voting_day:
            continue
        por_hora[d.hour] = por_hora.get(d.hour, 0) + 1
    throughput = [{"hora": h, "votos": por_hora.get(h, 0)}
                  for h in range(min(por_hora), max(por_hora) + 1)] if por_hora else []

    # --- agregados ---------------------------------------------------------
    execs = [v["exec_s"] for v in voters if v["exec_s"] is not None]
    waits = [v["wait_s"] for v in voters if v["wait_s"] is not None]
    idents = [v["ident_s"] for v in voters if v["ident_s"] is not None]
    tentativas_total = sum(v["solicitacoes"] for v in voters)
    multi_bio = sum(1 for v in voters if v["solicitacoes"] > 1)

    def med(xs):
        if not xs: return None
        xs = sorted(xs); n = len(xs)
        return xs[n//2] if n % 2 else (xs[n//2-1]+xs[n//2])/2

    agg = {
        "total_eleitores": len(voters),
        "exec_medio_s": round(sum(execs)/len(execs), 1) if execs else None,
        "exec_mediana_s": med(execs),
        "exec_max_s": max(execs) if execs else None,
        "espera_media_s": round(sum(waits)/len(waits), 1) if waits else None,
        "espera_max_s": max(waits) if waits else None,
        "ident_medio_s": round(sum(idents)/len(idents), 1) if idents else None,
        "tentativas_biometricas": tentativas_total,
        "eleitores_multi_tentativa": multi_bio,
        "taxa_biometria_1a": round(100*(len(voters)-multi_bio)/len(voters), 1) if voters else None,
        "alertas": len(alertas),
        "teclas_indevidas": sum(v["tecla_indevida"] for v in voters),
        "reacao_media_s": None, "reacao_mediana_s": None, "reacao_max_s": None,
    }

    # reação (habilitação -> 1ª interação na cabine)
    reacoes = [v["reacao_s"] for v in voters if v["reacao_s"] is not None]
    if reacoes:
        agg["reacao_media_s"] = round(sum(reacoes)/len(reacoes), 1)
        agg["reacao_mediana_s"] = med(reacoes)
        agg["reacao_max_s"] = max(reacoes)

    # tempos do presidente/mesário
    pres_inicio = [v["pres_inicio_s"] for v in voters if v["pres_inicio_s"] is not None]
    pres_hab = [v["pres_habilita_s"] for v in voters if v["pres_habilita_s"] is not None]
    agg["pres_inicio_medio_s"] = round(sum(pres_inicio)/len(pres_inicio), 1) if pres_inicio else None
    agg["pres_inicio_mediana_s"] = med(pres_inicio)
    agg["pres_inicio_max_s"] = max(pres_inicio) if pres_inicio else None
    agg["pres_habilita_medio_s"] = round(sum(pres_hab)/len(pres_hab), 1) if pres_hab else None
    agg["pres_habilita_mediana_s"] = med(pres_hab)
    agg["pres_habilita_max_s"] = max(pres_hab) if pres_hab else None

    # faixa de horas da votação (p/ todos os gráficos por hora ficarem alinhados)
    def hour_of(fmt_str):
        return datetime.strptime(fmt_str, FMT).hour
    horas_voto = [hour_of(v["computado"]) for v in voters if v["computado"]]
    h_ini = min(horas_voto) if horas_voto else 8
    h_fim = max(horas_voto) if horas_voto else 18
    faixa_horas = list(range(h_ini, h_fim + 1))

    # --- resumo de alertas por tipo (contagem + por hora) ------------------
    alert_summary = {}
    for a in alertas:
        d = alert_summary.setdefault(a["msg"], {"msg": a["msg"], "total": 0,
                                                "sub": a["sub"],
                                                "por_hora": {h: 0 for h in faixa_horas}})
        d["total"] += 1
        d["por_hora"][a["hora"]] = d["por_hora"].get(a["hora"], 0) + 1
    alert_summary = sorted(alert_summary.values(), key=lambda x: -x["total"])
    for d in alert_summary:
        d["por_hora"] = [{"hora": h, "n": d["por_hora"].get(h, 0)} for h in faixa_horas]

    # --- espera (fila) por hora: média e pico ------------------------------
    espera_por_hora = []
    for h in faixa_horas:
        hw = [v["wait_s"] for v in voters
              if v["wait_s"] is not None and v["ident"] and hour_of(v["ident"]) == h]
        espera_por_hora.append({
            "hora": h,
            "media_s": round(sum(hw)/len(hw)) if hw else 0,
            "max_s": max(hw) if hw else 0,
            "n": len(hw),
        })

    # --- ociosidade: períodos sem ninguém votando --------------------------
    # gap = do voto computado de um eleitor até a habilitação do próximo.
    # consideramos "ocioso" acima de um limiar (default 120s).
    LIMIAR_OCIOSO = 120
    ociosidade = []
    for i in range(1, len(voters)):
        prev = voters[i-1]; curv = voters[i]
        if not prev["computado"] or not curv["habilitado"]:
            continue
        t0 = datetime.strptime(prev["computado"], FMT)
        t1 = datetime.strptime(curv["habilitado"], FMT)
        gap = (t1 - t0).total_seconds()
        if gap >= LIMIAR_OCIOSO:
            ociosidade.append({
                "inicio": prev["computado"], "fim": curv["habilitado"],
                "dur_s": round(gap), "apos_eleitor": prev["n"],
            })
    ociosidade.sort(key=lambda x: -x["dur_s"])

    # --- teclas indevidas por hora -----------------------------------------
    teclas_por_hora_map = {h: 0 for h in faixa_horas}
    for dt in teclas_dt_all:
        teclas_por_hora_map[dt.hour] = teclas_por_hora_map.get(dt.hour, 0) + 1
    teclas_por_hora = [{"hora": h, "n": teclas_por_hora_map.get(h, 0)} for h in faixa_horas]

    # --- biometria por hora: solicitações de digital e repetições ----------
    # "Solicita digital. Tentativa [n] de [4]": cada evento é uma solicitação;
    # tentativa > 1 é uma REPETIÇÃO (biometria não pegou de primeira).
    re_tent_bio = re.compile(r"Tentativa \[(\d+)\] de \[\d+\]")
    bio_sol_map = {h: 0 for h in faixa_horas}
    bio_rep_map = {h: 0 for h in faixa_horas}
    for e in events:
        if e["dt"].date() != voting_day:
            continue
        if e["msg"].startswith("Solicita digital. Tentativa"):
            h = e["dt"].hour
            bio_sol_map[h] = bio_sol_map.get(h, 0) + 1
            mt = re_tent_bio.search(e["msg"])
            if mt and int(mt.group(1)) > 1:
                bio_rep_map[h] = bio_rep_map.get(h, 0) + 1
    biometria_por_hora = [{"hora": h,
                           "solicitacoes": bio_sol_map.get(h, 0),
                           "repeticoes": bio_rep_map.get(h, 0)}
                          for h in faixa_horas]

    # --- teclas indevidas por eleitor (distribuição + outliers) ------------
    teclas_por_eleitor = [{"n": v["n"], "teclas": v["tecla_indevida"],
                           "habilitado": v["habilitado"], "computado": v["computado"]}
                          for v in voters]
    top_teclas = sorted(teclas_por_eleitor, key=lambda x: -x["teclas"])[:15]

    # --- eventos por hora (volume total do log) ----------------------------
    eventos_hora_map = {}
    for e in events:
        eventos_hora_map[(e["dt"].date(), e["dt"].hour)] = \
            eventos_hora_map.get((e["dt"].date(), e["dt"].hour), 0) + 1
    # só o dia da votação
    eventos_por_hora = [{"hora": h, "n": eventos_hora_map.get((voting_day, h), 0)}
                        for h in faixa_horas]

    # --- eventos INDESEJÁVEIS / fora da programação normal, por hora -------
    # Padrões de mensagem que indicam problema ou desvio do fluxo normal de voto.
    # (prefixo = casa com startswith; a severidade ALERTA também entra sempre.)
    INDESEJAVEIS = [
        "Identificador do eleitor digitado inválido",
        "Eleitor sem atividade por",
        "Eleitor voltou a digitar enquanto estava sendo suspenso",
        "Biometria coletada não é do mesário",
        "O eleitor identificado já votou",
        "Habilitação cancelada",
        "Eleitor não encontrado para o identificador informado",
        "Timeout de reconhecimento do dedo",
        "Mesário indagado se eleitor está votando",
        "Digitado título inválido para o registro de mesário",
    ]
    def eh_indesejavel(e):
        if e["sev"] == "ALERTA":
            return True
        return any(e["msg"].startswith(p) for p in INDESEJAVEIS)

    indesej_hora_map = {h: 0 for h in faixa_horas}
    indesej_tipos = {}
    for e in events:
        if e["dt"].date() != voting_day:
            continue
        if eh_indesejavel(e):
            indesej_hora_map[e["dt"].hour] = indesej_hora_map.get(e["dt"].hour, 0) + 1
            # normaliza o tipo (tira colchetes/números para agrupar)
            tipo = re.sub(r"\[[^\]]*\]", "[]", e["msg"])
            tipo = re.sub(r"\bN\b|\d+", "N", tipo)
            indesej_tipos[tipo] = indesej_tipos.get(tipo, 0) + 1
    eventos_indesejaveis_por_hora = [{"hora": h, "n": indesej_hora_map.get(h, 0)}
                                     for h in faixa_horas]
    eventos_indesejaveis_tipos = sorted(
        ({"tipo": t, "n": c} for t, c in indesej_tipos.items()),
        key=lambda x: -x["n"])

    # --- resumo tipo "Boletim de Urna" (cabeçalho de contexto) -------------
    # Campos que o LOG comprova diretamente:
    #   identificadores (município/zona/local/seção), modelo, código UE,
    #   abertura/fechamento, habilitação biométrica (contagem) e comparecimento
    #   (= nº de votos computados). Os demais campos (eleitores aptos, habilitação
    #   biográfica, sem biometria, faltosos) vêm do BOLETIM DE URNA (bu.dat), não do
    #   log — ficam aqui como tabela editável POR SEÇÃO, pré-preenchida com os
    #   valores do Boletim (fonte: tela do BU no portal do TSE). Seções sem entrada
    #   aqui saem com esses campos em branco (None) — o resto vem do log/RDV.
    BU_POR_SECAO = {
        "0328": {
            "eleitores_aptos": 394, "eleitores_aptos_originais": 394,
            "eleitores_aptos_temporarios": 0, "habilitacao_biografica": 13,
            "habilitacao_sem_biometria": 8, "eleitores_faltosos": 90,
        },
        # 329 e 330: o Boletim de Urna não foi coletado para estas seções, então
        # os campos exclusivos do BU (aptos/faltosos/biográfica/sem biometria) ficam
        # None. O que o LOG comprova — comparecimento e habilitação biométrica — é
        # preenchido automaticamente abaixo, e a habilitação não-biométrica é
        # derivada (comparecimento − biométrica).
        "0329": {
            "eleitores_aptos": None, "eleitores_aptos_originais": None,
            "eleitores_aptos_temporarios": None, "habilitacao_biografica": None,
            "habilitacao_sem_biometria": None, "eleitores_faltosos": None,
        },
        "0330": {
            "eleitores_aptos": None, "eleitores_aptos_originais": None,
            "eleitores_aptos_temporarios": None, "habilitacao_biografica": None,
            "habilitacao_sem_biometria": None, "eleitores_faltosos": None,
        },
    }
    _bu_vazio = {
        "eleitores_aptos": None, "eleitores_aptos_originais": None,
        "eleitores_aptos_temporarios": None, "habilitacao_biografica": None,
        "habilitacao_sem_biometria": None, "eleitores_faltosos": None,
    }
    bu_secao = dict(BU_POR_SECAO.get(meta["secao"], _bu_vazio))
    comparecimento = agg["total_eleitores"]
    abertura_ue = meta["pronta"]
    fechamento_ue = None
    # último "Desligando a urna" no dia da votação = fechamento aproximado
    for e in reversed(events):
        if e["msg"] == "Desligando a urna" and e["dt"].date() == voting_day:
            fechamento_ue = e["dt"].strftime(FMT); break
    if fechamento_ue is None:
        fechamento_ue = events[-1]["dt"].strftime(FMT)
    boletim = {
        "municipio": meta["municipio"], "zona": meta["zona"],
        "local": meta["local"], "secao": meta["secao"],
        "modelo": meta["modelo"], "codigo_ue": meta["urna"],
        "turno": meta["turno"] or "1º turno",
        "abertura_ue": abertura_ue, "fechamento_ue": fechamento_ue,
        "comparecimento": comparecimento,
        "habilitacao_biometrica": hab_tipos.get("biométrica", 0),
        # vindos do Boletim de Urna (bu.dat):
        **bu_secao,
    }
    # habilitação não-biométrica derivada do log (comparecimento − biométrica).
    # Quando o BU separa biográfica e sem-biometria, esses campos ficam preenchidos;
    # quando não temos o BU, mostramos o total não-biométrico derivado.
    nao_bio = comparecimento - boletim["habilitacao_biometrica"]
    boletim["habilitacao_nao_biometrica"] = nao_bio if nao_bio >= 0 else None
    # % comparecimento (se tivermos os aptos)
    if boletim["eleitores_aptos"]:
        boletim["pct_comparecimento"] = round(100 * comparecimento / boletim["eleitores_aptos"], 1)

    # --- plano de melhoria: ações pontuadas pelos dados do log -------------
    # Cada ação recebe um "score" de prioridade 0–100 = quão longe a métrica
    # desta urna está de uma meta saudável. O top 5 alimenta o gráfico radial.
    teclas_por_eleitor_media = (agg["teclas_indevidas"] / agg["total_eleitores"]
                                if agg["total_eleitores"] else 0)
    tot_rep = sum(b["repeticoes"] for b in biometria_por_hora)
    tot_sol = sum(b["solicitacoes"] for b in biometria_por_hora)
    taxa_rep_bio = (100 * tot_rep / tot_sol) if tot_sol else 0

    # tempo "perdido" = espera entre eleitores sobre o total de tempo ocupado
    # (espera + execução). É o tempo que a mesa pode recuperar habilitando o
    # próximo eleitor assim que o atual termina.
    soma_espera = sum(v["wait_s"] for v in voters if v.get("wait_s") is not None)
    soma_exec = sum(v["exec_s"] for v in voters if v.get("exec_s") is not None)
    pct_tempo_perdido = round(100 * soma_espera / (soma_espera + soma_exec), 1) if (soma_espera + soma_exec) else 0
    agg["pct_tempo_perdido"] = pct_tempo_perdido

    def score(valor, meta_boa, meta_ruim):
        """0 quando valor<=meta_boa; 100 quando valor>=meta_ruim; linear no meio."""
        if meta_ruim == meta_boa:
            return 0
        s = 100 * (valor - meta_boa) / (meta_ruim - meta_boa)
        return int(max(0, min(100, round(s))))

    # --- #1 fixo: assim que terminar o voto, já habilitar o próximo ---------
    acao_prontidao = {
        "acao": "Ao finalizar o voto, já ir habilitando o próximo eleitor — não deixar a urna parada",
        "icone": "⏳", "para": "Presidente/mesário",
        "score": max(score(pct_tempo_perdido, 10, 40),
                     score(agg["pres_inicio_medio_s"], 10, 45)),
        "evidencia": f"{pct_tempo_perdido:.0f}% do tempo de atendimento foi espera entre eleitores · média de {int(agg['espera_media_s'])}s de espera por eleitor · {int(agg['pres_inicio_medio_s'])}s até a mesa começar a identificar o próximo",
        "metrica": "tempo perdido na fila",
    }

    # --- demais ações, ordenadas naturalmente pelo score --------------------
    meio = [
        {
            "acao": "Após ~10s sem o eleitor confirmar sequer 1 candidato, já interagir e avisar que ele está demorando",
            "icone": "🧭", "para": "Presidente/mesário",
            "score": score(teclas_por_eleitor_media, 1.5, 6),
            "evidencia": f"{agg['teclas_indevidas']} teclas indevidas no dia (~{teclas_por_eleitor_media:.1f} por eleitor) — sinal de eleitor travado/inseguro na cabine",
            "metrica": "teclas indevidas",
        },
        {
            "acao": "Limpar o leitor biométrico e orientar dedo limpo/seco e pressão firme",
            "icone": "🖐️", "para": "Mesário",
            "score": score(taxa_rep_bio, 12, 45),
            "evidencia": f"{taxa_rep_bio:.0f}% das capturas foram repetição ({agg['eleitores_multi_tentativa']} eleitores repetiram a digital)",
            "metrica": "repetição de biometria",
        },
        {
            "acao": "Direcionar ao simulador do TSE 1 a cada 5 da fila — e qualquer um com dúvida, dificuldade ou pouca instrução",
            "icone": "🕹️", "para": "Secretário",
            "score": score(agg["exec_medio_s"], 45, 110),
            "evidencia": f"execução média de {int(agg['exec_medio_s'])}s por eleitor (mediana {int(agg['exec_mediana_s'])}s)",
            "metrica": "tempo de execução",
        },
        {
            "acao": "Digitar o identificador com atenção para evitar título/documento inválido",
            "icone": "⌨️", "para": "Mesário",
            "score": score(agg["alertas"], 5, 40),
            "evidencia": f"{agg['alertas']} alertas no dia (a maioria por identificador digitado inválido)",
            "metrica": "alertas",
        },
    ]
    meio = sorted(meio, key=lambda x: -x["score"])

    # --- último fixo: acomodar pessoas sentadas (prioridade) ----------------
    acao_acomodar = {
        "acao": "Acomodar quem espera sentado — sobretudo idosos, gestantes e PcD (prioridade)",
        "icone": "🪑", "para": "Secretário/mesário",
        "score": score(agg["espera_media_s"], 15, 90),
        "evidencia": f"espera média de {int(agg['espera_media_s'])}s por eleitor, com pico de {int(agg['espera_max_s'])}s — tempo em pé que pesa para quem tem prioridade",
        "metrica": "conforto na espera",
    }

    melhorias = [acao_prontidao] + meio + [acao_acomodar]

    data = {
        "fonte": os.path.basename(path),
        "gerado_em": datetime.now().strftime(FMT),
        "meta": meta,
        "boletim": boletim,
        "melhorias": melhorias,
        "agg": agg,
        "throughput": throughput,
        "voters": voters,
        "alertas": alertas,
        "alert_summary": alert_summary,
        "espera_por_hora": espera_por_hora,
        "ociosidade": ociosidade,
        "teclas_por_hora": teclas_por_hora,
        "biometria_por_hora": biometria_por_hora,
        "teclas_por_eleitor": teclas_por_eleitor,
        "top_teclas": top_teclas,
        "eventos_por_hora": eventos_por_hora,
        "eventos_indesejaveis_por_hora": eventos_indesejaveis_por_hora,
        "eventos_indesejaveis_tipos": eventos_indesejaveis_tipos,
        "limiar_ocioso_s": LIMIAR_OCIOSO,
    }

    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"OK -> {out}")
    print(f"  eleitores: {agg['total_eleitores']}  "
          f"exec_medio: {agg['exec_medio_s']}s  "
          f"espera_media: {agg['espera_media_s']}s  "
          f"alertas: {agg['alertas']}  "
          f"taxa_bio_1a: {agg['taxa_biometria_1a']}%")


if __name__ == "__main__":
    main()
