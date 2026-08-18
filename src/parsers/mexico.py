"""
Parser del COU de México (INEGI, SCNM) — tabulados matriciales del CEPAL staging.

Archivos (un concepto por libro, hoja 'Tabulado'):
    MEX_COU_{anio}_PRECIOSCORRIENTES_20x20_OFERTA_{nivel}_SCIAN.xlsx
    MEX_COU_{anio}_PRECIOSCORRIENTES_20x20_DEMANDA_PCOMPRADOR_{nivel}_SCIAN_DOMESTICO&IMPORTADO.xlsx

Estructura (fila 4 = concepto, fila 5 = subencabezado, datos desde la fila 6;
0-indexado como los lee pandas con header=None):

  OFERTA   col 0  producto (rama SCIAN)
           col 1  OPC  — oferta total a precios de comprador
           col 2  MCT  — márgenes de comercio y transporte
           col 3  D.21-D.31 — impuestos sobre los productos, netos
           col 4  OPB  — oferta TOTAL a precios básicos (= producción + import.)
           col 5+ CAP  — clases de actividad productiva (las industrias)
           ...    Total — producción por actividad a precios básicos
           ...    I.CIF, Ajuste C.I.F./F.O.B., ICIFTFOB

  DEMANDA  col 0  producto · col 1 UTPC · col 2 DI Total · col 3+ industrias
           luego DF Total y los componentes de demanda final

Identidades verificadas sobre el dato de 2013 (nivel rama, 262×262):
    OPC − MCT − impuestos            == OPB            (exacto)
    Σ_ind producción                 == 'Total' CAP    (exacto)
    producción + I.CIF               == OPB            (exacto)
    Σ_ind utilización                == DI             (exacto)
    Σ componentes demanda final      == DF             (exacto)

Ojo con el ajuste C.I.F./F.O.B.: NO es un componente de la oferta por producto.
INEGI lo registra en su propia fila, fuera del bloque de ramas (junto con las
compras directas en el exterior por residentes). Por eso `Ajuste` va en cero por
producto: sumarlo rompería la identidad `producción + I.CIF == OPB`. El residuo
macro que eso deja lo absorbe el RAS del balanceo (Cap. 11), que lo reporta.

Nota sobre las importaciones: INEGI publica además la utilización con corte
DOMESTICO / IMPORTADO explícito. Este parser NO lo usa — alimenta el mismo motor
de valoración que los demás países (que separa por proporcionalidad, Cap. 8) para
que las cuatro MIP sean metodológicamente comparables. El corte explícito queda
disponible para validar ese supuesto.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from .. import crudo as _crudo

HR_CONCEPTO = 4      # fila con el concepto (OPC, MCT, DF...)
HR_DETALLE = 5       # fila con el detalle (códigos de industria, componentes)
R0 = 6               # primera fila de datos

_RAMA = re.compile(r"^(\d{2,6})\s*-\s*(.*)$")


def _n(x) -> str:
    """Normaliza a texto; los nulos devuelven '' (evita el 'nan' fantasma)."""
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(x)).strip()


def _split(texto: str) -> tuple[str, str]:
    """'1111 - Cultivo de semillas...' -> ('1111', 'Cultivo de semillas...')."""
    m = _RAMA.match(_n(texto))
    return (m.group(1), m.group(2).strip()) if m else (_n(texto), _n(texto))


def _es_rama(texto) -> bool:
    return bool(_RAMA.match(_n(texto)))


def _num(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(pd.to_numeric, errors="coerce").fillna(0.0)


def _hoja(ruta: Path) -> pd.DataFrame:
    return pd.read_excel(ruta, sheet_name="Tabulado", header=None)


def _col_por_concepto(d: pd.DataFrame, *claves: str) -> int:
    """Primera columna cuyo encabezado (fila 4 o 5) contiene alguna clave."""
    for c in range(1, d.shape[1]):
        h = (_n(d.iat[HR_CONCEPTO, c]) + " " + _n(d.iat[HR_DETALLE, c])).lower()
        if any(k.lower() in h for k in claves):
            return c
    raise KeyError(f"no encontré columna para {claves!r} en el tabulado")


def _filas_rama(d: pd.DataFrame) -> list[int]:
    return [r for r in range(R0, d.shape[0]) if _es_rama(d.iat[r, 0])]


def _cols_rama(d: pd.DataFrame) -> list[int]:
    return [c for c in range(1, d.shape[1]) if _es_rama(d.iat[HR_DETALLE, c])]


def parse(carpeta: str | Path, anio: int = 2013, nivel: str = "RAMA",
          verbose: bool = False) -> dict:
    carpeta = Path(carpeta)
    pre = f"MEX_COU_{anio}_PRECIOSCORRIENTES_20x20_"
    f_of = carpeta / f"{pre}OFERTA_{nivel}_SCIAN.xlsx"
    f_us = carpeta / f"{pre}DEMANDA_PCOMPRADOR_{nivel}_SCIAN_DOMESTICO&IMPORTADO.xlsx"
    for f in (f_of, f_us):
        if not f.exists():
            raise FileNotFoundError(f)

    of, us = _hoja(f_of), _hoja(f_us)

    # ── productos e industrias ────────────────────────────────────────────
    of_rows, us_rows = _filas_rama(of), _filas_rama(us)
    prod_keys = [_split(of.iat[r, 0])[0] for r in of_rows]
    prod_name = {k: _split(of.iat[r, 0])[1] for k, r in zip(prod_keys, of_rows)}
    prod_code = {k: k for k in prod_keys}

    of_icols = _cols_rama(of)
    ind_keys = [_split(of.iat[HR_DETALLE, c])[0] for c in of_icols]
    ind_name = {k: _split(of.iat[HR_DETALLE, c])[1] for k, c in zip(ind_keys, of_icols)}
    ind_code = {k: k for k in ind_keys}

    # ── V: producción por producto × industria (precios básicos) ──────────
    V_pi = pd.DataFrame(_num(of.iloc[of_rows, of_icols]).to_numpy(),
                        index=prod_keys, columns=ind_keys)

    # ── puente de valoración por producto ─────────────────────────────────
    c_opc = _col_por_concepto(of, "OPC")
    c_mct = _col_por_concepto(of, "MCT")
    c_imp = _col_por_concepto(of, "D.21-D.31", "Impuestos sobre los productos")
    c_cif = _col_por_concepto(of, "I.CIF - Importaciones")

    col = lambda c: pd.Series(_num(of.iloc[of_rows, [c]]).to_numpy().ravel(), index=prod_keys)
    OPC, Mg, IPnet, ICIF = col(c_opc), col(c_mct), col(c_imp), col(c_cif)
    OPB = V_pi.sum(axis=1)                      # producción doméstica a pb

    val = pd.DataFrame({
        "OPB": OPB,
        "IMPO": ICIF,
        # el ajuste C.I.F./F.O.B. vive fuera del bloque de ramas (ver docstring)
        "Ajuste": pd.Series(0.0, index=prod_keys),
        "IP": IPnet,                            # impuestos netos de subvenciones
        "DI": pd.Series(0.0, index=prod_keys),  # ya incluidos en IP
        "IVA": pd.Series(0.0, index=prod_keys),
        "Mg": Mg,
        "OPC": OPC,
    })

    # ── U y Y: utilización a precios de comprador ─────────────────────────
    us_icols = _cols_rama(us)
    us_ikeys = [_split(us.iat[HR_DETALLE, c])[0] for c in us_icols]
    us_pkeys = [_split(us.iat[r, 0])[0] for r in us_rows]
    U_pc = pd.DataFrame(_num(us.iloc[us_rows, us_icols]).to_numpy(),
                        index=us_pkeys, columns=us_ikeys)
    U_pc = U_pc.reindex(index=prod_keys, columns=ind_keys).fillna(0.0)

    # demanda final: columnas del bloque DF que no son el total
    c_df = _col_por_concepto(us, "DF - Demanda final")
    fd_cols, fd_names = [], []
    for c in range(c_df, us.shape[1]):
        det = _n(us.iat[HR_DETALLE, c])
        if not det or _es_rama(det):
            continue
        if re.sub(r"^[a-z]\s+", "", det).lower().startswith("total"):
            continue                            # 'b Total' = total de demanda final
        fd_cols.append(c); fd_names.append(det)
    Y_pc = pd.DataFrame(_num(us.iloc[us_rows, fd_cols]).to_numpy(),
                        index=us_pkeys, columns=fd_names)
    Y_pc = Y_pc.reindex(index=prod_keys).fillna(0.0)

    # ── VA por identidad: producción − consumo intermedio ─────────────────
    # (mismo criterio que Uruguay: evita depender de un tabulado extra de VA)
    VA = pd.DataFrame(
        [(V_pi.sum(axis=0) - U_pc.sum(axis=0)).reindex(ind_keys).fillna(0.0).to_numpy()],
        index=["valor_agregado_bruto"], columns=ind_keys)

    if verbose:
        print(f"  [MX {anio}] prod={len(prod_keys)} ind={len(ind_keys)} "
              f"fd={len(fd_names)} VBP={OPB.sum():,.0f}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "Y_pc": Y_pc, "val": val, "VA": VA,
        "crudo": [_crudo.hoja("Oferta", of, f_of, "Tabulado"),
                  _crudo.hoja("Demanda p. comprador", us, f_us, "Tabulado")],
        "prod_labels": {k: f"{k} - {prod_name[k]}" for k in prod_keys},
        "ind_labels": {k: f"{k} - {ind_name[k]}" for k in ind_keys},
        "ind_code": ind_code, "ind_name": ind_name,
        "prod_code": prod_code, "prod_name": prod_name,
        "pais": "México", "anio": anio,
        "unidad": "millones de pesos corrientes",
    }


# ── variante sin prorrateo ────────────────────────────────────────────────
def parse_sin_prorrateo(carpeta: str | Path, anio: int = 2013, nivel: str = "RAMA",
                        verbose: bool = False) -> dict:
    """
    Igual que `parse`, pero devuelve además la utilización DOMÉSTICA e IMPORTADA
    a precios básicos tal como las mide INEGI, para armar el SUT sin ningún
    supuesto de reparto (ver `valoracion.ensamblar_directo`).

    INEGI publica el mismo tabulado en tres versiones —DOMESTICO, IMPORTADO y
    DOMESTICO&IMPORTADO— y a precios básicos además de comprador. Con eso sobran
    los dos prorrateos: el de impuestos y márgenes y el de origen.
    """
    carpeta = Path(carpeta)
    base = parse(carpeta, anio, nivel=nivel, verbose=verbose)
    prod_keys = list(base["V_pi"].index)
    ind_keys = list(base["V_pi"].columns)
    pre = f"MEX_COU_{anio}_PRECIOSCORRIENTES_20x20_DEMANDA_"

    crudos_pb = []

    def leer(concepto: str, origen: str):
        f = carpeta / f"{pre}{concepto}_{nivel}_SCIAN_{origen}.xlsx"
        if not f.exists():
            raise FileNotFoundError(f)
        x = _hoja(f)
        crudos_pb.append(_crudo.hoja(f"Demanda pb {origen.replace('&', '+').lower()}",
                                     x, f, "Tabulado"))
        rows, icols = _filas_rama(x), _cols_rama(x)
        pk = [_split(x.iat[r, 0])[0] for r in rows]
        U = pd.DataFrame(_num(x.iloc[rows, icols]).to_numpy(), index=pk,
                         columns=[_split(x.iat[HR_DETALLE, c])[0] for c in icols])
        U = U.reindex(index=prod_keys, columns=ind_keys).fillna(0.0)
        c_df = _col_por_concepto(x, "DF - Demanda final")
        fdc, fdn = [], []
        for c in range(c_df, x.shape[1]):
            det = _n(x.iat[HR_DETALLE, c])
            if not det or _es_rama(det):
                continue
            if re.sub(r"^[a-z]\s+", "", det).lower().startswith("total"):
                continue
            fdc.append(c); fdn.append(det)
        Y = pd.DataFrame(_num(x.iloc[rows, fdc]).to_numpy(), index=pk, columns=fdn)
        return U, Y.reindex(index=prod_keys).fillna(0.0)

    U_dom, Y_dom = leer("PBASICOS", "DOMESTICO")
    U_imp, Y_imp = leer("PBASICOS", "IMPORTADO")
    U_pcb, _ = leer("PBASICOS", "DOMESTICO&IMPORTADO")

    # impuestos y márgenes por industria = comprador − básico (medido, no repartido)
    imptax_j = (base["U_pc"].sum(axis=0).reindex(ind_keys).fillna(0.0)
                - U_pcb.sum(axis=0).reindex(ind_keys).fillna(0.0))

    base.update({"U_dom": U_dom, "Y_dom": Y_dom, "U_imp": U_imp, "Y_imp": Y_imp,
                 "imptax_j": imptax_j,
                 # los tres tabulados a precios básicos que sólo usa este camino
                 "crudo": base["crudo"] + crudos_pb})
    if verbose:
        print(f"  [MX {anio} sin prorrateo] U_dom {U_dom.to_numpy().sum():,.0f} · "
              f"U_imp {U_imp.to_numpy().sum():,.0f} · impuestos {imptax_j.sum():,.0f}")
    return base
