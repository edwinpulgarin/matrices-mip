"""
Genera el LIBRO completo (industria×industria, Modelo D) para México (INEGI).

Publica la versión SIN PRORRATEO — INEGI mide la utilización a precios básicos y
con corte doméstico/importado, así que no hace falta ningún supuesto de reparto —
y calcula además la versión por proporcionalidad como CONTROL DE COMPARABILIDAD,
porque Argentina, Uruguay y la mayoría de los años de Brasil sí dependen de ella.

Uso:  py -3 scripts/mexico_libros.py
Genera: matrices/Mexico/MIP_Mexico_AAAA_LIBRO.xlsx  y  reports/mexico_todos.md
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

from src.parsers.mexico import parse, parse_sin_prorrateo
from src.valoracion import (ensamblar_directo, valorar_argentina as valorar_prorrateo,
                            NOTA_DIRECTO)
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_libro import build_libro

STG = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/_cepal_staging")
# nivel rama SCIAN = 262 ramas, el máximo detalle publicado por INEGI
FUENTES = {2013: (STG / "MEX_COU_2013", "RAMA")}


def _mip(sut):
    sutb, rb = balancear(sut)
    iot = transformar(sutb, "D")
    return sutb, iot, calcular(iot), rb


def main():
    filas = ["# México — MIP reconstruidas desde COU INEGI (UN Handbook F74 Rev.1)\n",
             "Industria × industria, Modelo D, precios básicos, millones de pesos corrientes.\n",
             "**Se publica la versión sin prorrateo.** INEGI mide la utilización a precios "
             "básicos y con corte doméstico/importado, así que no se aplica ningún supuesto "
             "de reparto: ni el de impuestos y márgenes (Cap. 7) ni el de origen (Cap. 8).\n",
             "| Año | Nivel | Dim | VBP | VAB | fila=columna | L·f=x | min Z | mult. medio |",
             "|----:|:------|----:|----:|----:|:---:|:---:|:---:|:---:|"]
    control = ["\n## Control de comparabilidad\n",
               "La misma MIP recalculada con el prorrateo proporcional que sí necesitan "
               "Argentina, Uruguay y 10 de los 12 años de Brasil. La diferencia es el sesgo "
               "que esos países cargan sin poder medirlo.\n",
               "| Año | Consumo interm. doméstico | Σᵢaᵢⱼ medio | Multiplicador medio |",
               "|----:|----:|----:|----:|"]

    for anio, (carpeta, nivel) in FUENTES.items():
        try:
            d = parse_sin_prorrateo(carpeta, anio, nivel=nivel)
            sut, _ = ensamblar_directo(d)
            sutb, iot, an, _ = _mip(sut)
            rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
            lfx = an.check_Lf_x / max(sut.g.sum(), 1)
            build_libro(iot, an, ROOT / "matrices" / "Mexico" / f"MIP_Mexico_{anio}_LIBRO.xlsx",
                        pais="México", anio=anio, codes=d["ind_code"], names=d["ind_name"],
                        fuente=(f"INEGI — SCNM, COU {anio} (nivel {nivel.lower()} SCIAN), "
                                f"utilización doméstica a precios básicos medida, sin prorrateo"),
                        cou_intermedio=d["U_pc"].sum(axis=0), nota_metodo=NOTA_DIRECTO,
                        sut=sutb, cou_orig=d, prod_codes=d["prod_code"], prod_names=d["prod_name"],
                        escala=1.0, unidad="millones de pesos corrientes")
            ok = "✅" if (rel < 1e-6 and lfx < 1e-6 and iot.min_valor() >= -1e-9) else "⚠️"
            filas.append(f"| {anio} | {nivel.lower()} | {iot.Z.shape[0]}×{iot.Z.shape[0]} | "
                         f"{sut.g.sum():,.0f} | {sut.VA.loc['valor_agregado_bruto'].sum():,.0f} | "
                         f"{rel:.1e} | {lfx:.1e} | {iot.min_valor():.2f} | "
                         f"{an.mult_produccion.mean():.4f} {ok} |")
            print(f"[OK] México {anio} sin prorrateo: {iot.Z.shape[0]}×{iot.Z.shape[0]} "
                  f"fila=col {rel:.1e} mult {an.mult_produccion.mean():.4f}")

            # control: misma fuente, reparto proporcional
            dp = parse(carpeta, anio, nivel=nivel)
            sp, _ = valorar_prorrateo(dp)
            _, iotp, anp, _ = _mip(sp)
            for etq, s, a in (("sin prorrateo (publicado)", sut, an),
                              ("proporcionalidad (control)", sp, anp)):
                control.append(f"| {anio} · {etq} | {s.U.to_numpy().sum():,.0f} | "
                               f"{a.A.sum(axis=0).mean():.4f} | {a.mult_produccion.mean():.4f} |")
            sesgo = 100 * (anp.mult_produccion.mean() / an.mult_produccion.mean() - 1)
            control.append(f"\n**Sesgo del prorrateo: +{sesgo:.2f} %** en el multiplicador medio "
                           f"({anp.mult_produccion.mean():.4f} vs {an.mult_produccion.mean():.4f}).\n")
            print(f"[OK] control por proporcionalidad: mult {anp.mult_produccion.mean():.4f} "
                  f"(+{sesgo:.2f} %)")
        except Exception as e:
            print(f"[ERROR] México {anio}: {type(e).__name__}: {e}")
            filas.append(f"| {anio} | {nivel.lower()} | — | — | — | — | — | — | ❌ {type(e).__name__} |")

    rep = ROOT / "reports" / "mexico_todos.md"
    rep.write_text("\n".join(filas + control) + "\n", encoding="utf-8")
    print(f"[OK] Reporte en {rep.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
