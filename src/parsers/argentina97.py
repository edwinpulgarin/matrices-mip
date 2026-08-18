"""
Argentina 1997 — la MIPAr97 del INDEC, que publica el COU COMPLETO.

Este parser es distinto de `argentina.py`: no lee un COU moderno sino la
publicación de la Matriz Insumo-Producto Argentina 1997, que trae 16 cuadros y
entre ellos **todas las piezas medidas celda a celda**:

    Cuadro 1   Matriz de oferta a precios básicos        producto × actividad
    Cuadro 2   Matriz de utilización a precios de comprador
    Cuadro 3   Matriz de utilización a precios básicos — SÓLO ORIGEN NACIONAL
    Cuadro 4   Matriz de importaciones a precios CIF
    Cuadro 12  Matriz simétrica de insumo producto (el resultado oficial)

Con eso Argentina 1997 se construye **sin ningún prorrateo**: el corte
doméstico/importado está medido (cuadro 4) y la cuña de impuestos y márgenes
sale por diferencia celda a celda (cuadro 2 − cuadro 3 − cuadro 4). Es el único
año de Argentina donde esto es posible; el COU moderno (2004, 2018-2023) sólo
publica esas piezas por producto.

Ojo con el cuadro 3: la metodología (pág. 21-22) dice que «las filas muestran el
destino de los productos de origen **nacional** a precios básicos», así que ya es
la matriz doméstica y NO hay que restarle el cuadro 4. Restárselo descuadra un
11 %.

Dimensiones: 195 productos × 124 ramas de actividad.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .. import crudo as _crudo

N_ACT = 124
N_PROD = 195
FILA_NUM = 5      # fila con el número de orden de cada actividad
FILA_NOM = 7      # fila con la denominación de la actividad
FILA_GRUPO = 6    # fila con el detalle de las columnas de demanda final
R0 = 8            # primera fila de producto

# Columnas de demanda final del cuadro 3 (y del 2, que comparte layout). Se
# toman sólo las HOJAS del árbol: el cuadro publica además los subtotales
# (TOTAL de exportaciones, SUBTOTAL HOGARES, etc.) y sumarlos duplicaría.
HOJAS_DF = {
    128: "Exportaciones - bienes",
    129: "Exportaciones - servicios",
    131: "Consumo - gasto de los hogares",
    132: "Consumo - transferencias a los hogares",
    134: "Consumo ISFLSH - instituciones sin fines de lucro",
    135: "Consumo - gobierno",
    137: "Formación bruta de capital fijo",
    138: "Variación de existencias",
}

# Actividades de NO MERCADO y hogares. El SCN no les atribuye ventas
# intermedias —su producción va a consumo final de gobierno o de los hogares— y
# la simétrica del INDEC lo refleja: estas cuatro filas están en cero. Sin esta
# regla el Modelo D les asignaría parte del uso intermedio del producto que
# comparten con su par privado (p. ej. «Servicios de salud humana», producido en
# un 29,85 % por la pública y en un 70,15 % por la privada).
NO_MERCADO = ["Enseñanza pública", "Salud humana pública",
              "Servicios sociales", "Servicio doméstico"]


def _es_entero(x) -> bool:
    try:
        v = float(str(x).strip())
        return v == int(v)
    except (TypeError, ValueError):
        return False


def _hoja(carpeta: Path, n: int) -> pd.DataFrame:
    f = carpeta / f"mip_matriz{n}.xls"
    if not f.exists():
        raise FileNotFoundError(f)
    return pd.read_excel(f, sheet_name=0, header=None)


def _cols_actividad(d: pd.DataFrame, c0: int) -> list[int]:
    """Las columnas de actividad son la secuencia 1..124 de la fila 5.

    Se busca por la secuencia y no por posición porque cada cuadro arranca en
    una columna distinta (el 1 tiene antes el puente de valoración) y después de
    las actividades siguen totales que también son numéricos.
    """
    seq, esperado = [], 1
    for c in range(c0, d.shape[1]):
        if _es_entero(d.iat[FILA_NUM, c]) and int(float(d.iat[FILA_NUM, c])) == esperado:
            seq.append(c)
            esperado += 1
            if len(seq) == N_ACT:
                break
    if len(seq) != N_ACT:
        raise ValueError(f"esperaba {N_ACT} actividades y encontré {len(seq)}")
    return seq


def _filas_producto(d: pd.DataFrame) -> list[int]:
    return [r for r in range(R0, d.shape[0]) if str(d.iat[r, 1]) != "nan"]


def _num(d, filas, cols):
    return d.iloc[filas, cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy()


def parse(carpeta: str | Path, anio: int = 1997, verbose: bool = False) -> dict:
    carpeta = Path(carpeta)
    d1, d2, d3, d4 = (_hoja(carpeta, n) for n in (1, 2, 3, 4))

    c1 = _cols_actividad(d1, 8)     # el cuadro 1 trae antes el puente de valoración
    c2 = _cols_actividad(d2, 3)
    c3 = _cols_actividad(d3, 3)
    c4 = _cols_actividad(d4, 3)

    f1, f2, f3, f4 = (_filas_producto(d) for d in (d1, d2, d3, d4))
    prod = [str(d3.iat[r, 1]).strip() for r in f3]
    prod_nombre = {str(d3.iat[r, 1]).strip(): str(d3.iat[r, 2]).strip() for r in f3}
    act_nombre = [str(d3.iat[FILA_NOM, c]).strip() for c in c3]
    if len(set(act_nombre)) != N_ACT:
        raise ValueError("hay nombres de actividad repetidos en el cuadro 3")
    # El INDEC no le pone código a las ramas: las identifica por número de orden
    # (la fila 5 de cada cuadro y la columna A del cuadro 12). Ese número es la
    # clave, y así el nombre queda libre para ser la denominación.
    act = [str(i + 1) for i in range(N_ACT)]
    act_name = dict(zip(act, act_nombre))

    # los cuatro cuadros comparten producto y actividad, en el mismo orden
    for etq, d, f in (("1", d1, f1), ("2", d2, f2), ("4", d4, f4)):
        otros = [str(d.iat[r, 1]).strip() for r in f]
        if otros != prod:
            raise ValueError(f"los productos del cuadro {etq} no coinciden con los del 3")

    V_pi = pd.DataFrame(_num(d1, f1, c1), index=prod, columns=act)
    U_pc = pd.DataFrame(_num(d2, f2, c2), index=prod, columns=act)
    U_dom = pd.DataFrame(_num(d3, f3, c3), index=prod, columns=act)
    U_imp = pd.DataFrame(_num(d4, f4, c4), index=prod, columns=act)

    def demanda(d, filas):
        cols = sorted(HOJAS_DF)
        return pd.DataFrame(_num(d, filas, cols), index=prod,
                            columns=[HOJAS_DF[c] for c in cols])

    Y_dom = demanda(d3, f3)
    Y_pc = demanda(d2, f2)
    # El cuadro 4 (importaciones CIF) trae las mismas columnas de demanda
    # final: es lo que falta para la versión TOTAL de la MIP, que es además la
    # que el propio INDEC publica en su cuadro 12.
    Y_imp = demanda(d4, f4)

    # Cuña de impuestos, márgenes y gastos de nacionalización: es lo que separa
    # el precio de comprador del básico, MEDIDA celda a celda como diferencia de
    # cuadros publicados. No hay prorrateo en ningún paso.
    cuna = U_pc - U_dom - U_imp
    imptax_j = cuna.sum(axis=0)

    return {
        "V_pi": V_pi, "U_pc": U_pc, "U_dom": U_dom, "U_imp": U_imp,
        "Y_dom": Y_dom, "Y_pc": Y_pc, "Y_imp": Y_imp, "imptax_j": imptax_j, "cuna": cuna,
        "prod_code": {k: k for k in prod}, "prod_name": prod_nombre,
        "ind_code": {a: a for a in act}, "ind_name": act_name,
        "prod_labels": {k: f"{k} - {prod_nombre[k]}" for k in prod},
        "ind_labels": {a: f"{a} - {act_name[a]}" for a in act},
        "no_mercado": [a for a, nm in act_name.items() if nm in NO_MERCADO],
        "pais": "Argentina", "anio": anio,
        "unidad": "miles de pesos corrientes de 1997",
        "crudo": [_crudo.hoja("Cuadro 1 oferta", d1, carpeta / "mip_matriz1.xls", ""),
                  _crudo.hoja("Cuadro 2 util. comprador", d2, carpeta / "mip_matriz2.xls", ""),
                  _crudo.hoja("Cuadro 3 util. básicos", d3, carpeta / "mip_matriz3.xls", ""),
                  _crudo.hoja("Cuadro 4 importaciones", d4, carpeta / "mip_matriz4.xls", "")],
    }


def simetrica_oficial(carpeta: str | Path) -> pd.DataFrame:
    """El cuadro 12: la matriz simétrica que publica el INDEC, para contrastar."""
    carpeta = Path(carpeta)
    d = _hoja(carpeta, 12)
    cols = _cols_actividad(d, 2)
    filas = [r for r in range(R0, d.shape[0]) if _es_entero(d.iat[r, 0])][:N_ACT]
    # se indexa por número de orden, igual que el parser
    orden = [str(int(float(d.iat[r, 0]))) for r in filas]
    return pd.DataFrame(_num(d, filas, cols), index=orden, columns=orden)
