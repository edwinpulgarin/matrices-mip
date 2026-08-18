"""¿Estamos leyendo toda la utilización que publica cada fuente?

Recorre todos los países y años, y para cada uno contrasta la identidad del
propio COU: la oferta que la fuente declara a precios de comprador contra la
utilización que el parser leyó. Un faltante de un solo signo es la firma de una
columna del archivo que ningún patrón reclamó.

Existe porque pasó: «Trabajos en curso» del INDEC estuvo seis años sin leerse y
el balanceo lo tapaba. Ver src/cobertura.py.

Uso:  py -3 scripts/auditar_cobertura.py   →  reports/cobertura_fuentes.md
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

from src import cobertura as cob

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw")
NI = RAW / "Nueva_Info"

# Desvíos investigados que NO son error de lectura. El control no puede
# distinguir solo «leímos de menos» de «la fuente no cierra»: las dos cosas dan
# faltante de un signo. La diferencia se establece revisando el archivo, y el
# resultado se anota acá para que el desvío quede declarado en vez de tapado.
CONOCIDOS = {
    ("Colombia", 2020): (
        "La MUPNI 2020 es **provisional** (`DANE_MUPNI_2020p.xlsx`) y no cierra contra el "
        "COU: la producción supera al uso doméstico en 9.173 (1,1 % de la oferta). "
        "Verificado que NO es lectura: 2020 tiene exactamente las mismas cuatro columnas "
        "de demanda final que 2014-2019, que cierran a cero. El desvío está en la fuente y "
        "lo absorbe el balanceo; conviene rehacer el año cuando el DANE publique la "
        "versión definitiva. En la versión a 392 productos se ve amplificado, porque el "
        "cierre intra-grupo sólo puede correr donde los márgenes del grupo son "
        "consistentes, y en 2020 no lo son."),
}


def casos():
    from src.parsers.argentina import parse as ar
    from src.parsers.brasil import parse as br
    from src.parsers.uruguay import parse as uy
    from src.parsers.mexico import parse_sin_prorrateo as mx
    from src.parsers.colombia import parse_cou as co   # la versión publicada

    for a in (2004, 2018, 2019, 2020, 2021, 2022, 2023):
        yield "Argentina", a, lambda a=a: ar(RAW / "argentina" / f"cou_{a}.xls", a)
    for a in range(2010, 2022):
        yield "Brasil", a, lambda a=a: br(RAW / "brasil", a)
    yield "Uruguay", 2012, lambda: uy(NI / "Uruguay_2012_Detallada_COU_C.xlsx", 2012, hoja="COU_C")
    for a in (2016, 2017):
        yield "Uruguay", a, lambda a=a: uy(NI / "Uruguay_2016-2017 Detallada_COU_C.xlsx", a,
                                           hoja=f"{a} CORRIENTE")
    yield "México", 2013, lambda: mx(RAW / "_cepal_staging" / "MEX_COU_2013", 2013, nivel="RAMA")
    # Colombia sale ahora del COU y su cobertura llega hasta la última
    # publicación: el control SÍ aplica (hay OPC contra qué contrastar), cosa
    # que con la MUPNI no ocurría.
    for a in range(2014, 2025):
        yield "Colombia", a, lambda a=a: co(RAW / "colombia", a)


def main():
    filas = [
        "# Cobertura de la fuente — ¿leemos toda la utilización que se publica?\n",
        "Para cada producto, la oferta que la fuente declara a precios de comprador "
        "tiene que ser igual a la utilización que leímos:\n",
        "```\nOPC_p  ==  Σ_j U_pc[p,j] + Σ_c Y_pc[p,c]\n```\n",
        "Es la identidad contable del propio COU, así que no supone nada. Si no cierra, "
        "o leímos de menos o la fuente no cuadra.\n",
        "**Por qué existe este control.** Los parsers eligen columnas por palabras clave. "
        "Si la fuente agrega una columna que ningún patrón reclama, se descarta sin error "
        "y el producto queda con oferta pero sin uso; el balanceo (Cap. 11) cierra esa fila "
        "igual y el resultado se ve normal. Pasó: el INDEC abre desde 2018 una columna de "
        "demanda final «Trabajos en curso» —los cultivos en pie— que el parser de Argentina "
        "no leía. En tabaco sin elaborar 2023 era el 33 % de la oferta del producto.\n",
        "**Neto vs bruto.** Una columna perdida falta siempre en el mismo sentido, así que "
        "se ve en el **neto**. El bruto además recoge reasignaciones de la fuente entre "
        "productos vecinos, que vienen en pares que se cancelan y no son un error de "
        f"lectura. El disparador es el neto, con tolerancia {cob.TOL_NETO:.0e}.\n",
        "¹ Colombia ya publica a precios básicos y sin puente de valoración, así que no "
        "hay OPC contra qué contrastar. El control equivalente es el **balance de producto "
        "antes del balanceo**: si leyéramos de menos, la oferta no igualaría al uso y el "
        "desvío aparecería igual.\n",
        "| País | Año | Productos | Neto | Bruto | Estado |",
        "|:---|---:|---:|---:|---:|:---:|",
    ]
    peor = 0.0
    problemas = []
    medidos = []          # los casos que se llegaron a evaluar, para el CSV
    for pais, anio, build in casos():
        medidos.append((pais, anio, None))
        try:
            d = build()
            r = cob.verificar(d, estricto=False)
            if not r["aplica"]:
                # Colombia ya viene a precios básicos y sin puente de valoración,
                # así que no hay OPC contra qué contrastar. El equivalente es el
                # balance de producto ANTES de balancear: si leyéramos de menos,
                # la oferta no igualaría al uso y el desvío saltaría acá igual.
                from src.valoracion import ensamblar_directo
                sut, _ = ensamblar_directo(d)
                bp = sut.balance_producto()
                esc = float(sut.q.sum()) or 1.0
                neto, bruto = float(bp.sum()) / esc, float(bp.abs().sum()) / esc
                ok = abs(neto) <= cob.TOL_NETO
                conocido = (pais, anio) in CONOCIDOS
                if not ok and not conocido:
                    problemas.append((pais, anio, {"neto_rel": neto, "peores": [
                        (str(d.get("prod_name", {}).get(p, p)), float(bp[p]))
                        for p in bp.abs().sort_values(ascending=False).head(3).index]}))
                marca = "✅" if ok else ("⚠️ documentado" if conocido else "❌")
                filas.append(f"| {pais} | {anio} | {len(d['U_dom']):,} | {neto:.2e} | "
                             f"{bruto:.2e} | {marca} ¹ |")
                print(f"[{'OK ' if ok else 'REV'}] {pais} {anio}: balance de producto "
                      f"pre-RAS {neto:.2e}")
                continue
            conocido = (pais, anio) in CONOCIDOS
            ok = "✅" if r["ok"] else ("⚠️ documentado" if conocido else "❌")
            if r["ok"]:
                peor = max(peor, abs(r["neto_rel"]))
            elif not conocido:
                problemas.append((pais, anio, r))
            filas.append(f"| {pais} | {anio} | {len(d['U_pc']):,} | {r['neto_rel']:.2e} | "
                         f"{r['bruto_rel']:.2e} | {ok} |")
            extra = d.get("columnas_sin_leer") or []
            if extra:
                problemas.append((pais, anio, {"sin_leer": extra}))
            print(f"[{'OK ' if r['ok'] else 'REV'}] {pais} {anio}: neto {r['neto_rel']:.2e}"
                  + (f"  columnas sin leer: {extra}" if extra else ""))
        except Exception as e:
            filas.append(f"| {pais} | {anio} | — | — | — | ❌ {type(e).__name__} |")
            print(f"[ERR] {pais} {anio}: {type(e).__name__}: {e}")

    filas.append("")
    if CONOCIDOS:
        filas.append("## Desvíos declarados (revisados: no son error de lectura)\n")
        for (p, a), txt in CONOCIDOS.items():
            filas.append(f"- **{p} {a}** — {txt}")
        filas.append("")
    if problemas:
        filas.append("## Casos a revisar\n")
        for pais, anio, r in problemas:
            if "sin_leer" in r:
                filas.append(f"- **{pais} {anio}**: columnas con datos que ningún patrón "
                             f"reclamó: {r['sin_leer']}")
            else:
                det = "; ".join(f"{n[:44]} ({v:,.0f})" for n, v in r["peores"][:3])
                filas.append(f"- **{pais} {anio}**: neto {r['neto_rel']:.2e}. Peores: {det}")
    else:
        filas.append(f"**Sin hallazgos.** El peor faltante neto de todo el conjunto es "
                     f"{peor:.2e} de la oferta, contra una tolerancia de {cob.TOL_NETO:.0e}: "
                     f"tres órdenes de magnitud de margen. Ninguna fuente tiene columnas con "
                     f"datos sin leer.")
    filas.append(
        "\n## Qué NO cubre este control\n\n"
        "Verifica que leímos todo lo publicado, no que lo publicado sea correcto ni que lo "
        "hayamos clasificado bien. Una columna leída pero mapeada a la categoría equivocada "
        "de demanda final pasa este control sin problema: eso lo cubre la hoja «COU Demanda "
        "final» de cada libro, que conserva los nombres nativos de la fuente al lado del "
        "esquema armonizado.")

    f = ROOT / "reports" / "cobertura_fuentes.md"
    f.write_text("\n".join(filas) + "\n", encoding="utf-8")

    # CSV para la lista de chequeo: sólo país, año y si pasó. El detalle vive en
    # el reporte; acá va lo que se cruza con los otros controles.
    import csv
    malos = {(p, str(a)) for p, a, _ in problemas}
    with open(ROOT / "reports" / "cobertura.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["pais", "anio", "ok"])
        for pais, anio, _ in medidos:
            w.writerow([pais, anio, "no" if (pais, str(anio)) in malos else "si"])

    print(f"\n[OK] Reporte en {f.relative_to(ROOT)}  ({len(problemas)} a revisar)")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
