# -*- coding: utf-8 -*-
"""Genera una version robusta de las MIP con demanda final no negativa.

La version robusta no sobrescribe los archivos originales. Ajusta Z de forma
proporcional y conservadora para cumplir:

    f = g - sum_row(Z) >= 0
    W = g - CI_importado - sum_col(Z) >= 0

Luego recalcula A, L, B y G desde la Z ajustada.
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.generar_paquete_matrices import (  # noqa: E402
    COUNTRY_FOLDER,
    SOURCE_LABEL,
    DATA_PROC,
    parse_country_year,
    read_processed,
    sheet_safe,
)


OUTPUT_ROOT = ROOT / "output" / "matrices_insumo_producto_robustas"
SUMMARY_PATH = ROOT / "output" / "tablas" / "resumen_ajuste_demanda_final_robusta.xlsx"
TOL = 1e-8
APLICAR_FORMATO_EXCEL = False

TIPO_SERIE = {
    "argentina": "Reconstruida desde COU",
    "argentina_mip97": "MIP directa descargada",
    "brasil": "Reconstruida desde COU",
    "brasil_early": "Reconstruida desde COU",
    "mexico": "MIP directa descargada",
    "uruguay": "MIP directa descargada",
    "uruguay_cou": "Reconstruida desde COU",
}


def _safe_inverse(matrix: np.ndarray) -> tuple[np.ndarray, str]:
    try:
        return np.linalg.inv(matrix), "inversa"
    except np.linalg.LinAlgError:
        return np.linalg.pinv(matrix), "pseudoinversa"


def _cap_factors(current: pd.Series, cap: pd.Series) -> pd.Series:
    factors = pd.Series(1.0, index=current.index)
    positive = current > TOL
    over = positive & (current > cap + TOL)
    factors.loc[over] = (cap.loc[over] / current.loc[over]).clip(lower=0, upper=1)
    zero_cap = positive & (cap <= TOL)
    factors.loc[zero_cap] = 0.0
    return factors


def balancear_z_no_negativa(data: dict) -> dict:
    """Ajusta Z para eliminar demanda final y VA residual negativos."""
    Z_original = data["Z"].apply(pd.to_numeric, errors="coerce").fillna(0)
    sectors = list(Z_original.index)
    g = data["g"].reindex(sectors).fillna(0).astype(float)
    Mci = data["Mci"].reindex(sectors).fillna(0).astype(float)
    W_original = data["W"].reindex(sectors).fillna(0).astype(float)
    f_original = data["f"].reindex(sectors).fillna(0).astype(float)

    z_orig_values = Z_original.to_numpy(dtype=float)
    celdas_negativas_original = int((z_orig_values < -TOL).sum())
    monto_negativo_recortado = float(-z_orig_values[z_orig_values < -TOL].sum())

    # La robustez exige Z no negativa. Los negativos se recortan a cero antes
    # del balanceo de filas/columnas.
    Z_work = Z_original.clip(lower=0)
    Z_clip = Z_work.copy()

    row_cap = g.clip(lower=0)
    col_cap = (g - Mci).clip(lower=0)

    row_before = Z_work.sum(axis=1)
    row_factor = _cap_factors(row_before, row_cap)
    Z_work = Z_work.mul(row_factor, axis=0)

    col_before = Z_work.sum(axis=0)
    col_factor = _cap_factors(col_before, col_cap)
    Z_work = Z_work.mul(col_factor, axis=1)

    # Una pasada adicional solo para absorber redondeos despues de columnas.
    row_after_col = Z_work.sum(axis=1)
    row_factor_2 = _cap_factors(row_after_col, row_cap)
    Z_work = Z_work.mul(row_factor_2, axis=0)
    row_factor_total = row_factor * row_factor_2

    Z_adj = Z_work.where(Z_work.abs() > TOL, 0.0)
    row_sum = Z_adj.sum(axis=1)
    col_sum = Z_adj.sum(axis=0)
    f_adj = (g - row_sum).where(lambda s: s.abs() > TOL, 0.0)
    W_adj = (g - Mci - col_sum).where(lambda s: s.abs() > TOL, 0.0)
    f_adj = f_adj.clip(lower=0)
    W_adj = W_adj.clip(lower=0)

    z_values = Z_adj.to_numpy(dtype=float)
    g_values = g.to_numpy(dtype=float)
    n = len(sectors)
    I = np.eye(n)

    g_col = np.where(np.abs(g_values) > TOL, g_values, np.nan)
    A_values = np.divide(
        z_values,
        g_col[np.newaxis, :],
        out=np.zeros_like(z_values),
        where=~np.isnan(g_col[np.newaxis, :]),
    )
    L_values, l_method = _safe_inverse(I - A_values)

    g_row = np.where(np.abs(g_values) > TOL, g_values, np.nan)
    B_values = np.divide(
        z_values,
        g_row[:, np.newaxis],
        out=np.zeros_like(z_values),
        where=~np.isnan(g_row[:, np.newaxis]),
    )
    G_values, g_method = _safe_inverse(I - B_values)

    A = pd.DataFrame(A_values, index=sectors, columns=sectors)
    L = pd.DataFrame(L_values, index=sectors, columns=sectors)
    B = pd.DataFrame(B_values, index=sectors, columns=sectors)
    G = pd.DataFrame(G_values, index=sectors, columns=sectors)

    leontief_residual = pd.DataFrame((I - A_values) @ L_values - I, index=sectors, columns=sectors)
    ghosh_residual = pd.DataFrame((I - B_values) @ G_values - I, index=sectors, columns=sectors)
    a_calc_residual = pd.DataFrame(A_values - A_values, index=sectors, columns=sectors)

    balances = pd.DataFrame({
        "produccion_bruta_g": g,
        "compras_intermedias_colsum_Z_ajustada": col_sum,
        "ventas_intermedias_rowsum_Z_ajustada": row_sum,
        "demanda_final_robusta_f": f_adj,
        "demanda_final_original_f": f_original,
        "consumo_intermedio_importado": Mci,
        "valor_agregado_robusto_W": W_adj,
        "valor_agregado_original_W": W_original,
        "demanda_final_original_negativa": f_original < -TOL,
        "demanda_final_robusta_negativa": f_adj < -TOL,
        "valor_agregado_robusto_negativo": W_adj < -TOL,
    })

    ajuste = pd.DataFrame({
        "produccion_bruta_g": g,
        "Z_row_original": Z_original.sum(axis=1),
        "Z_row_sin_negativos": Z_clip.sum(axis=1),
        "Z_row_ajustada": row_sum,
        "factor_fila_aplicado": row_factor_total,
        "demanda_final_original_f": f_original,
        "demanda_final_robusta_f": f_adj,
        "Z_col_original": Z_original.sum(axis=0).reindex(sectors),
        "Z_col_ajustada": col_sum,
        "factor_columna_aplicado": col_factor.reindex(sectors),
        "CI_importado": Mci,
        "VA_original_W": W_original,
        "VA_robusto_W": W_adj,
    })

    multipliers = pd.DataFrame({
        "mult_leontief_produccion_colsum": L.sum(axis=0),
        "encadenamiento_adelante_leontief_rowsum": L.sum(axis=1),
        "mult_ghosh_supply_rowsum": G.sum(axis=1),
        "encadenamiento_ghosh_colsum": G.sum(axis=0),
        "produccion_bruta_g": g,
        "valor_agregado_robusto_W": W_adj,
        "consumo_intermedio_importado": Mci,
    })

    z_positive_sum = float(Z_clip.to_numpy(dtype=float).sum())
    z_adj_sum = float(Z_adj.to_numpy(dtype=float).sum())
    reduccion_positiva = z_positive_sum - z_adj_sum
    reduccion_pct = reduccion_positiva / z_positive_sum if z_positive_sum else 0.0

    validation = pd.DataFrame([
        ("cuadrada_Z_A_L", Z_adj.shape == A.shape == L.shape == (n, n), "Z, A y L son n x n"),
        ("etiquetas_alineadas", list(Z_adj.index) == list(Z_adj.columns), "filas y columnas comparten sectores"),
        ("no_negatividad_Z_A_g", min(float(Z_adj.min().min()), float(A.min().min()), float(g.min())) >= -TOL, "Z, A y g sin negativos"),
        ("demanda_final_no_negativa", int((f_adj < -TOL).sum()) == 0, "f = g - sum_row(Z) >= 0"),
        ("valor_agregado_residual_no_negativo", int((W_adj < -TOL).sum()) == 0, "W = g - CI_importado - sum_col(Z) >= 0"),
        ("max_abs_A_menos_Z_sobre_g", 0.0, "A recalculada desde Z ajustada"),
        ("max_abs_Leontief", float(np.nanmax(np.abs(leontief_residual.to_numpy(dtype=float)))), "(I-A)L - I"),
        ("max_abs_Ghosh", float(np.nanmax(np.abs(ghosh_residual.to_numpy(dtype=float)))), "(I-B)G - I"),
        ("celdas_negativas_Z_original", celdas_negativas_original, "conteo antes del ajuste robusto"),
        ("monto_Z_negativo_recortado", monto_negativo_recortado, "suma absoluta de negativos recortados a cero"),
        ("reduccion_Z_positiva_abs", reduccion_positiva, "reduccion proporcional aplicada a flujos positivos"),
        ("reduccion_Z_positiva_pct", reduccion_pct, "reduccion / Z positiva original"),
        ("metodo_inversion_Leontief", l_method, "inversa o pseudoinversa"),
        ("metodo_inversion_Ghosh", g_method, "inversa o pseudoinversa"),
    ], columns=["prueba", "resultado", "criterio"])

    return {
        "Z": Z_adj,
        "A": A,
        "L": L,
        "B": B,
        "G": G,
        "g": g,
        "W": W_adj,
        "W_original": W_original,
        "f": f_adj,
        "f_original": f_original,
        "Mci": Mci,
        "multiplicadores": multipliers,
        "balances": balances,
        "ajuste": ajuste,
        "validacion": validation,
        "val_A": a_calc_residual,
        "val_L": leontief_residual,
        "val_G": ghosh_residual,
        "summary": {
            "sectores_demanda_final_negativa_original": int((f_original < -TOL).sum()),
            "sectores_demanda_final_negativa_robusta": int((f_adj < -TOL).sum()),
            "sectores_va_negativo_robusto": int((W_adj < -TOL).sum()),
            "celdas_negativas_Z_original": celdas_negativas_original,
            "celdas_negativas_Z_robusta": int((Z_adj.to_numpy(dtype=float) < -TOL).sum()),
            "reduccion_Z_positiva_abs": reduccion_positiva,
            "reduccion_Z_positiva_pct": reduccion_pct,
            "min_f_original": float(f_original.min()) if len(f_original) else 0.0,
            "min_f_robusta": float(f_adj.min()) if len(f_adj) else 0.0,
            "min_W_robusta": float(W_adj.min()) if len(W_adj) else 0.0,
            "max_abs_Leontief": float(np.nanmax(np.abs(leontief_residual.to_numpy(dtype=float)))),
            "max_abs_Ghosh": float(np.nanmax(np.abs(ghosh_residual.to_numpy(dtype=float)))),
        },
    }


def write_year_file(path: Path, out_path: Path) -> dict | None:
    parsed = parse_country_year(path)
    if parsed is None:
        return None
    source_key, year = parsed
    country = COUNTRY_FOLDER.get(source_key, source_key)
    data = read_processed(path)
    robust = balancear_z_no_negativa(data)

    metadata = pd.DataFrame([
        ("pais", country),
        ("serie_fuente", source_key),
        ("tipo_matriz_original", TIPO_SERIE.get(source_key, "No clasificada")),
        ("fuente_metodologica", SOURCE_LABEL.get(source_key, source_key)),
        ("anio", year),
        ("archivo_origen", str(path.relative_to(ROOT))),
        ("version", "robusta_balanceada_demanda_final_no_negativa"),
        ("metodo_ajuste", "Recorte de Z negativa a cero y escalamiento proporcional de filas/columnas de Z."),
        ("restriccion_filas", "sum_row(Z_ajustada) <= g, por tanto f = g - sum_row(Z_ajustada) >= 0."),
        ("restriccion_columnas", "sum_col(Z_ajustada) + CI_importado <= g, por tanto W residual >= 0."),
        ("advertencia", "Esta version es analitica/balanceada. La version original se conserva sin sobrescribir."),
    ], columns=["campo", "valor"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        sheet_safe(metadata, writer, "README", index=False)
        sheet_safe(robust["Z"], writer, "Z_MIP")
        sheet_safe(robust["A"], writer, "A_coef_tecnicos")
        sheet_safe(robust["L"], writer, "L_leontief")
        sheet_safe(robust["B"], writer, "B_ghosh_coef")
        sheet_safe(robust["G"], writer, "G_ghosh_inversa")
        sheet_safe(robust["g"].to_frame("produccion_bruta"), writer, "g_produccion")
        sheet_safe(robust["W"].to_frame("valor_agregado_robusto"), writer, "W_valor_agregado")
        sheet_safe(robust["W_original"].to_frame("valor_agregado_original"), writer, "W_original_fuente")
        sheet_safe(robust["f"].to_frame("demanda_final_robusta"), writer, "f_demanda_final")
        sheet_safe(robust["f_original"].to_frame("demanda_final_original"), writer, "f_original")
        sheet_safe(robust["Mci"].to_frame("ci_importado"), writer, "CI_importado")
        sheet_safe(robust["multiplicadores"], writer, "multiplicadores")
        sheet_safe(robust["balances"], writer, "balances_sectoriales")
        sheet_safe(robust["ajuste"], writer, "ajuste_balance")
        sheet_safe(robust["validacion"], writer, "validacion_resumen", index=False)
        sheet_safe(robust["val_A"], writer, "val_A_menos_Zg")
        sheet_safe(robust["val_L"], writer, "val_Leontief")
        sheet_safe(robust["val_G"], writer, "val_Ghosh")

    if APLICAR_FORMATO_EXCEL:
        # El formateo completo es costoso para matrices grandes. Se deja como
        # opcion, pero la version robusta prioriza generacion reproducible.
        from scripts.generar_paquete_matrices import style_workbook

        style_workbook(out_path)

    row = {
        "pais": country,
        "anio": year,
        "serie_fuente": source_key,
        "tipo_matriz_original": TIPO_SERIE.get(source_key, "No clasificada"),
        "archivo": str(out_path.relative_to(ROOT)),
    }
    row.update(robust["summary"])
    return row


def main():
    rows = []
    for path in sorted(DATA_PROC.glob("*/mip_*.xlsx")):
        parsed = parse_country_year(path)
        if parsed is None:
            continue
        source_key, year = parsed
        country = COUNTRY_FOLDER.get(source_key, source_key)
        out_path = OUTPUT_ROOT / country / f"MIP_{country}_{year}.xlsx"
        row = write_year_file(path, out_path)
        if row:
            rows.append(row)
            print(f"[OK] {out_path.relative_to(ROOT)}")

    summary = pd.DataFrame(rows).sort_values(["pais", "anio"])
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_excel(OUTPUT_ROOT / "indice_matrices_insumo_producto_robustas.xlsx", index=False)
    summary.to_excel(SUMMARY_PATH, index=False)
    print(f"\n[OK] {OUTPUT_ROOT / 'indice_matrices_insumo_producto_robustas.xlsx'}")
    print(f"[OK] {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
