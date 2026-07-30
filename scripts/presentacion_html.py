"""
Genera la presentación HTML de resultados desde output/resultados.json.

El HTML es autocontenido —datos, estilos y scripts incrustados, sin una sola
petición a otro host— así que el archivo se puede mandar por correo, abrir sin
conexión o imprimir a PDF con Ctrl+P.

Se emiten dos archivos con el mismo contenido y distinta envoltura:

    presentacion.html           documento completo, con <!doctype> y <head>.
                                Es el que se exporta y se comparte.
    presentacion_fragmento.html sin esas etiquetas, porque el publicador de
                                artefactos añade su propio esqueleto y rechaza
                                un documento anidado.

Uso:  py -3 scripts/presentacion_html.py
      (antes: py -3 scripts/resultados_presentacion.py)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

PLANTILLA = ROOT / "src" / "presentacion" / "plantilla.html"
DATOS = ROOT / "output" / "resultados.json"
SALIDA = ROOT / "output" / "presentacion.html"
SALIDA_FRAG = ROOT / "output" / "presentacion_fragmento.html"

TITULO = "MIP · Cinco economías reconstruidas desde sus COU"

# El <head> vive acá y no en la plantilla porque la plantilla tiene que seguir
# siendo publicable como fragmento. Sólo el documento exportable lo lleva.
ENVOLTURA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Multiplicadores y encadenamientos de treinta \
matrices insumo-producto de Argentina, Brasil, Colombia, México y Uruguay.">
<meta name="color-scheme" content="light dark">
<style>*,*::before,*::after{{box-sizing:border-box}}body{{margin:0}}</style>
{cuerpo}
</html>
"""


def main():
    if not DATOS.exists():
        sys.exit(f"falta {DATOS}. Corré antes scripts/resultados_presentacion.py")
    datos = json.loads(DATOS.read_text(encoding="utf-8"))
    compacto = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
    frag = PLANTILLA.read_text(encoding="utf-8").replace("/*__DATOS__*/", compacto)

    # El <title> de la plantilla queda dentro del <head>; el resto pasa al body.
    cuerpo = frag.replace(f"<title>{TITULO}</title>",
                          f"<title>{TITULO}</title>\n</head>\n<body>", 1)
    if "</head>" not in cuerpo:            # la plantilla cambió de título
        sys.exit(f"no se encontró el <title> esperado en {PLANTILLA.name}")
    completo = ENVOLTURA.format(cuerpo=cuerpo.rstrip() + "\n</body>")

    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(completo, encoding="utf-8")
    SALIDA_FRAG.write_text(frag, encoding="utf-8")
    kb = len(completo.encode("utf-8")) / 1024
    print(f"[OK] {SALIDA.relative_to(ROOT)} · {kb:,.0f} KB · "
          f"{len(datos['paises'])} países (documento completo, exportable)")
    print(f"[OK] {SALIDA_FRAG.relative_to(ROOT)} · para publicar como artefacto")


if __name__ == "__main__":
    main()
