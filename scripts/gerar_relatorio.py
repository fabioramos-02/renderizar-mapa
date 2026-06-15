#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gerar_relatorio.py — Detecta unidades de atendimento ATIVAS com "Source do Mapa"
incorreto no CMS do Portal ms.gov.br, via API pública (Api-Key read-only).

Critério de incorreto (definido com a SETDIG):
  - source vazio/None                  -> motivo "sem-source"
  - source começa com aspa (" ou ')    -> motivo "aspa-inicial"  (iframe.src vira "http -> 404)
  - source contém a tag "<iframe"      -> motivo "tag-iframe"     (snippet inteiro no campo)
  - URL não é /maps/embed (place/dir…) -> motivo "nao-embed"      (bloqueado em iframe -> 404)

Enumera TODAS as unidades ativas percorrendo os serviços do CMS (não há list-all de
unidades). O órgão é herdado do serviço (orgao_sigla).

Saída: data/unidades_incorretas.json e data/unidades_incorretas.csv

Uso:
    python scripts/gerar_relatorio.py
Env (opcionais):
    CMS_API_BASE  (default https://admin.ms.gov.br/api/cms)
    CMS_API_KEY   (default a key pública embutida na SPA)
"""
import os
import re
import csv
import json
import sys
import time

try:
    import requests
except ImportError:
    sys.exit("Instale 'requests': pip install requests")

API_BASE = os.environ.get("CMS_API_BASE", "https://admin.ms.gov.br/api/cms").rstrip("/")
API_KEY = os.environ.get("CMS_API_KEY", "8tqFBwkS.6eLeClPnZvZEioz7ghV4GuNvvPPf4GMG")
ADMIN_EDIT = "https://admin.ms.gov.br/locais_atendimento/editar/"

HEADERS = {"Authorization": f"Api-Key {API_KEY}", "Accept": "application/json"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get_json(url, tries=4):
    last = None
    for i in range(tries):
        try:
            r = SESSION.get(url, timeout=30)
            if r.status_code == 200:
                return r.json()
            last = f"HTTP {r.status_code}"
        except Exception as e:  # noqa
            last = str(e)
        time.sleep(0.8 * (i + 1))
    print(f"  ! falha em {url}: {last}", file=sys.stderr)
    return None


def iter_servicos():
    """Percorre /servicos/?page=N retornando cada serviço (com servicosUnidade)."""
    page = 1
    while True:
        data = get_json(f"{API_BASE}/servicos/?page={page}")
        if not data:
            break
        results = data.get("results") if isinstance(data, dict) else data
        if not results:
            break
        for s in results:
            yield s
        # paginação DRF
        if isinstance(data, dict) and data.get("next"):
            page += 1
        else:
            break


SRC_RE = re.compile(r'src\s*=\s*["\']([^"\']+)["\']', re.I)
URL_RE = re.compile(r'(https?://[^"\'\s>]+)', re.I)


def extrai_url(source):
    if not source:
        return None
    s = str(source).strip()
    m = SRC_RE.search(s)
    if m:
        return m.group(1)
    m = URL_RE.search(s)
    return m.group(1) if m else None


def classifica(source):
    """Retorna (incorreto: bool, motivo: str, corrigido: str)."""
    if source is None or not str(source).strip():
        return True, "sem-source", "__GERAR_EMBED__"
    s = str(source)
    t = s.strip()
    # OK: começa direto no embed
    if re.match(r'^https?://(www\.)?google\.[^/]*/maps/embed\?', t, re.I):
        return False, "ok", s
    # aspa inicial (com ou sem <iframe depois)
    if re.match(r'^["\']', t):
        url = extrai_url(t) or ""
        corrigido = url if "/maps/embed" in url else re.sub(r'^\s*["\']', '', t)
        return True, "aspa-inicial", corrigido
    # tag <iframe ...>
    if "<iframe" in t.lower():
        url = extrai_url(t)
        return True, "tag-iframe", (url or "__GERAR_EMBED__")
    # url que não é embed (place/dir/search/short)
    if re.match(r'^https?://', t, re.I):
        return True, "nao-embed", "__GERAR_EMBED__"
    return True, "sem-source", "__GERAR_EMBED__"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Coletando serviços de {API_BASE} ...")
    unidades = {}  # slug -> dict
    n_serv = 0
    for serv in iter_servicos():
        n_serv += 1
        orgao = serv.get("orgao_sigla") or serv.get("orgao_nome") or "—"
        for su in (serv.get("servicosUnidade") or []):
            un = su.get("unidade") or {}
            slug = un.get("slug_unidade")
            if not slug:
                continue
            rec = unidades.get(slug)
            if not rec:
                rec = {
                    "slug": slug,
                    "nome": un.get("complemento") or un.get("nome") or "",
                    "endereco": un.get("endereco") or "",
                    "bairro": un.get("bairro") or "",
                    "ativo": bool(un.get("ativo")),
                    "source_atual": un.get("source") or "",
                    "orgaos": set(),
                }
                unidades[slug] = rec
            rec["orgaos"].add(orgao)
        if n_serv % 25 == 0:
            print(f"  ... {n_serv} serviços, {len(unidades)} unidades")

    print(f"Total: {n_serv} serviços, {len(unidades)} unidades. Classificando...")
    incorretas = []
    for slug, rec in unidades.items():
        if not rec["ativo"]:
            continue
        bad, motivo, corrigido = classifica(rec["source_atual"])
        if not bad:
            continue
        incorretas.append({
            "slug": slug,
            "nome": rec["nome"],
            "endereco": rec["endereco"],
            "bairro": rec["bairro"],
            "orgao": " / ".join(sorted(rec["orgaos"])) or "—",
            "ativo": rec["ativo"],
            "motivo": motivo,
            "source_atual": rec["source_atual"],
            "source_corrigido": corrigido,
            "edit_url": ADMIN_EDIT + slug,
        })

    incorretas.sort(key=lambda r: (r["orgao"], r["motivo"], r["nome"]))

    with open(os.path.join(DATA_DIR, "_meta.json"), "w", encoding="utf-8") as f:
        json.dump({"n_servicos": n_serv, "n_unidades": len(unidades),
                   "n_incorretas": len(incorretas)}, f, ensure_ascii=False, indent=2)

    out_json = os.path.join(DATA_DIR, "unidades_incorretas.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(incorretas, f, ensure_ascii=False, indent=2)

    cols = ["slug", "nome", "endereco", "bairro", "orgao", "motivo",
            "source_atual", "source_corrigido", "edit_url"]
    out_csv = os.path.join(DATA_DIR, "unidades_incorretas.csv")
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        for r in incorretas:
            w.writerow({k: r.get(k, "") for k in cols})

    # resumo
    from collections import Counter
    by_motivo = Counter(r["motivo"] for r in incorretas)
    by_orgao = Counter(r["orgao"] for r in incorretas)
    print(f"\nIncorretas: {len(incorretas)}")
    print("Por motivo:", dict(by_motivo))
    print("Órgãos afetados:", len(by_orgao))
    print(f"-> {out_json}\n-> {out_csv}")


if __name__ == "__main__":
    main()
