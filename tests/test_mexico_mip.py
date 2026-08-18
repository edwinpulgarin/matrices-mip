"""
Tests del lector de la MIP simétrica oficial de INEGI (src/parsers/mexico_mip.py).

Acá no se reconstruye nada, así que lo que hay que probar es distinto de los
otros parsers: que el cuadro publicado se lea COMPLETO y sin desalinearse. Las
dos maneras realistas de romperlo son (a) tomar una columna corrida —el layout
del XLSX de 2008 tiene columnas y filas en blanco de separación— y (b) leer la
matriz importada de un archivo cuyas industrias no coincidan con la doméstica.
Ambas se detectan porque dejan de cerrar las identidades del propio cuadro.

Se corre sobre los tres años y a nivel SECTOR, que son 20×20 y tarda segundos;
el nivel RAMA que se publica pasa por el mismo código.

Uso:  py -3 tests/test_mexico_mip.py
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

from src.parsers import mexico_mip
from src.transformacion import desde_mip_oficial
from src.analisis import calcular
from src import demanda_final as df_mod

FALLOS = []


def _assert(cond, msg):
    print(f"  {'OK   ' if cond else 'FALLO'}  {msg}")
    if not cond:
        FALLOS.append(msg)


def probar(anio: int, nivel: str = "SECTOR"):
    print(f"\n--- México {anio} ({nivel.lower()}) ---")
    d = mexico_mip.parse(anio, nivel=nivel)
    Z, x = d["Z"], d["x"]
    n = Z.shape[0]

    _assert(Z.shape[0] == Z.shape[1], f"Z es cuadrada ({n}×{n})")
    _assert(list(Z.index) == list(Z.columns), "filas y columnas de Z en el mismo orden")
    _assert(len(d["ind_name"]) >= n, "hay una denominación por industria")
    _assert(all(str(d["ind_name"].get(k, "")).strip() not in ("", str(k))
                for k in Z.columns), "ninguna denominación viene vacía")

    # el parser ya exige las identidades; acá se confirma cuán ajustado quedó
    _assert(d["residuo"] < 1e-12,
            f"identidades del cuadro oficial: peor residuo {d['residuo']:.1e} "
            f"(«{d['residuo_en']}»)")
    _assert(d["residuo_zm"] < 1e-12,
            f"la matriz importada cruza con la doméstica: {d['residuo_zm']:.1e}")

    # signos: una MIP publicada no debería traer flujos negativos
    _assert(float(Z.to_numpy().min()) >= 0, "Z sin valores negativos")
    _assert(float(x.min()) > 0, "toda industria tiene producción positiva")

    # el envoltorio IOT tiene que preservar los balances
    iot = desde_mip_oficial(d)
    escala = float(iot.x.sum())
    dif = float(iot.balance_fila_columna().abs().max()) / escala
    _assert(dif < 1e-12, f"balance fila = columna en la IOT: {dif:.1e}")
    _assert(abs(float(iot.f.sum() + iot.Z.to_numpy().sum() - escala)) / escala < 1e-12,
            "Σ Z + Σ f = producción total")

    an = calcular(iot)
    _assert(an.check_Lf_x / escala < 1e-9, f"L·f = x  ({an.check_Lf_x / escala:.1e})")
    _assert(float(an.A.sum(axis=0).max()) < 1.0, "Σᵢ aᵢⱼ < 1 en toda columna")

    # la demanda final tiene que caer entera en el esquema armonizado
    Yh = df_mod.armonizar(iot.Y)
    dif_y = float((Yh.sum(axis=1) - iot.Y.sum(axis=1)).abs().max()) / escala
    _assert(dif_y < 1e-12, f"armonizar la demanda final conserva la suma: {dif_y:.1e}")

    return d


def main():
    print("Tests — MIP simétrica oficial de INEGI")
    lecturas = {}
    for anio in (2008, 2013, 2018):
        try:
            lecturas[anio] = probar(anio)
        except Exception as e:
            _assert(False, f"México {anio}: {type(e).__name__}: {e}")

    # Chequeo cruzado entre años. Las clasificaciones NO son idénticas: la MIP
    # 2008 usa SCIAN 2007, que trae el comercio en un solo sector ('43-46')
    # donde 2013 y 2018 lo parten en '43' y '46'. Así que se exige solapamiento
    # alto, no igualdad: si un año se leyera corrido, el solapamiento se
    # desplomaría, que es lo que este chequeo busca detectar.
    print("\n--- coherencia entre años ---")
    if len(lecturas) == 3:
        conjuntos = {a: set(d["Z"].columns) for a, d in lecturas.items()}
        _assert(conjuntos[2013] == conjuntos[2018],
                "2013 y 2018 comparten la clasificación (SCIAN 2013)")
        comun = len(conjuntos[2008] & conjuntos[2013]) / len(conjuntos[2013])
        _assert(comun > 0.85,
                f"2008 (SCIAN 2007) solapa {comun:.0%} con 2013 a nivel sector")
        vbp = {a: float(d["x"].sum()) for a, d in lecturas.items()}
        _assert(vbp[2008] < vbp[2013] < vbp[2018],
                f"el VBP nominal crece entre ediciones: {vbp[2008]:,.0f} < "
                f"{vbp[2013]:,.0f} < {vbp[2018]:,.0f}")

    print()
    if FALLOS:
        print(f"FALLARON {len(FALLOS)} verificaciones:")
        for m in FALLOS:
            print("  -", m)
        sys.exit(1)
    print("Todo OK.")


if __name__ == "__main__":
    main()
