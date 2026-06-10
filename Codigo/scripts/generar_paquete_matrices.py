# -*- coding: utf-8 -*-
"""Genera un paquete pais/anio con MIP extendidas y validaciones."""

from pathlib import Path
import re

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
DATA_PROC = ROOT / "data" / "processed"
OUTPUT_ROOT = ROOT / "output" / "matrices_insumo_producto"

NAVY = "0D2B6E"
BLUE = "105FC0"
LIGHT_BLUE = "E8F4FD"
LIGHT = "F8FAFC"
WARN = "FFF3CD"
BAD = "F8D7DA"
TEXT = "102A43"
MUTED = "627D98"
THIN = Side(style="thin", color="D9E2EC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


COUNTRY_FOLDER = {
    "argentina": "Argentina",
    "argentina_mip97": "Argentina",
    "brasil": "Brasil",
    "brasil_early": "Brasil",
    "mexico": "Mexico",
    "uruguay": "Uruguay",
    "uruguay_cou": "Uruguay",
}

SOURCE_LABEL = {
    "argentina": "COU INDEC/CEPAL",
    "argentina_mip97": "MIPAr97 INDEC directa",
    "brasil": "COU IBGE nivel 68",
    "brasil_early": "COU CEPAL Brasil base 2000",
    "mexico": "MIP directa CEPAL/INEGI",
    "uruguay": "MIP directa BCU 2016",
    "uruguay_cou": "COU CEPAL Uruguay 2017",
}


def parse_country_year(path: Path) -> tuple[str, int] | None:
    match = re.match(r"mip_(.+)_(\d{4})(?:_[A-Za-z0-9]+)?\.xlsx$", path.name)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def read_processed(path: Path) -> dict:
    sheets = pd.read_excel(path, sheet_name=None, index_col=0)
    data = {
        "Z": sheets["Z_flujos"].apply(pd.to_numeric, errors="coerce").fillna(0),
        "A": sheets["A_coeficientes"].apply(pd.to_numeric, errors="coerce").fillna(0),
        "L": sheets["L_leontief"].apply(pd.to_numeric, errors="coerce").fillna(0),
        "g": sheets["produccion"].iloc[:, 0].pipe(pd.to_numeric, errors="coerce").fillna(0),
    }
    if "valor_agregado" in sheets:
        data["W"] = sheets["valor_agregado"].iloc[:, 0].pipe(pd.to_numeric, errors="coerce").fillna(0)
    else:
        data["W"] = pd.Series(0.0, index=data["Z"].index, name="valor_agregado")
    if "demanda_final" in sheets:
        data["f"] = sheets["demanda_final"].iloc[:, 0].pipe(pd.to_numeric, errors="coerce").fillna(0)
    else:
        data["f"] = data["g"].reindex(data["Z"].index).fillna(0) - data["Z"].sum(axis=1)
    if "ci_importado" in sheets:
        data["Mci"] = sheets["ci_importado"].iloc[:, 0].pipe(pd.to_numeric, errors="coerce").fillna(0)
    else:
        data["Mci"] = pd.Series(0.0, index=data["Z"].index, name="ci_importado")
    if "Z_importada" in sheets:
        data["Z_m"] = sheets["Z_importada"].apply(pd.to_numeric, errors="coerce").fillna(0)
    if "ajuste_cierre" in sheets:
        data["ajuste_cierre"] = sheets["ajuste_cierre"]
    if "Z_pre_conciliacion" in sheets:
        data["Z_pre_conciliacion"] = sheets["Z_pre_conciliacion"].apply(pd.to_numeric, errors="coerce").fillna(0)
    return data


def matrix_from_values(values, index, columns):
    return pd.DataFrame(values, index=index, columns=columns)


def has_sector_name(label) -> bool:
    text = str(label).strip()
    if "—" in text or "---" in text:
        return len(text.split("—", 1)[-1].split("---", 1)[-1].strip()) >= 3
    if re.fullmatch(r"(\d+|\d+/\d+|P\d+|A\.\d+|[A-Z]\.\d+)", text):
        return False
    return any(ch.isalpha() for ch in text) and len(text) >= 3


def compute_extended(data: dict) -> dict:
    Z = data["Z"]
    A = data["A"]
    L = data["L"]
    g = data["g"].reindex(Z.index).fillna(0)
    W = data["W"].reindex(Z.index).fillna(0)
    f = data["f"].reindex(Z.index).fillna(0)
    Mci = data["Mci"].reindex(Z.index).fillna(0)
    sectors = list(Z.index)
    n = len(sectors)
    I = np.eye(n)

    z_values = Z.to_numpy(dtype=float)
    a_values = A.to_numpy(dtype=float)
    l_values = L.to_numpy(dtype=float)
    g_values = g.to_numpy(dtype=float)

    # Leontief: columnas normalizadas por produccion del sector comprador.
    g_col = np.where(np.abs(g_values) > 0, g_values, np.nan)
    A_calc = np.divide(
        z_values,
        g_col[np.newaxis, :],
        out=np.zeros_like(z_values),
        where=~np.isnan(g_col[np.newaxis, :]),
    )

    # Ghosh: filas normalizadas por produccion del sector vendedor.
    g_row = np.where(np.abs(g_values) > 0, g_values, np.nan)
    B_values = np.divide(
        z_values,
        g_row[:, np.newaxis],
        out=np.zeros_like(z_values),
        where=~np.isnan(g_row[:, np.newaxis]),
    )
    try:
        G_values = np.linalg.inv(I - B_values)
    except np.linalg.LinAlgError:
        G_values = np.linalg.pinv(I - B_values)

    leontief_residual = (I - a_values) @ l_values - I
    ghosh_residual = (I - B_values) @ G_values - I
    compras_col = pd.Series(Z.sum(axis=0).to_numpy(dtype=float), index=sectors)
    ventas_row = pd.Series(Z.sum(axis=1).to_numpy(dtype=float), index=sectors)
    va_residual = pd.Series(
        g.to_numpy(dtype=float) - compras_col.to_numpy(dtype=float) - Mci.to_numpy(dtype=float),
        index=sectors,
    )
    fd_residual = pd.Series(g.to_numpy(dtype=float) - ventas_row.to_numpy(dtype=float), index=sectors)
    oferta_demanda_diff = pd.Series(
        g.to_numpy(dtype=float) - ventas_row.to_numpy(dtype=float) - f.to_numpy(dtype=float),
        index=sectors,
    )

    balances = pd.DataFrame({
        "produccion_bruta_g": g,
        "compras_intermedias_colsum_Z": compras_col,
        "ventas_intermedias_rowsum_Z": ventas_row,
        "demanda_final_f": f,
        "ajuste_intermedio_no_basico": Mci,
        "valor_agregado_W": W,
        "valor_agregado_residual_g_menos_compras_menos_importado": va_residual,
        "demanda_final_residual_g_menos_ventas": fd_residual,
        "oferta_menos_demanda_g_menos_Zrow_menos_f": oferta_demanda_diff,
        "flag_Z_row_final_negativa": fd_residual < -1e-8,
        "flag_demanda_final_f_negativa": f < -1e-8,
        "flag_VA_residual_negativo": va_residual < -1e-8,
    })

    multipliers = pd.DataFrame({
        "mult_leontief_produccion_colsum": pd.Series(L.sum(axis=0).to_numpy(dtype=float), index=sectors),
        "encadenamiento_adelante_leontief_rowsum": pd.Series(L.sum(axis=1).to_numpy(dtype=float), index=sectors),
        "mult_ghosh_supply_rowsum": matrix_from_values(G_values, sectors, sectors).sum(axis=1),
        "encadenamiento_ghosh_colsum": matrix_from_values(G_values, sectors, sectors).sum(axis=0),
        "produccion_bruta_g": g,
        "valor_agregado_W": W,
        "ajuste_intermedio_no_basico": Mci,
    })

    validation_rows = [
        ("cuadrada_Z_A_L", Z.shape == A.shape == L.shape == (n, n), "Z, A y L son n x n"),
        (
            "etiquetas_alineadas",
            [str(x) for x in Z.index] == [str(x) for x in Z.columns]
            and [str(x) for x in A.index] == [str(x) for x in Z.index]
            and [str(x) for x in L.index] == [str(x) for x in Z.index]
            and [str(x) for x in g.index] == [str(x) for x in Z.index],
            "filas, columnas y vectores comparten sectores",
        ),
        ("nombres_sectoriales", all(has_sector_name(x) for x in sectors), "cada sector debe tener nombre economico, no solo codigo"),
        ("no_negatividad_Z_A_g", min(float(Z.min().min()), float(A.min().min()), float(g.min())) >= -1e-8, "Z, A y g sin negativos relevantes"),
        ("max_abs_A_menos_Z_sobre_g", float(np.nanmax(np.abs(a_values - A_calc))), "debe ser cercano a 0"),
        ("max_abs_Leontief", float(np.nanmax(np.abs(leontief_residual))), "(I-A)L - I debe ser cercano a 0"),
        ("max_abs_Ghosh", float(np.nanmax(np.abs(ghosh_residual))), "(I-B)G - I debe ser cercano a 0"),
        ("max_abs_oferta_menos_demanda", float(np.nanmax(np.abs(oferta_demanda_diff))), "g - sum_row(Z) - f debe ser cercano a 0"),
        ("celdas_negativas_Z", int((Z.to_numpy(dtype=float) < -1e-8).sum()), "conteo de flujos negativos"),
        ("sectores_demanda_final_residual_negativa", int((fd_residual < -1e-8).sum()), "diagnostico de cierre por filas"),
        ("sectores_va_residual_negativo", int((va_residual < -1e-8).sum()), "diagnostico de cierre por columnas"),
    ]
    validation = pd.DataFrame(validation_rows, columns=["prueba", "resultado", "criterio"])

    return {
        "A_calc": matrix_from_values(A_calc, sectors, sectors),
        "B_ghosh": matrix_from_values(B_values, sectors, sectors),
        "G_ghosh": matrix_from_values(G_values, sectors, sectors),
        "validacion_resumen": validation,
        "validacion_A_diferencia": matrix_from_values(a_values - A_calc, sectors, sectors),
        "validacion_Leontief_residual": matrix_from_values(leontief_residual, sectors, sectors),
        "validacion_Ghosh_residual": matrix_from_values(ghosh_residual, sectors, sectors),
        "balances_sectoriales": balances,
        "multiplicadores": multipliers,
        "Z_importada": data.get("Z_m"),
    }


def sheet_safe(df: pd.DataFrame, writer, name: str, index: bool = True):
    df.to_excel(writer, sheet_name=name[:31], index=index)


def read_source_sheets(path: Path | None) -> dict[str, pd.DataFrame]:
    if path is None or not path.exists():
        return {}
    return pd.read_excel(path, sheet_name=None, index_col=0)


def source_file_for(source_key: str, year: int) -> Path | None:
    candidate = DATA_PROC / source_key / f"cou_{source_key}_{year}.xlsx"
    return candidate if candidate.exists() else None


def source_notes(source_sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    notes = source_sheets.get("notas")
    if notes is None:
        return pd.DataFrame({"nota": ["Sin hoja de notas en la fuente procesada."]})
    values = []
    values.extend([str(x) for x in notes.index if str(x).strip() and str(x) != "nan"])
    for col in notes.columns:
        values.extend([str(x) for x in notes[col].dropna().tolist() if str(x).strip() and str(x) != "nan"])
    values = list(dict.fromkeys(values))
    return pd.DataFrame({"nota": values or ["Hoja de notas vacia."]})


def build_source_summary(
    source_key: str,
    year: int,
    mip_path: Path,
    cou_path: Path | None,
    source_sheets: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = [
        ("pais_publicado", COUNTRY_FOLDER.get(source_key, source_key)),
        ("serie_fuente", source_key),
        ("anio", year),
        ("tipo_matriz", "reconstruida_desde_COU" if cou_path else "MIP_directa_o_fuente_equivalente"),
        ("fuente_metodologica", SOURCE_LABEL.get(source_key, source_key)),
        ("archivo_mip_procesado", str(mip_path.relative_to(ROOT))),
        ("archivo_cou_procesado", str(cou_path.relative_to(ROOT)) if cou_path else "no_aplica"),
        ("criterio_sectores", "Las actividades fuente son filas de V_oferta, columnas de U_utilizacion y columnas de W_valor_agregado."),
        ("nota_diagonal_cero", "Un sector con diagonal Z[i,i] = 0 se conserva si tiene produccion, valor agregado, ventas o compras. No es obligatorio que un sector se compre a si mismo."),
        ("nota_productos", "Los productos del COU no necesariamente aparecen como sectores: se transforman a industrias mediante D_market_share."),
    ]
    for sheet_name, df in source_sheets.items():
        rows.append((f"dim_{sheet_name}", f"{df.shape[0]} filas x {df.shape[1]} columnas"))
    return pd.DataFrame(rows, columns=["campo", "valor"])


def build_sector_coverage(
    data: dict,
    source_sheets: dict[str, pd.DataFrame],
    source_key: str,
) -> pd.DataFrame:
    Z = data["Z"]
    g = data["g"].reindex(Z.index).fillna(0)
    f = data["f"].reindex(Z.index).fillna(0)
    W = data["W"].reindex(Z.index).fillna(0)
    Mci = data["Mci"].reindex(Z.index).fillna(0)
    mip_sectors = [str(x) for x in Z.index]

    V = source_sheets.get("V_oferta")
    U = source_sheets.get("U_utilizacion")
    Wsrc = source_sheets.get("W_valor_agregado")
    has_cou = V is not None or U is not None or Wsrc is not None

    source_labels = []
    if V is not None:
        source_labels.extend([str(x) for x in V.index])
    if U is not None:
        source_labels.extend([str(x) for x in U.columns])
    if Wsrc is not None:
        source_labels.extend([str(x) for x in Wsrc.columns])
    if not has_cou:
        source_labels = mip_sectors.copy()

    source_order = list(dict.fromkeys(source_labels))
    all_labels = list(dict.fromkeys(mip_sectors + [x for x in source_order if x not in mip_sectors]))

    rows = []
    for label in all_labels:
        in_mip = label in mip_sectors
        en_V = bool(V is not None and label in [str(x) for x in V.index])
        en_U_col = bool(U is not None and label in [str(x) for x in U.columns])
        en_W_col = bool(Wsrc is not None and label in [str(x) for x in Wsrc.columns])
        in_source = (en_V or en_U_col or en_W_col) if has_cou else in_mip

        if in_mip:
            original_label = Z.index[mip_sectors.index(label)]
            row_sum = float(Z.loc[original_label].sum())
            col_sum = float(Z[original_label].sum())
            diagonal = float(Z.loc[original_label, original_label])
            g_val = float(g.loc[original_label])
            f_val = float(f.loc[original_label])
            w_val = float(W.loc[original_label])
            mci_val = float(Mci.loc[original_label])
        else:
            row_sum = col_sum = diagonal = g_val = f_val = w_val = mci_val = np.nan

        diagonal_cero_con_flujos = (
            in_mip
            and abs(diagonal) <= 1e-8
            and (abs(row_sum) > 1e-8 or abs(col_sum) > 1e-8 or abs(g_val) > 1e-8)
        )
        if in_mip and in_source:
            decision = "incluido"
        elif in_source and not in_mip:
            decision = "revisar_fuente_no_incluida_en_MIP"
        elif in_mip and not in_source:
            decision = "revisar_MIP_sin_actividad_COU"
        else:
            decision = "revisar"

        nota = ""
        if diagonal_cero_con_flujos:
            nota = "Incluido aunque Z[i,i]=0: no se exige autoconsumo sectorial."
        if not has_cou:
            nota = "MIP directa: la cobertura se toma de la matriz publicada/procesada."

        rows.append({
            "sector": label,
            "en_MIP_final": in_mip,
            "en_fuente_actividad": in_source,
            "en_V_oferta_fila": en_V if has_cou else np.nan,
            "en_U_utilizacion_columna": en_U_col if has_cou else np.nan,
            "en_W_valor_agregado_columna": en_W_col if has_cou else np.nan,
            "decision_cobertura": decision,
            "produccion_g": g_val,
            "demanda_final_f": f_val,
            "valor_agregado_W": w_val,
            "ajuste_intermedio_no_basico": mci_val,
            "ventas_intermedias_fila_Z": row_sum,
            "compras_intermedias_columna_Z": col_sum,
            "diagonal_Z_ii": diagonal,
            "diagonal_cero_con_flujos": diagonal_cero_con_flujos,
            "nota": nota,
        })
    return pd.DataFrame(rows)


def build_product_coverage(source_sheets: dict[str, pd.DataFrame]) -> pd.DataFrame | None:
    V = source_sheets.get("V_oferta")
    U = source_sheets.get("U_utilizacion")
    Y = source_sheets.get("Y_demanda_final")
    M = source_sheets.get("M_importaciones")
    if V is None and U is None and Y is None and M is None:
        return None

    labels = []
    if V is not None:
        labels.extend([str(x) for x in V.columns])
    if U is not None:
        labels.extend([str(x) for x in U.index])
    if Y is not None:
        labels.extend([str(x) for x in Y.index])
    if M is not None:
        labels.extend([str(x) for x in M.index])
    all_labels = list(dict.fromkeys(labels))

    rows = []
    v_cols = [str(x) for x in V.columns] if V is not None else []
    u_idx = [str(x) for x in U.index] if U is not None else []
    y_idx = [str(x) for x in Y.index] if Y is not None else []
    m_idx = [str(x) for x in M.index] if M is not None else []
    for label in all_labels:
        row = {
            "producto": label,
            "en_V_oferta_columna": label in v_cols,
            "en_U_utilizacion_fila": label in u_idx,
            "en_Y_demanda_final_fila": label in y_idx,
            "en_M_importaciones_fila": label in m_idx,
            "lectura": "Producto COU: se transforma a industrias con D_market_share; no necesariamente aparece como sector en Z_MIP.",
        }
        if V is not None and label in v_cols:
            row["produccion_producto_q"] = float(V.iloc[:, v_cols.index(label)].sum())
        if U is not None and label in u_idx:
            row["uso_intermedio_producto"] = float(U.iloc[u_idx.index(label), :].sum())
        if Y is not None and label in y_idx:
            row["demanda_final_producto"] = float(Y.iloc[y_idx.index(label), :].sum())
        if M is not None and label in m_idx:
            row["importaciones_producto"] = float(M.iloc[m_idx.index(label), :].sum())
        rows.append(row)
    return pd.DataFrame(rows)


SOURCE_EXPORT_SHEETS = {
    "V_oferta": "src_V_oferta",
    "U_utilizacion": "src_U_utilizacion",
    "Y_demanda_final": "src_Y_demanda_final",
    "W_valor_agregado": "src_W_valor_agregado",
    "M_importaciones": "src_M_importaciones",
    "U_importada": "src_U_importada",
    "T_margenes": "src_T_margenes",
    "IMP_impuestos": "src_IMP_impuestos",
}


def style_workbook(path: Path):
    wb = load_workbook(path)
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
        max_row = ws.max_row
        max_col = ws.max_column
        if max_row == 0 or max_col == 0:
            continue

        ws.freeze_panes = "B2" if max_col > 2 else "A2"
        ws.auto_filter.ref = ws.dimensions

        for cell in ws[1]:
            cell.fill = PatternFill("solid", fgColor=NAVY)
            cell.font = Font(bold=True, color="FFFFFF", size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = BORDER
        ws.row_dimensions[1].height = 28

        style_all_cells = (max_row * max_col) <= 30000
        data_max_col = max_col if style_all_cells else min(max_col, 12)
        for row in ws.iter_rows(min_row=2, max_row=max_row, max_col=data_max_col):
            for cell in row:
                if cell.value is None:
                    continue
                cell.border = BORDER
                cell.font = Font(size=9, color=TEXT)
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if isinstance(cell.value, (int, float)):
                    cell.number_format = "#,##0.0000"
            if style_all_cells and row[0].row % 2 == 0:
                for cell in row:
                    if cell.value is not None:
                        cell.fill = PatternFill("solid", fgColor=LIGHT)

        if ws.max_column >= 1:
            for cell in next(ws.iter_cols(min_col=1, max_col=1, min_row=2, max_row=max_row)):
                if cell.value is not None:
                    cell.fill = PatternFill("solid", fgColor=LIGHT_BLUE)
                    cell.font = Font(size=9, color=NAVY, bold=True)

        if ws.title == "README":
            ws.freeze_panes = "A2"
            ws.column_dimensions["A"].width = 34
            ws.column_dimensions["B"].width = 105
        elif ws.title in {"fuente_resumen", "fuente_notas"}:
            ws.freeze_panes = "A2"
            ws.column_dimensions["A"].width = 36
            ws.column_dimensions["B"].width = 110
        elif ws.title in {"cobertura_sectores", "cobertura_productos"}:
            ws.freeze_panes = "A2"
            for col in range(1, max_col + 1):
                ws.column_dimensions[get_column_letter(col)].width = 24 if col > 1 else 46
            for row in ws.iter_rows(min_row=2, max_row=max_row):
                decision = str(row[6].value).lower() if ws.title == "cobertura_sectores" and len(row) > 6 else ""
                if "revisar" in decision:
                    for cell in row:
                        if cell.value is not None:
                            cell.fill = PatternFill("solid", fgColor=WARN)
                elif ws.title == "cobertura_sectores" and len(row) > 14 and str(row[14].value).upper() == "TRUE":
                    for cell in row:
                        if cell.value is not None:
                            cell.fill = PatternFill("solid", fgColor=LIGHT_BLUE)
        elif ws.title.startswith("validacion") or ws.title == "balances_sectoriales":
            for col in range(1, max_col + 1):
                ws.column_dimensions[get_column_letter(col)].width = 22
            for row in ws.iter_rows(min_row=2, max_row=max_row):
                for cell in row:
                    value = str(cell.value).upper()
                    if value == "FALSE" or value == "REVISAR":
                        cell.fill = PatternFill("solid", fgColor=BAD)
                    elif value == "TRUE" or value == "OK":
                        cell.fill = PatternFill("solid", fgColor="D4EFDF")
        else:
            for col in range(1, min(max_col, 60) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 13 if col > 1 else 34

    wb.save(path)


def write_year_file(path: Path, out_path: Path):
    parsed = parse_country_year(path)
    if parsed is None:
        return None
    source_key, year = parsed
    country = COUNTRY_FOLDER.get(source_key, source_key)
    data = read_processed(path)
    ext = compute_extended(data)
    cou_path = source_file_for(source_key, year)
    source_sheets = read_source_sheets(cou_path)
    fuente_resumen = build_source_summary(source_key, year, path, cou_path, source_sheets)
    cobertura_sectores = build_sector_coverage(data, source_sheets, source_key)
    cobertura_productos = build_product_coverage(source_sheets)
    notas_fuente = source_notes(source_sheets)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = pd.DataFrame([
        ("pais", country),
        ("serie_fuente", source_key),
        ("fuente_metodologica", SOURCE_LABEL.get(source_key, source_key)),
        ("anio", year),
        ("archivo_origen", str(path.relative_to(ROOT))),
        ("descripcion_Z", "Matriz insumo-producto / flujos intermedios"),
        ("descripcion_Z", "Z contiene solo consumo intermedio nacional/domestico cuando la fuente permite separarlo o estimarlo."),
        ("descripcion_ajuste_intermedio", "Ajuste intermedio fuera de Z. En MIP directas puede ser CI importado; en COU reconstruidos con puente de precios puede incluir importaciones, margenes, impuestos y diferencias de valoracion comprador-basico."),
        ("descripcion_fuente_resumen", "Resumen de la fuente usada, archivo COU cuando aplica y dimensiones de las hojas fuente."),
        ("descripcion_cobertura_sectores", "Auditoria sectorial: compara actividades del COU contra sectores de la MIP final y marca diagonal cero sin tratarlo como error."),
        ("descripcion_cobertura_productos", "Auditoria de productos COU: productos se transforman a sectores mediante D_market_share y no siempre aparecen como sectores."),
        ("descripcion_A", "Coeficientes tecnicos de Leontief: A = Z * diag(g)^-1"),
        ("descripcion_L", "Inversa de Leontief: L = (I - A)^-1"),
        ("descripcion_B_ghosh", "Coeficientes de distribucion de Ghosh: B = diag(g)^-1 * Z"),
        ("descripcion_G_ghosh", "Inversa de Ghosh: G = (I - B)^-1"),
    ], columns=["campo", "valor"])

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        sheet_safe(metadata, writer, "README", index=False)
        sheet_safe(fuente_resumen, writer, "fuente_resumen", index=False)
        sheet_safe(cobertura_sectores, writer, "cobertura_sectores", index=False)
        if cobertura_productos is not None:
            sheet_safe(cobertura_productos, writer, "cobertura_productos", index=False)
        sheet_safe(notas_fuente, writer, "fuente_notas", index=False)
        for source_sheet, output_sheet in SOURCE_EXPORT_SHEETS.items():
            if source_sheet in source_sheets:
                sheet_safe(source_sheets[source_sheet], writer, output_sheet)
        sheet_safe(data["Z"], writer, "Z_MIP")
        sheet_safe(data["A"], writer, "A_coef_tecnicos")
        sheet_safe(data["L"], writer, "L_leontief")
        sheet_safe(ext["B_ghosh"], writer, "B_ghosh_coef")
        sheet_safe(ext["G_ghosh"], writer, "G_ghosh_inversa")
        sheet_safe(data["g"].to_frame("produccion_bruta"), writer, "g_produccion")
        sheet_safe(data["W"].to_frame("valor_agregado"), writer, "W_valor_agregado")
        sheet_safe(data["f"].to_frame("demanda_final"), writer, "f_demanda_final")
        sheet_safe(data["Mci"].to_frame("ajuste_intermedio_no_basico"), writer, "ajuste_intermedio")
        if data.get("ajuste_cierre") is not None:
            sheet_safe(data["ajuste_cierre"], writer, "ajuste_cierre")
        if data.get("Z_pre_conciliacion") is not None:
            sheet_safe(data["Z_pre_conciliacion"], writer, "Z_pre_conciliacion")
        if ext.get("Z_importada") is not None:
            sheet_safe(ext["Z_importada"], writer, "Z_importada")
        sheet_safe(ext["multiplicadores"], writer, "multiplicadores")
        sheet_safe(ext["balances_sectoriales"], writer, "balances_sectoriales")
        sheet_safe(ext["validacion_resumen"], writer, "validacion_resumen", index=False)
        sheet_safe(ext["validacion_A_diferencia"], writer, "val_A_menos_Zg")
        sheet_safe(ext["validacion_Leontief_residual"], writer, "val_Leontief")
        sheet_safe(ext["validacion_Ghosh_residual"], writer, "val_Ghosh")

    style_workbook(out_path)

    return {
        "pais": country,
        "serie_fuente": source_key,
        "anio": year,
        "archivo": str(out_path.relative_to(ROOT)),
    }


def main():
    rows = []
    for path in sorted(DATA_PROC.glob("*/mip_*.xlsx")):
        parsed = parse_country_year(path)
        if parsed is None:
            continue
        source_key, year = parsed
        country = COUNTRY_FOLDER.get(source_key, source_key)
        out_name = f"MIP_{country}_{year}.xlsx"
        out_path = OUTPUT_ROOT / country / out_name
        row = write_year_file(path, out_path)
        if row:
            rows.append(row)
            print(f"[OK] {out_path.relative_to(ROOT)}")

    summary = pd.DataFrame(rows).sort_values(["pais", "anio"])
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    summary.to_excel(OUTPUT_ROOT / "indice_matrices_insumo_producto.xlsx", index=False)
    print(f"\n[OK] {OUTPUT_ROOT / 'indice_matrices_insumo_producto.xlsx'}")


if __name__ == "__main__":
    main()
