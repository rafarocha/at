# Acompanhamento em Tempo Real — 150ª Zona Eleitoral

Sistema simples de acompanhamento operacional para o dia da eleição: administradores de prédio e
mesários confirmam tarefas, rondas e ocorrências pelo **Telegram**, e isso alimenta ao vivo um mapa,
gráficos e painéis — sem ninguém precisar ligar seção por seção pra saber o que está acontecendo.

**Público-alvo:** mesários, administradores de prédio, gestores de administradores e juízes eleitorais.

👉 **[Veja a demonstração e os cenários de treinamento](https://rafarocha.github.io/at/)** — nenhum
dado real, só para conhecer a interface.

📄 Guia técnico de deploy: [`html-howto/publicar.html`](html-howto/publicar.html).

## Como funciona

1. O administrador/mesário abre um link do Telegram (do guia de bolso impresso) e confirma uma
   tarefa, ronda ou ocorrência com poucos toques.
2. O bot grava isso numa planilha do Google Sheets (`checkpoints`, `rondas`, `ocorrencias`).
3. Três páginas HTML estáticas leem essa planilha publicada como CSV e se atualizam sozinhas:
   **Visão Geral** (mapa + indicadores agregados), **Detalhe por Seção** (os 5 aspectos de uma seção
   específica) e **Painel Gestor** (grade com todas as seções lado a lado).

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `html-mockups/` | Código-fonte real das 3 páginas (`index.html`, `secao.html`, `painel.html`). Precisam de `CSV_URL_CHECKPOINTS` etc. configurados no início do `<script>` para funcionar com uma planilha de verdade. **É aqui que você edita.** Também guarda alguns arquivos antigos/de referência (`sunday.html`, `painel-exemplo-*.html`, `days.html`, `checkpoints-150ze.xlsx`) — me avise se algum desses devia ir para outro lugar. |
| `html-howto/` | Guias e material de apoio em HTML: `publicar.html` (como publicar no Pages), `sunday-tracking.html` e `tracking_guide.html` (configuração da planilha/CSV), `acoes-seguranca.html` (segurança/segredos). |
| `scripts/dados/` | Os 3 CSVs fictícios (`checkpoints`/`rondas`/`ocorrencias`) de cada cenário — matéria-prima dos samples e da demo. |
| `scripts/build_public.py` | Gera `public/` e `teste-local/` a partir de `html-mockups/` + `scripts/dados/`. É o "release" — veja `html-howto/publicar.html`. |
| `public/` | **Saída publicada no GitHub Pages.** `index.html` é escrito à mão (landing page); `demo/` e `samples/` são gerados — nunca edite à mão. |
| `teste-local/` | Cópia de `html-mockups/` apontando pros 3 CSVs locais — testa o fetch() de verdade sem depender de planilha. Também gerado pelo build. |
| `.github/workflows/pages.yml` | CI: builda e publica `public/` a cada push relevante. |
| `eleicoes-bot/` | Bot do Telegram (Python) que grava as confirmações na planilha. |
| `docs/` | Manuais de referência (mesário/administrador) — uso interno, não fica no site público. |

## Por que 3 CSVs/URLs em vez de um só

A planilha do Google Sheets tem 3 abas: `checkpoints`, `ocorrencias` e `rondas`. O recurso
"Publicar na web" do Google Sheets publica **uma aba por vez** — cada aba gera seu próprio link CSV,
por isso `html-mockups/*.html` pedem 3 constantes separadas (`CSV_URL_CHECKPOINTS`,
`CSV_URL_OCORRENCIAS`, `CSV_URL_RONDAS`), uma por aba/link.

`scripts/dados/` segue exatamente essa mesma divisão em 3 arquivos brutos por cenário. O
`scripts/build_public.py` lê esses 3 arquivos e embute o conteúdo deles dentro do `.html` gerado (como
`MOCK_CHECKPOINTS`, `MOCK_OCORRENCIAS`, `MOCK_RONDAS`), pra virar uma demonstração 100% offline em
`public/`. A organização em 3 partes é a mesma nos dois casos — o que muda é só se o dado vem de uma
planilha ao vivo (3 URLs) ou já vem embutido no arquivo (offline).

## Gerando um "release" (atualizando public/)

`public/demo/` e `public/samples/` **não são editados à mão** — eles são build output de
`html-mockups/` + `scripts/dados/`. Pra atualizar:

```bash
python3 scripts/build_public.py
```

Isso regenera `public/demo/`, `public/samples/*` e `teste-local/*`. O GitHub Actions roda o mesmo
comando sozinho a cada push que mexer em `html-mockups/`, `scripts/` ou `public/` — então normalmente
você nem precisa rodar isso localmente, só `git push` e o site atualiza em 1–2 minutos. Detalhes
completos (inclusive como ativar o Pages a primeira vez) em
[`html-howto/publicar.html`](html-howto/publicar.html).

## Testando

Duas pontas para testar, sem misturar uma com a outra:

**1) Interface/UX** (sem planilha nenhuma) — abra qualquer arquivo de `public/samples/` ou
`public/demo/` com duplo clique. É 100% offline (só os 3 gráficos da Visão Geral precisam de internet,
por causa da biblioteca de gráficos).

**2) Fluxo real de planilha** (fetch, atualização a cada 30s, botão "Atualizar agora", banner de erro)
— use `teste-local/`. É literalmente `html-mockups/` de produção, só que `CSV_URL_*` apontam pros 3
`.csv` locais dessa mesma pasta em vez de um link do Google Sheets. Como usa `fetch()` de verdade,
**precisa rodar por um servidor local** (duplo clique não funciona — navegador bloqueia `fetch` de
arquivo local):

```bash
cd teste-local
python3 -m http.server 8000
# depois abra http://localhost:8000/index.html
```

Edite qualquer um dos 3 CSVs, salve, e clique em "🔄 Atualizar agora" (ou espere os 30s) — dá pra ver a
mudança aparecer, exatamente como vai se comportar com a planilha real. Quando a planilha definitiva
estiver pronta, publique cada aba (`checkpoints`, `ocorrencias`, `rondas`) individualmente em **Arquivo
→ Compartilhar → Publicar na web**, escolhendo a aba certa e o formato CSV — isso gera um link por aba,
que você cola nas constantes `CSV_URL_*` de `html-mockups/index.html`, `secao.html` e `painel.html`.

## Licença

GNU GPLv3 — veja [LICENSE](LICENSE).
