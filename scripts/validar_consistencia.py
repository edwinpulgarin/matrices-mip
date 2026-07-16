"""
Validación de consistencia FINAL sobre los LIBROS ya generados (output/*.xlsx).

No re-ejecuta la tubería: re-abre cada Excel entregado y re-verifica de forma
independiente las identidades de la MIP a partir de los números tal como
quedaron escritos en el archivo. Así se audita el artefacto, no el código.

Chequeos por libro:
  1. Balance de filas      gᵢ = Σⱼ zᵢⱼ + fᵢ
  2. Balance de columnas   gⱼ = Σᵢ zᵢⱼ + zmⱼ + Wⱼ
  3. Coeficientes A        A ≈ Z·diag(g)⁻¹  y  aᵢⱼ≥0, aᵢⱼ≤1, Σᵢaᵢⱼ<1
  4. Leontief              L ≈ (I−A)⁻¹      y  L·f ≈ g
  5. Nombres               toda fila con Denominación ≠ Código y no vacía
  6. Dimensiones           Z, A, L y vectores con el mismo n

Uso:  py -3 scripts/validar_consistencia.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

OUT = ROOT / "matrices"
# Los libros guardan las celdas redondeadas a 6 decimales, así que las
# identidades contables (exactas a ~1e-14 en la tubería) sólo pueden re-verse
# aquí hasta ~1e-6. 1e-5 pasa el redondeo de Excel y aún detecta errores reales.
TOL = 1e-5   # tolerancia relativa a max(g) para identidades contables


def _leer_matriz(f, hoja):
    """Lee una hoja tipo _matriz: fila 5 = encabezado, col A código, col B nombre,
    resto = valores n×n. Corta al primer código vacío o nota 'Fuente'."""
    df = pd.read_excel(f, sheet_name=hoja, header=None)
    cod, filas = [], []
    for r in range(5, df.shape[0]):
        c0 = str(df.iat[r, 0]).strip()
        if c0 in ("", "nan") or c0.lower().startswith("fuente"):
            break
        cod.append(c0)
        filas.append(r)
    n = len(cod)
    vals = df.iloc[filas, 2:2 + n].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    nombres = [str(df.iat[r, 1]).strip() for r in filas]
    return cod, nombres, vals


def _leer_vectores(f):
    df = pd.read_excel(f, sheet_name="3. Vectores", header=None)
    cod, rows = [], []
    for r in range(5, df.shape[0]):
        c0 = str(df.iat[r, 0]).strip()
        if c0 in ("", "nan") or c0.lower().startswith("fuente"):
            break
        cod.append(c0); rows.append(r)
    def col(j):
        return df.iloc[rows, j].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()
    # cols: 2=g, 3=f, 4=W, 5=zm, 6=vab, 7=imptax
    return cod, col(2), col(3), col(4), col(5)  # g, f, W, zm


def _rel(dif, escala):
    return float(np.max(np.abs(dif))) / max(escala, 1.0)


def validar(f: Path) -> dict:
    hojas = pd.ExcelFile(f).sheet_names
    if "2. Z" not in hojas:
        return {"skip": True}
    cod_z, nom_z, Z = _leer_matriz(f, "2. Z")
    cod_v, g, fdem, W, zm = _leer_vectores(f)
    cod_a, _, A = _leer_matriz(f, "8. A")
    cod_l, _, L = _leer_matriz(f, "10. Leontief")
    n = len(cod_z)
    esc = float(np.max(np.abs(g))) if g.size else 1.0

    r = {"skip": False, "n": n, "checks": {}}

    # dimensiones
    dims_ok = (len(cod_v) == n == A.shape[0] == A.shape[1] == L.shape[0] == L.shape[1]
               and cod_z == cod_v == cod_a == cod_l)
    r["checks"]["dimensiones"] = (dims_ok, "" if dims_ok else
                                  f"n_z={n} n_v={len(cod_v)} A={A.shape} L={L.shape} códigos alineados={cod_z==cod_v==cod_a==cod_l}")

    # 1. balance de filas: g = rowsum(Z) + f
    dif_fila = g - (Z.sum(axis=1) + fdem)
    rf = _rel(dif_fila, esc)
    r["checks"]["balance_filas"] = (rf < TOL, f"máx rel = {rf:.1e}")

    # 2. balance de columnas: g = colsum(Z) + zm + W
    dif_col = g - (Z.sum(axis=0) + zm + W)
    rc = _rel(dif_col, esc)
    r["checks"]["balance_columnas"] = (rc < TOL, f"máx rel = {rc:.1e}")

    # 3. A ≈ Z·diag(g)⁻¹  y condiciones
    gsafe = np.where(g == 0, np.nan, g)
    A_calc = np.nan_to_num(Z / gsafe)  # columna j dividida por g_j
    dif_A = _rel(A - A_calc, 1.0)
    amin, amax, colsum = float(A.min()), float(A.max()), float(A.sum(axis=0).max())
    a_ok = (dif_A < 1e-4 and amin >= -1e-9 and amax <= 1 + 1e-6 and colsum < 1 - 1e-9)
    r["checks"]["coeficientes_A"] = (a_ok, f"|A−Z/g|={dif_A:.1e} min={amin:.4f} max={amax:.4f} máxΣcol={colsum:.4f}")

    # 4. L ≈ (I−A)⁻¹  y  L·f ≈ g
    try:
        L_calc = np.linalg.inv(np.eye(n) - A)
        dif_L = _rel(L - L_calc, 1.0)
    except np.linalg.LinAlgError:
        dif_L = np.inf
    lf = L @ fdem
    dif_lf = _rel(lf - g, esc)
    l_ok = (dif_L < 1e-3 and dif_lf < TOL)
    r["checks"]["leontief"] = (l_ok, f"|L−(I−A)⁻¹|={dif_L:.1e}  |L·f−g| rel={dif_lf:.1e}")

    # 5. nombres presentes (Denominación ≠ Código y no vacía)
    sin_nombre = [c for c, nm in zip(cod_z, nom_z)
                  if nm in ("", "nan") or nm == c]
    r["checks"]["nombres"] = (len(sin_nombre) == 0,
                              "todas con nombre" if not sin_nombre
                              else f"{len(sin_nombre)} sin nombre: {sin_nombre[:8]}")
    return r


def main():
    libros = sorted(OUT.glob("*/*_LIBRO*.xlsx"))
    res = {}
    for f in libros:
        try:
            res[f.name] = validar(f)
        except Exception as e:
            res[f.name] = {"error": f"{type(e).__name__}: {e}"}

    orden = ["dimensiones", "balance_filas", "balance_columnas",
             "coeficientes_A", "leontief", "nombres"]
    etq = {"dimensiones": "Dim", "balance_filas": "Filas", "balance_columnas": "Cols",
           "coeficientes_A": "A", "leontief": "Leontief", "nombres": "Nombres"}

    filas = ["# Validación de consistencia — LIBROS generados (última versión)\n",
             "Auditoría independiente: se re-abre cada Excel y se re-verifican las "
             "identidades de la MIP con los números tal como quedaron escritos. "
             "✅ = cumple, ❌ = revisar.\n",
             "| Libro | n | " + " | ".join(etq[k] for k in orden) + " |",
             "|:------|--:|" + "|".join([":--:"] * len(orden)) + "|"]
    detalles = []
    n_ok = n_fail = 0
    for name, r in res.items():
        corto = name.replace("MIP_", "").replace("_LIBRO", "").replace("_107x107", "").replace(".xlsx", "")
        if r.get("error"):
            filas.append(f"| {corto} | — | " + " | ".join(["⚠️"] * len(orden)) + " |")
            detalles.append(f"- **{corto}** — ERROR: {r['error']}")
            n_fail += 1
            continue
        if r.get("skip"):
            continue
        cel = []
        libro_ok = True
        for k in orden:
            ok, msg = r["checks"][k]
            cel.append("✅" if ok else "❌")
            if not ok:
                libro_ok = False
                detalles.append(f"- **{corto} · {etq[k]}**: {msg}")
        filas.append(f"| {corto} | {r['n']} | " + " | ".join(cel) + " |")
        n_ok += libro_ok
        n_fail += (not libro_ok)
        print(f"[{'OK ' if libro_ok else 'REV'}] {corto:24s} n={r['n']:>4} "
              + " ".join(f"{etq[k]}:{'✓' if r['checks'][k][0] else '✗'}" for k in orden))

    filas.append(f"\n**Resumen:** {n_ok} libros consistentes, {n_fail} a revisar, "
                 f"de {n_ok + n_fail} auditados.\n")
    if detalles:
        filas.append("## Detalle de hallazgos\n")
        filas.extend(detalles)
    else:
        filas.append("Todos los libros pasan las seis verificaciones. ✅")

    rep = ROOT / "reports" / "validacion_consistencia.md"
    rep.write_text("\n".join(filas), encoding="utf-8")
    print(f"\n[OK] Reporte en {rep.relative_to(ROOT)}  ({n_ok} OK / {n_fail} revisar)")


if __name__ == "__main__":
    main()
