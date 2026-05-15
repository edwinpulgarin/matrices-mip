"""
Parser de la Matriz de Insumo-Producto (MIP) directa de México — INEGI.

El INEGI publica MIPs ya construidas (no COU) a través de sus Datos Abiertos.
Disponibles: 2008 (CEPAL Excel), 2013 y 2018 (INEGI CSV), publicadas quinquenalmente.

Estructura ZIP 2008 (MEX_MIP_2008.zip) — CEPAL:
    MEX_MIP_2008_814 x814_IxI_DOMESTICA_RAMA.XLSX
        Fila 9       : números de columna (1-262)
        Filas 10-271 : 262 ramas SCIAN (col1=código, col2=nombre, col3=g)
        Cols 6-267   : bloque Z (demanda intermedia)
        Fila 294     : Valor Agregado Bruto (W)
        Fila 305     : Producción Total por Actividad (g columnar)

Estructura ZIP 2013 (mip_2013_csv.zip):
    conjunto_de_datos/mip_d_pb_ixi_3.csv   → Z doméstica, nivel rama (SCIAN)
    conjunto_de_datos/mip_m_pb_ixi_3.csv   → Z importaciones
    conjunto_de_datos/mip_t_pb_ixi_3.csv   → Z totales
    conjunto_de_datos/mip_ctec_ixi_3.csv   → A (coeficientes técnicos)
    conjunto_de_datos/mip_cdi_ixi_3.csv    → L (inversa de Leontief)

Estructura ZIP 2018 (mip_csv.zip):
    conjunto de datos/conjunto_de_datos_mip_d_pb_ixi_32018.csv   → Z doméstica
    (igual lógica pero con prefijo y sufijo de año)

Nomenclatura:
    cdi  = coeficientes directos e indirectos (= inversa Leontief L)
    ctec = coeficientes técnicos (= A)
    d    = doméstico, m = importado, t = total
    pb   = precios básicos
    ixi  = industria×industria, pxp = producto×producto
    _1 = sector, _2 = subsector, _3 = rama, _4 = clase

Unidad: millones de MXN a precios básicos
"""

import io
import zipfile
import numpy as np
import pandas as pd
from pathlib import Path

from .base import COU


def _detectar_nombres(zf: zipfile.ZipFile, nivel: str, anio: int) -> dict:
    """
    Detecta el esquema de nombres de archivos dentro del ZIP (2013 vs 2018+).
    Retorna un dict con las rutas internas para cada tipo de matriz.
    """
    nombres = zf.namelist()

    # Esquema 2013: conjunto_de_datos/mip_d_pb_ixi_3.csv
    if f'conjunto_de_datos/mip_d_pb_ixi_{nivel}.csv' in nombres:
        carpeta = 'conjunto_de_datos'
        return {
            'Z'  : f'{carpeta}/mip_d_pb_ixi_{nivel}.csv',
            'Z_m': f'{carpeta}/mip_m_pb_ixi_{nivel}.csv',
            'Z_t': f'{carpeta}/mip_t_pb_ixi_{nivel}.csv',
            'A'  : f'{carpeta}/mip_ctec_ixi_{nivel}.csv',
            'L'  : f'{carpeta}/mip_cdi_ixi_{nivel}.csv',
        }

    # Esquema 2018+: conjunto de datos/conjunto_de_datos_mip_d_pb_ixi_3AAAA.csv
    carpeta = 'conjunto de datos'
    sufijo = str(anio)
    return {
        'Z'  : f'{carpeta}/conjunto_de_datos_mip_d_pb_ixi_{nivel}{sufijo}.csv',
        'Z_m': f'{carpeta}/conjunto_de_datos_mip_m_pb_ixi_{nivel}{sufijo}.csv',
        'Z_t': f'{carpeta}/conjunto_de_datos_mip_t_pb_ixi_{nivel}{sufijo}.csv',
        'A'  : f'{carpeta}/conjunto_de_datos_mip_ctec_ixi_{nivel}{sufijo}.csv',
        'L'  : f'{carpeta}/conjunto_de_datos_mip_cdi_ixi_{nivel}{sufijo}.csv',
    }


def _leer_csv_zip(zf: zipfile.ZipFile, ruta_interna: str,
                  encoding: str = 'latin-1') -> pd.DataFrame:
    data = zf.read(ruta_interna)
    df = pd.read_csv(io.BytesIO(data), encoding=encoding, index_col=0)
    return df


def parsear(ruta_zip: Path, anio: int = 2013,
            nivel: str = '3', verbose: bool = False) -> dict:
    # Formato CEPAL Excel (2003, 20 sectores)
    if anio == 2003:
        return _parsear_2003(ruta_zip, verbose=verbose)

    # Formato CEPAL Excel (2008)
    if anio == 2008:
        return _parsear_2008(ruta_zip, verbose=verbose)

    """
    Lee el ZIP de MIP del INEGI y retorna las matrices ya construidas.

    Parámetros
    ----------
    ruta_zip : Path al archivo ZIP descargado del INEGI
    anio     : año de la MIP (default 2013)
    nivel    : desagregación SCIAN: '1'=sector, '2'=subsector, '3'=rama (default)
    verbose  : imprimir progreso

    Retorna dict con:
        'Z'   : DataFrame — flujos intermedios domésticos (industria×industria)
        'Z_m' : DataFrame — flujos importados
        'Z_t' : DataFrame — flujos totales
        'A'   : DataFrame — coeficientes técnicos
        'L'   : DataFrame — inversa de Leontief
        'g'   : Series   — producción bruta por industria (= Z.sum(axis=0) + VA estimado)
        'anio': int
        'pais': str
    """
    if verbose:
        print(f"  Leyendo {ruta_zip.name} (nivel {nivel}) ...")

    def _extraer_cuadrada(df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Las matrices del INEGI tienen formato "ancho" con columnas como:
            'DI---Demanda intermedia|1111---Cultivo...'
        Extrae solo las columnas de demanda intermedia sectorial y las renombra
        con el código de sector, produciendo una matriz cuadrada.
        """
        # Columnas de demanda intermedia sectorial
        col_di = {c: c.split('|', 1)[1] for c in df_raw.columns
                  if c.startswith('DI---Demanda intermedia|') and '|Total' not in c}
        # Filas son los sectores productivos (index no empieza con DI/ DF)
        sectores_fila = [i for i in df_raw.index
                         if not any(i.startswith(p) for p in ('DI---', 'DF---', 'UPIPB'))]
        Z_sq = df_raw.loc[sectores_fila, list(col_di.keys())].copy()
        Z_sq.columns = list(col_di.values())
        Z_sq = Z_sq.apply(pd.to_numeric, errors='coerce').fillna(0)
        # Cuadrar: usar solo sectores presentes en ambos ejes
        comunes = [s for s in Z_sq.index if s in Z_sq.columns]
        return Z_sq.loc[comunes, comunes]

    def _extraer_cuadrada_coef(df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Los coeficientes (A, L) del INEGI tienen columnas '1111---Nombre'.
        La índice tiene el mismo formato. Extrae la submatriz cuadrada.
        """
        # Columnas que son sectores (empiezan con dígito o código)
        col_sec = [c for c in df_raw.columns if '---' in c]
        fil_sec = [i for i in df_raw.index if '---' in str(i)]
        comunes = [s for s in fil_sec if s in col_sec]
        M = df_raw.loc[comunes, comunes].copy()
        return M.apply(pd.to_numeric, errors='coerce').fillna(0)

    with zipfile.ZipFile(ruta_zip) as zf:
        rutas = _detectar_nombres(zf, nivel, anio)
        # Flujos domésticos
        Z   = _extraer_cuadrada(_leer_csv_zip(zf, rutas['Z']))
        # Flujos importados
        try:
            Z_m = _extraer_cuadrada(_leer_csv_zip(zf, rutas['Z_m']))
            Z_m = Z_m.reindex(index=Z.index, columns=Z.columns).fillna(0)
        except Exception:
            Z_m = pd.DataFrame(0.0, index=Z.index, columns=Z.columns)
        # Flujos totales
        try:
            Z_t = _extraer_cuadrada(_leer_csv_zip(zf, rutas['Z_t']))
            Z_t = Z_t.reindex(index=Z.index, columns=Z.columns).fillna(0)
        except Exception:
            Z_t = Z + Z_m

        # Coeficientes técnicos y Leontief
        A = _extraer_cuadrada_coef(_leer_csv_zip(zf, rutas['A']))
        A = A.reindex(index=Z.index, columns=Z.columns).fillna(0)
        L = _extraer_cuadrada_coef(_leer_csv_zip(zf, rutas['L']))
        L = L.reindex(index=Z.index, columns=Z.columns).fillna(0)

    n = len(Z)
    if verbose:
        print(f"  MIP {anio}: {n} sectores (nivel {nivel})")

    # Producción bruta: desde la identidad A = Z/g → g_j = z_ij/a_ij para a_ij>0
    # Usar mediana de ratios válidos para robustez
    g_vals = []
    for j in range(n):
        ratios = []
        for i in range(n):
            if A.iloc[i, j] > 1e-10 and Z.iloc[i, j] > 0:
                ratios.append(Z.iloc[i, j] / A.iloc[i, j])
        g_vals.append(float(np.median(ratios)) if ratios else 0.0)
    g = pd.Series(g_vals, index=Z.columns, name='produccion_bruta')

    return {
        'Z'   : Z,
        'Z_m' : Z_m,
        'Z_t' : Z_t,
        'A'   : A,
        'L'   : L,
        'g'   : g,
        'anio': anio,
        'pais': 'mexico',
    }


def _parsear_2008(ruta_zip: Path, verbose: bool = False) -> dict:
    """
    Lee la MIP 2008 de México (formato CEPAL Excel, IxI DOMESTICA a nivel RAMA).

    Estructura de la hoja:
        Fila 9       : números de columna 1-262
        Filas 10-271 : 262 ramas SCIAN (col1=código SCIAN, col2=nombre, col3=g_fila)
        Cols 6-267   : bloque Z doméstico (demanda intermedia)
        Fila 294     : Valor Agregado Bruto a precios básicos (W)
        Fila 305     : Producción Total por Actividad (g columnar)
    """
    fname = 'MEX_MIP_2008_814 x814_IxI_DOMESTICA_RAMA.XLSX'
    with zipfile.ZipFile(ruta_zip) as zf:
        with zf.open(fname) as f:
            raw = io.BytesIO(f.read())
    df = pd.read_excel(raw, header=None, sheet_name=0)

    # ── Identificar filas y columnas de datos ────────────────────────────────
    # Fila 9: índices numéricos 1..262 en cols 6..267; luego NaN en col 268;
    # luego 263-269 (demanda final) en cols 269-275.
    # Detectamos el bloque continuo (sin saltos de columna) que empieza en 1.
    row9 = df.iloc[9].tolist()
    act_cols = []
    for j, v in enumerate(row9):
        if isinstance(v, (int, float)) and not pd.isna(v) and v == int(v):
            num = int(v)
            if not act_cols and num == 1:
                act_cols.append(j)
            elif act_cols and j == act_cols[-1] + 1:
                # Solo continuar si el índice de COLUMNA es consecutivo
                act_cols.append(j)
            elif act_cols:
                break  # hay un salto de columna → fin del bloque intermedio
    # Filas 10-271: datos de industrias (col1 = código SCIAN válido)
    data_rows = []
    for i in range(10, 280):
        v = df.iloc[i, 1]
        try:
            int(float(str(v)))
            data_rows.append(i)
        except (ValueError, TypeError):
            pass
        if len(data_rows) == 262:
            break

    # ── Etiquetas: código SCIAN + nombre económico ──────────────────────────
    labels = [
        f"{str(int(float(str(df.iloc[i, 1]))))}---{str(df.iloc[i, 2]).strip()}"
        for i in data_rows
    ]

    # ── Z (flujos intermedios domésticos) ───────────────────────────────────
    Z_raw = df.iloc[data_rows, act_cols].copy()
    Z_raw = Z_raw.apply(pd.to_numeric, errors='coerce').fillna(0)
    Z = pd.DataFrame(Z_raw.values, index=labels, columns=labels)

    # ── g (producción total por actividad — perspectiva columnar) ───────────
    # Fila 305: "PRODUCCIÓN TOTAL POR ACTIVIDAD A PRECIOS BÁSICOS"
    g_row = None
    for i in range(290, 320):
        txt = str(df.iloc[i, 2]).upper()
        if 'PRODUCCI' in txt and 'TOTAL' in txt and 'ACTIVIDAD' in txt:
            g_row = i
            break
    if g_row is None:
        g_row = 305
    g_vals = df.iloc[g_row, act_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    g = pd.Series(g_vals.values, index=labels, name='produccion_bruta')

    # ── W (Valor Agregado Bruto a precios básicos) ───────────────────────────
    # Fila 294: "VALOR AGREGADO BRUTO A PRECIOS BÁSICOS"
    w_row = None
    for i in range(280, 310):
        txt = str(df.iloc[i, 2]).upper()
        if 'VALOR AGREGADO BRUTO' in txt and 'PRECIOS' in txt:
            w_row = i
            break
    if w_row is None:
        w_row = 294
    w_vals = df.iloc[w_row, act_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    W = pd.Series(w_vals.values, index=labels, name='valor_agregado')

    # ── A y L ────────────────────────────────────────────────────────────────
    g_safe = g.replace(0, np.nan)
    A = Z.divide(g_safe, axis=1).fillna(0)
    I_mat = np.eye(len(labels))
    try:
        L_vals = np.linalg.inv(I_mat - A.values)
    except np.linalg.LinAlgError:
        L_vals = np.linalg.pinv(I_mat - A.values)
    L = pd.DataFrame(L_vals, index=labels, columns=labels)

    if verbose:
        print(f"  MIP 2008: {len(labels)} sectores (IxI RAMA)")

    return {'Z': Z, 'A': A, 'L': L, 'g': g, 'W': W, 'anio': 2008, 'pais': 'mexico'}


def _parsear_2003(ruta_zip: Path, verbose: bool = False) -> dict:
    """
    Lee la MIP 2003 de MÃ©xico (CEPAL, matriz simÃ©trica total 20x20).

    El archivo contiene Z, valor agregado y producciÃ³n bruta por sector.
    La unidad original es miles de pesos; se preserva tal como estÃ¡ publicada.
    """
    fname = 'MEX_MIP_2003_20x20_TOTAL.xls'
    with zipfile.ZipFile(ruta_zip) as zf:
        with zf.open(fname) as f:
            raw = io.BytesIO(f.read())

    df = pd.read_excel(raw, header=None, sheet_name='Matriz_simetrica_total')

    data_rows = []
    for i in range(len(df)):
        try:
            n = int(float(df.iloc[i, 0]))
        except (TypeError, ValueError):
            continue
        code = str(df.iloc[i, 1]).strip()
        name = str(df.iloc[i, 2]).strip()
        if 1 <= n <= 20 and code not in ('nan', '') and name not in ('nan', ''):
            data_rows.append(i)

    col_indices = list(range(3, 3 + len(data_rows)))
    labels = [
        f"{str(df.iloc[i, 1]).strip()}---{str(df.iloc[i, 2]).strip()}"
        for i in data_rows
    ]

    Z_raw = df.iloc[data_rows, col_indices].copy()
    Z = Z_raw.apply(pd.to_numeric, errors='coerce').fillna(0)
    Z.index = labels
    Z.columns = labels

    def _row_by_label(text: str) -> int:
        text = text.upper()
        for i in range(len(df)):
            values = ' '.join(str(v).upper() for v in df.iloc[i, :3].tolist())
            if text in values:
                return i
        raise ValueError(f"No se encontrÃ³ fila: {text}")

    g_row = _row_by_label('PRODUCCI')
    w_row = _row_by_label('VALOR AGREGADO BRUTO ECONOM')

    g_vals = df.iloc[g_row, col_indices].apply(pd.to_numeric, errors='coerce').fillna(0)
    w_vals = df.iloc[w_row, col_indices].apply(pd.to_numeric, errors='coerce').fillna(0)
    g = pd.Series(g_vals.values, index=labels, name='produccion_bruta')
    W = pd.Series(w_vals.values, index=labels, name='valor_agregado')

    g_safe = g.replace(0, np.nan)
    A = Z.divide(g_safe, axis=1).fillna(0)
    I_mat = np.eye(len(labels))
    try:
        L_vals = np.linalg.inv(I_mat - A.values)
    except np.linalg.LinAlgError:
        L_vals = np.linalg.pinv(I_mat - A.values)
    L = pd.DataFrame(L_vals, index=labels, columns=labels)

    if verbose:
        print(f"  MIP 2003: {len(labels)} sectores")

    return {'Z': Z, 'A': A, 'L': L, 'g': g, 'W': W, 'anio': 2003, 'pais': 'mexico'}


def multiplicadores_desde_mip(mip_dict: dict) -> pd.DataFrame:
    """
    Calcula multiplicadores directamente desde la MIP ya compilada del INEGI.
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
