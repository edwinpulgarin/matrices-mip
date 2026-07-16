"""
Procesa TODOS los años disponibles de Argentina: COU → MIP (Modelo D) → Excel,
y escribe un reporte consolidado de gates de identidades por año.

Uso:  py -3 scripts/argentina_todos.py
Genera: output/MIP_Argentina_AAAA.xlsx  y  reports/argentina_todos.md
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
from src.valoracion import valorar_argentina
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.export_excel import exportar

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/argentina")
ANIOS = {
    2004: "cou_2004.xls", 2018: "cou_2018.xls", 2019: "cou_2019.xls",
    2020: "cou_2020.xls", 2021: "cou_2021.xls", 2022: "cou_2022.xls",
}
S = 1e6


def main():
    modelo = sys.argv[1].upper() if len(sys.argv) > 1 else "D"
    sufijo = "_prod" if modelo == "B" else ""
    tipo = "producto × producto (Modelo B)" if modelo == "B" else "industria × industria (Modelo D)"
    filas = ["# Argentina — MIP reconstruidas desde COU (UN Handbook F74 Rev.1)\n",
             f"{tipo}, precios básicos, miles de millones de pesos corrientes.\n",
             "| Año | Dim | VBP | VAB | fila=columna | L·f=x | min Z | mult. medio | Excel |",
             "|----:|----:|----:|----:|:---:|:---:|:---:|:---:|:---|"]
    for anio, fn in ANIOS.items():
        d = parse(RAW / fn, anio)
        sut, _ = valorar_argentina(d)
        sutb, _ = balancear(sut)
        iot = transformar(sutb, modelo)
        an = calcular(iot)
        rel = float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max())
        lfx = an.check_Lf_x / max(sut.g.sum(), 1)
        n = iot.Z.shape[0]
        cou_int = d["U_pc"].sum(axis=0) if modelo == "D" else None
        xlsx = exportar(
            iot, an, ROOT / "output" / f"MIP_Argentina_{anio}{sufijo}.xlsx",
            pais="Argentina", anio=anio, unidad=sut.unidad,
            valoracion="derivados del COU INDEC", fuente=f"INDEC — COU {anio}",
            labels=sut.meta.get("ind_labels", {}) if modelo == "D" else sut.meta.get("prod_labels", {}),
            cou_intermedio=cou_int,
        )
        ok = "✅" if (rel < 1e-6 and lfx < 1e-6 and iot.min_valor() >= -1e-9) else "⚠️"
        filas.append(
            f"| {anio} | {n}×{n} | {sut.g.sum()/S:,.0f} | {d['VA'].values.sum()/S:,.0f} | "
            f"{rel:.1e} | {lfx:.1e} | {iot.min_valor():.2f} | {an.mult_produccion.mean():.2f} {ok} | "
            f"[{xlsx.name}](../output/{xlsx.name}) |"
        )
        print(f"[OK] {anio} ({tipo}): fila=col {rel:.1e} · L·f=x {lfx:.1e} · {xlsx.name}")

    out = ROOT / "reports" / f"argentina_todos{sufijo}.md"
    out.write_text("\n".join(filas), encoding="utf-8")
    print(f"\n[OK] Reporte consolidado en {out}")


if __name__ == "__main__":
    main()
