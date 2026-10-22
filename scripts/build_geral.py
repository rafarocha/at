#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_geral.py — Dashboard GERAL comparando as seções.

Lê os JSONs já gerados por parse_logd.py em logs/zone/<zona>/<secao>/dados-desempenho.json
(e, se houver, dados-rdv.json) e monta uma página única public/apos/desempenho-geral.html
com gráficos comparativos: produtividade por hora, indicadores lado a lado, melhores/piores
casos e principais problemas/ganhos.

Uso:
  python3 scripts/build_geral.py
  python3 scripts/build_geral.py 328 329 330      # seções específicas (pastas em logs/zone/150/)
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ZONA_DIR = REPO / "logs" / "zone" / "150"
OUT = REPO / "public" / "apos" / "desempenho-geral.html"


def carregar(secoes):
    dados = []
    for s in secoes:
        p = ZONA_DIR / s / "dados-desempenho.json"
        if not p.exists():
            print(f"  aviso: sem dados para seção {s} ({p})")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        rdv_p = ZONA_DIR / s / "dados-rdv.json"
        rdv = json.loads(rdv_p.read_text(encoding="utf-8")) if rdv_p.exists() else None
        dados.append({"secao": s, "d": d, "rdv": rdv})
    return dados


def resumo(dados):
    """Monta um objeto compacto por seção para o frontend."""
    out = []
    for item in dados:
        d = item["d"]; a = d["agg"]; m = d["meta"]; b = d.get("boletim", {})
        # votos nulos/brancos totais do RDV (se houver)
        nulos = brancos = None
        if item["rdv"]:
            nulos = sum((c["tipos"].get("nulo", 0)) for c in item["rdv"]["cargos"])
            brancos = sum((c["tipos"].get("branco", 0)) for c in item["rdv"]["cargos"])
        out.append({
            "secao": str(b.get("secao") or item["secao"]).lstrip("0") or item["secao"],
            "eleitores": a["total_eleitores"],
            "exec_mediana_s": a["exec_mediana_s"],
            "exec_medio_s": a["exec_medio_s"],
            "espera_media_s": a["espera_media_s"],
            "espera_max_s": a["espera_max_s"],
            "bio_1a": a["taxa_biometria_1a"],
            "alertas": a["alertas"],
            "teclas": a["teclas_indevidas"],
            "teclas_por_eleitor": round(a["teclas_indevidas"] / a["total_eleitores"], 1) if a["total_eleitores"] else 0,
            "pct_tempo_perdido": a.get("pct_tempo_perdido"),
            "reacao_mediana_s": a.get("reacao_mediana_s"),
            "pronta": (m.get("pronta") or "").split(" ")[1][:5] if m.get("pronta") else "—",
            "ultimo_voto": (m.get("ultimo_voto") or "").split(" ")[1][:5] if m.get("ultimo_voto") else "—",
            "throughput": d["throughput"],
            "nulos": nulos, "brancos": brancos,
            "melhorias": d.get("melhorias", []),
        })
    return out


def main():
    secoes = sys.argv[1:] or sorted(
        p.name for p in ZONA_DIR.iterdir()
        if p.is_dir() and (p / "dados-desempenho.json").exists())
    print("seções:", secoes)
    dados = carregar(secoes)
    if not dados:
        print("nenhum dado encontrado", file=sys.stderr); sys.exit(1)
    payload = {"secoes": resumo(dados)}
    data_json = json.dumps(payload, ensure_ascii=False, indent=1)

    # abas de navegação: uma por seção (link direto para cada página de desempenho)
    tabs = "\n    ".join(
        f'<a href="desempenho-{item["secao"]}.html" class="nav-item">📈 Seção '
        f'{str((item["d"].get("boletim") or {}).get("secao") or item["secao"]).lstrip("0") or item["secao"]}</a>'
        for item in dados)

    html = (TEMPLATE
            .replace("__DADOS_JSON__", data_json)
            .replace("__SECAO_TABS__", tabs)
            .replace("__JS__", JS))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print("  escrito:", OUT.relative_to(REPO))
    tot = sum(s["eleitores"] for s in payload["secoes"])
    print(f"  {len(payload['secoes'])} seções · {tot} eleitores no total")


# ---------------------------------------------------------------------------
# O template e o JS ficam embutidos aqui para manter o script autossuficiente.
TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📊 Desempenho Geral — Comparativo das Seções</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<style>
  :root {
    --bg:#0a0e14; --bg-card:#141a24; --bg-card-2:#1a2230; --bg-chip:#19212c;
    --border:#2a3342; --fg:#eef2f7; --fg-muted:#a8b3c2; --fg-sub:#7c8798;
    --accent:#5eaaff; --accent-dim:rgba(94,170,255,.14);
    --green:#3ecf82; --green-dim:rgba(62,207,130,.14);
    --amber:#e3ab3f; --amber-dim:rgba(227,171,63,.14);
    --red:#ff6b6b; --red-dim:rgba(255,107,107,.14);
    --purple:#c792ea; --purple-dim:rgba(199,146,234,.14);
    --mono:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;
    --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--fg); font-family:var(--sans); font-size:15px; line-height:1.55; font-weight:500; padding:16px 14px 60px; }
  .wrap { max-width:1180px; margin:0 auto; }
  .top-nav { display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; }
  .nav-item { flex:1; min-width:120px; text-align:center; background:var(--bg-card); border:1px solid var(--border); border-radius:10px; padding:9px 10px; font-size:12.5px; font-weight:800; color:var(--fg-muted); text-decoration:none; }
  .nav-item.active { background:var(--accent-dim); color:var(--accent); border-color:var(--accent); }
  header.hero { background:linear-gradient(160deg,var(--bg-card),var(--bg-card-2)); border:1px solid var(--border); border-radius:16px; padding:18px 20px; margin-bottom:16px; }
  header.hero h1 { font-size:21px; font-weight:800; }
  header.hero .sub { color:var(--fg-muted); font-size:13px; font-weight:600; margin-top:6px; max-width:720px; }
  section.block { background:var(--bg-card); border:1px solid var(--border); border-radius:14px; padding:16px 16px 14px; margin-bottom:16px; }
  section.block h2 { font-size:15px; font-weight:800; margin-bottom:4px; display:flex; align-items:center; gap:7px; }
  section.block .section-sub { color:var(--fg-sub); font-size:12px; font-weight:700; margin-bottom:14px; }
  .kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
  .kpi { background:var(--bg-card-2); border:1px solid var(--border); border-radius:12px; padding:13px 14px; }
  .kpi .k-label { font-size:11px; font-weight:800; color:var(--fg-sub); text-transform:uppercase; letter-spacing:.3px; }
  .kpi .k-value { font-family:var(--mono); font-size:24px; font-weight:800; margin-top:7px; line-height:1.1; }
  .kpi .k-foot { font-size:10.5px; color:var(--fg-sub); font-weight:700; margin-top:5px; }
  .kpi.green .k-value{color:var(--green)} .kpi.red .k-value{color:var(--red)} .kpi.accent .k-value{color:var(--accent)} .kpi.amber .k-value{color:var(--amber)}
  .chart-grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:860px){ .chart-grid{grid-template-columns:1fr} }
  .chart-card { background:var(--bg-card-2); border:1px solid var(--border); border-radius:12px; padding:13px 14px 8px; }
  .chart-card .chart-title { font-size:13px; font-weight:800; margin-bottom:2px; }
  .chart-card .chart-sub { font-size:11px; color:var(--fg-sub); font-weight:700; margin-bottom:10px; }
  .chart-svg-wrap { position:relative; }
  .chart-svg-wrap svg { display:block; width:100%; height:auto; overflow:visible; }
  .chart-axis path,.chart-axis line{stroke:var(--border)} .chart-axis text{fill:var(--fg-sub);font-size:9.5px}
  .grid-line{stroke:var(--border);stroke-opacity:.4}
  .hover-tip{position:absolute;pointer-events:none;background:var(--bg-chip);border:1px solid var(--accent);border-radius:7px;padding:5px 9px;font-size:10.5px;font-weight:700;color:var(--fg);white-space:nowrap;transform:translate(-50%,-120%);z-index:20;display:none}
  .legend{display:flex;flex-wrap:wrap;gap:14px;font-size:11.5px;color:var(--fg-muted);margin-top:10px;font-weight:700}
  .legend span{display:flex;align-items:center;gap:6px}
  .legend .dot{width:11px;height:11px;border-radius:3px;display:inline-block}
  table.cmp{width:100%;border-collapse:collapse;font-size:12.5px}
  table.cmp th{text-align:left;color:var(--fg-sub);font-size:10.5px;text-transform:uppercase;letter-spacing:.3px;font-weight:800;padding:7px 9px;border-bottom:1px solid var(--border)}
  table.cmp td{padding:8px 9px;border-bottom:1px solid var(--border)}
  table.cmp td.num{font-family:var(--mono)}
  table.cmp .best{color:var(--green);font-weight:800}
  table.cmp .worst{color:var(--red);font-weight:800}
  table.cmp tr td:first-child{font-weight:800}
  .cards2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  @media (max-width:760px){.cards2{grid-template-columns:1fr}}
  .flag{background:var(--bg-card-2);border:1px solid var(--border);border-radius:11px;padding:12px 14px;margin-bottom:9px}
  .flag.win{border-left:3px solid var(--green)} .flag.prob{border-left:3px solid var(--red)}
  .flag .f-top{font-size:12.5px;font-weight:800;display:flex;justify-content:space-between;gap:10px}
  .flag .f-sec{font-family:var(--mono);color:var(--accent)}
  .flag .f-desc{font-size:11.5px;color:var(--fg-muted);margin-top:4px}
  footer.pf{text-align:center;color:var(--fg-sub);font-size:11px;font-weight:600;padding:18px 6px 4px;line-height:1.7}
  footer.pf a{color:var(--accent)} footer.pf code{font-family:var(--mono);background:var(--bg-chip);border:1px solid var(--border);border-radius:5px;padding:1px 5px}
</style>
</head>
<body>
<div class="wrap">
  <nav class="top-nav">
    <a href="../index.html" class="nav-item">🏠 Início</a>
    <a href="desempenho-geral.html" class="nav-item active">📊 Geral</a>
    __SECAO_TABS__
    <a href="rdv-e-log-de-urna.html" class="nav-item">🔎 RDV &amp; Log</a>
  </nav>

  <header class="hero">
    <h1>📊 Desempenho Geral — Comparativo das Seções</h1>
    <div class="sub">Visão consolidada do dia de votação, do início ao fim do expediente, comparando as seções do local 1465 (Zona 150). Melhores e piores casos, principais problemas e onde há mais a ganhar. Reconstruído dos Logs de Urna e RDVs.</div>
  </header>

  <section class="block">
    <h2>⚡ Panorama</h2>
    <div class="section-sub">Totais do local e os melhores/piores casos por indicador.</div>
    <div class="kpi-grid" id="kpiGrid"></div>
  </section>

  <section class="block">
    <h2>🗳️ Produtividade por hora — todas as seções</h2>
    <div class="section-sub">Eleitores atendidos em cada faixa de hora, do início ao fim do expediente. Uma linha por seção.</div>
    <div class="chart-svg-wrap"><svg id="chartLinhas" viewBox="0 0 1060 320"></svg><div class="hover-tip" id="tipLinhas"></div></div>
    <div class="legend" id="legLinhas"></div>
  </section>

  <section class="block">
    <h2>📏 Comparativo de indicadores</h2>
    <div class="section-sub">Barras lado a lado por seção. Passe o mouse para o valor.</div>
    <div class="chart-grid">
      <div class="chart-card"><div class="chart-title">⏱️ Execução mediana (s/eleitor)</div><div class="chart-sub">menor é melhor</div><div class="chart-svg-wrap"><svg id="chartExec" viewBox="0 0 520 220"></svg><div class="hover-tip" id="tipExec"></div></div></div>
      <div class="chart-card"><div class="chart-title">⏳ Espera média na fila (s)</div><div class="chart-sub">menor é melhor</div><div class="chart-svg-wrap"><svg id="chartEspera" viewBox="0 0 520 220"></svg><div class="hover-tip" id="tipEspera"></div></div></div>
      <div class="chart-card"><div class="chart-title">🖐️ Biometria na 1ª tentativa (%)</div><div class="chart-sub">maior é melhor</div><div class="chart-svg-wrap"><svg id="chartBio" viewBox="0 0 520 220"></svg><div class="hover-tip" id="tipBio"></div></div></div>
      <div class="chart-card"><div class="chart-title">⌨️ Teclas indevidas por eleitor</div><div class="chart-sub">menor é melhor</div><div class="chart-svg-wrap"><svg id="chartTeclas" viewBox="0 0 520 220"></svg><div class="hover-tip" id="tipTeclas"></div></div></div>
    </div>
  </section>

  <section class="block">
    <h2>🏁 Tabela comparativa</h2>
    <div class="section-sub">Verde = melhor caso · vermelho = pior caso de cada coluna.</div>
    <div style="overflow-x:auto"><table class="cmp" id="tabela"></table></div>
  </section>

  <section class="block">
    <h2>🎯 Principais ganhos e problemas</h2>
    <div class="section-sub">Onde cada seção se destaca (ganho) e onde precisa de atenção (problema).</div>
    <div class="cards2">
      <div><div class="chart-title" style="color:var(--green);margin-bottom:8px">✅ Ganhos (melhores casos)</div><div id="ganhos"></div></div>
      <div><div class="chart-title" style="color:var(--red);margin-bottom:8px">⚠️ Problemas (piores casos)</div><div id="problemas"></div></div>
    </div>
  </section>

  <footer class="pf">
    Gerado dos Logs de Urna + RDV · <code>scripts/build_geral.py</code> ·
    Projeto <a href="https://github.com/rafarocha/at" target="_blank" rel="noopener">at</a> · GNU GPLv3
  </footer>
</div>
<script id="dados" type="application/json">__DADOS_JSON__</script>
<script>__JS__</script>
</body>
</html>
"""

JS = r"""
(function(){
  "use strict";
  const CORES=["#5eaaff","#3ecf82","#c792ea","#e3ab3f","#ff6b6b","#6bd6c9"];
  const S=JSON.parse(document.getElementById("dados").textContent).secoes;
  const secStr=(s)=> s==null?"—":(s<60?Math.round(s)+"s":Math.floor(s/60)+"min"+(Math.round(s%60)?" "+Math.round(s%60)+"s":""));
  const M={top:16,right:16,bottom:30,left:42};
  function dims(svg){const vb=svg.getAttribute("viewBox").split(" ").map(Number);return{w:vb[2],h:vb[3],iw:vb[2]-M.left-M.right,ih:vb[3]-M.top-M.bottom};}
  function tip(id,px,py,html,svg){const t=document.getElementById(id);const wrap=svg.parentNode;const d=dims(svg);t.innerHTML=html;t.style.display="block";t.style.left=px*(wrap.clientWidth/d.w)+"px";t.style.top=py*(wrap.clientHeight/d.h)+"px";}
  function hide(id){document.getElementById(id).style.display="none";}

  // ---- Panorama (KPIs: totais + melhor/pior) ----
  const totalEleitores=S.reduce((a,s)=>a+s.eleitores,0);
  const best=(key,menor)=>S.slice().sort((a,b)=>menor?a[key]-b[key]:b[key]-a[key])[0];
  const worst=(key,menor)=>S.slice().sort((a,b)=>menor?b[key]-a[key]:a[key]-b[key])[0];
  const kpis=[
    {cls:"accent",label:"Seções",value:S.length,foot:totalEleitores+" eleitores no total"},
    {cls:"green",label:"Mais rápida (execução)",value:"Seção "+best("exec_mediana_s",true).secao,foot:secStr(best("exec_mediana_s",true).exec_mediana_s)+" mediana"},
    {cls:"green",label:"Melhor biometria 1ª",value:"Seção "+best("bio_1a",false).secao,foot:best("bio_1a",false).bio_1a+"% na 1ª tentativa"},
    {cls:"red",label:"Mais alertas",value:"Seção "+worst("alertas",true).secao,foot:worst("alertas",true).alertas+" alertas no dia"},
    {cls:"amber",label:"Maior espera na fila",value:"Seção "+worst("espera_media_s",true).secao,foot:secStr(worst("espera_media_s",true).espera_media_s)+" em média"},
    {cls:"red",label:"Mais teclas indevidas",value:"Seção "+worst("teclas_por_eleitor",true).secao,foot:worst("teclas_por_eleitor",true).teclas_por_eleitor+" por eleitor"},
  ];
  document.getElementById("kpiGrid").innerHTML=kpis.map(k=>`<div class="kpi ${k.cls}"><div class="k-label">${k.label}</div><div class="k-value">${k.value}</div><div class="k-foot">${k.foot}</div></div>`).join("");

  // ---- Produtividade por hora (multilinha) ----
  (function(){
    const svg=d3.select("#chartLinhas"),el=svg.node(),{ih,iw}=dims(el);
    const horas=Array.from(new Set(S.flatMap(s=>s.throughput.map(t=>t.hora)))).sort((a,b)=>a-b);
    const g=svg.append("g").attr("transform",`translate(${M.left},${M.top})`);
    const x=d3.scalePoint().domain(horas).range([0,iw]).padding(0.3);
    const ymax=d3.max(S,s=>d3.max(s.throughput,t=>t.votos))*1.12;
    const y=d3.scaleLinear().domain([0,ymax]).range([ih,0]);
    y.ticks(5).forEach(t=>g.append("line").attr("class","grid-line").attr("x1",0).attr("x2",iw).attr("y1",y(t)).attr("y2",y(t)));
    g.append("g").attr("class","chart-axis").attr("transform",`translate(0,${ih})`).call(d3.axisBottom(x).tickFormat(h=>h+"h"));
    g.append("g").attr("class","chart-axis").call(d3.axisLeft(y).ticks(5));
    const line=d3.line().x(t=>x(t.hora)).y(t=>y(t.votos)).curve(d3.curveMonotoneX);
    S.forEach((s,i)=>{
      const c=CORES[i%CORES.length];
      g.append("path").datum(s.throughput).attr("fill","none").attr("stroke",c).attr("stroke-width",2.2).attr("d",line);
      g.selectAll(".dot"+i).data(s.throughput).enter().append("circle").attr("cx",t=>x(t.hora)).attr("cy",t=>y(t.votos)).attr("r",3).attr("fill",c)
        .on("mousemove",(e,t)=>tip("tipLinhas",M.left+x(t.hora),M.top+y(t.votos),`<b>Seção ${s.secao}</b> · ${t.hora}h · ${t.votos} eleitores`,el))
        .on("mouseleave",()=>hide("tipLinhas"));
    });
    document.getElementById("legLinhas").innerHTML=S.map((s,i)=>`<span><span class="dot" style="background:${CORES[i%CORES.length]}"></span>Seção ${s.secao} · abre ${s.pronta} → último voto ${s.ultimo_voto}</span>`).join("");
  })();

  // ---- barras comparativas ----
  function barras(svgId,tipId,key,fmt,menorMelhor,cor){
    const svg=d3.select("#"+svgId),el=svg.node(),{ih,iw}=dims(el);
    const g=svg.append("g").attr("transform",`translate(${M.left},${M.top})`);
    const x=d3.scaleBand().domain(S.map(s=>s.secao)).range([0,iw]).padding(0.35);
    const vals=S.map(s=>s[key]);
    const y=d3.scaleLinear().domain([0,d3.max(vals)*1.18]).range([ih,0]);
    const melhor=menorMelhor?d3.min(vals):d3.max(vals), pior=menorMelhor?d3.max(vals):d3.min(vals);
    y.ticks(4).forEach(t=>g.append("line").attr("class","grid-line").attr("x1",0).attr("x2",iw).attr("y1",y(t)).attr("y2",y(t)));
    g.append("g").attr("class","chart-axis").attr("transform",`translate(0,${ih})`).call(d3.axisBottom(x).tickFormat(s=>"Seção "+s));
    g.append("g").attr("class","chart-axis").call(d3.axisLeft(y).ticks(4));
    g.selectAll("rect").data(S).enter().append("rect")
      .attr("x",s=>x(s.secao)).attr("width",x.bandwidth())
      .attr("y",s=>y(s[key])).attr("height",s=>ih-y(s[key])).attr("rx",3)
      .attr("fill",s=> s[key]===melhor?"var(--green)": s[key]===pior?"var(--red)": cor)
      .on("mousemove",(e,s)=>tip(tipId,M.left+x(s.secao)+x.bandwidth()/2,M.top+y(s[key]),`Seção ${s.secao}: <b>${fmt(s[key])}</b>`,el))
      .on("mouseleave",()=>hide(tipId));
    g.selectAll("text.v").data(S).enter().append("text").attr("class","v")
      .attr("x",s=>x(s.secao)+x.bandwidth()/2).attr("y",s=>y(s[key])-5).attr("text-anchor","middle")
      .attr("fill","var(--fg-muted)").attr("font-size","10px").attr("font-weight","800").text(s=>fmt(s[key]));
  }
  barras("chartExec","tipExec","exec_mediana_s",secStr,true,"var(--accent)");
  barras("chartEspera","tipEspera","espera_media_s",v=>secStr(Math.round(v)),true,"var(--amber)");
  barras("chartBio","tipBio","bio_1a",v=>v+"%",false,"var(--accent)");
  barras("chartTeclas","tipTeclas","teclas_por_eleitor",v=>v,true,"var(--purple)");

  // ---- tabela comparativa ----
  (function(){
    const cols=[
      {k:"eleitores",t:"Eleitores",menor:null,fmt:v=>v},
      {k:"pronta",t:"Abertura",menor:null,fmt:v=>v},
      {k:"ultimo_voto",t:"Último voto",menor:null,fmt:v=>v},
      {k:"exec_mediana_s",t:"Exec. mediana",menor:true,fmt:secStr},
      {k:"espera_media_s",t:"Espera média",menor:true,fmt:v=>secStr(Math.round(v))},
      {k:"bio_1a",t:"Biometria 1ª",menor:false,fmt:v=>v+"%"},
      {k:"teclas_por_eleitor",t:"Teclas/eleitor",menor:true,fmt:v=>v},
      {k:"alertas",t:"Alertas",menor:true,fmt:v=>v},
      {k:"pct_tempo_perdido",t:"% tempo perdido",menor:true,fmt:v=>v==null?"—":v+"%"},
    ];
    const t=document.getElementById("tabela");
    const head="<tr><th>Seção</th>"+cols.map(c=>`<th>${c.t}</th>`).join("")+"</tr>";
    const bestOf={},worstOf={};
    cols.forEach(c=>{ if(c.menor===null)return; const vals=S.map(s=>s[c.k]).filter(v=>v!=null);
      bestOf[c.k]=c.menor?Math.min(...vals):Math.max(...vals); worstOf[c.k]=c.menor?Math.max(...vals):Math.min(...vals); });
    const rows=S.map(s=>"<tr><td>Seção "+s.secao+"</td>"+cols.map(c=>{
      let cls=""; if(c.menor!==null){ if(s[c.k]===bestOf[c.k])cls="best"; else if(s[c.k]===worstOf[c.k])cls="worst"; }
      return `<td class="num ${cls}">${c.fmt(s[c.k])}</td>`; }).join("")+"</tr>").join("");
    t.innerHTML=head+rows;
  })();

  // ---- ganhos / problemas ----
  (function(){
    const g=[
      {sec:bestSec("exec_mediana_s",true),txt:"atendimento mais rápido",val:s=>secStr(s.exec_mediana_s)+" de execução mediana"},
      {sec:bestSec("bio_1a",false),txt:"melhor biometria",val:s=>s.bio_1a+"% na 1ª tentativa"},
      {sec:bestSec("espera_media_s",true),txt:"menor espera na fila",val:s=>secStr(Math.round(s.espera_media_s))+" em média"},
      {sec:bestSec("teclas_por_eleitor",true),txt:"eleitores mais seguros",val:s=>s.teclas_por_eleitor+" teclas indevidas por eleitor"},
    ];
    const p=[
      {sec:worstSec("alertas",true),txt:"mais alertas no dia",val:s=>s.alertas+" alertas (conferir identificador digitado)"},
      {sec:worstSec("bio_1a",false),txt:"biometria mais falha",val:s=>s.bio_1a+"% na 1ª — limpar leitor e orientar o dedo"},
      {sec:worstSec("espera_media_s",true),txt:"maior espera na fila",val:s=>secStr(Math.round(s.espera_media_s))+" — já habilitar o próximo ao terminar"},
      {sec:worstSec("teclas_por_eleitor",true),txt:"mais teclas indevidas",val:s=>s.teclas_por_eleitor+" por eleitor — orientar na cabine"},
    ];
    document.getElementById("ganhos").innerHTML=g.map(x=>`<div class="flag win"><div class="f-top"><span>${x.txt}</span><span class="f-sec">Seção ${x.sec.secao}</span></div><div class="f-desc">${x.val(x.sec)}</div></div>`).join("");
    document.getElementById("problemas").innerHTML=p.map(x=>`<div class="flag prob"><div class="f-top"><span>${x.txt}</span><span class="f-sec">Seção ${x.sec.secao}</span></div><div class="f-desc">${x.val(x.sec)}</div></div>`).join("");
    function bestSec(k,menor){return S.slice().sort((a,b)=>menor?a[k]-b[k]:b[k]-a[k])[0];}
    function worstSec(k,menor){return S.slice().sort((a,b)=>menor?b[k]-a[k]:a[k]-b[k])[0];}
  })();
})();
"""

if __name__ == "__main__":
    main()
