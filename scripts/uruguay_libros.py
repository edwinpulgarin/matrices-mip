"""
Genera el LIBRO (industria×industria, Modelo D) para Uruguay (BCU).
Uso:  py -3 scripts/uruguay_libros.py
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

from src.parsers.uruguay import parse
from src.valoracion import (valorar_argentina as valorar, NOTA_PRORRATEO,
                            NOTA_ORIGEN_MEDIDO)
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_libro import build_libro, avisar_libros_abiertos

NI = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/Nueva_Info")
RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/uruguay")
# El tercer elemento es la carpeta con la utilización intermedia abierta en
# nacional e importada. El BCU la publica sólo para 2017; en 2012 y 2016 el
# origen se sigue prorrateando por fila porque no hay con qué medirlo.
FUENTES = {
    2012: (NI / "Uruguay_2012_Detallada_COU_C.xlsx", "COU_C", None),
    2016: (NI / "Uruguay_2016-2017 Detallada_COU_C.xlsx", "2016 CORRIENTE", None),
    2017: (NI / "Uruguay_2016-2017 Detallada_COU_C.xlsx", "2017 CORRIENTE", RAW / "cou_2017"),
}


def main():
    avisar_libros_abiertos(ROOT / "matrices")
    filas = ["# Uruguay — MIP reconstruidas desde COU BCU (UN Handbook F74 Rev.1)\n",
             "Industria × industria, Modelo D, precios básicos, millones de pesos uruguayos corrientes.\n",
             "**2017 sale con el origen medido**: el BCU publica la utilización intermedia "
             "nacional e importada celda a celda, así que ahí no se aplica el supuesto de "
             "proporcionalidad de las importaciones (§8.33). En 2012 y 2016 sólo hay "
             "utilización total, así que el origen se prorratea.\n",
             "| Año | Origen | Dim | VBP | VAB | Interm. importado | fila=columna | L·f=x | min Z | mult. medio |",
             "|----:|:-------|----:|----:|----:|----:|:---:|:---:|:---:|:---:|"]
    for anio, (f, hoja, detalle) in FUENTES.items():
        try:
            d = parse(f, anio, hoja=hoja, carpeta_detalle=detalle)
            sut, rep = valorar(d)
            medido = rep["origen_medido"]
            sutb, _ = balancear(sut)
            iot = transformar(sutb, "D")
            an = calcular(iot)
            rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
            lfx = an.check_Lf_x / max(sut.g.sum(), 1)
            build_libro(iot, an, ROOT / "matrices" / "Uruguay" / f"MIP_Uruguay_{anio}_LIBRO.xlsx",
                        pais="Uruguay", anio=anio, codes=d["ind_code"], names=d["ind_name"],
                        fuente=(f"BCU — COU {anio}" + (", con la utilización intermedia "
                                "nacional/importada publicada por separado" if medido else "")),
                        cou_intermedio=d["U_pc"].sum(axis=0),
                        nota_metodo=NOTA_ORIGEN_MEDIDO if medido else NOTA_PRORRATEO,
                        sut=sutb, sut_prev=sut,
                        cou_orig=d, prod_codes=d["prod_code"], prod_names=d["prod_name"],
                        escala=1.0, unidad="millones de pesos uruguayos corrientes",
                        clasif_prod="productos, CPC", clasif_ind="industrias, CIIU")
            ok = "✅" if (rel < 1e-6 and lfx < 1e-6 and iot.min_valor() >= -1e-9) else "⚠️"
            filas.append(f"| {anio} | {'**medido**' if medido else 'prorrateo'} | "
                         f"{iot.Z.shape[0]}×{iot.Z.shape[0]} | {sut.g.sum():,.0f} | "
                         f"{d['VA'].values.sum():,.0f} | {rep['importado_total']:,.0f} | "
                         f"{rel:.1e} | {lfx:.1e} | {iot.min_valor():.2f} | "
                         f"{an.mult_produccion.mean():.4f} {ok} |")
            print(f"[OK] Uruguay {anio}: {iot.Z.shape[0]}×{iot.Z.shape[0]} fila=col {rel:.1e}"
                  f" origen={'medido' if medido else 'prorrateo'}")
        except Exception as e:
            print(f"[ERROR] Uruguay {anio}: {type(e).__name__}: {e}")
            filas.append(f"| {anio} | ERROR | {type(e).__name__} | | | | | | | |")
    (ROOT / "reports" / "uruguay_todos.md").write_text("\n".join(filas), encoding="utf-8")
    print("[OK] Reporte en reports/uruguay_todos.md")


if __name__ == "__main__":
    main()
