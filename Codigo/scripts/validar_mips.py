# -*- coding: utf-8 -*-
"""Validaciones matematicas de las MIP procesadas."""

from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_PROC = ROOT / "data" / "processed"
OUT_DIR = ROOT / "output" / "tablas"


def parse_country_year(path: Path) -> tuple[str, int] | None:
    match = re.match(r"mip_(.+)_(\d{4})(?:_[A-Za-z0-9]+)?\.xlsx$", path.name)
    if not match:
        return None
    return match.group(1), int(match.group(2))


def max_abs_rel(values: np.ndarray, scale: np.ndarray | float) -> float:
    denom = np.maximum(np.asarray(scale, dtype=float), 1.0)
    return float(np.nanmax(np.abs(values) / denom)) if values.size else 0.0


def has_sector_name(label: object) -> bool:
    text = str(label).strip()
    if "—" in text or "---" in text:
        return len(text.split("—", 1)[-1].split("---", 1)[-1].strip()) >= 3
    bare_code = re.fullmatch(r"(\d+|\d+/\d+|P\d+|A\.\d+|[A-Z]\.\d+)", text)
    if bare_code:
        return False
    return any(ch.isalpha() for ch in text) and len(text) >= 3


def validate_file(path: Path) -> dict:
    parsed = parse_country_year(path)
    if parsed is None:
        raise ValueError(f"Nombre no reconocido: {path.name}")
    pais, anio = parsed

    sheets = pd.read_excel(path, sheet_name=None, index_col=0)
    Z = sheets["Z_flujos"].apply(pd.to_numeric, errors="coerce").fillna(0)
    A = sheets["A_coeficientes"].apply(pd.to_numeric, errors="coerce").fillna(0)
    L = sheets["L_leontief"].apply(pd.to_numeric, errors="coerce").fillna(0)
    g = sheets["produccion"].iloc[:, 0].pipe(pd.to_numeric, errors="coerce").fillna(0)
    W = None
    if "valor_agregado" in sheets:
        W = sheets["valor_agregado"].iloc[:, 0].pipe(pd.to_numeric, errors="coerce").fillna(0)
    f_saved = None
    if "demanda_final" in sheets:
        f_saved = sheets["demanda_final"].iloc[:, 0].pipe(pd.to_numeric, errors="coerce").fillna(0)
    Mci = None
    if "ci_importado" in sheets:
        Mci = sheets["ci_importado"].iloc[:, 0].pipe(pd.to_numeric, errors="coerce").fillna(0)

    sectors = list(Z.index)
    sector_keys = [str(x) for x in sectors]
    n = len(sectors)
    square_ok = Z.shape == (n, n) and A.shape == (n, n) and L.shape == (n, n)
    labels_ok = (
        [str(x) for x in Z.index] == [str(x) for x in Z.columns]
        and [str(x) for x in A.index] == sector_keys
        and [str(x) for x in A.columns] == sector_keys
        and [str(x) for x in L.index] == sector_keys
        and [str(x) for x in L.columns] == sector_keys
        and [str(x) for x in g.index] == sector_keys
    )
    nombres_sector_ok = all(has_sector_name(x) for x in sectors)

    min_value = float(min(Z.min().min(), A.min().min(), L.min().min(), g.min()))
    nonnegative_core = min(float(Z.min().min()), float(A.min().min()), float(g.min())) >= -1e-8

    g_aligned = g.reindex(sectors).fillna(0)
    g_values = g_aligned.to_numpy(dtype=float)
    g_values_safe = np.where(np.abs(g_values) > 0, g_values, np.nan)
    A_from_Z_values = np.divide(
        Z.to_numpy(dtype=float),
        g_values_safe[np.newaxis, :],
        out=np.zeros_like(Z.to_numpy(dtype=float), dtype=float),
        where=~np.isnan(g_values_safe[np.newaxis, :]),
    )
    a_diff = A.to_numpy(dtype=float) - A_from_Z_values
    a_abs_max = float(np.nanmax(np.abs(a_diff))) if a_diff.size else 0.0

    I = np.eye(n)
    leontief_left = (I - A.to_numpy(dtype=float)) @ L.to_numpy(dtype=float) - I
    leontief_right = L.to_numpy(dtype=float) @ (I - A.to_numpy(dtype=float)) - I
    leontief_abs_max = float(
        max(np.nanmax(np.abs(leontief_left)), np.nanmax(np.abs(leontief_right)))
    )

    z_colsum = Z.sum(axis=0)
    if Mci is None:
        Mci = pd.Series(0.0, index=sectors, name="ci_importado")
    Mci = Mci.reindex(sectors).fillna(0)
    residual_va = pd.Series(
        g_aligned.to_numpy(dtype=float) - z_colsum.to_numpy(dtype=float) - Mci.to_numpy(dtype=float),
        index=sectors,
        name="valor_agregado_residual",
    )
    residual_va_neg_count = int((residual_va < -1e-8).sum())
    residual_va_min = float(residual_va.min()) if n else 0.0
    if W is not None:
        W = W.reindex(sectors).fillna(0)
        w_diff = W.to_numpy(dtype=float) - residual_va.to_numpy(dtype=float)
        w_rel_max = max_abs_rel(w_diff, np.maximum(g_aligned.to_numpy(dtype=float), 1.0))
        w_abs_max = float(np.nanmax(np.abs(w_diff))) if w_diff.size else 0.0
        va_neg_count = int((W < -1e-8).sum())
        va_min = float(W.min()) if n else 0.0
    else:
        w_rel_max = np.nan
        w_abs_max = np.nan
        va_neg_count = np.nan
        va_min = np.nan

    # Preferir la demanda final sectorial guardada; si no existe, usar residual.
    if f_saved is not None:
        f_ind = f_saved.reindex(sectors).fillna(0)
        f_ind.name = "demanda_final"
    else:
        f_ind = pd.Series(
            g_aligned.to_numpy(dtype=float) - Z.sum(axis=1).to_numpy(dtype=float),
            index=sectors,
            name="demanda_final_residual",
        )
    g_hat = L.to_numpy(dtype=float) @ f_ind.to_numpy(dtype=float)
    identity_diff = g_hat - g_aligned.to_numpy(dtype=float)
    identity_rel_max = max_abs_rel(identity_diff, np.maximum(g_aligned.to_numpy(dtype=float), 1.0))
    identity_abs_max = float(np.nanmax(np.abs(identity_diff))) if identity_diff.size else 0.0

    negative_final_demand_share = float((f_ind < -1e-8).sum() / n) if n else 0.0
    negative_final_demand_count = int((f_ind < -1e-8).sum()) if n else 0
    final_demand_min = float(f_ind.min()) if n else 0.0
    adjustment_negative_count = int((Mci < -1e-8).sum()) if n else 0
    adjustment_min = float(Mci.min()) if n else 0.0
    oferta_demanda_diff = g_aligned - (Z.sum(axis=1) + f_ind)
    oferta_demanda_abs_max = float(np.nanmax(np.abs(oferta_demanda_diff))) if n else 0.0
    oferta_demanda_rel_max = max_abs_rel(
        oferta_demanda_diff.to_numpy(dtype=float),
        np.maximum(g_aligned.to_numpy(dtype=float), 1.0),
    )

    structural_tolerance = 1e-3
    strict_ok = (
        square_ok
        and labels_ok
        and nombres_sector_ok
        and nonnegative_core
        and a_abs_max <= structural_tolerance
        and leontief_abs_max <= structural_tolerance
    )
    diagnostic_ok = (
        strict_ok
        and (np.isnan(w_rel_max) or w_rel_max <= 1e-6)
        and oferta_demanda_rel_max <= 1e-6
        and identity_rel_max <= 1e-6
        and negative_final_demand_share == 0
        and (np.isnan(va_neg_count) or va_neg_count == 0)
        and residual_va_neg_count == 0
    )

    return {
        "pais": pais,
        "anio": anio,
        "archivo": str(path.relative_to(ROOT)),
        "n_sectores": n,
        "cuadrada_ok": square_ok,
        "etiquetas_ok": labels_ok,
        "nombres_sector_ok": nombres_sector_ok,
        "no_negativa_core": nonnegative_core,
        "min_valor_core": min_value,
        "A_vs_Zg_abs_max": a_abs_max,
        "leontief_abs_max": leontief_abs_max,
        "W_vs_gmenosZ_abs_max": w_abs_max,
        "W_vs_gmenosZ_rel_max": w_rel_max,
        "CI_importado_total": float(Mci.sum()),
        "ajuste_intermedio_neg_count": adjustment_negative_count,
        "ajuste_intermedio_min": adjustment_min,
        "oferta_vs_demanda_abs_max": oferta_demanda_abs_max,
        "oferta_vs_demanda_rel_max": oferta_demanda_rel_max,
        "Lf_vs_g_abs_max": identity_abs_max,
        "Lf_vs_g_rel_max": identity_rel_max,
        "demanda_final_neg_count": negative_final_demand_count,
        "demanda_final_neg_share": negative_final_demand_share,
        "demanda_final_min": final_demand_min,
        "VA_neg_count": va_neg_count,
        "VA_min": va_min,
        "VA_residual_neg_count": residual_va_neg_count,
        "VA_residual_min": residual_va_min,
        "validacion_estructural": "OK" if strict_ok else "REVISAR",
        "validacion_diagnostica": "OK" if diagnostic_ok else "AVISO",
    }


def main():
    rows = []
    for path in sorted(DATA_PROC.glob("*/mip_*.xlsx")):
        rows.append(validate_file(path))

    df = pd.DataFrame(rows).sort_values(["pais", "anio"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_xlsx = OUT_DIR / "validacion_matematica_mip.xlsx"
    df.to_excel(out_xlsx, index=False)

    summary = df.groupby("validacion_estructural").size().to_dict()
    diag = df.groupby("validacion_diagnostica").size().to_dict()
    out_md = OUT_DIR / "validacion_matematica_mip.md"
    lines = [
        "# Validacion matematica de MIP",
        "",
        f"Archivos revisados: {len(df)}",
        f"Validacion estructural: {summary}",
        f"Validacion diagnostica: {diag}",
        "",
        "Criterios estructurales OK: matrices cuadradas, etiquetas alineadas, Z/A/g no negativas, A = Z/g y (I-A)L = I.",
        "Criterios diagnosticos: ademas revisa oferta = demanda (g = sum_row(Z nacional) + f), W = g - sum_col(Z nacional) - CI importado, Lf = g, demanda final no negativa y valor agregado no negativo.",
        "",
    ]
    if not df.empty:
        review = df[df["validacion_estructural"] != "OK"]
        if review.empty:
            lines.append("Todas las MIP pasan las validaciones estructurales.")
        else:
            lines.append("MIP con validacion estructural por revisar:")
            for _, row in review.iterrows():
                lines.append(f"- {row['pais']} {int(row['anio'])}: {row['archivo']}")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[OK] {out_xlsx}")
    print(f"[OK] {out_md}")
    print(df[["pais", "anio", "validacion_estructural", "validacion_diagnostica"]].to_string(index=False))


if __name__ == "__main__":
    main()
