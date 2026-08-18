"""
Tests del control de cobertura de la fuente (src/cobertura.py).

Lo que se protege: que una columna de la fuente que ningún patrón del parser
reclame no pueda pasar en silencio. El modo de falla real fue «Trabajos en
curso» del INDEC —los cultivos en pie— que estuvo seis años sin leerse; el
balanceo cerraba la fila igual y nada chillaba.

El control tiene que distinguir dos cosas que se parecen en los números:
  * columna perdida  -> faltante de UN SOLO signo, se ve en el neto
  * reasignación de la fuente entre productos vecinos -> pares que se cancelan,
    se ve en el bruto pero no en el neto, y no es un error nuestro

Uso:  py -3 tests/test_cobertura.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import pandas as pd

from src.cobertura import TOL_NETO, CoberturaIncompleta, columnas_no_leidas, verificar

FALLOS = []


def _assert(cond, msg):
    print(f"  {'OK ' if cond else 'FALLO'}  {msg}")
    if not cond:
        FALLOS.append(msg)


def _cou(uso_extra=0.0, reasignar=0.0):
    """COU mínimo de 3 productos × 2 industrias que cierra exacto.

    `uso_extra` resta uso a un producto (simula una columna no leída).
    `reasignar` mueve uso de un producto a otro (simula la reasignación de la
    fuente: cambia el bruto, deja el neto en cero).
    """
    prod = ["p1", "p2", "p3"]
    U = pd.DataFrame([[10.0, 5.0], [4.0, 6.0], [2.0, 3.0]], index=prod, columns=["i1", "i2"])
    Y = pd.DataFrame([[20.0], [10.0], [5.0]], index=prod, columns=["consumo"])
    opc = U.sum(axis=1) + Y.sum(axis=1)          # cierra por construcción
    Y = Y.copy()
    Y.iloc[0, 0] -= uso_extra                     # falta uso en p1 y en nadie más
    Y.iloc[1, 0] -= reasignar                     # sale de p2...
    Y.iloc[2, 0] += reasignar                     # ...y entra en p3
    return {"U_pc": U, "Y_pc": Y, "val": pd.DataFrame({"OPC": opc}),
            "prod_name": {p: p for p in prod}, "pais": "Test", "anio": 2020}


print("cobertura: el caso sano")
r = verificar(_cou())
_assert(r["aplica"] and r["ok"], "un COU que cierra pasa el control")
_assert(abs(r["neto_rel"]) < 1e-12, f"neto ~0 ({r['neto_rel']:.1e})")

print("\ncobertura: columna perdida")
falta = _cou(uso_extra=8.0)                       # 8 de un total de 65
try:
    verificar(falta)
    _assert(False, "una columna perdida tiene que levantar CoberturaIncompleta")
except CoberturaIncompleta as e:
    _assert(True, "una columna perdida levanta CoberturaIncompleta")
    _assert("p1" in str(e), "el mensaje nombra el producto afectado")

r = verificar(falta, estricto=False)
_assert(not r["ok"], "en modo no estricto queda marcado ok=False")
_assert(r["neto_rel"] > TOL_NETO, "el faltante se ve en el NETO")

print("\ncobertura: reasignación de la fuente (no es error de lectura)")
r = verificar(_cou(reasignar=6.0), estricto=False)
_assert(r["ok"], "una reasignación que se cancela NO dispara el control")
_assert(abs(r["neto_rel"]) < 1e-12, "el neto queda en cero")
_assert(r["bruto_rel"] > 0.1, f"pero el bruto sí la registra ({r['bruto_rel']:.2f})")

print("\ncobertura: fuentes sin puente de valoración")
r = verificar({"U_pc": pd.DataFrame(), "Y_pc": pd.DataFrame()}, estricto=False)
_assert(not r["aplica"], "sin OPC el control se declara no aplicable en vez de inventar")

print("\ncolumnas_no_leidas")
enc = ["Consumo hogares", "Exportaciones", "Trabajos en curso", "DEMANDA TOTAL"]
sin = columnas_no_leidas(enc, {"Consumo hogares", "Exportaciones"}, ignorar=("DEMANDA TOTAL",))
_assert(sin == ["Trabajos en curso"], f"detecta la columna sin reclamar (dio {sin})")

print()
if FALLOS:
    print(f"{len(FALLOS)} FALLO(S):")
    for f in FALLOS:
        print(f"  - {f}")
    sys.exit(1)
print("TODOS LOS TESTS PASARON")
