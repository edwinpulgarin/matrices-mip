"""
Balanceo del SUT  (UN Handbook, Cap. 11).

Ajuste biproporcional (RAS) del bloque de utilización completo [U | Y] para
cerrar simultáneamente:

    balance producto : Σ_uso(p) = oferta(p) = Σ_i V[i,p] + M[p]
    balance industria: Σ_p U[p,j] = g_j − VA_j   (consumo intermedio de la ind.)

Se mantienen fijos V (oferta) y VA (valor agregado); se ajustan las celdas de
uso intermedio U y de demanda final Y. La demanda final es, en la práctica del
Handbook, la variable con más margen de ajuste.

Precondición macro (SUT bien valorado, Cap. 7):
    Σ oferta = Σ(g − VA) + Σ Y_col   ⟺   Σ Y_col = Σ VA + Σ M
Si hay un residuo pequeño, se absorbe escalando los totales de columna de la
demanda final (queda registrado en el reporte).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .sut import SUT


def ras(A0: np.ndarray, u: np.ndarray, v: np.ndarray,
        max_iter: int = 1000, tol: float = 1e-10) -> tuple[np.ndarray, int]:
    """Ajuste biproporcional: filas -> u, columnas -> v. Devuelve (A, iters)."""
    su, sv = float(u.sum()), float(v.sum())
    if not np.isclose(su, sv, rtol=1e-9, atol=1e-6):
        raise ValueError(f"RAS: Σfilas ({su:.4f}) ≠ Σcolumnas ({sv:.4f})")
    A = A0.astype(float).copy()
    it = 0
    for it in range(1, max_iter + 1):
        rs = A.sum(axis=1); rs[rs == 0] = 1.0
        A = (A.T * (u / rs)).T
        cs = A.sum(axis=0); cs[cs == 0] = 1.0
        A = A * (v / cs)
        if (np.abs(A.sum(axis=1) - u).max() < tol and
                np.abs(A.sum(axis=0) - v).max() < tol):
            break
    return A, it


def balancear(sut: SUT, tol_rel: float = 1e-9, verbose: bool = False) -> tuple[SUT, dict]:
    """Devuelve (SUT balanceado, reporte)."""
    ind = sut.industrias
    prod = sut.productos
    fd_cols = sut.Y.columns.tolist()
    n_ind = len(ind)

    V = sut.V.reindex(index=ind, columns=prod).fillna(0)
    U = sut.U.reindex(index=prod, columns=ind).fillna(0)
    Y = sut.Y.reindex(index=prod, columns=fd_cols).fillna(0)
    VA = sut.VA.reindex(columns=ind).fillna(0)
    M = (sut.M.reindex(prod).fillna(0) if sut.M is not None
         else pd.Series(0.0, index=prod))

    # márgenes objetivo
    oferta = V.sum(axis=0) + M                       # fila (por producto)
    interm_col = (V.sum(axis=1) - VA.sum(axis=0)).reindex(ind).fillna(0)  # g − VA
    fd_col = Y.sum(axis=0)                            # totales demanda final

    # consistencia macro de márgenes
    total_fila = float(oferta.sum())
    total_col = float(interm_col.sum() + fd_col.sum())
    residuo = total_fila - total_col
    if abs(residuo) > tol_rel * max(total_fila, 1.0):
        # absorber el residuo escalando los totales de demanda final
        escala = (total_fila - interm_col.sum()) / fd_col.sum() if fd_col.sum() != 0 else 1.0
        fd_col = fd_col * escala
    col_margins = np.concatenate([interm_col.to_numpy(), fd_col.to_numpy()])

    W0 = np.hstack([U.to_numpy(), Y.to_numpy()])     # (n_prod × (n_ind + n_fd))
    W, iters = ras(W0, oferta.to_numpy(), col_margins, tol=tol_rel)

    U_bal = pd.DataFrame(W[:, :n_ind], index=prod, columns=ind)
    Y_bal = pd.DataFrame(W[:, n_ind:], index=prod, columns=fd_cols)

    sut_bal = SUT(V=V, U=U_bal, Y=Y_bal, VA=VA, M=(M if sut.M is not None else None),
                  pais=sut.pais, anio=sut.anio, unidad=sut.unidad,
                  valoracion="básicos", meta=dict(sut.meta))

    rep = {
        "iteraciones_ras": iters,
        "residuo_margenes_abs": float(residuo),
        "residuo_margenes_rel": float(residuo / max(total_fila, 1.0)),
        "balance_previo": sut.resumen_balance(),
        "balance_post": sut_bal.resumen_balance(),
    }
    if verbose:
        print(f"  [balanceo] RAS {iters} iter; residuo margen "
              f"{rep['residuo_margenes_rel']:.2e}; "
              f"balanceado={rep['balance_post']['balanceado']}")
    return sut_bal, rep
