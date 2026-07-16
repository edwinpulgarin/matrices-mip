"""
Transformación SUT balanceado -> IOT simétrica  (UN Handbook, Cap. 12).

Se implementan los dos modelos que NO generan elementos negativos:

    Modelo D  industria×industria, estructura fija de ventas de producto
              D = V·q̂⁻¹        (participación de mercado, ind×prod)
              Z = D · U         (ind×ind)
    Modelo B  producto×producto, supuesto de tecnología de industria
              Z = U · ĝ⁻¹ · V   (prod×prod)

Los modelos A (tecnología de producto) y C (estructura fija de ventas de
industria) se descartan porque requieren invertir una matriz de
transformación y pueden producir negativos (Cap. 12, Anexo B).

La entrada debe ser un SUT YA BALANCEADO y a precios básicos (Cap. 7 y 11);
en caso contrario los balances de la IOT resultante no cerrarán.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .sut import SUT


@dataclass
class IOT:
    """Matriz Insumo-Producto simétrica resultante."""

    modelo: str                 # "D" (ind×ind) | "B" (prod×prod)
    Z: pd.DataFrame             # flujos intermedios (n × n)
    x: pd.Series                # producción bruta por sector (n,)
    f: pd.Series                # demanda final total por sector (n,)
    va: pd.Series               # valor agregado por sector (n,)
    Y: pd.DataFrame             # demanda final desagregada (n × n_fd)
    VA: pd.DataFrame            # valor agregado desagregado (n_va × n)

    # balances por construcción
    def balance_fila_columna(self) -> pd.Series:
        """(Σfila Z + f) − (Σcol Z + va)  por sector; 0 = cuadra."""
        fila = self.Z.sum(axis=1) + self.f
        col = self.Z.sum(axis=0) + self.va
        return fila - col

    def min_valor(self) -> float:
        return float(min(self.Z.values.min(), self.va.min()))


def _diag_inv(v: pd.Series) -> np.ndarray:
    d = v.to_numpy(dtype=float).copy()
    d[d == 0] = 1.0
    return 1.0 / d


def modelo_D(sut: SUT) -> IOT:
    """Industria×industria, estructura fija de ventas de producto (Z = D·U)."""
    ind = sut.industrias
    q = sut.q                                   # producción por producto
    g = sut.g                                   # producción por industria

    D = sut.V.mul(pd.Series(_diag_inv(q), index=sut.productos), axis=1)  # ind×prod
    Z = pd.DataFrame(D.to_numpy() @ sut.U.to_numpy(), index=ind, columns=ind)

    # demanda final por industria: f = D · (Σ Y por producto)
    y_prod = sut.Y.sum(axis=1).reindex(sut.productos).fillna(0)
    f = pd.Series(D.to_numpy() @ y_prod.to_numpy(), index=ind, name="demanda_final")
    Y_ind = pd.DataFrame(D.to_numpy() @ sut.Y.reindex(sut.productos).fillna(0).to_numpy(),
                         index=ind, columns=sut.Y.columns)

    # VA por industria queda intacto (ya está en espacio de industrias)
    VA_ind = sut.VA.reindex(columns=ind).fillna(0)
    va = VA_ind.sum(axis=0)
    va.name = "valor_agregado"

    return IOT("D", Z, g.rename("produccion"), f, va, Y_ind, VA_ind)


def modelo_B(sut: SUT) -> IOT:
    """Producto×producto, supuesto de tecnología de industria (Z = U·ĝ⁻¹·V)."""
    prod = sut.productos
    q = sut.q
    g = sut.g

    Ug = sut.U.mul(pd.Series(_diag_inv(g), index=sut.industrias), axis=1)  # prod×ind
    Z = pd.DataFrame(Ug.to_numpy() @ sut.V.to_numpy(), index=prod, columns=prod)

    # demanda final se mantiene en espacio de productos
    Y_prod = sut.Y.reindex(prod).fillna(0)
    f = Y_prod.sum(axis=1)
    f.name = "demanda_final"

    # VA por producto: transformar VA de industrias a productos vía market share
    # W_prod = W · ĝ⁻¹ · V  (misma transformación de tecnología de industria)
    VA_g = sut.VA.mul(pd.Series(_diag_inv(g), index=sut.industrias), axis=1)  # va×ind
    VA_prod = pd.DataFrame(VA_g.to_numpy() @ sut.V.to_numpy(),
                           index=sut.VA.index, columns=prod)
    va = VA_prod.sum(axis=0)
    va.name = "valor_agregado"

    return IOT("B", Z, q.rename("produccion"), f, va, Y_prod, VA_prod)


def transformar(sut: SUT, modelo: str = "D") -> IOT:
    modelo = modelo.upper()
    if modelo == "D":
        return modelo_D(sut)
    if modelo == "B":
        return modelo_B(sut)
    raise ValueError(f"Modelo no soportado: {modelo!r} (use 'D' o 'B')")
