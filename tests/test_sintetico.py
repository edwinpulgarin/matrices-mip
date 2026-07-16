"""
Test de identidades sobre un SUT sintético balanceado de dimensiones conocidas.

Verifica que:
  - un SUT ya balanceado atraviesa el balanceo sin alterarse,
  - un SUT desbalanceado queda balanceado tras RAS,
  - la transformación (Modelo D y B) preserva fila=columna, sin negativos,
  - la inversa de Leontief cumple L·f = x.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.sut import SUT
from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular


def sut_balanceado() -> SUT:
    ind = ["I1", "I2"]
    prod = ["P1", "P2"]
    V = pd.DataFrame([[80.0, 20.0], [10.0, 90.0]], index=ind, columns=prod)   # ind×prod
    U = pd.DataFrame([[30.0, 40.0], [20.0, 25.0]], index=prod, columns=ind)   # prod×ind
    Y = pd.DataFrame([[20.0], [65.0]], index=prod, columns=["dem_final"])
    VA = pd.DataFrame([[50.0, 35.0]], index=["valor_agregado"], columns=ind)
    return SUT(V=V, U=U, Y=Y, VA=VA, pais="TEST", anio=2000, unidad="u")


def _assert(cond, msg):
    print(("  OK  " if cond else " FAIL ") + msg)
    assert cond, msg


def main():
    s = sut_balanceado()
    rb = s.resumen_balance()
    _assert(rb["balanceado"], f"SUT sintético parte balanceado ({rb['max_rel_producto']:.1e})")

    # balanceo idempotente sobre SUT ya balanceado
    s_bal, rep = balancear(s)
    _assert(s_bal.resumen_balance()["balanceado"], "balanceo mantiene el balance")
    _assert(np.allclose(s.U.values, s_bal.U.values, atol=1e-6),
            "balanceo no altera un SUT ya balanceado")

    # desbalancear U y comprobar que RAS lo cierra
    s2 = sut_balanceado()
    s2.U.iloc[0, 0] *= 1.5
    s2.U.iloc[1, 1] *= 0.5
    _assert(not s2.resumen_balance()["balanceado"], "SUT perturbado queda desbalanceado")
    s2_bal, _ = balancear(s2)
    _assert(s2_bal.resumen_balance()["balanceado"], "RAS cierra el SUT perturbado")

    # transformación + análisis para ambos modelos
    for modelo in ("D", "B"):
        iot = transformar(s_bal, modelo)
        gap = iot.balance_fila_columna().abs().max()
        _assert(gap < 1e-8, f"Modelo {modelo}: fila=columna (gap={gap:.1e})")
        _assert(iot.min_valor() >= -1e-9, f"Modelo {modelo}: sin negativos")
        an = calcular(iot)
        _assert(an.check_Lf_x < 1e-6, f"Modelo {modelo}: L·f = x (err={an.check_Lf_x:.1e})")
        _assert((an.L.values >= -1e-9).all(), f"Modelo {modelo}: L ≥ 0")

    print("\nTODOS LOS TESTS PASARON")


if __name__ == "__main__":
    main()
