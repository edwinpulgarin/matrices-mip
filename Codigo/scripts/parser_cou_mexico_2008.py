# -*- coding: utf-8 -*-
"""Parser del COU matricial INEGI de Mexico 2008 (nivel rama SCIAN, 262 ramas).

Fuente: INEGI. SCNM. Cuadros de Oferta y Utilizacion 2008. Tabulados
descargados por el equipo (Tabulados_cou2008). Archivos usados:
  O_pc_3.XLSX    Oferta de bienes y servicios por rama (make / V).
  U_d_pb_3.XLSX  Utilizacion de origen domestico, precios basicos (use nacional + demanda final).
  U_m_pb_3.XLSX  Utilizacion de origen importado, precios basicos (use importado).

Produce data/processed/mexico/couref_mexico_2008.xlsx para adjuntar el COU como
REFERENCIA a la MIP directa de Mexico 2008 (misma logica que 2013).

Layout 2008 (distinto al de CEPAL 2013):
  col B = codigo clase SCIAN del producto (fila); col C = denominacion.
  fila de codigos de actividad (4 digitos) detectada dinamicamente; la fila
  anterior trae los nombres de actividad. Al final, columnas de demanda final
  (consumo privado, gobierno, FBKF, variacion de existencias, exportaciones,
  discrepancia).
"""

from pathlib import Path
import re

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "Nueva_Info" / "_stg" / "cou2008" / "Tabulados_cou2008" / "cou2008"
OUT = ROOT / "data" / "processed" / "mexico" / "couref_mexico_2008.xlsx"

F_OFERTA = SRC / "O_pc_3.XLSX"
F_DOM = SRC / "U_d_pb_3.XLSX"
F_IMP = SRC / "U_m_pb_3.XLSX"

CODE4 = re.compile(r"^\d{4}$")

FD_MAP = [
    ("CONSUMO PRIVADO", "CP - Consumo Privado"),
    ("CONSUMO DE GOBIERNO", "CG - Consumo de gobierno"),
    ("FORMACION BRUTA", "P.51b - Formación bruta de capital fijo"),
    ("VARIACION DE EXISTENCIAS", "P.52 - Variación de existencias"),
    ("EXPORTACIONES", "P.6 - Exportaciones de bienes y servicios"),
    ("DISCREPANCIA", "YA0 - Discrepancia estadística"),
]


def _num(v):
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _ascii(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper()


def _load(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    ncol = max(len(r) for r in rows)
    rows = [r + [None] * (ncol - len(r)) for r in rows]
    code_row = max(range(min(14, len(rows))),
                   key=lambda i: sum(1 for c in rows[i] if c is not None and CODE4.fullmatch(str(c).strip())))
    return rows, code_row, ncol


def _product_rows(rows):
    """(row_idx, 'codigo - nombre') de filas cuyo col B es codigo de 4 digitos."""
    out = []
    for i, r in enumerate(rows):
        b = r[1]
        if b is not None and CODE4.fullmatch(str(b).strip()):
            name = str(r[2]).strip() if r[2] is not None else ""
            out.append((i, "%s - %s" % (str(b).strip(), name)))
    return out


def _activity_cols(rows, code_row):
    """(col_idx, 'codigo - nombre') de columnas de actividad."""
    name_row = code_row - 1
    out = []
    for c, code in enumerate(rows[code_row]):
        if code is not None and CODE4.fullmatch(str(code).strip()):
            name = rows[name_row][c]
            name = str(name).strip() if name is not None else ""
            out.append((c, "%s - %s" % (str(code).strip(), name)))
    return out


def _fd_cols(rows, code_row, act_set):
    """(col_idx, etiqueta_canonica) de columnas de demanda final."""
    out = []
    for c in range(len(rows[code_row])):
        if c in act_set:
            continue
        header = " ".join(_ascii(rows[r][c]) for r in range(code_row - 2, code_row + 1)
                          if rows[r][c] is not None)
        for key, canon in FD_MAP:
            if key in header:
                out.append((c, canon))
                break
    # quitar duplicados conservando orden
    seen, uniq = set(), []
    for c, canon in out:
        if canon not in seen:
            seen.add(canon)
            uniq.append((c, canon))
    return uniq


def _matrix(rows, prod_rows, cols):
    data = np.zeros((len(prod_rows), len(cols)), dtype=float)
    for r, (ri, _) in enumerate(prod_rows):
        for k, (ci, _) in enumerate(cols):
            data[r, k] = _num(rows[ri][ci])
    return pd.DataFrame(data, index=[l for _, l in prod_rows], columns=[l for _, l in cols])


def _total_col(rows, prod_rows, code_row):
    """Columna 'UTILIZACION TOTAL' (col D, idx 3) por producto."""
    return pd.Series([_num(rows[ri][3]) for ri, _ in prod_rows],
                     index=[l for _, l in prod_rows])


def main():
    of_rows, of_cr, _ = _load(F_OFERTA)
    of_prods = _product_rows(of_rows)
    of_acts = _activity_cols(of_rows, of_cr)
    make = _matrix(of_rows, of_prods, of_acts)          # producto x actividad
    V_oferta = make.T

    dd_rows, dd_cr, _ = _load(F_DOM)
    dd_prods = _product_rows(dd_rows)
    dd_acts = _activity_cols(dd_rows, dd_cr)
    act_set = {c for c, _ in dd_acts}
    dd_fd = _fd_cols(dd_rows, dd_cr, act_set)
    U_utilizacion = _matrix(dd_rows, dd_prods, dd_acts)
    Y_demanda_final = _matrix(dd_rows, dd_prods, dd_fd)

    di_rows, di_cr, _ = _load(F_IMP)
    di_prods = _product_rows(di_rows)
    di_acts = _activity_cols(di_rows, di_cr)
    U_importada = _matrix(di_rows, di_prods, di_acts)
    M_importaciones = _total_col(di_rows, di_prods, di_cr).to_frame("importaciones")

    g_act = make.sum(axis=0)
    ci_dom = U_utilizacion.reindex(columns=g_act.index).fillna(0).sum(axis=0)
    ci_imp = U_importada.reindex(columns=g_act.index).fillna(0).sum(axis=0)
    W = g_act - ci_dom - ci_imp
    W_valor_agregado = W.to_frame().T
    W_valor_agregado.index = ["valor_agregado_bruto"]

    notas = pd.DataFrame({"nota": [
        "Cuadro de Oferta y Utilizacion (COU) oficial de Mexico 2008, adjuntado "
        "como REFERENCIA del mismo marco estadistico de la MIP directa.",
        "Fuente: INEGI. Sistema de Cuentas Nacionales de Mexico (SCNM). "
        "Cuadros de Oferta y Utilizacion 2008, nivel rama SCIAN (262 ramas).",
        "Archivos: O_pc_3 (oferta), U_d_pb_3 (utilizacion domestica, precios "
        "basicos), U_m_pb_3 (utilizacion importada, precios basicos).",
        "V_oferta: actividad x producto (make). U_utilizacion / U_importada: "
        "producto x actividad. Y_demanda_final: CP, CG, P.51b, P.52, P.6, YA0.",
        "W_valor_agregado por actividad = produccion bruta (suma de columnas de "
        "V) menos consumo intermedio domestico mas importado.",
        "Se adjunta SIN alterar la MIP publicada (tipo_matriz = "
        "MIP_directa_con_COU_referencia). Comparte el nivel rama de la MIP.",
    ]})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        V_oferta.to_excel(w, sheet_name="V_oferta")
        U_utilizacion.to_excel(w, sheet_name="U_utilizacion")
        U_importada.to_excel(w, sheet_name="U_importada")
        Y_demanda_final.to_excel(w, sheet_name="Y_demanda_final")
        M_importaciones.to_excel(w, sheet_name="M_importaciones")
        W_valor_agregado.to_excel(w, sheet_name="W_valor_agregado")
        notas.to_excel(w, sheet_name="notas", index=False)

    print("[OK] %s" % OUT.relative_to(ROOT))
    print("  V_oferta:", V_oferta.shape, " U_utilizacion:", U_utilizacion.shape,
          " U_importada:", U_importada.shape)
    print("  Y_demanda_final cols:", list(Y_demanda_final.columns))
    print("  g total (suma V):        {:,.1f}".format(float(make.to_numpy().sum())))
    print("  CI dom total:            {:,.1f}".format(float(U_utilizacion.to_numpy().sum())))
    print("  CI imp total:            {:,.1f}".format(float(U_importada.to_numpy().sum())))
    print("  VA total (g-CI):         {:,.1f}".format(float(W.sum())))
    print("  Demanda final dom total: {:,.1f}".format(float(Y_demanda_final.to_numpy().sum())))
    print("  VA negativos:", int((W < -1e-6).sum()))


if __name__ == "__main__":
    main()
