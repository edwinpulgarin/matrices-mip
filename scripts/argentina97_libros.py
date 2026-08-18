"""
Genera el LIBRO de Argentina 1997 desde la publicación de la MIPAr97 del INDEC.

Es el único año de Argentina que se puede construir **sin ningún prorrateo**: el
INDEC publica el COU completo, con la matriz de importaciones celda a celda
(cuadro 4) y la utilización nacional ya a precios básicos (cuadro 3). Los otros
años (2004, 2018-2023) sólo traen esas piezas por producto y dependen del
reparto proporcional del Handbook §8.33.

Además, el INDEC publica su propia matriz simétrica (cuadro 12), así que este
año sirve de prueba de cierre del motor. El contraste se escribe en el reporte.

Uso:  py -3 scripts/argentina97_libros.py
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

from src.parsers.argentina97 import parse, simetrica_oficial
from src.valoracion import ensamblar_directo, NOTA_DIRECTO
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_libro import build_libro, avisar_libros_abiertos

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/argentina_mip97")
ANIO = 1997


def main():
    avisar_libros_abiertos(ROOT / "matrices")
    d = parse(RAW, ANIO)
    sut, rep = ensamblar_directo(d)
    sutb, _ = balancear(sut)
    iot = transformar(sutb, "D", no_mercado=d["no_mercado"])
    an = calcular(iot)

    rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
    lfx = an.check_Lf_x / max(sut.g.sum(), 1)
    build_libro(iot, an, ROOT / "matrices" / "Argentina" / f"MIP_Argentina_{ANIO}_LIBRO.xlsx",
                pais="Argentina", anio=ANIO,
                codes=d["ind_code"], names=d["ind_name"],
                fuente=("INDEC — Matriz Insumo-Producto Argentina 1997, cuadros 1 a 4 "
                        "(oferta, utilización a precios de comprador y básicos, "
                        "importaciones CIF), sin prorrateo"),
                cou_intermedio=d["U_pc"].sum(axis=0), nota_metodo=NOTA_DIRECTO,
                sut=sutb, sut_prev=sut, cou_orig=d,
                prod_codes=d["prod_code"], prod_names=d["prod_name"],
                escala=1000.0, unidad="millones de pesos corrientes de 1997",
                clasif_prod="productos MIPAr97", clasif_ind="ramas de actividad MIPAr97")
    print(f"[OK] Argentina {ANIO}: {iot.Z.shape[0]}×{iot.Z.shape[0]} "
          f"fila=col {rel:.1e} mult {an.mult_produccion.mean():.4f}")

    # ── contraste contra la simétrica oficial (cuadro 12) ──────────────────
    # El cuadro 12 del INDEC es la matriz NACIONAL: su suma, 167.856.141, es
    # exactamente la del cuadro 3 (utilización a precios básicos de producción
    # nacional). Es el mismo objeto que publicamos —la MIP doméstica—, así que se
    # compara directo contra `iot.Z`. (La convención cambia de país a país: el
    # Cuadro 7 del DANE es la total, que este paquete no publica.)
    Zo = simetrica_oficial(RAW)
    A = iot.Z.reindex(index=Zo.index, columns=Zo.columns).to_numpy()
    B = Zo.to_numpy()
    corr = float(np.corrcoef(A.ravel(), B.ravel())[0, 1])
    desvio = 100 * np.abs(A - B).sum() / np.abs(B).sum()

    md = [f"# Argentina {ANIO} — reconstruida desde la MIPAr97 del INDEC\n",
          "El INDEC publica el COU completo de 1997, con la matriz de importaciones "
          "celda a celda y la utilización nacional ya a precios básicos. Es el único "
          "año de Argentina que se construye **sin ningún prorrateo**.\n",
          f"- Dimensión: **{iot.Z.shape[0]} ramas × {len(d['prod_code'])} productos**",
          f"- VBP: {sut.g.sum():,.0f} miles de pesos",
          f"- Consumo intermedio doméstico: {sut.U.to_numpy().sum():,.0f}",
          f"- Insumo importado: {rep['importado_total']:,.0f}",
          f"- Impuestos y márgenes: {rep['impuestos_total']:,.0f}",
          f"- Valor agregado: {rep['va_total']:,.0f}",
          f"- Balance fila = columna: {rel:.1e} · L·f = x: {lfx:.1e}\n",
          "## Contraste contra la matriz simétrica oficial (cuadro 12)\n",
          "La metodología del INDEC (sección 12) dice que su simétrica «resulta de "
          "multiplicar la traspuesta de la matriz de oferta a precios básicos "
          "transformada en estructura expresada en tanto por uno —matriz de cuota de "
          "mercado— por la matriz 3 de utilización a precios básicos». Es el Modelo D "
          "del Handbook, el mismo que aplica este motor.\n",
          "| | Nuestra | Oficial | Diferencia |",
          "|:--|--:|--:|--:|",
          f"| Suma de Z | {A.sum():,.0f} | {B.sum():,.0f} | {100 * (A.sum() / B.sum() - 1):+.4f} % |",
          f"| Máx. diferencia por columna | | | {np.abs(A.sum(0) - B.sum(0)).max():.2e} |",
          f"| Correlación celda a celda | | | {corr:.4f} |",
          f"| Desvío absoluto total | | | {desvio:.2f} % |",
          "",
          "**La suma y las columnas cierran exacto.** En el Modelo D las columnas de Z "
          "son invariantes al modelo, así que eso prueba que la lectura del COU, la "
          "valoración y el corte por origen reproducen los del INDEC.\n",
          "El residuo está en las filas. Una parte se explica y está implementada: las "
          "cuatro actividades de **no mercado** —enseñanza y salud públicas, servicios "
          "sociales y servicio doméstico— tienen fila cero en la matriz oficial, porque "
          "el SCN no les atribuye ventas intermedias. El resto son ajustes propios del "
          "INDEC que su metodología no documenta; la propia publicación advierte que "
          "dejó «expuestos» valores de comercio mayorista y transporte de carga por "
          "comisionistas y transporte contratado, y que la simétrica «no se aconseja "
          "para el estudio de las estructuras de costos».\n",
          "No se implementaron ajustes por actividad para forzar la coincidencia: eso "
          "sería calzar con la respuesta y dejaría al motor sin capacidad de aplicarse "
          "a años sin MIP oficial.\n"]
    rep_path = ROOT / "reports" / "argentina_1997.md"
    rep_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] contraste vs cuadro 12: corr {corr:.4f}, desvío {desvio:.2f} %")
    print(f"[OK] Reporte en {rep_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
