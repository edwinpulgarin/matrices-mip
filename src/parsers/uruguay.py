"""
Parser del COU de Uruguay (BCU), formato detallado con oferta y utilización
APILADAS en una misma hoja ('AAAA CORRIENTE'):

    Bloque OFERTA (arriba):  productos × industrias (producción, precios básicos)
        + columnas: Oferta Total, Producción Total, Oferta Importada,
          Márgenes Totales, Impuestos s/ productos, Ajuste CIF/FOB.
    Bloque USO (abajo):      productos × industrias (utilización) + demanda final
          (Consumo hogares, gobierno, FBKF, variación existencias, exportaciones)
        + filas de valor agregado al final (VAB en 'Valor agregado bruto').

Devuelve la estructura canónica. Unidad: millones de pesos uruguayos corrientes.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


def _n(x):
    return re.sub(r"\s+", " ", str(x)).strip()


def _num(df):
    return df.apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()


def _is_ind(h):
    return bool(re.match(r"^[A-Z]+\.\d+$", _n(h)))


def _find_row(df, col, kw, r0=0, r1=None):
    r1 = r1 or df.shape[0]
    for r in range(r0, r1):
        if kw.lower() in _n(df.iat[r, col]).lower():
            return r
    return None


def _prod_rows(df, r0, r1):
    """Filas cuyo col0 es un código numérico (productos)."""
    return [r for r in range(r0, r1) if re.match(r"^\d+$", _n(df.iat[r, 0]))]


def _block_end(df, r0, r1):
    """Fin del bloque de productos: primera fila 'Sub Total'/'Total'."""
    for r in range(r0, r1):
        if _n(df.iat[r, 1]).lower().startswith(("sub total", "subtotal", "total")):
            return r
    return r1


def _clasif_actividades(ruta: str | Path) -> dict:
    """Mapa código→nombre de industria desde la hoja 'Clasificación_Actividades'.

    Los COU del BCU no traen el nombre de la industria junto al código en la hoja
    de oferta/utilización: están en una hoja aparte, código (col 0) → descripción
    (col 1). Sin esto las industrias quedan etiquetadas solo con el código.
    """
    xl = pd.ExcelFile(ruta)
    hojas = [h for h in xl.sheet_names if "clasific" in _n(h).lower()]
    if not hojas:
        return {}
    cl = pd.read_excel(ruta, sheet_name=hojas[0], header=None)
    # La descripción puede estar en col 1 (2012) o col 2 (2016/2017): se toma
    # la primera celda de texto no vacía a la derecha del código.
    out = {}
    for r in range(cl.shape[0]):
        if not _is_ind(cl.iat[r, 0]):
            continue
        cod = _n(cl.iat[r, 0])
        desc = next((_n(cl.iat[r, c]) for c in range(1, cl.shape[1])
                     if _n(cl.iat[r, c]) not in ("", "nan")), cod)
        out[cod] = desc
    return out


def parse(ruta: str | Path, anio: int, hoja: str | None = None, verbose: bool = False) -> dict:
    ruta = str(ruta)
    if hoja is None:
        hoja = f"{anio} CORRIENTE"
    df = pd.read_excel(ruta, sheet_name=hoja, header=None)

    hr_of = _find_row(df, 6, "Oferta Total", 0, 20)
    hr_us = _find_row(df, 6, "Utilización Total", hr_of + 1, df.shape[0])
    va_row = _find_row(df, 1, "Valor agregado bruto", hr_us, df.shape[0])

    ind_cols = [c for c in range(2, df.shape[1]) if _is_ind(df.iat[hr_of, c])]
    ind_keys = [_n(df.iat[hr_of, c]) for c in ind_cols]

    # columnas de valoración (bloque oferta) y demanda final (bloque uso), por keyword
    def col_kw(hr, kw):
        for c in range(2, df.shape[1]):
            if kw.lower() in _n(df.iat[hr, c]).lower():
                return c
        return None

    c_prodtot = col_kw(hr_of, "Producción Total")
    c_impo = col_kw(hr_of, "Oferta Importada")
    c_marg = col_kw(hr_of, "Márgenes")
    c_imp = col_kw(hr_of, "Impuestos menos subvenciones sobre los produc")
    c_ajuste = col_kw(hr_of, "Ajuste Cif")
    c_opc = col_kw(hr_of, "Oferta Total")
    fd_cols, fd_names = [], []
    for c in range(2, df.shape[1]):
        h = _n(df.iat[hr_us, c])
        if any(k in h.lower() for k in ["gasto de consumo", "formación bruta",
                                        "variación de existencias", "exportaciones"]):
            fd_cols.append(c); fd_names.append(h)

    of_rows = _prod_rows(df, hr_of + 1, _block_end(df, hr_of + 1, hr_us))
    us_rows = _prod_rows(df, hr_us + 1, _block_end(df, hr_us + 1, va_row))
    of_codes0 = [_n(df.iat[r, 0]) for r in of_rows]   # con posibles duplicados
    of_codes = of_codes0
    us_codes = [_n(df.iat[r, 0]) for r in us_rows]

    V_pi = pd.DataFrame(_num(df.iloc[of_rows, ind_cols]), index=of_codes, columns=ind_keys).groupby(level=0).sum()
    of_codes = list(V_pi.index)
    U_pc = pd.DataFrame(_num(df.iloc[us_rows, ind_cols]), index=us_codes, columns=ind_keys).groupby(level=0).sum()
    U_pc = U_pc.reindex(index=of_codes).fillna(0.0)
    Y_pc = pd.DataFrame(_num(df.iloc[us_rows, fd_cols]), index=us_codes, columns=fd_names).groupby(level=0).sum()
    Y_pc = Y_pc.reindex(index=of_codes).fillna(0.0)

    # VAB por identidad: producción por industria − consumo intermedio por industria
    # (robusto; evita filas de VA numeradas que ensucian la lectura directa).
    VA = pd.DataFrame([(V_pi.sum(axis=0) - U_pc.sum(axis=0)).reindex(ind_keys).fillna(0.0).to_numpy()],
                      index=["valor_agregado_bruto"], columns=ind_keys)

    def ocol(c):
        s = (pd.Series(_num(df.iloc[of_rows, [c]]).ravel(), index=of_codes0)
             if c else pd.Series(0.0, index=of_codes0))
        return s.groupby(level=0).sum().reindex(of_codes).fillna(0.0)

    val = pd.DataFrame({
        "OPB": V_pi.sum(axis=1), "IMPO": ocol(c_impo), "Ajuste": ocol(c_ajuste),
        "DI": 0.0, "IP": ocol(c_imp), "IVA": 0.0, "Comisiones": 0.0,
        "Mg": ocol(c_marg), "OPC": ocol(c_opc),
    }).reindex(index=of_codes).fillna(0.0)

    prod_code = {k: k for k in of_codes}
    prod_name = {_n(df.iat[r, 0]): _n(df.iat[r, 1]) for r in of_rows}
    ind_code = {k: k for k in ind_keys}
    # El nombre de la industria vive en la hoja 'Clasificación_Actividades', no
    # junto al código en la hoja de oferta/utilización.
    clasif = _clasif_actividades(ruta)
    ind_name = {k: clasif.get(k, k) for k in ind_keys}

    if verbose:
        print(f"  [UY {anio}] prod={len(of_codes)} ind={len(ind_keys)} fd={fd_names}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "Y_pc": Y_pc, "val": val, "VA": VA,
        "prod_labels": {k: f"{k} - {prod_name.get(k, k)}" for k in of_codes},
        "ind_labels": {k: f"{k} - {ind_name.get(k, k)}" for k in ind_keys},
        "ind_code": ind_code, "ind_name": ind_name,
        "prod_code": prod_code, "prod_name": prod_name,
        "pais": "Uruguay", "anio": anio, "unidad": "millones de pesos uruguayos corrientes",
    }
