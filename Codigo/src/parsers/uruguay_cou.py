"""
Parser de los Cuadros de Oferta y Utilización (COU) de Uruguay — BCU / CEPAL.

Fuente: repositorio CEPAL https://statistics.cepal.org/repository/cou-mip/
Disponible: año 2017 (único año con V + U completos en formato CEPAL).

Estructura para 2017 (archivos en data/raw/uruguay/cou_2017/):
    URY_2017_Detallada_Produccion_pb_C(1).xlsx        → V (producción a pb)
    URY_2017_Detallada_Utilizacion intermedia Total_pc_C.xlsx → U (uso intermedio total)
    URY_2017_Detallada_Oferta Importada.xlsx           → M (importaciones)

Estructura en cada archivo:
    Hoja 0: datos
      Fila 7: encabezados (Código, Denominación, nan×4, Total, A.1, A.2, ..., T.1)
      Filas 8-117: 110 productos (col 0=código, col 1=descripción, cols 7-101=actividades)
      Fila 118: TOTAL

Unidad: millones de UYU a precios corrientes (2017)
"""

import numpy as np
import pandas as pd
from pathlib import Path

from .base import COU


def _leer_matriz_cepal_ury(path: Path, hoja: int = 0) -> pd.DataFrame:
    """
    Lee una hoja de COU Uruguay formato CEPAL 2017.
    Retorna DataFrame (productos × actividades) con índice = código de producto.
    """
    df = pd.read_excel(path, header=None, sheet_name=hoja, engine='openpyxl')

    # Fila 7: encabezados de columna
    row7 = df.iloc[7].tolist()

    # Actividades: columnas con encabezado 'A.1', 'B.1', etc. (patrón X.N)
    import re
    act_cols = [j for j, v in enumerate(row7)
                if re.match(r'^[A-Z]+\.\d+$', str(v).strip())]
    act_labels = [str(row7[j]).strip() for j in act_cols]

    # Filas de productos: rows 8-117 (row 118 = TOTAL)
    prod_rows = list(range(8, 118))
    prod_codes = [
        f"{str(df.iloc[i, 0]).strip()}---{str(df.iloc[i, 1]).strip()}"
        for i in prod_rows
    ]

    # Extraer bloque de datos
    bloque = df.iloc[prod_rows, act_cols].copy()
    bloque = bloque.apply(pd.to_numeric, errors='coerce').fillna(0)
    bloque.index = prod_codes
    bloque.columns = act_labels
    return bloque


def _leer_vector_cepal_ury(path: Path, hoja: int = 0) -> pd.Series:
    """
    Lee un archivo CEPAL Uruguay que contiene un vector por producto.
    Usa la última columna con datos numéricos después de la denominación.
    """
    df = pd.read_excel(path, header=None, sheet_name=hoja, engine='openpyxl')
    row7 = df.iloc[7].tolist()
    candidate_cols = [j for j, v in enumerate(row7) if str(v).strip() not in ('', 'nan', 'None')]
    value_cols = [j for j in candidate_cols if j >= 2]
    if not value_cols:
        raise ValueError(f"No se encontró columna de valores en {path.name}")
    value_col = value_cols[-1]

    prod_rows = list(range(8, 118))
    prod_codes = [
        f"{str(df.iloc[i, 0]).strip()}---{str(df.iloc[i, 1]).strip()}"
        for i in prod_rows
    ]
    values = pd.to_numeric(df.iloc[prod_rows, value_col], errors='coerce').fillna(0)
    return pd.Series(values.values, index=prod_codes, name=str(row7[value_col]).strip())


def parsear(carpeta: Path, anio: int = 2017, verbose: bool = False) -> COU:
    """
    Lee el COU de Uruguay 2017 (CEPAL) y retorna un objeto COU.

    Parámetros
    ----------
    carpeta : Path al directorio data/raw/uruguay/
    anio    : año de la tabla (default 2017)
    """
    carpeta = Path(carpeta)
    cou_dir = carpeta / f'cou_{anio}'

    if not cou_dir.exists():
        raise FileNotFoundError(f"No se encontró el directorio: {cou_dir}")

    if verbose:
        print(f"  Leyendo COU Uruguay {anio} de {cou_dir.name}/...")

    # V: producción por industria a precios básicos
    v_files = list(cou_dir.glob('*Produccion_pb_C*.xlsx'))
    if not v_files:
        raise FileNotFoundError(f"No se encontró archivo V en {cou_dir}")
    V_raw = _leer_matriz_cepal_ury(v_files[0])
    # V_raw es (productos × actividades) → transponer a (actividades × productos)
    V = V_raw.T.copy().clip(lower=0)

    # U: consumo intermedio nacional. La MIP domestica debe excluir importados.
    # El archivo fuente está a precios comprador; se reescala por producto para
    # aproximar precios básicos usando producción pb y oferta importada.
    u_nat_files = list(cou_dir.glob('*Utilizacion intermedia Nacional_pc_C*.xlsx'))
    if not u_nat_files:
        raise FileNotFoundError(f"No se encontró archivo U nacional en {cou_dir}")
    U_nacional_pc = _leer_matriz_cepal_ury(u_nat_files[0])

    u_imp_files = list(cou_dir.glob('*Utilizacion intermedia Importada_pc_C*.xlsx'))
    U_importada_pc = _leer_matriz_cepal_ury(u_imp_files[0]) if u_imp_files else pd.DataFrame(
        0.0, index=U_nacional_pc.index, columns=U_nacional_pc.columns
    )

    # M: importaciones (opcional)
    m_files = list(cou_dir.glob('*Oferta Importada*.xlsx'))
    if m_files:
        M_sums = _leer_vector_cepal_ury(m_files[0]).rename('importaciones')
    else:
        M_sums = pd.Series(0.0, index=U_nacional_pc.index, name='importaciones')

    oferta_files = list(cou_dir.glob('*Oferta Total_pc_C*.xlsx'))
    oferta_total_pc = _leer_vector_cepal_ury(oferta_files[0]).rename('oferta_total_pc') if oferta_files else None
    marg_files = list(cou_dir.glob('*Margenes Totales_C*.xlsx'))
    margenes = _leer_vector_cepal_ury(marg_files[0]).rename('margenes') if marg_files else None
    tax_files = list(cou_dir.glob('*Impuestos Totales_C*.xlsx'))
    impuestos = _leer_vector_cepal_ury(tax_files[0]).rename('impuestos_netos') if tax_files else None

    # Alinear índices V y U
    prods_comunes = [p for p in V.columns if p in U_nacional_pc.index]
    acts_comunes  = [a for a in V.index  if a in U_nacional_pc.columns]
    V = V.loc[acts_comunes, prods_comunes]
    U_nacional_pc = U_nacional_pc.loc[prods_comunes, acts_comunes]
    U_importada_pc = U_importada_pc.reindex(index=prods_comunes, columns=acts_comunes).fillna(0)
    M_sums = M_sums.reindex(prods_comunes).fillna(0)
    if oferta_total_pc is not None:
        oferta_total_pc = oferta_total_pc.reindex(prods_comunes).fillna(0)
    if margenes is not None:
        margenes = margenes.reindex(prods_comunes).fillna(0)
    if impuestos is not None:
        impuestos = impuestos.reindex(prods_comunes).fillna(0)

    label_by_act = {}
    for act in acts_comunes:
        row = V.loc[act]
        if row.empty or row.max() <= 0:
            label_by_act[act] = f"{act} — actividad económica {act}"
            continue
        principal = str(row.idxmax()).split('---', 1)[-1]
        label_by_act[act] = f"{act} — {principal}"
    act_labels = [label_by_act[a] for a in acts_comunes]
    V.index = act_labels
    U_nacional_pc.columns = act_labels
    U_importada_pc.columns = act_labels
    acts_comunes = act_labels

    q_pb = V.sum(axis=0)
    if oferta_total_pc is not None:
        oferta_domestica_pc = (oferta_total_pc - M_sums).clip(lower=0)
        factor_pb = q_pb.div(oferta_domestica_pc.replace(0, np.nan)).fillna(1.0).clip(lower=0)
    else:
        factor_pb = pd.Series(1.0, index=prods_comunes)
    U = U_nacional_pc.mul(factor_pb, axis=0).clip(lower=0)

    # Demanda final domestica residual a precios basicos, necesaria para cerrar
    # oferta = demanda en la MIP domestica.
    Y_residual = q_pb - U.sum(axis=1)
    Y = Y_residual.to_frame('demanda_final_domestica_residual_pb')

    # W: valor agregado residual (g - CI nacional - CI importado)
    g = V.sum(axis=1)  # producción por actividad
    W_vals = g - U.sum(axis=0) - U_importada_pc.sum(axis=0)
    W = W_vals.to_frame('valor_agregado_bruto').T
    W.columns = acts_comunes

    n_act  = len(acts_comunes)
    n_prod = len(prods_comunes)
    if verbose:
        print(f"  {anio}: V={V.shape}, U={U.shape}, {n_act} act × {n_prod} prod")

    return COU(
        pais='uruguay', anio=anio, moneda='UYU', unidad='millones',
        V=V, U=U, Y=Y, W=W, M=M_sums,
        T=margenes, imp_ind=impuestos, U_importada=U_importada_pc,
        notas=[
            'U usa solo consumo intermedio nacional.',
            'U nacional se aproxima a precios basicos reescalando pc por producto con produccion_pb/(oferta_total_pc-importaciones).',
            'Y es demanda final domestica residual para cerrar oferta=demanda a precios basicos.',
        ],
    )
