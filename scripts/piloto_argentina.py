"""
Piloto end-to-end Argentina 2004: COU -> valoración -> balanceo ->
transformación (Modelo D) -> análisis, con reporte de gates de identidades.

Uso:  py -3 scripts/piloto_argentina.py [ruta_cou.xls] [anio]
Genera: reports/argentina_<anio>_balance.md
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

S = 1e6  # miles de pesos -> miles de millones (billones) de pesos


def main():
    ruta = (sys.argv[1] if len(sys.argv) > 1
            else r"c:/Users/edwin/Documents/MIP V2/data/raw/argentina/cou_2004.xls")
    anio = int(sys.argv[2]) if len(sys.argv) > 2 else 2004

    d = parse(ruta, anio)
    sut, repv = valorar_argentina(d)
    sutb, repb = balancear(sut)
    iot = transformar(sutb, "D")
    an = calcular(iot)

    gap = iot.balance_fila_columna()
    L = ["# Piloto Argentina %d — Reconstrucción MIP (UN Handbook F74 Rev.1)\n" % anio]
    L.append("Unidades: miles de millones de pesos corrientes.\n")

    L.append("## Insumo (COU crudo)")
    L.append(f"- Productos: {len(sut.productos)} · Industrias: {len(sut.industrias)}")
    L.append(f"- Producción bruta (VBP pb): {sut.g.sum()/S:,.1f}")
    L.append(f"- Consumo intermedio doméstico (pb): {sut.U.values.sum()/S:,.1f}")
    L.append(f"- Importaciones intermedias: {repv['importado_total']/S:,.1f}")
    L.append(f"- Impuestos netos a productos: {repv['impuestos_total']/S:,.1f}")
    L.append(f"- Valor agregado bruto: {repv['va_total']/S:,.1f}")
    L.append(f"- Demanda final doméstica: {sut.Y.values.sum()/S:,.1f}\n")

    def ok(x, umbral=1e-6):
        return "✅" if x < umbral else "⚠️"

    b0 = repv["balance"]; b1 = repb["balance_post"]
    L.append("## Gates de identidades contables")
    L.append("| Etapa (capítulo) | Identidad | Error relativo | |")
    L.append("|---|---|---|---|")
    L.append(f"| Valoración (Cap. 7) | balance industria `g=IC+M+T+VA` | {b0['max_rel_industria']:.2e} | {ok(b0['max_rel_industria'])} |")
    L.append(f"| Balanceo (Cap. 11) | balance producto oferta=uso | {b1['max_rel_producto']:.2e} | {ok(b1['max_rel_producto'])} |")
    L.append(f"| Balanceo (Cap. 11) | balance industria | {b1['max_rel_industria']:.2e} | {ok(b1['max_rel_industria'])} |")
    rel_fc = float((gap.abs() / iot.x.replace(0, 1)).max())
    L.append(f"| Transformación (Cap. 12) | **IOT fila = columna** | {rel_fc:.2e} | {ok(rel_fc)} |")
    L.append(f"| Análisis (Cap. 20) | Leontief `L·f = x` | {an.check_Lf_x/max(sut.g.sum(),1):.2e} | {ok(an.check_Lf_x/max(sut.g.sum(),1))} |")
    neg = "✅" if iot.min_valor() >= -1e-9 else "⚠️"
    Lneg = "✅" if (an.L.values >= -1e-9).all() else "⚠️"
    L.append(f"| Transformación (Cap. 12) | sin negativos en Z/VA | min={iot.min_valor():.3f} | {neg} |")
    L.append(f"| Análisis (Cap. 20) | inversa de Leontief `L≥0` | min={an.L.values.min():.3f} | {Lneg} |\n")

    L.append("## Multiplicadores de producción (encadenamiento hacia atrás)")
    L.append(f"- min={an.mult_produccion.min():.2f} · media={an.mult_produccion.mean():.2f} · max={an.mult_produccion.max():.2f}")
    top = an.mult_produccion.sort_values(ascending=False).head(5)
    labs = sut.meta.get("ind_labels", {})
    L.append("- Top 5:")
    for cod, m in top.items():
        L.append(f"  - {labs.get(cod, cod)[:45]}: {m:.2f}")

    out = ROOT / "reports" / f"argentina_{anio}_balance.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))
    print(f"\n[OK] Reporte escrito en {out}")

    xlsx = exportar(
        iot, an, ROOT / "output" / f"MIP_Argentina_{anio}.xlsx",
        pais="Argentina", anio=anio, unidad=sut.unidad,
        valoracion="derivados del COU INDEC", fuente=f"INDEC — COU {anio}",
        labels=sut.meta.get("ind_labels", {}),
    )
    print(f"[OK] Excel auditable (valores calculados) en {xlsx}")


if __name__ == "__main__":
    main()
