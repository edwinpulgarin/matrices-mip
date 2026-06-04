"""
Parser de los Cuadros de Oferta y Utilización (COU) de Argentina — INDEC.

El INDEC publica COUs directamente descargables desde el FTP:
    sh_cou_06_16.xls   → año 2004 (base 2004)
    sh_cou_08_21.xls   → año 2018 (base 2004, revisión agosto 2021)

Estructura detectada en ambos archivos:

COU 2004 (sh_cou_06_16.xls):
    Hoja 'Mat Oferta pb'      → V: products×activities (precios básicos)
      Fila 2: nombres de actividades
      Fila 3: códigos (11, 12, ..., 950)
      Filas 4-275: productos (col 0=desc, col 1=CPC, cols 2-163=actividades)
    Hoja 'Mat Utilizacion pc' → U: products×activities (precios comprador)
      Fila 3: códigos columnas (OPB, IMPO, ..., códigos actividades..., UI, CH, CP, EX, INV, VE, UF, DEMANDA)
      Filas 4-275: productos
      Fila 277: VAB, Fila 278: VBP

COU 2018 (sh_cou_08_21.xls):
    Hoja 'Mat_Of_pc_2018'     → V: products×activities (precios comprador)
      Fila 3: nombres actividades, Fila 4: códigos
      Filas 5-227: productos
    Hoja 'Mat_Ut_pc_2018'     → U: products×activities
      Fila 4: códigos (Descripción, CPC, 011/014, ..., UI, CH, CP, EX, ...)
      Filas 5-227: productos, Fila 229: VAB, Fila 230: VBP

Unidad: miles de ARS corrientes
"""

import re
import numpy as np
import pandas as pd
from pathlib import Path

from .base import COU


def _to_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(pd.to_numeric, errors='coerce').fillna(0)


def _limpiar(s) -> str:
    s = str(s).strip()
    if s in ('nan', 'None', ''):
        return ''
    # Quitar saltos de línea internos
    return re.sub(r'\s+', ' ', s).strip()


def _es_codigo_actividad(v) -> bool:
    """True si el valor parece un código CIIU/ISIC de actividad (número o combinación)."""
    s = str(v).strip()
    if s in ('nan', 'None', '', 'Descripción', 'CPC 1.1', 'Producto',
             'OPB', 'IMPO', 'Ajuste CIF/FOB', 'DI', 'IP', 'Mg C', 'Mg T',
             'IVA', 'OPC', 'UI', 'CH', 'CP', 'EX', 'INV', 'VE', 'UF', 'DEMANDA',
             'UTILIZACION INTERMEDIA', 'UTILIZACIÓN FINAL', 'DEMANDA TOTAL',
             'Fbc Fijo', 'OV', 'Productos terminados', 'Trabajos en curso'):
        return False
    # Es un código si es numérico o comienza con dígito (con posibles '/', letras sufijo)
    return bool(re.match(r'^\d', s))


def _identificar_cols_actividad(row: pd.Series) -> list[int]:
    """Devuelve los índices de columna que contienen códigos de actividad."""
    return [j for j, v in enumerate(row) if _es_codigo_actividad(v)]


def _identificar_cols_df(row: pd.Series, marcadores: list[str]) -> list[int]:
    """Devuelve índices de columnas cuyos valores están en marcadores (demanda final)."""
    return [j for j, v in enumerate(row)
            if str(v).strip() in marcadores or
            any(m in str(v).strip().upper() for m in marcadores)]


def _extraer_submatriz(df: pd.DataFrame, filas: list[int],
                       cols: list[int], etiq_filas: list[str],
                       etiq_cols: list[str]) -> pd.DataFrame:
    bloque = df.iloc[filas, :]
    bloque = bloque.iloc[:, cols]
    bloque = _to_numeric_df(bloque.copy())
    bloque.index = etiq_filas[:len(bloque)]
    bloque.columns = etiq_cols[:len(bloque.columns)]
    return bloque


def _label_actividad(codigo, nombre='') -> str:
    codigo = _limpiar(codigo)
    nombre = _limpiar(nombre)
    nombre = re.sub(r'\b\d{2,4}\s*[-–—]\s*', '', nombre).strip()
    if nombre:
        return f"{codigo} — {nombre}"
    return codigo


def _codigo_match(codigo) -> list[str]:
    """Variantes de codigo para empatar oferta y uso cuando cambia un cero final."""
    codigo = _limpiar(codigo)
    variantes = [codigo]
    if re.fullmatch(r'\d+0', codigo or ''):
        variantes.append(codigo[:-1])
    return variantes


def _serie_columna(df: pd.DataFrame, filas: list[int], col: int,
                   etiquetas: list[str], nombre: str) -> pd.Series:
    vals = pd.to_numeric(df.iloc[filas, col], errors='coerce').fillna(0)
    return pd.Series(vals.values, index=etiquetas[:len(vals)], name=nombre)


# ──────────────────────────────────────────────────────────────────────────────
# Parsers específicos por formato
# ──────────────────────────────────────────────────────────────────────────────

def _parsear_2004(xls: pd.ExcelFile, anio: int, verbose: bool) -> COU:
    """Formato: sh_cou_06_16.xls  (año 2004, base 2004)"""

    df_v = xls.parse('Mat Oferta pb', header=None)
    df_u = xls.parse('Mat Utilizacion pc', header=None)

    # ── V matrix ─────────────────────────────────────────────────────────────
    # Row 2: activity names, Row 3: codes, Rows 4-275: products
    row3_v = df_v.iloc[3]
    act_cols_v = _identificar_cols_actividad(row3_v)
    act_codes_v = [str(df_v.iloc[3, j]).strip() for j in act_cols_v]
    act_names_v = [str(df_v.iloc[2, j]).strip() for j in act_cols_v]
    act_labels_v = [_label_actividad(c, n) for c, n in zip(act_codes_v, act_names_v)]
    label_by_code = dict(zip(act_codes_v, act_labels_v))

    # Product rows: rows 4 to 275 (row 276 = Total)
    fila_total_v = next((i for i in range(4, len(df_v))
                         if str(df_v.iloc[i, 0]).strip().lower() == 'total'), 276)
    prod_rows_v = list(range(4, fila_total_v))
    prod_labels_v = []
    for i in prod_rows_v:
        etiq = _limpiar(df_v.iloc[i, 1])  # col 1 = CPC code
        if not etiq:
            etiq = _limpiar(df_v.iloc[i, 0])
        prod_labels_v.append(etiq)

    V_raw = _extraer_submatriz(df_v, prod_rows_v, act_cols_v,
                                prod_labels_v, act_labels_v)
    # V is (products × activities) → transpose to (activities × products)
    V = V_raw.T.copy()

    # ── U matrix ─────────────────────────────────────────────────────────────
    # Row 3: codes. Activity codes start at col 11, end before 'UI'
    row3_u = df_u.iloc[3]
    act_cols_u = _identificar_cols_actividad(row3_u)
    act_codes_u = [str(df_u.iloc[3, j]).strip() for j in act_cols_u]

    # Match U activity columns to V activity columns by code
    # Use codes as labels
    act_labels_u = [label_by_code.get(c, c) for c in act_codes_u]

    # Product rows in U: rows 4 to fila_total_u
    fila_total_u = next((i for i in range(4, len(df_u))
                         if str(df_u.iloc[i, 0]).strip().lower() == 'total'), 276)
    prod_rows_u = list(range(4, fila_total_u))
    prod_labels_u = []
    for i in prod_rows_u:
        etiq = _limpiar(df_u.iloc[i, 1])  # col 1 = CPC code
        if not etiq:
            etiq = _limpiar(df_u.iloc[i, 0])
        prod_labels_u.append(etiq)

    U_raw = _extraer_submatriz(df_u, prod_rows_u, act_cols_u,
                                prod_labels_u, act_labels_u)
    U = U_raw.copy()

    # ── Final demand Y ────────────────────────────────────────────────────────
    # Cols after 'UI': CH, CP, EX, INV, VE. UF is the aggregate final-use total,
    # not an additional component.
    FD_CODES = {'CH', 'CP', 'EX', 'INV', 'VE'}
    fd_cols = [j for j, v in enumerate(row3_u) if str(v).strip() in FD_CODES]
    fd_labels = [str(row3_u.iloc[j]).strip() for j in fd_cols]
    Y = _extraer_submatriz(df_u, prod_rows_u, fd_cols, prod_labels_u, fd_labels)

    demanda_col = next((j for j, v in enumerate(row3_u) if str(v).strip() == 'DEMANDA'), None)
    demanda_total_pc = _serie_columna(df_u, prod_rows_u, demanda_col, prod_labels_u,
                                      'demanda_total_pc') if demanda_col is not None else None

    # ── Imports M ─────────────────────────────────────────────────────────────
    # Col 3 in U = IMPO
    impo_col = next((j for j, v in enumerate(row3_u) if str(v).strip() == 'IMPO'), None)
    if impo_col is not None:
        M_raw = df_u.iloc[prod_rows_u, impo_col]
        M = pd.to_numeric(M_raw, errors='coerce').fillna(0)
        M.index = prod_labels_u[:len(M)]
        M.name = 'importaciones'
    else:
        M = pd.Series(0.0, index=prod_labels_u, name='importaciones')

    # ── Value added W ─────────────────────────────────────────────────────────
    # Row 277: VAB, Row 278: VBP
    fila_vab = next((i for i in range(fila_total_u, min(fila_total_u+10, len(df_u)))
                     if 'valor agregado' in str(df_u.iloc[i, 0]).lower()), None)
    if fila_vab is not None:
        W_row = df_u.iloc[fila_vab, act_cols_u]
        W = pd.to_numeric(W_row, errors='coerce').fillna(0)
        W.index = act_labels_u[:len(W)]
        W.name = 'valor_agregado_bruto'
    else:
        W = pd.Series(0.0, index=act_labels_u, name='valor_agregado_bruto')

    if verbose:
        print(f"  2004: V={V.shape}, U={U.shape}, Y={Y.shape}, "
              f"W={len(W)} act, M={len(M)} prod")

    cou = COU(pais='argentina', anio=anio, moneda='ARS', unidad='miles',
              V=V, U=U, Y=Y, W=W.to_frame().T, M=M)
    if demanda_total_pc is not None:
        q_dom = V.sum(axis=0).reindex(demanda_total_pc.index).fillna(0)
        cou.demanda_total_pc = demanda_total_pc
        cou.factor_domestico_pb = q_dom.div(demanda_total_pc.replace(0, np.nan)).fillna(0)
        cou.notas.append('Y fuente excluye UF porque UF es total de utilizacion final.')
        cou.notas.append('Factor domestico/precios basicos calculado como OPB/DEMANDA por producto.')
    return cou


def _parsear_2018(xls: pd.ExcelFile, anio: int, verbose: bool) -> COU:
    """Formato: sh_cou_08_21.xls — delega a _parsear_2018_gen."""
    hoja_v = next(s for s in xls.sheet_names if s.startswith('Mat_Of_pc_'))
    hoja_u = next(s for s in xls.sheet_names if s.startswith('Mat_Ut_pc_'))
    return _parsear_2018_gen(xls, hoja_v, hoja_u, anio, verbose)


def _parsear_2018_gen(xls: pd.ExcelFile, hoja_v: str, hoja_u: str,
                      anio: int, verbose: bool) -> COU:
    """Formato: Mat_Of_pc_YYYY / Mat_Ut_pc_YYYY  (años 2018-2021)"""

    df_v = xls.parse(hoja_v, header=None)
    df_u = xls.parse(hoja_u, header=None)

    # ── V matrix ─────────────────────────────────────────────────────────────
    # Row 3: names, Row 4: codes, Rows 5+ : products
    row4_v = df_v.iloc[4]
    act_cols_v = _identificar_cols_actividad(row4_v)
    act_codes_v = [str(df_v.iloc[4, j]).strip() for j in act_cols_v]
    act_names_v = [str(df_v.iloc[3, j]).strip() for j in act_cols_v]
    act_labels_v = [_label_actividad(c, n) for c, n in zip(act_codes_v, act_names_v)]
    label_by_code = dict(zip(act_codes_v, act_labels_v))

    fila_total_v = next((i for i in range(5, len(df_v))
                         if str(df_v.iloc[i, 0]).strip().lower() == 'total'), 228)
    prod_rows_v = list(range(5, fila_total_v))
    prod_labels_v = []
    for i in prod_rows_v:
        etiq = _limpiar(df_v.iloc[i, 1])
        if not etiq:
            etiq = _limpiar(df_v.iloc[i, 0])
        prod_labels_v.append(etiq)

    V_raw = _extraer_submatriz(df_v, prod_rows_v, act_cols_v,
                                prod_labels_v, act_labels_v)
    V = V_raw.T.copy()

    # ── U matrix ─────────────────────────────────────────────────────────────
    # Row 4: codes. Activity codes start at col 2
    row4_u = df_u.iloc[4]
    act_cols_u = _identificar_cols_actividad(row4_u)
    act_codes_u = [str(df_u.iloc[4, j]).strip() for j in act_cols_u]
    act_labels_u = []
    for c in act_codes_u:
        label = None
        for variante in _codigo_match(c):
            label = label_by_code.get(variante)
            if label is not None:
                break
        act_labels_u.append(label if label is not None else c)

    fila_total_u = next((i for i in range(5, len(df_u))
                         if str(df_u.iloc[i, 0]).strip().lower() == 'total'), 228)
    prod_rows_u = list(range(5, fila_total_u))
    prod_labels_u = []
    for i in prod_rows_u:
        etiq = _limpiar(df_u.iloc[i, 1])
        if not etiq:
            etiq = _limpiar(df_u.iloc[i, 0])
        prod_labels_u.append(etiq)

    U_raw = _extraer_submatriz(df_u, prod_rows_u, act_cols_u,
                                prod_labels_u, act_labels_u)
    U = U_raw.copy()

    # ── Final demand Y ────────────────────────────────────────────────────────
    # Columns after 'UI' (col 109): CH, CP, EX, Fbc Fijo, OV, Productos terminados, Trabajos en curso, UF
    ui_col = next((j for j, v in enumerate(row4_u)
                   if str(v).strip() in ('UI', 'UTILIZACION INTERMEDIA')), None)
    if ui_col is not None:
        fd_cols = list(range(ui_col + 1, len(row4_u)))
        # Exclude trailing empty/DEMANDA
        fd_cols = [j for j in fd_cols
                   if str(row4_u.iloc[j]).strip() not in ('', 'nan', 'UF', 'DEMANDA', 'DEMANDA TOTAL')]
        fd_labels = [str(row4_u.iloc[j]).strip() for j in fd_cols]
        Y = _extraer_submatriz(df_u, prod_rows_u, fd_cols, prod_labels_u, fd_labels)
    else:
        Y = pd.DataFrame(0.0, index=prod_labels_u, columns=['demanda_final'])

    demanda_col = next((j for j, v in enumerate(row4_u) if str(v).strip() == 'DEMANDA'), None)
    demanda_total_pc = _serie_columna(df_u, prod_rows_u, demanda_col, prod_labels_u,
                                      'demanda_total_pc') if demanda_col is not None else None

    # ── Imports M ─────────────────────────────────────────────────────────────
    impo_col = next((j for j, v in enumerate(row4_v) if str(v).strip() == 'IMPO'), None)
    if impo_col is not None:
        M = _serie_columna(df_v, prod_rows_v, impo_col, prod_labels_v, 'importaciones')
        M = M.reindex(prod_labels_u).fillna(0)
    else:
        M = pd.Series(0.0, index=prod_labels_u, name='importaciones')

    # ── Value added W ─────────────────────────────────────────────────────────
    fila_vab = next((i for i in range(fila_total_u, min(fila_total_u+10, len(df_u)))
                     if 'valor agregado' in str(df_u.iloc[i, 0]).lower()), None)
    if fila_vab is not None:
        W_row = df_u.iloc[fila_vab, act_cols_u]
        W = pd.to_numeric(W_row, errors='coerce').fillna(0)
        W.index = act_labels_u[:len(W)]
        W.name = 'valor_agregado_bruto'
    else:
        W = pd.Series(0.0, index=act_labels_u, name='valor_agregado_bruto')

    if verbose:
        print(f"  2018: V={V.shape}, U={U.shape}, Y={Y.shape}, "
              f"W={len(W)} act, M={len(M)} prod")

    cou = COU(pais='argentina', anio=anio, moneda='ARS', unidad='miles',
              V=V, U=U, Y=Y, W=W.to_frame().T, M=M)
    if demanda_total_pc is not None:
        q_dom = V.sum(axis=0).reindex(demanda_total_pc.index).fillna(0)
        cou.demanda_total_pc = demanda_total_pc
        cou.factor_domestico_pb = q_dom.div(demanda_total_pc.replace(0, np.nan)).fillna(0)
        cou.notas.append('Y fuente excluye UF porque UF es total de utilizacion final.')
        cou.notas.append('Factor domestico/precios basicos calculado como OPB/DEMANDA por producto.')
    return cou


# ──────────────────────────────────────────────────────────────────────────────
# Función pública
# ──────────────────────────────────────────────────────────────────────────────

def parsear(ruta: Path, anio: int, verbose: bool = False) -> COU:
    """
    Lee un archivo COU de Argentina (INDEC/CEPAL) y retorna un objeto COU.

    Parámetros
    ----------
    ruta  : Path al archivo .xls o .xlsx
    anio  : año de la tabla
    """
    ruta = Path(ruta)
    if verbose:
        print(f"  Leyendo {ruta.name} ...")

    engine = 'xlrd' if ruta.suffix.lower() == '.xls' else 'openpyxl'
    xls = pd.ExcelFile(ruta, engine=engine)
    sheet_names = xls.sheet_names

    # Formato 2004 (precios básicos)
    if 'Mat Oferta pb' in sheet_names:
        return _parsear_2004(xls, anio, verbose)

    # Formato 2018+ (precios comprador, hoja nombrada por año)
    hoja_v = next((s for s in sheet_names if s.startswith('Mat_Of_pc_')), None)
    if hoja_v is not None:
        hoja_u = next((s for s in sheet_names if s.startswith('Mat_Ut_pc_')), None)
        if hoja_u:
            return _parsear_2018_gen(xls, hoja_v, hoja_u, anio, verbose)

    raise ValueError(
        f"Formato desconocido en {ruta.name}. "
        f"Hojas: {sheet_names}"
    )
