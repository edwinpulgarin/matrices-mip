# -*- coding: utf-8 -*-
"""Crea un repositorio local navegable con las matrices MIP generadas."""

from pathlib import Path
import shutil

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "output" / "matrices_insumo_producto"
REPO_ROOT = ROOT / "output" / "repositorio_matrices_mip"
METODOLOGIA = ROOT / "docs" / "metodologia_mip.md"


def main():
    REPO_ROOT.mkdir(parents=True, exist_ok=True)

    rows = []
    for path in sorted(SOURCE_ROOT.glob("*/*.xlsx")):
        if path.name.startswith("~$"):
            continue
        country = path.parent.name
        year = "".join(ch for ch in path.stem if ch.isdigit())[-4:]
        dest_dir = REPO_ROOT / country / year
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        shutil.copy2(path, dest)
        rows.append({
            "pais": country,
            "anio": int(year) if year else None,
            "archivo": str(dest.relative_to(REPO_ROOT)),
            "fuente_excel": str(path.relative_to(ROOT)),
        })

    index = pd.DataFrame(rows).sort_values(["pais", "anio", "archivo"])
    index.to_csv(REPO_ROOT / "indice_matrices.csv", index=False, encoding="utf-8-sig")
    index.to_excel(REPO_ROOT / "indice_matrices.xlsx", index=False)

    if METODOLOGIA.exists():
        shutil.copy2(METODOLOGIA, REPO_ROOT / "METODOLOGIA.md")

    readme = [
        "# Repositorio de matrices insumo-producto MIP V2",
        "",
        "Repositorio local con matrices MIP por pais y anio.",
        "",
        "## Estructura",
        "",
        "```text",
        "repositorio_matrices_mip/",
        "  indice_matrices.xlsx",
        "  indice_matrices.csv",
        "  METODOLOGIA.md",
        "  Argentina/{anio}/MIP_Argentina_{anio}.xlsx",
        "  Brasil/{anio}/MIP_Brasil_{anio}.xlsx",
        "  Mexico/{anio}/MIP_Mexico_{anio}.xlsx",
        "  Uruguay/{anio}/MIP_Uruguay_{anio}.xlsx",
        "```",
        "",
        "## Criterios incluidos",
        "",
        "- Z nacional/domestica.",
        "- Filas y columnas con nombres de sectores economicos.",
        "- Consumo intermedio importado separado.",
        "- Demanda final residual domestica.",
        "- Validaciones macro de oferta, demanda y valor agregado.",
        "- Multiplicadores de empleo cuando existe vector de trabajo en la fuente.",
        "",
        "Ver `METODOLOGIA.md` para el detalle completo.",
        "",
        f"Archivos incluidos: {len(index)}",
    ]
    (REPO_ROOT / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print(f"[OK] {REPO_ROOT}")
    print(f"[OK] matrices copiadas: {len(index)}")


if __name__ == "__main__":
    main()
