"""
Parser de las Tabelas de Recursos e Usos (TRU) de Brasil — IBGE.

Estructura verificada (nivel 68, serie 2010-2021):
    Archivos: 68_tab1_AAAA.xls  y  68_tab2_AAAA.xls

    68_tab1_AAAA.xls:
        Hoja 'producao'   → V: matriz de producción (produtos × atividades)
        Hoja 'importacao' → M: vector de importaciones por produto
        Hoja 'oferta'     → resumen de oferta (no se usa directamente)

    68_tab2_AAAA.xls:
        Hoja 'CI'         → U: consumo intermediário (produtos × atividades)
        Hoja 'demanda'    → Y: demanda final (produtos × componentes)
        Hoja 'VA'         → W: valor adicionado (componentes × atividades)

    Estructura de filas en cada hoja:
        Fila 0: título
        Fila 2: encabezado de bloque ("Produção das atividades...")
        Fila 3: códigos/nombres de actividades (cols 2+)
        Fila 4: fila vacía
        Filas 5+: datos (col 0=código produto, col 1=descripción, cols 2+=valores)

    Unidad: millones de BRL corrientes
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional

from .base import COU, limpiar_nombre


# Fila donde comienzan los datos (0-indexed)
FILA_DATOS   = 5
# Fila donde están los nombres de actividades
FILA_ACT     = 3
# Columna de descripción del producto
COL_DESC     = 1
# Primera columna de datos numéricos
COL_DATOS    = 2


def _leer_hoja(xls: pd.ExcelFile, hoja: str) -> pd.DataFrame:
    return pd.read_excel(xls, sheet_name=hoja, header=None, dtype=str)


def _extraer_nombres_actividades(df: pd.DataFrame) -> list:
    """Lee los nombres de actividades de la fila FILA_ACT, desde COL_DATOS."""
    nombres = []
    for j in range(COL_DATOS, len(df.columns)):
        v = str(df.iloc[FILA_ACT, j]).strip()
        if v in ('', 'nan', 'None'):
            break
        # El nombre puede ser "0191\nAgricultura..." — limpiamos el código
        # Mantenemos el código+nombre para trazabilidad
        nombre = v.replace('\n', ' — ').strip()
        nombres.append(nombre)
    return nombres


def _extraer_nombres_produtos(df: pd.DataFrame, n_filas: int) -> list:
    """Lee los nombres de produtos de la columna COL_DESC, desde FILA_DATOS."""
    nombres = []
    for i in range(FILA_DATOS, FILA_DATOS + n_filas):
        if i >= len(df):
            break
        v = str(df.iloc[i, COL_DESC]).strip()
        if v in ('', 'nan', 'None'):
            break
        nombres.append(v)
    return nombres


def _extraer_bloque(df: pd.DataFrame,
                    n_filas: int,
                    n_cols: int) -> np.ndarray:
    """Extrae bloque numérico (n_filas × n_cols) desde (FILA_DATOS, COL_DATOS)."""
    bloque = df.iloc[FILA_DATOS:FILA_DATOS + n_filas,
                     COL_DATOS:COL_DATOS + n_cols]
    return bloque.apply(pd.to_numeric, errors='coerce').fillna(0).values


def parsear(ruta_tab1: Path = None,
            ruta_tab2: Path = None,
            anio: int = None,
            carpeta: Path = None,
            verbose: bool = False) -> COU:
    """
    Lee los archivos TRU de Brasil y retorna un objeto COU.

    Se puede llamar de dos formas:
    1. Con rutas explícitas: parsear(ruta_tab1=..., ruta_tab2=..., anio=...)
    2. Con carpeta y año:    parsear(carpeta=..., anio=...)
       (buscará 68_tab1_AAAA.xls y 68_tab2_AAAA.xls automáticamente)
    """
    if carpeta is not None and anio is not None:
        ruta_tab1 = carpeta / f"68_tab1_{anio}.xls"
        ruta_tab2 = carpeta / f"68_tab2_{anio}.xls"

    if ruta_tab1 is None or ruta_tab2 is None:
        raise ValueError("Proporcionar ruta_tab1 y ruta_tab2, o carpeta y anio")

    if not ruta_tab1.exists():
        raise FileNotFoundError(f"No encontrado: {ruta_tab1}")
    if not ruta_tab2.exists():
        raise FileNotFoundError(f"No encontrado: {ruta_tab2}")

    if verbose:
        print(f"  Leyendo {ruta_tab1.name} + {ruta_tab2.name} ...")

    xls1 = pd.ExcelFile(ruta_tab1, engine='xlrd')
    xls2 = pd.ExcelFile(ruta_tab2, engine='xlrd')

    # ── Hoja 'producao': matriz V (produtos × atividades) ────────────────────
    df_prod = _leer_hoja(xls1, 'producao')
    noms_atv  = _extraer_nombres_actividades(df_prod)
    n_atv     = len(noms_atv)

    # Contar filas de productos (hasta fila vacía)
    n_prod = 0
    for i in range(FILA_DATOS, len(df_prod)):
        v = str(df_prod.iloc[i, COL_DADOS := COL_DATOS]).strip()
        if v in ('', 'nan', 'None'):
            break
        n_prod += 1

    noms_prod = _extraer_nombres_produtos(df_prod, n_prod)
    n_prod    = len(noms_prod)  # puede ser menor si hay vacíos antes

    V_arr = _extraer_bloque(df_prod, n_prod, n_atv)
    V = pd.DataFrame(V_arr, index=noms_prod, columns=noms_atv)
    V = V.T  # → (n_atv × n_prod)

    if verbose:
        print(f"  V: {V.shape[0]} atividades × {V.shape[1]} produtos")

    # ── Hoja 'importacao': vector M ───────────────────────────────────────────
    M = None
    if 'importacao' in xls1.sheet_names:
        df_imp = _leer_hoja(xls1, 'importacao')
        # La hoja de importación tiene la misma estructura de filas
        # La columna de importaciones CIF generalmente está en la col COL_DATOS
        imp_arr = _extraer_bloque(df_imp, n_prod, 1).flatten()
        M = pd.Series(imp_arr, index=noms_prod, name='importacoes')

    # ── Hoja 'CI': matriz U de consumo intermediário ──────────────────────────
    df_ci = _leer_hoja(xls2, 'CI')
    noms_prod_u = _extraer_nombres_produtos(df_ci, n_prod + 10)  # margen extra
    noms_prod_u = noms_prod_u[:n_prod]  # alinear con V
    U_arr = _extraer_bloque(df_ci, n_prod, n_atv)
    U = pd.DataFrame(U_arr, index=noms_prod_u, columns=noms_atv[:n_atv])

    # ── Hoja 'demanda': matriz Y de demanda final ─────────────────────────────
    df_dem = _leer_hoja(xls2, 'demanda')
    # Nombres de componentes de demanda final (fila FILA_ACT, cols desde COL_DATOS)
    noms_fd = []
    for j in range(COL_DATOS, len(df_dem.columns)):
        v = str(df_dem.iloc[FILA_ACT, j]).strip()
        if v in ('', 'nan', 'None'):
            break
        noms_fd.append(v.replace('\n', ' ').strip())

    n_fd = len(noms_fd)
    Y_arr = _extraer_bloque(df_dem, n_prod, n_fd)
    Y = pd.DataFrame(Y_arr,
                     index=noms_prod_u[:n_prod],
                     columns=noms_fd[:n_fd])

    # ── Hoja 'VA': valor adicionado ───────────────────────────────────────────
    df_va = _leer_hoja(xls2, 'VA')
    # Filas de VA: desde FILA_DATOS, col 0 = etiqueta, cols 1.. = actividades
    W = None
    empleo = None
    for i in range(FILA_DATOS, len(df_va)):
        etiq = str(df_va.iloc[i, 0]).strip()
        if etiq in ('', 'nan', 'None'):
            continue
        etiq_l = etiq.lower()
        # Solo las filas de componentes de VA (excluir sub-totales redundantes)
        if 'valor adicion' in etiq_l:
            fila_num = df_va.iloc[i, 1:1 + n_atv]
            vals = fila_num.apply(pd.to_numeric, errors='coerce').fillna(0).values
            if len(vals) >= n_atv:
                W = pd.Series(vals[:n_atv], index=noms_atv[:n_atv],
                              name='valor_agregado_bruto').to_frame().T
        if 'fator trabalho' in etiq_l or 'ocup' in etiq_l:
            fila_num = df_va.iloc[i, 1:1 + n_atv]
            vals = fila_num.apply(pd.to_numeric, errors='coerce').fillna(0).values
            if len(vals) >= n_atv:
                empleo = pd.DataFrame({'ocupaciones': vals[:n_atv]}, index=noms_atv[:n_atv])

    if W is None:
        W = pd.DataFrame({'valor_adicionado': np.zeros(n_atv)},
                         index=noms_atv).T

    return COU(
        pais='brasil',
        anio=anio,
        moneda='BRL',
        unidad='millones',
        V=V,
        U=U,
        Y=Y,
        W=W,
        M=M,
        empleo=empleo,
    )
