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


# Notas de método que se estampan en la portada de cada libro, para que quien lo
# abra sepa sobre qué supuesto está parado sin tener que leer el repositorio.
NOTA_DIRECTO = (
    "SIN PRORRATEO. La fuente publica la utilización a precios básicos y el corte "
    "doméstico/importado medido celda a celda, así que no se aplica ningún supuesto de "
    "reparto: ni el del Cap. 7 (impuestos y márgenes) ni el del Cap. 8 (origen)."
)

NOTA_PRORRATEO = (
    "CON PRORRATEO. Esta fuente publica impuestos, márgenes e importaciones sólo POR "
    "PRODUCTO, no celda a celda, así que se reparten proporcionalmente por fila, como "
    "prescribe el Handbook §7.77 y la Tabla 7.1 para ese caso. El supuesto sobreestima "
    "los encadenamientos domésticos e infla los multiplicadores. Está MEDIDO donde sí "
    "existe el dato: México 2013 +5,65 % en el multiplicador medio; Brasil 2010 +1,34 % "
    "y 2015 +1,57 %; Uruguay 2016 subestima los insumos importados un 15,8 % frente a la "
    "matriz M del BCU. Detalle en reports/mexico_validacion.md y reports/brasil_todos.md."
)


def ensamblar_directo(parsed: dict, verbose: bool = False) -> tuple[SUT, dict]:
    """
    Arma el SUT SIN NINGÚN PRORRATEO, para fuentes que ya publican la utilización
    a precios básicos y con el corte doméstico/importado medido celda a celda.

    Es la alternativa a `valorar_argentina`, que tiene que repartir impuestos,
    márgenes e importaciones proporcionalmente por fila porque la fuente sólo los
    da por producto. Ese prorrateo está prescrito por el Handbook §7.77 como
    *fallback*, pero medido contra el dato real de INEGI sobreestima el consumo
    intermedio doméstico un 15,7 % e infla los multiplicadores un 5,65 % en
    promedio (hasta +58 % en manufactura de exportación). Donde hay dato, se usa
    el dato.

    Espera en `parsed`:
        V_pi     producto × industria, producción a precios básicos
        U_dom    producto × industria, utilización DOMÉSTICA a precios básicos
        Y_dom    producto × componentes, demanda final DOMÉSTICA a precios básicos
        U_imp    producto × industria, utilización IMPORTADA a precios básicos
        imptax_j impuestos netos sobre productos por industria (opcional)
    """
    V_pi = parsed["V_pi"]
    U_dom = parsed["U_dom"]
    Y_dom = parsed["Y_dom"]
    U_imp = parsed["U_imp"]
    ind = list(U_dom.columns)

    V = V_pi.T.clip(lower=0.0)
    g = V.sum(axis=1)

    importado_j = U_imp.sum(axis=0).reindex(ind).fillna(0.0)
    if "imptax_j" in parsed:
        impuestos_j = parsed["imptax_j"].reindex(ind).fillna(0.0)
    else:
        impuestos_j = pd.Series(0.0, index=ind)
    # el VAB cierra la columna por identidad contable, sin supuestos:
    #   g_j = Σ_p U_dom[p,j] + importado_j + impuestos_j + VAB_j
    vab_j = (g.reindex(ind).fillna(0.0) - U_dom.sum(axis=0).reindex(ind).fillna(0.0)
             - importado_j - impuestos_j)

    VA = pd.concat([
        pd.DataFrame([importado_j.to_numpy()], index=["consumo_intermedio_importado"], columns=ind),
        pd.DataFrame([impuestos_j.to_numpy()], index=["impuestos_netos_productos"], columns=ind),
        pd.DataFrame([vab_j.to_numpy()], index=["valor_agregado_bruto"], columns=ind),
    ])

    sut = SUT(V=V, U=U_dom, Y=Y_dom, VA=VA, M=None,
              pais=parsed["pais"], anio=parsed["anio"], unidad=parsed["unidad"],
              valoracion="básicos",
              meta={"prod_labels": parsed.get("prod_labels", {}),
                    "ind_labels": parsed.get("ind_labels", {}),
                    "sin_prorrateo": True})

    rep = {
        "metodo": "directo (sin prorrateo)",
        "importado_total": float(importado_j.sum()),
        "impuestos_total": float(impuestos_j.sum()),
        "va_total": float(vab_j.sum()),
        "balance": sut.resumen_balance(),
    }
    if verbose:
        print(f"  [directo] importado {rep['importado_total']:,.0f} · "
              f"VAB {rep['va_total']:,.0f} · balanceado={rep['balance']['balanceado']}")
    return sut, rep


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
