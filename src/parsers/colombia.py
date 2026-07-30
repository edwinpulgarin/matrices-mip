"""
Parser del COU de Colombia (DANE, base 2015) — versión SIN PRORRATEO.

Colombia es el único caso donde el dato limpio viene repartido en dos archivos,
y hay que cruzarlos:

  data/raw/colombia/DANE_COU_2014_2024_corrientes.xlsx
      Cuadro oferta-utilización, 2014-2024p, a dos y a seis dígitos CPC.
      De acá sale la matriz de PRODUCCIÓN (V) y el consumo intermedio a precios
      de comprador (para medir la cuña de impuestos y márgenes por industria).

  data/raw/colombia/DANE_MUPNI_2020p.xlsx
      Matriz de utilización desagregada en productos nacionales e importados
      (MUPNI), 2014-2020, ya a precios básicos y con el origen MEDIDO.
      De acá salen U_dom, U_imp y la demanda final doméstica.

Mapeo de hojas (ambos archivos usan «Cuadro N», numerados por año):

    COU, dos dígitos   año 2014+k  ->  oferta Cuadro 1+2k · utilización Cuadro 2+2k
    MUPNI              año 2014+k  ->  importados Cuadro 1+2k · nacionales Cuadro 2+2k

Alineación
----------
Los productos son divisiones CPC Vers. 2 A.C. y los códigos coinciden literalmente
entre los dos archivos ('01', '02', ..., '12 + 13', ...), así que se cruzan por
código. Las industrias son las mismas 61 agrupaciones CIIU en el mismo orden, pero
**cada archivo las rotula distinto**: el COU usa códigos CIIU ('A0101-02',
'A0102', 'O', 'R + S') y la MUPNI usa códigos de producto ('003', '009 - 012').
Por eso se cruzan por POSICIÓN, con una verificación dura de que ambos traigan 61
y de que la última coincida por nombre.

Nivel de agregación
-------------------
Se trabaja al nivel de la MUPNI (~68 divisiones CPC × 61 industrias), que es el
más fino donde existe el corte doméstico/importado medido. El COU a seis dígitos
llega a 394 productos, pero ahí el origen habría que prorratearlo.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

HR_CONCEPTO = 9      # fila con el concepto ('Consumo intermedio según divisiones CIIU')
HR_COD_IND = 10      # fila con el código de industria
HR_NOM_IND = 11      # fila con el nombre de industria (sólo en la MUPNI)
R0 = 13              # primera fila de datos

_COD_PROD = re.compile(r"^\d+(\s*\+\s*\d+)*$")   # '01', '12 + 13'
N_IND = 61


def _n(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(x)).strip()


def _clave(s: str) -> str:
    """Normaliza un nombre para comparar (minúsculas, sin acentos ni puntuación)."""
    s = unicodedata.normalize("NFKD", _n(s))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9 ]+", " ", re.sub(r"\s+", " ", s)).strip()


def _num(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(pd.to_numeric, errors="coerce").fillna(0.0)


def _filas_producto(d: pd.DataFrame) -> list[int]:
    """Filas de datos: las que tienen un código de división CPC en la col. 0.

    Filtra explícitamente el pie del cuadro ('Fuente: DANE...', 'Actualizado el
    ...'), que si no se cuela como un producto fantasma.
    """
    return [r for r in range(R0, d.shape[0]) if _COD_PROD.match(_n(d.iat[r, 0]))]


def _col_concepto(d: pd.DataFrame, *claves: str) -> int:
    for c in range(1, d.shape[1]):
        h = _clave(" ".join(_n(d.iat[r, c]) for r in range(HR_CONCEPTO, HR_NOM_IND + 1)))
        if any(_clave(k) in h for k in claves):
            return c
    raise KeyError(f"no encontré columna para {claves!r}")


def _cols_industria(d: pd.DataFrame, c_ini: int) -> list[int]:
    """61 columnas consecutivas de industria a partir de la primera."""
    cols = []
    for c in range(c_ini, d.shape[1]):
        cod, nom = _n(d.iat[HR_COD_IND, c]), _n(d.iat[HR_NOM_IND, c])
        if not cod and not nom:
            break
        if _clave(cod).startswith("total") or _clave(nom).startswith("total"):
            break
        cols.append(c)
        if len(cols) == N_IND:
            break
    return cols


def parse(carpeta: str | Path, anio: int = 2020, verbose: bool = False) -> dict:
    carpeta = Path(carpeta)
    f_cou = carpeta / "DANE_COU_2014_2024_corrientes.xlsx"
    f_mup = carpeta / "DANE_MUPNI_2020p.xlsx"
    for f in (f_cou, f_mup):
        if not f.exists():
            raise FileNotFoundError(f)
    k = anio - 2014
    if not 0 <= k <= 6:
        raise ValueError(f"la MUPNI cubre 2014-2020; pediste {anio}")

    hoja = lambda f, n: pd.read_excel(f, f"Cuadro {n}", header=None)
    of = hoja(f_cou, 1 + 2 * k)          # oferta, dos dígitos
    us = hoja(f_cou, 2 + 2 * k)          # utilización, dos dígitos
    imp = hoja(f_mup, 1 + 2 * k)         # MUPNI importados
    nac = hoja(f_mup, 2 + 2 * k)         # MUPNI nacionales

    # ── productos: se cruzan por código CPC ───────────────────────────────
    rn = _filas_producto(nac)
    prod_keys = [_n(nac.iat[r, 0]) for r in rn]
    prod_name = {k_: _n(nac.iat[r, 1]) for k_, r in zip(prod_keys, rn)}
    prod_code = {k_: k_ for k_ in prod_keys}

    # ── industrias: por POSICIÓN, con verificación ────────────────────────
    c_nac = _col_concepto(nac, "Consumo intermedio segun divisiones CIIU")
    ic_nac = _cols_industria(nac, c_nac)
    c_of = _col_concepto(of, "Produccion segun divisiones CIIU")
    ic_of = _cols_industria(of, c_of)
    c_us = _col_concepto(us, "Consumo intermedio segun divisiones CIIU")
    ic_us = _cols_industria(us, c_us)
    for nom, cc in (("MUPNI", ic_nac), ("COU oferta", ic_of), ("COU utilización", ic_us)):
        if len(cc) != N_IND:
            raise ValueError(f"{nom}: esperaba {N_IND} industrias, encontré {len(cc)}")
    # La MUPNI rotula las industrias distinto que el COU (códigos de producto vs
    # códigos CIIU), así que el cruce es POSICIONAL. Para detectar un corrimiento
    # entre publicaciones se mide cuántas de las 61 posiciones comparten palabras
    # significativas del nombre: la hoja de utilización del COU sí trae nombre
    # completo (la de oferta a veces sólo el código).
    def _palabras(s):
        return {w for w in _clave(s).split() if len(w) > 4}

    coinciden = 0
    for c_m, c_u in zip(ic_nac, ic_us):
        pm = _palabras(_n(nac.iat[HR_NOM_IND, c_m]))
        pu = _palabras(" ".join(_n(us.iat[r, c_u]) for r in (HR_COD_IND, HR_NOM_IND)))
        if pm and pu and pm & pu:
            coinciden += 1
    if coinciden < N_IND * 0.6:
        raise ValueError(f"industrias posiblemente desalineadas entre COU y MUPNI: "
                         f"sólo {coinciden}/{N_IND} posiciones coinciden por nombre")
    if verbose:
        print(f"  [CO {anio}] alineación de industrias: {coinciden}/{N_IND} por nombre")

    ind_keys, ind_code, ind_name = [], {}, {}
    for j, (c_m, c_o) in enumerate(zip(ic_nac, ic_of)):
        cod = _n(of.iat[HR_COD_IND, c_o]).split()[0] if _n(of.iat[HR_COD_IND, c_o]) else f"I{j:02d}"
        nom = _n(nac.iat[HR_NOM_IND, c_m]) or cod
        while cod in ind_code:                      # códigos CIIU repetidos
            cod += "'"
        ind_keys.append(cod); ind_code[cod] = cod; ind_name[cod] = nom

    def bloque(d, rows, cols):
        return pd.DataFrame(_num(d.iloc[rows, cols]).to_numpy(),
                            index=[_n(d.iat[r, 0]) for r in rows], columns=ind_keys)

    ri = _filas_producto(imp)
    ro = _filas_producto(of)
    ru = _filas_producto(us)
    U_dom = bloque(nac, rn, ic_nac).reindex(index=prod_keys).fillna(0.0)
    U_imp = bloque(imp, ri, ic_nac).reindex(index=prod_keys).fillna(0.0)
    V_pi = bloque(of, ro, ic_of).reindex(index=prod_keys).fillna(0.0)
    U_pc = bloque(us, ru, ic_us).reindex(index=prod_keys).fillna(0.0)

    # ── demanda final doméstica (columnas de la MUPNI tras el CI) ─────────
    # El encabezado va en dos niveles: el grupo en HR_CONCEPTO y el detalle en
    # HR_COD_IND, y el grupo sólo aparece en su primera columna. Sin arrastrarlo,
    # 'Exportaciones / Bienes' + 'Servicios' quedarían como 'Bienes' y
    # 'Servicios', y 'Servicios' a secas es inclasificable como demanda final.
    c_tot = ic_nac[-1] + 1                       # 'Total consumo intermedio'
    fdc, fdn = [], []
    grupo = ""
    for c in range(c_tot, nac.shape[1]):
        top, det = _n(nac.iat[HR_CONCEPTO, c]), _n(nac.iat[HR_COD_IND, c])
        if top:
            grupo = top
        etiqueta = det or grupo
        if not etiqueta or _clave(etiqueta).startswith("total"):
            continue
        nombre = etiqueta if _clave(etiqueta) == _clave(grupo) else f"{grupo} {etiqueta}".strip()
        fdc.append(c); fdn.append(nombre)
    Y_dom = pd.DataFrame(_num(nac.iloc[rn, fdc]).to_numpy(), index=prod_keys, columns=fdn)

    # ── impuestos y márgenes por industria: MEDIDOS, no repartidos ────────
    #   COU a precios de comprador − MUPNI a precios básicos (dom + imp)
    imptax_j = (U_pc.sum(axis=0) - U_dom.sum(axis=0) - U_imp.sum(axis=0)).reindex(ind_keys).fillna(0.0)

    if verbose:
        print(f"  [CO {anio}] prod={len(prod_keys)} ind={len(ind_keys)} fd={len(fdn)} "
              f"U_dom={U_dom.to_numpy().sum():,.0f} U_imp={U_imp.to_numpy().sum():,.0f}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "U_dom": U_dom, "U_imp": U_imp, "Y_dom": Y_dom,
        "imptax_j": imptax_j,
        "prod_labels": {k_: f"{k_} - {prod_name[k_]}" for k_ in prod_keys},
        "ind_labels": {k_: f"{k_} - {ind_name[k_]}" for k_ in ind_keys},
        "ind_code": ind_code, "ind_name": ind_name,
        "prod_code": prod_code, "prod_name": prod_name,
        "pais": "Colombia", "anio": anio,
        "unidad": "miles de millones de pesos corrientes",
    }
