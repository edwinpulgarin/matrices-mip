"""
¿En qué matrices interviene el balanceo RAS, y cuánto?

El RAS (Handbook, Cap. 11) es el único paso de toda la cadena que cambia celdas
sin que lo mande una identidad contable: ajusta la utilización hasta que la
oferta y el uso cierren a la vez por producto y por industria. Es legítimo y
está en el Handbook, pero es también el paso que un auditor quiere ver acotado,
porque es el único que no se puede rehacer con aritmética directa entre hojas.

Este reporte contesta tres preguntas, matriz por matriz:

  1. ¿Corre el RAS?  Sólo corre si el SUT entra sin cumplir las identidades.
  2. ¿Cuánto tuvo que mover?  En porcentaje de la utilización y en la celda peor.
  3. ¿Por qué?  El desbalance con el que entra el SUT mide la calidad del cuadro
     PUBLICADO, no la del pipeline: si el instituto publica un cuadro que cierra
     solo, el RAS no hace nada.

El orden de la tabla es de menor a mayor intervención, así que se lee de arriba
—las matrices que se pueden cerrar sin discusión— hacia abajo.

Uso:  py -3 scripts/estado_ras.py
Sale: reports/estado_ras.md
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

from src.valoracion import valorar_argentina, ensamblar_directo
from src.balanceo import balancear
from src.transformacion import transformar, desde_mip_oficial
from src.analisis import calcular

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw")
NI = RAW / "Nueva_Info"


def casos():
    """(país, año, cargar, limpio) para las 38 matrices publicadas."""
    from src.parsers.argentina import parse as ar
    from src.parsers.argentina97 import parse as ar97
    from src.parsers.brasil import parse as br
    from src.parsers.brasil_mip import parse as brmip
    from src.parsers.uruguay import parse as uy
    from src.parsers.mexico import parse_sin_prorrateo as mx
    from src.parsers.colombia import parse_cou as co

    for a in range(2014, 2025):
        yield "Colombia", a, (lambda a=a: co(RAW / "colombia", a)), False
    yield "México", 2013, (lambda: mx(RAW / "_cepal_staging" / "MEX_COU_2013", 2013,
                                      nivel="RAMA")), True
    for a in (2010, 2015):
        yield "Brasil", a, (lambda a=a: brmip(RAW / "brasil", a)), True
    for a in (2011, 2012, 2013, 2014, 2016, 2017, 2018, 2019, 2020, 2021):
        yield "Brasil", a, (lambda a=a: br(RAW / "brasil", a)), False
    yield "Uruguay", 2012, (lambda: uy(NI / "Uruguay_2012_Detallada_COU_C.xlsx", 2012,
                                       hoja="COU_C")), False
    yield "Uruguay", 2016, (lambda: uy(NI / "Uruguay_2016-2017 Detallada_COU_C.xlsx", 2016,
                                       hoja="2016 CORRIENTE")), False
    yield "Uruguay", 2017, (lambda: uy(NI / "Uruguay_2016-2017 Detallada_COU_C.xlsx", 2017,
                                       hoja="2017 CORRIENTE",
                                       carpeta_detalle=RAW / "uruguay" / "cou_2017")), False
    yield "Argentina", 1997, (lambda: ar97(RAW / "argentina_mip97", 1997)), True
    for a in (2004, 2018, 2019, 2020, 2021, 2022, 2023):
        yield "Argentina", a, (lambda a=a: ar(RAW / "argentina" / f"cou_{a}.xls", a)), False


def medir(pais, anio, cargar, limpio):
    d = cargar()
    # Se mide el SUT que alimenta la matriz publicada, que es la doméstica.
    sut, _ = (ensamblar_directo(d) if limpio else valorar_argentina(d))
    prev = sut.resumen_balance()
    sutb, rep = balancear(sut)
    iot = transformar(sutb, "D", no_mercado=d.get("no_mercado"))
    an = calcular(iot)

    dif = (sutb.U - sut.U).abs()
    total_u = float(sut.U.to_numpy().sum()) or 1.0

    # Los productos que obligan al ajuste. Es el dato que hace falta para
    # decidir si el desbalance es del cuadro publicado o de nuestra lectura: si
    # se concentra en pocos productos, hay que ir a mirarlos uno por uno, que es
    # exactamente como apareció lo del tabaco.
    bp = sut.balance_producto()
    oferta = (sut.V.sum(axis=0) + (sut.M if sut.M is not None else 0)).abs()
    rel = (bp.abs() / oferta.replace(0, float("nan"))).fillna(0.0)
    peores = [{"cod": str(k),
               "nombre": str(d.get("prod_name", {}).get(k, k))[:44],
               "rel": float(rel[k]),
               "abs": float(bp[k]),
               "oferta": float(oferta.get(k, 0.0))}
              for k in rel.sort_values(ascending=False).head(3).index
              if rel[k] > 1e-6]
    return {
        "pais": pais, "anio": anio,
        "corre": rep["aplicado"],
        "modo": rep.get("modo", "RAS" if rep["aplicado"] else "no hizo falta"),
        "discrepancia": rep.get("discrepancia_rel", 0.0),
        "desbalance": prev["max_rel_producto"],
        "mueve": float(dif.to_numpy().sum()) / total_u,
        "peor_celda": float(dif.to_numpy().max()),
        "peor_pct": float((dif / sut.U.abs().replace(0, float("nan"))).max().max() or 0.0),
        "negativos": rep.get("celdas_fijas_negativas", 0),
        "iter": rep.get("iteraciones_ras", 0),
        "fila_col": float((iot.balance_fila_columna().abs() / iot.x.replace(0, 1)).max()),
        "mult": float(an.mult_produccion.mean()),
        "unidad": sut.unidad,
        "peores": peores,
    }


# Las MIP oficiales de INEGI no pasan por el SUT: la matriz viene construida, así
# que no hay nada que balancear. Se listan aparte para que no falten en el
# inventario y para que quede claro POR QUÉ no tienen RAS.
OFICIALES = [("México", 2008), ("México", 2013), ("México", 2018)]


def main():
    filas, errores = [], []
    for pais, anio, cargar, limpio in casos():
        try:
            r = medir(pais, anio, cargar, limpio)
            filas.append(r)
            print(f"[OK] {pais} {anio}: {r['modo']:<13} "
                  f"mueve {100 * r['mueve']:.4f}% desbalance {r['desbalance']:.1e}")
        except Exception as e:
            errores.append((pais, anio, f"{type(e).__name__}: {e}"))
            print(f"[ERROR] {pais} {anio}: {type(e).__name__}: {e}")

    # orden: primero las que no necesitan RAS, después por cuánto mueve
    _orden = {"no hizo falta": 0, "discrepancia": 1, "RAS": 2}
    filas.sort(key=lambda r: (_orden.get(r["modo"], 9), r["desbalance"]))

    sin_ras = [r for r in filas if not r["corre"]]
    con_ras = [r for r in filas if r["corre"]]

    md = [
        "# ¿Dónde interviene el balanceo RAS, y cuánto?\n",
        "El RAS (Handbook, Cap. 11) es el **único paso de toda la cadena que cambia "
        "celdas sin que lo mande una identidad contable**. Ajusta la utilización hasta "
        "que la oferta y el uso cierren a la vez por producto y por industria: escala "
        "las filas para que den su total, después las columnas, y repite hasta "
        "converger. Es también el único paso que no se puede rehacer con aritmética "
        "directa entre las hojas del libro, por ser iterativo.\n",
        "Por eso conviene tenerlo acotado y a la vista, y por eso el pipeline lo usa lo "
        "menos posible. Hay tres formas de cerrar el cuadro y cada libro declara cuál "
        "usó:\n",
        "1. **Cerraba solo** — el cuadro publicado ya cumple las dos identidades y no se "
        "toca nada.",
        "2. **Sin tocar nada** — queda un residuo chico y se anota en una columna propia "
        "de demanda final, «discrepancia estadística», como hacen las cuentas "
        "nacionales. **Ninguna celda leída se modifica**, así que `Z = D·U` se puede "
        "rehacer a mano desde las hojas del libro.",
        "3. **RAS** — el residuo es demasiado grande para llamarlo discrepancia (más del "
        "2 % de la oferta de algún producto) y ahí sí se ajusta.\n",
        "La columna «desbalance al entrar» mide la **calidad del cuadro publicado**, no "
        "la del pipeline: si el instituto publica un cuadro que cierra solo, no hay nada "
        "que hacer.\n",
        "## Resumen\n",
        f"- **{sum(1 for r in filas if r['modo'] != 'RAS')} de {len(filas)} matrices se "
        f"arman sin modificar una sola celda leída** "
        f"({sum(1 for r in filas if r['modo'] == 'no hizo falta')} cerraban solas y "
        f"{sum(1 for r in filas if r['modo'] == 'discrepancia')} anotan el residuo como "
        "discrepancia).",
        f"- **Sólo {len(con_ras)} necesitan el RAS.**",
        f"- **{len(OFICIALES)} más** (las MIP oficiales de INEGI) no pasan siquiera por el "
        "SUT: la matriz viene ya construida por el instituto.\n",
        "## El cuadro\n",
        "Ordenado de menor a mayor intervención: arriba las que se pueden cerrar sin "
        "discusión, abajo las que hay que mirar.\n",
        "| # | País | Año | Cómo se cerró | Desbalance al entrar | Discrepancia | "
        "Mueve de U | Negativos fijos | fila = columna | Mult. |",
        "|--:|:--|--:|:--|--:|--:|--:|--:|--:|--:|",
    ]
    for i, r in enumerate(filas, 1):
        etq = {"no hizo falta": "**cerraba solo**",
               "discrepancia": "**sin tocar nada**",
               "RAS": "RAS"}.get(r["modo"], r["modo"])
        md.append(
            f"| {i} | {r['pais']} | {r['anio']} | {etq} | "
            f"{r['desbalance']:.1e} | "
            f"{100 * r['discrepancia']:.4f} % | "
            f"{100 * r['mueve']:.4f} % | "
            f"{r['negativos'] or '—'} | "
            f"{r['fila_col']:.1e} | {r['mult']:.4f} |")
    for pais, anio in OFICIALES:
        md.append(f"| — | {pais} | {anio} | no aplica | — | — | — | — | — | — |")

    md += [
        "",
        "## El patrón: son comercio y transporte\n",
        "Los productos que obligan al ajuste son casi siempre los mismos: **servicios "
        "de comercio y de transporte**. No es casualidad ni ruido — son las filas que "
        "PRESTAN los márgenes. El paso de precios de comprador a básicos les saca el "
        "margen a los bienes y se lo devuelve a esas filas (§7.77), y como el reparto "
        "entre celdas es proporcional, el residuo de esa operación aterriza ahí.\n",
        "Es una buena noticia para la auditoría: el RAS no está tapando un error "
        "disperso, está cerrando el residuo de un paso identificado. Si el desbalance "
        "apareciera en un producto agrícola aislado, como pasó con el tabaco, ahí sí "
        "habría que ir a mirar la lectura de la fuente.\n",
        "«Negativos fijos» son las celdas que la fuente publica en negativo —variación "
        "de existencias— y que quedan **fuera** del ajuste: el RAS es multiplicativo y "
        "sólo está definido sobre celdas no negativas (Box 11.3). Se conservan con su "
        "valor exacto y su aporte se descuenta del margen de su fila y de su columna.\n",
        "## Cómo leer cada bloque\n",
    ]

    # ── bloque por país, del más limpio al más complejo ────────────────────
    por_pais = {}
    for r in filas:
        por_pais.setdefault(r["pais"], []).append(r)
    orden_pais = sorted(por_pais, key=lambda p: (
        any(r["corre"] for r in por_pais[p]),
        max(r["mueve"] for r in por_pais[p])))

    for pais in orden_pais:
        rs = por_pais[pais]
        n_sin = sum(1 for r in rs if not r["corre"])
        peor = max(rs, key=lambda r: r["mueve"])
        md.append(f"### {pais}\n")
        md.append(f"- {n_sin} de {len(rs)} años **no necesitan** el ajuste.")
        md.append(f"- El año que más lo necesita es **{peor['anio']}**: mueve el "
                  f"{100 * peor['mueve']:.4f} % de la utilización, y la celda que más "
                  f"cambia lo hace en {peor['peor_celda']:,.0f} "
                  f"({peor['unidad']}).")
        # El año a mirar no es el que más MUEVE sino el que entra con el mayor
        # desbalance relativo: ahí es donde un producto suelto puede estar
        # arrastrando al resto, que es como apareció lo del tabaco.
        peor_des = max(rs, key=lambda r: r["desbalance"])
        md.append(f"- El que entra **peor** es **{peor_des['anio']}**: hay un producto "
                  f"desbalanceado en {100 * peor_des['desbalance']:.1f} % de su propia "
                  f"oferta antes del ajuste.")
        if peor_des["peores"]:
            md.append(f"- Los productos que obligan al ajuste en {peor_des['anio']}:")
            md.append("")
            md.append("  | Producto | Desbalance | Sobre su oferta |")
            md.append("  |:--|--:|--:|")
            for q in peor_des["peores"]:
                md.append(f"  | {q['cod']} · {q['nombre']} | {q['abs']:,.0f} | "
                          f"{100 * q['rel']:.1f} % |")
        md.append("")

    if errores:
        md += ["## No se pudieron medir\n"]
        for pais, anio, e in errores:
            md.append(f"- {pais} {anio}: {e}")
        md.append("")

    ruta = ROOT / "reports" / "estado_ras.md"
    ruta.write_text("\n".join(md) + "\n", encoding="utf-8")

    # El mismo contenido en CSV, para que la lista de chequeo lo consuma sin
    # volver a calcular nada. Mismo criterio que `validacion_oficiales.csv`: un
    # reporte se lee, un CSV se cruza.
    import csv
    campos = ["pais", "anio", "modo", "desbalance", "discrepancia", "mueve",
              "negativos", "fila_col", "mult"]
    with open(ROOT / "reports" / "estado_ras.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for r in filas:
            w.writerow({k: r[k] for k in campos})

    print(f"\n[OK] Reporte en {ruta.relative_to(ROOT)}  "
          f"({len(sin_ras)} sin RAS / {len(filas)} medidas)")


if __name__ == "__main__":
    main()
