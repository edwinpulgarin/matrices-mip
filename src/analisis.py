"""
Análisis insumo-producto sobre una IOT simétrica (UN Handbook, Cap. 20).

    A = Z · x̂⁻¹                coeficientes técnicos
    L = (I − A)⁻¹              inversa de Leontief
    multiplicadores de producción (encadenamiento hacia atrás) = Σ_i L[i,j]

Identidad de verificación:  L · f = x

Encadenamientos de Rasmussen (Cap. 20.C)
----------------------------------------
Se normalizan las sumas de L por su media global, de modo que 1 es el promedio
de la economía:

    BL_j = (Σ_i L[i,j] / n) / (ΣΣ L / n²)   poder de dispersión (hacia atrás)
    FL_i = (Σ_j L[i,j] / n) / (ΣΣ L / n²)   sensibilidad de dispersión (adelante)

BL alto = el sector arrastra a sus proveedores cuando crece su demanda.
FL alto = el sector es empujado cuando crece la demanda del resto.
El cruce de ambos con el umbral 1 clasifica en cuatro tipos (`clasificar`).

Dispersión de Rasmussen (V_j)
-----------------------------
Un BL alto puede venir de arrastrar mucho a UN solo proveedor o de arrastrar un
poco a todos. El coeficiente de variación de la columna distingue los dos casos:

    V_j = sd_i(L[i,j]) / media_i(L[i,j])

V_j bajo = el arrastre se reparte por toda la economía. Un sector con BL alto y
V_j bajo es el candidato genuino a "clave" en el sentido de política: estimularlo
mueve muchos sectores, no uno.

Descomposición del multiplicador (Cap. 20.B)
--------------------------------------------
El multiplicador de producción se abre en tres tramos que suman exactamente:

    1                        efecto inicial: producir el peso que se demanda
    Σ_i A[i,j]               efecto directo: lo que ese sector compra a otros
    Σ_i L[i,j] − 1 − Σ_i A   efecto indirecto: las vueltas siguientes

El reparto entre directo e indirecto distingue dos economías con el mismo
multiplicador: una cadena corta y ancha (mucho directo) de una larga y entrelazada
(mucho indirecto), que son problemas de política distintos.

Nota sobre multiplicadores de valor agregado
--------------------------------------------
NO se calculan aquí. Con estas fuentes el VA se obtiene por identidad
(va = x − Σ_i Z[i,j]), de modo que v' = i'(I−A) y por lo tanto v'L ≡ i': el
"multiplicador de VA" daría 1 en todos los sectores de todos los países, que es
una identidad contable y no un resultado. Calcularlo requeriría la fila de
remuneraciones separada, que ninguna de las cinco fuentes publica dentro del COU
utilizado.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .transformacion import IOT

# BL / FL frente al umbral 1
TIPOS = {
    (True, True): "Clave",
    (True, False): "Demandante",
    (False, True): "Distribuidor",
    (False, False): "Independiente",
}


@dataclass
class Analisis:
    A: pd.DataFrame
    L: pd.DataFrame
    mult_produccion: pd.Series      # Σ columna de L
    check_Lf_x: float               # max |L·f − x|
    bl: pd.Series = None            # encadenamiento hacia atrás, normalizado
    fl: pd.Series = None            # encadenamiento hacia adelante, normalizado
    vj: pd.Series = None            # dispersión del arrastre (CV de la columna de L)
    mult_directo: pd.Series = None  # Σ columna de A (primera vuelta)

    @property
    def mult_indirecto(self) -> pd.Series:
        """Las vueltas posteriores a la primera: L − 1 − A, por columna."""
        return (self.mult_produccion - 1.0 - self.mult_directo).rename("mult_indirecto")

    def clasificar(self) -> pd.Series:
        """Tipo de sector según el cruce BL/FL con el umbral 1."""
        return pd.Series(
            [TIPOS[(b > 1, f > 1)] for b, f in zip(self.bl, self.fl)],
            index=self.bl.index, name="tipo")

    def mult_medio_ponderado(self, pesos: pd.Series) -> float:
        """Multiplicador medio ponderado por `pesos` (p. ej. demanda final).

        El promedio simple trata igual a un sector marginal y a uno que es el
        10 % de la economía; ponderado responde a "cuánto se mueve el país si
        la demanda crece como está repartida hoy".
        """
        w = pesos.reindex(self.mult_produccion.index).fillna(0.0).clip(lower=0)
        tot = float(w.sum())
        if tot == 0:
            return float(self.mult_produccion.mean())
        return float((self.mult_produccion * w).sum() / tot)


def calcular(iot: IOT) -> Analisis:
    sectores = iot.Z.index.tolist()
    x = iot.x.reindex(sectores).to_numpy(dtype=float)
    x_safe = x.copy()
    x_safe[x_safe == 0] = 1.0

    A_arr = iot.Z.to_numpy() / x_safe[np.newaxis, :]
    n = len(sectores)
    ImA = np.eye(n) - A_arr
    try:
        L_arr = np.linalg.inv(ImA)
    except np.linalg.LinAlgError:
        L_arr = np.linalg.pinv(ImA)

    A = pd.DataFrame(A_arr, index=sectores, columns=sectores)
    L = pd.DataFrame(L_arr, index=sectores, columns=sectores)

    f = iot.f.reindex(sectores).to_numpy(dtype=float)
    check = float(np.abs(L_arr @ f - x).max())

    mult = pd.Series(L_arr.sum(axis=0), index=sectores, name="mult_produccion")

    # Rasmussen: la media global de L es el denominador común de ambos índices,
    # así que 1 significa "igual al promedio de la economía".
    media = L_arr.mean()
    den = media if media != 0 else 1.0
    bl = pd.Series(L_arr.mean(axis=0) / den, index=sectores, name="BL")
    fl = pd.Series(L_arr.mean(axis=1) / den, index=sectores, name="FL")

    # V_j separa "arrastra a todos un poco" de "arrastra mucho a uno solo".
    col_media = L_arr.mean(axis=0)
    col_media_safe = np.where(col_media == 0, 1.0, col_media)
    vj = pd.Series(L_arr.std(axis=0, ddof=1) / col_media_safe, index=sectores, name="Vj")

    mult_dir = pd.Series(A_arr.sum(axis=0), index=sectores, name="mult_directo")

    return Analisis(A, L, mult, check, bl, fl, vj, mult_dir)
