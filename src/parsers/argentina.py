"""
Parser del COU de Argentina (INDEC) robusto a las dos variantes de formato:

  Formato A (2004): hoja 'Mat Oferta pb' con la producción a precios básicos y
     'Mat Utilizacion pc' que contiene el puente de valoración por producto
     (OPB, IMPO, Ajuste CIF/FOB, DI, IP, Mg Comercio, Mg Transporte, IVA, OPC).

  Formato B (2018-2022): hojas 'Mat_Of_pc_AAAA' y 'Mat_Ut_pc_AAAA'. La hoja de
     oferta trae la matriz de producción (precios básicos) y, al final, el
     puente de valoración por producto (Producción nacional, Importaciones,
     Ajuste, Derechos, Impuestos, Márgenes de distribución, IVA, Comisiones,
     Oferta total). La utilización es producto×industria + demanda final.

Devuelve un dict canónico con las mismas piezas en ambos casos:
    V_pi   producción  (prod × ind, precios básicos)
    U_pc   uso interm. (prod × ind, precios comprador)
    Y_pc   demanda final (prod × componentes)
    val    puente de valoración por producto: OPB, IMPO, Ajuste, DI, IP, IVA,
           Comisiones, Mg (márgenes combinados), OPC
    VA     valor agregado bruto agregado (1 × ind)
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd


def _norm(x) -> str:
    s = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


def _clean_code(x) -> str:
    return re.sub(r"\s+", "", str(x)).strip()


def _num(df: pd.DataFrame) -> np.ndarray:
    return df.apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()


_HEADER_LABELS = ("DESCRIPCION", "PRODUCTO", "DENOMINACION", "CODIGO", "CPC")
# palabras que marcan el fin del bloque de industrias (valoración / demanda final / totales)
_STOP_COL = ("PRODUCCION NACIONAL", "OFERTA TOTAL", "IMPORTACIONES", "AJUSTE CIF",
             "DERECHOS DE IMPORTACION", "IMPUESTOS A LOS PRODUCTOS", "IMPUESTO AL VALOR",
             "MARGENES", "COMISIONES", "UTILIZACION INTERMEDIA", "UTILIZACION FINAL",
             "GASTO DE CONSUMO", "EXPORTACIONES", "FORMACION BRUTA", "OBJETOS VALIOSOS",
             "VARIACION DE EXISTENCIAS", "DEMANDA TOTAL", "PRODUCCION TOTAL",
             "TRABAJOS EN CURSO")


def _header_row(df: pd.DataFrame) -> int:
    """Fila de encabezado: la que tiene una etiqueta de producto en col0/col1."""
    for r in range(min(15, df.shape[0])):
        for c in (0, 1):
            h = _norm(df.iat[r, c])
            if h.startswith(_HEADER_LABELS) and len(h) < 20:
                return r
    # respaldo: fila con más celdas de texto con letras (nombres de industria)
    best, bestr = -1, 0
    for r in range(min(15, df.shape[0])):
        cnt = sum(1 for c in range(2, df.shape[1])
                  if re.search(r"[A-Za-z]", str(df.iat[r, c])))
        if cnt > best:
            best, bestr = cnt, r
    return bestr

# palabras clave de las columnas del puente de valoración (por producto)
_VAL_KW = {
    "OPB": ["PRODUCCION NACIONAL"],
    "IMPO": ["IMPORTACIONES"],
    "Ajuste": ["AJUSTE CIF"],
    "DI": ["DERECHOS DE IMPORTACION"],
    "IP": ["IMPUESTOS A LOS PRODUCTOS"],
    "IVA": ["IMPUESTO AL VALOR AGREGADO"],
    "Comisiones": ["COMISIONES"],
    "MgC": ["MARGENES DE COMERCIO"],
    "MgT": ["MARGENES DE TRANSPORTE"],
    "MgD": ["MARGENES DE DISTRIBUCION", "MARGENES DE DIST"],
    "OPC": ["OFERTA TOTAL"],
}
# columnas de demanda final (en la hoja de utilización)
_FD_KW = {
    "consumo_hogares": ["GASTO DE CONSUMO FINAL DE LOS HOGARES", "GASTO DE CONSUMO FNAL DE LOS HOGARES"],
    "consumo_gobierno": ["GASTO DE CONSUMO FNAL DEL GOBIERNO", "GASTO DE CONSUMO FINAL DEL GOBIERNO"],
    "exportaciones": ["EXPORTACIONES"],
    "formacion_capital": ["FORMACION BRUTA"],
    "objetos_valiosos": ["OBJETOS VALIOSOS"],
    "var_existencias": ["VARIACION DE EXISTENCIAS"],
}
_FD_EXCLUDE = ["UTILIZACION INTERMEDIA", "UTILIZACION FINAL", "DEMANDA TOTAL"]
_STOP_PROD = ("TOTAL", "VALOR AGREGADO", "VALOR BRUTO")


def _find_cols(df: pd.DataFrame, hr: int, kwmap: dict, exclude=None) -> dict:
    exclude = exclude or []
    found = {}
    for c in range(2, df.shape[1]):
        h = _head2(df, hr, c)
        if not h or any(x in h for x in exclude):
            continue
        for name, kws in kwmap.items():
            if name in found:
                continue
            if any(_norm(k) in h for k in kws):
                found[name] = c
                break
    return found


def _head2(df: pd.DataFrame, hr: int, c: int) -> str:
    """Encabezado combinado: fila de nombre (hr-1) + fila de código (hr).

    En 2004 el nombre completo de las columnas está en hr-1 y el código corto en
    hr; en 2018+ todo está en hr. Concatenar cubre ambos casos.
    """
    partes = []
    for r in (hr - 1, hr):
        if 0 <= r < df.shape[0]:
            partes.append(str(df.iat[r, c]))
    return _norm(" ".join(partes))


def _industry_cols(df: pd.DataFrame, hr: int) -> list[int]:
    """Industrias = columnas con encabezado no vacío que NO son de valoración/demanda final/total."""
    out = []
    for c in range(2, df.shape[1]):
        h = _head2(df, hr, c)
        # el código de la industria vive en la fila hr; una celda NaN normaliza a
        # "NAN" (no vacía), por eso hay que descartarla explícitamente: si no, una
        # columna final toda-NaN se colaría como una industria fantasma "NAN NAN".
        if str(df.iat[hr, c]).strip().lower() in ("", "nan"):
            continue
        if any(k in h for k in _STOP_COL):
            continue
        out.append(c)
    return out


def _product_rows(df: pd.DataFrame, hr: int, code_col: int = 1) -> list[int]:
    rows = []
    for r in range(hr + 1, df.shape[0]):
        lab0 = _norm(df.iat[r, 0]); lab1 = _norm(df.iat[r, code_col])
        if lab0.startswith(_STOP_PROD) or lab1.startswith(_STOP_PROD):
            break
        if str(df.iat[r, code_col]).strip() not in ("", "nan"):
            rows.append(r)
    return rows


def _combined_margin(val: pd.DataFrame) -> pd.Series:
    if "MgD" in val:
        return val["MgD"]
    return val.get("MgC", 0) + val.get("MgT", 0)


def _strip_code(t: str) -> str:
    """Quita un código al inicio ('15120 - ', '011 - ') y al final (' 11')."""
    t = re.sub(r"^[0-9A-Z/]+\s*[-.]\s*", "", t)
    t = re.sub(r"\s+[0-9/]+$", "", t)
    t = re.sub(r"[^A-Z ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _name_key(df: pd.DataFrame, hr: int, c: int) -> str:
    """Clave de industria por nombre (primeros 30 caracteres significativos)."""
    return _strip_code(_head2(df, hr, c))[:30]


def _pname(df: pd.DataFrame, r: int) -> str:
    """Clave de producto por nombre (col0), robusta a diferencias de código."""
    return _strip_code(_norm(df.iat[r, 0]))[:40]


def _unique(keys: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out = []
    for k in keys:
        if k in seen:
            seen[k] += 1
            out.append(f"{k}#{seen[k]}")
        else:
            seen[k] = 0
            out.append(k)
    return out


def _orig_label(df: pd.DataFrame, hr: int, c: int) -> str:
    """Etiqueta en su MAYÚSCULA/minúscula original (fila de nombre + fila de código)."""
    partes = []
    for r in (hr - 1, hr):
        if 0 <= r < df.shape[0]:
            v = df.iat[r, c]
            if v is not None and str(v).strip() and str(v).strip().lower() != "nan":
                partes.append(str(v).strip())
    return " ".join(partes)


def _ind_code_name(df: pd.DataFrame, hr: int, c: int) -> tuple[str, str]:
    """Código (fila hr) y nombre (fila hr-1) legibles de una industria."""
    code = str(df.iat[hr, c]).strip()
    if code.lower() == "nan":
        code = ""
    name = str(df.iat[hr - 1, c]).strip() if hr - 1 >= 0 else ""
    if not name or name.lower() == "nan":
        name = code
    # quita un prefijo de código del nombre ('011 - ', '701 A - '), solo si empieza en dígito
    name = re.sub(r"^\s*[0-9][0-9A-Za-z/ ]*?\s*[-–.]\s*", "", name).strip()
    return code, name


def _split_code_name(texto: str) -> tuple[str, str]:
    """Separa 'código - nombre' o 'nombre código' en (código, nombre) legible."""
    texto = re.sub(r"\s+", " ", str(texto)).strip()
    m = re.match(r"^([0-9][0-9A-Za-z/]*)\s*[-.]\s*(.+)$", texto)      # '012 - Cría de animales'
    if m:
        code, name = m.group(1), m.group(2)
    else:
        m2 = re.match(r"^(.+?)\s+([0-9][0-9/]*)$", texto)             # 'Cría de animales 012'
        if m2:
            name, code = m2.group(1), m2.group(2)
        else:
            code, name = "", texto
    name = re.sub(r"\s+[0-9][0-9/]*\s*$", "", name).strip()           # quita código pegado al final
    return code, name


def _unidad(df: pd.DataFrame) -> str:
    """Lee la unidad del encabezado ('Año 2023 (millones de pesos)').

    INDEC cambió la escala: 2004–2022 vienen en MILES de pesos y 2023 en
    MILLONES. Hardcodearla desalineaba el libro por un factor de 1000, así que
    se lee del archivo y sólo se cae a 'miles' si no dice nada.
    """
    for r in range(min(8, df.shape[0])):
        for c in range(min(4, df.shape[1])):
            t = _norm(df.iat[r, c])
            if "MILLONES DE PESOS" in t:
                return "millones de pesos corrientes"
            if "MILES DE PESOS" in t:
                return "miles de pesos corrientes"
    return "miles de pesos corrientes"


def parse(ruta: str, anio: int, verbose: bool = False) -> dict:
    xl = pd.ExcelFile(ruta)
    of_sheet = next(s for s in xl.sheet_names if _norm(s).startswith(("MAT OFERTA", "MAT_OF")))
    ut_sheet = next(s for s in xl.sheet_names if _norm(s).startswith(("MAT UTILIZACION", "MAT_UT")))
    of = pd.read_excel(ruta, sheet_name=of_sheet, header=None)
    ut = pd.read_excel(ruta, sheet_name=ut_sheet, header=None)

    of_hr = _header_row(of); ut_hr = _header_row(ut)

    # ¿el puente de valoración está en la oferta (formato B) o en el uso (A)?
    val_in_of = _find_cols(of, of_hr, {"OPC": _VAL_KW["OPC"]})
    val_sheet, val_hr = (of, of_hr) if val_in_of else (ut, ut_hr)
    valcols = _find_cols(val_sheet, val_hr, _VAL_KW)
    val_rows = _product_rows(val_sheet, val_hr)
    val_codes = _unique([_pname(val_sheet, r) for r in val_rows])
    val = pd.DataFrame(
        {k: _num(val_sheet.iloc[val_rows, [c]]).ravel() for k, c in valcols.items()},
        index=val_codes,
    )
    val["Mg"] = _combined_margin(val)
    for col in ("OPB", "IMPO", "Ajuste", "DI", "IP", "IVA", "Comisiones", "OPC"):
        if col not in val:
            val[col] = 0.0

    # industrias y productos de la hoja de utilización.
    # Las industrias se alinean por NOMBRE (robusto a diferencias de código entre
    # las hojas de oferta y utilización, p.ej. '15120' vs '1512').
    ut_ind = _industry_cols(ut, ut_hr)
    ut_ikeys = _unique([_name_key(ut, ut_hr, c) for c in ut_ind])
    ut_rows = _product_rows(ut, ut_hr)
    ut_codes = _unique([_pname(ut, r) for r in ut_rows])

    U_pc = pd.DataFrame(_num(ut.iloc[ut_rows, ut_ind]), index=ut_codes, columns=ut_ikeys)
    fdcols = _find_cols(ut, ut_hr, _FD_KW, exclude=_FD_EXCLUDE)
    Y_pc = pd.DataFrame(
        {k: _num(ut.iloc[ut_rows, [c]]).ravel() for k, c in fdcols.items()},
        index=ut_codes,
    )

    # producción V (prod × ind) a precios básicos
    of_ind = _industry_cols(of, of_hr)
    of_ikeys = _unique([_name_key(of, of_hr, c) for c in of_ind])
    of_rows = _product_rows(of, of_hr)
    of_codes = _unique([_pname(of, r) for r in of_rows])
    V_pi = pd.DataFrame(_num(of.iloc[of_rows, of_ind]), index=of_codes, columns=of_ikeys)
    V_pi = (V_pi.groupby(level=0).sum().T.groupby(level=0).sum().T
            .reindex(index=ut_codes, columns=ut_ikeys).fillna(0.0))

    # valor agregado bruto (fila 'Valor Agregado Bruto pb')
    va_row = None
    for r in range(ut_rows[-1] + 1, ut.shape[0]):
        if _norm(ut.iat[r, 0]).startswith("VALOR AGREGADO"):
            va_row = r
            break
    VA = pd.DataFrame(_num(ut.iloc[[va_row], ut_ind]), index=["valor_agregado_bruto"], columns=ut_ikeys)

    val = val.reindex(index=ut_codes).fillna(0.0)
    # códigos y nombres legibles (en su caso original), consistentes
    ind_code, ind_name = {}, {}
    for k, c in zip(ut_ikeys, ut_ind):
        code, name = _ind_code_name(ut, ut_hr, c)
        ind_code[k] = code or k
        ind_name[k] = name or k
    prod_code, prod_name = {}, {}
    for k, r in zip(ut_codes, ut_rows):
        code, name = _split_code_name(str(ut.iat[r, 0]))
        prod_code[k] = _clean_code(ut.iat[r, 1]) or code or k
        prod_name[k] = name or k
    labels = {k: f"{prod_code[k]} - {prod_name[k]}" for k in ut_codes}
    ind_labels = {k: f"{ind_code[k]} - {ind_name[k]}" for k in ut_ikeys}
    ut_ind_codes = ut_ikeys

    if verbose:
        print(f"  [AR {anio}] fmt={'B' if val_in_of else 'A'} prod={len(ut_codes)} "
              f"ind={len(ut_ind_codes)} valcols={list(valcols)} fd={list(fdcols)}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "Y_pc": Y_pc, "val": val, "VA": VA,
        "prod_labels": labels, "ind_labels": ind_labels,
        "ind_code": ind_code, "ind_name": ind_name,
        "prod_code": prod_code, "prod_name": prod_name,
        "pais": "Argentina", "anio": anio, "unidad": _unidad(of),
    }
