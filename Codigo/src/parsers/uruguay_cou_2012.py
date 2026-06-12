"""
Parser del Cuadro de Oferta y Utilización (COU) detallado de Uruguay 2012 — BCU.

Fuente: BCU, "Cuadro de Oferta y Utilización 2012, detallado, a precios
corrientes" (archivo Uruguay_2012_Detallada_COU_C.xlsx). A diferencia del COU
2017 de CEPAL (un archivo por cuadro), el 2012 viene en UNA sola hoja `COU_C`
con tres bloques apilados verticalmente que comparten las mismas 107 columnas
de industria (A.1 … T.1):

    Bloque 1 — OFERTA  (134 productos × 107 industrias)
        col 6  Oferta Total            col 7  Producción Total (= V por fila)
        cols 8-114 producción por industria (matriz V, producto × industria)
        col 115 Oferta Importada       col 116 Márgenes
        col 117 Impuestos netos        col 118 Ajuste CIF/FOB
    Bloque 2 — UTILIZACIÓN  (134 productos × 107 industrias), precios comprador
        col 6  Utilización Total       col 7  Utilización Intermedia Total
        cols 8-114 uso intermedio por industria (matriz U)
        col 115 Consumo Hogares        col 116 Consumo Gobierno+ISFLSH
        col 117 FBKF                   col 118 Variación de existencias
        col 119 Exportaciones
    Bloque 3 — VALOR AGREGADO (6 componentes × 107 industrias)

Reconstrucción idéntica a la de Uruguay 2017 (`uruguay_cou.py`): U se lleva a
precios básicos domésticos reescalando por producto con
producción_pb/(oferta_total−importada) capado en 1.0, y la demanda final
doméstica se cierra como residual oferta−uso intermedio. Así oferta = demanda a
precios básicos y la MIP queda comparable con el resto de la serie.

Unidad: millones de UYU a precios corrientes (2012).
"""

import re
import numpy as np
import pandas as pd
from pathlib import Path

from .base import COU

HOJA = 'COU_C'


def _industrias_cols(row7) -> list:
    """Columnas con encabezado tipo 'A.1', 'C.45', 'T.1' (patrón X.N)."""
    return [j for j, v in enumerate(row7) if re.match(r'^[A-Z]+\.\d+$', str(v).strip())]


def _bloques(df: pd.DataFrame) -> list:
    """
    Localiza los bloques 'Código/Denominación'. Devuelve, por bloque, la fila de
    encabezado y la lista de filas de datos (col 0 numérica) que le siguen.
    """
    encabezados = [r for r in range(len(df)) if str(df.iat[r, 0]).strip() == 'Código']
    bloques = []
    for k, h in enumerate(encabezados):
        fin = encabezados[k + 1] if k + 1 < len(encabezados) else len(df)
        filas = []
        for r in range(h + 1, fin):
            cod = str(df.iat[r, 0]).strip()
            if cod in ('', 'nan'):
                continue
            try:
                float(cod)
            except ValueError:
                continue
            filas.append(r)
        bloques.append((h, filas))
    return bloques


def _codigo(df, r):
    return f"{str(df.iat[r, 0]).strip()}---{str(df.iat[r, 1]).strip()}"


def parsear(carpeta: Path, anio: int = 2012, verbose: bool = False) -> COU:
    """Lee el COU detallado de Uruguay 2012 y retorna un objeto COU doméstico."""
    carpeta = Path(carpeta)
    archivo = carpeta / 'cou_2012' / 'Uruguay_2012_Detallada_COU_C.xlsx'
    if not archivo.exists():
        # respaldo: archivo suelto en la carpeta del país
        cand = list(carpeta.glob('*2012*Detallada*COU*C*.xlsx'))
        if not cand:
            raise FileNotFoundError(f"No se encontró el COU 2012 de Uruguay en {carpeta}")
        archivo = cand[0]

    if verbose:
        print(f"  Leyendo COU Uruguay 2012 de {archivo.name}...")

    df = pd.read_excel(archivo, sheet_name=HOJA, header=None, engine='openpyxl')
    row7 = df.iloc[7].tolist()
    ind_cols = _industrias_cols(row7)
    ind_labels = [str(row7[j]).strip() for j in ind_cols]

    bloques = _bloques(df)
    if len(bloques) < 3:
        raise ValueError(f"Se esperaban 3 bloques (oferta/uso/VA), hay {len(bloques)}")
    (_, filas_of), (_, filas_uso), (h_va, filas_va) = bloques[0], bloques[1], bloques[2]

    prod_of = [_codigo(df, r) for r in filas_of]
    prod_uso = [_codigo(df, r) for r in filas_uso]

    # — Bloque 1: oferta —
    V_raw = df.iloc[filas_of, ind_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    V_raw.index, V_raw.columns = prod_of, ind_labels        # producto × industria
    importada = pd.to_numeric(df.iloc[filas_of, 115], errors='coerce').fillna(0)
    importada.index = prod_of
    oferta_total = pd.to_numeric(df.iloc[filas_of, 6], errors='coerce').fillna(0)
    oferta_total.index = prod_of
    margenes = pd.to_numeric(df.iloc[filas_of, 116], errors='coerce').fillna(0)
    margenes.index = prod_of
    impuestos = pd.to_numeric(df.iloc[filas_of, 117], errors='coerce').fillna(0)
    impuestos.index = prod_of

    # — Bloque 2: utilización (precios comprador, total nacional+importado) —
    U_raw = df.iloc[filas_uso, ind_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    U_raw.index, U_raw.columns = prod_uso, ind_labels        # producto × industria

    # — Alinear productos comunes (oferta y uso comparten códigos y orden) —
    prods = [p for p in prod_of if p in set(prod_uso)]
    V = V_raw.loc[prods].T.clip(lower=0)                      # industria × producto
    U_total_pc = U_raw.loc[prods]
    importada = importada.reindex(prods).fillna(0)
    oferta_total = oferta_total.reindex(prods).fillna(0)
    margenes = margenes.reindex(prods).fillna(0)
    impuestos = impuestos.reindex(prods).fillna(0)

    # — Etiquetas de industria por producto principal (como en 2017) —
    label_by_act = {}
    for act in ind_labels:
        fila = V.loc[act]
        if fila.empty or fila.max() <= 0:
            label_by_act[act] = f"{act} — actividad económica {act}"
        else:
            principal = str(fila.idxmax()).split('---', 1)[-1]
            label_by_act[act] = f"{act} — {principal}"
    act_labels = [label_by_act[a] for a in ind_labels]
    V.index = act_labels
    U_total_pc.columns = act_labels

    # — Precios comprador → básicos domésticos (factor capado en 1.0) —
    q_pb = V.sum(axis=0)                                      # producción a pb por producto
    oferta_domestica_pc = (oferta_total - importada).clip(lower=0)
    factor_pb = q_pb.div(oferta_domestica_pc.replace(0, np.nan)).fillna(1.0).clip(lower=0, upper=1.0)
    U = U_total_pc.mul(factor_pb, axis=0).clip(lower=0)

    # — Demanda final doméstica residual para cerrar oferta = demanda a pb —
    Y_residual = q_pb - U.sum(axis=1)
    Y = Y_residual.to_frame('demanda_final_domestica_residual_pb')

    # — Valor agregado: VAB publicado por industria (bloque 3). Ese bloque trae
    #   una columna 'Subtotal' extra, así que sus industrias arrancan desplazadas;
    #   se detectan con el encabezado propio del bloque (no el de la oferta). —
    va_cols = _industrias_cols(df.iloc[h_va].tolist())
    fila_vab = filas_va[-1]                                   # 'Valor agregado bruto/PIB'
    W_vals = pd.to_numeric(df.iloc[fila_vab, va_cols], errors='coerce').fillna(0)
    if len(va_cols) == len(act_labels):
        W = pd.DataFrame([W_vals.values], index=['valor_agregado_bruto'], columns=act_labels)
    else:                                                    # respaldo: VA residual
        g = V.sum(axis=1)
        W = (g - U.sum(axis=0)).to_frame('valor_agregado_bruto').T
        W.columns = act_labels

    M_sums = importada.rename('importaciones')

    if verbose:
        print(f"  2012: V={V.shape}, U={U.shape}, {len(act_labels)} act × {len(prods)} prod")

    return COU(
        pais='uruguay', anio=2012, moneda='UYU', unidad='millones',
        V=V, U=U, Y=Y, W=W, M=M_sums,
        T=margenes, imp_ind=impuestos,
        U_importada=pd.DataFrame(0.0, index=U.index, columns=U.columns),
        notas=[
            'U usa solo consumo intermedio nacional.',
            'U nacional se aproxima a precios basicos reescalando pc por producto '
            'con produccion_pb/(oferta_total-importaciones), capado en 1.0 por '
            'identidad basico<=comprador.',
            'Y es demanda final domestica residual para cerrar oferta=demanda a '
            'precios basicos.',
            'Fuente: BCU COU 2012 detallado, hoja unica COU_C (oferta+uso+VA).',
        ],
    )
