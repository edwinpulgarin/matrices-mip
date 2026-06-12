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
FRAC_PROMEDIO = 0.20        # candidato si su peso < 20% del peso promedio por sector
CONCENTRACION_FUERTE = 25.0  # % del flujo intermedio del sector que va al socio top


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


def read_A(path: Path, sectors) -> np.ndarray | None:
    """Matriz de coeficientes tecnicos A (estructura de insumos por columna)."""
    xls = pd.ExcelFile(path)
    name = next((s for s in ["A_coef_tecnicos"] if s in xls.sheet_names), None)
    if name is None:
        return None
    a = pd.read_excel(path, sheet_name=name, index_col=0)
    a.index = [str(i).strip() for i in a.index]
    a.columns = [str(c).strip() for c in a.columns]
    a = a.reindex(index=sectors, columns=sectors).apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return a.to_numpy(dtype=float)


def socio_similitud(A: np.ndarray | None, sectors: list[str]) -> list[str]:
    """Para cada sector, el mas parecido por estructura de insumos (coseno de columnas de A)."""
    if A is None:
        return ["" for _ in sectors]
    cols = A  # columna j = receta de insumos del sector j
    norms = np.linalg.norm(cols, axis=0)
    out = []
    for j in range(cols.shape[1]):
        if norms[j] <= 1e-12:
            out.append("")
            continue
        sims = (cols.T @ cols[:, j]) / (norms * norms[j] + 1e-12)
        sims[j] = -1.0
        k = int(np.argmax(sims))
        out.append(sectors[k] if sims[k] > 0.05 else "")
    return out


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
    # Socio por FLUJO: mayor flujo combinado Z[i,j]+Z[j,i] (excluye la diagonal)
    combinado = znp + znp.T
    np.fill_diagonal(combinado, -1.0)
    socio_idx = combinado.argmax(axis=1)
    flujo_socio = combinado[np.arange(n), socio_idx]          # valor del mayor vinculo
    sugerencia_flujo = [sectors[j] for j in socio_idx]
    # Socio por SIMILITUD tecnica (estructura de insumos)
    A = read_A(path, sectors)
    sugerencia_sim = socio_similitud(A, sectors)

    flujo_intermedio_sector = ci_compras.values + ci_ventas.reindex(sectors).values
    # "sin flujos": el sector casi no participa de la red intermedia -> la
    # sugerencia por flujo no es confiable (caso servicios domesticos).
    nil = flujo_intermedio_sector < (1e-4 * total)

    # Concentracion: que fraccion del flujo intermedio del sector va al socio top.
    flujo_sector_safe = np.where(flujo_intermedio_sector > 0, flujo_intermedio_sector, np.nan)
    concentracion = 100 * flujo_socio / flujo_sector_safe

    df = pd.DataFrame({
        "pais": pais,
        "anio": anio,
        "sector": sectors,
        "ci_compras": ci_compras.values,
        "ci_ventas": ci_ventas.reindex(sectors).values,
        "x_produccion": x.values,
        "diag_autoconsumo": np.diag(znp),
        "sugerencia_por_flujo": sugerencia_flujo,
        "vinculo_flujo_pct": 100 * flujo_socio / total,
        "concentracion_socio_pct": np.nan_to_num(concentracion, nan=0.0),
        "sugerencia_por_similitud_tecnica": sugerencia_sim,
    })
    df["flujo_y_similitud_coinciden"] = (
        df["sugerencia_por_flujo"] == df["sugerencia_por_similitud_tecnica"]
    )
    df["part_compras_pct"] = 100 * df["ci_compras"] / total
    df["part_ventas_pct"] = 100 * df["ci_ventas"] / total
    # Cuando el sector casi no tiene flujos intermedios, no se sugiere por flujo.
    df.loc[nil, "sugerencia_por_flujo"] = "(sin flujos intermedios — decidir por clasificación)"
    df.loc[nil, "vinculo_flujo_pct"] = 0.0
    df.loc[nil, "concentracion_socio_pct"] = 0.0
    df.loc[nil, "flujo_y_similitud_coinciden"] = False
    umbral_pct = FRAC_PROMEDIO * (100.0 / n)   # 20% del peso promedio (1/n)
    df["umbral_pct"] = round(umbral_pct, 4)
    df["candidato_agregar"] = (
        (df["part_compras_pct"] < umbral_pct) & (df["part_ventas_pct"] < umbral_pct)
    )
    # Candidato FUERTE/defendible: es pequeno, tiene flujos, y su socio concentra
    # buena parte de su actividad intermedia (target de fusion claro).
    df["sin_flujos"] = nil
    df["candidato_fuerte"] = (
        df["candidato_agregar"] & (~df["sin_flujos"])
        & (df["concentracion_socio_pct"] >= CONCENTRACION_FUERTE)
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

    # Candidatos FUERTES: lista corta y defendible para la reunion.
    cols_fuertes = [
        "pais", "anio", "sector", "sugerencia_por_flujo",
        "concentracion_socio_pct", "vinculo_flujo_pct",
        "flujo_y_similitud_coinciden", "sugerencia_por_similitud_tecnica",
        "part_compras_pct", "part_ventas_pct",
    ]
    fuertes = (
        full[full["candidato_fuerte"]]
        .sort_values(["pais", "anio", "concentracion_socio_pct"], ascending=[True, True, False])
        [cols_fuertes]
    )
    resumen_fuertes = (
        full.groupby(["pais", "anio"])
        .agg(n_sectores=("sector", "count"),
             n_candidatos=("candidato_agregar", "sum"),
             n_fuertes=("candidato_fuerte", "sum"))
        .reset_index()
    )

    out_path = OUT
    try:
        target = open(out_path, "a")   # falla si esta abierto en Excel (lock)
        target.close()
    except PermissionError:
        out_path = OUT.with_name(OUT.stem + "_v2.xlsx")
        print(f"[AVISO] {OUT.name} esta abierto/bloqueado; se escribe en {out_path.name}.")

    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        resumen_fuertes.to_excel(w, sheet_name="resumen_por_matriz", index=False)
        fuertes.round(4).to_excel(w, sheet_name="candidatos_fuertes", index=False)
        top.round(4).to_excel(w, sheet_name="top_candidatos", index=False)
        candidatos.round(4).to_excel(w, sheet_name="todos_los_candidatos", index=False)
        full.round(4).to_excel(w, sheet_name="detalle_todos_sectores", index=False)

    print(f"[OK] {out_path}")
    print(f"Matrices analizadas: {resumen_fuertes.shape[0]}")
    print(f"Total sectores: {len(full)}  |  candidatos: {len(candidatos)}  |  FUERTES: {len(fuertes)}")
    print("\nResumen por matriz (n_candidatos = sectores con peso < 0.5% en compras y ventas):")
    print(resumen.to_string(index=False))


if __name__ == "__main__":
    main()
