"""
CLI para simular choques sobre una MIP publicada.

Ejemplos
--------
Choque de demanda: +10% a la demanda final de Construccion y +5% a Mineria,
sobre la MIP de Mexico 2018, exportando reporte trazable:

    py -3 -X utf8 scripts/simular_choques.py ^
        --mip "MIP/Mexico/MIP_Mexico_2018.xlsx" ^
        --pais Mexico --anio 2018 ^
        --tipo demanda --modo pct ^
        --choque "Construccion=10" --choque "Mineria=5" ^
        --salida output/simulaciones/demanda_mexico_2018.xlsx

Choque de oferta (Ghosh) absoluto:

    py -3 -X utf8 scripts/simular_choques.py ^
        --mip "MIP/Brasil/MIP_Brasil_2018.xlsx" ^
        --pais Brasil --anio 2018 --tipo oferta --modo abs ^
        --choque "Petroleo=-1000"

Los sectores se pueden indicar por etiqueta exacta o por coincidencia
parcial (case-insensitive); si la coincidencia es ambigua, el script lo
reporta y se detiene.
"""

import argparse
import os
import sys

# Permitir importar src/ cuando se ejecuta desde la raiz del proyecto.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import simulador  # noqa: E402


def _parse_choques(items):
    choques = {}
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"Choque mal formado (falta '='): {it}")
        sector, val = it.rsplit("=", 1)
        try:
            choques[sector.strip()] = float(val)
        except ValueError:
            raise SystemExit(f"Magnitud no numerica en: {it}")
    if not choques:
        raise SystemExit("Debe especificar al menos un --choque sector=valor")
    return choques


def main():
    ap = argparse.ArgumentParser(description="Simulador de choques MIP")
    ap.add_argument("--mip", required=True, help="ruta al Excel de la MIP publicada")
    ap.add_argument("--pais", default="", help="metadato pais")
    ap.add_argument("--anio", default="", help="metadato anio")
    ap.add_argument("--tipo", choices=["demanda", "oferta"], default="demanda")
    ap.add_argument("--modo", choices=["pct", "abs"], default="pct")
    ap.add_argument("--choque", action="append", metavar="SECTOR=VALOR",
                    help="puede repetirse; SECTOR exacto o parcial, VALOR numerico")
    ap.add_argument("--salida", default="", help="ruta .xlsx del reporte (opcional)")
    ap.add_argument("--top", type=int, default=15, help="filas en el ranking de consola")
    args = ap.parse_args()

    if not os.path.exists(args.mip):
        raise SystemExit(f"No existe la MIP: {args.mip}")

    choques = _parse_choques(args.choque)
    mip = simulador.cargar_mip(args.mip, pais=args.pais, anio=args.anio)

    if args.tipo == "demanda":
        res = simulador.choque_demanda(mip, choques, modo=args.modo)
    else:
        res = simulador.choque_oferta(mip, choques, modo=args.modo)

    print(res.resumen())
    print()
    print(f"Top {args.top} sectores mas afectados:")
    with __import__("pandas").option_context("display.width", 160,
                                             "display.max_colwidth", 55):
        print(res.ranking(args.top).to_string())

    if args.salida:
        os.makedirs(os.path.dirname(os.path.abspath(args.salida)), exist_ok=True)
        simulador.exportar_resultado(res, args.salida)
        print(f"\nReporte trazable escrito en: {args.salida}")


if __name__ == "__main__":
    main()
