# -*- coding: utf-8 -*-
"""
Compara los coeficientes de Leontief de la versión ANTERIOR del repositorio
(`matrices-mip/`, libros `_auditable.xlsx`) contra los actuales, por país y año.

La comparación va en dos carriles porque las dos versiones NO publican el mismo
objeto:

  * El `Cuadro 8` del libro viejo es la inversa de Leontief de la matriz TOTAL
    (nacional + importada). Verificado: recalcular (I−A)⁻¹ desde el `Cuadro 7`
    con x = Σcolumna + valor agregado reproduce el `Cuadro 8` con diferencia
    máxima 0,00000 en Brasil 2015; desde el `Cuadro 5` (nacional) no.
  * El libro actual publica SÓLO la matriz DOMÉSTICA (hoja «Leontief») y todo lo
    que se deriva de ella. La total no se entrega, pero se reconstruye desde el
    propio libro: Z^total = Z + D·U^imp, con las tres piezas en las hojas «MIP
    completa», «D participaciones» y «SUT importado».

  Carril A — misma definición: L viejo vs L total del libro nuevo, reconstruida
             con L = (I − Z^total·diag(g)⁻¹)⁻¹.
  Carril B — lo publicado antes vs lo publicado ahora: L viejo vs hoja
             «Leontief». Es la diferencia que ve quien baje los dos paquetes.

Salidas: `reports/comparacion_version_anterior.md` y el CSV con las métricas.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

# La consola de Windows es cp1252 y este script imprime flechas y acentos: sin
# esto el proceso muere en el último print, después de haber hecho todo el
# trabajo. Mismo preámbulo que el resto de los scripts del repo.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

RAIZ = Path(__file__).resolve().parents[1]
VIEJO = RAIZ / "matrices-mip" / "matrices"
NUEVO = RAIZ / "matrices"
SALIDA_MD = RAIZ / "reports" / "comparacion_version_anterior.md"
SALIDA_CSV = RAIZ / "reports" / "comparacion_version_anterior.csv"

# Años con detalle sectorial en el reporte (uno por país, el más informativo).
FOCO = {("Argentina", 2022), ("Brasil", 2015), ("Mexico", 2013), ("Uruguay", 2012)}


# ── lectura de las hojas ──────────────────────────────────────────────────────

def _num(x):
    """Los libros viejos guardan los números como TEXTO en varias hojas."""
    if x is None:
        return np.nan
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip().replace(",", "."))
    except ValueError:
        return np.nan


def _txt(x):
    return "" if x is None else str(x).strip()


def grilla(f: Path, patron: str) -> tuple[list[list], str]:
    """Grilla de valores de la primera hoja cuyo título coincida con `patron`."""
    wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
    try:
        hojas = [ws.title for ws in wb.worksheets]
        elegida = next((h for h in hojas if re.search(patron, h, re.I)), None)
        if elegida is None:
            raise KeyError(f"{f.name}: ninguna hoja coincide con /{patron}/ ({hojas})")
        ws = wb[elegida]
        return [list(r) for r in ws.iter_rows(values_only=True)], elegida
    finally:
        wb.close()


def matriz(g: list[list]) -> pd.DataFrame:
    """
    Matriz cuadrada rotulada: las filas de datos traen código en la col A y
    números desde la C; el encabezado es la fila que más repite esos códigos.
    Sirve igual para el libro viejo (`Cuadro N`) y para el nuevo.
    """
    cand = []
    for i, r in enumerate(g):
        cod = _txt(r[0] if r else None)
        if not cod or len(cod) > 14:
            continue
        if sum(1 for v in (_num(c) for c in r[2:]) if not np.isnan(v)) < 3:
            continue
        cand.append((i, cod))
    if not cand:
        raise ValueError("no encontré filas de datos")

    # El encabezado es la fila que más códigos de las filas SIGUIENTES repite. Hay
    # que buscarlo así y no sólo por encima de la primera fila con números: donde
    # los códigos son numéricos (Argentina, México) el propio encabezado parece
    # una fila de datos.
    def coincidencias(i):
        posteriores = {c for k, c in cand if k > i}
        return sum(1 for c in g[i][2:] if _txt(c) in posteriores)

    hr = max(range(len(g)), key=coincidencias)
    filas = [(i, c) for i, c in cand if i > hr]
    cs = {c for _, c in filas}
    cols = [(j + 2, _txt(c)) for j, c in enumerate(g[hr][2:]) if _txt(c) in cs]
    M = pd.DataFrame([[_num(g[i][j]) for j, _ in cols] for i, _ in filas],
                     index=[c for _, c in filas], columns=[c for _, c in cols]).fillna(0.0)
    return M.loc[~M.index.duplicated(), ~M.columns.duplicated()]


def nombres(g: list[list]) -> dict:
    return {_txt(r[0]): _txt(r[1]) for r in g if r and _txt(r[0]) and _txt(r[1])}


def columna_por_rotulo(g: list[list], rotulo: str, codigos: list[str]) -> pd.Series:
    """Columna de la hoja identificada por su rótulo de encabezado (p. ej. 'Producción total')."""
    clave = rotulo.lower()
    for i, r in enumerate(g[:20]):
        for j, c in enumerate(r):
            if clave in _txt(c).lower():
                vals = {}
                for rr in g[i + 1:]:
                    cod = _txt(rr[0] if rr else None)
                    if cod in codigos and len(rr) > j:
                        vals[cod] = _num(rr[j])
                if len(vals) >= len(codigos) * 0.9:
                    return pd.Series(vals).reindex(codigos)
    raise KeyError(f"no encontré la columna «{rotulo}»")


def fila_por_rotulo(g: list[list], rotulo: str, codigos: list[str]) -> pd.Series:
    """Fila de totales identificada por su rótulo en las dos primeras columnas."""
    clave = rotulo.lower()
    for r in g:
        if any(clave in _txt(c).lower() for c in r[:2]):
            nums = [v for v in (_num(c) for c in r[2:]) if not np.isnan(v)]
            if len(nums) >= len(codigos):
                return pd.Series(nums[:len(codigos)], index=codigos)
    raise KeyError(f"no encontré la fila «{rotulo}»")


# ── construcción de las inversas ──────────────────────────────────────────────

def leontief(Z: pd.DataFrame, x: pd.Series) -> pd.DataFrame:
    """L = (I − A)⁻¹ con A[i,j] = Z[i,j] / x[j]. Columna sin producción ⇒ A = 0."""
    cod = list(Z.index)
    xv = x.reindex(cod).fillna(0.0).to_numpy()
    A = np.nan_to_num(Z.to_numpy() / np.where(xv == 0, np.nan, xv)[None, :])
    L = np.linalg.inv(np.eye(len(cod)) - A)
    return pd.DataFrame(L, index=cod, columns=cod)


def l_vieja(f: Path) -> pd.DataFrame:
    """`Cuadro 8` = inversa de Leontief de la matriz total, tal como se publicó."""
    return matriz(grilla(f, r"^Cuadro 8$")[0])


def matriz_rect(g: list[list]) -> pd.DataFrame:
    """Matriz RECTANGULAR rotulada (D es ind×prod, U^imp es prod×ind).

    `matriz()` no sirve acá: identifica el encabezado por cuántos códigos de fila
    repite, y en una rectangular las filas y las columnas son dimensiones
    distintas, así que no repite ninguno. Se ubica el encabezado por la misma
    convención que usa el exportador y que ya lee `validar_consistencia`: la fila
    que trae «Código» en la columna A. Debajo puede venir una fila de nombres sin
    código, que se saltea.
    """
    hr = next((i for i, r in enumerate(g[:30])
               if r and _txt(r[0]).lower() == "código"), None)
    if hr is None:
        raise KeyError("no encontré la fila de encabezado («Código» en la columna A)")
    cols = []
    for j, c in enumerate(g[hr][2:], start=2):
        cod = _txt(c)
        if not cod:
            break
        cols.append((j, cod))
    filas = []
    for r in g[hr + 1:]:
        cod = _txt(r[0] if r else None)
        if not cod:
            if filas:
                break
            continue          # la fila de nombres, debajo del encabezado
        if cod.lower().startswith("fuente"):
            break
        filas.append((r, cod))
    M = pd.DataFrame([[_num(r[j]) if len(r) > j else np.nan for j, _ in cols]
                      for r, _ in filas],
                     index=[c for _, c in filas],
                     columns=[c for _, c in cols]).fillna(0.0)
    return M.loc[~M.index.duplicated(), ~M.columns.duplicated()]


def z_total(f: Path, Z_dom: pd.DataFrame) -> pd.DataFrame:
    """Z total reconstruida desde el propio libro:  Z^total = Z + D · U^imp.

    El libro ya no publica la matriz total —todo lo que entrega se deriva de la Z
    doméstica— pero las tres piezas siguen estando y la identidad es exacta
    (7,3e-12 medido en Colombia 2019 sobre los valores del pipeline). Acá se
    rehace desde las celdas del archivo, redondeadas a 6 decimales, así que el
    producto acumula redondeo: contra la hoja total que el libro traía antes, el
    multiplicador reconstruido difiere hasta 2,2e-04. Es dos órdenes por debajo
    de las diferencias que este reporte mide (1-5 %).

    En los libros oficiales de INEGI no hay
    matriz `D` porque no hay transformación nuestra: ahí la hoja de importado es
    la matriz M publicada, ya industria × industria, y la total es Z + M.
    """
    ind = list(Z_dom.index)
    U_imp = matriz_rect(grilla(f, r"SUT importado|U importada")[0])
    try:
        D = matriz_rect(grilla(f, r"D participaciones")[0])
    except KeyError:
        extra = U_imp.reindex(index=ind, columns=ind).fillna(0.0)
    else:
        prods = [p for p in D.columns if p in set(U_imp.index)]
        if not prods:
            raise KeyError("D y U^imp no comparten códigos de producto")
        extra = pd.DataFrame(
            D.reindex(columns=prods).to_numpy() @ U_imp.reindex(index=prods).to_numpy(),
            index=D.index, columns=U_imp.columns).reindex(
                index=ind, columns=ind).fillna(0.0)
    return Z_dom + extra


def l_nueva(f: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """(L doméstica publicada, L total reconstruida, nombres de industria)."""
    g_dom, _ = grilla(f, r"Leontief$")
    L_dom = matriz(g_dom)

    g_mip, _ = grilla(f, r"MIP completa")
    Z_dom = matriz(g_mip)
    cod = list(Z_dom.index)
    try:
        g_prod = columna_por_rotulo(g_mip, "Producción total", cod)
    except KeyError:
        g_prod = fila_por_rotulo(g_mip, "Producción total", cod)
    L_tot = leontief(z_total(f, Z_dom), g_prod)
    return L_dom, L_tot, nombres(g_dom)


# ── métricas ─────────────────────────────────────────────────────────────────

def comparar(L_viejo: pd.DataFrame, L_nuevo: pd.DataFrame) -> dict:
    comun = [c for c in L_viejo.index if c in set(L_nuevo.index)]
    V = L_viejo.loc[comun, comun].to_numpy()
    N = L_nuevo.loc[comun, comun].to_numpy()
    dif = N - V
    # el multiplicador se informa sobre la matriz COMPLETA de cada versión: es la
    # cifra que cada paquete publica. La correlación y el desvío, sobre la común.
    mv, mn = L_viejo.to_numpy().sum(0).mean(), L_nuevo.to_numpy().sum(0).mean()
    fuera = np.abs(dif[~np.eye(len(comun), dtype=bool)])
    return {
        "n_comun": len(comun),
        "mult_viejo": mv,
        "mult_nuevo": mn,
        "dif_mult_%": 100 * (mn - mv) / mv if mv else np.nan,
        "corr": float(np.corrcoef(V.ravel(), N.ravel())[0, 1]),
        "mae_fuera_diag": float(fuera.mean()),
        "max_dif": float(np.abs(dif).max()),
        "diag_viejo": float(np.diag(V).mean()),
        "diag_nuevo": float(np.diag(N).mean()),
        "_comun": comun,
        "_mult_v": pd.Series(V.sum(0), index=comun),
        "_mult_n": pd.Series(N.sum(0), index=comun),
    }


def pares() -> list[tuple[str, int, Path, Path, str]]:
    """(país, año, libro viejo, libro nuevo, variante) para los años que existen en ambos."""
    out = []
    for fv in sorted(VIEJO.glob("*/MIP_*_auditable.xlsx")):
        pais, anio = fv.stem.split("_")[1], int(fv.stem.split("_")[2])
        rec = NUEVO / pais / f"MIP_{pais}_{anio}_LIBRO.xlsx"
        ofi = NUEVO / pais / f"MIP_{pais}_{anio}_LIBRO_OFICIAL.xlsx"
        if rec.exists():
            out.append((pais, anio, fv, rec, "reconstruida"))
        elif ofi.exists():
            out.append((pais, anio, fv, ofi, "oficial"))
    return out


def main() -> int:
    filas, detalle = [], {}
    for pais, anio, fv, fn, variante in pares():
        print(f"  {pais} {anio} ({variante})…", flush=True)
        Lv = l_vieja(fv)
        Ld, Lt, noms = l_nueva(fn)
        a = comparar(Lv, Lt)   # carril A: total vs total
        b = comparar(Lv, Ld)   # carril B: publicado vs publicado
        filas.append({
            "pais": pais, "anio": anio, "variante": variante,
            "n_viejo": len(Lv), "n_nuevo": len(Ld), "n_comun": a["n_comun"],
            "mult_viejo_total": a["mult_viejo"],
            "mult_nuevo_total": a["mult_nuevo"],
            "dif_total_%": a["dif_mult_%"],
            "corr_total": a["corr"], "mae_total": a["mae_fuera_diag"],
            "mult_nuevo_domestica": b["mult_nuevo"],
            "dif_publicado_%": b["dif_mult_%"],
            "corr_publicado": b["corr"],
            "diag_viejo": a["diag_viejo"], "diag_nuevo_total": a["diag_nuevo"],
        })
        if (pais, anio) in FOCO:
            d = (a["_mult_n"] - a["_mult_v"]).sort_values()
            detalle[(pais, anio)] = [
                (c, noms.get(c, c), a["_mult_v"][c], a["_mult_n"][c]) for c in
                list(d.index[:5]) + list(d.index[-5:])
            ]

    df = pd.DataFrame(filas).sort_values(["pais", "anio"])
    SALIDA_CSV.parent.mkdir(exist_ok=True)
    df.to_csv(SALIDA_CSV, index=False, float_format="%.6f")
    escribir_md(df, detalle)
    print(f"\n{len(df)} pares comparados → {SALIDA_MD.relative_to(RAIZ)}")
    return 0


def escribir_md(df: pd.DataFrame, detalle: dict) -> None:
    f = lambda v, n=4: ("—" if pd.isna(v) else f"{v:,.{n}f}".replace(",", " ").replace(".", ","))
    L = []
    ap = L.append
    ap("# Coeficientes de Leontief: versión anterior vs. actual\n")
    ap("Comparación por país y año entre los libros `_auditable.xlsx` de "
       "`matrices-mip/` (la versión anterior del repositorio) y los `_LIBRO.xlsx` "
       "actuales. Generado por `scripts/comparar_versiones.py`.\n")
    ap("## Qué se está comparando\n")
    ap("Las dos versiones **no publican el mismo objeto**, así que hay dos carriles:\n")
    ap("- El **`Cuadro 8` viejo es la Leontief de la matriz TOTAL** (nacional + "
       "importada). Verificado: recalcular `(I−A)⁻¹` desde el `Cuadro 7` con "
       "`x = Σcolumna + valor agregado` lo reproduce con diferencia máxima "
       "**0,00000**; desde el `Cuadro 5` (nacional) no.\n")
    ap("- El **libro actual publica SÓLO la DOMÉSTICA** (hoja «Leontief»), con el insumo "
       "importado en fila primaria. La total no se entrega: para este carril se "
       "reconstruye desde el propio libro con `Z^total = Z + D·U^imp`.\n")
    ap("**Carril A** compara total contra total —misma definición, así que la "
       "diferencia es método y datos—. **Carril B** compara lo que cada paquete "
       "publica en su portada, que es lo que ve quien baje los dos.\n")
    ap("## Carril A — misma definición (total vs. total)\n")
    ap("| País | Año | n viejo | n nuevo | n común | Mult. medio viejo | "
       "Mult. medio nuevo | Dif. | Corr. celda a celda | MAE fuera de diagonal |")
    ap("|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for _, r in df.iterrows():
        ap(f"| {r.pais} | {r.anio} | {r.n_viejo} | {r.n_nuevo} | {r.n_comun} | "
           f"{f(r.mult_viejo_total)} | {f(r.mult_nuevo_total)} | "
           f"{f(r['dif_total_%'], 2)} % | {f(r.corr_total)} | {f(r.mae_total)} |")
    ap("\n## Carril B — lo publicado antes vs. lo publicado ahora\n")
    ap("El viejo es total; el nuevo, doméstico. La brecha de esta tabla es "
       "**mayoritariamente de definición**, no de error: la matriz total incluye "
       "las rondas de producción que ocurren fuera del país.\n")
    ap("| País | Año | Mult. medio publicado antes | Mult. medio publicado ahora | "
       "Dif. | Corr. celda a celda |")
    ap("|:--|--:|--:|--:|--:|--:|")
    for _, r in df.iterrows():
        ap(f"| {r.pais} | {r.anio} | {f(r.mult_viejo_total)} | "
           f"{f(r.mult_nuevo_domestica)} | {f(r['dif_publicado_%'], 2)} % | "
           f"{f(r.corr_publicado)} |")
    if detalle:
        ap("\n## Detalle sectorial (carril A)\n")
        ap("Las cinco industrias que más bajan y las cinco que más suben, por "
           "multiplicador de producción.\n")
        for (pais, anio), items in sorted(detalle.items()):
            ap(f"\n### {pais} {anio}\n")
            ap("| Código | Industria | Viejo | Nuevo | Dif. |")
            ap("|:--|:--|--:|--:|--:|")
            for cod, nom, mv, mn in items:
                ap(f"| {cod} | {nom[:52]} | {f(mv)} | {f(mn)} | {f(mn - mv, 4)} |")
    ap("\n## Advertencias\n")
    ap("- Cuando `n común < n`, las clasificaciones no coinciden: en Brasil 2010 y "
       "2015 el libro nuevo es **nível 67** (viene de la MIP del IBGE, que trae el "
       "corte importado medido) y el viejo **nível 68**. Parte de la diferencia es "
       "de agregación.\n")
    ap("- El multiplicador medio de cada versión se calcula sobre su matriz "
       "**completa**, que es la cifra que cada paquete publica; la correlación y el "
       "MAE, sobre la submatriz de códigos comunes.\n")
    ap("- México 2008 no tiene libro reconstruido nuevo: el contraste es contra el "
       "**libro oficial de INEGI**, así que ahí la columna «nuevo» es el dato del "
       "instituto, no una reconstrucción.\n")
    SALIDA_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
