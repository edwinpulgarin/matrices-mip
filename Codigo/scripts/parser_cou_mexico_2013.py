# -*- coding: utf-8 -*-
"""Parser del COU matricial INEGI/CEPAL de Mexico 2013 (nivel rama SCIAN).

Produce data/processed/mexico/couref_mexico_2013.xlsx con las tablas del Cuadro
de Oferta y Utilizacion oficial, para adjuntarlas como REFERENCIA al Excel de la
MIP directa de Mexico 2013. No altera la MIP publicada.

Fuente: INEGI. Sistema de Cuentas Nacionales de Mexico. COU 2013, precios
corrientes, nivel rama SCIAN, separacion domestico/importado. Descargado del
repositorio CEPAL COU/MIP. Archivos en data/raw/_cepal_staging/MEX_COU_2013/.

Orientacion de salida (igual que los COU reconstruidos del proyecto):
- V_oferta        : actividad x producto (matriz de produccion / make).
- U_utilizacion   : producto x actividad (uso intermedio domestico).
- U_importada     : producto x actividad (uso intermedio importado).
- Y_demanda_final : producto x componente (demanda final domestica).
- M_importaciones : producto x 1 (importaciones totales por producto).
- W_valor_agregado: 1 x actividad (g - consumo intermedio total).
- notas           : trazabilidad de la fuente.
"""

from pathlib import Path
import re

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "_cepal_staging" / "MEX_COU_2013"
OUT = ROOT / "data" / "processed" / "mexico" / "couref_mexico_2013.xlsx"

F_OFERTA = SRC / "MEX_COU_2013_PRECIOSCORRIENTES_20x20_OFERTA_RAMA_SCIAN.xlsx"
F_DEM_DOM = SRC / "MEX_COU_2013_PRECIOSCORRIENTES_20x20_DEMANDA_PBASICOS_RAMA_SCIAN_DOMESTICO.xlsx"
F_DEM_IMP = SRC / "MEX_COU_2013_PRECIOSCORRIENTES_20x20_DEMANDA_PBASICOS_RAMA_SCIAN_IMPORTADO.xlsx"

# Filas de encabezado (1-based en Excel): grupo en 5, detalle en 6, datos desde 7.
ROW_GROUP = 4  # 0-based
ROW_DETAIL = 5
ROW_DATA0 = 6

ACT_RE = re.compile(r"^(\d{4})\s*-\s*(.+)$")
FD_PREFIXES = ("CP", "CG", "P.51", "P.52", "P.6", "YA0")


def _strip_prefix(text) -> str:
    """Quita un prefijo de una sola letra minuscula + espacio (p. ej. 'a Total')."""
    h = " ".join(str(text).strip().split())
    m = re.match(r"^[a-z]\s+(.*)$", h)
    return m.group(1).strip() if m else h


def _num(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _load(path: Path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Tabulado"]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    ncol = max(len(r) for r in rows)
    rows = [r + [None] * (ncol - len(r)) for r in rows]
    headers = []
    for c in range(ncol):
        detail = rows[ROW_DETAIL][c]
        group = rows[ROW_GROUP][c]
        headers.append(detail if detail not in (None, "") else group)
    return rows, headers, ncol


def _product_rows(rows):
    """Devuelve [(row_idx, label_canonico)] de las filas de producto (codigo rama)."""
    out = []
    for i in range(ROW_DATA0, len(rows)):
        lab = rows[i][0]
        if lab is None:
            continue
        m = ACT_RE.match(_strip_prefix(lab))
        if m:
            out.append((i, "%s - %s" % (m.group(1), m.group(2).strip())))
    return out


def _activity_cols(headers):
    out = []
    for c, h in enumerate(headers):
        if h is None:
            continue
        m = ACT_RE.match(_strip_prefix(h))
        if m:
            out.append((c, "%s - %s" % (m.group(1), m.group(2).strip())))
    return out


def _fd_cols(headers):
    out = []
    for c, h in enumerate(headers):
        if h is None:
            continue
        hs = _strip_prefix(h)
        if any(hs.startswith(p) for p in FD_PREFIXES):
            out.append((c, hs))
    return out


def _matrix(rows, prod_rows, cols):
    data = np.zeros((len(prod_rows), len(cols)), dtype=float)
    for r, (ri, _) in enumerate(prod_rows):
        for k, (ci, _) in enumerate(cols):
            data[r, k] = _num(rows[ri][ci])
    idx = [lab for _, lab in prod_rows]
    colnames = [lab for _, lab in cols]
    return pd.DataFrame(data, index=idx, columns=colnames)


def main():
    # OFERTA -> make matrix (producto x actividad).
    of_rows, of_head, _ = _load(F_OFERTA)
    of_prods = _product_rows(of_rows)
    of_acts = _activity_cols(of_head)
    make = _matrix(of_rows, of_prods, of_acts)            # producto x actividad
    V_oferta = make.T                                      # actividad x producto

    # OPB por producto (oferta total a precios basicos) = produccion por producto q.
    opb_col = next((c for c, h in enumerate(of_head)
                    if h and _strip_prefix(h).startswith("OPB")), None)
    q = pd.Series(
        [_num(of_rows[ri][opb_col]) if opb_col is not None else np.nan for ri, _ in of_prods],
        index=[lab for _, lab in of_prods], name="oferta_basicos_q",
    )

    # DEMANDA DOMESTICO -> uso intermedio domestico + demanda final domestica.
    dd_rows, dd_head, _ = _load(F_DEM_DOM)
    dd_prods = _product_rows(dd_rows)
    dd_acts = _activity_cols(dd_head)
    dd_fd = _fd_cols(dd_head)
    U_utilizacion = _matrix(dd_rows, dd_prods, dd_acts)    # producto x actividad
    Y_demanda_final = _matrix(dd_rows, dd_prods, dd_fd)    # producto x componente

    # DEMANDA IMPORTADO -> uso intermedio importado + demanda final importada.
    di_rows, di_head, _ = _load(F_DEM_IMP)
    di_prods = _product_rows(di_rows)
    di_acts = _activity_cols(di_head)
    U_importada = _matrix(di_rows, di_prods, di_acts)      # producto x actividad

    # M por producto: utilizacion total importada a precios basicos (col UTPB).
    utpb_col = next((c for c, h in enumerate(di_head)
                     if h and _strip_prefix(h).startswith("UTPB")), None)
    M = pd.Series(
        [_num(di_rows[ri][utpb_col]) if utpb_col is not None else np.nan for ri, _ in di_prods],
        index=[lab for _, lab in di_prods], name="importaciones",
    )
    M_importaciones = M.to_frame()

    # Valor agregado por actividad = produccion bruta - consumo intermedio total.
    g_act = make.sum(axis=0)                               # produccion por actividad
    ci_dom = U_utilizacion.reindex(columns=g_act.index).fillna(0).sum(axis=0)
    ci_imp = U_importada.reindex(columns=g_act.index).fillna(0).sum(axis=0)
    W = (g_act - ci_dom - ci_imp)
    W_valor_agregado = W.to_frame().T
    W_valor_agregado.index = ["valor_agregado_bruto"]

    notas = pd.DataFrame({"nota": [
        "Cuadro de Oferta y Utilizacion (COU) oficial de Mexico 2013, "
        "adjuntado como REFERENCIA del mismo marco estadistico de la MIP directa.",
        "Fuente: INEGI. Sistema de Cuentas Nacionales de Mexico. COU 2013, "
        "precios corrientes, nivel rama SCIAN, separacion domestico/importado.",
        "Obtenido del repositorio CEPAL COU/MIP "
        "(https://statistics.cepal.org/repository/cou-mip/).",
        "Archivos fuente: MEX_COU_2013_PRECIOSCORRIENTES_20x20_OFERTA_RAMA_SCIAN, "
        "DEMANDA_PBASICOS_RAMA_SCIAN_DOMESTICO e _IMPORTADO.",
        "V_oferta: actividad x producto (make). U_utilizacion / U_importada: "
        "producto x actividad (uso intermedio domestico / importado).",
        "Y_demanda_final: componentes domesticos CP, CG, P.51b, P.52, P.6, YA0.",
        "W_valor_agregado por actividad = produccion bruta (suma de columnas de V) "
        "menos consumo intermedio domestico mas importado.",
        "Este COU se adjunta SIN alterar la MIP publicada. La MIP de Mexico 2013 "
        "sigue siendo directa (tipo_matriz = MIP_directa_con_COU_referencia).",
        "El COU comparte el nivel rama SCIAN (262 ramas) de la MIP, por lo que "
        "sirve de verificacion del marco; no se usa para reconstruir la matriz.",
    ]})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        V_oferta.to_excel(w, sheet_name="V_oferta")
        U_utilizacion.to_excel(w, sheet_name="U_utilizacion")
        U_importada.to_excel(w, sheet_name="U_importada")
        Y_demanda_final.to_excel(w, sheet_name="Y_demanda_final")
        M_importaciones.to_excel(w, sheet_name="M_importaciones")
        W_valor_agregado.to_excel(w, sheet_name="W_valor_agregado")
        q.to_frame().to_excel(w, sheet_name="q_oferta_producto")
        notas.to_excel(w, sheet_name="notas", index=False)

    # Reporte de consistencia.
    print("[OK] %s" % OUT.relative_to(ROOT))
    print("  V_oferta (act x prod):", V_oferta.shape)
    print("  U_utilizacion (prod x act):", U_utilizacion.shape)
    print("  U_importada (prod x act):", U_importada.shape)
    print("  Y_demanda_final (prod x comp):", Y_demanda_final.shape,
          "->", list(Y_demanda_final.columns))
    print("  W_valor_agregado (1 x act):", W_valor_agregado.shape)
    print("  productos:", len(of_prods), " actividades:", len(of_acts))
    print("  g total (suma V):        {:,.1f}".format(float(make.to_numpy().sum())))
    print("  CI dom total:            {:,.1f}".format(float(U_utilizacion.to_numpy().sum())))
    print("  CI imp total:            {:,.1f}".format(float(U_importada.to_numpy().sum())))
    print("  VA total (g-CI):         {:,.1f}".format(float(W.sum())))
    print("  Demanda final dom total: {:,.1f}".format(float(Y_demanda_final.to_numpy().sum())))
    print("  VA negativos:", int((W < -1e-6).sum()))


if __name__ == "__main__":
    main()
