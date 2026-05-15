"""
Cálculo de multiplicadores de insumo-producto.

Multiplicadores implementados:
    1. Producción  (encadenamiento hacia atrás / backward linkage)
    2. Demanda     (encadenamiento hacia adelante / forward linkage)
    3. Valor agregado
    4. Empleo      (requiere vector de empleo por industria)
    5. Emisiones   (requiere vector de emisiones por unidad de producción)

Referencia: Miller & Blair (2009). Input-Output Analysis. Caps. 6, 12, 13.
"""

import numpy as np
import pandas as pd
from typing import Optional


def multiplicador_produccion(L: pd.DataFrame) -> pd.Series:
    """
    Multiplicador de producción (backward linkage).
    m_j = sum_i L_ij  (suma de columna j de la inversa de Leontief)

    Mide el efecto total en la producción de toda la economía ante
    un aumento unitario en la demanda final del sector j.
    """
    m = L.sum(axis=0)
    m.name = 'mult_produccion'
    return m


def multiplicador_demanda(L: pd.DataFrame) -> pd.Series:
    """
    Multiplicador de demanda (forward linkage / Ghosh).
    m_i = sum_j L_ij  (suma de fila i de la inversa de Leontief)

    Mide la importancia sistémica del sector i como proveedor.
    """
    m = L.sum(axis=1)
    m.name = 'mult_demanda'
    return m


def multiplicador_valor_agregado(L: pd.DataFrame,
                                 W_total: pd.Series,
                                 g: pd.Series) -> pd.Series:
    """
    Multiplicador de valor agregado.
    f_va[j] = W_total[j] / g[j]   (coeficiente de VA por unidad de producción)
    m_va[j] = f_va @ L[:,j]       (vector fila × columna j de L)
    """
    g_safe = g.copy()
    g_safe[g_safe == 0] = 1
    f_va = W_total / g_safe
    f_va = f_va.reindex(L.index).fillna(0)

    m_va = pd.Series(f_va.values @ L.values, index=L.columns, name='mult_va')
    return m_va


def multiplicador_empleo(L: pd.DataFrame,
                         empleo: pd.DataFrame,
                         g: pd.Series) -> pd.DataFrame:
    """
    Multiplicadores de empleo.

    empleo : DataFrame (n_ind × n_categorias)
              Cada columna es una categoría (total, hombre, mujer, urbano, rural, etc.)
              Valores = número de personas empleadas por industria.
    g      : producción bruta por industria.

    Retorna DataFrame (n_ind × n_categorias) con multiplicadores de empleo:
        m_emp[j, cat] = f_emp[cat] @ L[:,j]

    Donde f_emp[i, cat] = empleo[i, cat] / g[i]
    """
    g_safe = g.copy()
    g_safe[g_safe == 0] = 1

    # Coeficientes de empleo directo
    F_emp = empleo.div(g_safe, axis=0)     # n_ind × n_cat
    F_emp = F_emp.reindex(L.index).fillna(0)

    # Multiplicadores: F_emp.T @ L
    M_emp_arr = F_emp.values.T @ L.values  # n_cat × n_ind
    M_emp = pd.DataFrame(
        M_emp_arr.T,
        index=L.columns,
        columns=empleo.columns
    )
    return M_emp


def multiplicador_emisiones(L: pd.DataFrame,
                            emisiones: pd.Series,
                            g: pd.Series) -> pd.Series:
    """
    Multiplicadores de emisiones (CO₂ u otro contaminante).

    emisiones : Series (n_ind,) — emisiones totales por industria
    g         : producción bruta por industria

    Retorna vector de multiplicadores de emisiones m_CO2:
        f_E[i]    = emisiones[i] / g[i]   (intensidad directa)
        m_CO2[j]  = f_E @ L[:,j]          (toneladas por unidad de demanda final del sector j)
    """
    g_safe = g.copy()
    g_safe[g_safe == 0] = 1
    f_E = (emisiones.reindex(L.index).fillna(0)) / g_safe
    m_co2 = pd.Series(f_E.values @ L.values, index=L.columns, name='mult_emisiones')
    return m_co2


def tabla_multiplicadores_completa(L: pd.DataFrame,
                                   g: pd.Series,
                                   W_total: Optional[pd.Series] = None,
                                   empleo: Optional[pd.DataFrame] = None,
                                   emisiones: Optional[pd.Series] = None) -> pd.DataFrame:
    """
    Construye tabla resumen con todos los multiplicadores disponibles.

    Retorna DataFrame con índice = sectores y columnas = multiplicadores.
    """
    resultados = {}

    resultados['mult_produccion'] = multiplicador_produccion(L)
    resultados['mult_demanda']    = multiplicador_demanda(L)

    if W_total is not None:
        resultados['mult_va'] = multiplicador_valor_agregado(L, W_total, g)

    tabla = pd.DataFrame(resultados)

    if empleo is not None:
        M_emp = multiplicador_empleo(L, empleo, g)
        for col in M_emp.columns:
            tabla[f'emp_{col}'] = M_emp[col]

    if emisiones is not None:
        tabla['mult_emisiones'] = multiplicador_emisiones(L, emisiones, g)

    return tabla


def clasificar_sectores(tabla: pd.DataFrame,
                        col_prod: str = 'mult_produccion',
                        col_dem: str  = 'mult_demanda') -> pd.Series:
    """
    Clasificación de Rasmussen (1956) / Hirschman:
        - Sector clave    : mult_prod > media  Y  mult_dem > media
        - Motor (impulsor): mult_prod > media  Y  mult_dem <= media
        - Base (estratégico): mult_prod <= media Y  mult_dem > media
        - Isla           : mult_prod <= media  Y  mult_dem <= media

    Retorna Series con la clasificación de cada sector.
    """
    media_prod = tabla[col_prod].mean()
    media_dem  = tabla[col_dem].mean()

    condiciones = [
        (tabla[col_prod] > media_prod) & (tabla[col_dem] > media_prod),
        (tabla[col_prod] > media_prod) & (tabla[col_dem] <= media_dem),
        (tabla[col_prod] <= media_prod) & (tabla[col_dem] > media_dem),
        (tabla[col_prod] <= media_prod) & (tabla[col_dem] <= media_dem),
    ]
    etiquetas = ['Clave', 'Motor', 'Base', 'Isla']

    clasificacion = pd.Series('Isla', index=tabla.index, name='clasificacion')
    for cond, etiq in zip(condiciones, etiquetas):
        clasificacion[cond] = etiq
    return clasificacion
