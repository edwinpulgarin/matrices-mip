"""
Parser del COU de Brasil (IBGE, nível 68), archivos por año:
    68_tab1_AAAA.xls  (Recursos)  — hojas: oferta, producao, importacao
    68_tab2_AAAA.xls  (Usos)      — hojas: CI, demanda, VA, ...

Mapeo a la estructura canónica:
    producao  -> V  (producto × industria, precios básicos)
    CI        -> U  (producto × industria, precios de consumidor)
    demanda   -> Y  (producto × componentes de demanda final)
    VA (fila 'Valor adicionado bruto') -> VA agregado por industria
    oferta    -> puente de valoración por producto (márgenes, impuestos, OPC)
    importacao-> importaciones por producto

Unidad IBGE: millones de reales corrientes.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


def _n(x):
    """Normaliza a texto. Los nulos devuelven '' a propósito: `str(nan)` es
    'nan', que es no-vacío y no empieza con 'total', así que una fila o columna
    final toda-NaN se colaba como un producto fantasma 'nan' (todo en ceros,
    inocuo en los agregados pero que inflaba el conteo de productos y dejaba
    filas sin etiqueta). Mismo blindaje que `_industry_cols` en argentina.py."""
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(x)).strip()


def _num(df):
    return df.apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()


def _split(texto):
    """'0191 Agricultura...' -> ('0191', 'Agricultura...')."""
    t = _n(texto)
    m = re.match(r"^(\S+)\s+(.*)$", t)
    return (m.group(1), m.group(2)) if m else (t, t)


def _is_total(s):
    return _n(s).lower().startswith("total")


def parse(carpeta: str | Path, anio: int, verbose: bool = False) -> dict:
    carpeta = Path(carpeta)
    f1 = carpeta / f"68_tab1_{anio}.xls"
    f2 = carpeta / f"68_tab2_{anio}.xls"

    prod = pd.read_excel(f1, sheet_name="producao", header=None)
    ofer = pd.read_excel(f1, sheet_name="oferta", header=None)
    impo = pd.read_excel(f1, sheet_name="importacao", header=None)
    ci = pd.read_excel(f2, sheet_name="CI", header=None)
    dem = pd.read_excel(f2, sheet_name="demanda", header=None)
    va = pd.read_excel(f2, sheet_name="VA", header=None)

    HR = 3          # fila de encabezado de industria
    R0 = 5          # primera fila de producto

    # ── industrias (de producao, columnas c2.. sin 'Total') ────────────────
    ind_cols, ind_code, ind_name = [], {}, {}
    for c in range(2, prod.shape[1]):
        h = _n(prod.iloc[HR, c])
        if not h or _is_total(h):
            continue
        code, name = _split(h)
        ind_cols.append(c); ind_code[code] = code; ind_name[code] = name
    ind_keys = [_split(_n(prod.iloc[HR, c]))[0] for c in ind_cols]

    # ── productos (filas R0.. sin 'Total') ─────────────────────────────────
    prod_rows = [r for r in range(R0, prod.shape[0])
                 if _n(prod.iloc[r, 0]) and not _is_total(prod.iloc[r, 0])]
    prod_keys = [_n(prod.iloc[r, 0]) for r in prod_rows]
    prod_code = {k: k for k in prod_keys}
    prod_name = {_n(prod.iloc[r, 0]): _n(prod.iloc[r, 1]) for r in prod_rows}

    def matrix(df, rows, cols):
        return pd.DataFrame(_num(df.iloc[rows, cols]), index=prod_keys, columns=ind_keys)

    V_pi = matrix(prod, prod_rows, ind_cols)                       # prod × ind (básicos)

    # CI: mismas filas/columnas (asumimos misma estructura IBGE)
    ci_rows = [r for r in range(R0, ci.shape[0])
               if _n(ci.iloc[r, 0]) and not _is_total(ci.iloc[r, 0])]
    ci_cols = [c for c in range(2, ci.shape[1]) if not _is_total(ci.iloc[HR, c])]
    U_pc = pd.DataFrame(_num(ci.iloc[ci_rows, ci_cols]),
                        index=[_n(ci.iloc[r, 0]) for r in ci_rows],
                        columns=[_split(_n(ci.iloc[HR, c]))[0] for c in ci_cols])
    U_pc = U_pc.reindex(index=prod_keys, columns=ind_keys).fillna(0.0)

    # demanda final (columnas sin 'Demanda final'/'Demanda total')
    dem_rows = [r for r in range(R0, dem.shape[0])
                if _n(dem.iloc[r, 0]) and not _is_total(dem.iloc[r, 0])]
    fd_cols, fd_names = [], []
    for c in range(2, dem.shape[1]):
        h = _n(dem.iloc[HR, c])
        if not h or h.lower().startswith(("demanda final", "demanda total")):
            continue
        fd_cols.append(c); fd_names.append(h)
    Y_pc = pd.DataFrame(_num(dem.iloc[dem_rows, fd_cols]),
                        index=[_n(dem.iloc[r, 0]) for r in dem_rows], columns=fd_names)
    Y_pc = Y_pc.reindex(index=prod_keys).fillna(0.0)

    # valor agregado bruto (fila 'Valor adicionado bruto')
    vab_row = next(r for r in range(va.shape[0])
                   if "valor adicionado bruto" in _n(va.iloc[r, 0]).lower())
    # las industrias en la hoja VA empiezan en col 1 (una sola columna de etiqueta):
    # detectar por encabezado que empieza en dígito
    va_cols = [c for c in range(1, va.shape[1])
               if re.match(r"^\d", _n(va.iloc[HR, c])) and not _is_total(va.iloc[HR, c])]
    VA = pd.DataFrame(_num(va.iloc[[vab_row], va_cols]),
                      index=["valor_agregado_bruto"],
                      columns=[_split(_n(va.iloc[HR, c]))[0] for c in va_cols])
    VA = VA.reindex(columns=ind_keys).fillna(0.0)

    # ── puente de valoración por producto (de 'oferta') ────────────────────
    of_rows = [r for r in range(R0, ofer.shape[0])
               if _n(ofer.iloc[r, 0]) and not _is_total(ofer.iloc[r, 0])]
    ofk = [_n(ofer.iloc[r, 0]) for r in of_rows]

    def ocol(c):
        return pd.Series(_num(ofer.iloc[of_rows, [c]]).ravel(), index=ofk)

    OPC = ocol(2); MgC = ocol(3); MgT = ocol(4); DI = ocol(5)
    IPI = ocol(6); ICMS = ocol(7); OUTROS = ocol(8)
    # importaciones por producto (col con valores; importacao tiene [cod, desc, valor])
    imp_rows = [r for r in range(R0, impo.shape[0])
                if _n(impo.iloc[r, 0]) and not _is_total(impo.iloc[r, 0])]
    IMPO = pd.Series(_num(impo.iloc[imp_rows, [impo.shape[1] - 1]]).ravel(),
                     index=[_n(impo.iloc[r, 0]) for r in imp_rows])
    IMPO = IMPO.groupby(level=0).sum().reindex(ofk).fillna(0.0)

    OPB_dom = V_pi.sum(axis=1).reindex(ofk).fillna(0.0)            # producción doméstica básica
    val = pd.DataFrame({
        "OPB": OPB_dom, "IMPO": IMPO, "Ajuste": 0.0,
        "DI": DI, "IP": IPI + ICMS + OUTROS, "IVA": 0.0, "Comisiones": 0.0,
        "Mg": MgC + MgT, "OPC": OPC,
    }).reindex(index=prod_keys).fillna(0.0)

    if verbose:
        print(f"  [BR {anio}] prod={len(prod_keys)} ind={len(ind_keys)}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "Y_pc": Y_pc, "val": val, "VA": VA,
        "prod_labels": {k: f"{prod_code[k]} - {prod_name[k]}" for k in prod_keys},
        "ind_labels": {k: f"{ind_code[k]} - {ind_name[k]}" for k in ind_keys},
        "ind_code": ind_code, "ind_name": ind_name,
        "prod_code": prod_code, "prod_name": prod_name,
        "pais": "Brasil", "anio": anio, "unidad": "millones de reales corrientes",
    }
