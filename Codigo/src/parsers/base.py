"""
Clase base y utilidades compartidas por todos los parsers de COU.
"""

import re
import numpy as np
import pandas as pd
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class COU:
    """
    Contenedor estándar para un Cuadro de Oferta y Utilización.

    Todas las tablas en millones de moneda local (o la unidad que use la fuente).

    Atributos
    ---------
    pais    : str           — 'argentina', 'brasil', 'mexico', 'uruguay'
    anio    : int           — año de la tabla
    moneda  : str           — ej. 'ARS', 'BRL', 'MXN', 'UYU'
    unidad  : str           — ej. 'millones', 'miles de millones'

    V       : DataFrame  (n_ind × n_prod)   — tabla de oferta/producción
    U       : DataFrame  (n_prod × n_ind)   — tabla de utilización intermedia
    Y       : DataFrame  (n_prod × n_fd)    — demanda final (cols = componentes)
    W       : DataFrame  (n_va × n_ind)     — valor agregado (filas = componentes)
    M       : Series     (n_prod,)          — importaciones (opcional)
    T       : Series     (n_prod,)          — márgenes de comercio y transporte (opcional)
    imp_ind : Series     (n_prod,)          — impuestos netos sobre productos (opcional)
    U_importada : DataFrame (n_prod × n_ind) — utilización intermedia importada (opcional)
    empleo  : DataFrame (n_ind × categorias) — vector de trabajo/ocupaciones (opcional)

    industrias : list[str]   — nombres de industrias
    productos  : list[str]   — nombres de productos
    """
    pais      : str
    anio      : int
    moneda    : str = ''
    unidad    : str = 'millones'

    V         : Optional[pd.DataFrame] = None
    U         : Optional[pd.DataFrame] = None
    Y         : Optional[pd.DataFrame] = None
    W         : Optional[pd.DataFrame] = None
    M         : Optional[pd.Series]    = None
    T         : Optional[pd.Series]    = None
    imp_ind   : Optional[pd.Series]    = None
    U_importada: Optional[pd.DataFrame] = None
    empleo    : Optional[pd.DataFrame] = None

    notas     : list = field(default_factory=list)

    @property
    def industrias(self):
        return list(self.V.index) if self.V is not None else []

    @property
    def productos(self):
        return list(self.V.columns) if self.V is not None else []

    @property
    def n_ind(self):
        return len(self.industrias)

    @property
    def n_prod(self):
        return len(self.productos)

    def resumen(self):
        print(f"COU {self.pais.upper()} {self.anio}")
        print(f"  Industrias : {self.n_ind}")
        print(f"  Productos  : {self.n_prod}")
        if self.V is not None:
            print(f"  V shape    : {self.V.shape}")
        if self.U is not None:
            print(f"  U shape    : {self.U.shape}")
        if self.Y is not None:
            print(f"  Y shape    : {self.Y.shape}  cols={list(self.Y.columns)}")
        if self.W is not None:
            print(f"  W shape    : {self.W.shape}  filas={list(self.W.index)}")
        if self.M is not None:
            print(f"  M total    : {self.M.sum():,.0f} {self.moneda} {self.unidad}")
        prod_total = self.V.sum().sum() if self.V is not None else 0
        print(f"  Producción total: {prod_total:,.0f} {self.moneda} {self.unidad}")


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades genéricas
# ─────────────────────────────────────────────────────────────────────────────

def limpiar_nombre(s: str) -> str:
    """Limpia un nombre de sector: elimina códigos al inicio, espacios extra."""
    if not isinstance(s, str):
        return str(s)
    # Eliminar códigos tipo "A01", "01", "A01.1" al inicio
    s = re.sub(r'^[A-Z]?\d+[\.\d]*\s*[-–—]\s*', '', s.strip())
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def leer_bloque_numerico(df: pd.DataFrame,
                         fila_inicio: int,
                         fila_fin: int,
                         col_inicio: int,
                         col_fin: int) -> np.ndarray:
    """
    Extrae un bloque rectangular del DataFrame como array numérico.
    Reemplaza valores no numéricos con 0.
    """
    bloque = df.iloc[fila_inicio:fila_fin, col_inicio:col_fin]
    return pd.to_numeric(bloque.stack(), errors='coerce').unstack().fillna(0).values


def encontrar_fila(df: pd.DataFrame,
                   patron: str,
                   col: int = 0,
                   desde: int = 0) -> Optional[int]:
    """
    Busca la primera fila (desde 'desde') donde la celda [fila, col]
    contiene el patrón (case-insensitive). Retorna None si no encuentra.
    """
    for i in range(desde, len(df)):
        celda = str(df.iloc[i, col]).strip().lower()
        if patron.lower() in celda:
            return i
    return None


def encontrar_columna(df: pd.DataFrame,
                      patron: str,
                      fila: int = 0) -> Optional[int]:
    """
    Busca la primera columna donde la celda [fila, col] contiene el patrón.
    """
    for j in range(len(df.columns)):
        celda = str(df.iloc[fila, j]).strip().lower()
        if patron.lower() in celda:
            return j
    return None


def coerce_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte todas las celdas a numérico, rellenando NaN con 0."""
    return df.apply(pd.to_numeric, errors='coerce').fillna(0)
