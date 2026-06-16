-- =====================================================================
-- correcao.sql — Corrige o "Source do Mapa" das unidades com aspa inicial.
-- Tabela: gerenciamento_unidades  (DB admin_prd)
--
-- Resolve SOMENTE o caso "aspa-inicial" (de longe o mais comum): o campo
-- começa com `"` por causa do `src="` colado junto. Remover a aspa já faz
-- o mapa renderizar.
--
-- NÃO resolve (tratar à parte, embed novo via admin):
--   * tag-iframe   -> extrair só a URL do src="..."
--   * nao-embed    -> /maps/place|dir|search|short -> gerar /maps/embed
--   * sem-source   -> campo vazio / texto
--
-- PRÉ-REQUISITOS: usuário com UPDATE, rede SETDIG (VPN), backup + conferir
-- o dry-run ANTES do COMMIT. Credenciais por env vars (ver CLAUDE.md).
-- =====================================================================

BEGIN;

-- 1) Backup dos registros afetados
CREATE TABLE IF NOT EXISTS bkp_unidades_source_aspa AS
SELECT slug_unidade, source, now() AS bkp_at
FROM gerenciamento_unidades
WHERE source ~ '^\s*["'']';

-- 2) DRY-RUN: quantos serão corrigidos + amostra
SELECT count(*) AS total_a_corrigir
FROM gerenciamento_unidades
WHERE source ~ '^\s*["'']';

SELECT slug_unidade, left(source, 25) AS antes
FROM gerenciamento_unidades
WHERE source ~ '^\s*["'']'
LIMIT 5;

-- 3) FIX: remove espaços à esquerda + a 1ª aspa (simples ou dupla)
UPDATE gerenciamento_unidades
SET source = regexp_replace(source, '^\s*["'']', '')
WHERE source ~ '^\s*["'']';

-- 4) VERIFICAÇÃO: deve retornar 0
SELECT count(*) AS restantes_com_aspa
FROM gerenciamento_unidades
WHERE source ~ '^\s*["'']';

-- 5) total_a_corrigir batia e restantes = 0  -> COMMIT ; senão -> ROLLBACK
COMMIT;
-- ROLLBACK;

-- Rollback de emergência (restaura do backup):
--   UPDATE gerenciamento_unidades g
--   SET source = b.source
--   FROM bkp_unidades_source_aspa b
--   WHERE g.slug_unidade = b.slug_unidade;
