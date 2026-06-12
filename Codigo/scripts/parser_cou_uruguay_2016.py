# -*- coding: utf-8 -*-
"""Parser del COU detallado de Uruguay 2016 (BCU), hoja '2016 CORRIENTE'.

Fuente: BCU. Cuadro de Oferta y Utilizacion 2016, version detallada, precios
corrientes. Archivo aportado por el equipo:
  data/raw/Nueva_Info/Uruguay_2016-2017 Detallada_COU_C.xlsx

Produce data/processed/uruguay/couref_uruguay_2016.xlsx para adjuntar el COU
como REFERENCIA a la MIP directa de Uruguay 2016.

Nota de alcance: el COU esta a 95 industrias x 110 productos; la MIP directa de
Uruguay 2016 esta a otra clasificacion (128 sectores). Por eso el COU se adjunta
como referencia oficial del mismo anio/marco, no como reconstruccion 1:1.

Layout: la hoja trae dos bloques apilados con productos en filas e industrias
(A.1..T.1) en columnas:
  - Bloque OFERTA   (header 'Oferta Total' en col G): produccion por industria
    (make) + oferta importada, margenes, impuestos.
  - Bloque UTILIZACION (header 'Utilizacion Total' en col G): uso intermedio por
    industria + demanda final (consumo hogares, gobierno, FBKF, variacion de
    existencias, exportaciones) + fila de valor agregado bruto.
"""

from pathlib import Path
import re

import numpy as np
import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "Nueva_Info" / "Uruguay_2016-2017 Detallada_COU_C.xlsx"
OUT = ROOT / "data" / "processed" / "uruguay" / "couref_uruguay_2016.xlsx"
HOJA = "2016 CORRIENTE"

IND = re.compile(r"^[A-Z]\.\d+$")
NPROD = 110

FD_MAP = [
    ("HOGARES", "CP - Consumo final de hogares"),
    ("GOBIERNO", "CG - Consumo del gobierno e ISFLSH"),
    ("FORMACION BRUTA", "P.51b - Formación bruta de capital fijo"),
    ("VARIACION DE EXISTENCIAS", "P.52 - Variación de existencias"),
    ("EXPORTACION", "P.6 - Exportaciones"),
]


def _num(v):
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().replace(",", ""))
    except ValueError:
        return 0.0


def _ascii(t):
    import unicodedata
    t = unicodedata.normalize("NFKD", str(t))
    return "".join(c for c in t if not unicodedata.combining(c)).upper()


def _load():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb[HOJA]
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    wb.close()
    ncol = max(len(r) for r in rows)
    return [r + [None] * (ncol - len(r)) for r in rows]


def _header_row(rows, col6_prefix):
    for i, r in enumerate(rows):
        if str(r[0]).strip() == "Código" and isinstance(r[6], str) and r[6].strip().startswith(col6_prefix):
            return i
    raise ValueError("No se encontro header con col G='%s'" % col6_prefix)


def _industry_cols(rows, hdr):
    return [(c, str(h).strip()) for c, h in enumerate(rows[hdr]) if isinstance(h, str) and IND.fullmatch(h.strip())]


def _product_rows(rows, hdr, n=NPROD):
    out = []
    i = hdr + 1
    while i < len(rows) and len(out) < n:
        a = rows[i][0]
        if a is not None and re.fullmatch(r"\d+", str(a).strip()):
            name = str(rows[i][1]).strip() if rows[i][1] is not None else ""
            out.append((i, "%s - %s" % (str(a).strip(), name)))
        i += 1
    return out


def _matrix(rows, prod_rows, cols):
    data = np.zeros((len(prod_rows), len(cols)), dtype=float)
    for r, (ri, _) in enumerate(prod_rows):
        for k, (ci, _) in enumerate(cols):
            data[r, k] = _num(rows[ri][ci])
    return pd.DataFrame(data, index=[l for _, l in prod_rows], columns=[l for _, l in cols])


def main():
    rows = _load()
    of_hdr = _header_row(rows, "Oferta")
    ut_hdr = _header_row(rows, "Utilizaci")
    of_ind = _industry_cols(rows, of_hdr)
    ut_ind = _industry_cols(rows, ut_hdr)
    of_prods = _product_rows(rows, of_hdr)
    ut_prods = _product_rows(rows, ut_hdr)

    # OFERTA -> make (producto x industria) y oferta importada por producto.
    make = _matrix(rows, of_prods, of_ind)
    V_oferta = make.T
    imp_col = next((c for c, h in enumerate(rows[of_hdr])
                    if isinstance(h, str) and "importad" in _ascii(h).lower()), None)
    M = pd.Series([_num(rows[ri][imp_col]) if imp_col is not None else np.nan for ri, _ in of_prods],
                  index=[l for _, l in of_prods], name="importaciones")

    # UTILIZACION -> uso intermedio (producto x industria) y demanda final.
    U_utilizacion = _matrix(rows, ut_prods, ut_ind)
    last_ind = ut_ind[-1][0]
    fd_cols = []
    for c in range(last_ind + 1, len(rows[ut_hdr])):
        h = rows[ut_hdr][c]
        if not isinstance(h, str) or not h.strip():
            continue
        hu = _ascii(h)
        for key, canon in FD_MAP:
            if key in hu:
                fd_cols.append((c, canon))
                break
    Y_demanda_final = _matrix(rows, ut_prods, fd_cols)

    # Nota: el COU trae el valor agregado en un subcuadro aparte (Remuneraciones,
    # Excedente, Ingreso mixto, Impuestos) cuyas columnas NO se alinean 1:1 con
    # las 95 industrias del bloque de utilizacion. Para no publicar un vector
    # incoherente, NO se incluye W_valor_agregado en esta referencia.

    notas = pd.DataFrame({"nota": [
        "Cuadro de Oferta y Utilizacion (COU) oficial de Uruguay 2016, adjuntado "
        "como REFERENCIA del mismo marco estadistico de la MIP directa.",
        "Fuente: BCU. COU 2016 detallado, precios corrientes "
        "(hoja '2016 CORRIENTE' del archivo Uruguay_2016-2017 Detallada_COU_C).",
        "Estructura: 95 industrias (A.1..T.1) x 110 productos.",
        "V_oferta: industria x producto (make). U_utilizacion: producto x "
        "industria (uso intermedio). Y_demanda_final: consumo hogares, gobierno "
        "e ISFLSH, FBKF, variacion de existencias, exportaciones.",
        "El valor agregado existe en el COU en un subcuadro aparte "
        "(remuneraciones, excedente, ingreso mixto, impuestos) que no se alinea "
        "1:1 con las 95 industrias; no se incluye aqui para no inducir error.",
        "ALCANCE: el COU esta a 95 industrias x 110 productos; la MIP directa de "
        "Uruguay 2016 esta a 128 sectores (otra clasificacion). El COU se adjunta "
        "como referencia oficial del mismo anio, no como reconstruccion 1:1.",
        "Se adjunta SIN alterar la MIP publicada "
        "(tipo_matriz = MIP_directa_con_COU_referencia).",
    ]})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        V_oferta.to_excel(w, sheet_name="V_oferta")
        U_utilizacion.to_excel(w, sheet_name="U_utilizacion")
        Y_demanda_final.to_excel(w, sheet_name="Y_demanda_final")
        M.to_frame().to_excel(w, sheet_name="M_importaciones")
        notas.to_excel(w, sheet_name="notas", index=False)

    print("[OK] %s" % OUT.relative_to(ROOT))
    print("  V_oferta:", V_oferta.shape, " U_utilizacion:", U_utilizacion.shape)
    print("  industrias:", len(ut_ind), " productos:", len(ut_prods))
    print("  Y_demanda_final cols:", list(Y_demanda_final.columns))
    print("  produccion total (suma V): {:,.1f}".format(float(make.to_numpy().sum())))
    print("  uso intermedio total:      {:,.1f}".format(float(U_utilizacion.to_numpy().sum())))
    print("  demanda final total:       {:,.1f}".format(float(Y_demanda_final.to_numpy().sum())))


if __name__ == "__main__":
    main()
