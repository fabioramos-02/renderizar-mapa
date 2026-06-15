-- =====================================================================
-- Fix: remover aspa dupla inicial do campo `source` (Source do Mapa)
-- Tabela: gerenciamento_unidades  (DB admin_prd)
-- Causa: source colado com `src="` deixou `"` no inicio -> iframe.src
--        invalido -> Google 404. Tirar a aspa inicial resolve.
-- Afeta TODAS as unidades da tabela (todos os servicos), nao so o 424.
-- =====================================================================
-- PRE-REQUISITOS:
--   * usuario com permissao de UPDATE
--   * rodar de dentro da rede SETDIG (host s0845.ms e interno)
--   * conferir o dry-run ANTES de COMMIT
-- =====================================================================

BEGIN;

-- 1) Backup dos registros afetados (rollback manual se precisar)
CREATE TABLE IF NOT EXISTS bkp_unidades_source_20260615 AS
SELECT slug_unidade, source, now() AS bkp_at
FROM gerenciamento_unidades
WHERE source ~ '^\s*"';

-- 2) DRY-RUN: quantos serao corrigidos + amostra
SELECT count(*) AS total_a_corrigir
FROM gerenciamento_unidades
WHERE source ~ '^\s*"';

SELECT slug_unidade, left(source, 25) AS antes
FROM gerenciamento_unidades
WHERE source ~ '^\s*"'
LIMIT 5;

-- 3) FIX: remove espacos a esquerda + a 1a aspa (simples ou dupla)
UPDATE gerenciamento_unidades
SET source = regexp_replace(source, '^\s*["'']', '')
WHERE source ~ '^\s*"';

-- 4) VERIFICACAO: deve retornar 0
SELECT count(*) AS restantes_com_aspa
FROM gerenciamento_unidades
WHERE source ~ '^\s*"';

-- 5) Se total_a_corrigir batia e restantes = 0  -> COMMIT
--    Caso contrario                            -> ROLLBACK
COMMIT;
-- ROLLBACK;

-- =====================================================================
-- NAO resolvidos por este script (tratar a parte, embed novo):
--   pmms126  -> source = texto "nao encontrado"
--   7o-batalhao-de-policia-militar46 -> URL /maps/place (bloqueada em iframe)
-- Rollback de emergencia (se preciso):
--   UPDATE gerenciamento_unidades g
--   SET source = b.source
--   FROM bkp_unidades_source_20260615 b
--   WHERE g.slug_unidade = b.slug_unidade;
-- =====================================================================
