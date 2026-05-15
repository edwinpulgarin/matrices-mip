"""
Conversión de Cuadros de Oferta y Utilización (COU/SUT) a
Matrices de Insumo-Producto (MIP/IOT) simétricas.

Metodología: Supuesto de Tecnología de Industria (STI / ITA)
Resultado:   MIP Industria × Industria

Referencia:  Eurostat (2008). Eurostat Manual of Supply, Use and
             Input-Output Tables. Cap. 11.
             Miller & Blair (2009). Input-Output Analysis. Cap. 5.

Convenciones de dimensiones:
    n_ind  = número de industrias (actividades)
    n_prod = número de productos
    n_fd   = número de componentes de demanda final
    n_va   = número de filas de valor agregado

Matrices requeridas (como DataFrames con índices/columnas nombrados):
    V   : oferta/producción  (n_ind  × n_prod)  — filas=industrias, cols=productos
    U   : utilización interm. (n_prod × n_ind )  — filas=productos,  cols=industrias
    Y   : demanda final       (n_prod × n_fd  )
    W   : valor agregado      (n_va   × n_ind )
    M   : importaciones       (n_prod × 1     )  — opcional
"""

import numpy as np
import pandas as pd
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# 1. Verificación de coherencia del COU
# ─────────────────────────────────────────────────────────────────────────────

def verificar_balance(V: pd.DataFrame,
                      U: pd.DataFrame,
                      Y: pd.DataFrame,
                      M: Optional[pd.Series] = None,
                      tolerancia: float = 1.0) -> dict:
    """
    Verifica las identidades contables del COU.

    Oferta total por producto  = Utilización total por producto
        q_oferta[p] = V[:,p].sum() + M[p]   (producción interna + importaciones)
        q_uso[p]    = U[p,:].sum() + Y[p,:].sum()

    Retorna dict con:
        'balance_productos' : Series con discrepancia por producto
        'balance_industrias': Series con discrepancia por industria
        'max_discrepancia'  : float
        'balanceado'        : bool
    """
    productos = V.columns
    industrias = V.index

    # Oferta por producto
    prod_interna = V.sum(axis=0)                      # n_prod
    importaciones = M.reindex(productos).fillna(0) if M is not None else pd.Series(0, index=productos)
    oferta_total = prod_interna + importaciones

    # Uso por producto
    uso_intermedio = U.sum(axis=1).reindex(productos).fillna(0)  # n_prod
    demanda_final  = Y.sum(axis=1).reindex(productos).fillna(0)  # n_prod
    uso_total = uso_intermedio + demanda_final

    balance_prod = oferta_total - uso_total

    # Output por industria: producción bruta = sum de columna en U + valor agregado
    # No verificamos esto sin W, solo informamos si se pasa
    resultado = {
        'balance_productos' : balance_prod,
        'max_discrepancia'  : balance_prod.abs().max(),
        'balanceado'        : balance_prod.abs().max() <= tolerancia,
        'oferta_total'      : oferta_total,
        'uso_total'         : uso_total,
    }
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
# 2. Ajuste biproporcional RAS
# ─────────────────────────────────────────────────────────────────────────────

def ras(A0: np.ndarray,
        u: np.ndarray,
        v: np.ndarray,
        max_iter: int = 500,
        tol: float = 1e-8) -> np.ndarray:
    """
    Ajuste biproporcional RAS.

    Ajusta la matriz A0 tal que:
        filas sumen u   (totales de fila objetivo)
        cols  sumen v   (totales de columna objetivo)

    Parámetros
    ----------
    A0      : matriz inicial  (n × m)
    u       : totales de fila objetivo  (n,)
    v       : totales de columna objetivo (m,)
    max_iter: máximo de iteraciones
    tol     : tolerancia de convergencia

    Retorna
    -------
    A ajustada (n × m)
    """
    assert abs(u.sum() - v.sum()) < tol * 1e3, \
        f"Suma de filas ({u.sum():.4f}) ≠ suma de cols ({v.sum():.4f})"

    A = A0.copy().astype(float)
    for _ in range(max_iter):
        # Ajuste de filas
        row_sums = A.sum(axis=1)
        row_sums[row_sums == 0] = 1  # evitar división por cero
        r = u / row_sums
        A = (A.T * r).T

        # Ajuste de columnas
        col_sums = A.sum(axis=0)
        col_sums[col_sums == 0] = 1
        s = v / col_sums
        A = A * s

        # Convergencia
        if (np.abs(A.sum(axis=1) - u).max() < tol and
                np.abs(A.sum(axis=0) - v).max() < tol):
            break
    return A


# ─────────────────────────────────────────────────────────────────────────────
# 3. Conversión SUT → IOT (Supuesto Tecnología de Industria)
# ─────────────────────────────────────────────────────────────────────────────

def sut_a_iot_industria(V: pd.DataFrame,
                        U: pd.DataFrame,
                        Y: pd.DataFrame,
                        W: pd.DataFrame,
                        M: Optional[pd.Series] = None,
                        U_importada: Optional[pd.DataFrame] = None,
                        ajustar_ras: bool = False) -> dict:
    """
    Convierte tablas de Oferta y Utilización a MIP Industria×Industria
    bajo el Supuesto de Tecnología de Industria (STI).

    Derivación:
        D[i,j] = V[i,j] / q[j]           market share (industria i en producto j)
        B[i,j] = U[i,j] / g[j]           coef. de insumos (producto i por industria j)
        Z      = D @ U                    flujos intermedios (n_ind × n_ind)
        A      = D @ B  = Z @ diag(1/g)   coeficientes técnicos
        L      = (I - A)^{-1}             inversa de Leontief

    También construye el vector de demanda final transformado:
        f_ind  = D @ Y.sum(axis=1)        (n_ind,) demanda final por industria

    Parámetros
    ----------
    V  : oferta/producción  (n_ind  × n_prod)
    U  : utilización interm. (n_prod × n_ind)
    Y  : demanda final       (n_prod × n_fd)
    W  : valor agregado      (n_va   × n_ind)
    M  : importaciones por producto (n_prod,) — si None se ignoran
    ajustar_ras : si True aplica RAS para forzar balance exacto

    Retorna dict con:
        'Z'        : DataFrame n_ind × n_ind  — flujos intermedios
        'A'        : DataFrame n_ind × n_ind  — coeficientes técnicos
        'L'        : DataFrame n_ind × n_ind  — inversa de Leontief
        'g'        : Series   n_ind            — producción bruta por industria
        'q'        : Series   n_prod           — producción bruta por producto
        'D'        : DataFrame n_ind × n_prod  — market shares
        'B'        : DataFrame n_prod × n_ind  — coef. de insumos
        'f_ind'    : Series n_ind              — demanda final por industria
        'W_total'  : Series n_ind              — valor agregado total
    """
    industrias = V.index.tolist()
    productos  = V.columns.tolist()

    # ── Totales ──────────────────────────────────────────────────────────────
    g = V.sum(axis=1)          # producción bruta por industria  (n_ind,)
    q = V.sum(axis=0)          # producción bruta por producto   (n_prod,)

    # ── Verificar balance (informativo) ──────────────────────────────────────
    bal = verificar_balance(V, U, Y, M)
    if not bal['balanceado']:
        max_d = bal['max_discrepancia']
        pct   = (bal['balance_productos'].abs() / bal['oferta_total'].clip(1)).max() * 100
        print(f"  [AVISO] Desbalance máximo: {max_d:,.1f} ({pct:.2f}%)")
        if ajustar_ras:
            print("  [INFO]  Aplicando ajuste RAS en tabla de utilización...")
            u_target = q.values - (Y.sum(axis=1).reindex(productos).fillna(0).values)
            v_target = g.values  # uso total por industria debe igualar producción
            U_arr = ras(U.values, u_target, v_target)
            U = pd.DataFrame(U_arr, index=productos, columns=industrias)

    # ── Market share matrix D  (n_ind × n_prod) ──────────────────────────────
    # D[i,j] = V[i,j] / q[j]
    q_safe = q.copy()
    q_safe[q_safe == 0] = 1  # evitar /0
    D = V.div(q_safe, axis=1)         # (n_ind × n_prod)

    # ── Coeficientes de insumo B  (n_prod × n_ind) ───────────────────────────
    # B[i,j] = U[i,j] / g[j]
    g_safe = g.copy()
    g_safe[g_safe == 0] = 1
    B = U.div(g_safe, axis=1)         # (n_prod × n_ind)

    # ── Flujos intermedios Z  (n_ind × n_ind) ────────────────────────────────
    # Z = D @ U    con D(n_ind×n_prod) @ U(n_prod×n_ind) = (n_ind×n_ind)
    Z_arr = D.values @ U.values
    Z = pd.DataFrame(Z_arr, index=industrias, columns=industrias)

    if U_importada is not None:
        U_imp = U_importada.reindex(index=productos, columns=industrias).fillna(0)
        M_intermedia_ind = U_imp.sum(axis=0).reindex(industrias).fillna(0)
    else:
        M_intermedia_ind = pd.Series(0.0, index=industrias)
    M_intermedia_ind.name = 'consumo_intermedio_importado'

    # ── Coeficientes técnicos A  (n_ind × n_ind) ─────────────────────────────
    A_arr = Z_arr / g_safe.values[np.newaxis, :]
    A = pd.DataFrame(A_arr, index=industrias, columns=industrias)

    # ── Inversa de Leontief L  (n_ind × n_ind) ───────────────────────────────
    I_n = np.eye(len(industrias))
    try:
        L_arr = np.linalg.inv(I_n - A_arr)
    except np.linalg.LinAlgError:
        print("  [ERROR] Matriz singular — usando pseudo-inversa")
        L_arr = np.linalg.pinv(I_n - A_arr)
    L = pd.DataFrame(L_arr, index=industrias, columns=industrias)

    # ── Demanda final transformada a espacio de industrias ───────────────────
    y_prod = Y.sum(axis=1).reindex(productos).fillna(0)
    f_ind_arr = D.values @ y_prod.values
    f_ind = pd.Series(f_ind_arr, index=industrias, name='demanda_final')

    # ── Valor agregado total ──────────────────────────────────────────────────
    W_total = W.sum(axis=0).reindex(industrias).fillna(0)
    W_total.name = 'valor_agregado'

    return {
        'Z'      : Z,
        'A'      : A,
        'L'      : L,
        'g'      : g,
        'q'      : q,
        'D'      : D,
        'B'      : B,
        'f_ind'  : f_ind,
        'W_total': W_total,
        'M_intermedia_ind': M_intermedia_ind,
        'balance': bal,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. Verificación post-conversión
# ─────────────────────────────────────────────────────────────────────────────

def verificar_leontief(mip: dict, tol: float = 1.0) -> bool:
    """
    Verifica la identidad fundamental: L @ f = g
    (la inversa de Leontief aplicada a la demanda final reproduce la producción)
    """
    g_rec = mip['L'].values @ mip['f_ind'].values
    discrepancia = np.abs(g_rec - mip['g'].values).max()
    ok = discrepancia <= tol
    if not ok:
        print(f"  [AVISO] Discrepancia máx L·f vs g: {discrepancia:,.2f}")
    return ok
