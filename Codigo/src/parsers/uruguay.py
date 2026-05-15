"""
Parser de los Cuadros de Oferta y Utilización (COU) de Uruguay — BCU/INE.

Estructura:
    - 95 actividades, 110 productos (año base 2016)
    - Años disponibles: 2012–2017
    - Unidad: millones de pesos uruguayos corrientes (UYU)

Fuente: BCU — https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Cuentas-Nacionales.aspx
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from .base import COU, limpiar_nombre, coerce_numeric_df


HOJAS_OFERTA = ['Cuadro de Oferta', 'Oferta', 'CO', 'oferta',
                'Tabla Oferta', 'OFERTA', 'Supply']
HOJAS_UTIL   = ['Cuadro de Utilización', 'Utilizacion', 'Utilización', 'CU',
                'utilizacion', 'Tabla Utilización', 'UTILIZACION', 'Use']


def _encontrar_hoja(xls, candidatos):
    hojas = {h.lower().strip(): h for h in xls.sheet_names}
    for c in candidatos:
        if c.lower() in hojas:
            return hojas[c.lower()]
    for c in candidatos:
        for h_low, h_orig in hojas.items():
            if c.lower()[:5] in h_low:
                return h_orig
    return None


def _es_numero(s) -> bool:
    try:
        float(str(s).replace(',', '.').replace(' ', '').replace('\xa0', ''))
        return True
    except (ValueError, TypeError):
        return False


def _hallar_encabezado(df, min_texto=3):
    for i in range(min(30, len(df))):
        n_txt = sum(1 for v in df.iloc[i]
                    if str(v).strip() not in ('', 'nan', 'None') and not _es_numero(v))
        if n_txt >= min_texto:
            return i
    return 0


def _hallar_col_etiq(df, fila_enc):
    for j in range(min(5, len(df.columns))):
        v = str(df.iloc[fila_enc, j]).strip()
        if v not in ('', 'nan', 'None') and not _es_numero(v):
            return j
    return 0


def _hallar_fin_prod(df, fila_dat, col_etiq):
    for i in range(fila_dat, len(df)):
        etiq = str(df.iloc[i, col_etiq]).strip().lower()
        if any(k in etiq for k in ['valor agreg', 'remuner', 'excedente', 'ingreso mixto',
                                    'impuesto', 'consumo de capital', 'total']):
            if i > fila_dat + 5:
                return i
    return len(df)


def parsear(ruta: Path, anio: int, verbose: bool = False) -> COU:
    """
    Lee el COU de Uruguay y retorna un objeto COU.
    """
    if verbose:
        print(f"  Leyendo {ruta.name} ...")

    engine = 'xlrd' if ruta.suffix == '.xls' else 'openpyxl'
    xls = pd.ExcelFile(ruta, engine=engine)

    if verbose:
        print(f"  Hojas: {xls.sheet_names}")

    hoja_o = _encontrar_hoja(xls, HOJAS_OFERTA)
    hoja_u = _encontrar_hoja(xls, HOJAS_UTIL)

    if hoja_o is None or hoja_u is None:
        raise ValueError(
            f"No se encontraron hojas de oferta/utilización en {ruta.name}.\n"
            f"Hojas disponibles: {xls.sheet_names}"
        )

    df_o = pd.read_excel(xls, sheet_name=hoja_o, header=None, dtype=str)
    df_u = pd.read_excel(xls, sheet_name=hoja_u, header=None, dtype=str)

    return _parsear_bcu(df_o, df_u, anio, verbose)


def _parsear_bcu(df_o, df_u, anio, verbose):

    # ── Tabla de Oferta ───────────────────────────────────────────────────────
    enc_o = _hallar_encabezado(df_o)
    col_o = _hallar_col_etiq(df_o, enc_o)
    dat_o = enc_o + 1

    noms_act = []
    for j in range(col_o + 1, len(df_o.columns)):
        v = str(df_o.iloc[enc_o, j]).strip()
        if v in ('', 'nan', 'None'):
            if noms_act:
                break
            continue
        if not _es_numero(v):
            noms_act.append(limpiar_nombre(v))

    n_act = len(noms_act)

    noms_prod = []
    for i in range(dat_o, len(df_o)):
        etiq = str(df_o.iloc[i, col_o]).strip()
        if etiq in ('', 'nan', 'None') or _es_numero(etiq):
            break
        noms_prod.append(limpiar_nombre(etiq))

    n_prod = len(noms_prod)

    if verbose:
        print(f"  Oferta: {n_act} actividades, {n_prod} productos")

    V_raw = df_o.iloc[dat_o:dat_o + n_prod, col_o + 1:col_o + 1 + n_act]
    V = V_raw.apply(pd.to_numeric, errors='coerce').fillna(0)
    V.index   = noms_prod[:len(V)]
    V.columns = noms_act[:len(V.columns)]
    V = V.T

    M = None
    for j in range(col_o + 1 + n_act, min(col_o + 1 + n_act + 6, len(df_o.columns))):
        enc_txt = str(df_o.iloc[enc_o, j]).strip().lower()
        if 'import' in enc_txt:
            m_raw = df_o.iloc[dat_o:dat_o + n_prod, j]
            M = m_raw.apply(pd.to_numeric, errors='coerce').fillna(0)
            M.index = noms_prod[:len(M)]
            M.name  = 'importaciones'
            break

    # ── Tabla de Utilización ──────────────────────────────────────────────────
    enc_u = _hallar_encabezado(df_u)
    col_u = _hallar_col_etiq(df_u, enc_u)
    dat_u = enc_u + 1
    fin_u = _hallar_fin_prod(df_u, dat_u, col_u)

    noms_prod_u = []
    for i in range(dat_u, fin_u):
        etiq = str(df_u.iloc[i, col_u]).strip()
        if etiq in ('', 'nan', 'None') or _es_numero(etiq):
            continue
        noms_prod_u.append(limpiar_nombre(etiq))

    n_prod_u = len(noms_prod_u)

    U_raw = df_u.iloc[dat_u:dat_u + n_prod_u, col_u + 1:col_u + 1 + n_act]
    U = U_raw.apply(pd.to_numeric, errors='coerce').fillna(0)
    U.index   = noms_prod_u
    U.columns = noms_act[:len(U.columns)]

    fd_etiq, fd_cols = [], []
    for j in range(col_u + 1 + n_act, len(df_u.columns)):
        v = str(df_u.iloc[enc_u, j]).strip()
        if v in ('', 'nan', 'None'):
            if fd_etiq:
                break
            continue
        v_l = v.lower()
        if any(k in v_l for k in ['consumo priv', 'hogar', 'gobierno', 'fbkf',
                                    'formac', 'export', 'variacion', 'total']):
            fd_etiq.append(limpiar_nombre(v))
            fd_cols.append(j)

    if fd_cols:
        Y_raw = df_u.iloc[dat_u:dat_u + n_prod_u, fd_cols]
        Y = Y_raw.apply(pd.to_numeric, errors='coerce').fillna(0)
        Y.index   = noms_prod_u
        Y.columns = fd_etiq[:len(Y.columns)]
    else:
        Y = pd.DataFrame(0, index=noms_prod_u, columns=['demanda_final'])

    W_dict = {}
    for i in range(fin_u, min(fin_u + 15, len(df_u))):
        etiq = str(df_u.iloc[i, col_u]).strip()
        if etiq in ('', 'nan', 'None'):
            continue
        etiq_l = etiq.lower()
        if any(k in etiq_l for k in ['remuner', 'excedente', 'ingreso mixto',
                                      'impuesto', 'valor agr']):
            fila_va = df_u.iloc[i, col_u + 1:col_u + 1 + n_act]
            W_dict[limpiar_nombre(etiq)] = fila_va.apply(pd.to_numeric, errors='coerce').fillna(0).values

    if W_dict:
        W = pd.DataFrame(W_dict, index=noms_act[:n_act]).T
    else:
        W = pd.DataFrame({'valor_agregado': np.zeros(n_act)}, index=noms_act).T

    return COU(
        pais='uruguay',
        anio=anio,
        moneda='UYU',
        unidad='millones',
        V=V,
        U=U,
        Y=Y,
        W=W,
        M=M,
    )
