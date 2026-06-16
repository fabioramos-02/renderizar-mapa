-- =====================================================================
-- deteccao.sql — Levanta unidades de atendimento ATIVAS com
-- "Source do Mapa" (coluna source) incorreto.
-- Tabela: gerenciamento_unidades  (DB admin_prd)
--
-- Critério de incorreto (mesmo do script Python):
--   * source vazio/NULL
--   * começa com aspa  (" ou ')        -> iframe.src vira "http -> 404
--   * contém a tag "<iframe"           -> snippet inteiro colado no campo
--   * URL que NÃO é /maps/embed        -> place/dir/search/short -> bloqueado em iframe
--
-- Rodar de dentro da rede SETDIG (host s0845.ms é interno / VPN).
-- Credenciais por variáveis de ambiente — ver CLAUDE.md.
-- =====================================================================

SELECT
    u.slug_unidade,
    u.complemento,
    u.endereco,
    u.bairro,
    u.orgao_id,
    u.cidade_id,
    CASE
        WHEN u.source IS NULL OR btrim(u.source) = ''            THEN 'sem-source'
        WHEN u.source ~ '^\s*["'']'                              THEN 'aspa-inicial'
        WHEN u.source ILIKE '%<iframe%'                          THEN 'tag-iframe'
        WHEN u.source !~* '^https?://(www\.)?google\.[^/]*/maps/embed\?' THEN 'nao-embed'
        ELSE 'ok'
    END AS motivo,
    left(u.source, 40) AS source_preview
FROM gerenciamento_unidades u
WHERE u.ativo IS TRUE
  AND (
        u.source IS NULL
     OR btrim(u.source) = ''
     OR u.source ~ '^\s*["'']'
     OR u.source ILIKE '%<iframe%'
     OR u.source !~* '^https?://(www\.)?google\.[^/]*/maps/embed\?'
  )
ORDER BY u.orgao_id, motivo, u.complemento;

-- Resumo por órgão + motivo:
-- SELECT u.orgao_id,
--   CASE WHEN u.source ~ '^\s*["'']' THEN 'aspa-inicial'
--        WHEN u.source ILIKE '%<iframe%' THEN 'tag-iframe'
--        WHEN u.source IS NULL OR btrim(u.source)='' THEN 'sem-source'
--        ELSE 'nao-embed' END AS motivo,
--   count(*)
-- FROM gerenciamento_unidades u
-- WHERE u.ativo IS TRUE AND u.source !~* '^https?://(www\.)?google\.[^/]*/maps/embed\?'
-- GROUP BY 1,2 ORDER BY 1,2;
