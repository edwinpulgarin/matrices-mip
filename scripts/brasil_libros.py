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
from src.valoracion import valorar_argentina as valorar
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_libro import build_libro

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/brasil")


def anios_disponibles():
    t1 = {int(m.group(1)) for f in RAW.glob("68_tab1_*.xls")
          if (m := re.search(r"(\d{4})", f.name))}
    t2 = {int(m.group(1)) for f in RAW.glob("68_tab2_*.xls")
          if (m := re.search(r"(\d{4})", f.name))}
    return sorted(t1 & t2)


def main():
    filas = ["# Brasil — MIP reconstruidas desde COU IBGE (UN Handbook F74 Rev.1)\n",
             "Industria × industria, Modelo D, precios básicos, millones de reales corrientes.\n",
             "| Año | Dim | VBP | VAB | fila=columna | L·f=x | min Z | mult. medio |",
             "|----:|----:|----:|----:|:---:|:---:|:---:|:---:|"]
    for anio in anios_disponibles():
        try:
            d = parse(RAW, anio)
            sut, _ = valorar(d)
            sutb, _ = balancear(sut)
            iot = transformar(sutb, "D")
            an = calcular(iot)
            rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
            lfx = an.check_Lf_x / max(sut.g.sum(), 1)
            build_libro(iot, an, ROOT / "output" / f"MIP_Brasil_{anio}_LIBRO.xlsx",
                        pais="Brasil", anio=anio, codes=d["ind_code"], names=d["ind_name"],
                        fuente=f"IBGE — COU nível 68, {anio}", cou_intermedio=d["U_pc"].sum(axis=0),
                        escala=1.0, unidad="millones de reales corrientes")
            ok = "✅" if (rel < 1e-6 and lfx < 1e-6 and iot.min_valor() >= -1e-9) else "⚠️"
            filas.append(f"| {anio} | {iot.Z.shape[0]}×{iot.Z.shape[0]} | {sut.g.sum():,.0f} | "
                         f"{d['VA'].values.sum():,.0f} | {rel:.1e} | {lfx:.1e} | {iot.min_valor():.2f} | "
                         f"{an.mult_produccion.mean():.2f} {ok} |")
            print(f"[OK] Brasil {anio}: {iot.Z.shape[0]}×{iot.Z.shape[0]} fila=col {rel:.1e} minZ {iot.min_valor():.2f}")
        except Exception as e:
            print(f"[ERROR] Brasil {anio}: {type(e).__name__}: {e}")
            filas.append(f"| {anio} | ERROR | {type(e).__name__} | | | | | |")
    (ROOT / "reports" / "brasil_todos.md").write_text("\n".join(filas), encoding="utf-8")
    print("[OK] Reporte en reports/brasil_todos.md")


if __name__ == "__main__":
    main()
