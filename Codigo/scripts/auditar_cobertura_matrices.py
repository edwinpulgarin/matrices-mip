# -*- coding: utf-8 -*-
"""Compila la auditoria de cobertura sectorial de los Excel MIP finales."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MIP_ROOT = ROOT / "output" / "matrices_insumo_producto"
OUT_DIR = ROOT / "output" / "tablas"


def df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sin registros._"

    text_df = df.fillna("").astype(str)
    headers = list(text_df.columns)
    rows = text_df.values.tolist()
    widths = [
        max(len(str(header)), *(len(row[idx]) for row in rows))
        for idx, header in enumerate(headers)
    ]

    def fmt_row(values: list[str]) -> str:
        return "| " + " | ".join(
            str(value).ljust(widths[idx]) for idx, value in enumerate(values)
        ) + " |"

    separator = "| " + " | ".join("-" * width for width in widths) + " |"
    return "\n".join([fmt_row(headers), separator, *(fmt_row(row) for row in rows)])


def main() -> None:
    rows = []
    details = []
    for path in sorted(MIP_ROOT.glob("*/*.xlsx")):
        if path.name.startswith("~$"):
            continue
        xls = pd.ExcelFile(path)
        if "cobertura_sectores" not in xls.sheet_names:
            continue
        meta = pd.read_excel(path, sheet_name="fuente_resumen")
        meta_map = dict(zip(meta["campo"], meta["valor"]))
        cov = pd.read_excel(path, sheet_name="cobertura_sectores")
        cov.insert(0, "archivo", str(path.relative_to(ROOT)))
        cov.insert(0, "anio", int(meta_map.get("anio", 0)))
        cov.insert(0, "pais", meta_map.get("pais_publicado", path.parent.name))
        cov.insert(0, "serie_fuente", meta_map.get("serie_fuente", ""))
        details.append(cov)

        revisar = cov["decision_cobertura"].astype(str).str.contains("revisar", case=False, na=False)
        rows.append({
            "pais": meta_map.get("pais_publicado", path.parent.name),
            "serie_fuente": meta_map.get("serie_fuente", ""),
            "anio": int(meta_map.get("anio", 0)),
            "tipo_matriz": meta_map.get("tipo_matriz", ""),
            "archivo": str(path.relative_to(ROOT)),
            "sectores_mip": int(cov["en_MIP_final"].fillna(False).sum()),
            "sectores_fuente": int(cov["en_fuente_actividad"].fillna(False).sum()),
            "sectores_fuente_no_mip": int(((cov["en_fuente_actividad"] == True) & (cov["en_MIP_final"] != True)).sum()),
            "sectores_mip_no_fuente": int(((cov["en_MIP_final"] == True) & (cov["en_fuente_actividad"] != True)).sum()),
            "sectores_revisar": int(revisar.sum()),
            "sectores_diagonal_cero_con_flujos": int(cov["diagonal_cero_con_flujos"].fillna(False).sum()),
        })

    summary = pd.DataFrame(rows).sort_values(["pais", "anio", "serie_fuente"])
    detail = pd.concat(details, ignore_index=True) if details else pd.DataFrame()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_xlsx = OUT_DIR / "auditoria_cobertura_sectores_mip.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="resumen", index=False)
        detail.to_excel(writer, sheet_name="detalle", index=False)

    out_md = OUT_DIR / "auditoria_cobertura_sectores_mip.md"
    lines = [
        "# Auditoria de cobertura sectorial MIP",
        "",
        f"Matrices auditadas: {len(summary)}",
        "",
        "## Lectura",
        "",
        "- `sectores_fuente_no_mip`: actividades que aparecen en la fuente de actividad y no en la MIP final.",
        "- `sectores_mip_no_fuente`: sectores que aparecen en la MIP final y no en la fuente de actividad procesada.",
        "- `sectores_diagonal_cero_con_flujos`: sectores incluidos con `Z[i,i] = 0` pero con produccion, ventas o compras. No son errores por si mismos.",
        "",
        "## Resumen",
        "",
        df_to_markdown(summary),
        "",
    ]
    if not summary.empty and int(summary["sectores_revisar"].sum()) == 0:
        lines.append("No se encontraron diferencias de cobertura sectorial por revisar entre fuente de actividad y MIP final.")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"[OK] {out_xlsx}")
    print(f"[OK] {out_md}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
