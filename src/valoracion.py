"""
Valoración: utilización a precios de comprador -> SUT doméstico a precios
básicos  (UN Handbook, Cap. 7 y Cap. 8).

Partiendo de la utilización a precios de comprador y del puente de valoración
por producto (OPB, importaciones, ajuste CIF/FOB, derechos, impuestos a
productos, márgenes de comercio y transporte), se construye un SUT doméstico a
precios básicos en tres pasos, conservando totales por columna (usuario):

  1. Impuestos: se retiran los impuestos sobre los productos (IP+DI+IVA) de las
     celdas de uso y se acumulan en una fila primaria 'impuestos_netos_productos'.
  2. Márgenes: los márgenes de comercio y transporte incorporados al precio de
     cada bien se retiran de la fila del bien y se reasignan a las filas de los
     productos-servicio que los proveen (aquellos con margen neto negativo en la
     tabla de oferta), en la MISMA columna -> se conserva la suma por columna.
  3. Importaciones: cada fila de uso a precios básicos se separa en parte
     doméstica (proporción OPB/(OPB+IMPO+Ajuste)) e importada; la parte importada
     se acumula en una fila primaria 'consumo_intermedio_importado'.

Identidad resultante por industria j:
    g_j = Σ_p U_dom[p,j] + importado_j + impuestos_j + VAB_j
y por producto p (fila):
    OPB_p = Σ_j U_dom[p,j] + Σ demanda_final_dom[p]
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .sut import SUT


def _row_scale(df: pd.DataFrame, factor: pd.Series) -> pd.DataFrame:
    return df.mul(factor.reindex(df.index).fillna(0.0), axis=0)


def valorar_argentina(parsed: dict, verbose: bool = False) -> tuple[SUT, dict]:
    """Construye el SUT doméstico a precios básicos desde el dict del parser AR."""
    U = parsed["U_pc"].copy()          # prod × ind (precios comprador)
    Y = parsed["Y_pc"].copy()          # prod × fd
    val = parsed["val"]                # prod × columnas de valoración
    V_pi = parsed["V_pi"]              # prod × ind (oferta pb)
    VA_ind = parsed["VA"]              # 1 × ind  (VAB pb)
    prod = U.index
    ind = U.columns

    OPB = val["OPB"]; IMPO = val["IMPO"]; Ajuste = val["Ajuste"]
    IP = val["IP"]; DI = val["DI"]; IVA = val["IVA"]; Com = val.get("Comisiones", 0.0)
    Mg = val["Mg"]; OPC = val["OPC"]

    basic = OPB + IMPO + Ajuste                       # oferta a precios básicos (dom+imp)
    tax = (IP + DI + IVA + Com)                       # cuña de impuestos y comisiones sobre productos
    pm = (basic + Mg).replace(0, np.nan)              # precio productor incl. márgenes
    opc_safe = OPC.replace(0, np.nan)

    # ── Paso 1: retirar impuestos (proporcional por fila) ────────────────
    keep_tax = ((OPC - tax) / opc_safe).fillna(0.0)   # fracción sin impuestos
    U1 = _row_scale(U, keep_tax)
    Y1 = _row_scale(Y, keep_tax)
    impuestos_j = (U.sum(axis=0) - U1.sum(axis=0))     # por industria (fila primaria)

    # ── Paso 2: reasignar márgenes de bienes a servicios (por columna) ────
    def reasignar(mg: pd.Series, U1, Y1):
        frac = (mg.clip(lower=0) / pm).fillna(0.0)     # sólo bienes (mg>0)
        w = (-mg.clip(upper=0))                        # proveedores de margen (mg<0)
        w = (w / w.sum()) if w.sum() != 0 else w
        # margen retirado por columna (intermedio + demanda final)
        remU = _row_scale(U1, frac)
        remY = _row_scale(Y1, frac)
        U2 = U1 - remU
        Y2 = Y1 - remY
        # añadir el total retirado por columna a las filas-servicio (peso w)
        addU = np.outer(w.reindex(U1.index).fillna(0.0).to_numpy(), remU.sum(axis=0).to_numpy())
        addY = np.outer(w.reindex(Y1.index).fillna(0.0).to_numpy(), remY.sum(axis=0).to_numpy())
        U2 = U2 + pd.DataFrame(addU, index=U1.index, columns=U1.columns)
        Y2 = Y2 + pd.DataFrame(addY, index=Y1.index, columns=Y1.columns)
        return U2, Y2

    U2, Y2 = reasignar(Mg, U1, Y1)
    # la reasignación de márgenes puede dejar negativos minúsculos (cuando el
    # margen supera el valor de una celda); se llevan a 0 y el balanceo RAS
    # (Cap. 11) reabsorbe la diferencia. Garantiza una MIP sin negativos.
    U2 = U2.clip(lower=0.0)
    Y2 = Y2.clip(lower=0.0)

    # ── Paso 3: separar doméstico / importado ─────────────────────────────
    dom_share = (OPB / basic.replace(0, np.nan)).fillna(0.0).clip(0, 1)
    U_dom = _row_scale(U2, dom_share)
    Y_dom = _row_scale(Y2, dom_share)
    importado_j = (U2.sum(axis=0) - U_dom.sum(axis=0))   # importado intermedio por ind

    # ── SUT canónico (ind × prod para V) ──────────────────────────────────
    # ind × prod (oferta pb). Se llevan a 0 los negativos de la matriz de
    # producción (p.ej. IBGE tiene ~4 ajustes negativos): una producción
    # negativa no tiene sentido económico y generaría negativos en la MIP.
    V = V_pi.T.clip(lower=0.0)
    VA = pd.concat([
        pd.DataFrame([importado_j.reindex(ind).fillna(0.0).to_numpy()],
                     index=["consumo_intermedio_importado"], columns=ind),
        pd.DataFrame([impuestos_j.reindex(ind).fillna(0.0).to_numpy()],
                     index=["impuestos_netos_productos"], columns=ind),
        VA_ind.reindex(columns=ind).fillna(0.0).rename(index={VA_ind.index[0]: "valor_agregado_bruto"}),
    ])

    sut = SUT(V=V, U=U_dom, Y=Y_dom, VA=VA, M=None,
              pais=parsed["pais"], anio=parsed["anio"], unidad=parsed["unidad"],
              valoracion="básicos",
              meta={"prod_labels": parsed.get("prod_labels", {}),
                    "ind_labels": parsed.get("ind_labels", {})})

    rep = {
        "balance": sut.resumen_balance(),
        "importado_total": float(importado_j.sum()),
        "impuestos_total": float(impuestos_j.sum()),
        "va_total": float(VA_ind.values.sum()),
        "margen_neto_residual": float(Mg.sum()),
    }
    if verbose:
        b = rep["balance"]
        print(f"  [valoración AR {parsed['anio']}] "
              f"balanceado={b['balanceado']} "
              f"(max_rel prod={b['max_rel_producto']:.1e}, ind={b['max_rel_industria']:.1e})")
    return sut, rep
