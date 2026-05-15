"""
Parser de la Matriz de Insumo-Producto (MIP) del BCU Uruguay.

El BCU publica MIPs ya construidas (no COU) en su sección de Estadísticas.
Disponible: año 2016 (base 2016).

Archivos descargados de:
    https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Matriz-Insumo-Producto.aspx

Archivos relevantes (en data/raw/uruguay/):
    mip_producto_detallada_2016.xlsx → Z producto×producto (128×128)
    leontief_producto_2016.xlsx      → A, L = Inv(I-A) producto×producto

Estructura hoja 'MIP 128 x 128':
    Fila 8   : encabezados (P1..P128 a partir de col 6)
    Filas 9-136 : Z matrix (productos P1..P128)
    Fila 137 : Total usos intermedios
    Fila 141 : VAB precios básicos
    Fila 142 : Producción precios básicos

Estructura hojas en leontief_producto_2016.xlsx:
    'Matriz A'   → A matrix (open model, 128×128)
    'Inv (I-A)'  → L matrix (Leontief inverse, 128×128)

Unidad: millones de UYU a precios básicos (2016)
"""

import numpy as np
import pandas as pd
from pathlib import Path


def _extraer_cuadrada_mip(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Extrae Z (flows), g (producción), W (VAB) desde la hoja 'MIP 128 x 128'.
    """
    # Fila 8: encabezados de columnas
    header_row = 8
    headers = df_raw.iloc[header_row]

    # Columnas que corresponden a productos (P1..P128, a partir de col 6)
    col_indices = []
    col_codes = []
    for j, h in enumerate(headers):
        if isinstance(h, str) and h.startswith('P') and h[1:].isdigit():
            col_indices.append(j)
            col_codes.append(h)

    # Filas de productos (P1..P128): filas 9-136
    fila_prod = [i for i in range(9, len(df_raw))
                 if isinstance(df_raw.iloc[i, 0], str)
                 and str(df_raw.iloc[i, 0]).startswith('P')
                 and str(df_raw.iloc[i, 0])[1:].isdigit()]

    row_codes = [str(df_raw.iloc[i, 0]) for i in fila_prod]
    row_names = [str(df_raw.iloc[i, 1]).strip() for i in fila_prod]
    label_by_code = {
        code: f"{code}---{name}" if name and name.lower() != 'nan' else code
        for code, name in zip(row_codes, row_names)
    }
    col_names = [label_by_code.get(code, code) for code in col_codes]
    row_labels = [label_by_code.get(code, code) for code in row_codes]

    Z_raw = df_raw.iloc[fila_prod, col_indices].copy()
    Z_raw.index = row_labels
    Z_raw.columns = col_names
    Z = Z_raw.apply(pd.to_numeric, errors='coerce').fillna(0)

    # Producción (g): fila donde col 0 == 'Producción precios básicos'
    g_vals = None
    W_vals = None
    for i in range(len(df_raw)):
        v = str(df_raw.iloc[i, 0])
        if 'Producción precios básicos' in v or 'roducci' in v and 'precios b' in v:
            g_vals = df_raw.iloc[i, col_indices].copy()
        if 'VAB precios básicos' in v:
            W_vals = df_raw.iloc[i, col_indices].copy()

    if g_vals is None:
        # Fallback: last numeric row
        g_vals = pd.Series([0.0] * len(col_names), index=col_names)
    else:
        g_vals = pd.to_numeric(g_vals, errors='coerce').fillna(0)
        g_vals.index = col_names

    if W_vals is None:
        W_vals = pd.Series([0.0] * len(col_names), index=col_names)
    else:
        W_vals = pd.to_numeric(W_vals, errors='coerce').fillna(0)
        W_vals.index = col_names

    g = pd.Series(g_vals.values, index=col_names, name='produccion_bruta')
    W = pd.Series(W_vals.values, index=col_names, name='valor_agregado')
    return Z, g, W


def _extraer_cuadrada_leontief(df_raw: pd.DataFrame,
                               target_index: list) -> pd.DataFrame:
    """
    Extrae una matriz cuadrada (A o L) del archivo Leontief del BCU.
    Los encabezados de columna son float (1.0, 2.0, ...) en fila 7,
    el índice de filas son enteros en col 0 a partir de fila 8.
    Alinea el resultado con target_index (ej. ['P1', 'P2', ...]).
    """
    header_row = 7
    headers = df_raw.iloc[header_row]

    # Columnas de datos: las que tienen encabezado numérico (float)
    col_indices = []
    col_codes = []
    for j, h in enumerate(headers):
        try:
            v = float(h)
            if v == int(v) and int(v) >= 1:
                col_indices.append(j)
                col_codes.append(int(v))
        except (TypeError, ValueError):
            pass

    # Filas de datos: fila 8 en adelante con código entero en col 0
    fila_datos = []
    row_codes = []
    for i in range(8, len(df_raw)):
        try:
            code = int(float(df_raw.iloc[i, 0]))
            fila_datos.append(i)
            row_codes.append(code)
        except (TypeError, ValueError):
            pass

    M_raw = df_raw.iloc[fila_datos, col_indices].copy()
    M_raw = M_raw.apply(pd.to_numeric, errors='coerce').fillna(0)
    M_raw.index = [f'P{c}' for c in row_codes]
    M_raw.columns = [f'P{c}' for c in col_codes]

    # Alinear con target_index, que puede venir como "P1---Nombre".
    code_to_label = {str(s).split('---', 1)[0]: s for s in target_index}
    comunes = [code for code in code_to_label if code in M_raw.index and code in M_raw.columns]
    if comunes:
        M_raw = M_raw.loc[comunes, comunes]
        labels = [code_to_label[code] for code in comunes]
        M_raw.index = labels
        M_raw.columns = labels
    return M_raw


def parsear(carpeta: Path, anio: int = 2016, verbose: bool = False) -> dict:
    """
    Lee los archivos MIP del BCU Uruguay y retorna las matrices ya construidas.

    Parámetros
    ----------
    carpeta  : Path al directorio data/raw/uruguay/
    anio     : año de la MIP (default 2016, único disponible)
    verbose  : imprimir progreso

    Retorna dict con:
        'Z'   : DataFrame — flujos intermedios producto×producto
        'A'   : DataFrame — coeficientes técnicos (modelo abierto)
        'L'   : DataFrame — inversa de Leontief (modelo abierto)
        'g'   : Series   — producción bruta por producto
        'W'   : Series   — valor agregado bruto por producto
        'anio': int
        'pais': str
    """
    carpeta = Path(carpeta)

    mip_file = carpeta / f'mip_producto_detallada_{anio}.xlsx'
    lf_file  = carpeta / f'leontief_producto_{anio}.xlsx'

    if not mip_file.exists():
        raise FileNotFoundError(f"No se encontró: {mip_file}")

    if verbose:
        print(f"  Leyendo {mip_file.name} ...")

    xl_mip = pd.ExcelFile(mip_file)
    # Buscar la hoja con la Z detallada
    hoja_z = next((s for s in xl_mip.sheet_names if 'MIP' in s and '128' in s), xl_mip.sheet_names[1])
    df_mip = xl_mip.parse(hoja_z, header=None)

    Z, g, W = _extraer_cuadrada_mip(df_mip)
    n = len(Z)

    if verbose:
        print(f"  MIP {anio}: {n} productos")

    # Coeficientes técnicos y Leontief
    if lf_file.exists():
        if verbose:
            print(f"  Leyendo {lf_file.name} ...")
        xl_lf = pd.ExcelFile(lf_file)
        df_A = xl_lf.parse('Matriz A', header=None)
        df_L = xl_lf.parse('Inv (I-A)', header=None)
        A = _extraer_cuadrada_leontief(df_A, list(Z.index))
        L = _extraer_cuadrada_leontief(df_L, list(Z.index))
    else:
        # Calcular A y L desde Z y g
        if verbose:
            print("  Archivo Leontief no encontrado, calculando A y L desde Z...")
        g_arr = g.values
        A_arr = np.where(g_arr > 0, Z.values / g_arr[np.newaxis, :], 0)
        A = pd.DataFrame(A_arr, index=Z.index, columns=Z.columns)
        I = np.eye(n)
        try:
            L_arr = np.linalg.inv(I - A_arr)
        except np.linalg.LinAlgError:
            L_arr = np.eye(n)
        L = pd.DataFrame(L_arr, index=Z.index, columns=Z.columns)

    # Reindexar para asegurar alineación
    A = A.reindex(index=Z.index, columns=Z.columns).fillna(0)
    L = L.reindex(index=Z.index, columns=Z.columns).fillna(0)

    return {
        'Z'   : Z,
        'A'   : A,
        'L'   : L,
        'g'   : g,
        'W'   : W,
        'anio': anio,
        'pais': 'uruguay',
    }


def multiplicadores_desde_mip(mip_dict: dict) -> pd.DataFrame:
    """
    Calcula multiplicadores directamente desde la MIP ya compilada del BCU.
    """
    from src.multiplicadores import (multiplicador_produccion,
                                     multiplicador_demanda,
                                     clasificar_sectores)

    L = mip_dict['L']
    tabla = pd.DataFrame({
        'mult_produccion': multiplicador_produccion(L),
        'mult_demanda'   : multiplicador_demanda(L),
        'anio'           : mip_dict['anio'],
        'pais'           : mip_dict['pais'],
    })
    tabla['clasificacion'] = clasificar_sectores(tabla)
    return tabla
