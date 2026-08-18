"""
Esquema armonizado de demanda final (UN Handbook Cap. 2; SCN 2008 §9).

Cada fuente nacional publica la demanda final con su propia granularidad y en su
propio idioma. Este módulo colapsa esa heterogeneidad a un esquema único,
idéntico en todos los países, para que las columnas sean comparables entre sí.

Por qué el consumo va colapsado
-------------------------------
La frontera entre consumo de hogares y de gobierno NO es armonizable con las
fuentes disponibles, porque las ISFLSH caen de lados distintos:

    Argentina  hogares | gobierno                       (ISFLSH implícita)
    Brasil     famílias | ISFLSF | governo              (las tres separadas)
    Uruguay    hogares | GOBIERNO E ISFLSH              (ISFLSH con gobierno)
    México     CONSUMO PRIVADO (hogares+ISFLSH) | CG    (ISFLSH con hogares)

Uruguay no permite extraer las ISFLSH del gobierno, y México no permite
extraerlas del consumo privado. Cualquier apertura C vs. G quedaría con las
ISFLSH de un lado en unos países y del otro en otros: una comparación falsa.
El único corte limpio es el consumo final total (P.3).

Por qué la formación de capital va colapsada
--------------------------------------------
Mismo motivo, otra fuente. La MUPNI de DANE —la matriz de utilización de
productos nacionales e importados, que es el único dato de Colombia sin
supuestos de reparto— publica una sola columna de **formación bruta de capital**,
sin separar la fija (P.51) de la variación de existencias (P.52). Argentina,
Brasil, Uruguay y México sí las separan, pero el esquema armonizado es el mínimo
común denominador: si Colombia no puede partirla, la columna comparable es P.5
completa.

El detalle NO se pierde: la hoja «COU Demanda final» de cada libro conserva las
columnas nativas de su fuente, con los nombres originales. Lo que se armoniza es
la presentación comparable, no el archivo.

Invariante
----------
La suma de las columnas armonizadas es idénticamente igual a la suma de las
columnas de origen, fila por fila: es una reagrupación, no un recálculo.
Por eso `Σ Y = f` se conserva exactamente.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

# ── esquema canónico (orden de presentación) ──────────────────────────────
# clave interna -> (etiqueta para el Excel, código SCN 2008)
CANONICO: dict[str, tuple[str, str]] = {
    "consumo_final": ("Consumo final (hogares + ISFLSH + gobierno)", "P.3"),
    "formacion_bruta_capital": ("Formación bruta de capital (fija + existencias)", "P.5"),
    "exportaciones": ("Exportaciones de bienes y servicios", "P.6"),
    "discrepancia_estadistica": ("Discrepancia estadística", "—"),
}

COLUMNAS = list(CANONICO)


def etiqueta(clave: str) -> str:
    return CANONICO[clave][0]


def codigo_scn(clave: str) -> str:
    return CANONICO[clave][1]


# ── clasificador ──────────────────────────────────────────────────────────
def _norm(s: str) -> str:
    """minúsculas, sin acentos, sin puntuación ni dígitos sueltos de nota al pie."""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("_", " ")
    s = re.sub(r"[^a-z ]+", " ", s)          # cae "(1)", el "1" de 'Existencias1', "P.51b"
    return re.sub(r"\s+", " ", s).strip()


# El orden importa: la primera regla que matchea gana.
_REGLAS: list[tuple[str, tuple[str, ...]]] = [
    ("discrepancia_estadistica", ("discrepancia",)),
    ("exportaciones", ("exporta",)),
    # «trabajos en curso» son los cultivos en pie que abre INDEC: variación de
    # existencias de trabajos en curso (P.52), o sea formación bruta de capital.
    ("formacion_bruta_capital", ("capital", "existencia", "estoque", "valioso",
                                 "trabajos en curso")),
    ("consumo_final", ("consumo", "familias", "hogares", "governo", "gobierno", "isfls")),
]


def clasificar(columna: str) -> str:
    """Devuelve la clave canónica de una columna de demanda final de origen."""
    n = _norm(columna)
    for clave, patrones in _REGLAS:
        if any(p in n for p in patrones):
            return clave
    raise ValueError(
        f"columna de demanda final no reconocida: {columna!r} (normalizada: {n!r}). "
        f"Agregá un patrón en _REGLAS de src/demanda_final.py."
    )


def armonizar(Y: pd.DataFrame) -> pd.DataFrame:
    """
    Reagrupa las columnas de demanda final de origen al esquema canónico.

    Devuelve siempre las mismas columnas y en el mismo orden, rellenando con 0
    los componentes que la fuente no distingue (p. ej. la discrepancia
    estadística, que solo publica INEGI). Conserva `Y.sum(axis=1)` exactamente.
    """
    destino = {c: clasificar(c) for c in Y.columns}
    out = pd.DataFrame(0.0, index=Y.index, columns=COLUMNAS)
    for origen, clave in destino.items():
        out[clave] = out[clave] + Y[origen].astype(float)
    return out


def trazabilidad(Y: pd.DataFrame) -> list[tuple[str, str]]:
    """[(columna de origen, clave canónica)] — para documentar el mapeo en el libro."""
    return [(c, clasificar(c)) for c in Y.columns]
