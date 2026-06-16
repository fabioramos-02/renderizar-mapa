#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_dashboard.py — Gera dashboard/index.html a partir de data/unidades_incorretas.json
e do template dashboard/template.html. O dashboard é estático e self-contained
(dados embutidos), com filtro por órgão, busca, agrupamento e checklist local.

Uso:
    python scripts/gen_dashboard.py
"""
import os
import re
import json
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "unidades_incorretas.json")
TPL = os.path.join(ROOT, "dashboard", "template.html")
OUT = os.path.join(ROOT, "dashboard", "index.html")
META = os.path.join(ROOT, "data", "_meta.json")


def main():
    data = json.load(open(DATA, encoding="utf-8"))
    tpl = open(TPL, encoding="utf-8").read()

    n_serv = n_uni = "—"
    if os.path.exists(META):
        m = json.load(open(META, encoding="utf-8"))
        n_serv, n_uni = m.get("n_servicos", "—"), m.get("n_unidades", "—")

    gen_at = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    # Embed seguro em <script>: neutraliza "</script>" e "<iframe" no JSON.
    data_json = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    html = (tpl
            .replace("{{DATA_JSON}}", data_json)
            .replace("{{GENERATED_AT}}", gen_at)
            .replace("{{N_SERVICOS}}", str(n_serv))
            .replace("{{N_UNIDADES}}", str(n_uni)))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK -> {OUT} | {len(data)} unidades")


if __name__ == "__main__":
    main()
