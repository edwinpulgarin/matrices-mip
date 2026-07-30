"""
Parser de la MIP del IBGE (Brasil) — versión SIN PRORRATEO.

El COU anual del IBGE (`68_tab1/tab2`, que usa `parsers/brasil.py`) sólo publica
importaciones, impuestos y márgenes POR PRODUCTO, así que para llegar a precios
básicos y separar el origen hay que prorratear. La publicación de la **Matriz de
Insumo-Produto**, en cambio, trae todo medido celda a celda — pero sólo para
**2010 y 2015**, y a nivel 67 (no 68).

    data/raw/brasil/MIP_IBGE_2010_Nivel_67.xls
    data/raw/brasil/MIP_IBGE_2015_Nivel_67.xls
    (ftp.ibge.gov.br/Contas_Nacionais/Matriz_de_Insumo_Produto/{2010,2015}/)

Hojas usadas (todas comparten el mismo layout de columnas):

    01  Recursos            c7..c73  producción por actividad  -> V
    03  Producción NACIONAL c3..c69  consumo intermedio        -> U_dom
                            c71..c76 demanda final             -> Y_dom
    04  Productos IMPORTADOS c3..c69 consumo intermedio        -> U_imp
    05  Destino de los impuestos sobre productos nacionales  ┐
    06  Destino de los impuestos sobre productos importados  │  suma por actividad
    07  Destino del margen de comercio, nacionales           ├─> impuestos y
    08  Destino del margen de comercio, importados           │   márgenes por
    09  Destino del margen de transporte, nacionales         │   industria
    10  Destino del margen de transporte, importados         ┘

Las tablas 05 a 10 son la razón por la que estos dos años salen completamente
limpios: el IBGE publica a qué celda va a parar cada impuesto y cada margen, así
que tampoco hace falta el prorrateo del Cap. 7.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

HR_GRUPO = 2         # fila del encabezado de grupo
HR_DET = 3           # fila del encabezado de detalle (código + nombre)
R0 = 5               # primera fila de producto

C_IND0 = 3           # primera actividad en las tablas 03-10 (c2 es 'Recursos')
N_IND = 67
C_V0, C_V1 = 7, 74   # bloque de producción por actividad en la tabla 01
C_FD0 = 71           # primera columna de demanda final en las tablas 03-10
C_FD1 = 77           # exclusivo: c77 es 'Demanda final' (total)

_HOJAS_CUNA = ("05", "06", "07", "08", "09", "10")


def _n(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(x)).strip()


def _split(texto: str) -> tuple[str, str]:
    """'0191 Agricultura, inclusive...' -> ('0191', 'Agricultura, inclusive...')."""
    t = _n(texto)
    m = re.match(r"^(\S+)\s+(.*)$", t)
    return (m.group(1), m.group(2)) if m else (t, t)


def _num(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(pd.to_numeric, errors="coerce").fillna(0.0)


def _filas_producto(d: pd.DataFrame) -> list[int]:
    return [r for r in range(R0, d.shape[0]) if re.match(r"^\d{5}$", _n(d.iat[r, 0]))]


def parse(carpeta: str | Path, anio: int = 2015, verbose: bool = False) -> dict:
    carpeta = Path(carpeta)
    f = carpeta / f"MIP_IBGE_{anio}_Nivel_67.xls"
    if not f.exists():
        raise FileNotFoundError(f)
    xl = pd.ExcelFile(f)
    hoja = lambda h: xl.parse(h, header=None)

    t01, t03, t04 = hoja("01"), hoja("03"), hoja("04")

    rows = _filas_producto(t03)
    prod_keys = [_n(t03.iat[r, 0]) for r in rows]
    prod_name = {k: _n(t03.iat[r, 1]) for k, r in zip(prod_keys, rows)}
    prod_code = {k: k for k in prod_keys}

    ind_cols = list(range(C_IND0, C_IND0 + N_IND))
    ind_keys, ind_code, ind_name = [], {}, {}
    for c in ind_cols:
        cod, nom = _split(t03.iat[HR_DET, c])
        while cod in ind_code:
            cod += "'"
        ind_keys.append(cod); ind_code[cod] = cod; ind_name[cod] = nom

    # las actividades de la tabla 01 deben ser las mismas y en el mismo orden
    v_cols = list(range(C_V0, C_V1))
    if len(v_cols) != N_IND:
        raise ValueError(f"tabla 01: esperaba {N_IND} actividades, hay {len(v_cols)}")
    v_keys = [_split(t01.iat[HR_DET, c])[0] for c in v_cols]
    if v_keys != ind_keys:
        raise ValueError("las actividades de la tabla 01 no coinciden con las de la 03")

    def bloque(d, cols, rr=None):
        rr = rr if rr is not None else _filas_producto(d)
        return pd.DataFrame(_num(d.iloc[rr, cols]).to_numpy(),
                            index=[_n(d.iat[r, 0]) for r in rr],
                            columns=ind_keys).reindex(index=prod_keys).fillna(0.0)

    U_dom = bloque(t03, ind_cols, rows)
    U_imp = bloque(t04, ind_cols)
    V_pi = bloque(t01, v_cols)

    # demanda final doméstica (la importada va en la tabla 04, no se usa acá)
    fd_cols, fd_names = [], []
    for c in range(C_FD0, C_FD1):
        det = _n(t03.iat[HR_DET, c]) or _n(t03.iat[HR_GRUPO, c])
        if not det:
            continue
        fd_cols.append(c); fd_names.append(det)
    Y_dom = pd.DataFrame(_num(t03.iloc[rows, fd_cols]).to_numpy(),
                         index=prod_keys, columns=fd_names)

    # ── cuña de impuestos y márgenes: MEDIDA celda a celda ────────────────
    # Las tablas 05-10 dan a qué celda va a parar cada impuesto y cada margen,
    # sobre productos nacionales e importados. Sumadas dan la cuña completa.
    cuna = pd.DataFrame(0.0, index=prod_keys, columns=ind_keys)
    for h in _HOJAS_CUNA:
        cuna = cuna + bloque(hoja(h), ind_cols)
    imptax_j = cuna.sum(axis=0)

    # Consumo intermedio a PRECIOS DE COMPRADOR, para la hoja de auditoría COU:
    # básico doméstico + básico importado + cuña. Sin la cuña, la auditoría
    # compara precios básicos contra precios de comprador y descuadra ~16 %.
    U_pc = U_dom + U_imp + cuna

    if verbose:
        print(f"  [BR-MIP {anio}] prod={len(prod_keys)} ind={len(ind_keys)} "
              f"fd={len(fd_names)} U_dom={U_dom.to_numpy().sum():,.0f} "
              f"U_imp={U_imp.to_numpy().sum():,.0f} cuña={imptax_j.sum():,.0f}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "U_dom": U_dom, "U_imp": U_imp, "Y_dom": Y_dom,
        "imptax_j": imptax_j,
        "prod_labels": {k: f"{k} - {prod_name[k]}" for k in prod_keys},
        "ind_labels": {k: f"{k} - {ind_name[k]}" for k in ind_keys},
        "ind_code": ind_code, "ind_name": ind_name,
        "prod_code": prod_code, "prod_name": prod_name,
        "pais": "Brasil", "anio": anio,
        "unidad": "millones de reales corrientes",
    }
