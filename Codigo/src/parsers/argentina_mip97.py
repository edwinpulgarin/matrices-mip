"""
Parser de la MIPAr97 de Argentina (INDEC).

Fuente oficial:
    https://biblioteca.indec.gob.ar/bases/minde/

Archivos usados:
    mip_matriz12.xls -> Z, produccion y valor agregado
    mip_matriz13.xls -> A, coeficientes tecnicos
    mip_matriz14.xls -> L, requerimientos directos e indirectos

Unidad: miles de pesos de 1997.
"""

import numpy as np
import pandas as pd
import unicodedata
from pathlib import Path


def _leer_bloque_cuadrado(path: Path, sheet_name: str | int = 0) -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_excel(path, header=None, sheet_name=sheet_name)

    data_rows = []
    for i in range(len(df)):
        try:
            n = int(float(df.iloc[i, 0]))
        except (TypeError, ValueError):
            continue
        if 1 <= n <= 124:
            data_rows.append(i)

    labels = [str(df.iloc[i, 1]).strip() for i in data_rows]
    data_cols = list(range(2, 2 + len(data_rows)))
    bloque = df.iloc[data_rows, data_cols].copy()
    bloque = bloque.apply(pd.to_numeric, errors='coerce').fillna(0)
    bloque.index = labels
    bloque.columns = labels
    return bloque, labels


def _leer_series_desde_matriz12(path: Path, labels: list[str]) -> tuple[pd.Series, pd.Series]:
    df = pd.read_excel(path, header=None, sheet_name='Cuadro 12')

    def normalize(text: str) -> str:
        text = unicodedata.normalize('NFKD', str(text).lower())
        return ''.join(ch for ch in text if not unicodedata.combining(ch))

    def row_contains(text: str) -> int:
        text = normalize(text)
        for i in range(len(df)):
            value = ' '.join(normalize(v).strip() for v in df.iloc[i, :2].tolist())
            if text in value:
                return i
        raise ValueError(f"No se encontro la fila: {text}")

    w_row = row_contains('valor agregado bruto a precios')
    g_row = row_contains('valor bruto de la produccion a precios')

    data_cols = list(range(2, 2 + len(labels)))
    W = df.iloc[w_row, data_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    g = df.iloc[g_row, data_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
    W = pd.Series(W.values, index=labels, name='valor_agregado')
    g = pd.Series(g.values, index=labels, name='produccion_bruta')
    return g, W


def parsear(carpeta: Path, anio: int = 1997, verbose: bool = False) -> dict:
    if anio != 1997:
        raise FileNotFoundError("MIPAr97 solo esta disponible para 1997")

    carpeta = Path(carpeta)
    z_path = carpeta / 'mip_matriz12.xls'
    a_path = carpeta / 'mip_matriz13.xls'
    l_path = carpeta / 'mip_matriz14.xls'

    if not z_path.exists():
        raise FileNotFoundError(f"No se encontro: {z_path}")

    Z, labels = _leer_bloque_cuadrado(z_path, 'Cuadro 12')
    g, W = _leer_series_desde_matriz12(z_path, labels)

    if a_path.exists():
        A, _ = _leer_bloque_cuadrado(a_path, 'Cuadro 13')
        A = A.reindex(index=labels, columns=labels).fillna(0)
    else:
        g_safe = g.replace(0, np.nan)
        A = Z.divide(g_safe, axis=1).fillna(0)

    if l_path.exists():
        L, _ = _leer_bloque_cuadrado(l_path, 'Cuadro 14')
        L = L.reindex(index=labels, columns=labels).fillna(0)
    else:
        I = np.eye(len(labels))
        try:
            L_arr = np.linalg.inv(I - A.values)
        except np.linalg.LinAlgError:
            L_arr = np.linalg.pinv(I - A.values)
        L = pd.DataFrame(L_arr, index=labels, columns=labels)

    if verbose:
        print(f"  MIPAr97: {len(labels)} sectores")

    return {
        'Z'   : Z,
        'A'   : A,
        'L'   : L,
        'g'   : g,
        'W'   : W,
        'anio': 1997,
        'pais': 'argentina_mip97',
    }
