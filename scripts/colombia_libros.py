"""
Genera el LIBRO completo (industria×industria, Modelo D) para Colombia (DANE).

**Todo sale del COU**, un solo archivo, el mismo camino que Argentina, Brasil,
Uruguay y México: oferta y utilización a precios de comprador, y el puente de
valoración por producto que publica el propio cuadro (impuestos, subvenciones,
márgenes de comercio y transporte, IVA). De ahí, valoración del Cap. 7.

La matriz publicada es DOMÉSTICA: Z lleva sólo el insumo de origen nacional y
el importado va en la fila primaria «consumo intermedio importado». La versión
total (nacional + importada) no se publica: todo lo que trae el libro se deriva
de la Z doméstica. `scripts/comparar_dom_total.py` mide cuánto cambiaría cada
indicador con la otra definición (Cuadro 7 del DANE).

Eso deja dos supuestos en pie: el reparto proporcional de impuestos y márgenes
dentro de cada fila (§7.76), porque el COU publica el puente por producto y no
por celda, y el de origen (§8.33), que es el caro —+5,65 % en los
multiplicadores de México— y que sólo la hoja total esquiva.

Medido contra la MUPNI, que sí mide precios básicos y origen celda a celda
(2019): la suma de Z difiere **+0,09 %**, la correlación celda a celda es
**0,9975** y el multiplicador medio **−0,26 %**. Contra el Cuadro 8 del DANE,
nuestro multiplicador medio queda a **−0,33 %**.

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

from src.parsers.colombia import parse_cou
from src.valoracion import valorar_argentina, NOTA_PRORRATEO
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_libro import build_libro, avisar_libros_abiertos

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/colombia")
# El COU publicado llega a 2024p. Antes la cobertura la limitaba la MUPNI
# (2014-2020); saliendo sólo del COU, esa restricción desaparece.
ANIOS = range(2014, 2025)


def main():
    avisar_libros_abiertos(ROOT / "matrices")
    filas = ["# Colombia — MIP reconstruidas desde el COU del DANE (UN Handbook F74 Rev.1)\n",
             "Industria × industria, Modelo D, **matriz doméstica** (importaciones en fila "
             "primaria), precios básicos, miles de millones de pesos corrientes, base 2015. "
             "La versión total (nacional + importada) no se publica: todo lo que trae "
             "el libro se deriva de esta matriz.\n",
             "**Todo sale del COU**: oferta, utilización a precios de comprador y el puente "
             "de valoración por producto. Dos supuestos: el reparto proporcional de "
             "impuestos y márgenes dentro de cada fila (§7.76) y el de origen (§8.33), "
             "que separa lo nacional de lo importado dentro de cada celda.\n",
             "**El balanceo no modifica ninguna celda, en ningún año.** Siete de los once "
             "cuadros entran cumpliendo las identidades y no hay nada que hacer; en los "
             "otros cuatro queda un residuo del propio cuadro publicado y se anota como "
             "«discrepancia estadística» en la demanda final, sin tocar la utilización. "
             "Ver `reports/estado_ras.md`.\n",
             "| Año | Dim | VBP | VAB | Interm. total | Insumo importado | fila=columna | L·f=x | min Z | mult. medio |",
             "|----:|----:|----:|----:|----:|----:|:---:|:---:|:---:|:---:|"]
    for anio in ANIOS:
        try:
            d = parse_cou(RAW, anio)
            sut, rep = valorar_argentina(d)
            sutb, rb = balancear(sut)
            iot = transformar(sutb, "D")
            an = calcular(iot)
            rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
            lfx = an.check_Lf_x / max(sut.g.sum(), 1)
            build_libro(iot, an, ROOT / "matrices" / "Colombia" / f"MIP_Colombia_{anio}_LIBRO.xlsx",
                        pais="Colombia", anio=anio, codes=d["ind_code"], names=d["ind_name"],
                        fuente=(f"DANE — Cuentas nacionales anuales base 2015, "
                                f"cuadro de oferta y utilización {anio}"),
                        cou_intermedio=d["U_pc"].sum(axis=0), nota_metodo=NOTA_PRORRATEO,
                        sut=sutb, sut_prev=sut,
                        cou_orig=d, prod_codes=d["prod_code"], prod_names=d["prod_name"],
                        escala=1.0, unidad="miles de millones de pesos corrientes",
                        clasif_prod="productos, divisiones CPC",
                        clasif_ind="industrias, divisiones CIIU")
            ok = "✅" if (rel < 1e-6 and lfx < 1e-6 and iot.min_valor() >= -1e-9) else "⚠️"
            filas.append(f"| {anio} | {iot.Z.shape[0]}×{iot.Z.shape[0]} | {sut.g.sum():,.0f} | "
                         f"{d['VA'].to_numpy().sum():,.0f} | {sutb.U.to_numpy().sum():,.0f} | "
                         f"{sutb.VA.loc['consumo_intermedio_importado'].sum():,.0f} | "
                         f"{rel:.1e} | {lfx:.1e} | "
                         f"{iot.min_valor():.2f} | {an.mult_produccion.mean():.4f} {ok} |")
            print(f"[OK] Colombia {anio}: {iot.Z.shape[0]}×{iot.Z.shape[0]} "
                  f"fila=col {rel:.1e} mult {an.mult_produccion.mean():.4f} "
                  f"RAS={'sí' if rb['aplicado'] else 'no'}")
        except Exception as e:
            print(f"[ERROR] Colombia {anio}: {type(e).__name__}: {e}")
            filas.append(f"| {anio} | — | — | — | — | — | — | — | — | ❌ {type(e).__name__} |")

    rep_f = ROOT / "reports" / "colombia_todos.md"
    rep_f.write_text("\n".join(filas) + "\n", encoding="utf-8")
    print(f"[OK] Reporte en {rep_f.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
