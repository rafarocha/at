#!/usr/bin/env python3
"""
Gera scripts/seed_demo/{checkpoints,ocorrencias,rondas}.csv — um preenchimento BREVE e REAL (não
fictício-congelado como os samples) para colocar na planilha real (checkpoints-999ze) e poder
testar o /start pelo celular vendo o public/demo/ com alguma coisa na tela, em vez de vazio.

Cada seção acompanha 27 "atividades" no total (21 tarefas T01-T21 + 6 rondas do dia) — este
script preenche só uma FATIA BREVE disso, por volta de 30% nas seções boas (e bem menos nas
ruins, de propósito, pra reforçar que estão atrasadas), em vez do dia inteiro:
  - 3 seções "boas"   (01-03): ~30% das atividades feitas (T01-T07 + 1 ronda), fila baixa.
  - 3 seções "médias"  (04-06): ~26% (T01-T06 + 1 ronda), fila começando a incomodar.
  - 10 seções "ruins" (07-16, ~60%): 4%-22% feito (poucas tarefas, 0 ou 1 ronda), motivos
    variados — tarefa não confirmada, ronda faltando, ocorrência aberta, fila grande.

Depois de gerar, use scripts/seed_demo_sheet.py para subir isso pra planilha real (soma às linhas
que já existirem — não apaga nada).
"""
import csv
import datetime
import pathlib
import random

random.seed(42)

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "scripts" / "seed_demo"
HOJE = datetime.date.today().isoformat()

NOMES = [
    "Marcos Vinicius", "Helena Duarte", "Bianca Ferreira", "Otavio Ramos", "Livia Santana",
    "Caio Mendes", "Sofia Barreto", "Igor Cavalcanti", "Nicole Almeida", "Vitor Hugo Lopes",
    "Amanda Rezende", "Daniel Prado", "Carolina Vasconcelos", "Bruno Tavares", "Isadora Campos",
    "Rodrigo Peixoto", "Fernanda Salles", "Henrique Borges", "Yasmin Cordeiro", "Pedro Augusto",
]

def par_nomes():
    a, b = random.sample(NOMES, 2)
    return f"{a} e {b}"

def hhmm(minuto):
    return f"{minuto // 60:02d}:{minuto % 60:02d}"

def carimbo(minuto):
    return f"{HOJE} {hhmm(minuto)}"

TAREFAS_T = [
    ("T01", 405), ("T02", 420), ("T03", 420), ("T04", 420), ("T05", 450), ("T06", 450),
    ("T07", 465), ("T08", 480), ("T09", 480), ("T10", 480), ("T11", 510), ("T12", 510), ("T13", 600),
]
TAREFAS_G = [("G01", 390), ("G02", 390), ("G03", 420), ("G04", 480), ("G05", 510)]

SECOES_BOAS = ["01", "02", "03"]
SECOES_MEDIAS = ["04", "05", "06"]
INCLUIR_BOAS = ["T01", "T02", "T03", "T04", "T05", "T06", "T07"]   # 7 de 21 -> + 1 ronda = 8/27 (~30%)
INCLUIR_MEDIAS = ["T01", "T02", "T03", "T04", "T05", "T06"]         # 6 de 21 -> + 1 ronda = 7/27 (~26%)
# cada seção "ruim": quais tarefas confirmar (bem poucas, de propósito), se tem ocorrência aberta
# (tipo), fila/votados da única ronda feita (ou nenhuma) — resultado fica entre ~4% e ~22%.
SECOES_RUINS = {
    "07": {"incluir": ["T01", "T02", "T03"], "ocorrencia": None, "fila": 32, "votados": 95, "num_rondas": 1},
    "08": {"incluir": ["T01", "T02"], "ocorrencia": ("FILA", "Fila grande e mesa sem administrador para organizar."), "fila": 22, "votados": 88, "num_rondas": 1},
    "09": {"incluir": ["T01", "T02", "T03", "T04"], "ocorrencia": None, "fila": 20, "votados": 70, "num_rondas": 1},
    "10": {"incluir": ["T01"], "ocorrencia": ("URNA", "Urna travou na leitura, suporte técnico acionado."), "fila": 38, "votados": 60, "num_rondas": 0},
    "11": {"incluir": ["T01", "T02", "T03", "T04", "T05"], "ocorrencia": None, "fila": 18, "votados": 82, "num_rondas": 1},
    "12": {"incluir": ["T01", "T02"], "ocorrencia": ("ENERGIA", "Oscilação de energia, no-break ativado."), "fila": 19, "votados": 90, "num_rondas": 1},
    "13": {"incluir": ["T01"], "ocorrencia": None, "fila": 45, "votados": 30, "num_rondas": 0},
    "14": {"incluir": ["T01", "T02", "T04", "T05"], "ocorrencia": ("SEGURANCA", "Discussão entre eleitores na fila, mesário intervindo."), "fila": 24, "votados": 78, "num_rondas": 1},
    "15": {"incluir": ["T01", "T02", "T03"], "ocorrencia": None, "fila": 16, "votados": 65, "num_rondas": 1},
    "16": {"incluir": ["T01"], "ocorrencia": ("FILA", "Fila grande desde a abertura, ritmo muito lento."), "fila": 33, "votados": 55, "num_rondas": 0},
}

checkpoints_rows = []
rondas_rows = []
ocorrencias_rows = []

# tarefas gerais (G01-G05) — uma vez só, sem seção, todas confirmadas
for codigo, hora in TAREFAS_G:
    checkpoints_rows.append([codigo, "", "", "", "concluido", par_nomes(), carimbo(hora - 3), ""])

def add_tarefas(secao, incluir):
    for codigo, hora in TAREFAS_T:
        if codigo not in incluir:
            continue
        obs = "" if random.random() > 0.3 else random.choice(["Tudo certo por aqui.", "Sem novidades.", ""])
        checkpoints_rows.append([codigo, secao, "", "", "concluido", par_nomes(), carimbo(hora - random.randint(1, 6)), obs])

RONDA_ATIVIDADES_TODAS = "R01 R02 R03 R04 R05"

def tempo_espera_para(fila):
    # tempo médio de espera relatado (R05) — cresce com o tamanho da fila, com alguma variação
    return str(max(1, round(fila * 1.5) + random.randint(-2, 3)))

def add_rondas(secao, fila1, votados1, fila2=None, votados2=None, obs2="", num_rondas=2):
    # ronda mora só na aba "rondas" — checkpoints.csv leva só tarefas T##/G## (nunca RONDA)
    if num_rondas == 0:
        return  # seção "ruim" que nem a primeira ronda conseguiu fazer ainda
    rondas_rows.append([secao, hhmm(510 + random.randint(1, 6)), str(fila1), str(votados1), "sim",
                         tempo_espera_para(fila1), RONDA_ATIVIDADES_TODAS, "", par_nomes()])
    if num_rondas >= 2:
        rondas_rows.append([secao, hhmm(600 + random.randint(1, 6)), str(fila2), str(votados2), "sim",
                             tempo_espera_para(fila2), RONDA_ATIVIDADES_TODAS, obs2, par_nomes()])

for secao in SECOES_BOAS:
    add_tarefas(secao, incluir=INCLUIR_BOAS)
    add_rondas(secao, fila1=random.randint(4, 9), votados1=random.randint(30, 45), num_rondas=1)

for secao in SECOES_MEDIAS:
    add_tarefas(secao, incluir=INCLUIR_MEDIAS)
    add_rondas(secao, fila1=random.randint(10, 16), votados1=random.randint(25, 35),
               obs2="Fila aumentou um pouco, acompanhando.", num_rondas=1)

for secao, cfg in SECOES_RUINS.items():
    add_tarefas(secao, incluir=cfg["incluir"])
    add_rondas(secao, fila1=cfg["fila"], votados1=cfg["votados"],
               obs2="Situação sendo monitorada." if not cfg["ocorrencia"] else "",
               num_rondas=cfg["num_rondas"])
    if cfg["ocorrencia"]:
        codigo_oc, desc = cfg["ocorrencia"]
        ocorrencias_rows.append([codigo_oc, secao, desc, par_nomes(), hhmm(random.randint(420, 480)), "aberta"])

OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "checkpoints.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codigo", "secao", "titulo", "horario_previsto", "status", "confirmado_por", "confirmado_em", "observacao"])
    w.writerows(checkpoints_rows)

with open(OUT / "rondas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["secao", "horario", "fila", "votados", "bateria_ok", "tempo_espera_min", "atividades", "observacao", "confirmado_por"])
    w.writerows(rondas_rows)

with open(OUT / "ocorrencias.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codigo", "secao", "descricao", "reportado_por", "horario", "status"])
    w.writerows(ocorrencias_rows)

print(f"checkpoints: {len(checkpoints_rows)} linhas")
print(f"rondas: {len(rondas_rows)} linhas")
print(f"ocorrencias: {len(ocorrencias_rows)} linhas")
