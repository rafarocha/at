#!/usr/bin/env python3
"""
Gera scripts/seed_demo/{checkpoints,ocorrencias,rondas}.csv — um preenchimento BREVE e REAL (não
fictício-congelado como os samples) para colocar na planilha real (checkpoints-150ze) e poder
testar o /start pelo celular vendo o public/demo/ com alguma coisa na tela, em vez de vazio.

Cobre as 16 seções até por volta das 10:30 (T01-T13 e as 2 rondas do período da manhã — tarefas
T14 em diante são da tarde e ficam de fora de propósito), com uma mistura de situações:
  - 3 seções "boas"   (01-03): tudo em dia, fila baixa, votação adiantada.
  - 3 seções "médias"  (04-06): tudo confirmado, mas fila/votação um pouco devagar (fica "atenção").
  - 10 seções "ruins" (07-16, ~60%): motivos variados — tarefa não confirmada, ronda faltando,
    ocorrência aberta, fila grande ou votação muito atrasada.

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
# motivo de cada seção "ruim": tasks a pular, se tem ocorrência aberta (tipo), fila e votados da ronda das 10:00
SECOES_RUINS = {
    "07": {"pular": ["T13"], "ocorrencia": None, "fila": 32, "votados": 95},
    "08": {"pular": ["T09", "T11"], "ocorrencia": ("FILA", "Fila grande e mesa sem administrador para organizar."), "fila": 22, "votados": 88},
    "09": {"pular": ["T05", "T08", "T11", "T13"], "ocorrencia": None, "fila": 20, "votados": 70},
    "10": {"pular": [], "ocorrencia": ("URNA", "Urna travou na leitura, suporte técnico acionado."), "fila": 38, "votados": 60},
    "11": {"pular": ["T07"], "ocorrencia": None, "fila": 18, "votados": 82, "so_uma_ronda": True},
    "12": {"pular": ["T13"], "ocorrencia": ("ENERGIA", "Oscilação de energia, no-break ativado."), "fila": 19, "votados": 90},
    "13": {"pular": [], "ocorrencia": None, "fila": 45, "votados": 30},
    "14": {"pular": ["T03", "T06"], "ocorrencia": ("SEGURANCA", "Discussão entre eleitores na fila, mesário intervindo."), "fila": 24, "votados": 78},
    "15": {"pular": ["T04", "T07", "T09", "T12", "T13"], "ocorrencia": None, "fila": 16, "votados": 65},
    "16": {"pular": [], "ocorrencia": ("FILA", "Fila grande desde a abertura, ritmo muito lento."), "fila": 33, "votados": 55},
}

checkpoints_rows = []
rondas_rows = []
ocorrencias_rows = []

# tarefas gerais (G01-G05) — uma vez só, sem seção, todas confirmadas
for codigo, hora in TAREFAS_G:
    checkpoints_rows.append([codigo, "", "", "", "concluido", par_nomes(), carimbo(hora - 3), ""])

def add_tarefas(secao, pular):
    for codigo, hora in TAREFAS_T:
        if codigo in pular:
            continue
        obs = "" if random.random() > 0.3 else random.choice(["Tudo certo por aqui.", "Sem novidades.", ""])
        checkpoints_rows.append([codigo, secao, "", "", "concluido", par_nomes(), carimbo(hora - random.randint(1, 6)), obs])

def add_rondas(secao, fila1, votados1, fila2, votados2, obs2="", so_uma=False):
    # checklist (aba checkpoints, codigo RONDA) — usado pro aspecto "Rondas"
    checkpoints_rows.append(["RONDA", secao, "", "", "concluido", par_nomes(), carimbo(510 + random.randint(1, 6)), ""])
    rondas_rows.append([secao, hhmm(510 + random.randint(1, 6)), str(fila1), str(votados1), "sim", "", par_nomes()])
    if not so_uma:
        checkpoints_rows.append(["RONDA", secao, "", "", "concluido", par_nomes(), carimbo(600 + random.randint(1, 6)), ""])
        rondas_rows.append([secao, hhmm(600 + random.randint(1, 6)), str(fila2), str(votados2), "sim", obs2, par_nomes()])

for secao in SECOES_BOAS:
    add_tarefas(secao, pular=[])
    add_rondas(secao, fila1=random.randint(4, 9), votados1=random.randint(30, 45),
               fila2=random.randint(5, 12), votados2=random.randint(145, 165))

for secao in SECOES_MEDIAS:
    add_tarefas(secao, pular=[])
    add_rondas(secao, fila1=random.randint(6, 10), votados1=random.randint(28, 40),
               fila2=random.randint(18, 25), votados2=random.randint(95, 125),
               obs2="Fila aumentou um pouco, acompanhando.")

for secao, cfg in SECOES_RUINS.items():
    add_tarefas(secao, pular=cfg["pular"])
    add_rondas(secao, fila1=random.randint(8, 14), votados1=random.randint(25, 40),
               fila2=cfg["fila"], votados2=cfg["votados"],
               obs2="Situação sendo monitorada." if not cfg["ocorrencia"] else "",
               so_uma=cfg.get("so_uma_ronda", False))
    if cfg["ocorrencia"]:
        codigo_oc, desc = cfg["ocorrencia"]
        ocorrencias_rows.append([codigo_oc, secao, desc, par_nomes(), hhmm(random.randint(520, 600)), "aberta"])

OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "checkpoints.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codigo", "secao", "titulo", "horario_previsto", "status", "confirmado_por", "confirmado_em", "observacao"])
    w.writerows(checkpoints_rows)

with open(OUT / "rondas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["secao", "horario", "fila", "votados", "bateria_ok", "observacao", "confirmado_por"])
    w.writerows(rondas_rows)

with open(OUT / "ocorrencias.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codigo", "secao", "descricao", "reportado_por", "horario", "status"])
    w.writerows(ocorrencias_rows)

print(f"checkpoints: {len(checkpoints_rows)} linhas")
print(f"rondas: {len(rondas_rows)} linhas")
print(f"ocorrencias: {len(ocorrencias_rows)} linhas")
