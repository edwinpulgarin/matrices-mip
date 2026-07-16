"""
Estructura canónica de un Cuadro de Oferta y Utilización (SUT) y sus
identidades contables básicas (UN Handbook, Cap. 2).

Convención de dimensiones y orientación (idéntica a MIP V2/src/cou_to_mip.py
para poder reutilizar el motor):

    n_ind  = número de industrias (actividades)
    n_prod = número de productos
    V   : oferta/producción   (n_ind  × n_prod)  filas=industrias, cols=productos
    U   : utilización interm.  (n_prod × n_ind )  filas=productos,  cols=industrias
    Y   : demanda final        (n_prod × n_fd  )
    VA  : valor agregado        (n_va   × n_ind )  componentes × industrias
    M   : importaciones         (n_prod,)          por producto (opcional)

Identidades (a precios básicos):
    Oferta por producto : q_p = Σ_i V[i,p] + M[p]
    Uso por producto    : Σ_j U[p,j] + Σ Y[p,·]
    -> balance producto : oferta_p == uso_p
    Producción industria: g_j = Σ_i V[j,i]            (fila de V)
    Costo industria     : Σ_p U[p,j] + Σ_va VA[·,j]
    -> balance industria: g_j == costo_j
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class SUT:
    """Cuadro de Oferta y Utilización con nombres de fila/columna."""

    V: pd.DataFrame                       # (n_ind × n_prod)  oferta
    U: pd.DataFrame                       # (n_prod × n_ind)  uso intermedio
    Y: pd.DataFrame                       # (n_prod × n_fd)   demanda final
    VA: pd.DataFrame                      # (n_va × n_ind)    valor agregado
    M: Optional[pd.Series] = None         # (n_prod,)         importaciones
    pais: str = ""
    anio: int = 0
    unidad: str = ""                      # p.ej. "miles de millones de pesos corrientes"
    valoracion: str = "básicos"           # "básicos" | "comprador"
    meta: dict = field(default_factory=dict)

    # ── accesores derivados ───────────────────────────────────────────────
    @property
    def industrias(self) -> list:
        return self.V.index.tolist()

    @property
    def productos(self) -> list:
        return self.V.columns.tolist()

    @property
    def g(self) -> pd.Series:
        """Producción bruta por industria (suma de filas de V)."""
        return self.V.sum(axis=1)

    @property
    def q(self) -> pd.Series:
        """Producción bruta por producto (suma de columnas de V)."""
        return self.V.sum(axis=0)

    # ── identidades contables ─────────────────────────────────────────────
    def balance_producto(self) -> pd.Series:
        """oferta_p − uso_p por producto (0 = balanceado)."""
        prod = self.productos
        prod_interna = self.V.sum(axis=0)
        imp = (self.M.reindex(prod).fillna(0) if self.M is not None
               else pd.Series(0.0, index=prod))
        oferta = prod_interna + imp
        uso = (self.U.sum(axis=1).reindex(prod).fillna(0)
               + self.Y.sum(axis=1).reindex(prod).fillna(0))
        return oferta - uso

    def balance_industria(self) -> pd.Series:
        """producción_j − costo_j por industria (0 = balanceado)."""
        ind = self.industrias
        g = self.g
        costo = (self.U.sum(axis=0).reindex(ind).fillna(0)
                 + self.VA.sum(axis=0).reindex(ind).fillna(0))
        return g - costo

    def resumen_balance(self, tol_rel: float = 1e-6) -> dict:
        bp = self.balance_producto()
        bi = self.balance_industria()
        q = self.q.replace(0, np.nan)
        g = self.g.replace(0, np.nan)
        return {
            "max_abs_producto": float(bp.abs().max()),
            "max_rel_producto": float((bp.abs() / q).max(skipna=True)),
            "max_abs_industria": float(bi.abs().max()),
            "max_rel_industria": float((bi.abs() / g).max(skipna=True)),
            "balanceado": bool(
                (bp.abs() / q).max(skipna=True) < tol_rel
                and (bi.abs() / g).max(skipna=True) < tol_rel
            ),
        }
