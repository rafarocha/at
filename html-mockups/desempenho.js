/* desempenho.js — painel de desempenho da seção a partir do Log de Urna.
   Lê os dados de um <script type="application/json" id="dadosDesempenho"> embutido
   (preenchido pelo build) ou, em fallback, faz fetch() de dados-desempenho.json. */
(function () {
  "use strict";

  const fmt = (n) => (n == null ? "—" : n.toLocaleString("pt-BR"));
  const secStr = (s) => {
    if (s == null) return "—";
    if (s < 60) return s + "s";
    const m = Math.floor(s / 60), r = Math.round(s % 60);
    return m + "min" + (r ? " " + r + "s" : "");
  };
  const hhmm = (str) => (str ? str.split(" ")[1].slice(0, 5) : "—");
  const hhmmss = (str) => (str ? str.split(" ")[1] : "—");
  const dateStr = (str) => (str ? str.split(" ")[0] : "—");

  // ---- popup ----------------------------------------------------------------
  const overlay = document.getElementById("overlay");
  function openPopup({ icon, kicker, title, html }) {
    document.getElementById("popIcon").textContent = icon || "📊";
    document.getElementById("popKicker").textContent = kicker || "INDICADOR";
    document.getElementById("popTitle").textContent = title || "";
    document.getElementById("popBody").innerHTML = html || "";
    overlay.style.display = "flex";
  }
  function closePopup() { overlay.style.display = "none"; }
  document.getElementById("popClose").addEventListener("click", closePopup);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) closePopup(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closePopup(); });

  function insight(title, body) {
    return `<div class="pop-insight"><div class="pi-title">💡 ${title}</div>${body}</div>`;
  }
  function links(arr) {
    return `<div class="pop-foot">${arr.map((l) =>
      l.href ? `<a class="pop-link" href="${l.href}" target="_blank" rel="noopener">${l.text} →</a>`
             : `<span class="pop-tag">${l.text}</span>`).join("")}</div>`;
  }

  // ---- carregar dados -------------------------------------------------------
  function loadData() {
    const el = document.getElementById("dadosDesempenho");
    const raw = el ? el.textContent.trim() : "";
    if (raw && raw[0] === "{") {
      try { return Promise.resolve(JSON.parse(raw)); } catch (e) { /* cai no fetch */ }
    }
    return fetch("dados-desempenho.json").then((r) => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  loadData().then(render).catch((err) => {
    document.getElementById("statusBadge").textContent = "⚠️ não foi possível ler o log";
    console.error(err);
  });

  // ===========================================================================
  function render(d) {
    const agg = d.agg, meta = d.meta, voters = d.voters || [];
    document.getElementById("footSrc").textContent = d.fonte || "logd.dat";
    document.getElementById("footGen").textContent = d.gerado_em || "—";

    const diaVoto = meta.ultimo_voto ? meta.ultimo_voto.split(" ")[0] : "—";
    document.getElementById("statusBadge").textContent = "✅ " + agg.total_eleitores + " eleitores · " + diaVoto;

    // meta chips
    const chips = [
      ["Urna", meta.urna],
      ["App", (meta.versao || "").split(" - ")[0]],
      ["Abertura", hhmm(meta.pronta)],
      ["Encerramento", hhmm(meta.encerramento)],
      ["1º voto", hhmm(meta.primeiro_voto)],
      ["Último voto", hhmm(meta.ultimo_voto)],
    ];
    document.getElementById("metaChips").innerHTML = chips
      .map(([k, v]) => `<span class="meta-chip">${k}: <b>${v || "—"}</b></span>`).join("");

    renderBoletim(d);
    renderKPIs(d);
    renderMelhorias(d);
    renderThroughput(d);
    renderExecHora(d);
    renderBio(d);
    renderBioHora(d);
    renderWait(d);
    renderReacao(d);
    renderPresInicio(d);
    renderPresHabilita(d);
    renderEsperaHora(d);
    renderOciosidade(d);
    renderTeclasEleitor(d);
    renderTeclasHora(d);
    renderEventos(d);
    renderIndesejaveis(d);
    renderRdv(d);
    renderCumulative(d);
    renderAlerts(d);
  }

  // ---- Boletim de Urna (guia de contexto no cabeçalho) ----------------------
  function renderBoletim(d) {
    const b = d.boletim; if (!b) return;
    document.getElementById("buCard").style.display = "";
    // remove zeros à esquerda para exibição (ex.: "0329" -> "329", "0150" -> "150")
    const semZero = (v) => (v == null || v === "" ? "—" : String(v).replace(/^0+(?=\d)/, ""));
    const mun = b.municipio || "—";
    document.getElementById("buLoc").firstChild.nodeValue = "Município " + mun + " · PE";
    document.getElementById("buLocSub").textContent = "Zona " + semZero(b.zona) + " · Seção " + semZero(b.secao) + " · Local " + semZero(b.local);
    document.getElementById("buTurno").textContent = (b.turno || "1º turno").replace(" turno", "");
    document.getElementById("buAbertura").textContent = b.abertura_ue || "—";
    document.getElementById("buFechamento").textContent = b.fechamento_ue || "—";
    document.getElementById("buModelo").textContent = b.modelo || "—";
    document.getElementById("buCodigo").textContent = b.codigo_ue || "—";
    document.getElementById("buMun").textContent = mun;
    document.getElementById("buZona").textContent = semZero(b.zona);
    document.getElementById("buLocal").textContent = semZero(b.local);
    document.getElementById("buSecao").textContent = semZero(b.secao);

    const pad = (n) => (n == null ? "—" : String(n).padStart(4, "0"));
    // quando o Boletim de Urna não foi coletado (sem aptos), a habilitação não-biométrica
    // é derivada do log (comparecimento − biométrica) e mostrada num único cartão.
    const temBU = b.eleitores_aptos != null;
    const cells = [
      { l: "👥 Eleitores aptos", v: pad(b.eleitores_aptos), hl: false,
        help: temBU ? "Total de eleitores habilitados a votar nesta seção (fonte: Boletim de Urna)."
                    : "Não disponível: o Boletim de Urna (bu.dat) desta seção não foi coletado. Este número não aparece no Log de Urna." },
      { l: "✅ Comparecimento", v: pad(b.comparecimento), hl: true,
        help: "Eleitores que efetivamente votaram — igual ao total de votos computados no log (" + fmt(b.comparecimento) + "). Extraído do próprio log." },
      { l: "🚫 Faltosos", v: pad(b.eleitores_faltosos), hl: false,
        help: temBU ? "Aptos que não compareceram (" + pad(b.eleitores_aptos) + " aptos − " + pad(b.comparecimento) + " comparecimento). Fonte: Boletim de Urna."
                    : "Não disponível sem o Boletim de Urna (depende do total de aptos, que só o BU traz)." },
      { l: "📊 % comparecimento", v: (b.pct_comparecimento != null ? b.pct_comparecimento + "%" : "—"), hl: true,
        help: temBU ? "Comparecimento sobre aptos. Útil para comparar seções."
                    : "Não calculável sem o total de aptos (Boletim de Urna)." },
      { l: "🖐️ Habilitação biométrica", v: pad(b.habilitacao_biometrica), hl: false,
        help: "Eleitores identificados pela digital (contado direto no log: " + fmt(b.habilitacao_biometrica) + " eventos de habilitação biométrica)." },
    ];
    if (temBU) {
      cells.push(
        { l: "📷 Habilitação biográfica", v: pad(b.habilitacao_biografica), hl: false,
          help: "Identificação por foto/dados (sem leitura de digital válida). Fonte: Boletim de Urna." },
        { l: "⌨️ Sem biometria", v: pad(b.habilitacao_sem_biometria), hl: false,
          help: "Habilitação manual pelo mesário, sem biometria. Fonte: Boletim de Urna." },
        { l: "🗳️ Aptos originais", v: pad(b.eleitores_aptos_originais), hl: false,
          help: "Aptos antes de inclusões temporárias (temporários: " + pad(b.eleitores_aptos_temporarios) + "). Fonte: Boletim de Urna." });
    } else {
      cells.push(
        { l: "⌨️ Hab. não-biométrica", v: pad(b.habilitacao_nao_biometrica), hl: false,
          help: "Derivado do log: comparecimento (" + fmt(b.comparecimento) + ") − habilitação biométrica (" + fmt(b.habilitacao_biometrica) + "). Reúne biográfica + sem biometria, que só o Boletim de Urna separa." });
    }
    const grid = document.getElementById("buGrid");
    grid.innerHTML = cells.map((c, i) => `
      <div class="bu-cell ${c.hl ? "hl" : ""}" data-i="${i}">
        <div class="bc-label">${c.l}</div>
        <div class="bc-value">${c.v}</div>
      </div>`).join("");
    grid.querySelectorAll(".bu-cell").forEach((el) => {
      el.style.cursor = "pointer";
      el.addEventListener("click", () => {
        const c = cells[+el.dataset.i];
        openPopup({ icon: "📋", kicker: "BOLETIM DE URNA", title: c.l.replace(/^\S+\s/, ""),
          html: `<div class="pop-metric">${c.v}</div><p>${c.help}</p>` });
      });
    });
  }

  // ---- KPIs -----------------------------------------------------------------
  function renderKPIs(d) {
    const a = d.agg;
    const horas = d.throughput.length;
    const velPorHora = horas ? Math.round(a.total_eleitores / horas) : 0;
    const kpis = [
      { cls: "accent", icon: "🗳️", label: "Eleitores", value: fmt(a.total_eleitores), unit: "no dia",
        foot: "≈ " + velPorHora + " por hora",
        pop: { icon: "🗳️", kicker: "PRODUTIVIDADE", title: "Total de eleitores atendidos",
          html: `<div class="pop-metric">${fmt(a.total_eleitores)}</div>
            <p>Votos efetivamente <b>computados</b> nesta urna no dia. É a soma de todas as
            sessões concluídas (evento <b>“O voto do eleitor foi computado”</b>).</p>
            ${insight("Leitura", "Com atendimento das <b>8h às ~18h</b>, isso dá cerca de <b>" + velPorHora + " eleitores/hora</b>. Compare com seções vizinhas para calibrar sua fila.")}` } },
      { cls: "accent", icon: "⏱️", label: "Execução média", value: secStr(Math.round(a.exec_medio_s)), unit: "",
        foot: "mediana " + secStr(a.exec_mediana_s),
        pop: { icon: "⏱️", kicker: "TEMPO", title: "Tempo médio de execução por eleitor",
          html: `<div class="pop-metric">${secStr(Math.round(a.exec_medio_s))}</div>
            <p>Da <b>habilitação</b> até o <b>voto computado</b> — ou seja, o tempo que o eleitor passa
            na cabine digitando. A <b>mediana</b> (${secStr(a.exec_mediana_s)}) é mais justa que a média,
            pois ignora os poucos casos muito longos (máx. ${secStr(a.exec_max_s)}).</p>
            ${insight("O que o presidente pode fazer", `<ul style="margin:0;padding-left:16px;">
              <li>Tempo alto costuma ser eleitor com dúvida nas teclas. Um cartaz grande com a <b>ordem dos cargos</b> ao lado da urna reduz esse tempo.</li>
              <li><b>Gatilho de 10 segundos:</b> se o eleitor ficar <b>10s sem apertar nenhuma tecla</b>, aproximar-se e puxar conversa — perguntar sobre a demora, se tem dúvida ou precisa de ajuda. Pega travamentos cedo, antes de virarem minutos.</li>
              <li><b>Na fila:</b> para pessoas menos familiarizadas com a urna, o secretário pode mostrar o <a href="https://www.tse.jus.br/eleicoes/simulador-de-votacao" target="_blank" rel="noopener">simulador de votação do TSE</a> enquanto esperam — chegam na cabine já sabendo o fluxo, e o tempo de execução cai.</li>
            </ul>`)}` } },
      { cls: "accent", icon: "⚡", label: "Reação do eleitor", value: secStr(Math.round(a.reacao_media_s)), unit: "",
        foot: "mediana " + secStr(a.reacao_mediana_s),
        pop: { icon: "⚡", kicker: "TEMPO", title: "Tempo de reação do eleitor",
          html: `<div class="pop-metric">${secStr(Math.round(a.reacao_media_s))}</div>
            <p>Tempo entre a <b>habilitação</b> e a <b>1ª ação do eleitor na cabine</b> (primeiro voto
            confirmado, ou primeira tecla). Mede quanto o eleitor demora a <b>começar</b> a votar depois de liberado.
            Mediana <b>${secStr(a.reacao_mediana_s)}</b>, máximo <b>${secStr(a.reacao_max_s)}</b>.</p>
            ${insight("Leitura", "Reação alta = eleitor lendo instruções/ se situando. Um lembrete do mesário (<b>“pode começar, digite o número”</b>) ao liberar a cabine encurta esse tempo.")}` } },
      { cls: "green", icon: "🖐️", label: "Biometria 1ª tentativa", value: a.taxa_biometria_1a + "%", unit: "",
        foot: a.eleitores_multi_tentativa + " precisaram repetir",
        pop: { icon: "🖐️", kicker: "BIOMETRIA", title: "Identificação na 1ª tentativa",
          html: `<div class="pop-metric">${a.taxa_biometria_1a}%</div>
            <p>Percentual de eleitores cuja digital foi aceita <b>de primeira</b>. Foram
            <b>${a.tentativas_biometricas}</b> solicitações de digital no total; <b>${a.eleitores_multi_tentativa}</b>
            eleitores precisaram de mais de uma.</p>
            ${insight("Referência nacional", "O Brasil tem <b>89%</b> do eleitorado com biometria e a <b>PB é o 4º estado</b> (96,33%). Muitas repetições → oriente o eleitor a limpar o dedo e pressionar sem arrastar.")}` } },
      { cls: "amber", icon: "⏳", label: "Espera média (fila)", value: secStr(Math.round(a.espera_media_s)), unit: "",
        foot: "pico de " + secStr(a.espera_max_s),
        pop: { icon: "⏳", kicker: "ESPERA / OCIOSIDADE", title: "Espera entre eleitores",
          html: `<div class="pop-metric">${secStr(Math.round(a.espera_media_s))}</div>
            <p>Tempo <b>ocioso da urna</b>: do voto computado de um eleitor até o próximo ser identificado
            pelo mesário. Pico de <b>${secStr(a.espera_max_s)}</b> (provável troca de turno ou fila vazia).</p>
            ${insight("Dica de fluxo", "Espera alta com fila cheia = gargalo na mesa de identificação. Ter o <b>caderno/título em mãos</b> antes de chamar o eleitor derruba esse número.")}` } },
      { cls: "red", icon: "⚠️", label: "Alertas", value: fmt(a.alertas), unit: "no log",
        foot: "ver linha do tempo",
        pop: { icon: "⚠️", kicker: "QUALIDADE", title: "Alertas registrados",
          html: `<div class="pop-metric">${fmt(a.alertas)}</div>
            <p>Eventos de severidade <b>ALERTA</b>. A maioria é <b>“identificador digitado inválido”</b>
            — digitação errada do título/documento, corrigida em seguida. Não são falhas da urna.</p>
            ${insight("Leitura", "Role até a seção <b>Alertas</b> abaixo para ver cada um com horário. Picos de alerta costumam coincidir com horários de pico de fila.")}` } },
      { cls: "purple", icon: "👆", label: "Teclas indevidas", value: fmt(a.teclas_indevidas), unit: "",
        foot: "≈ " + (a.total_eleitores ? (a.teclas_indevidas / a.total_eleitores).toFixed(1) : 0) + " por eleitor",
        pop: { icon: "👆", kicker: "USABILIDADE", title: "Teclas indevidas pressionadas",
          html: `<div class="pop-metric">${fmt(a.teclas_indevidas)}</div>
            <p>Toques em teclas que não valem naquele momento (ex.: apertar número durante uma tela de
            confirmação). São <b>inofensivos</b> — a urna ignora — mas indicam <b>insegurança</b> do eleitor.</p>
            ${insight("O que o presidente pode fazer", "Volume alto reforça o valor de orientar o eleitor: <b>“digite o número, confira a foto, aperte VERDE”</b>. Isso também reduz o tempo de execução.")}` } },
    ];
    const grid = document.getElementById("kpiGrid");
    grid.innerHTML = kpis.map((k, i) => `
      <div class="kpi ${k.cls}" data-i="${i}">
        <div class="k-label">${k.icon} ${k.label}<span class="info-i">i</span></div>
        <div class="k-value">${k.value} <span class="k-unit">${k.unit}</span></div>
        <div class="k-foot">${k.foot}</div>
      </div>`).join("");
    grid.querySelectorAll(".kpi").forEach((el) =>
      el.addEventListener("click", () => openPopup(kpis[+el.dataset.i].pop)));
  }

  // ---- Plano de melhoria: radial top-5 + lista ------------------------------
  const MELH_CORES = ["var(--red)", "var(--amber)", "var(--accent)", "var(--purple)", "var(--green)"];
  function renderMelhorias(d) {
    const itens = d.melhorias || [];
    if (!itens.length) return;

    // --- gráfico radial (barras polares; raio ∝ score) ---
    const svg = d3.select("#chartMelhoriasRadial"); const el = svg.node();
    const W = 300, H = 300, cx = W / 2, cy = H / 2;
    const rMin = 34, rMax = 120;
    const g = svg.append("g").attr("transform", `translate(${cx},${cy})`);
    const n = itens.length;
    const ang = (2 * Math.PI) / n;
    const rScale = d3.scaleLinear().domain([0, 100]).range([rMin, rMax]);
    // anéis de referência (25/50/75/100)
    [25, 50, 75, 100].forEach((t) => {
      g.append("circle").attr("r", rScale(t)).attr("fill", "none")
        .attr("stroke", "var(--border)").attr("stroke-opacity", .5).attr("stroke-dasharray", "2,3");
    });
    const arc = d3.arc().innerRadius(rMin).padAngle(0.04).cornerRadius(3);
    const slices = g.selectAll("path.melh").data(itens).enter().append("path")
      .attr("class", "melh dot-clickable")
      .attr("d", (m, i) => arc({
        startAngle: i * ang, endAngle: (i + 1) * ang,
        outerRadius: rScale(m.score), innerRadius: rMin,
      }))
      .attr("fill", (m, i) => MELH_CORES[i % MELH_CORES.length])
      .attr("fill-opacity", .85)
      .on("mousemove", function (e, m) {
        const i = itens.indexOf(m);
        const wrap = el.parentNode, sx = wrap.clientWidth / W, sy = wrap.clientHeight / H;
        const mid = (i + 0.5) * ang - Math.PI / 2, rr = (rMin + rScale(m.score)) / 2;
        const tip = document.getElementById("tipMelhoriasRadial");
        tip.innerHTML = `<b>${m.score}</b> · ${m.metrica}`;
        tip.style.display = "block";
        tip.style.left = (cx + Math.cos(mid) * rr) * sx + "px";
        tip.style.top = (cy + Math.sin(mid) * rr) * sy + "px";
        highlight(i);
      })
      .on("mouseleave", () => { document.getElementById("tipMelhoriasRadial").style.display = "none"; highlight(-1); })
      .on("click", (e, m) => openMelhPopup(m, itens.indexOf(m)));
    // rótulo do nº da ação no centro de cada fatia
    g.selectAll("text.melhnum").data(itens).enter().append("text").attr("class", "melhnum")
      .attr("transform", (m, i) => {
        const mid = (i + 0.5) * ang - Math.PI / 2, rr = rScale(m.score) + 10;
        return `translate(${Math.cos(mid) * rr},${Math.sin(mid) * rr})`;
      })
      .attr("text-anchor", "middle").attr("dominant-baseline", "middle")
      .attr("fill", "var(--fg-muted)").attr("font-size", "10px").attr("font-weight", "800")
      .text((m, i) => (i + 1) + "º");
    g.append("text").attr("text-anchor", "middle").attr("dy", "0.35em")
      .attr("fill", "var(--fg-sub)").attr("font-size", "9px").attr("font-weight", "800").text("AÇÕES");

    // --- lista ao lado ---
    const box = document.getElementById("planoLista");
    box.innerHTML = itens.map((m, i) => `
      <div class="plano-item" data-i="${i}">
        <div class="plano-rank">${i + 1}º</div>
        <div class="plano-body">
          <div class="plano-acao"><span class="pa-ico">${m.icone}</span>${m.acao}</div>
          <div class="plano-meta"><span class="pm-para">${m.para}</span> · ${m.metrica}</div>
          <div class="plano-ev">📊 ${m.evidencia}</div>
        </div>
        <div class="plano-bar">
          <span class="pb-score" style="color:${MELH_CORES[i % MELH_CORES.length]}">${m.score}</span>
          <div class="pb-track"><div class="pb-fill" style="width:${m.score}%;background:${MELH_CORES[i % MELH_CORES.length]}"></div></div>
        </div>
      </div>`).join("");
    const rows = box.querySelectorAll(".plano-item");
    rows.forEach((r) => {
      r.addEventListener("click", () => openMelhPopup(itens[+r.dataset.i], +r.dataset.i));
      r.addEventListener("mouseenter", () => highlight(+r.dataset.i));
      r.addEventListener("mouseleave", () => highlight(-1));
    });
    function highlight(i) {
      slices.attr("fill-opacity", (m, j) => (i < 0 || j === i) ? .85 : .25);
      rows.forEach((r, j) => r.classList.toggle("active", j === i));
    }
  }
  function openMelhPopup(m, i) {
    openPopup({
      icon: m.icone, kicker: (i + 1) + "ª PRIORIDADE · " + m.para,
      title: m.acao,
      html: `<div class="pop-metric">${m.score}<span style="font-size:14px;color:var(--fg-muted)"> / 100 prioridade</span></div>
        <p>Base nos dados desta urna: <b>${m.evidencia}</b>.</p>
        ${insight("Como agir", "Quanto maior a pontuação, mais este ponto pesou na seção. É uma ação concreta que o " + m.para.toLowerCase() + " pode adotar na próxima eleição para reduzir o indicador de <b>" + m.metrica + "</b>.")}`
    });
  }

  // ---- helpers de eixo ------------------------------------------------------
  const M = { top: 14, right: 14, bottom: 28, left: 38 };
  function dims(svg) {
    const vb = svg.getAttribute("viewBox").split(" ").map(Number);
    return { w: vb[2], h: vb[3], iw: vb[2] - M.left - M.right, ih: vb[3] - M.top - M.bottom };
  }
  function tipFor(svg) { return document.getElementById("tip" + svg.id.replace("chart", "")); }
  function showTip(svg, px, py, html) {
    const tip = tipFor(svg); const wrap = svg.parentNode;
    const scaleX = wrap.clientWidth / dims(svg).w;
    tip.innerHTML = html; tip.style.display = "block";
    tip.style.left = px * scaleX + "px"; tip.style.top = py * (wrap.clientHeight / dims(svg).h) + "px";
  }
  function hideTip(svg) { tipFor(svg).style.display = "none"; }

  // ---- 1) throughput por hora (barras) --------------------------------------
  function renderThroughput(d) {
    const svg = d3.select("#chartThroughput"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = d.throughput;
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleBand().domain(data.map((v) => v.hora)).range([0, iw]).padding(0.22);
    const y = d3.scaleLinear().domain([0, d3.max(data, (v) => v.votos) * 1.15]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`)
      .call(d3.axisBottom(x).tickFormat((h) => h + "h"));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4));
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("x", (v) => x(v.hora)).attr("width", x.bandwidth())
      .attr("y", (v) => y(v.votos)).attr("height", (v) => ih - y(v.votos))
      .attr("rx", 3).attr("fill", "var(--accent)")
      .on("mousemove", (e, v) => showTip(el, M.left + x(v.hora) + x.bandwidth() / 2, M.top + y(v.votos), `<b>${v.votos}</b> eleitores · ${v.hora}h`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "🗳️", kicker: "PRODUTIVIDADE · " + v.hora + "h", title: "Eleitores entre " + v.hora + "h e " + (v.hora + 1) + "h",
        html: `<div class="pop-metric">${v.votos}</div>
          <p>Votos computados nesta faixa de hora. O pico do dia foi de
          <b>${d3.max(data, (k) => k.votos)}</b> eleitores/hora.</p>
          ${insight("Leitura", v.votos >= d3.max(data, (k) => k.votos) * 0.9 ? "Esta foi uma das <b>horas de pico</b> — reforce mesários na identificação neste horário." : "Fluxo abaixo do pico — bom momento para pausas e trocas de turno.")}`
      }));
  }

  // ---- 2) tempo de execução ao longo do dia (eixo de horas + tendência) -----
  function renderExecHora(d) {
    const svg = d3.select("#chartExecHora"); const el = svg.node();
    const { ih, iw } = dims(el);
    const parse = d3.timeParse("%d/%m/%Y %H:%M:%S");
    const data = d.voters.filter((v) => v.exec_s != null && v.computado)
      .map((v) => ({ ...v, t: parse(v.computado) }));
    const med = d.agg.exec_mediana_s;
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleTime().domain(d3.extent(data, (v) => v.t)).range([0, iw]);
    const y = d3.scaleLinear().domain([0, d3.max(data, (v) => v.exec_s) * 1.1]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat("%H:%M")));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4).tickFormat((v) => v + "s"));
    // mediana de referência
    g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(med)).attr("y2", y(med))
      .attr("stroke", "var(--green)").attr("stroke-dasharray", "4,3").attr("stroke-width", 1.2);
    // pontos
    g.selectAll("circle").data(data).enter().append("circle")
      .attr("class", "dot-clickable").attr("cx", (v) => x(v.t)).attr("cy", (v) => y(v.exec_s)).attr("r", 2.4)
      .attr("fill", (v) => v.exec_s > med * 2 ? "var(--red)" : v.exec_s > med * 1.3 ? "var(--amber)" : "var(--accent)")
      .attr("fill-opacity", .6)
      .on("mousemove", (e, v) => showTip(el, M.left + x(v.t), M.top + y(v.exec_s), `${hhmm(v.computado)} · <b>${secStr(v.exec_s)}</b>`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "🕰️", kicker: "ELEITOR #" + v.n + " · " + hhmm(v.computado), title: "Execução: " + secStr(v.exec_s),
        html: `<div class="pop-metric">${secStr(v.exec_s)}</div>
          <p>Voto computado às <b>${hhmm(v.computado)}</b>. Veja onde o ponto está na curva de
          tendência: se a média móvel sobe, a seção está <b>desacelerando</b> naquele trecho.</p>
          ${insight("Leitura", "Tempos maiores no fim do dia costumam ser cansaço do mesário ou eleitores com mais dúvidas; no começo, aquecimento da equipe.")}`
      }));
    // média móvel (janela de 15 eleitores) como tendência
    const W = 15;
    const trend = data.map((v, i) => {
      const ini = Math.max(0, i - Math.floor(W / 2));
      const fim = Math.min(data.length, i + Math.ceil(W / 2));
      const slice = data.slice(ini, fim);
      return { t: v.t, m: d3.mean(slice, (s) => s.exec_s) };
    });
    const line = d3.line().x((p) => x(p.t)).y((p) => y(p.m)).curve(d3.curveMonotoneX);
    g.append("path").datum(trend).attr("fill", "none").attr("stroke", "var(--fg)").attr("stroke-width", 2).attr("opacity", .9).attr("d", line);
  }

  // ---- 3) biometria (barras empilhadas simples) -----------------------------
  function renderBio(d) {
    const svg = d3.select("#chartBio"); const el = svg.node();
    const { ih, iw } = dims(el);
    const vs = d.voters;
    const buckets = [
      { k: "1 tentativa", n: vs.filter((v) => v.solicitacoes <= 1).length, c: "var(--green)" },
      { k: "2 tentativas", n: vs.filter((v) => v.solicitacoes === 2).length, c: "var(--amber)" },
      { k: "3 tentativas", n: vs.filter((v) => v.solicitacoes === 3).length, c: "var(--red)" },
      { k: "4+ tentativas", n: vs.filter((v) => v.solicitacoes >= 4).length, c: "var(--purple)" },
    ];
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleBand().domain(buckets.map((b) => b.k)).range([0, iw]).padding(0.28);
    const y = d3.scaleLinear().domain([0, d3.max(buckets, (b) => b.n) * 1.15]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4));
    g.selectAll("rect").data(buckets).enter().append("rect")
      .attr("class", "bar-clickable").attr("x", (b) => x(b.k)).attr("width", x.bandwidth())
      .attr("y", (b) => y(b.n)).attr("height", (b) => ih - y(b.n)).attr("rx", 3).attr("fill", (b) => b.c)
      .on("mousemove", (e, b) => showTip(el, M.left + x(b.k) + x.bandwidth() / 2, M.top + y(b.n), `<b>${b.n}</b> eleitores · ${b.k}`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, b) => {
        const pct = (100 * b.n / vs.length).toFixed(1);
        openPopup({
          icon: "🖐️", kicker: "BIOMETRIA", title: b.k,
          html: `<div class="pop-metric">${b.n} <span style="font-size:14px;color:var(--fg-muted)">(${pct}%)</span></div>
            <p>Eleitores que precisaram de <b>${b.k}</b> para a digital ser aceita.</p>
            ${insight("Leitura", b.k === "1 tentativa" ? "O ideal — quanto maior esta barra, melhor o leitor e o cadastro." : "Repetições custam tempo. Oriente: <b>dedo limpo e seco, pressão firme sem arrastar</b>. Persistindo, o mesário habilita manualmente.")}`
        });
      });
  }

  // ---- 3b) biometria por hora: solicitações + repetições --------------------
  function renderBioHora(d) {
    const svg = d3.select("#chartBioHora"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = d.biometria_por_hora || [];
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleBand().domain(data.map((v) => v.hora)).range([0, iw]).padding(0.22);
    const y = d3.scaleLinear().domain([0, Math.max(1, d3.max(data, (v) => v.solicitacoes)) * 1.15]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickFormat((h) => h + "h"));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4));
    // barra de fundo = total de solicitações; barra sobreposta = repetições
    g.selectAll("rect.sol").data(data).enter().append("rect").attr("class", "sol bar-clickable")
      .attr("x", (v) => x(v.hora)).attr("width", x.bandwidth())
      .attr("y", (v) => y(v.solicitacoes)).attr("height", (v) => ih - y(v.solicitacoes))
      .attr("rx", 3).attr("fill", "var(--accent)").attr("fill-opacity", .45)
      .on("mousemove", (e, v) => showTip(el, M.left + x(v.hora) + x.bandwidth() / 2, M.top + y(v.solicitacoes), `${v.hora}h · <b>${v.solicitacoes}</b> capturas · ${v.repeticoes} repetições`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => bioHoraPopup(v));
    g.selectAll("rect.rep").data(data).enter().append("rect").attr("class", "rep bar-clickable")
      .attr("x", (v) => x(v.hora) + x.bandwidth() * 0.18).attr("width", x.bandwidth() * 0.64)
      .attr("y", (v) => y(v.repeticoes)).attr("height", (v) => ih - y(v.repeticoes))
      .attr("rx", 3).attr("fill", "var(--red)")
      .on("mousemove", (e, v) => showTip(el, M.left + x(v.hora) + x.bandwidth() / 2, M.top + y(v.repeticoes), `${v.hora}h · <b>${v.repeticoes}</b> repetições`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => bioHoraPopup(v));
    // legenda
    const lg = g.append("g").attr("transform", `translate(${iw - 170},0)`);
    [["var(--accent)", "capturas (solicitações)"], ["var(--red)", "repetições (2ª tentativa+)"]].forEach((p, i) => {
      lg.append("rect").attr("x", 0).attr("y", i * 13).attr("width", 10).attr("height", 10).attr("rx", 2).attr("fill", p[0]).attr("fill-opacity", i === 0 ? .45 : 1);
      lg.append("text").attr("x", 14).attr("y", i * 13 + 9).attr("fill", "var(--fg-muted)").attr("font-size", "9.5px").attr("font-weight", "700").text(p[1]);
    });
  }
  function bioHoraPopup(v) {
    const taxa = v.solicitacoes ? (100 * v.repeticoes / v.solicitacoes).toFixed(0) : 0;
    openPopup({
      icon: "🕒", kicker: "BIOMETRIA · " + v.hora + "h", title: "Digital entre " + v.hora + "h e " + (v.hora + 1) + "h",
      html: `<div class="pop-metric">${v.solicitacoes}</div>
        <p><b>${v.solicitacoes}</b> solicitações de digital nesta hora, das quais <b>${v.repeticoes}</b> foram
        repetições (${taxa}% não pegaram de primeira).</p>
        ${insight("Leitura", v.repeticoes >= v.solicitacoes * 0.4 ? "Taxa de repetição alta — típico do começo do dia (dedos frios/secos) ou leitor sujo. Vale limpar o sensor e orientar o posicionamento do dedo." : "Dentro do esperado para a hora.")}`
    });
  }

  // ---- 4) espera entre eleitores (área) -------------------------------------
  function renderWait(d) {
    const svg = d3.select("#chartWait"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = d.voters.filter((v) => v.wait_s != null).map((v, i) => ({ ...v, i }));
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleLinear().domain([0, data.length]).range([0, iw]);
    const cap = d3.quantile(data.map((v) => v.wait_s).sort(d3.ascending), 0.98) || d3.max(data, (v) => v.wait_s);
    const y = d3.scaleLinear().domain([0, Math.max(cap, 10) * 1.1]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6).tickFormat((v) => "#" + v));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4).tickFormat((v) => v + "s"));
    const area = d3.area().x((v) => x(v.i)).y0(ih).y1((v) => y(Math.min(v.wait_s, y.domain()[1]))).curve(d3.curveMonotoneX);
    g.append("path").datum(data).attr("fill", "var(--amber-dim)").attr("stroke", "var(--amber)").attr("stroke-width", 1.3).attr("d", area);
    g.append("rect").attr("width", iw).attr("height", ih).attr("fill", "transparent")
      .on("mousemove", function (e) {
        const mx = d3.pointer(e, this)[0]; const i = Math.round(x.invert(mx));
        const v = data[Math.max(0, Math.min(data.length - 1, i))]; if (!v) return;
        showTip(el, M.left + x(v.i), M.top + y(Math.min(v.wait_s, y.domain()[1])), `#${v.i + 1} · espera <b>${secStr(v.wait_s)}</b>`);
      })
      .on("mouseleave", () => hideTip(el))
      .on("click", () => openPopup({
        icon: "⏳", kicker: "ESPERA / OCIOSIDADE", title: "Espera entre eleitores",
        html: `<div class="pop-metric">${secStr(Math.round(d.agg.espera_media_s))}</div>
          <p>Cada ponto é o tempo ocioso antes de um eleitor. Média de
          <b>${secStr(Math.round(d.agg.espera_media_s))}</b>, pico de <b>${secStr(d.agg.espera_max_s)}</b>.</p>
          ${insight("O que o presidente pode fazer", "Vales = fluxo bom. Picos = fila parada ou troca de mesário. Antecipar a conferência do título corta a espera.")}`
      }));
  }

  // ---- 5) ritmo acumulado (linha) -------------------------------------------
  function renderCumulative(d) {
    const svg = d3.select("#chartCumulative"); const el = svg.node();
    const { ih, iw } = dims(el);
    const parse = d3.timeParse("%d/%m/%Y %H:%M:%S");
    const pts = d.voters.filter((v) => v.computado).map((v, i) => ({ t: parse(v.computado), n: i + 1, hhmm: hhmm(v.computado) }));
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleTime().domain(d3.extent(pts, (p) => p.t)).range([0, iw]);
    const y = d3.scaleLinear().domain([0, pts.length]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat("%H:%M")));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4));
    const line = d3.line().x((p) => x(p.t)).y((p) => y(p.n)).curve(d3.curveMonotoneX);
    g.append("path").datum(pts).attr("fill", "none").attr("stroke", "var(--accent)").attr("stroke-width", 2).attr("d", line);
    const focus = g.append("circle").attr("r", 4).attr("fill", "var(--accent)").style("display", "none");
    g.append("rect").attr("width", iw).attr("height", ih).attr("fill", "transparent")
      .on("mousemove", function (e) {
        const mx = d3.pointer(e, this)[0]; const t0 = x.invert(mx);
        const bi = d3.bisector((p) => p.t).left(pts, t0); const p = pts[Math.min(bi, pts.length - 1)]; if (!p) return;
        focus.style("display", null).attr("cx", x(p.t)).attr("cy", y(p.n));
        showTip(el, M.left + x(p.t), M.top + y(p.n), `${p.hhmm} · <b>${p.n}</b> eleitores`);
      })
      .on("mouseleave", () => { hideTip(el); focus.style("display", "none"); })
      .on("click", function (e) {
        const mx = d3.pointer(e, this)[0]; const p = pts[Math.min(d3.bisector((q) => q.t).left(pts, x.invert(mx)), pts.length - 1)];
        openPopup({
          icon: "📉", kicker: "RITMO · " + p.hhmm, title: p.n + "º eleitor atendido",
          html: `<p>Às <b>${p.hhmm}</b> a seção já havia atendido <b>${p.n}</b> de ${pts.length} eleitores
            (<b>${(100 * p.n / pts.length).toFixed(0)}%</b>).</p>
            ${insight("Leitura", "A inclinação da curva é a velocidade. Trechos quase planos = fila parada; trechos íngremes = pico de atendimento.")}`
        });
      });
  }

  // ---- alertas --------------------------------------------------------------
  const ALERT_HELP = {
    "Identificador do eleitor digitado inválido": { icon: "⌨️", help: "O mesário digitou um título/documento que a urna não reconheceu (dígito errado, eleitor de outra seção). É corrigido na hora — não afeta a votação.", acao: "Conferir o número com calma antes de confirmar reduz esses alertas." },
    "O eleitor identificado já votou": { icon: "🔁", help: "Tentativa de habilitar alguém que já consta como tendo votado. A urna bloqueia corretamente.", acao: "Verificar o caderno de votação / assinatura antes de habilitar." },
    "Urna não testada": { icon: "🧪", help: "Registrado na preparação: a urna ainda não havia passado pelo teste de votação quando o evento foi gravado.", acao: "Normal na fase de preparação; some após o teste oficial." },
    "Mesário indagado se eleitor está votando": { icon: "❓", help: "A urna perguntou ao mesário se havia eleitor na cabine após um tempo sem ação.", acao: "Acompanhar o eleitor na cabine evita a interrupção." },
    "Habilitação cancelada durante reconhecimento biométrico": { icon: "✋", help: "A habilitação foi cancelada no meio da leitura da digital (eleitor desistiu, troca de dedo).", acao: "Reiniciar a identificação com calma; orientar o posicionamento do dedo." },
    "Digitado título inválido para o registro de mesário": { icon: "🧑‍💼", help: "No encerramento, um título de mesário digitado não foi aceito.", acao: "Conferir o título do mesário no registro final." },
  };
  function alertHelp(msg, sub) {
    return ALERT_HELP[msg] || { icon: "⚠️", help: "Evento de alerta registrado pelo subsistema " + sub + ".", acao: "Verificar o contexto no horário indicado." };
  }
  function renderAlerts(d) {
    const list = document.getElementById("alertList");
    document.getElementById("alertCount").textContent = d.alertas.length;
    // lista com DATA + HORA
    list.innerHTML = d.alertas.map((a, i) => `
      <div class="alert-item" data-i="${i}">
        <span class="a-msg">${a.msg}</span>
        <span class="a-when">
          <span class="a-time">${hhmmss(a.t)}</span>
          <span class="a-date">${dateStr(a.t)}</span>
        </span>
        <span class="a-sub">${a.sub}</span>
      </div>`).join("");
    list.querySelectorAll(".alert-item").forEach((el) =>
      el.addEventListener("click", () => {
        const a = d.alertas[+el.dataset.i];
        const h = alertHelp(a.msg, a.sub);
        openPopup({
          icon: h.icon, kicker: "ALERTA · " + dateStr(a.t) + " " + hhmmss(a.t), title: a.msg,
          html: `<p>${h.help}</p>${insight("O que fazer", h.acao)}`
        });
      }));

    renderAlertSummary(d);
  }

  // resumo por tipo (clicável — filtra o gráfico de horas) + gráfico de horas
  let alertSelType = null;
  function renderAlertSummary(d) {
    const box = document.getElementById("alertSummary");
    const sum = d.alert_summary || [];
    box.innerHTML = sum.map((s, i) => {
      const peak = s.por_hora.reduce((a, b) => (b.n > a.n ? b : a), { n: 0, hora: "—" });
      return `<div class="as-row" data-i="${i}">
        <span class="as-count">${s.total}</span>
        <span class="as-msg">${s.msg}</span>
        <span class="as-peak">${peak.n ? "pico " + peak.n + "× às " + peak.hora + "h" : ""}</span>
      </div>`;
    }).join("");
    box.querySelectorAll(".as-row").forEach((el) =>
      el.addEventListener("click", () => {
        const i = +el.dataset.i;
        alertSelType = alertSelType === i ? null : i;
        box.querySelectorAll(".as-row").forEach((r, j) => r.classList.toggle("active", j === alertSelType));
        drawAlertHora(d);
      }));
    drawAlertHora(d);
  }
  function drawAlertHora(d) {
    const svg = d3.select("#chartAlertHora"); svg.selectAll("*").remove();
    const el = svg.node(); const { ih, iw } = dims(el);
    const sum = d.alert_summary || [];
    const title = document.getElementById("alertHoraTitle");
    let series, label;
    if (alertSelType != null && sum[alertSelType]) {
      series = sum[alertSelType].por_hora; label = sum[alertSelType].msg;
      title.textContent = "🕐 Ocorrências por hora — " + label;
    } else {
      // soma de todos os tipos por hora
      const horas = sum.length ? sum[0].por_hora.map((p) => p.hora) : [];
      series = horas.map((h) => ({ hora: h, n: sum.reduce((acc, s) => acc + (s.por_hora.find((p) => p.hora === h)?.n || 0), 0) }));
      label = "todos os tipos";
      title.textContent = "🕐 Ocorrências por hora — todos os tipos";
    }
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleBand().domain(series.map((s) => s.hora)).range([0, iw]).padding(0.2);
    const y = d3.scaleLinear().domain([0, Math.max(1, d3.max(series, (s) => s.n)) * 1.2]).range([ih, 0]);
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickFormat((h) => h + "h"));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4).tickFormat(d3.format("d")));
    g.selectAll("rect").data(series).enter().append("rect")
      .attr("class", "bar-clickable").attr("x", (s) => x(s.hora)).attr("width", x.bandwidth())
      .attr("y", (s) => y(s.n)).attr("height", (s) => ih - y(s.n)).attr("rx", 3)
      .attr("fill", (s) => s.n ? "var(--amber)" : "var(--border)")
      .on("mousemove", (e, s) => showTip(el, M.left + x(s.hora) + x.bandwidth() / 2, M.top + y(s.n), `<b>${s.n}</b> alerta(s) · ${s.hora}h`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, s) => {
        const naHora = d.alertas.filter((a) => a.hora === s.hora && (alertSelType == null || a.msg === label));
        openPopup({
          icon: "⚠️", kicker: "ALERTAS · " + s.hora + "h", title: s.n + " alerta(s) entre " + s.hora + "h e " + (s.hora + 1) + "h",
          html: (naHora.length ? "<p>" + naHora.map((a) => `<b>${hhmmss(a.t)}</b> — ${a.msg}`).join("<br>") + "</p>" : "<p>Sem alertas nesta hora.</p>")
            + insight("Dica", "Compare com o gráfico de fila/eventos na mesma hora para ver se o alerta coincidiu com o pico de movimento.")
        });
      });
  }

  // ---- reação do eleitor (scatter) ------------------------------------------
  function renderReacao(d) {
    const svg = d3.select("#chartReacao"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = d.voters.filter((v) => v.reacao_s != null);
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleLinear().domain([0, data.length]).range([0, iw]);
    const med = d.agg.reacao_mediana_s || 0;
    const y = d3.scaleLinear().domain([0, d3.max(data, (v) => v.reacao_s) * 1.1]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6).tickFormat((v) => "#" + v));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4).tickFormat((v) => v + "s"));
    g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(med)).attr("y2", y(med)).attr("stroke", "var(--green)").attr("stroke-dasharray", "4,3").attr("stroke-width", 1.4);
    g.append("text").attr("x", iw).attr("y", y(med) - 4).attr("text-anchor", "end").attr("fill", "var(--green)").attr("font-size", "9px").attr("font-weight", "800").text("mediana " + med + "s");
    g.selectAll("circle").data(data).enter().append("circle")
      .attr("class", "dot-clickable").attr("cx", (v, i) => x(i)).attr("cy", (v) => y(v.reacao_s)).attr("r", 2.6)
      .attr("fill", (v) => v.reacao_s > med * 3 ? "var(--red)" : v.reacao_s > med * 1.5 ? "var(--amber)" : "var(--accent)").attr("fill-opacity", .75)
      .on("mousemove", (e, v) => showTip(el, M.left + x(data.indexOf(v)), M.top + y(v.reacao_s), `#${v.n} · reação <b>${secStr(v.reacao_s)}</b>`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "⚡", kicker: "ELEITOR #" + v.n, title: "Reação: " + secStr(v.reacao_s),
        html: `<div class="pop-metric">${secStr(v.reacao_s)}</div>
          <p>Habilitado às <b>${hhmm(v.habilitado)}</b>; 1ª ação na cabine às <b>${hhmm(v.primeiro_voto || v.habilitado)}</b>.
          Depois levou <b>${secStr(v.exec_s)}</b> no total para concluir o voto.</p>
          ${insight("Leitura", v.reacao_s > med * 3 ? "Muito acima da mediana — eleitor parado/lendo antes de começar." : "Dentro do esperado.")}`
      }));
  }

  // ---- scatter genérico por eleitor (reaproveitado p/ tempos do presidente) --
  function scatterPorEleitor(cfg) {
    const svg = d3.select("#" + cfg.svgId); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = cfg.data;
    if (!data.length) return;
    const med = cfg.med || 0;
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleLinear().domain([0, data.length]).range([0, iw]);
    const y = d3.scaleLinear().domain([0, d3.max(data, cfg.val) * 1.1]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6).tickFormat((v) => "#" + v));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4).tickFormat((v) => v + "s"));
    g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(med)).attr("y2", y(med)).attr("stroke", "var(--green)").attr("stroke-dasharray", "4,3").attr("stroke-width", 1.4);
    g.append("text").attr("x", iw).attr("y", y(med) - 4).attr("text-anchor", "end").attr("fill", "var(--green)").attr("font-size", "9px").attr("font-weight", "800").text("mediana " + med + "s");
    g.selectAll("circle").data(data).enter().append("circle")
      .attr("class", "dot-clickable").attr("cx", (v, i) => x(i)).attr("cy", (v) => y(cfg.val(v))).attr("r", 2.6)
      .attr("fill", (v) => cfg.val(v) > med * 3 ? "var(--red)" : cfg.val(v) > med * 1.5 ? "var(--amber)" : cfg.color).attr("fill-opacity", .75)
      .on("mousemove", (e, v) => showTip(el, M.left + x(data.indexOf(v)), M.top + y(cfg.val(v)), `#${v.n} · <b>${secStr(cfg.val(v))}</b>`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup(cfg.pop(v, med)));
  }

  // A) tempo do presidente COMEÇAR a digitar o próximo identificador
  function renderPresInicio(d) {
    scatterPorEleitor({
      svgId: "chartPresInicio",
      data: d.voters.filter((v) => v.pres_inicio_s != null),
      val: (v) => v.pres_inicio_s, med: d.agg.pres_inicio_mediana_s || 0, color: "var(--accent)",
      pop: (v, med) => ({
        icon: "⌨️", kicker: "ELEITOR #" + v.n, title: "Começar a identificar: " + secStr(v.pres_inicio_s),
        html: `<div class="pop-metric">${secStr(v.pres_inicio_s)}</div>
          <p>Da urna liberar a tela (<b>${hhmm(v.aguardando)}</b>) até o mesário digitar o identificador
          (<b>${hhmm(v.ident)}</b>). Mediana da seção: <b>${secStr(med)}</b>; máximo <b>${secStr(d.agg.pres_inicio_max_s)}</b>.</p>
          ${insight("Leitura", v.pres_inicio_s > med * 3 ? "Muito acima da mediana — provável fila vazia, troca de turno ou mesa distraída. Com fila cheia, é o tempo a cortar primeiro." : "Dentro do ritmo da mesa.")}`
      }),
    });
  }

  // B) tempo do presidente HABILITAR (identificador digitado -> habilitado)
  function renderPresHabilita(d) {
    scatterPorEleitor({
      svgId: "chartPresHabilita",
      data: d.voters.filter((v) => v.pres_habilita_s != null),
      val: (v) => v.pres_habilita_s, med: d.agg.pres_habilita_mediana_s || 0, color: "var(--purple)",
      pop: (v, med) => ({
        icon: "🪪", kicker: "ELEITOR #" + v.n, title: "Habilitar: " + secStr(v.pres_habilita_s),
        html: `<div class="pop-metric">${secStr(v.pres_habilita_s)}</div>
          <p>Do identificador digitado (<b>${hhmm(v.ident)}</b>) até <b>Eleitor habilitado</b> (<b>${hhmm(v.habilitado)}</b>).
          Inclui <b>${v.solicitacoes}</b> solicitação(ões) de digital · habilitação <b>${v.tipo_hab || "—"}</b>.
          Mediana da seção: <b>${secStr(med)}</b>; máximo <b>${secStr(d.agg.pres_habilita_max_s)}</b>.</p>
          ${insight("Leitura", v.pres_habilita_s > med * 3 ? "Bem acima da mediana — normalmente biometria que não pega de primeira (várias tentativas de digital)." : "Dentro do esperado.")}`
      }),
    });
  }

  // ---- espera por hora (barras média + losango de pico) ---------------------
  function renderEsperaHora(d) {
    const svg = d3.select("#chartEsperaHora"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = d.espera_por_hora || [];
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleBand().domain(data.map((v) => v.hora)).range([0, iw]).padding(0.22);
    const y = d3.scaleLinear().domain([0, d3.max(data, (v) => v.max_s) * 1.12]).range([ih, 0]);
    const pior = data.reduce((a, b) => (b.max_s > a.max_s ? b : a), { max_s: 0 });
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickFormat((h) => h + "h"));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4).tickFormat((v) => v + "s"));
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("x", (v) => x(v.hora)).attr("width", x.bandwidth())
      .attr("y", (v) => y(v.media_s)).attr("height", (v) => ih - y(v.media_s)).attr("rx", 3)
      .attr("fill", (v) => v.hora === pior.hora ? "var(--red)" : "var(--amber)")
      .on("mousemove", (e, v) => showTip(el, M.left + x(v.hora) + x.bandwidth() / 2, M.top + y(v.media_s), `${v.hora}h · média <b>${secStr(v.media_s)}</b> · pico ${secStr(v.max_s)}`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "🕐", kicker: "FILA · " + v.hora + "h", title: "Espera entre " + v.hora + "h e " + (v.hora + 1) + "h",
        html: `<div class="pop-metric">${secStr(v.media_s)}</div>
          <p>Espera <b>média</b> nesta hora, com pico de <b>${secStr(v.max_s)}</b> (${v.n} eleitores atendidos).
          ${v.hora === pior.hora ? "Foi a <b>pior hora de fila</b> do dia." : ""}</p>
          ${insight("O que fazer", "Horas de pior fila pedem um mesário a mais na identificação e conferência antecipada do título.")}`
      }));
    // losango = pico da hora
    g.selectAll("path.peak").data(data).enter().append("path").attr("class", "peak")
      .attr("d", d3.symbol().type(d3.symbolDiamond).size(26))
      .attr("transform", (v) => `translate(${x(v.hora) + x.bandwidth() / 2},${y(v.max_s)})`)
      .attr("fill", "var(--fg)").attr("stroke", "var(--bg-card-2)").style("pointer-events", "none");
  }

  // ---- ociosidade (barras dos períodos sem votar) ---------------------------
  function renderOciosidade(d) {
    document.getElementById("limiarOcioso").textContent = Math.round((d.limiar_ocioso_s || 120) / 60);
    const svg = d3.select("#chartOciosidade"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = (d.ociosidade || []).slice(0, 12); // os maiores
    const g = svg.append("g").attr("transform", `translate(${M.left + 6},${M.top})`);
    const iw2 = iw - 6;
    if (!data.length) {
      g.append("text").attr("x", iw2 / 2).attr("y", ih / 2).attr("text-anchor", "middle").attr("fill", "var(--fg-sub)").attr("font-size", "11px").text("Nenhum período ocioso acima do limiar 🎉");
      return;
    }
    const y = d3.scaleBand().domain(data.map((o) => hhmm(o.inicio))).range([0, ih]).padding(0.22);
    const x = d3.scaleLinear().domain([0, d3.max(data, (o) => o.dur_s) * 1.1]).range([0, iw2]);
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(4).tickFormat((v) => Math.round(v / 60) + "min"));
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("y", (o) => y(hhmm(o.inicio))).attr("height", y.bandwidth())
      .attr("x", 0).attr("width", (o) => x(o.dur_s)).attr("rx", 3).attr("fill", "var(--gray)")
      .on("mousemove", (e, o) => showTip(el, M.left + 6 + x(o.dur_s), M.top + y(hhmm(o.inicio)) + y.bandwidth() / 2, `<b>${secStr(o.dur_s)}</b> parada · ${hhmm(o.inicio)}→${hhmm(o.fim)}`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, o) => openPopup({
        icon: "💤", kicker: "OCIOSIDADE · " + hhmm(o.inicio), title: "Urna parada por " + secStr(o.dur_s),
        html: `<div class="pop-metric">${secStr(o.dur_s)}</div>
          <p>Nenhum eleitor votando entre <b>${hhmm(o.inicio)}</b> e <b>${hhmm(o.fim)}</b>
          (logo após o eleitor #${o.apos_eleitor}).</p>
          ${insight("Leitura", "Períodos ociosos no meio do dia podem ser fila vazia de verdade, pausa de mesário ou almoço. No início/fim do dia são normais.")}`
      }));
  }

  // ---- teclas indevidas por eleitor (barras ordenadas) ----------------------
  function renderTeclasEleitor(d) {
    document.getElementById("teclasTotal").textContent = fmt(d.agg.teclas_indevidas);
    const media = d.agg.total_eleitores ? d.agg.teclas_indevidas / d.agg.total_eleitores : 0;
    document.getElementById("teclasMedia").textContent = media.toFixed(1);
    const svg = d3.select("#chartTeclasEleitor"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = (d.teclas_por_eleitor || []).slice().sort((a, b) => b.teclas - a.teclas);
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleLinear().domain([0, data.length]).range([0, iw]);
    const y = d3.scaleLinear().domain([0, d3.max(data, (v) => v.teclas) * 1.1]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(6).tickFormat((v) => v + "º"));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4));
    g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(media)).attr("y2", y(media)).attr("stroke", "var(--green)").attr("stroke-dasharray", "4,3").attr("stroke-width", 1.3);
    g.append("text").attr("x", iw).attr("y", y(media) - 4).attr("text-anchor", "end").attr("fill", "var(--green)").attr("font-size", "9px").attr("font-weight", "800").text("média " + media.toFixed(1));
    const bw = Math.max(1, iw / data.length - 0.5);
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("x", (v, i) => x(i)).attr("width", bw)
      .attr("y", (v) => y(v.teclas)).attr("height", (v) => ih - y(v.teclas))
      .attr("fill", (v) => v.teclas > media * 3 ? "var(--red)" : v.teclas > media * 1.8 ? "var(--amber)" : "var(--purple)")
      .on("mousemove", (e, v) => showTip(el, M.left + x(data.indexOf(v)) + bw / 2, M.top + y(v.teclas), `eleitor #${v.n} · <b>${v.teclas}</b> teclas`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "🧑", kicker: "ELEITOR #" + v.n, title: v.teclas + " teclas indevidas",
        html: `<div class="pop-metric">${v.teclas}</div>
          <p>Este eleitor pressionou <b>${v.teclas}</b> teclas inválidas — contra uma média de
          <b>${media.toFixed(1)}</b> por eleitor. Habilitado às <b>${hhmm(v.habilitado)}</b>,
          voto computado às <b>${hhmm(v.computado)}</b>.</p>
          ${insight("Leitura", v.teclas > media * 3 ? "Um <b>outlier claro</b>: eleitor com muita dificuldade de usar o teclado. É o tipo de caso que puxa o total para cima (" + fmt(d.agg.teclas_indevidas) + " no dia) sem ser a regra." : "Dentro ou pouco acima da média.")}`
      }));
  }

  // ---- teclas indevidas por hora (barras) -----------------------------------
  function renderTeclasHora(d) {
    const svg = d3.select("#chartTeclasHora"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = d.teclas_por_hora || [];
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleBand().domain(data.map((v) => v.hora)).range([0, iw]).padding(0.22);
    const y = d3.scaleLinear().domain([0, d3.max(data, (v) => v.n) * 1.15]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickFormat((h) => h + "h"));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4));
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("x", (v) => x(v.hora)).attr("width", x.bandwidth())
      .attr("y", (v) => y(v.n)).attr("height", (v) => ih - y(v.n)).attr("rx", 3).attr("fill", "var(--purple)")
      .on("mousemove", (e, v) => showTip(el, M.left + x(v.hora) + x.bandwidth() / 2, M.top + y(v.n), `<b>${v.n}</b> teclas · ${v.hora}h`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "🕒", kicker: "TECLAS · " + v.hora + "h", title: v.n + " teclas indevidas às " + v.hora + "h",
        html: `<div class="pop-metric">${v.n}</div>
          <p>Teclas inválidas pressionadas <b>no teclado da cabine (Terminal do Eleitor)</b> nesta faixa de hora —
          pelos próprios <b>eleitores</b>, não pelo mesário no microterminal.</p>
          ${insight("Leitura", "Picos costumam acompanhar as horas de maior movimento — mais eleitores, mais toques por insegurança.")}`
      }));
  }

  // ---- eventos por hora (barras largas) -------------------------------------
  function renderEventos(d) {
    const svg = d3.select("#chartEventos"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = d.eventos_por_hora || [];
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleBand().domain(data.map((v) => v.hora)).range([0, iw]).padding(0.18);
    const y = d3.scaleLinear().domain([0, d3.max(data, (v) => v.n) * 1.12]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickFormat((h) => h + "h"));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(5));
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("x", (v) => x(v.hora)).attr("width", x.bandwidth())
      .attr("y", (v) => y(v.n)).attr("height", (v) => ih - y(v.n)).attr("rx", 3).attr("fill", "var(--accent)")
      .on("mousemove", (e, v) => showTip(el, M.left + x(v.hora) + x.bandwidth() / 2, M.top + y(v.n), `<b>${fmt(v.n)}</b> eventos · ${v.hora}h`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "📡", kicker: "EVENTOS · " + v.hora + "h", title: fmt(v.n) + " eventos às " + v.hora + "h",
        html: `<div class="pop-metric">${fmt(v.n)}</div>
          <p>Total de linhas de log geradas nesta hora — identificação, biometria, votos, teclas e tudo mais.</p>
          ${insight("Leitura", "É um termômetro de movimento: mais eventos = hora mais intensa de operação da urna.")}`
      }));
  }

  // ---- eventos indesejáveis por hora + tipos --------------------------------
  function renderIndesejaveis(d) {
    const svg = d3.select("#chartIndesejaveis"); const el = svg.node();
    const { ih, iw } = dims(el);
    const data = d.eventos_indesejaveis_por_hora || [];
    const tipos = d.eventos_indesejaveis_tipos || [];
    const total = tipos.reduce((a, t) => a + t.n, 0);
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x = d3.scaleBand().domain(data.map((v) => v.hora)).range([0, iw]).padding(0.18);
    const y = d3.scaleLinear().domain([0, Math.max(1, d3.max(data, (v) => v.n)) * 1.2]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).tickFormat((h) => h + "h"));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4).tickFormat(d3.format("d")));
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("x", (v) => x(v.hora)).attr("width", x.bandwidth())
      .attr("y", (v) => y(v.n)).attr("height", (v) => ih - y(v.n)).attr("rx", 3)
      .attr("fill", (v) => v.n ? "var(--red)" : "var(--border)")
      .on("mousemove", (e, v) => showTip(el, M.left + x(v.hora) + x.bandwidth() / 2, M.top + y(v.n), `<b>${v.n}</b> evento(s) · ${v.hora}h`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "⚠️", kicker: "INDESEJÁVEIS · " + v.hora + "h", title: v.n + " evento(s) fora do normal às " + v.hora + "h",
        html: `<div class="pop-metric">${v.n}</div>
          <p>Eventos fora do fluxo normal de voto nesta hora. No dia todo foram <b>${total}</b>.</p>
          ${insight("Leitura", "Picos aqui costumam coincidir com horas de maior movimento (mais chance de digitação errada e inatividade).")}`
      }));

    // lista compacta de tipos
    const box = document.getElementById("indesejTipos");
    box.innerHTML = tipos.map((t) => `
      <div class="mini-row" title="${t.tipo}">
        <span class="ml-n">${t.n}</span>
        <span class="ml-t">${t.tipo}</span>
      </div>`).join("");
  }

  // ---- RDV: mapas de votos --------------------------------------------------
  const RDV_HELP = {
    "Presidente": "Número de 2 dígitos. Clique numa barra para ver os votos daquele número.",
    "Governador": "Número de 2 dígitos (governo estadual).",
    "Senador": "Número de 3 dígitos. Normalmente há 2 vagas — por isso o total de votos é maior.",
  };
  function renderRdv(d) {
    const rdv = d.rdv;
    const aviso = document.getElementById("rdvAviso");
    if (!rdv || !rdv.cargos || !rdv.cargos.length) {
      aviso.style.display = "";
      aviso.textContent = "⚠️ Dados do RDV não embutidos. Rode: python3 scripts/parse_rdv.py <RDV_...dat> e reconstrua com build_desempenho.py.";
      return;
    }
    const byCargo = {};
    rdv.cargos.forEach((c) => { byCargo[c.cargo] = c; });
    drawRdvBar("chartRdvPres", "rdvSubPres", byCargo["Presidente"], "var(--accent)");
    drawRdvBar("chartRdvGov", "rdvSubGov", byCargo["Governador"], "var(--green)");
    drawRdvBar("chartRdvSen", "rdvSubSen", byCargo["Senador"], "var(--purple)");
    drawRdvNulos(d);
    drawRdvNulosNum(d);
  }
  function drawRdvBar(svgId, subId, cargo, cor) {
    const svg = d3.select("#" + svgId); const el = svg.node();
    const { ih, iw } = dims(el);
    if (!cargo) return;
    const nominal = (cargo.tipos.nominal || 0) + (cargo.tipos.legenda || 0);
    document.getElementById(subId).innerHTML =
      `${fmt(cargo.total)} votos · <b>${fmt(nominal)}</b> nominais · top 10 números`;
    const data = (cargo.nominais || []).slice(0, 10);
    const g = svg.append("g").attr("transform", `translate(${M.left + 8},${M.top})`);
    const iw2 = iw - 8;
    const y = d3.scaleBand().domain(data.map((v) => v.numero)).range([0, ih]).padding(0.18);
    const x = d3.scaleLinear().domain([0, d3.max(data, (v) => v.votos) * 1.1]).range([0, iw2]);
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(4));
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("y", (v) => y(v.numero)).attr("height", y.bandwidth())
      .attr("x", 0).attr("width", (v) => x(v.votos)).attr("rx", 3).attr("fill", cor)
      .on("mousemove", (e, v) => showTip(el, M.left + 8 + x(v.votos), M.top + y(v.numero) + y.bandwidth() / 2, `nº <b>${v.numero}</b> · ${v.votos} votos`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => openPopup({
        icon: "🗳️", kicker: "RDV · " + cargo.cargo, title: "Número " + v.numero,
        html: `<div class="pop-metric">${v.votos}</div>
          <p>votos nominais no número <b>${v.numero}</b> para <b>${cargo.cargo}</b>
          (${(100 * v.votos / cargo.total).toFixed(1)}% do total do cargo).</p>
          ${insight("Sobre o RDV", RDV_HELP[cargo.cargo] || "Votos reconstruídos do RDV, sem brancos nem nulos.")}`
      }));
  }
  function drawRdvNulos(d) {
    const svg = d3.select("#chartRdvNulos"); const el = svg.node();
    const { ih, iw } = dims(el);
    const cargos = d.rdv.cargos.map((c) => ({
      cargo: c.cargo, branco: c.tipos.branco || 0, nulo: c.tipos.nulo || 0, total: c.total,
    }));
    const g = svg.append("g").attr("transform", `translate(${M.left},${M.top})`);
    const x0 = d3.scaleBand().domain(cargos.map((c) => c.cargo)).range([0, iw]).padding(0.25);
    const sub = d3.scaleBand().domain(["branco", "nulo"]).range([0, x0.bandwidth()]).padding(0.1);
    const y = d3.scaleLinear().domain([0, Math.max(1, d3.max(cargos, (c) => Math.max(c.branco, c.nulo))) * 1.2]).range([ih, 0]);
    y.ticks(4).forEach((t) => g.append("line").attr("class", "grid-line").attr("x1", 0).attr("x2", iw).attr("y1", y(t)).attr("y2", y(t)));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x0));
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y).ticks(4));
    const cor = { branco: "var(--gray)", nulo: "var(--red)" };
    cargos.forEach((c) => {
      ["branco", "nulo"].forEach((k) => {
        g.append("rect").attr("class", "bar-clickable")
          .attr("x", x0(c.cargo) + sub(k)).attr("width", sub.bandwidth())
          .attr("y", y(c[k])).attr("height", ih - y(c[k])).attr("rx", 2).attr("fill", cor[k])
          .on("mousemove", (e) => showTip(el, M.left + x0(c.cargo) + sub(k) + sub.bandwidth() / 2, M.top + y(c[k]), `${c.cargo} · ${k}: <b>${c[k]}</b>`))
          .on("mouseleave", () => hideTip(el))
          .on("click", () => openPopup({
            icon: "❓", kicker: "RDV · " + c.cargo, title: k === "nulo" ? "Votos nulos" : "Votos em branco",
            html: `<div class="pop-metric">${c[k]}</div>
              <p>${k === "nulo" ? "Votos <b>nulos</b>" : "Votos em <b>branco</b>"} para <b>${c.cargo}</b>
              (${(100 * c[k] / c.total).toFixed(1)}% do cargo).</p>
              ${insight("Leitura", "Cargos com mais brancos/nulos são onde o eleitor mais hesitou ou errou — tipicamente deputados e senador, de números mais longos. Veja ao lado QUAIS números deram nulo.")}`
          }));
      });
    });
    // legenda
    const lg = g.append("g").attr("transform", `translate(${iw - 150},0)`);
    [["branco", "Branco"], ["nulo", "Nulo"]].forEach((p, i) => {
      lg.append("rect").attr("x", i * 75).attr("y", 0).attr("width", 10).attr("height", 10).attr("rx", 2).attr("fill", cor[p[0]]);
      lg.append("text").attr("x", i * 75 + 14).attr("y", 9).attr("fill", "var(--fg-muted)").attr("font-size", "10px").attr("font-weight", "700").text(p[1]);
    });
  }

  // ---- RDV: números que foram anulados (barras horizontais agrupadas) -------
  function drawRdvNulosNum(d) {
    const svg = d3.select("#chartRdvNulosNum"); const el = svg.node();
    const { ih, iw } = dims(el);
    // junta os números nulos de todos os cargos, guardando de qual cargo veio o maior
    const porNumero = {};
    d.rdv.cargos.forEach((c) => {
      (c.nulos_numeros || []).forEach((x) => {
        const key = x.numero;
        if (!porNumero[key]) porNumero[key] = { numero: key, votos: 0, cargos: {} };
        porNumero[key].votos += x.votos;
        porNumero[key].cargos[c.cargo] = (porNumero[key].cargos[c.cargo] || 0) + x.votos;
      });
    });
    const data = Object.values(porNumero).sort((a, b) => b.votos - a.votos).slice(0, 12);
    if (!data.length) {
      svg.append("text").attr("x", iw / 2).attr("y", ih / 2).attr("text-anchor", "middle")
        .attr("fill", "var(--fg-sub)").attr("font-size", "11px").text("Sem números de voto nulo neste RDV");
      return;
    }
    const g = svg.append("g").attr("transform", `translate(${M.left + 14},${M.top})`);
    const iw2 = iw - 14;
    const y = d3.scaleBand().domain(data.map((v) => v.numero)).range([0, ih]).padding(0.16);
    const x = d3.scaleLinear().domain([0, d3.max(data, (v) => v.votos) * 1.1]).range([0, iw2]);
    g.append("g").attr("class", "chart-axis").call(d3.axisLeft(y));
    g.append("g").attr("class", "chart-axis").attr("transform", `translate(0,${ih})`).call(d3.axisBottom(x).ticks(4).tickFormat(d3.format("d")));
    const corZeros = (n) => /^0+$/.test(n);
    g.selectAll("rect").data(data).enter().append("rect")
      .attr("class", "bar-clickable").attr("y", (v) => y(v.numero)).attr("height", y.bandwidth())
      .attr("x", 0).attr("width", (v) => x(v.votos)).attr("rx", 3)
      .attr("fill", (v) => corZeros(v.numero) ? "var(--gray)" : "var(--red)")
      .on("mousemove", (e, v) => showTip(el, M.left + 14 + x(v.votos), M.top + y(v.numero) + y.bandwidth() / 2, `nº <b>${v.numero}</b> · ${v.votos} nulo(s)`))
      .on("mouseleave", () => hideTip(el))
      .on("click", (e, v) => {
        const porCargo = Object.entries(v.cargos).sort((a, b) => b[1] - a[1]);
        const zeros = corZeros(v.numero);
        openPopup({
          icon: "🔢", kicker: "VOTO NULO", title: "Número " + v.numero + " → " + v.votos + " nulo(s)",
          html: `<div class="pop-metric">${v.votos}</div>
            <p>Vezes que digitar <b>${v.numero}</b> resultou em <b>voto nulo</b>, por cargo:
            ${porCargo.map(([cg, n]) => `<br><b>${cg}</b>: ${n}`).join("")}</p>
            ${insight("Leitura", zeros
              ? "Só zeros = o eleitor <b>quis anular de propósito</b> (digitou 00/0000)."
              : "Número de candidato inexistente para o cargo — normalmente <b>confusão</b> (ex.: digitar o nº de presidente no governador) ou erro de digitação.")}`
        });
      });
    // legenda
    const lg = g.append("g").attr("transform", `translate(${iw2 - 170},-2)`);
    [["var(--gray)", "só zeros (proposital)"], ["var(--red)", "nº inválido (erro/confusão)"]].forEach((p, i) => {
      lg.append("rect").attr("x", 0).attr("y", i * 12).attr("width", 9).attr("height", 9).attr("rx", 2).attr("fill", p[0]);
      lg.append("text").attr("x", 13).attr("y", i * 12 + 8).attr("fill", "var(--fg-muted)").attr("font-size", "9px").attr("font-weight", "700").text(p[1]);
    });
  }
})();
