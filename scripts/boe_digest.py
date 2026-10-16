import sys, time, pathlib, datetime as dt
import requests

KW = ["evaluación ambiental","impacto ambiental","fotovoltaic","eólic","hidrógeno",
      "biogás","biometano","minería","minas","residuos","biodiversidad","red natura",
      "espacios naturales","fauna","flora","aguas","suelos","cambio climático",
      "huella de carbono","taxonomía","sostenibilidad","autorización ambiental",
      "energías renovables","almacenamiento","transición ecológica","dominio público hidráulico"]

def items(node):
    if isinstance(node, dict):
        if "identificador" in node and "titulo" in node:
            yield node
        for v in node.values():
            yield from items(v)
    elif isinstance(node, list):
        for v in node:
            yield from items(v)

def link(it):
    for k in ("url_html", "url_pdf"):
        u = it.get(k)
        if isinstance(u, dict):
            u = u.get("texto")
        if u:
            return u
    return ""

day = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().strftime("%Y%m%d")
url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{day}"
r = None
for attempt in range(5):
    try:
        r = requests.get(url, headers={"Accept": "application/json"}, timeout=60)
        if r.status_code in (200, 404):
            break
    except requests.RequestException as e:
        print("intento", attempt + 1, "error:", e)
    time.sleep(30 * (attempt + 1))

if r is None or r.status_code not in (200, 404):
    print("ERROR: no se pudo obtener el sumario", day)
    sys.exit(1)

out_dir = pathlib.Path("digest")
out_dir.mkdir(exist_ok=True)

if r.status_code == 404:
    text = f"# Sumario BOE {day}\n\nSin edición del BOE para esta fecha (404).\n"
else:
    todos = list(items(r.json()))
    sel = [i for i in todos if any(k in i["titulo"].lower() for k in KW)]
    lines = [f"# Sumario BOE filtrado {day}",
             f"Fuente: {url}",
             f"Disposiciones totales: {len(todos)} | Coincidencias con palabras clave: {len(sel)}",
             "Filtro solo por palabras clave en el título: puede dejar fuera normas relevantes.\n"]
    lines += [f"- {i['identificador']} | {i['titulo']} | {link(i)}" for i in sel]
    text = "\n".join(lines) + "\n"

(out_dir / f"{day}.md").write_text(text, encoding="utf-8")
(out_dir / "latest.md").write_text(text, encoding="utf-8")
print(text)
