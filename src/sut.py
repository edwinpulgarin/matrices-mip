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

    def a_total(self) -> "SUT":
        """Devuelve el mismo SUT en su versión TOTAL (nacional + importado).

        La MIP doméstica trata al insumo importado como un primario exógeno: sale
        de las celdas de `U` y va a la fila «consumo intermedio importado». La MIP
        total lo deja adentro, endógeno, que es como publican su matriz el DANE
        (Cuadro 7) y el INDEC (MIPAr97, cuadro 12).

        La conversión no supone nada: `U_dom + U_imp` devuelve exactamente la
        utilización valorada a precios básicos ANTES del corte por origen, así que
        el supuesto de proporcionalidad de las importaciones (Cap. 8, §8.33) —el
        que mide +5,65 % de sesgo en los multiplicadores de México— desaparece del
        resultado. Es la razón por la que esta versión se puede publicar para los
        cinco países aunque sólo tres midan el origen.

        Las importaciones pasan a la oferta (`M`, por producto), de donde salen
        para cerrar el balance de fila: producción + importaciones = usos.
        """
        U_imp = self.meta.get("U_imp")
        Y_imp = self.meta.get("Y_imp")
        if U_imp is None or Y_imp is None:
            raise ValueError(
                "el SUT no trae la utilización ni la demanda final importadas en "
                "`meta`; sin ellas la versión total no es reconstruible")
        U_imp = U_imp.reindex(index=self.U.index, columns=self.U.columns).fillna(0.0)
        Y_imp = Y_imp.reindex(index=self.Y.index).fillna(0.0)
        # La demanda final importada puede traer menos columnas que la doméstica
        # (Colombia mide consumo y formación de capital, no exportaciones de
        # producto importado): se alinean por nombre y lo que falta entra en cero.
        Y_imp = Y_imp.reindex(columns=self.Y.columns).fillna(0.0)

        # Las importaciones por producto son las que DECLARA la fuente, no las
        # que se deducen del corte por origen. La identidad de la versión total
        # lo obliga: como `U_dom + U_imp = U` cualquiera sea el reparto, el
        # balance exige `M = importaciones + ajuste CIF/FOB` exacto.
        #
        # Deducirlas del corte fallaba donde el reparto tiene un tope: el INDEC
        # imputa el ajuste CIF/FOB al flete aéreo, y en 2018 eso deja al producto
        # con importaciones NETAS NEGATIVAS (7.513.861 − 12.050.618). La
        # participación doméstica salía 2,44, se recortaba a 1, y el producto
        # entraba desbalanceado en el 59 % de su oferta. Lo absorbía el RAS.
        M = self.meta.get("M_prod")
        M = (M.reindex(self.U.index).fillna(0.0) if M is not None
             else U_imp.sum(axis=1) + Y_imp.sum(axis=1))

        VA = self.VA.drop(index="consumo_intermedio_importado", errors="ignore")
        meta = dict(self.meta)
        meta["alcance"] = "total"
        return SUT(V=self.V, U=self.U + U_imp, Y=self.Y + Y_imp, VA=VA, M=M,
                   pais=self.pais, anio=self.anio, unidad=self.unidad,
                   valoracion=self.valoracion, meta=meta)

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
