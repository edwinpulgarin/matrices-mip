"""
Análisis insumo-producto sobre una IOT simétrica (UN Handbook, Cap. 20).

    A = Z · x̂⁻¹                coeficientes técnicos
    L = (I − A)⁻¹              inversa de Leontief
    multiplicadores de producción (encadenamiento hacia atrás) = Σ_i L[i,j]

Identidad de verificación:  L · f = x
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .transformacion import IOT


@dataclass
class Analisis:
    A: pd.DataFrame
    L: pd.DataFrame
    mult_produccion: pd.Series      # Σ columna de L
    check_Lf_x: float               # max |L·f − x|


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
    return Analisis(A, L, mult, check)
