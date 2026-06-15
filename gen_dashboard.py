# -*- coding: utf-8 -*-
import json, html, urllib.parse

data = json.load(open("unidades-424-fix.json", encoding="utf-8"))
if isinstance(data, str):
    data = json.loads(data)
EDIT = "https://admin.ms.gov.br/locais_atendimento/editar/"
bad = [r for r in data if r["motivo"] != "OK"]

for r in bad:
    if r["source_corrigido"] == "__GERAR_EMBED__":
        q = ", ".join([x for x in [r["endereco"], r["bairro"], "Mato Grosso do Sul"] if x and x.strip()])
        r["source_corrigido"] = "https://www.google.com/maps?q=" + urllib.parse.quote(q) + "&output=embed"
        r["precisa_revisar"] = True
    else:
        r["precisa_revisar"] = False

badge_map = {
    "aspa-inicial": "aspa inicial",
    "maps/place": "/maps/place",
    "sem-url": 'texto "nao encontrado"',
    "url-nao-embed": "url nao-embed",
}

rows = ""
for i, r in enumerate(bad, 1):
    cls = "aspa" if r["motivo"] == "aspa-inicial" else "place"
    badge = badge_map.get(r["motivo"], r["motivo"])
    rev = ' <span class="warn">! revisar endereco</span>' if r["precisa_revisar"] else ""
    search = (r["slug"] + " " + (r["local"] or "") + " " + (r["endereco"] or "") + " " + (r["bairro"] or "")).lower()
    rows += (
        '<tr data-motivo="%s" data-search="%s">' % (html.escape(r["motivo"]), html.escape(search))
        + '<td class="chk"><input type="checkbox" data-slug="%s"></td>' % html.escape(r["slug"])
        + '<td class="n">%d</td>' % i
        + '<td><b>%s</b><div class="sub">%s</div></td>' % (html.escape(r["local"] or ""), html.escape(r["slug"]))
        + '<td>%s<div class="sub">%s</div></td>' % (html.escape(r["endereco"] or ""), html.escape(r["bairro"] or ""))
        + '<td><span class="badge %s">%s</span>%s</td>' % (cls, badge, rev)
        + '<td><a class="edit" href="%s%s" target="_blank" rel="noopener">Editar &#8599;</a></td>' % (EDIT, html.escape(r["slug"]))
        + '<td><button class="copy" data-src="%s">Copiar source</button></td>' % html.escape(r["source_corrigido"], quote=True)
        + "</tr>"
    )

n_aspa = sum(1 for r in bad if r["motivo"] == "aspa-inicial")
n_esp = len(bad) - n_aspa

tpl = open("dashboard_template.html", encoding="utf-8").read()
out = (tpl
    .replace("{{BAD}}", str(len(bad)))
    .replace("{{NASPA}}", str(n_aspa))
    .replace("{{NESP}}", str(n_esp))
    .replace("{{ROWS}}", rows))
open("dashboard-source-mapa.html", "w", encoding="utf-8").write(out)
print("OK -> dashboard-source-mapa.html | linhas:", len(bad))
