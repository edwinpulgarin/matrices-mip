"""
Lista de chequeo de las matrices: cuáles quedan cerradas y cuáles pendientes.

Cruza los controles que ya existen —no vuelve a calcular nada— y arma un
`reports/CHECKLIST.md` con una casilla por matriz para ir marcando en la
revisión con el equipo:

    manifest_publicables.csv       las siete verificaciones sobre el Excel
    reports/estado_ras.csv         cómo se cerró el cuadro (RAS o no)
    reports/cobertura.csv          ¿leímos toda la utilización publicada?
    reports/validacion_oficiales.csv   contraste contra la MIP del instituto

**Las marcas que ustedes pongan se conservan.** El script lee el archivo
anterior, se queda con las casillas tildadas y las vuelve a escribir. Así se
puede regenerar sin perder la revisión hecha: lo automático se recalcula, lo
humano se respeta.

Uso:  py -3 scripts/checklist.py
"""

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SALIDA = ROOT / "reports" / "CHECKLIST.md"


def _csv(ruta, clave):
    if not ruta.exists():
        return {}
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        return {clave(r): r for r in csv.DictReader(fh)}


def _marcadas(ruta: Path) -> set[str]:
    """Los identificadores ya tildados en el archivo anterior."""
    if not ruta.exists():
        return set()
    marcadas = set()
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*-\s*\[[xX]\]\s.*`([^`]+)`", linea)
        if m:
            marcadas.add(m.group(1))
    return marcadas


def main():
    libros = []
    with open(ROOT / "manifest_publicables.csv", encoding="utf-8-sig", newline="") as fh:
        libros = list(csv.DictReader(fh))

    ras = _csv(ROOT / "reports" / "estado_ras.csv", lambda r: (r["pais"], r["anio"]))
    cob = _csv(ROOT / "reports" / "cobertura.csv", lambda r: (r["pais"], r["anio"]))
    ofi = {}
    f_ofi = ROOT / "reports" / "validacion_oficiales.csv"
    if f_ofi.exists():
        with open(f_ofi, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                ofi.setdefault(r["caso"], []).append(r)

    ya = _marcadas(SALIDA)

    def pais_csv(p):
        return "México" if p == "Mexico" else p

    listas, revisar = [], []
    for lb in libros:
        pais, anio = lb["pais"], lb["anio"]
        ident = f"{pais} {anio}" + (f" {lb['variante']}" if lb.get("variante") == "OFICIAL" else "")
        k = (pais_csv(pais), anio)
        r_ras = ras.get(k, {})
        r_cob = cob.get(k, {})
        comp = ofi.get(f"{pais_csv(pais)} {anio}", [])

        modo = r_ras.get("modo", "—")
        notas = []
        pendiente = []

        if lb["estado"] != "CONSISTENTE":
            pendiente.append("no pasa las siete verificaciones")
        else:
            notas.append("7/7 verificaciones")

        if lb.get("variante") == "OFICIAL":
            notas.append("matriz publicada por el instituto")
        elif modo == "RAS":
            pendiente.append(f"usa RAS (mueve {100 * float(r_ras.get('mueve', 0)):.3f} % de U)")
        elif modo == "discrepancia":
            notas.append(f"sin tocar celdas · discrepancia {100 * float(r_ras.get('discrepancia', 0)):.3f} %")
        elif modo == "no hizo falta":
            notas.append("el cuadro cerraba solo")

        if r_cob:
            if r_cob.get("ok") == "si":
                notas.append("cobertura ✓")
            else:
                pendiente.append("cobertura de la fuente a revisar")

        for c in comp:
            dif = float(c.get("dif_suma_pct", 0))
            notas.append(f"vs oficial ({c['objeto']}) {dif:+.2f} %")

        linea = (f"- [{'x' if ident in ya else ' '}] **{ident}** · `{ident}` · "
                 + " · ".join(notas + [f"**{p}**" for p in pendiente]))
        (revisar if pendiente else listas).append(linea)

    md = [
        "# Lista de chequeo de las matrices\n",
        "Una casilla por matriz, para ir marcando en la revisión con el equipo. "
        "**Las marcas se conservan** cuando se regenera el archivo: el script lee las "
        "casillas tildadas y las vuelve a escribir.\n",
        "No calcula nada: cruza los controles que ya corrieron "
        "(`manifest_publicables.csv`, `estado_ras.csv`, `cobertura.csv` y "
        "`validacion_oficiales.csv`). Para actualizarlo, correr esos y después:\n",
        "```\npy -3 scripts/checklist.py\n```\n",
        f"## Listas para cerrar ({len(listas)})\n",
        "Pasan las siete verificaciones sobre el Excel, leen toda la utilización que la "
        "fuente publica y **no necesitaron el RAS**: la matriz se arma sin modificar "
        "ninguna celda leída.\n",
    ]
    md += sorted(listas) or ["_(ninguna)_"]
    md += [
        "",
        f"## Revisar antes de cerrar ({len(revisar)})\n",
        "Cada línea dice qué falta. No significa que estén mal: significa que hay una "
        "decisión que tomar o un dato que mirar antes de darlas por cerradas.\n",
    ]
    md += sorted(revisar) or ["_(ninguna)_"]
    md += [
        "",
        "## Cómo se decide\n",
        "| Criterio | Dónde se verifica |",
        "|:--|:--|",
        "| Las siete verificaciones sobre el Excel entregado | `reports/validacion_consistencia.md` |",
        "| Leímos toda la utilización que publica la fuente | `reports/cobertura_fuentes.md` |",
        "| Cómo se cerró el cuadro (sin tocar celdas o con RAS) | `reports/estado_ras.md` |",
        "| Contraste contra la MIP que publica el instituto | `reports/validacion_oficiales.md` |",
        "",
    ]
    SALIDA.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"[OK] {SALIDA.relative_to(ROOT)}  "
          f"({len(listas)} listas / {len(revisar)} a revisar · "
          f"{len(ya)} marcas conservadas)")


if __name__ == "__main__":
    main()
