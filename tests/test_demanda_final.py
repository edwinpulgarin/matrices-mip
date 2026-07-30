"""
Tests del esquema armonizado de demanda final (src/demanda_final.py).

El invariante que importa: armonizar es una REAGRUPACIÓN de columnas, nunca un
recálculo. Si `Y.sum(axis=1)` cambiara, `Σ Y = f` dejaría de cumplirse y la MIP
quedaría inconsistente.

Uso:  py -3 tests/test_demanda_final.py
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

import numpy as np
import pandas as pd

from src.demanda_final import COLUMNAS, armonizar, clasificar, etiqueta

FALLOS = []


def _assert(cond, msg):
    print(f"  {'OK ' if cond else 'FALLO'}  {msg}")
    if not cond:
        FALLOS.append(msg)


# Encabezados reales de las cuatro fuentes nacionales.
FUENTES = {
    "Argentina": ["consumo_hogares", "consumo_gobierno", "exportaciones",
                  "formacion_capital", "objetos_valiosos", "var_existencias"],
    "Brasil": ["Exportação de bens e serviços (1)", "Consumo do governo",
               "Consumo das ISFLSF", "Consumo das famílias",
               "Formação bruta de capital fixo", "Variação de estoque"],
    "Uruguay": ["Gasto de Consumo Final Hogares",
                "Gasto de Consumo Final del Gobierno e ISFLSH",
                "Formación Bruta de Capital Fijo", "Variación de Existencias1",
                "Exportaciones"],
    # MUPNI parte el encabezado en dos filas ('Exportaciones' / 'Bienes'); el
    # parser compone el nombre completo, si no 'Servicios' a secas es inclasificable
    "Colombia": ["Gasto de consumo final", "Formación bruta de capital",
                 "Exportaciones Bienes", "Exportaciones Servicios"],
    "México": ["CP - Consumo Privado", "CG - Consumo de gobierno",
               "P.51b - Formación bruta de capital fijo",
               "P.52 - Variación de existencias",
               "c P.6 - Exportaciones de bienes y servicios",
               "YA0 - Discrepancia estadística"],
}

ESPERADO = {
    "consumo_hogares": "consumo_final",
    "Consumo das ISFLSF": "consumo_final",
    "Gasto de Consumo Final del Gobierno e ISFLSH": "consumo_final",
    "CP - Consumo Privado": "consumo_final",
    "formacion_capital": "formacion_bruta_capital",
    "Formação bruta de capital fixo": "formacion_bruta_capital",
    "objetos_valiosos": "formacion_bruta_capital",
    "Variação de estoque": "formacion_bruta_capital",
    "Variación de Existencias1": "formacion_bruta_capital",
    "Exportação de bens e serviços (1)": "exportaciones",
    "c P.6 - Exportaciones de bienes y servicios": "exportaciones",
    "YA0 - Discrepancia estadística": "discrepancia_estadistica",
}


def main():
    rng = np.random.default_rng(0)

    print("Clasificación de encabezados reales")
    for col, esperado in ESPERADO.items():
        _assert(clasificar(col) == esperado, f"{col[:44]:44s} -> {esperado}")

    print("\nInvariante: armonizar conserva la suma por fila")
    for pais, cols in FUENTES.items():
        Y = pd.DataFrame(rng.random((40, len(cols))) * 1000,
                         index=[f"p{i}" for i in range(40)], columns=cols)
        H = armonizar(Y)
        gap = float((H.sum(axis=1) - Y.sum(axis=1)).abs().max())
        _assert(gap < 1e-9, f"{pais}: Σ filas intacta (gap={gap:.1e})")
        _assert(list(H.columns) == COLUMNAS, f"{pais}: esquema idéntico y ordenado")
        _assert(len(H) == len(Y), f"{pais}: no pierde ni agrega filas")

    print("\nCasos borde")
    # una fuente que no distingue discrepancia estadística deja la columna en 0
    Y = pd.DataFrame({"consumo_hogares": [1.0, 2.0], "exportaciones": [3.0, 4.0]})
    H = armonizar(Y)
    _assert(float(H["discrepancia_estadistica"].abs().sum()) == 0.0,
            "componente ausente en la fuente queda en cero, no NaN")
    _assert(float(H["consumo_final"].sum()) == 3.0, "suma de un solo aportante")

    # varias columnas al mismo destino se acumulan, no se pisan
    Y = pd.DataFrame({"Consumo das famílias": [10.0], "Consumo do governo": [5.0],
                      "Consumo das ISFLSF": [1.0]})
    _assert(float(armonizar(Y)["consumo_final"].iloc[0]) == 16.0,
            "tres columnas de consumo se suman (10+5+1=16)")

    # una columna desconocida debe fallar fuerte, no colarse en silencio
    try:
        armonizar(pd.DataFrame({"Ingreso mixto bruto": [1.0]}))
        _assert(False, "columna desconocida lanza ValueError")
    except ValueError:
        _assert(True, "columna desconocida lanza ValueError")

    # Colombia (MUPNI) no separa FBKF de existencias: por eso el canónico es P.5
    Y = pd.DataFrame({"Formación bruta de capital": [7.0]})
    _assert(float(armonizar(Y)["formacion_bruta_capital"].iloc[0]) == 7.0,
            "FBK sin separar (MUPNI) entra en P.5")
    Y = pd.DataFrame({"formacion_capital": [4.0], "var_existencias": [2.0],
                      "objetos_valiosos": [1.0]})
    _assert(float(armonizar(Y)["formacion_bruta_capital"].iloc[0]) == 7.0,
            "P.51+P.52+P.53 separadas suman lo mismo (4+2+1=7)")

    _assert(all(etiqueta(c) for c in COLUMNAS), "toda columna canónica tiene etiqueta")

    if FALLOS:
        print(f"\n{len(FALLOS)} TESTS FALLARON")
        for m in FALLOS:
            print("  -", m)
        return 1
    print("\nTODOS LOS TESTS PASARON")
    return 0


if __name__ == "__main__":
    sys.exit(main())
