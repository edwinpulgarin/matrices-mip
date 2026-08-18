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

import numpy as np
import pandas as pd

from .. import crudo as _crudo

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

    # ── demanda final IMPORTADA, para la versión total de la MIP ──────────
    # El cuadro de importados tiene las mismas columnas de uso que el de
    # nacionales —consumo final y formación de capital— y después, en vez de las
    # exportaciones, la fila de origen: «Importaciones / Bienes» y «Servicios».
    # Esas dos NO son uso, son la oferta importada del producto, así que se
    # descartan acá: el uso importado ya está en U_imp más estas dos columnas.
    fdc_i, fdn_i = [], []
    grupo = ""
    for c in range(ic_nac[-1] + 1, imp.shape[1]):
        top, det = _n(imp.iat[HR_CONCEPTO, c]), _n(imp.iat[HR_COD_IND, c])
        if top:
            grupo = top
        etiqueta = det or grupo
        cl = _clave(etiqueta)
        if not etiqueta or cl.startswith("total") or cl.startswith("importaciones") \
                or _clave(grupo).startswith("importaciones") or "cif" in cl:
            continue
        fdc_i.append(c)
        fdn_i.append(etiqueta if cl == _clave(grupo) else f"{grupo} {etiqueta}".strip())
    Y_imp = pd.DataFrame(_num(imp.iloc[ri, fdc_i]).to_numpy(), index=prod_keys, columns=fdn_i)

    # ── impuestos y márgenes por industria: MEDIDOS, no repartidos ────────
    #   COU a precios de comprador − MUPNI a precios básicos (dom + imp)
    imptax_j = (U_pc.sum(axis=0) - U_dom.sum(axis=0) - U_imp.sum(axis=0)).reindex(ind_keys).fillna(0.0)

    if verbose:
        print(f"  [CO {anio}] prod={len(prod_keys)} ind={len(ind_keys)} fd={len(fdn)} "
              f"U_dom={U_dom.to_numpy().sum():,.0f} U_imp={U_imp.to_numpy().sum():,.0f}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "U_dom": U_dom, "U_imp": U_imp, "Y_dom": Y_dom,
        "Y_imp": Y_imp,
        # Colombia cruza dos archivos: el COU da oferta y uso a precios básicos,
        # la MUPNI da el corte nacional/importado. Van los cuatro cuadros.
        "crudo": [_crudo.hoja("COU Oferta", of, f_cou, f"Cuadro {1 + 2 * k}"),
                  _crudo.hoja("COU Utilización", us, f_cou, f"Cuadro {2 + 2 * k}"),
                  _crudo.hoja("MUPNI importados", imp, f_mup, f"Cuadro {1 + 2 * k}"),
                  _crudo.hoja("MUPNI nacionales", nac, f_mup, f"Cuadro {2 + 2 * k}")],
        "imptax_j": imptax_j,
        "prod_labels": {k_: f"{k_} - {prod_name[k_]}" for k_ in prod_keys},
        "ind_labels": {k_: f"{k_} - {ind_name[k_]}" for k_ in ind_keys},
        "ind_code": ind_code, "ind_name": ind_name,
        "prod_code": prod_code, "prod_name": prod_name,
        "pais": "Colombia", "anio": anio,
        "unidad": "miles de millones de pesos corrientes",
    }


# ───────────────────────────────────────────────────────────────────────────
# Variante SÓLO COU: un único archivo, el mismo camino que los otros países
# ───────────────────────────────────────────────────────────────────────────
#
# Lee el COU y nada más. La utilización queda a precios de comprador y el puente
# a básicos —impuestos, subvenciones, márgenes de comercio y transporte, IVA— sale
# del propio cuadro, por producto, que es como lo publican las cinco fuentes. De
# ahí en adelante corre `valoracion.valorar_argentina`, el Cap. 7 del Handbook,
# igual que Argentina, Brasil, Uruguay y México.
#
# Qué se gana y qué se paga, dicho sin adornos:
#
#   + Una sola fuente por país y un solo método para los cinco.
#   + La demanda final con TODO el detalle que el COU publica —hogares, ISFLSH,
#     gobierno, formación bruta de capital fijo, variación de existencias,
#     objetos valiosos, exportaciones—, cada componente con su propio puente de
#     valoración. La MUPNI sólo tenía cuatro columnas agregadas.
#   + El control de cobertura (`cobertura.py`) pasa a aplicar: hay `OPC` contra
#     qué contrastar lo leído, cosa que con la MUPNI no existía.
#   + La cobertura temporal deja de estar atada a la MUPNI (2014-2020).
#
#   − El reparto de impuestos y márgenes DENTRO de cada fila es proporcional
#     (§7.76), porque el COU publica el puente por producto y no por celda.
#     Medido contra el dato real de INEGI 2013: correlación 0,990 celda a celda,
#     error mediano por industria 1,64 %.
#
# El otro supuesto, el del origen nacional/importado (§8.33) —el que infla los
# multiplicadores hasta 5,65 %—, NO interviene: estas matrices son la versión
# TOTAL, y ahí las dos partes se vuelven a sumar.
#
# El propio COU permite medir el primer supuesto: publica cada componente de
# demanda final a precios básicos, así que el resultado prorrateado se puede
# contrastar contra el dato. `Y_basico` sale del parser justamente para eso.

_HR_ENC = range(8, 13)      # filas del encabezado de dos y tres niveles


def _rutas(d: pd.DataFrame, desde: int) -> dict[int, list[str]]:
    """Ruta de encabezado de cada columna, arrastrando los niveles vacíos.

    El DANE escribe el encabezado en varios niveles y sólo pone el rótulo del
    grupo en su PRIMERA columna, así que leer una fila suelta no alcanza:
    'A precios básicos' aparece siete veces y sólo la ruta completa dice a cuál
    de los siete componentes pertenece. Al cambiar un nivel se limpian los de
    abajo, si no una rama arrastra el detalle de la anterior.
    """
    carry: dict[int, str] = {}
    rutas: dict[int, list[str]] = {}
    for c in range(desde, d.shape[1]):
        for r in _HR_ENC:
            v = _n(d.iat[r, c])
            if v:
                carry[r] = v
                for rr in _HR_ENC:
                    if rr > r:
                        carry.pop(rr, None)
        rutas[c] = [carry[r] for r in _HR_ENC if carry.get(r)]
    return rutas


def _col_ruta(rutas: dict[int, list[str]], *claves) -> int:
    """Primera columna cuya ruta contiene todas las claves, en orden.

    Cada clave puede ser un texto o una tupla de alternativas: las fuentes
    renombran columnas entre ediciones y el parser tiene que sobrevivir a eso.
    """
    objetivo = [tuple(_clave(x) for x in (k if isinstance(k, tuple) else (k,)))
                for k in claves]
    for c, ruta in rutas.items():
        r = [_clave(x) for x in ruta]
        i = 0
        for parte in r:
            if i < len(objetivo) and any(alt in parte for alt in objetivo[i]):
                i += 1
        if i == len(objetivo):
            return c
    raise KeyError(f"no encontré columna para la ruta {claves!r}")


# Componentes de demanda final del COU, con la ruta que los identifica. El orden
# es el de la publicación y se conserva en el libro.
_FD_COU = [
    ("Hogares", ("gasto de consumo final", "hogares")),
    # El DANE renombró la columna en 2020: antes «Instituciones sin fines de
    # lucro que sirven a los hogares», después «ISFLH1» (con llamada al pie). Se
    # aceptan los dos rótulos o el parser se queda sin los años recientes.
    ("ISFLSH", ("gasto de consumo final", ("instituciones sin fines", "isfl"))),
    ("Gobierno", ("gasto de consumo final", "gobierno", "total")),
    ("Formación bruta de capital fijo", ("formacion bruta de capital",
                                         "formacion bruta de capital fijo")),
    ("Variación de existencias", ("formacion bruta de capital",
                                  "variacion de existencias")),
    ("Objetos valiosos", ("formacion bruta de capital", "adquisicion menos")),
    ("Exportaciones", ("exportaciones", "total")),
]


def parse_cou(carpeta: str | Path, anio: int = 2019, verbose: bool = False) -> dict:
    """COU del DANE, y sólo el COU: oferta, utilización y puente de valoración."""
    carpeta = Path(carpeta)
    f_cou = carpeta / "DANE_COU_2014_2024_corrientes.xlsx"
    if not f_cou.exists():
        raise FileNotFoundError(f_cou)
    k = anio - 2014
    if not 0 <= k <= 10:
        raise ValueError(f"el COU publicado cubre 2014-2024; pediste {anio}")

    of = pd.read_excel(f_cou, f"Cuadro {1 + 2 * k}", header=None)   # oferta
    us = pd.read_excel(f_cou, f"Cuadro {2 + 2 * k}", header=None)   # utilización

    ro, ru = _filas_producto(of), _filas_producto(us)
    prod_keys = [_n(us.iat[r, 0]) for r in ru]
    prod_name = {k_: _n(us.iat[r, 1]) for k_, r in zip(prod_keys, ru)}
    if [_n(of.iat[r, 0]) for r in ro] != prod_keys:
        raise ValueError("los productos de la oferta y la utilización no coinciden")

    c_of = _col_concepto(of, "Produccion segun divisiones CIIU")
    c_us = _col_concepto(us, "Consumo intermedio segun divisiones CIIU")
    ic_of, ic_us = _cols_industria(of, c_of), _cols_industria(us, c_us)
    for nom, cc in (("oferta", ic_of), ("utilización", ic_us)):
        if len(cc) != N_IND:
            raise ValueError(f"{nom}: esperaba {N_IND} industrias, encontré {len(cc)}")

    ind_keys, ind_code, ind_name = [], {}, {}
    for c_o, c_u in zip(ic_of, ic_us):
        cod = _n(of.iat[HR_COD_IND, c_o]).split()[0] or _n(us.iat[HR_COD_IND, c_u])
        nom = _n(us.iat[HR_NOM_IND, c_u]) or _n(of.iat[HR_NOM_IND, c_o]) or cod
        while cod in ind_code:
            cod += "'"
        ind_keys.append(cod); ind_code[cod] = cod; ind_name[cod] = nom

    def bloque(d, filas, cols):
        return pd.DataFrame(_num(d.iloc[filas, cols]).to_numpy(),
                            index=prod_keys, columns=ind_keys)

    V_pi = bloque(of, ro, ic_of)
    U_pc = bloque(us, ru, ic_us)

    # ── puente de valoración, del cuadro de oferta ────────────────────────
    ro_of = _rutas(of, 1)
    col = lambda *cl: pd.Series(_num(of.iloc[ro, _col_ruta(ro_of, *cl)]).to_numpy(),
                                index=prod_keys)
    OPC = col("total oferta a precios comprador")
    OPB = col("produccion a precios basicos", "total")
    Ajuste = col("importaciones", "ajustes")
    IMPO = col("importaciones", "bienes") + col("importaciones", "servicios")
    MgC = col("margenes de comercio")
    MgT = col("margenes de transporte")
    IP = col("impuestos a los productos") - col("subvenciones a los productos")
    DI = col("impuestos y derechos a las importaciones")
    IVA = col("iva no deducible")
    val = pd.DataFrame({"OPB": OPB, "IMPO": IMPO, "Ajuste": Ajuste,
                        "IP": IP, "DI": DI, "IVA": IVA,
                        "MgC": MgC, "MgT": MgT, "Mg": MgC + MgT, "OPC": OPC})

    # El puente del propio cuadro tiene que cerrar: básicos + impuestos +
    # márgenes = comprador. Cuando no cierra, el residuo es de la FUENTE y hay
    # que medirlo y publicarlo, no taparlo ni abortar por él: el DANE deja 544
    # en el producto 01 de 2014 (1,1 % de su oferta) y 8 en 2015. Se corta sólo
    # si el residuo agregado deja de ser ruido, que sería síntoma de una columna
    # mal leída y no de un redondeo del instituto.
    puente = OPB + IMPO + Ajuste + IP + DI + IVA + MgC + MgT - OPC
    rel = float(puente.abs().sum()) / max(float(OPC.sum()), 1.0)
    if rel > 1e-3:
        raise ValueError(f"el puente de valoración no cierra: {rel:.2%} de la oferta "
                         f"(máx {puente.abs().max():,.2f} en «{puente.abs().idxmax()}»)")

    # ── demanda final: cada componente con su columna ─────────────────────
    ru_us = _rutas(us, ic_us[-1] + 1)
    Y_pc, Y_basico = {}, {}
    for nombre, ruta in _FD_COU:
        Y_pc[nombre] = _num(us.iloc[ru, _col_ruta(ru_us, *ruta, "a precios de comprador")])\
            .to_numpy().ravel()
        Y_basico[nombre] = _num(us.iloc[ru, _col_ruta(ru_us, *ruta, "a precios basicos")])\
            .to_numpy().ravel()
    Y_pc = pd.DataFrame(Y_pc, index=prod_keys)
    Y_basico = pd.DataFrame(Y_basico, index=prod_keys)

    # ── valor agregado por industria, de la fila del propio cuadro ────────
    fila_va = next((r for r in range(ru[-1] + 1, us.shape[0])
                    if _clave(_n(us.iat[r, 1])) == "valor agregado"), None)
    if fila_va is None:
        raise ValueError("no encontré la fila «Valor agregado» en el cuadro de utilización")
    VA = pd.DataFrame([_num(us.iloc[[fila_va], ic_us]).to_numpy().ravel()],
                      index=["valor_agregado_bruto"], columns=ind_keys)

    if verbose:
        print(f"  [CO-COU {anio}] prod={len(prod_keys)} ind={len(ind_keys)} "
              f"U_pc={U_pc.to_numpy().sum():,.0f} OPC={OPC.sum():,.0f} "
              f"VA={VA.to_numpy().sum():,.0f}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "Y_pc": Y_pc, "val": val, "VA": VA,
        "residuo_valoracion": puente,
        # el mismo dato a precios básicos, publicado: sirve para MEDIR el error
        # del reparto proporcional en vez de suponerlo chico
        "Y_basico": Y_basico,
        "crudo": [_crudo.hoja("COU Oferta", of, f_cou, f"Cuadro {1 + 2 * k}"),
                  _crudo.hoja("COU Utilización", us, f_cou, f"Cuadro {2 + 2 * k}")],
        "prod_labels": {k_: f"{k_} - {prod_name[k_]}" for k_ in prod_keys},
        "ind_labels": {k_: f"{k_} - {ind_name[k_]}" for k_ in ind_keys},
        "ind_code": ind_code, "ind_name": ind_name,
        "prod_code": {k_: k_ for k_ in prod_keys}, "prod_name": prod_name,
        "pais": "Colombia", "anio": anio,
        "unidad": "miles de millones de pesos corrientes",
    }


# ───────────────────────────────────────────────────────────────────────────
# Variante DETALLADA: la matriz D calculada sobre los 392 productos del COU
# ───────────────────────────────────────────────────────────────────────────
#
# Por qué existe. `Z = D·U` con `D = V·diag(q)⁻¹`, y esa operación NO conmuta con
# agregar productos: agrupar productos heterogéneos promedia sus cuotas de
# mercado antes de repartir. El DANE construye su D sobre el COU de 392
# productos —Anexo 1 de DSO-MIP-MET-001: «Nomenclatura 392 productos cuadro de
# oferta y utilización → Nomenclatura 68 productos matriz insumo-producto»— y la
# variante de arriba la construye sobre 66. Medido sobre nuestros propios datos,
# bajar de 66 a 44 productos ya mueve Z un 33 % dejando las columnas intactas,
# así que el detalle de producto es el término dominante de la diferencia contra
# la matriz publicada.
#
# El mismo archivo que ya leemos trae los dos niveles: los Cuadros 1-22 están a
# dos dígitos CPC y los Cuadros 23-44 repiten los mismos años a seis dígitos.
#
# Qué se mide y qué se supone. La MUPNI —el corte doméstico/importado, ya a
# precios básicos— existe SÓLO a 66 productos, y en el COU detallado el bloque de
# 61 industrias está a precios de comprador. Así que el uso doméstico a 392 se
# arma repartiendo el dato medido de la MUPNI entre los subproductos de cada
# grupo, con la estructura que el propio COU detallado publica:
#
#     U_dom[p,j] = U_dom66[g(p),j] · U_pc[p,j] / Σ_{p'∈g(p)} U_pc[p',j]
#
# El supuesto es que, dentro de un grupo CPC de dos dígitos y para una misma
# industria, la participación importada y la cuña de impuestos y márgenes son
# parejas entre subproductos. Es mucho más débil que el prorrateo del §8.33, que
# supone lo mismo a lo ancho de TODAS las industrias. Y los dos invariantes que
# importan se conservan exactos: los totales por columna de U_dom son los de la
# MUPNI, y los totales por grupo de producto también.
#
# Lo que esta variante NO puede cerrar: el DANE publica su MIP a 68 actividades
# y el COU trae 61, y el Anexo 2 muestra que no es un refinamiento sino un CRUCE
# (por eso la partición común da 58, menos que ambas). Pasar de 61 a 68 exige
# microdatos que no se publican.

_HR_DET = 9          # fila de concepto en los cuadros detallados
_HR_COD_DET = 10     # fila con el código de industria (código + salto + nombre)
_COD_DET = re.compile(r"^\d{6}$")

# Bloques de columnas, estables en todos los años de la publicación.
_OF_IND = (10, 70)   # oferta detallada: producción por industria, precios básicos
_OF_IMPO = (78, 79)  # oferta detallada: importaciones (bienes, servicios)
_US_IND = (5, 65)    # utilización detallada: consumo intermedio a precios de comprador
_US_FD = {           # totales de demanda final a precios de comprador
    "consumo_final": 76,
    "formacion_bruta_capital": 104,
    "exportaciones": 131,
}


def _filas_det(d: pd.DataFrame) -> list[int]:
    return [r for r in range(_HR_COD_DET + 1, d.shape[0])
            if _COD_DET.match(_n(d.iat[r, 0]))]


def _bloque_det(d: pd.DataFrame, filas: list[int], c0: int, c1: int,
                cod: list[str], cols) -> pd.DataFrame:
    return pd.DataFrame(_num(d.iloc[filas, c0:c1 + 1]).to_numpy(), index=cod, columns=cols)


def _puente_a_mupni(det: list[str], grupos: list[str]) -> dict:
    """Código CPC de seis dígitos -> grupo de la MUPNI.

    El grupo es el prefijo de dos dígitos, salvo que la MUPNI publique varias
    divisiones juntas ('12 + 13', '64 + 65 + 66'), en cuyo caso el prefijo cae
    en el grupo que lo contiene.
    """
    de_prefijo = {}
    for g in grupos:
        for parte in re.split(r"\s*\+\s*", g):
            de_prefijo[parte.strip().zfill(2)] = g
    mapa, huerfanos = {}, set()
    for c in det:
        g = de_prefijo.get(c[:2])
        if g is None:
            huerfanos.add(c[:2])
        else:
            mapa[c] = g
    return mapa, sorted(huerfanos)


def parse_detallado(carpeta: str | Path, anio: int = 2019, verbose: bool = False) -> dict:
    """COU a seis dígitos (392 productos) cruzado con la MUPNI de 66.

    Devuelve la misma estructura que `parse`, para que el resto del motor no
    cambie: `ensamblar_directo` la toma igual.
    """
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
    of = hoja(f_cou, 23 + 2 * k)          # oferta, seis dígitos
    us = hoja(f_cou, 24 + 2 * k)          # utilización, seis dígitos
    imp = hoja(f_mup, 1 + 2 * k)          # MUPNI importados (66 productos)
    nac = hoja(f_mup, 2 + 2 * k)          # MUPNI nacionales

    # ── industrias: el código va en la fila 10, pegado al nombre ──────────
    def ind_det(d):
        out = []
        for c in range(d.shape[1]):
            txt = str(d.iat[_HR_COD_DET, c])
            if txt.strip() in ("", "nan"):
                continue
            out.append((c, _n(txt.split("\n")[0])))
        return out

    cols_of = [c for c, _ in ind_det(of) if _OF_IND[0] <= c <= _OF_IND[1]]
    cols_us = [c for c, _ in ind_det(us) if _US_IND[0] <= c <= _US_IND[1]]
    if len(cols_of) != N_IND or len(cols_us) != N_IND:
        raise ValueError(f"CO {anio} detallado: esperaba {N_IND} industrias, "
                         f"encontré {len(cols_of)} en oferta y {len(cols_us)} en utilización")

    # Los códigos y nombres se toman de la variante a dos dígitos, que ya los
    # resuelve y es la que rotula los libros: así las dos versiones de Colombia
    # son comparables columna a columna.
    base = parse(carpeta, anio)
    ind_keys = list(base["U_dom"].columns)

    # ── productos a seis dígitos ──────────────────────────────────────────
    r_of, r_us = _filas_det(of), _filas_det(us)
    cod_of = [_n(of.iat[r, 0]) for r in r_of]
    cod_us = [_n(us.iat[r, 0]) for r in r_us]
    prod = [c for c in cod_us if c in set(cod_of)] or cod_us

    V_pi = _bloque_det(of, r_of, cols_of[0], cols_of[-1], cod_of, ind_keys) \
        .groupby(level=0).sum().reindex(prod).fillna(0.0)
    U_pc = _bloque_det(us, r_us, cols_us[0], cols_us[-1], cod_us, ind_keys) \
        .groupby(level=0).sum().reindex(prod).fillna(0.0)
    Y_pc = pd.DataFrame(
        {nombre: _num(us.iloc[r_us, [c]]).to_numpy().ravel() for nombre, c in _US_FD.items()},
        index=cod_us).groupby(level=0).sum().reindex(prod).fillna(0.0)

    # ── puente a los grupos de la MUPNI ───────────────────────────────────
    grupos = list(base["U_dom"].index)
    mapa, huerfanos = _puente_a_mupni(prod, grupos)
    if huerfanos:
        # un prefijo sin grupo en la MUPNI significaría tirar uso; se exige que
        # no mueva valor antes de dejarlo pasar
        perdido = float(U_pc.loc[[p for p in prod if p[:2] in huerfanos]].to_numpy().sum())
        if abs(perdido) > 1e-6 * max(float(U_pc.to_numpy().sum()), 1.0):
            raise ValueError(f"CO {anio} detallado: los prefijos {huerfanos} no tienen "
                             f"grupo en la MUPNI y mueven {perdido:,.0f} de consumo intermedio")
    prod = [p for p in prod if p in mapa]
    V_pi, U_pc, Y_pc = V_pi.loc[prod], U_pc.loc[prod], Y_pc.loc[prod]
    g = pd.Series({p: mapa[p] for p in prod})

    # ── repartir el dato MEDIDO de la MUPNI entre los subproductos ────────
    def repartir(M66: pd.DataFrame, estructura: pd.DataFrame) -> pd.DataFrame:
        """M66 (grupo × col) -> (subproducto × col) con los pesos de `estructura`.

        Si dentro de un grupo la estructura es toda cero para esa columna, se cae
        al peso por fila del grupo; y si tampoco hay, se reparte parejo. Nunca se
        pierde valor: la suma por grupo y por columna se conserva.
        """
        e = estructura.reindex(index=g.index, columns=M66.columns).fillna(0.0)
        den = e.groupby(g).transform("sum").to_numpy()          # por grupo y columna
        num = e.to_numpy()

        fila = e.sum(axis=1)                                     # peso por producto
        den_f = fila.groupby(g).transform("sum").to_numpy()[:, None]
        w_fila = np.divide(fila.to_numpy()[:, None], den_f,
                           out=np.zeros((len(g), 1)), where=den_f > 0)

        n = pd.Series(1.0, index=g.index).groupby(g).transform("sum").to_numpy()[:, None]
        w_par = 1.0 / n                                          # reparto parejo

        w = np.divide(num, den, out=np.zeros_like(num), where=den > 0)
        sin_col = den <= 0                                       # la columna no discrimina
        w = np.where(sin_col, np.broadcast_to(w_fila, w.shape), w)
        sin_nada = sin_col & (den_f <= 0)                        # el grupo entero es cero
        w = np.where(sin_nada, np.broadcast_to(w_par, w.shape), w)

        valores = M66.reindex(g.to_numpy()).to_numpy()           # una fila por producto
        return pd.DataFrame(w * valores, index=g.index, columns=M66.columns)

    # La estructura de reparto no puede ser la misma para lo doméstico y lo
    # importado. `U_pc` mezcla los dos orígenes, así que usarla para las dos
    # cosas le asigna uso doméstico a subproductos que en realidad se importan,
    # y la fila del producto deja de cerrar contra su oferta. Se pondera por la
    # participación doméstica de la OFERTA de cada subproducto, que el COU
    # detallado sí publica.
    opb = V_pi.sum(axis=1)
    impo = _num(of.iloc[r_of, [_OF_IMPO[0], _OF_IMPO[1]]]).sum(axis=1)
    impo = pd.Series(impo.to_numpy(), index=cod_of).groupby(level=0).sum().reindex(prod).fillna(0.0)
    dom_share = (opb / (opb + impo).replace(0, np.nan)).fillna(0.0).clip(0, 1)

    U_dom = repartir(base["U_dom"], U_pc.mul(dom_share, axis=0))
    U_imp = repartir(base["U_imp"], U_pc.mul(1.0 - dom_share, axis=0))

    # Para la demanda final el peso no puede ser el mismo para todas las
    # columnas: la composición por producto de las exportaciones no se parece a
    # la del consumo de los hogares. Cada columna nativa de la MUPNI se lleva al
    # agregado detallado que le corresponde (consumo, capital o exportaciones) y
    # se reparte con ESE peso.
    from ..demanda_final import clasificar
    estr_Y = pd.DataFrame(index=Y_pc.index, columns=base["Y_dom"].columns, dtype=float)
    for col in base["Y_dom"].columns:
        clave = clasificar(col)
        peso = Y_pc[clave] if clave in Y_pc.columns else Y_pc.sum(axis=1)
        estr_Y[col] = peso.to_numpy()
    Y_dom = repartir(base["Y_dom"], estr_Y)

    # ── cerrar la fila de cada subproducto, grupo por grupo ───────────────
    # El reparto de arriba respeta los totales por columna y por grupo, pero no
    # la fila de cada subproducto: nada garantiza que el uso doméstico asignado
    # a un producto iguale su oferta doméstica. Se cierra con un ajuste
    # biproporcional DENTRO de cada grupo, sobre [U_dom | Y_dom].
    #
    # Los dos márgenes son consistentes por construcción, y ese es el punto: a
    # 66 productos el SUT de Colombia cierra EXACTO, así que dentro de cada
    # grupo la oferta doméstica de los subproductos suma lo mismo que el uso
    # doméstico que la MUPNI le asigna al grupo. El ajuste no inventa nada: sólo
    # decide cómo se reparte adentro, y deja el resultado balanceado a nivel de
    # producto, que es lo que permite que el balanceo general (Cap. 11) no tenga
    # que tocar Colombia.
    from ..balanceo import ras as _ras
    n_ind = U_dom.shape[1]
    for grupo, idx in g.groupby(g).groups.items():
        idx = list(idx)
        if len(idx) < 2:
            continue
        # El ajuste biproporcional exige márgenes NO NEGATIVOS (Handbook,
        # Box 11.3). Algunas columnas de formación bruta de capital son negativas
        # —desacumulación de existencias— y meterlas en el ajuste devuelve celdas
        # negativas minúsculas que después ensucian Z. Esas columnas se quedan
        # con su reparto estructural y salen del ajuste; su aporte se descuenta
        # del objetivo de fila para que los dos márgenes sigan cerrando.
        y66 = base["Y_dom"].loc[grupo].to_numpy()
        pos = y66 >= 0
        Yn = Y_dom.loc[idx].to_numpy()[:, ~pos]
        W0 = np.hstack([U_dom.loc[idx].to_numpy(), Y_dom.loc[idx].to_numpy()[:, pos]])
        u = opb.reindex(idx).fillna(0.0).to_numpy() - Yn.sum(axis=1)
        v = np.concatenate([base["U_dom"].loc[grupo].to_numpy(), y66[pos]])
        if (u < 0).any():
            if verbose:
                print(f"  [CO {anio} detallado] grupo {grupo}: la demanda final negativa "
                      f"supera la oferta de algún subproducto; se deja el reparto estructural")
            continue
        if not np.isclose(u.sum(), v.sum(), rtol=1e-7, atol=1e-6):
            # el grupo no cierra en la fuente: se deja como está y lo absorbe el
            # balanceo general, pero queda dicho en vez de tapado
            if verbose:
                print(f"  [CO {anio} detallado] grupo {grupo}: oferta {u.sum():,.1f} ≠ "
                      f"uso {v.sum():,.1f}; se deja al balanceo general")
            continue
        if W0.sum() <= 0 or u.sum() <= 0:
            continue
        W, _, _ = _ras(np.where(W0 > 0, W0, 1e-12), u, v, tol=1e-12)
        U_dom.loc[idx] = W[:, :n_ind]
        Yg = Y_dom.loc[idx].to_numpy().copy()
        Yg[:, pos] = W[:, n_ind:]
        Y_dom.loc[idx] = Yg

    prod_name = {p: _n(us.iat[r, 1]) for p, r in zip(cod_us, r_us) if p in set(prod)}
    imptax_j = (U_pc.sum(axis=0) - U_dom.sum(axis=0) - U_imp.sum(axis=0)) \
        .reindex(ind_keys).fillna(0.0)

    if verbose:
        print(f"  [CO {anio} detallado] prod={len(prod)} ind={len(ind_keys)} "
              f"U_dom={U_dom.to_numpy().sum():,.0f} (MUPNI {base['U_dom'].to_numpy().sum():,.0f}) "
              f"U_imp={U_imp.to_numpy().sum():,.0f}")

    return {
        "V_pi": V_pi, "U_pc": U_pc, "U_dom": U_dom, "U_imp": U_imp, "Y_dom": Y_dom,
        "crudo": [_crudo.hoja("COU Oferta 6 díg.", of, f_cou, f"Cuadro {23 + 2 * k}"),
                  _crudo.hoja("COU Utilización 6 díg.", us, f_cou, f"Cuadro {24 + 2 * k}"),
                  _crudo.hoja("MUPNI importados", imp, f_mup, f"Cuadro {1 + 2 * k}"),
                  _crudo.hoja("MUPNI nacionales", nac, f_mup, f"Cuadro {2 + 2 * k}")],
        "imptax_j": imptax_j,
        "prod_labels": {p: f"{p} - {prod_name.get(p, p)}" for p in prod},
        "ind_labels": base["ind_labels"],
        "ind_code": base["ind_code"], "ind_name": base["ind_name"],
        "prod_code": {p: p for p in prod}, "prod_name": prod_name,
        "pais": "Colombia", "anio": anio,
        "unidad": "miles de millones de pesos corrientes",
    }
