# -*- coding: utf-8 -*-
"""Simplifica los Excel MIP publicados a una estructura pedagogica.

No recalcula ni reconstruye las matrices. Lee cada workbook ya publicado en
MIP/{Pais}/MIP_{Pais}_{Anio}.xlsx y conserva solo las hojas de entrega:

1. Indice
2. COU_Tabla_Original
3. Z_consumos_intermedios
4. x_produccion_bruta
5. y_demanda_final
6. X_hat
7. A_coef_tecnicos
8. L_leontief
9. B_coef_distribucion

Las validaciones quedan en los archivos consolidados de la raiz:
validacion_matematica_mip.* y auditoria_cobertura_sectores_mip.*.
"""

from __future__ import annotations

from pathlib import Path
import os
import tempfile

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


REPO_ROOT = Path(__file__).resolve().parents[2]
MIP_ROOT = REPO_ROOT / "MIP"

NAVY = "0D2B6E"
BLUE = "105FC0"
LIGHT_BLUE = "E8F4FD"
LIGHT = "F8FAFC"
TEXT = "102A43"
MUTED = "627D98"
WHITE = "FFFFFF"
THIN = Side(style="thin", color="D9E2EC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


OUTPUT_SHEETS = [
    "Indice",
    "COU_Tabla_Original",
    "Z_consumos_intermedios",
    "x_produccion_bruta",
    "y_demanda_final",
    "X_hat",
    "A_coef_tecnicos",
    "L_leontief",
    "B_coef_distribucion",
]


def read_sheet(xls: pd.ExcelFile, name: str, index_col: int | None = 0) -> pd.DataFrame | None:
    if name not in xls.sheet_names:
        return None
    return pd.read_excel(xls, sheet_name=name, index_col=index_col)


def as_numeric_df(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None:
        return None
    out = df.copy()
    out.index = [str(i).strip() for i in out.index]
    out.columns = [str(c).strip() for c in out.columns]
    return out.apply(pd.to_numeric, errors="coerce").fillna(0.0)


def first_existing(xls: pd.ExcelFile, names: list[str]) -> pd.DataFrame | None:
    for name in names:
        df = read_sheet(xls, name)
        if df is not None:
            return df
    return None


def meta_map(xls: pd.ExcelFile) -> dict[str, str]:
    meta = read_sheet(xls, "fuente_resumen", index_col=None)
    if meta is None or not {"campo", "valor"}.issubset(set(meta.columns)):
        indice = read_sheet(xls, "Indice", index_col=None)
        if indice is not None and {"campo", "descripcion"}.issubset(set(indice.columns)):
            return {
                str(row["campo"]).strip(): "" if pd.isna(row["descripcion"]) else str(row["descripcion"])
                for _, row in indice.iterrows()
            }
        return {}
    return {
        str(row["campo"]).strip(): "" if pd.isna(row["valor"]) else str(row["valor"])
        for _, row in meta.iterrows()
    }


def build_index(path: Path, xls: pd.ExcelFile, meta: dict[str, str]) -> pd.DataFrame:
    src_count = sum(1 for s in xls.sheet_names if s.startswith("src_"))
    rows = [
        ("Archivo", path.name),
        ("Pais", meta.get("pais_publicado", path.parent.name)),
        ("Anio", meta.get("anio", "")),
        ("Tipo de matriz", meta.get("tipo_matriz", "")),
        ("Serie fuente", meta.get("serie_fuente", "")),
        ("Fuente metodologica", meta.get("fuente_metodologica", "")),
        ("COU procesado", meta.get("archivo_cou_procesado", "no_aplica")),
        ("COU de referencia", meta.get("archivo_cou_referencia", "")),
        ("Hojas COU/fuente adjuntas", str(src_count)),
        ("Lectura", "Libro simplificado para explicacion. Las validaciones estan en archivos consolidados separados."),
        ("", ""),
        ("HOJA", "CONTENIDO"),
        ("COU_Tabla_Original", "Tablas fuente COU cuando existen; si no hay COU publico, notas de fuente original."),
        ("Z_consumos_intermedios", "Matriz Z de consumos intermedios sector vendedor x sector comprador."),
        ("x_produccion_bruta", "Vector x de produccion bruta y componentes de cierre por sector."),
        ("y_demanda_final", "Vector y de demanda final; incluye componentes cuando la fuente los trae."),
        ("X_hat", "Matriz diagonal de produccion bruta, diag(x)."),
        ("A_coef_tecnicos", "Matriz A de coeficientes tecnicos, A = Z * X_hat^-1."),
        ("L_leontief", "Inversa de Leontief, L = (I - A)^-1."),
        ("B_coef_distribucion", "Matriz B de coeficientes de distribucion de Ghosh, B = X_hat^-1 * Z."),
    ]
    return pd.DataFrame(rows, columns=["campo", "descripcion"])


def build_x_components(xls: pd.ExcelFile, sectors: list[str]) -> pd.DataFrame:
    x = first_existing(xls, ["x_produccion_bruta", "g_produccion"])
    if x is None:
        raise ValueError("No se encontro vector de produccion bruta")
    balances = read_sheet(xls, "balances_sectoriales")
    if balances is None and x.shape[1] > 1:
        out = x.apply(pd.to_numeric, errors="coerce").fillna(0.0).reindex(sectors).fillna(0.0)
        out.index.name = "sector"
        return clean_x_components(out)

    x_series = pd.to_numeric(x.iloc[:, 0], errors="coerce").fillna(0.0).reindex(sectors).fillna(0.0)
    x_series.name = "x_produccion_bruta"

    y = first_existing(xls, ["y_demanda_final", "f_demanda_final"])
    v = first_existing(xls, ["v_valor_agregado", "W_valor_agregado"])

    out = pd.DataFrame(index=sectors)
    out["x_produccion_bruta"] = x_series

    if balances is not None:
        b = balances.reindex(sectors)
        for src, dst in [
            ("ventas_intermedias_rowsum_Z", "ventas_intermedias_Z"),
            ("demanda_final_f", "y_demanda_final_total"),
            ("compras_intermedias_colsum_Z", "compras_intermedias_Z"),
            ("ajuste_intermedio_no_basico", "ajuste_intermedio_no_basico"),
            ("valor_agregado_W", "v_valor_agregado"),
        ]:
            if src in b.columns:
                out[dst] = pd.to_numeric(b[src], errors="coerce").fillna(0.0)

    if "y_demanda_final_total" not in out.columns and y is not None:
        y_num = y.apply(pd.to_numeric, errors="coerce").fillna(0.0).reindex(sectors).fillna(0.0)
        total_col = next((c for c in y_num.columns if str(c).lower() in {"demanda_final_total", "demanda_final", "y"}), y_num.columns[-1])
        out["y_demanda_final_total"] = y_num[total_col]

    if "v_valor_agregado" not in out.columns and v is not None:
        out["v_valor_agregado"] = pd.to_numeric(v.iloc[:, 0], errors="coerce").fillna(0.0).reindex(sectors).fillna(0.0)

    out.index.name = "sector"
    return clean_x_components(out)


def clean_x_components(out: pd.DataFrame) -> pd.DataFrame:
    """Oculta componentes no disponibles para no sugerir cierres incompletos."""
    out = out.drop(columns=[c for c in out.columns if str(c).startswith("check_")], errors="ignore")
    if "v_valor_agregado" in out.columns and float(out["v_valor_agregado"].abs().sum()) <= 1e-8:
        drop_cols = [
            "compras_intermedias_Z",
            "ajuste_intermedio_no_basico",
            "v_valor_agregado",
            "check_x_menos_Zcol_menos_v_menos_ajuste",
        ]
        out = out.drop(columns=[c for c in drop_cols if c in out.columns])
    return out


def build_y(xls: pd.ExcelFile, sectors: list[str]) -> pd.DataFrame:
    y = first_existing(xls, ["y_demanda_final", "f_demanda_final"])
    if y is None:
        return pd.DataFrame(index=sectors, data={"demanda_final_total": 0.0})
    out = y.apply(pd.to_numeric, errors="coerce").fillna(0.0).reindex(sectors).fillna(0.0)
    out.index.name = "sector"
    return out


def build_xhat(x: pd.DataFrame) -> pd.DataFrame:
    sectors = list(x.index)
    values = pd.to_numeric(x["x_produccion_bruta"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    out = pd.DataFrame(np.diag(values), index=sectors, columns=sectors)
    out.index.name = "sector_vendedor"
    return out


def collect_source_tables(xls: pd.ExcelFile) -> list[tuple[str, pd.DataFrame, bool]]:
    src = [(s, read_sheet(xls, s), True) for s in xls.sheet_names if s.startswith("src_")]
    src = [(name, df, index) for name, df, index in src if df is not None]
    if src:
        return src

    existing_source = read_sheet(xls, "COU_Tabla_Original", index_col=None)
    if existing_source is not None:
        return [("COU_Tabla_Original", existing_source, False)]

    fallback = []
    for name in ["fuente_resumen", "fuente_notas"]:
        df = read_sheet(xls, name, index_col=None)
        if df is not None:
            fallback.append((name, df, False))
    if not fallback:
        fallback.append(("sin_COU_publico", pd.DataFrame({
            "nota": ["No hay COU publico separado adjunto para esta matriz; ver Indice y documentacion de fuentes."]
        }), False))
    return fallback


def write_source_sheet(writer: pd.ExcelWriter, source_tables: list[tuple[str, pd.DataFrame, bool]]) -> None:
    sheet = "COU_Tabla_Original"
    startrow = 0
    for title, df, include_index in source_tables:
        if title == "COU_Tabla_Original":
            df.to_excel(writer, sheet_name=sheet, index=False, startrow=startrow)
            startrow += len(df) + 2
            continue
        marker = pd.DataFrame([[title, "Tabla fuente original o referencia"]], columns=["bloque", "descripcion"])
        marker.to_excel(writer, sheet_name=sheet, index=False, startrow=startrow)
        startrow += len(marker) + 2
        df.to_excel(writer, sheet_name=sheet, index=include_index, startrow=startrow)
        startrow += len(df) + 4


def write_workbook(path: Path) -> None:
    xls = pd.ExcelFile(path)
    try:
        meta = meta_map(xls)
        index_df = build_index(path, xls, meta)
        source_tables = collect_source_tables(xls)
        Z = as_numeric_df(first_existing(xls, ["Z_MIP", "Z_consumos_intermedios"]))
        A = as_numeric_df(read_sheet(xls, "A_coef_tecnicos"))
        L = as_numeric_df(read_sheet(xls, "L_leontief"))
        B = as_numeric_df(first_existing(xls, ["B_coef_distribucion", "B_ghosh_coef"]))
        if Z is None or A is None or L is None or B is None:
            raise ValueError(f"{path}: faltan Z/A/L/B")

        sectors = [str(i).strip() for i in Z.index]
        Z = Z.reindex(index=sectors, columns=sectors).fillna(0.0)
        A = A.reindex(index=sectors, columns=sectors).fillna(0.0)
        L = L.reindex(index=sectors, columns=sectors).fillna(0.0)
        B = B.reindex(index=sectors, columns=sectors).fillna(0.0)
        for df in [Z, A, L, B]:
            df.index.name = "sector_vendedor"

        x = build_x_components(xls, sectors)
        y = build_y(xls, sectors)
        Xhat = build_xhat(x)
    finally:
        xls.close()

    handle, tmp_name = tempfile.mkstemp(suffix=".xlsx")
    os.close(handle)
    tmp = Path(tmp_name)
    try:
        with pd.ExcelWriter(tmp, engine="openpyxl") as writer:
            index_df.to_excel(writer, sheet_name="Indice", index=False)
            write_source_sheet(writer, source_tables)
            Z.to_excel(writer, sheet_name="Z_consumos_intermedios")
            x.to_excel(writer, sheet_name="x_produccion_bruta")
            y.to_excel(writer, sheet_name="y_demanda_final")
            Xhat.to_excel(writer, sheet_name="X_hat")
            A.to_excel(writer, sheet_name="A_coef_tecnicos")
            L.to_excel(writer, sheet_name="L_leontief")
            B.to_excel(writer, sheet_name="B_coef_distribucion")
        style_workbook(tmp)
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def style_workbook(path: Path) -> None:
    wb = load_workbook(path)
    for ws in wb.worksheets:
        max_row = ws.max_row
        max_col = ws.max_column
        ws.freeze_panes = "B2" if max_col > 2 else "A2"
        ws.sheet_view.showGridLines = False
        for cell in ws[1]:
            cell.border = BORDER
            cell.fill = PatternFill("solid", fgColor=NAVY)
            cell.font = Font(size=9, color=WHITE, bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        if ws.title == "Indice":
            ws.freeze_panes = "A2"
            ws.column_dimensions["A"].width = 28
            ws.column_dimensions["B"].width = 110
            for row in ws.iter_rows(min_row=2, max_row=max_row, max_col=2):
                if str(row[0].value or "") == "HOJA":
                    for cell in row:
                        cell.border = BORDER
                        cell.fill = PatternFill("solid", fgColor=BLUE)
                        cell.font = Font(size=9, color=WHITE, bold=True)
        elif ws.title == "COU_Tabla_Original":
            ws.freeze_panes = "A1"
            ws.column_dimensions["A"].width = 34
            for col in range(2, min(max_col, 24) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 16
            for row in ws.iter_rows(min_row=1, max_row=max_row, max_col=min(max_col, 2)):
                if row[0].value and row[1].value == "Tabla fuente original o referencia":
                    for cell in row:
                        cell.border = BORDER
                        cell.fill = PatternFill("solid", fgColor=LIGHT_BLUE)
                        cell.font = Font(size=10, color=NAVY, bold=True)
        else:
            ws.column_dimensions["A"].width = 44
            for col in range(2, min(max_col, 40) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 14

        if max_row > 1 and max_col > 1:
            ws.auto_filter.ref = ws.dimensions

    wb.save(path)


def main() -> None:
    paths = sorted(MIP_ROOT.glob("*/*.xlsx"))
    if not paths:
        raise SystemExit(f"No se encontraron Excel en {MIP_ROOT}")
    for path in paths:
        if path.name.startswith("~$"):
            continue
        write_workbook(path)
        print(f"[OK] {path}")


if __name__ == "__main__":
    main()
