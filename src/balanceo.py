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
        max_iter: int = 5000, tol: float = 1e-13) -> tuple[np.ndarray, int, float]:
    """Ajuste biproporcional: filas -> u, columnas -> v.

    Devuelve (A, iteraciones, error_relativo_final).

    El criterio de salida es RELATIVO a la escala de los márgenes. Con una
    tolerancia absoluta, «error < 1e-9» es inalcanzable cuando los márgenes son
    del orden de 1e9 —que es el caso en cuanto las cifras vienen en miles de
    pesos—: el bucle agota siempre las iteraciones sin que eso signifique que no
    convergió. Medido contra la escala, la tolerancia significa lo que dice:
    dígitos significativos de cierre en cada fila y cada columna.
    """
    su, sv = float(u.sum()), float(v.sum())
    if not np.isclose(su, sv, rtol=1e-9, atol=1e-6):
        raise ValueError(f"RAS: Σfilas ({su:.4f}) ≠ Σcolumnas ({sv:.4f})")
    esc = max(float(np.abs(u).max()), float(np.abs(v).max()), 1.0)
    A = A0.astype(float).copy()
    it, err = 0, np.inf
    for it in range(1, max_iter + 1):
        rs = A.sum(axis=1); rs[rs == 0] = 1.0
        A = (A.T * (u / rs)).T
        cs = A.sum(axis=0); cs[cs == 0] = 1.0
        A = A * (v / cs)
        err = max(float(np.abs(A.sum(axis=1) - u).max()),
                  float(np.abs(A.sum(axis=0) - v).max())) / esc
        if err < tol:
            break
    return A, it, err


def _discrepancia(sut: SUT, previo: dict, verbose: bool,
                  tol: float = 1e-9) -> tuple[SUT, dict]:
    """Cierra el balance de producto SIN tocar ninguna celda leída.

    El residuo se anota en una columna propia de demanda final,
    «discrepancia estadística», que es como lo resuelven las cuentas nacionales
    cuando dos fuentes no calzan al peso. Frente al RAS tiene tres ventajas:

      - **no modifica un solo dato leído**: `U` entra a la MIP tal como se leyó,
        así que `Z = D·U` es reproducible a mano desde las hojas del libro;
      - el residuo queda **en un solo lugar y con nombre**, en vez de repartido
        entre miles de celdas;
      - es reversible: quien no lo quiera, borra la columna.

    A cambio, el residuo aparece como demanda final de un producto que nadie
    demandó. Por eso sólo se usa cuando es chico: si un producto descuadra en
    una fracción grande de su propia oferta, eso no es una discrepancia
    estadística, es un problema que hay que mirar, y ahí corre el RAS.

    El balance por industria no se toca: agregar una columna de demanda final no
    entra en la identidad de la columna (`g_j = Σ_p U[p,j] + VA_j`).
    """
    resid = sut.balance_producto()          # oferta − uso, por producto
    Y = sut.Y.copy()
    Y["discrepancia_estadistica"] = resid.reindex(Y.index).fillna(0.0)

    # El cuadro tiene DOS identidades y hay que cerrar las dos. La columna de
    # arriba cierra la del producto; la de la industria —producción contra
    # costos— puede quedar abierta por su cuenta, porque el valor agregado lo
    # publica la fuente y no siempre calza al peso con el resto de la columna.
    # Brasil deja 1,1e-03 por esa vía. Se cierra igual: con una fila primaria
    # que la declara, en vez de repartir el residuo entre las celdas.
    # Sólo se agrega si dice algo: por debajo de `tol` el residuo es polvo de
    # punto flotante y una fila de ceros en el bloque primario es ruido que hay
    # que explicar en cada libro.
    resid_ind = sut.balance_industria()
    VA = sut.VA
    if float((resid_ind.abs() / sut.g.replace(0, np.nan)).max(skipna=True) or 0.0) > tol:
        VA = pd.concat([
            VA,
            pd.DataFrame([resid_ind.reindex(VA.columns).fillna(0.0).to_numpy()],
                         index=["discrepancia_estadistica"], columns=VA.columns)])

    sut_d = SUT(V=sut.V, U=sut.U, Y=Y, VA=VA, M=sut.M,
                pais=sut.pais, anio=sut.anio, unidad=sut.unidad,
                valoracion=sut.valoracion, meta=dict(sut.meta))
    post = sut_d.resumen_balance()
    rep = {
        "aplicado": False,
        "modo": "discrepancia",
        "motivo": ("el residuo se anotó como discrepancia estadística en la demanda "
                   "final; ninguna celda leída se modificó"),
        "discrepancia_abs": float(resid.abs().sum()),
        "discrepancia_industria_abs": float(resid_ind.abs().sum()),
        "discrepancia_rel": float(resid.abs().sum()) / max(float(sut.q.sum()), 1.0),
        "peor_producto_rel": previo["max_rel_producto"],
        "iteraciones_ras": 0,
        "error_relativo_ras": 0.0,
        "convergio": True,
        "residuo_margenes_abs": float(resid.sum()),
        "residuo_margenes_rel": float(resid.sum()) / max(float(sut.q.sum()), 1.0),
        "celdas_fijas_negativas": 0,
        "monto_fijo_negativo": 0.0,
        "balance_previo": previo,
        "balance_post": post,
    }
    if verbose:
        print(f"  [balanceo] sin RAS: residuo {rep['discrepancia_rel']:.2e} anotado como "
              f"discrepancia estadística (peor producto {previo['max_rel_producto']:.1e})")
    return sut_d, rep


def balancear(sut: SUT, tol_rel: float = 1e-9, tol_ras: float = 1e-13,
              tol_omitir: float = 1e-9, tol_discrepancia: float = 0.02,
              verbose: bool = False) -> tuple[SUT, dict]:
    """Devuelve (SUT balanceado, reporte).

    Si el SUT que entra YA cumple las identidades dentro de `tol_omitir`, no se
    balancea nada: se devuelve tal cual y el reporte lo dice. Un ajuste que no
    hace falta no debería correr sólo porque está en el pipeline —Colombia
    2014-2019 entra cuadrada y el RAS movía 0,000000 %—, y dejarlo correr da la
    impresión de que el balanceo participó en un resultado que ya estaba.

    `tol_rel` es cuánto residuo macro se tolera entre los márgenes de fila y de
    columna antes de absorberlo en la demanda final. `tol_ras` es el criterio de
    salida del ajuste iterativo, relativo a la escala de los márgenes. Son dos
    cosas distintas y por eso van separadas: la primera mide la calidad del SUT
    que entra, la segunda cuán apretado se cierra el ajuste. `tol_ras` se fija
    cerca del límite de la doble precisión para que el balance final quede en
    ~1e-15 relativo, que es lo que declaran los libros.
    """
    previo = sut.resumen_balance(tol_rel=tol_omitir)
    if previo["balanceado"]:
        rep = {
            "aplicado": False,
            "motivo": "el SUT ya cumple las identidades; no se ajustó nada",
            "iteraciones_ras": 0,
            "error_relativo_ras": 0.0,
            "convergio": True,
            "residuo_margenes_abs": 0.0,
            "residuo_margenes_rel": 0.0,
            "balance_previo": previo,
            "balance_post": previo,
        }
        rep["modo"] = "no hizo falta"
        if verbose:
            print("  [balanceo] no hizo falta: el SUT entra cuadrado "
                  f"(máx rel producto {previo['max_rel_producto']:.1e})")
        return sut, rep

    # Residuo chico: se anota y no se toca nada. El RAS queda para cuando el
    # descuadre es lo bastante grande como para no poder llamarse discrepancia.
    if previo["max_rel_producto"] <= tol_discrepancia:
        return _discrepancia(sut, previo, verbose, tol=tol_omitir)

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

    W0 = np.hstack([U.to_numpy(), Y.to_numpy()])     # (n_prod × (n_ind + n_fd))

    # ── Las celdas negativas quedan FUERA del ajuste ──────────────────────
    # El RAS es multiplicativo, así que sólo está definido sobre celdas no
    # negativas (Handbook, Box 11.3): con una celda negativa el factor de fila
    # la empuja en el sentido contrario al del resto y el ajuste deja de
    # significar lo que dice. Y las fuentes SÍ publican negativos —variación de
    # existencias, o sea desacumulación de stock—, que no se pueden borrar sin
    # inventar dato.
    # La salida es tratarlas como exógenas: se conservan tal cual y su aporte se
    # descuenta del margen de su fila y del de su columna. Como se resta lo
    # mismo de los dos lados, los márgenes siguen siendo consistentes entre sí y
    # el ajuste corre sobre un bloque no negativo, que es donde el método vale.
    neg = W0 < 0
    fijo = np.where(neg, W0, 0.0)
    W_adj = np.where(neg, 0.0, W0)
    fila_margins = oferta.to_numpy() - fijo.sum(axis=1)
    interm_col = interm_col - fijo[:, :n_ind].sum(axis=0)
    fd_col = fd_col - fijo[:, n_ind:].sum(axis=0)

    # ── Consistencia macro de márgenes ────────────────────────────────────
    # Va DESPUÉS de apartar las celdas fijas, y sobre los márgenes que quedan
    # para ajustar. Escalar los totales originales rompía las columnas cuya masa
    # ajustable es cero: «objetos valiosos» de Argentina 2019 tiene una sola
    # celda y es negativa, así que su bloque ajustable es todo ceros; al escalar
    # su total el RAS quedaba con un objetivo que ninguna celda podía alcanzar y
    # el residuo se repartía por las filas más grandes (26 sobre 2.285.674.161).
    # Sobre el margen ajustable, ese objetivo es 0 y el ajuste cierra.
    total_fila = float(fila_margins.sum())
    total_col = float(interm_col.sum() + fd_col.sum())
    residuo = total_fila - total_col
    if abs(residuo) > tol_rel * max(abs(total_fila), 1.0):
        # absorber el residuo escalando los totales de demanda final
        escala = (total_fila - interm_col.sum()) / fd_col.sum() if fd_col.sum() != 0 else 1.0
        fd_col = fd_col * escala
    col_margins = np.concatenate([interm_col.to_numpy(), fd_col.to_numpy()])

    W, iters, err = ras(W_adj, fila_margins, col_margins, tol=tol_ras)
    W = W + fijo                                     # vuelven en su posición

    U_bal = pd.DataFrame(W[:, :n_ind], index=prod, columns=ind)
    Y_bal = pd.DataFrame(W[:, n_ind:], index=prod, columns=fd_cols)

    sut_bal = SUT(V=V, U=U_bal, Y=Y_bal, VA=VA, M=(M if sut.M is not None else None),
                  pais=sut.pais, anio=sut.anio, unidad=sut.unidad,
                  valoracion="básicos", meta=dict(sut.meta))

    rep = {
        "aplicado": True,
        "modo": "RAS",
        "celdas_fijas_negativas": int(neg.sum()),
        "monto_fijo_negativo": float(fijo.sum()),
        "iteraciones_ras": iters,
        "error_relativo_ras": float(err),
        "convergio": bool(err < tol_ras),
        "residuo_margenes_abs": float(residuo),
        "residuo_margenes_rel": float(residuo / max(total_fila, 1.0)),
        "balance_previo": sut.resumen_balance(),
        "balance_post": sut_bal.resumen_balance(),
    }
    if verbose:
        print(f"  [balanceo] RAS {iters} iter (err rel {err:.1e}, "
              f"convergió={rep['convergio']}); residuo margen "
              f"{rep['residuo_margenes_rel']:.2e}; "
              f"balanceado={rep['balance_post']['balanceado']}")
    return sut_bal, rep
