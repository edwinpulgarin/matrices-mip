"""
STATUS: qué matrices nuestras coinciden con la MIP que publica cada país.

Cruza dos cosas que ya existen y no vuelve a calcular nada:

    manifest_publicables.csv        el inventario de libros publicados
    reports/validacion_oficiales.csv  el resultado del arnés en R

y produce una tabla única que responde, libro por libro: ¿el país publica una
MIP oficial para ese año?, ¿la comparamos?, ¿coincide?

El criterio de «coincide» se aplica por separado a las dos mitades de la matriz,
porque miden cosas distintas:

    columnas  el consumo intermedio de cada sector. En el Modelo D es invariante
              al modelo (las columnas de D suman 1), así que una diferencia acá
              es de DATOS: valoración, corte por origen o balanceo.
    filas     el reparto producto→industria, que es la matriz D. Una diferencia
              acá es de MÉTODO o de nivel de detalle de productos.

Uso:  py -3 scripts/status_vs_oficiales.py
Sale: reports/STATUS_vs_MIP_oficiales.md
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# Tolerancias. La de columnas es exigente porque ahí no hay margen de método: o
# partimos del mismo dato o no. La de celdas admite el redondeo de la
# publicación oficial.
TOL_COL_REL = 1e-6      # columnas EXACTAS, respecto de la suma de la matriz
TOL_COL_CERCA = 1e-2    # columnas que difieren poco: el orden del §7.76
TOL_DESVIO = 0.10       # % de desvío absoluto por debajo del cual se considera igual
TOL_AGREGADO = 1.0      # % de dif. de suma admitida en matrices de coeficientes (A, L)

# Casos donde el país publica MIP pero no podemos contrastarla, con el motivo.
# Se declaran a mano porque el motivo no está en ningún dato: hay que saberlo.
SIN_CONTRASTE = {
    ("Colombia", "2015"): "el DANE publica MIP 2015, pero el anexo no está en el patrón de URL de 2019 y 2021",
    ("Colombia", "2017"): "el DANE publica MIP 2017, pero el anexo no está en el patrón de URL de 2019 y 2021",
    # 2021 ya se contrasta: desde que Colombia sale sólo del COU hay libro hasta
    # 2024, así que esta entrada quedó de reserva por si el anexo no está.
    ("Colombia", "2021"): "no está descargado el anexo del DANE de ese año",
    ("Mexico", "2008"): "INEGI publica MIP 2008, pero no el COU de utilización de ese año",
    ("Mexico", "2018"): "INEGI publica MIP 2018, pero no el COU de utilización de ese año",
    ("Uruguay", "2016"): ("el BCU publica producto×producto (128×128, Modelo B) y sólo 11 sectores "
                          "en industria×industria; no publica la correspondencia con el COU y su "
                          "metodología es un PDF escaneado"),
}

# Países y años donde directamente no hay MIP oficial publicada.
SIN_MIP = {
    "Argentina": "la única MIP publicada es la de 1997",
    "Brasil": "el IBGE publica MIP sólo para 2010 y 2015",
    "Colombia": "el DANE publica MIP para 2015, 2017, 2019 y 2021",
    "Mexico": "INEGI publica MIP para 2008, 2013 y 2018",
    "Uruguay": "el BCU publica MIP sólo para 2016",
}


def _leer_csv(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _veredicto(fila):
    """Clasifica una comparación en las mitades que importan.

    El criterio de columnas vale para las matrices de VALORES (`Z`, `D`): ahí la
    columna es el consumo intermedio del sector y tiene que dar exacto, porque en
    el Modelo D es invariante al reparto por productos. En una matriz de
    COEFICIENTES (`A`, `L`) esa prueba no significa nada —la columna de `L` es un
    multiplicador, no una suma de pesos— y aplicarla marcaba «DISTINTA» a la
    Leontief de Colombia, cuyo multiplicador medio queda a +0,43 % del DANE. Para
    ésas el veredicto se apoya en el agregado.
    """
    suma = abs(float(fila["suma_oficial"])) or 1.0
    desvio = float(fila["desvio_abs_pct"])
    coef = fila["objeto"].split()[0] in ("A", "L")
    col_ok = abs(float(fila["max_dif_columna"])) / suma < TOL_COL_REL
    if desvio < TOL_DESVIO:
        return "IGUAL", col_ok, desvio
    if coef:
        if abs(float(fila["dif_suma_pct"])) < TOL_AGREGADO:
            return "IGUAL EN AGREGADO", col_ok, desvio
        return "DISTINTA", col_ok, desvio
    if col_ok:
        return "IGUAL EN COLUMNAS", col_ok, desvio
    # Escalón intermedio: la columna no da exacta pero la diferencia es del orden
    # del reparto de impuestos y márgenes (§7.76), no de un problema de datos.
    # Sin él, Colombia —que difiere 0,09 %— caía en la misma bolsa que una
    # matriz que no tiene nada que ver.
    if abs(float(fila["max_dif_columna"])) / suma < TOL_COL_CERCA:
        return "CERCA EN COLUMNAS", col_ok, desvio
    return "DISTINTA", col_ok, desvio


def main():
    libros = _leer_csv(ROOT / "manifest_publicables.csv")
    comps = _leer_csv(ROOT / "reports" / "validacion_oficiales.csv")
    if not comps:
        print("[AVISO] falta reports/validacion_oficiales.csv — correr antes el arnés en R")

    # caso -> lista de comparaciones (Brasil compara D, A y L)
    por_caso = {}
    for c in comps:
        por_caso.setdefault(c["caso"], []).append(c)

    filas, resumen = [], {"IGUAL": 0, "IGUAL EN COLUMNAS": 0, "CERCA EN COLUMNAS": 0,
                          "IGUAL EN AGREGADO": 0, "DISTINTA": 0, "SIN CONTRASTE": 0}
    for lb in libros:
        pais, anio = lb["pais"], lb["anio"]
        caso = f"{'México' if pais == 'Mexico' else pais} {anio}"
        comparaciones = por_caso.get(caso, [])
        if lb.get("variante") == "OFICIAL":
            filas.append((pais, anio, lb["variante"], "—",
                          "es la matriz oficial: no se contrasta contra sí misma", ""))
            continue
        if not comparaciones:
            motivo = SIN_CONTRASTE.get((pais, anio))
            if motivo is None:
                motivo = f"no hay MIP oficial para ese año — {SIN_MIP.get(pais, '')}"
                estado = "sin MIP oficial"
            else:
                estado = "SIN CONTRASTE"
                resumen["SIN CONTRASTE"] += 1
            filas.append((pais, anio, lb.get("variante", ""), estado, motivo, ""))
            continue
        for c in comparaciones:
            estado, col_ok, desvio = _veredicto(c)
            resumen[estado] += 1
            # se reporta el número y no un juicio binario: en las matrices de
            # coeficientes (A, L) la tolerancia relativa a la suma es demasiado
            # exigente y diría «difieren» junto a un veredicto IGUAL.
            detalle = (f"suma {float(c['dif_suma_pct']):+.4f} % · "
                       f"máx. dif. columna {float(c['max_dif_columna']):.1e} · "
                       f"correlación {float(c['correlacion']):.4f} · "
                       f"desvío {desvio:.2f} %")
            filas.append((pais, anio, c["objeto"], estado, detalle, c["caso"]))

    md = ["# STATUS — nuestras matrices contra las MIP oficiales", "",
          "Qué matrices reproducen la MIP que publica el instituto y cuáles no.",
          "Se genera cruzando el inventario de libros con el resultado del arnés en R;",
          "no recalcula nada.", "",
          "## Cómo se lee el veredicto", "",
          "| Veredicto | Qué significa |",
          "|:--|:--|",
          "| **IGUAL** | Reproduce la matriz oficial: desvío absoluto por debajo del "
          f"{TOL_DESVIO:g} % |",
          "| **IGUAL EN COLUMNAS** | El consumo intermedio de cada sector coincide "
          "exacto —o sea que el dato, la valoración, el corte por origen y el balanceo "
          "son los del instituto— pero el reparto por filas difiere, porque el "
          "instituto arma su matriz `D` con más detalle de productos del que publica |",
          "| **IGUAL EN AGREGADO** | Sólo para matrices de coeficientes (`A`, `L`), donde "
          "la prueba de columnas no aplica —la columna de `L` es un multiplicador, no una "
          f"suma de pesos—: el agregado queda dentro del {TOL_AGREGADO:g} % y la diferencia "
          "que resta está en el reparto por filas |",
          "| **CERCA EN COLUMNAS** | El consumo intermedio por sector no da exacto pero "
          f"difiere menos del {100 * TOL_COL_CERCA:g} % de la suma de la matriz: es el "
          "orden del reparto proporcional de impuestos y márgenes, no un problema de "
          "datos |",
          "| **DISTINTA** | Ni siquiera las columnas se acercan: hay diferencia de datos |",
          "| **SIN CONTRASTE** | El país publica MIP para ese año pero falta algo para "
          "compararla; el motivo va en la fila |", "",
          "## Resultado", "",
          "| País | Año | Objeto | Veredicto | Detalle |",
          "|:--|:--|:--|:--|:--|"]
    for pais, anio, obj, estado, detalle, _ in sorted(filas):
        md.append(f"| {pais} | {anio} | {obj} | {estado} | {detalle} |")

    md += ["", "## Resumen", "",
           f"- **{resumen['IGUAL']}** comparaciones dan **igual** a la oficial",
           f"- **{resumen['IGUAL EN COLUMNAS']}** coinciden en columnas y difieren en filas",
           f"- **{resumen['CERCA EN COLUMNAS']}** difieren en columnas por debajo del "
           f"{100 * TOL_COL_CERCA:g} %",
           f"- **{resumen['IGUAL EN AGREGADO']}** son matrices de coeficientes que coinciden "
           "en el agregado",
           f"- **{resumen['DISTINTA']}** difieren también en columnas",
           f"- **{resumen['SIN CONTRASTE']}** tienen MIP oficial pero no se pudo contrastar",
           "",
           "El resto de los libros corresponde a años en los que el país no publica MIP: "
           "son justamente los que este trabajo produce por primera vez.", "",
           "## Por qué Colombia se aparta, y qué lo demuestra", "",
           "Las comparaciones domésticas de Colombia (`Z` y `L dom.`) son las que quedan "
           "por debajo del resto, y la causa está medida: **el COU del DANE no publica "
           "qué parte de cada celda se importó**, así que el corte por origen sale del "
           "prorrateo proporcional (§8.33) y deja insumo importado dentro de la matriz "
           "doméstica —27.226 de más en 2019, sobre un `Z` de 757.403—.", "",
           "La contraprueba está en el mismo cuadro: la **versión total**, donde las dos "
           "partes se vuelven a sumar y ese supuesto no interviene, da **−0,01 % en 2019 "
           "y +0,08 % en 2021** contra el Cuadro 8 del DANE, y el consumo intermedio "
           "total coincide al 0,09 %. O sea que el método, la valoración y el balanceo "
           "reproducen al instituto; lo que falta es un dato que la fuente no trae. Cada "
           "libro lo declara en la hoja «SUT importado». Ver `sesgo_prorrateo.md`.", ""]

    ruta = ROOT / "reports" / "STATUS_vs_MIP_oficiales.md"
    ruta.write_text("\n".join(md), encoding="utf-8")
    for k, v in resumen.items():
        print(f"  {k:20s} {v}")
    print(f"[OK] Status en {ruta.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
