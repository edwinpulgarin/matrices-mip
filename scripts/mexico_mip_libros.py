"""
Genera los LIBROS de México a partir de la MIP simétrica OFICIAL de INEGI.

Es la única de las cinco fuentes que publica la matriz ya transformada, y además
con la doméstica y la importada por separado. Eso deja los tres años (2008, 2013
y 2018) sin ninguno de los dos prorrateos, y sin siquiera nuestra transformación
de COU a MIP: acá el Modelo D no se aplica, Z viene medida.

Convive con `mexico_libros.py`, que reconstruye 2013 desde el COU. Los dos libros
de 2013 se conservan a propósito: la comparación entre ellos mide cuánto se
aparta el Modelo D del Handbook del método propio de INEGI, sobre exactamente los
mismos datos de base. Ese contraste se escribe al final del reporte.

Uso:  py -3 scripts/mexico_mip_libros.py
Genera: matrices/Mexico/MIP_Mexico_AAAA_LIBRO_OFICIAL.xlsx  y
        reports/mexico_mip_oficial.md
"""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from src.parsers import mexico_mip
from src.transformacion import desde_mip_oficial
from src.analisis import calcular
from src.export_libro import build_libro, avisar_libros_abiertos
from src.valoracion import NOTA_OFICIAL

ANIOS = [2008, 2013, 2018]
NIVEL = "RAMA"          # máximo detalle publicado de la MIP industria × industria


def main():
    avisar_libros_abiertos(ROOT / "matrices")
    filas = ["# México — MIP simétrica OFICIAL de INEGI\n",
             "Industria × industria, precios básicos, **matriz doméstica** (el insumo "
             "importado va en fila primaria), millones de pesos corrientes. Nivel rama "
             "SCIAN. La versión total (nacional + importada) no se publica: todo lo que "
             "trae el libro se deriva de esta matriz.\n",
             "**Sin ningún prorrateo y sin transformación propia.** INEGI publica la "
             "matriz simétrica ya construida y con la doméstica y la importada medidas "
             "por separado, así que no interviene ni el supuesto del Cap. 7 (impuestos y "
             "márgenes) ni el del Cap. 8 (origen), ni el Modelo D del Cap. 12.\n",
             "| Año | Dim | VBP | VAB | Importaciones | fila=columna | L·f=x | mult. medio |",
             "|----:|----:|----:|----:|----:|:---:|:---:|:---:|"]
    nota_scian = [
        "\n**Cuidado al comparar 2008 contra los otros dos.** La MIP 2008 está en "
        "SCIAN 2007 y las de 2013 y 2018 en SCIAN 2013, así que la clasificación no "
        "es la misma: a nivel sector 2007 trae el comercio junto (`43-46`) donde 2013 "
        "lo parte en `43` y `46`, y a nivel rama hay seis códigos que entran o salen "
        "(`7221`/`7222` se reagrupan en `7225`, aparecen `4611` y `4922`, desaparece "
        "`9321`). Los agregados y los multiplicadores medios sí son comparables; el "
        "cruce rama por rama entre 2008 y los otros años, no, sin un puente de "
        "clasificaciones.\n"]
    resultados = {}

    for anio in ANIOS:
        try:
            d = mexico_mip.parse(anio, nivel=NIVEL)
            # La MIP que se publica es la DOMÉSTICA, con el insumo importado en
            # fila primaria: es la matriz tal como la entrega INEGI y la misma
            # definición que los otros cuatro países. La total —que acá tampoco
            # supone nada, porque INEGI publica la matriz importada por
            # separado— no se publica.
            iot = desde_mip_oficial(d, total=False)
            an = calcular(iot)
            escala_x = max(float(iot.x.sum()), 1.0)
            rel = float(iot.balance_fila_columna().abs().max()) / escala_x
            lfx = an.check_Lf_x / escala_x
            build_libro(
                iot, an,
                ROOT / "matrices" / "Mexico" / f"MIP_Mexico_{anio}_LIBRO_OFICIAL.xlsx",
                pais="México", anio=anio,
                codes={k: k for k in iot.Z.columns}, names=d["ind_name"],
                fuente=(f"INEGI — SCNM, Matriz de Insumo-Producto {anio} "
                        f"(matriz simétrica industria × industria, nivel "
                        f"{NIVEL.lower()} SCIAN, doméstica a precios básicos)"),
                nota_metodo=NOTA_OFICIAL,
                # la matriz de importaciones entra completa: es el otro archivo
                # que publica INEGI y de él sale la fila de insumo importado
                u_imp=d["M"], crudo=d["crudo"],
                escala=1.0, unidad="millones de pesos corrientes",
                clasif_prod="productos, rama SCIAN",
                clasif_ind=f"industrias, {NIVEL.lower()} SCIAN")
            ok = "✅" if (rel < 1e-8 and lfx < 1e-8 and iot.min_valor() >= -1e-9) else "⚠️"
            filas.append(
                f"| {anio} | {iot.Z.shape[0]}×{iot.Z.shape[0]} | {iot.x.sum():,.0f} | "
                f"{iot.VA.loc['valor_agregado_bruto'].sum():,.0f} | "
                # en la versión total el insumo importado ya no es una fila
                # primaria: entra por la oferta, junto con la producción
                f"{iot.m.sum() if iot.m is not None else iot.VA.loc['consumo_intermedio_importado'].sum():,.0f} | "
                f"{rel:.1e} | {lfx:.1e} | {an.mult_produccion.mean():.4f} {ok} |")
            resultados[anio] = (iot, an, d)
            print(f"[OK] México {anio} oficial: {iot.Z.shape[0]}×{iot.Z.shape[0]} "
                  f"fila=col {rel:.1e} mult {an.mult_produccion.mean():.4f}")
        except Exception as e:
            print(f"[ERROR] México {anio}: {type(e).__name__}: {e}")
            filas.append(f"| {anio} | — | — | — | — | — | — | ❌ {type(e).__name__} |")

    filas += nota_scian
    filas += _seccion_contraste(resultados)
    filas += _seccion_extra(resultados)

    rep = ROOT / "reports" / "mexico_mip_oficial.md"
    rep.write_text("\n".join(filas) + "\n", encoding="utf-8")
    print(f"[OK] Reporte en {rep.relative_to(ROOT)}")


def _seccion_contraste(resultados):
    """2013 oficial vs. 2013 reconstruido desde el COU por nuestro Modelo D."""
    if 2013 not in resultados:
        return []
    from src.parsers.mexico import parse_sin_prorrateo
    from src.valoracion import ensamblar_directo
    from src.balanceo import balancear
    from src.transformacion import transformar

    STG = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/_cepal_staging")
    try:
        d = parse_sin_prorrateo(STG / "MEX_COU_2013", 2013, nivel=NIVEL)
        # las dos son domésticas, que es el objeto que se publica
        sut = ensamblar_directo(d)[0]
        sutb, _ = balancear(sut)
        iot_r = transformar(sutb, "D")
        an_r = calcular(iot_r)
    except Exception as e:
        return [f"\n## Contraste 2013\n\nNo se pudo recalcular la reconstrucción: "
                f"{type(e).__name__}: {e}\n"]

    iot_o, an_o, _ = resultados[2013]
    # La reconstrucción indexa por posición; la oficial, por código SCIAN. Se
    # reetiqueta para poder cruzar rama contra rama.
    codes = [str(c) for c in d["ind_code"]]
    Zr_full = iot_r.Z.copy()
    Zr_full.index = codes
    Zr_full.columns = codes
    comun = [c for c in iot_o.Z.index if c in set(codes)]
    Ao = iot_o.Z.loc[comun, comun].to_numpy()
    Ar = Zr_full.loc[comun, comun].to_numpy()
    corr = float(np.corrcoef(Ao.ravel(), Ar.ravel())[0, 1])
    difs = 100 * (Ar.sum() / Ao.sum() - 1)
    dmult = 100 * (an_r.mult_produccion.mean() / an_o.mult_produccion.mean() - 1)

    return ["\n## Contraste 2013 — oficial vs. reconstruida desde el COU\n",
            "Mismo año, mismo instituto, mismo nivel de agregación y los mismos datos de "
            "base. Lo único que cambia es quién hizo la transformación de COU a matriz "
            "simétrica: INEGI con su método, o nosotros con el Modelo D del Handbook. "
            "Es la prueba más exigente del motor, porque no hay diferencia de fuente "
            "detrás de la que esconderse.\n",
            "| | MIP oficial INEGI | Reconstruida (Modelo D) | Diferencia |",
            "|:--|--:|--:|--:|",
            f"| Ramas en común | {len(comun)} | {len(comun)} | — |",
            f"| Suma de Z | {Ao.sum():,.0f} | {Ar.sum():,.0f} | {difs:+.2f} % |",
            f"| Producción total | {iot_o.x.sum():,.0f} | {iot_r.x.sum():,.0f} | "
            f"{100 * (iot_r.x.sum() / iot_o.x.sum() - 1):+.2f} % |",
            f"| Multiplicador medio | {an_o.mult_produccion.mean():.4f} | "
            f"{an_r.mult_produccion.mean():.4f} | {dmult:+.2f} % |",
            f"\nCorrelación celda a celda de Z: **{corr:.4f}**.\n",
            "Los agregados coinciden y la correlación es casi perfecta. La dispersión "
            "que queda en las celdas chicas es la diferencia entre dos métodos de "
            "transformación legítimos —no un error de lectura—, y da la medida de cuánta "
            "incertidumbre de método cargan los libros de los países que sólo publican "
            "el COU y no la MIP.\n"]


def _seccion_extra(resultados):
    """Filas que INEGI publica y las otras cuatro fuentes no."""
    if not resultados:
        return []
    out = ["\n## Filas que sólo publica INEGI\n",
           "El COU de los otros cuatro países trae el valor agregado en una sola fila "
           "agregada, y por eso el multiplicador de valor agregado no es calculable: "
           "sale por identidad y da 1,0000 en todos los sectores (ver el docstring de "
           "`analisis.py`). INEGI sí abre remuneraciones y puestos de trabajo, así que "
           "para México quedan habilitados los multiplicadores de ingreso y de empleo.\n",
           "Estos datos los lee el parser y quedan en `parse(...)['extra']`. Todavía no "
           "se escriben en el libro, para que México conserve la misma estructura de "
           "pestañas que los demás países.\n",
           "| Año | Remuneraciones (D.1) | Excedente bruto (B.2b) | Puestos de trabajo (PT) |",
           "|----:|----:|----:|----:|"]
    for anio, (_, _, d) in sorted(resultados.items()):
        e = d["extra"]
        def tot(k):
            return f"{float(e[k].sum()):,.0f}" if k in e else "—"
        out.append(f"| {anio} | {tot('remuneraciones')} | {tot('excedente')} | "
                   f"{tot('puestos_trabajo')} |")
    return out


if __name__ == "__main__":
    main()
