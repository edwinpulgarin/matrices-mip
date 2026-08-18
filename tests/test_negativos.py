"""
Test de los negativos que publican las fuentes (variación de existencias).

Un COU oficial puede traer celdas negativas —desacumulación de stock— y borrarlas
es inventar dato. Pero el RAS es multiplicativo y sólo está definido sobre celdas
no negativas (Handbook, Box 11.3), así que el balanceo las aparta y las conserva.

Verifica que:
  - la celda negativa llega al SUT balanceado con su valor EXACTO,
  - el balanceo cierra igual las dos identidades,
  - una columna cuya única celda es negativa no rompe el ajuste — ése fue el caso
    de «objetos valiosos» en Argentina 2019, que dejaba un residuo de 26 sobre
    2.285.674.161 repartido por las filas más grandes.
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


def _assert(cond, msg):
    print(("  OK  " if cond else " FAIL ") + msg)
    assert cond, msg


def sut_con_negativo(desbalancear: bool = True) -> SUT:
    """SUT de 2×2 con variación de existencias negativa en un producto.

    La columna `objetos_valiosos` tiene una sola celda y es negativa: reproduce
    en chico la que hacía fallar a Argentina 2019.
    """
    ind = ["I1", "I2"]
    prod = ["P1", "P2"]
    V = pd.DataFrame([[80.0, 20.0], [10.0, 90.0]], index=ind, columns=prod)
    U = pd.DataFrame([[30.0, 40.0], [20.0, 25.0]], index=prod, columns=ind)
    Y = pd.DataFrame([[25.0, -5.0, 0.0], [70.0, 0.0, -5.0]],
                     index=prod, columns=["consumo", "var_existencias", "objetos_valiosos"])
    VA = pd.DataFrame([[50.0, 35.0]], index=["valor_agregado"], columns=ind)
    s = SUT(V=V, U=U, Y=Y, VA=VA, pais="TEST", anio=2000, unidad="u")
    if desbalancear:
        s.U.iloc[0, 0] *= 1.4
        s.U.iloc[1, 1] *= 0.6
    return s


def main():
    s = sut_con_negativo()
    neg_antes = s.Y[s.Y < 0].stack().to_dict()
    _assert(len(neg_antes) == 2, f"el SUT de prueba entra con 2 negativos ({len(neg_antes)})")

    s_bal, rep = balancear(s)
    _assert(rep["aplicado"], "el balanceo corrió (el SUT entra desbalanceado)")
    _assert(rep["celdas_fijas_negativas"] == 2,
            f"las 2 celdas negativas quedaron fuera del ajuste "
            f"({rep['celdas_fijas_negativas']})")

    neg_despues = s_bal.Y[s_bal.Y < 0].stack().to_dict()
    _assert(set(neg_despues) == set(neg_antes), "los negativos siguen en las mismas celdas")
    _assert(all(np.isclose(neg_despues[k], v, rtol=0, atol=1e-12)
                for k, v in neg_antes.items()),
            "conservan su valor EXACTO: el RAS no los tocó")

    b = s_bal.resumen_balance()
    _assert(b["balanceado"],
            f"las identidades cierran igual (producto {b['max_rel_producto']:.1e}, "
            f"industria {b['max_rel_industria']:.1e})")
    _assert(b["max_rel_producto"] < 1e-12,
            f"y cierran hasta la doble precisión, no «casi» ({b['max_rel_producto']:.1e})")

    # el negativo es de demanda final: no debe aparecer en la MIP
    iot = transformar(s_bal, "D")
    _assert(iot.Z.to_numpy().min() >= -1e-12,
            f"Z sigue sin negativos ({iot.Z.to_numpy().min():.2e})")

    # y el SUT que ya está balanceado no se toca aunque traiga negativos
    s2 = sut_con_negativo(desbalancear=False)
    s2_bal, rep2 = balancear(s2)
    _assert(not rep2["aplicado"], "un SUT con negativos que ya cuadra no se ajusta")
    _assert(np.allclose(s2.Y.to_numpy(), s2_bal.Y.to_numpy(), atol=1e-12),
            "y su demanda final vuelve idéntica")

    print("\nTODOS LOS TESTS PASARON")


if __name__ == "__main__":
    main()
