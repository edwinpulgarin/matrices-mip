# -*- coding: utf-8 -*-
"""Identifica sectores candidatos a agregarse en otros por bajos consumos
intermedios. Para cada matriz publicada calcula, por sector:

- ci_compras  : suma de columna de Z (consumo intermedio que compra el sector).
- ci_ventas   : suma de fila de Z (insumos que vende el sector a otros).
- x           : produccion bruta.
- part_compras: ci_compras / total de Z (peso del sector como comprador).
- part_ventas : ci_ventas  / total de Z (peso del sector como vendedor).

Un sector es CANDIDATO a agregacion cuando su peso como comprador y como
vendedor estan ambos muy por debajo del peso promedio por sector (umbral
RELATIVO: < 20% de 1/n, donde n es el numero de sectores de la matriz). Ademas,
para cada candidato se sugiere el sector con el que conviene fusionarlo: aquel
con el que intercambia el mayor flujo intermedio combinado (Z[i,j] + Z[j,i]).
Genera un Excel con resumen, sugerencias y detalle por matriz.
"""

from __future__ import annotations
from pathlib import Path
import glob
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MIP = REPO / "MIP"
OUT = REPO / "sectores_agregables_revision.xlsx"
FRAC_PROMEDIO = 0.20  # candidato si su peso < 20% del peso promedio por sector


def read_Z(path: Path) -> pd.DataFrame | None:
    xls = pd.ExcelFile(path)
    name = next((s for s in ["Z_consumos_intermedios", "Z_MIP"] if s in xls.sheet_names), None)
    if name is None:
        return None
    z = pd.read_excel(path, sheet_name=name, index_col=0)
    z = z.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return z


def read_x(path: Path, sectors) -> pd.Series:
    xls = pd.ExcelFile(path)
    if "x_produccion_bruta" in xls.sheet_names:
        x = pd.read_excel(path, sheet_name="x_produccion_bruta", index_col=0)
        col = "x_produccion_bruta" if "x_produccion_bruta" in x.columns else x.columns[0]
        return pd.to_numeric(x[col], errors="coerce").fillna(0.0).reindex(sectors).fillna(0.0)
    return pd.Series(0.0, index=sectors)


def analizar(path: Path) -> pd.DataFrame:
    z = read_Z(path)
    if z is None:
        return pd.DataFrame()
    sectors = [str(i).strip() for i in z.index]
    z.index = sectors
    z.columns = [str(c).strip() for c in z.columns]
    total = float(z.to_numpy().sum()) or 1.0
    ci_compras = z.sum(axis=0)          # columna: lo que compra cada sector
    ci_ventas = z.sum(axis=1)           # fila: lo que vende cada sector
    x = read_x(path, sectors)
    name = path.stem.replace("MIP_", "")
    pais, anio = name.rsplit("_", 1)
    n = len(sectors)
    zmat = z.reindex(index=sectors, columns=sectors).fillna(0.0)
    znp = zmat.to_numpy()
    # Socio para fusionar: mayor flujo combinado Z[i,j]+Z[j,i] (excluye la diagonal)
    combinado = znp + znp.T
    np.fill_diagonal(combinado, -1.0)
    socio_idx = combinado.argmax(axis=1)
    sugerencia = [sectors[j] for j in socio_idx]

    df = pd.DataFrame({
        "pais": pais,
        "anio": anio,
        "sector": sectors,
        "ci_compras": ci_compras.values,
        "ci_ventas": ci_ventas.reindex(sectors).values,
        "x_produccion": x.values,
        "diag_autoconsumo": np.diag(znp),
        "sugerencia_agregar_con": sugerencia,
    })
    df["part_compras_pct"] = 100 * df["ci_compras"] / total
    df["part_ventas_pct"] = 100 * df["ci_ventas"] / total
    umbral_pct = FRAC_PROMEDIO * (100.0 / n)   # 20% del peso promedio (1/n)
    df["umbral_pct"] = round(umbral_pct, 4)
    df["candidato_agregar"] = (
        (df["part_compras_pct"] < umbral_pct) & (df["part_ventas_pct"] < umbral_pct)
    )
    return df.sort_values("part_compras_pct")


def main() -> None:
    paths = sorted(MIP.glob("*/MIP_*.xlsx"))
    todo = []
    for p in paths:
        if p.name.startswith("~$"):
            continue
        d = analizar(p)
        if not d.empty:
            todo.append(d)
    full = pd.concat(todo, ignore_index=True)

    candidatos = full[full["candidato_agregar"]].copy()
    resumen = (
        full.groupby(["pais", "anio"])
        .agg(n_sectores=("sector", "count"),
             n_candidatos=("candidato_agregar", "sum"))
        .reset_index()
    )
    resumen["pct_candidatos"] = (100 * resumen["n_candidatos"] / resumen["n_sectores"]).round(1)

    # Top 10 candidatos mas pequenos por matriz (para revision con el equipo)
    top = (
        candidatos.sort_values(["pais", "anio", "part_compras_pct"])
        .groupby(["pais", "anio"]).head(10)
    )

    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        resumen.to_excel(w, sheet_name="resumen_por_matriz", index=False)
        top.round(4).to_excel(w, sheet_name="top_candidatos", index=False)
        candidatos.round(4).to_excel(w, sheet_name="todos_los_candidatos", index=False)
        full.round(4).to_excel(w, sheet_name="detalle_todos_sectores", index=False)

    print(f"[OK] {OUT}")
    print(f"Matrices analizadas: {resumen.shape[0]}")
    print(f"Total sectores: {len(full)}  |  candidatos a agregar: {len(candidatos)}")
    print("\nResumen por matriz (n_candidatos = sectores con peso < 0.5% en compras y ventas):")
    print(resumen.to_string(index=False))


if __name__ == "__main__":
    main()
