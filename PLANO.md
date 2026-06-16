# Plano — Repositório `renderizar-mapa`: relatório + dashboard de Source do Mapa incorreto

## Context

A correção das unidades PMMS (serviço 424) já foi feita nesta sessão (57/68; 11 manuais pendentes). Agora o objetivo muda: transformar o trabalho ad-hoc num **projeto versionado e reutilizável** que detecta **todas as unidades ativas com Source do Mapa incorreto** (não só o serviço 424), agrupa por **órgão**, e entrega um **dashboard funcional** + relatório.

Decisões do Fabio:
- **Detecção inicial via API** (Api-Key pública, read-only). O caminho **DB/SQL** (mais completo) fica **documentado** num `CLAUDE.md` pra ele continuar numa máquina com **VPN + acesso ao banco**.
- **Critério de incorreto:** `source` começa com **aspa** (`"` ou `'`) **OU** contém a tag **`<iframe`**. Só unidades **ativas**.
- **Órgão:** herdado do serviço via API (`orgao_sigla`) — resolve agrupamento sem precisar da tabela de órgãos.
- Repo: **organiza + commita + push** pra `origin/main`.
- `/frontend-design`: dashboard com qualidade visual (distinto, limpo, não-genérico).

## Diagnóstico de API (validado)

- Auth: header `Authorization: Api-Key <KEY>` (pública, embutida na SPA, **só leitura**; via env `CMS_API_KEY`).
- `GET /api/cms/servicos/?page=N` → paginado (`count`, `next`, `total_pages`, `page_size`, `results[]`).
- `GET /api/cms/servicos/<id>/` → objeto com `orgao_sigla`, `orgao_nome`, `servicosUnidade[].unidade{ slug_unidade, nome, endereco, complemento, bairro, source, ativo }`.
- `unidades_geral/` sem filtro = vazio → **não** há list-all de unidades; enumerar via serviços.
- Edit URL no admin: `https://admin.ms.gov.br/locais_atendimento/editar/<slug_unidade>`.

## Estrutura-alvo do repositório

```
renderizar-mapa/
├── README.md                 # estilizado, simples/objetivo (frontend-design)
├── CLAUDE.md                 # contexto p/ continuar em outra máquina (VPN+DB)
├── PLANO.md                  # este plano, versionado no repo
├── .gitignore                # + data/*.gerado opcional
├── scripts/
│   ├── gerar_relatorio.py    # API → data/ (todas ativas incorretas, c/ órgão)
│   └── gen_dashboard.py      # data/json → dashboard/index.html
├── data/
│   ├── unidades_incorretas.json
│   └── unidades_incorretas.csv
├── dashboard/
│   ├── template.html         # tema + filtro por órgão
│   └── index.html            # gerado
└── sql/
    ├── deteccao.sql          # SELECT incorretas (aspa OR <iframe>) WHERE ativo
    └── correcao.sql          # UPDATE strip aspa (era fix-source-aspa.sql)
```

Mover existentes: `gen_dashboard.py`→`scripts/`; `dashboard_template.html`→`dashboard/template.html`; `dashboard-source-mapa.html`→`dashboard/index.html` (regenerado); `fix-source-aspa.sql`→`sql/correcao.sql`; `unidades-424-*`→ removidos/regenerados em `data/`.

## scripts/gerar_relatorio.py (API)

- Config no topo: `API_BASE`, `API_KEY` (default a key pública conhecida; override por `os.environ`).
- Enumerar serviços: loop `?page=N` até `next` nulo; coletar IDs. Para cada serviço, usar `servicosUnidade` (se a lista já trouxer) ou `GET servicos/<id>/` (fallback) — extrair `orgao_sigla`.
- Montar dict de unidades **dedup por `slug_unidade`**; acumular `set(orgaos)` (unidade pode estar em +1 serviço).
- Filtrar `ativo == True`.
- Classificar incorreto (`motivo`):
  - vazio/None → `sem-source`
  - `re.match(r'^\s*["\']', source)` → `aspa-inicial`
  - `'<iframe' in source.lower()` → `tag-iframe`
  - contém `/maps/place` ou não-embed → `nao-embed`
  - senão → OK (excluir do relatório)
- `source_corrigido`:
  - aspa → `re.sub(r'^\s*["\']', '', source)` (e se tiver `<iframe`, extrair `src="..."`).
  - tag-iframe → extrair URL do `src=`.
  - nao-embed/sem-source → `__GERAR_EMBED__` (flag p/ revisão manual).
- Saída: `data/unidades_incorretas.json` (lista de `{slug, nome, complemento, endereco, bairro, orgao, ativo, motivo, source_atual, source_corrigido, edit_url}`) + CSV (`;`, utf-8-sig).
- `requests` (stdlib `urllib` se requests ausente). Resiliente a timeout/retry.

## dashboard (frontend-design)

- `template.html` com placeholders `{{ROWS}}`, KPIs, `{{ORGAOS}}` (options do filtro).
- Recursos:
  - **Filtro por órgão** (select com contagem por órgão) + **busca** texto + filtro por **motivo**.
  - **Agrupar por órgão** (cabeçalhos de seção) com contadores.
  - KPIs: total incorretas, por motivo, nº de órgãos afetados, concluídas.
  - **Checklist** persistente (localStorage), **Editar↗** (link admin), **Copiar source corrigido**.
- Estética: tema escuro existente refinado — tipografia clara, espaçamento, badges por motivo, responsivo. Sem cara de template genérico.

## CLAUDE.md (para a máquina com VPN+DB)

- Resumo do projeto + bug (aspa inicial / tag `<iframe`) + critério.
- Como rodar: `python scripts/gerar_relatorio.py` → `data/` → `python scripts/gen_dashboard.py` → abrir `dashboard/index.html`.
- **Roadmap DB (preferido depois):** na rede SETDIG, `gerenciamento_unidades` tem `ativo, source, orgao_id, cidade_id`. Usar `sql/deteccao.sql` p/ levantar e `sql/correcao.sql` p/ corrigir (com backup + transação). Host `s0845.ms` é interno (só via VPN).
- **Segurança:** credenciais do banco por **variáveis de ambiente** (`DB_HOST/PORT/USER/PASSWORD/NAME`) — **nunca commitar**. Api-Key é pública (read). Rotacionar senha do banco e a Api-Key expostas no chat.

## sql/

- `deteccao.sql`: `SELECT slug_unidade, complemento, endereco, orgao_id, source FROM gerenciamento_unidades WHERE ativo IS TRUE AND (source ~ '^\s*["'']' OR source ILIKE '%<iframe%');`
- `correcao.sql`: transação com backup + `UPDATE ... SET source = regexp_replace(source, '^\s*["'']','') WHERE source ~ '^\s*"';` (já existente, movido/renomeado).

## Execução

1. Criar pastas e mover/gerar arquivos.
2. Escrever `scripts/gerar_relatorio.py`, `scripts/gen_dashboard.py`, `dashboard/template.html`, `README.md`, `CLAUDE.md`, `PLANO.md`, `sql/*`.
3. Rodar `gerar_relatorio.py` (API, internet pública — alcançável daqui) → popular `data/`.
4. Rodar `gen_dashboard.py` → `dashboard/index.html`.
5. Verificar dashboard (servir em localhost + screenshot; filtro por órgão funcionando).
6. `git add` + commit (sem assinatura IA) + push `origin/main`.

## Verificação

- `data/unidades_incorretas.json` populado; contagem por motivo coerente (serviço 424 já majoritariamente corrigido → refletir estado atual).
- Dashboard abre, filtro por órgão muda a lista, KPIs batem, checklist persiste.
- README/ CLAUDE.md legíveis.
- `git log` mostra 1 commit limpo; push ok.

## Segurança (recap)
- Nenhuma credencial de banco no repo (env vars). Rotacionar senha `painel-sgd` + Api-Key (expostas no chat).
