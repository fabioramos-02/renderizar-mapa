<div align="center">

# 🗺️ Mapa Quebrado

**Detecção e correção de _Source do Mapa_ incorreto nas unidades de atendimento do Portal [ms.gov.br](https://www.ms.gov.br)**

`SETDIG` · `Portal Único de Serviços` · `CMS`

</div>

---

## O problema

Nas cartas de serviço, a seção **"Unidades disponíveis"** mostra um mapa do Google por unidade. Muitos não renderizam — aparece o **404 do Google** no lugar do mapa.

**Causa raiz:** o campo *Source do Mapa* (coluna `source`) foi preenchido colando o snippet `<iframe>` inteiro, deixando uma **aspa `"` no início**. O front faz `iframe.src = source`, virando `"https://...` → URL inválida → **404**.

| Motivo | O que é | Correção |
|---|---|---|
| `aspa-inicial` | `source` começa com `"`/`'` | remover a aspa inicial |
| `tag-iframe` | campo contém `<iframe ...>` | extrair só a URL do `src=` |
| `nao-embed` | URL `/maps/place`, `/dir`, short-link | gerar `/maps/embed` novo |
| `sem-source` | campo vazio / texto | gerar embed novo |

> Embed **válido** começa em `https://www.google.com/maps/embed?pb=...`

---

## O que este repo faz

1. **Varre** todas as unidades **ativas** do CMS (via API pública, read-only).
2. **Classifica** as incorretas pelo critério acima.
3. **Gera** um relatório (`CSV`/`JSON`) + um **dashboard** com filtro por **órgão**, busca, checklist e link direto de edição no admin.

---

## Uso rápido

```bash
# 0. configurar credenciais (.env é ignorado pelo git)
cp .env.example .env   # e preencher CMS_API_KEY

# 1. levanta as unidades incorretas -> data/
python scripts/gerar_relatorio.py

# 2. gera o dashboard -> index.html (raiz)
python scripts/gen_dashboard.py

# 3. abre o dashboard (duplo-clique ou):
#    Windows:  start index.html
```

> Publicado na Vercel: a raiz serve o `index.html` gerado (sem build). Push no `main` = redeploy.

Requisito: Python 3 + `requests` (`pip install requests`).

---

## Estrutura

```
renderizar-mapa/
├── index.html               # dashboard gerado (servido na raiz pela Vercel)
├── scripts/
│   ├── gerar_relatorio.py   # API CMS -> data/ (unidades ativas incorretas)
│   └── gen_dashboard.py     # data/json -> index.html
├── data/
│   ├── unidades_incorretas.json
│   └── unidades_incorretas.csv
├── dashboard/
│   └── template.html        # tema DS-MS + UI (filtro por órgão, checklist)
├── sql/
│   ├── deteccao.sql         # levantamento direto no banco
│   └── correcao.sql         # UPDATE (strip aspa) com backup + transação
├── vercel.json
├── README.md
└── CLAUDE.md                # contexto p/ continuar via banco (VPN)
```

---

## Dashboard

Tema "console operacional". Recursos:

- **KPIs** — total, pendentes, concluídas, por motivo, órgãos afetados.
- **Filtro por órgão** (com contagem) + **busca** + filtro por **motivo**.
- **Agrupamento por órgão** com progresso por grupo.
- **Editar ↗** — abre `admin.ms.gov.br/locais_atendimento/editar/<slug>`.
- **Copiar fix** — copia o `source` já corrigido.
- **Checklist** persistente (localStorage).

---

## Dois caminhos de detecção

| | **API** (este repo, padrão) | **Banco** (`sql/`) |
|---|---|---|
| Acesso | Internet pública (Api-Key read-only) | Rede SETDIG (VPN) |
| Cobertura | Unidades ligadas a serviços | Tabela `gerenciamento_unidades` inteira |
| Correção | Manual no admin (links no dash) | `UPDATE` transacional |

O caminho via banco é mais completo — ver **[CLAUDE.md](CLAUDE.md)**.

---

## Segurança

- **Nenhuma credencial** de banco no repo — usar **variáveis de ambiente**.
- A `Api-Key` do CMS é **pública** (já vai no bundle da SPA) e **só leitura**.
