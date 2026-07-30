"""
Genera el LIBRO completo (12 pestañas, industria×industria, Modelo D) para todos
los años de Argentina, con hoja de Auditoría COU columna-a-columna.

Uso:  py -3 scripts/argentina_libros.py
Genera: matrices/Argentina/MIP_Argentina_AAAA_LIBRO.xlsx
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

from src.parsers.argentina import parse
from src.valoracion import valorar_argentina, NOTA_PRORRATEO
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_libro import build_libro

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/argentina")
ANIOS = {2004: "cou_2004.xls", 2018: "cou_2018.xls", 2019: "cou_2019.xls",
         2020: "cou_2020.xls", 2021: "cou_2021.xls", 2022: "cou_2022.xls",
         2023: "cou_2023.xls"}


def main():
    for anio, fn in ANIOS.items():
        d = parse(RAW / fn, anio)
        sut, _ = valorar_argentina(d)
        sutb, _ = balancear(sut)
        iot = transformar(sutb, "D")
        an = calcular(iot)
        # El libro siempre se presenta en millones. INDEC publica 2004–2022 en
        # miles de pesos y 2023 en millones, así que la escala sale de la unidad
        # que el parser leyó del archivo, no de una constante.
        escala = 1.0 if "millones" in sut.unidad else 1000.0
        ruta = build_libro(
            iot, an, ROOT / "matrices" / "Argentina" / f"MIP_Argentina_{anio}_LIBRO.xlsx",
            pais="Argentina", anio=anio,
            codes=d["ind_code"], names=d["ind_name"],
            fuente=f"INDEC — COU {anio}",
            cou_intermedio=d["U_pc"].sum(axis=0), nota_metodo=NOTA_PRORRATEO,
            sut=sutb, cou_orig=d, prod_codes=d["prod_code"], prod_names=d["prod_name"],
            escala=escala, unidad="millones de pesos corrientes",
        )
        rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
        print(f"[OK] {anio}: {iot.Z.shape[0]}×{iot.Z.shape[0]} · fila=col {rel:.1e} · {ruta.name}")


if __name__ == "__main__":
    main()
