"""
Genera el LIBRO completo (industria×industria, Modelo D) para Colombia (DANE).

Sin ningún prorrateo: la MUPNI de DANE mide el corte doméstico/importado celda a
celda y ya viene a precios básicos, así que no se aplica ni el supuesto del
Cap. 7 (impuestos y márgenes) ni el del Cap. 8 (origen).

Uso:  py -3 scripts/colombia_libros.py
Genera: matrices/Colombia/MIP_Colombia_AAAA_LIBRO.xlsx  y  reports/colombia_todos.md
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

from src.parsers.colombia import parse
from src.valoracion import ensamblar_directo, NOTA_DIRECTO
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_libro import build_libro

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/colombia")
ANIOS = range(2014, 2021)          # cobertura de la MUPNI


def main():
    filas = ["# Colombia — MIP reconstruidas desde COU DANE (UN Handbook F74 Rev.1)\n",
             "Industria × industria, Modelo D, precios básicos, miles de millones de pesos "
             "corrientes, base 2015.\n",
             "**Sin prorrateo.** La MUPNI (matriz de utilización de productos nacionales e "
             "importados) mide el origen celda a celda y ya viene a precios básicos: no se "
             "aplica ningún supuesto de reparto. Nivel: divisiones CPC × 61 agrupaciones CIIU.\n",
             "| Año | Dim | VBP | VAB | Interm. doméstico | Interm. importado | fila=columna | L·f=x | min Z | mult. medio |",
             "|----:|----:|----:|----:|----:|----:|:---:|:---:|:---:|:---:|"]
    for anio in ANIOS:
        try:
            d = parse(RAW, anio)
            sut, rep = ensamblar_directo(d)
            sutb, _ = balancear(sut)
            iot = transformar(sutb, "D")
            an = calcular(iot)
            rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
            lfx = an.check_Lf_x / max(sut.g.sum(), 1)
            build_libro(iot, an, ROOT / "matrices" / "Colombia" / f"MIP_Colombia_{anio}_LIBRO.xlsx",
                        pais="Colombia", anio=anio, codes=d["ind_code"], names=d["ind_name"],
                        fuente=(f"DANE — Cuentas nacionales anuales base 2015, COU {anio} y "
                                f"MUPNI (utilización de productos nacionales e importados), "
                                f"sin prorrateo"),
                        cou_intermedio=d["U_pc"].sum(axis=0), nota_metodo=NOTA_DIRECTO,
                        sut=sutb, cou_orig=d, prod_codes=d["prod_code"], prod_names=d["prod_name"],
                        escala=1.0, unidad="miles de millones de pesos corrientes")
            ok = "✅" if (rel < 1e-6 and lfx < 1e-6 and iot.min_valor() >= -1e-9) else "⚠️"
            filas.append(f"| {anio} | {iot.Z.shape[0]}×{iot.Z.shape[0]} | {sut.g.sum():,.0f} | "
                         f"{rep['va_total']:,.0f} | {d['U_dom'].to_numpy().sum():,.0f} | "
                         f"{rep['importado_total']:,.0f} | {rel:.1e} | {lfx:.1e} | "
                         f"{iot.min_valor():.2f} | {an.mult_produccion.mean():.4f} {ok} |")
            print(f"[OK] Colombia {anio}: {iot.Z.shape[0]}×{iot.Z.shape[0]} "
                  f"fila=col {rel:.1e} mult {an.mult_produccion.mean():.4f}")
        except Exception as e:
            print(f"[ERROR] Colombia {anio}: {type(e).__name__}: {e}")
            filas.append(f"| {anio} | — | — | — | — | — | — | — | — | ❌ {type(e).__name__} |")

    rep_f = ROOT / "reports" / "colombia_todos.md"
    rep_f.write_text("\n".join(filas) + "\n", encoding="utf-8")
    print(f"[OK] Reporte en {rep_f.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
