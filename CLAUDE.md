# CLAUDE.md — contexto do projeto `renderizar-mapa`

Guia para continuar o trabalho em **outra máquina** (com VPN + acesso ao banco).
Leia antes de agir.

## Objetivo

Detectar e corrigir unidades de atendimento **ativas** do Portal ms.gov.br cujo
campo **Source do Mapa** (`gerenciamento_unidades.source`) está incorreto e
renderiza **404** no lugar do mapa.

## Causa raiz e critério

`source` deveria ser uma URL `https://www.google.com/maps/embed?pb=...`.
Está incorreto quando:

| motivo | condição | correção |
|---|---|---|
| `aspa-inicial` | começa com `"` ou `'` (resíduo do `src="`) | remover a aspa inicial |
| `tag-iframe` | contém `<iframe ...>` | extrair só a URL do `src=` |
| `nao-embed` | URL não-`/maps/embed` (place/dir/search/short) | gerar `/maps/embed` novo |
| `sem-source` | vazio / texto | gerar embed novo |

## Dois caminhos

### 1) API (já implementado — roda em qualquer rede)
- Auth: header `Authorization: Api-Key <KEY>` — key **pública** (no bundle da SPA), **só leitura**.
- `python scripts/gerar_relatorio.py` → `data/unidades_incorretas.{json,csv}` + `data/_meta.json`.
- `python scripts/gen_dashboard.py` → `dashboard/index.html`.
- Limitação: só vê unidades **ligadas a serviços** (enumera via `/api/cms/servicos/?page=N`; órgão vem de `orgao_sigla`). Não há endpoint list-all de unidades.
- A correção em si é **manual no admin** (o dashboard dá o link `editar/<slug>` por unidade).

### 2) Banco (preferido para cobertura total — exige VPN)
- Host **`s0845.ms`** é **interno** → só resolve dentro da rede SETDIG.
- Tabela `gerenciamento_unidades` tem: `slug_unidade, nome, endereco, complemento, bairro, cep, ativo, source, cidade_id, orgao_id, user_id, ...`.
- **Levantamento:** `sql/deteccao.sql` (todas ativas incorretas, por motivo/órgão).
- **Correção (aspa):** `sql/correcao.sql` — transação com backup + `UPDATE ... regexp_replace(source,'^\s*["'']','')`. Conferir dry-run antes do COMMIT.
- Para resolver o nome do **órgão** no relatório DB: a tabela só tem `orgao_id`. Descobrir a tabela de órgãos (ex.: `information_schema.columns WHERE column_name ILIKE '%sigla%'`) e fazer JOIN, **ou** reaproveitar o mapa `orgao_id→sigla` que a API expõe via serviços.

### Próximo passo sugerido (na máquina com VPN)
Portar `scripts/gerar_relatorio.py` para uma versão **DB** (`psycopg2`) usando
`sql/deteccao.sql`, gerando o mesmo `data/unidades_incorretas.json` — assim o
dashboard funciona igual, com cobertura org-wide.

## Credenciais (NUNCA commitar)

Usar **variáveis de ambiente**:

```bash
# Banco (caminho 2)
export DB_HOST=s0845.ms DB_PORT=5432 DB_USER=<user> DB_PASSWORD=<senha> DB_NAME=admin_prd
# API (caminho 1) — opcional, tem default público no script
export CMS_API_KEY=<api-key>
```

`.gitignore` já cobre `.env`. **Não** colocar senha em arquivo versionado.

## Segurança / pendências
- A senha do banco e a Api-Key foram expostas em chat durante o desenvolvimento → **rotacionar**.
- PMMS (serviço 424): 57/68 já corrigidas nesta primeira rodada; 11 `aspa` ficaram para correção manual. Rodar `gerar_relatorio.py` mostra o estado atual.

## Comandos
```bash
pip install requests
python scripts/gerar_relatorio.py
python scripts/gen_dashboard.py
start dashboard/index.html   # Windows
```
