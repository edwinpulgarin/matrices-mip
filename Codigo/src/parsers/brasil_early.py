"""
Parser de los Cuadros de Oferta y Utilización (COU) de Brasil — CEPAL, base 2000.

Fuente: repositorio CEPAL https://statistics.cepal.org/repository/cou-mip/
Archivos: BRA_COU_2000_2004.zip y BRA_COU_2005_2009.zip

Clasificación: 107 productos × 51 actividades (año base 2000, SCN 1993).
Nota: distinta de la serie 2010-2021 de IBGE (68 actividades, SCN 2008).

Estructura de cada archivo anual:
    OFERTA → hoja 'producao': V (productos × actividades), shape (113, 53)
    DEMANDA → hoja 'CI'     : U (productos × actividades), shape (113, 53)
    DEMANDA → hoja 'VA'     : W componentes × actividades  (20, 53)
    DEMANDA → hoja 'demanda': Y demanda final por producto  (113, 10)

Formato de cada hoja:
    Fila 0: título
    Fila 1: vacía
    Fila 2: encabezado ("Produção das atividades" / "Consumo intermediário")
    Fila 3: nombres de actividades (cols 1-51)
    Fila 4: vacía
    Filas 5-111: 107 productos (col 0 = nombre, cols 1-51 = valores)
    Fila 112: TOTAL

Unidad: millones de BRL a precios corrientes del año respectivo.
"""

import io
import zipfile
import numpy as np
import pandas as pd
from pathlib import Path

from .base import COU

# Mapa: año → nombre del ZIP que lo contiene
_ZIP_MAP = {
    2000: 'BRA_COU_2000_2004.zip',
    2001: 'BRA_COU_2000_2004.zip',
    2002: 'BRA_COU_2000_2004.zip',
    2003: 'BRA_COU_2000_2004.zip',
    2004: 'BRA_COU_2000_2004.zip',
    2005: 'BRA_COU_2005_2009.zip',
    2006: 'BRA_COU_2005_2009.zip',
    2007: 'BRA_COU_2005_2009.zip',
    2008: 'BRA_COU_2005_2009.zip',
    2009: 'BRA_COU_2005_2009.zip',
}


def _leer_hoja(zf: zipfile.ZipFile, nombre_archivo: str,
               hoja: str) -> pd.DataFrame:
    """Lee una hoja desde un XLS dentro del ZIP."""
    with zf.open(nombre_archivo) as f:
        raw = io.BytesIO(f.read())
    return pd.read_excel(raw, header=None, sheet_name=hoja, engine='xlrd')


def _extraer_matriz(df: pd.DataFrame, n_act: int = 51) -> pd.DataFrame:
    """
    Extrae la submatriz numérica (productos × actividades) de una hoja COU.
    Usa row 3 como etiquetas de actividades, filas 5+ como datos de producto.
    """
    # Etiquetas de actividades (row 3, cols 1..n_act)
    act_labels = [str(df.iloc[3, j]).strip() for j in range(1, n_act + 1)]

    # Filas de productos: desde fila 5, col 0 no nulo y no es "Total"
    prod_rows = []
    prod_labels = []
    for i in range(5, len(df)):
        v = df.iloc[i, 0]
        if pd.isna(v):
            continue
        s = str(v).strip()
        if s.lower().startswith('total'):
            break
        prod_rows.append(i)
        prod_labels.append(s)

    bloque = df.iloc[prod_rows, 1:n_act + 1].copy()
    bloque = bloque.apply(pd.to_numeric, errors='coerce').fillna(0)
    bloque.index = prod_labels
    bloque.columns = act_labels
    return bloque


def parsear(carpeta: Path, anio: int, verbose: bool = False) -> COU:
    """
    Lee el COU de Brasil para un año entre 2000-2009 (CEPAL base 2000).

    Parámetros
    ----------
    carpeta : Path al directorio data/raw/brasil/
    anio    : año entre 2000 y 2009
    """
    carpeta = Path(carpeta)

    if anio not in _ZIP_MAP:
        raise FileNotFoundError(
            f"Año {anio} fuera del rango soportado (2000-2009)")

    zip_name = _ZIP_MAP[anio]
    zip_path = carpeta / zip_name

    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP no encontrado: {zip_path}")

    # Nombres de archivos dentro del ZIP
    base = f'BRA_COU_{anio}_PRECIOSCORRIENTES_107x51'
    oferta_name  = f'{base}_OFERTA.xls'
    demanda_name = f'{base}_DEMANDA.xls'

    if verbose:
        print(f"  Leyendo {zip_name} → {anio} ...")

    with zipfile.ZipFile(zip_path) as zf:
        disponibles = zf.namelist()
        if oferta_name not in disponibles or demanda_name not in disponibles:
            raise FileNotFoundError(
                f"Archivos {anio} no encontrados en {zip_name}. "
                f"Disponibles: {disponibles[:4]} ...")

        df_oferta  = _leer_hoja(zf, oferta_name,  hoja='producao')
        df_ci      = _leer_hoja(zf, demanda_name, hoja='CI')
        df_va      = _leer_hoja(zf, demanda_name, hoja='VA')
        df_demanda = _leer_hoja(zf, demanda_name, hoja='demanda')

    # ── V: producción por actividad (productos × actividades) ────────────────
    V_raw = _extraer_matriz(df_oferta)       # (107 prod × 51 act)
    # Transponer a (actividades × productos) = formato estándar del pipeline
    V = V_raw.T.copy()

    # ── U: uso intermedio (productos × actividades) ──────────────────────────
    U = _extraer_matriz(df_ci)               # (107 prod × 51 act)

    # Alinear índices
    prods_comunes = [p for p in V.columns if p in U.index]
    acts_comunes  = [a for a in V.index   if a in U.columns]
    V = V.loc[acts_comunes, prods_comunes]
    U = U.loc[prods_comunes, acts_comunes]

    # ── Y: demanda final (productos × categorías) ────────────────────────────
    # Filas 5+: productos, col 0 = nombre, cols 1+ = categorías
    y_rows, y_labels = [], []
    for i in range(5, len(df_demanda)):
        v = df_demanda.iloc[i, 0]
        if pd.isna(v):
            continue
        s = str(v).strip()
        if s.lower().startswith('total'):
            break
        y_rows.append(i)
        y_labels.append(s)
    Y_bloque = df_demanda.iloc[y_rows, 1:].apply(pd.to_numeric, errors='coerce').fillna(0)
    Y_bloque.index = y_labels
    Y = Y_bloque.reindex(prods_comunes).fillna(0)
    Y.columns = [f'DF_{j}' for j in range(len(Y.columns))]

    # ── W: Valor Agregado Bruto (primera fila de VA = "Valor adicionado bruto") ──
    # Fila 5 = "Valor adicionado bruto (PIB)"
    w_vals = df_va.iloc[5, 1:52].apply(pd.to_numeric, errors='coerce').fillna(0)
    act_labels_va = [str(df_va.iloc[3, j]).strip() for j in range(1, 52)]
    W_series = pd.Series(w_vals.values, index=act_labels_va, name='valor_agregado_bruto')
    W_series = W_series.reindex(acts_comunes).fillna(0)
    W = W_series.to_frame('valor_agregado_bruto').T
    W.columns = acts_comunes

    empleo = None
    for i in range(5, len(df_va)):
        etiq = str(df_va.iloc[i, 0]).strip().lower()
        if 'fator trabalho' in etiq or 'ocup' in etiq:
            e_vals = df_va.iloc[i, 1:52].apply(pd.to_numeric, errors='coerce').fillna(0)
            empleo = pd.DataFrame({'ocupaciones': e_vals.values}, index=act_labels_va)
            empleo = empleo.reindex(acts_comunes).fillna(0)
            break

    # ── M: importaciones (no disponibles en este formato, zeros) ─────────────
    M = pd.Series(0.0, index=prods_comunes, name='importaciones')

    n_act  = len(acts_comunes)
    n_prod = len(prods_comunes)
    if verbose:
        print(f"  {anio}: V={V.shape}, U={U.shape}, {n_act} act × {n_prod} prod")

    return COU(
        pais='brasil', anio=anio, moneda='BRL', unidad='millones',
        V=V, U=U, Y=Y, W=W, M=M, empleo=empleo,
    )
