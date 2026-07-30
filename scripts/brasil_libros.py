"""
Genera el LIBRO completo (industria×industria, Modelo D) para todos los años
disponibles de Brasil (IBGE nível 68), con hoja de Auditoría COU.

Uso:  py -3 scripts/brasil_libros.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from src.parsers.brasil import parse
from src.parsers.brasil_mip import parse as parse_mip
from src.valoracion import (valorar_argentina as valorar, ensamblar_directo,
                            NOTA_DIRECTO, NOTA_PRORRATEO)
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_libro import build_libro

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/brasil")
# años con Matriz de Insumo-Produto publicada: son los únicos donde el IBGE mide
# el consumo intermedio nacional/importado y el destino de impuestos y márgenes
MIP_ANIOS = {2010, 2015}


def anios_disponibles():
    t1 = {int(m.group(1)) for f in RAW.glob("68_tab1_*.xls")
          if (m := re.search(r"(\d{4})", f.name))}
    t2 = {int(m.group(1)) for f in RAW.glob("68_tab2_*.xls")
          if (m := re.search(r"(\d{4})", f.name))}
    return sorted(t1 & t2)


def _pipeline(sut):
    sutb, _ = balancear(sut)
    iot = transformar(sutb, "D")
    return sutb, iot, calcular(iot)


def main():
    filas = ["# Brasil — MIP reconstruidas desde el IBGE (UN Handbook F74 Rev.1)\n",
             "Industria × industria, Modelo D, precios básicos, millones de reales corrientes.\n",
             "**2010 y 2015 salen sin prorrateo**: la publicación de la Matriz de Insumo-Produto "
             "del IBGE mide el consumo intermedio nacional e importado y el destino de cada "
             "impuesto y margen celda a celda (Tabelas 03-10). Es nivel 67, no 68. El resto de "
             "los años sólo tiene el COU, que publica importaciones, impuestos y márgenes por "
             "producto, así que dependen del prorrateo del Handbook §7.77.\n",
             "| Año | Origen | Dim | VBP | VAB | fila=columna | L·f=x | min Z | mult. medio |",
             "|----:|:-------|----:|----:|----:|:---:|:---:|:---:|:---:|"]
    comparacion = []

    for anio in anios_disponibles():
        try:
            limpio = anio in MIP_ANIOS
            if limpio:
                d = parse_mip(RAW, anio)
                sut, rep = ensamblar_directo(d)
                vab = rep["va_total"]
                fuente = (f"IBGE — Matriz de Insumo-Produto {anio}, nível 67 "
                          f"(Tabelas 03-10, nacional/importado medido), sin prorrateo")
                origen = "MIP n67 · **sin prorrateo**"
                nota = NOTA_DIRECTO
            else:
                d = parse(RAW, anio)
                sut, _ = valorar(d)
                vab = d["VA"].values.sum()
                fuente = f"IBGE — COU nível 68, {anio} (prorrateo proporcional, Handbook §7.77)"
                origen = "COU n68 · prorrateo"
                nota = NOTA_PRORRATEO
            sutb, iot, an = _pipeline(sut)
            rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
            lfx = an.check_Lf_x / max(sut.g.sum(), 1)
            build_libro(iot, an, ROOT / "matrices" / "Brasil" / f"MIP_Brasil_{anio}_LIBRO.xlsx",
                        pais="Brasil", anio=anio, codes=d["ind_code"], names=d["ind_name"],
                        fuente=fuente, cou_intermedio=d["U_pc"].sum(axis=0), nota_metodo=nota,
                        sut=sutb, prod_codes=d["prod_code"], prod_names=d["prod_name"],
                        escala=1.0, unidad="millones de reales corrientes")
            ok = "✅" if (rel < 1e-6 and lfx < 1e-6 and iot.min_valor() >= -1e-9) else "⚠️"
            filas.append(f"| {anio} | {origen} | {iot.Z.shape[0]}×{iot.Z.shape[0]} | "
                         f"{sut.g.sum():,.0f} | {vab:,.0f} | {rel:.1e} | {lfx:.1e} | "
                         f"{iot.min_valor():.2f} | {an.mult_produccion.mean():.4f} {ok} |")
            print(f"[OK] Brasil {anio} ({'sin prorrateo' if limpio else 'prorrateo'}): "
                  f"{iot.Z.shape[0]}×{iot.Z.shape[0]} fila=col {rel:.1e} "
                  f"mult {an.mult_produccion.mean():.4f}")

            if limpio:   # control: el mismo año por el camino con prorrateo
                dp = parse(RAW, anio)
                sp, _ = valorar(dp)
                _, _, anp = _pipeline(sp)
                sesgo = 100 * (anp.mult_produccion.mean() / an.mult_produccion.mean() - 1)
                comparacion.append(
                    f"| {anio} | {an.mult_produccion.mean():.4f} (n67) | "
                    f"{anp.mult_produccion.mean():.4f} (n68) | **{sesgo:+.2f} %** |")
                print(f"     control por prorrateo: {anp.mult_produccion.mean():.4f} ({sesgo:+.2f} %)")
        except Exception as e:
            print(f"[ERROR] Brasil {anio}: {type(e).__name__}: {e}")
            filas.append(f"| {anio} | ERROR | {type(e).__name__} | | | | | | |")

    if comparacion:
        filas += ["\n## Control: cuánto cambia el multiplicador por prorratear\n",
                  "Los dos años donde existe el dato medido permiten cuantificar el sesgo que "
                  "cargan los otros diez. Ojo: el nivel de agregación también difiere (67 vs 68), "
                  "así que parte de la diferencia es de agregación y no sólo de método.\n",
                  "| Año | Sin prorrateo | Con prorrateo | Diferencia |",
                  "|----:|----:|----:|----:|"] + comparacion
    (ROOT / "reports" / "brasil_todos.md").write_text("\n".join(filas) + "\n", encoding="utf-8")
    print("[OK] Reporte en reports/brasil_todos.md")


if __name__ == "__main__":
    main()
