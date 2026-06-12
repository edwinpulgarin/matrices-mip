"""
Simulador de choques sobre Matrices Insumo-Producto (MIP).

Construye escenarios de impacto economico a partir de las matrices ya
publicadas y validadas (A, L, B, G, g, f, W). No reconstruye ni altera
las matrices: solo las usa como insumo, preservando trazabilidad.

Dos familias de choque:

1. Choque de demanda (modelo de cantidades de Leontief)
   Delta_x = L @ Delta_f
   Un cambio en la demanda final (Delta_f) propaga efectos hacia atras
   (backward linkages) sobre la produccion de toda la economia.

2. Choque de oferta / costos (modelo de precios de Ghosh)
   Delta_x' = Delta_v' @ G    (vector fila)
   Un cambio en los insumos primarios / valor agregado (Delta_v) propaga
   efectos hacia adelante (forward linkages).

Referencia: Miller & Blair (2009), Input-Output Analysis, caps. 2, 6, 12.

El modulo es puro (numpy/pandas), sin efectos de I/O salvo la carga
explicita de un Excel publicado mediante `cargar_mip`.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import Optional, Mapping, Union

import numpy as np
import pandas as pd


def _reparar_mojibake(texto: str) -> str:
    """
    Repara doble codificacion UTF-8 leida como latin-1 (mojibake), p.ej.
    'EdificaciÃ³n' -> 'Edificacion/Edificación'. Si la reparacion falla, deja
    el texto original. Solo se usa para comparar etiquetas, no altera la
    matriz publicada.
    """
    s = str(texto)
    try:
        reparado = s.encode("latin-1").decode("utf-8")
        # Solo aceptar si redujo marcadores tipicos de mojibake (Ã, Â, etc.)
        if ("Ã" in s or "Â" in s) and ("Ã" not in reparado and "Â" not in reparado):
            return reparado
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return s


def _norm(texto: str) -> str:
    """Normaliza para comparar: repara mojibake, minusculas y sin acentos."""
    t = _reparar_mojibake(texto)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.strip().lower()


# ---------------------------------------------------------------------------
# Carga de una matriz publicada
# ---------------------------------------------------------------------------

# Hojas estandar de los Excel publicados (ver MIP/*/MIP_*.xlsx)
_HOJA_L = "L_leontief"
_HOJA_A = "A_coef_tecnicos"
_HOJA_G = "G_ghosh_inversa"
_HOJA_B = ["B_coef_distribucion", "B_ghosh_coef"]
_HOJA_Z = "Z_MIP"
# Nombres de hoja: primero la notacion CEPAL (x, y, v); se mantienen los
# nombres antiguos (g, f, W) como respaldo para Excel generados antes.
_HOJA_G_PROD = ["x_produccion_bruta", "g_produccion"]
_HOJA_F = ["y_demanda_final", "f_demanda_final"]
_HOJA_W = ["v_valor_agregado", "W_valor_agregado"]
# Columnas de la hoja de demanda final que representan el total (no un componente).
_COLS_DEMANDA_TOTAL = ("demanda_final_total", "demanda_final", "y")


def _leer_matriz_cuadrada(path: str, hoja: str) -> pd.DataFrame:
    """Lee una hoja matricial (n x n) usando la primera columna como indice."""
    df = pd.read_excel(path, sheet_name=hoja, index_col=0)
    # La cabecera de la primera columna puede traer BOM ("﻿Descriptores").
    df.index = [str(i).strip() for i in df.index]
    df.columns = [str(c).strip() for c in df.columns]
    return df.apply(pd.to_numeric, errors="coerce").fillna(0.0)


def _leer_vector(path: str, hoja: str, cols_total: tuple = ()) -> pd.Series:
    """Lee una hoja como Serie indexada por sector.

    Si la hoja trae varias columnas (p. ej. la demanda final desglosada) y
    alguna coincide con `cols_total`, se usa esa columna como total; en otro
    caso se toma la primera columna.
    """
    df = pd.read_excel(path, sheet_name=hoja, index_col=0)
    df.index = [str(i).strip() for i in df.index]
    col = df.columns[0]
    if cols_total:
        norm = {str(c).strip().lower(): c for c in df.columns}
        for cand in cols_total:
            if cand in norm:
                col = norm[cand]
                break
    s = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    s.index = df.index
    return s


@dataclass
class MIP:
    """
    Contenedor inmutable de una matriz publicada lista para simular.

    Atributos principales:
        L : inversa de Leontief (n x n)
        G : inversa de Ghosh    (n x n)
        A : coeficientes tecnicos (n x n)
        B : coeficientes de Ghosh (n x n)
        g : produccion bruta por sector (n,)
        f : demanda final por sector (n,)
        W : valor agregado por sector (n,) — puede venir en 0 en MIP directas
        sectores : lista ordenada de etiquetas
        pais, anio, fuente : metadatos
    """

    L: pd.DataFrame
    G: pd.DataFrame
    A: pd.DataFrame
    B: pd.DataFrame
    g: pd.Series
    f: pd.Series
    W: pd.Series
    sectores: list = field(default_factory=list)
    pais: str = ""
    anio: str = ""
    fuente: str = ""

    @property
    def n(self) -> int:
        return len(self.sectores)

    def tiene_va(self) -> bool:
        """True si el vector de valor agregado trae informacion util."""
        return float(self.W.abs().sum()) > 0


def cargar_mip(path: str, pais: str = "", anio: str = "") -> MIP:
    """
    Carga una matriz publicada (.xlsx) en un objeto MIP.

    Alinea todos los vectores al orden de sectores de L para garantizar
    consistencia algebraica.
    """
    L = _leer_matriz_cuadrada(path, _HOJA_L)
    sectores = list(L.index)

    def _try_matriz(hojas):
        for h in (hojas if isinstance(hojas, (list, tuple)) else [hojas]):
            try:
                return _leer_matriz_cuadrada(path, h).reindex(index=sectores, columns=sectores).fillna(0.0)
            except Exception:
                continue
        return pd.DataFrame(0.0, index=sectores, columns=sectores)

    def _try_vector(hojas, cols_total=()):
        for h in (hojas if isinstance(hojas, (list, tuple)) else [hojas]):
            try:
                return _leer_vector(path, h, cols_total).reindex(sectores).fillna(0.0)
            except Exception:
                continue
        return pd.Series(0.0, index=sectores)

    A = _try_matriz(_HOJA_A)
    B = _try_matriz(_HOJA_B)
    G = _try_matriz(_HOJA_G)
    if float(np.abs(G.to_numpy(dtype=float)).sum()) == 0.0 and float(np.abs(B.to_numpy(dtype=float)).sum()) > 0.0:
        I = np.eye(len(sectores))
        b_values = B.to_numpy(dtype=float)
        try:
            g_values = np.linalg.inv(I - b_values)
        except np.linalg.LinAlgError:
            g_values = np.linalg.pinv(I - b_values)
        G = pd.DataFrame(g_values, index=sectores, columns=sectores)
    g = _try_vector(_HOJA_G_PROD)
    f = _try_vector(_HOJA_F, _COLS_DEMANDA_TOTAL)
    W = _try_vector(_HOJA_W)

    L = L.reindex(index=sectores, columns=sectores).fillna(0.0)

    return MIP(L=L, G=G, A=A, B=B, g=g, f=f, W=W,
               sectores=sectores, pais=pais, anio=str(anio),
               fuente=path)


# ---------------------------------------------------------------------------
# Definicion de un choque
# ---------------------------------------------------------------------------

ChoqueSpec = Mapping[str, float]


def _resolver_sector(etiqueta: str, sectores: list) -> str:
    """
    Permite especificar un sector por etiqueta exacta o por coincidencia
    parcial (case-insensitive). Lanza error si es ambiguo o no existe.
    """
    if etiqueta in sectores:
        return etiqueta
    low = _norm(etiqueta)
    coincidencias = [s for s in sectores if low in _norm(s)]
    if len(coincidencias) == 1:
        return coincidencias[0]
    if len(coincidencias) == 0:
        raise KeyError(f"Sector no encontrado: '{etiqueta}'")
    raise KeyError(
        f"Sector ambiguo '{etiqueta}'. Candidatos: {coincidencias[:5]}"
    )


def construir_delta(
    mip: MIP,
    choques: ChoqueSpec,
    base: pd.Series,
    modo: str = "pct",
) -> pd.Series:
    """
    Traduce una especificacion de choque a un vector Delta absoluto.

    choques : dict {sector: magnitud}. El sector puede ser etiqueta exacta
              o coincidencia parcial.
    base    : vector base contra el que se aplica el % (f para demanda,
              W o g para oferta).
    modo    : 'pct'  -> magnitud es variacion porcentual (10 = +10%)
              'abs'  -> magnitud es variacion absoluta en unidades monetarias
    """
    delta = pd.Series(0.0, index=mip.sectores)
    for etiqueta, valor in choques.items():
        s = _resolver_sector(etiqueta, mip.sectores)
        if modo == "pct":
            delta[s] += base.get(s, 0.0) * (valor / 100.0)
        elif modo == "abs":
            delta[s] += valor
        else:
            raise ValueError("modo debe ser 'pct' o 'abs'")
    return delta


# ---------------------------------------------------------------------------
# Resultado de un escenario
# ---------------------------------------------------------------------------

@dataclass
class ResultadoChoque:
    tipo: str                      # 'demanda' | 'oferta'
    modo: str                      # 'pct' | 'abs'
    choques: dict                  # especificacion original
    delta_input: pd.Series         # Delta_f o Delta_v aplicado
    delta_x: pd.Series             # cambio en produccion por sector
    x_base: pd.Series              # produccion base (g)
    delta_va: Optional[pd.Series] = None   # cambio en valor agregado por sector
    pais: str = ""
    anio: str = ""

    # --- agregados ---
    @property
    def impacto_total(self) -> float:
        return float(self.delta_x.sum())

    @property
    def impacto_directo(self) -> float:
        return float(self.delta_input.sum())

    @property
    def efecto_multiplicador(self) -> float:
        d = self.impacto_directo
        return float(self.impacto_total / d) if d != 0 else float("nan")

    @property
    def impacto_va_total(self) -> Optional[float]:
        return None if self.delta_va is None else float(self.delta_va.sum())

    def ranking(self, top: int = 15) -> pd.DataFrame:
        """Sectores mas afectados por |Delta_x|."""
        tabla = pd.DataFrame({
            "delta_x": self.delta_x,
            "x_base": self.x_base,
        })
        tabla["delta_x_pct"] = np.where(
            tabla["x_base"] != 0,
            100.0 * tabla["delta_x"] / tabla["x_base"],
            np.nan,
        )
        return tabla.reindex(
            self.delta_x.abs().sort_values(ascending=False).index
        ).head(top)

    def resumen(self) -> str:
        lineas = [
            f"Escenario {self.tipo.upper()} | {self.pais} {self.anio} | modo={self.modo}",
            f"  Choque directo total : {self.impacto_directo:,.2f}",
            f"  Impacto total prod.  : {self.impacto_total:,.2f}",
            f"  Efecto multiplicador : {self.efecto_multiplicador:,.4f}",
        ]
        if self.impacto_va_total is not None:
            lineas.append(f"  Impacto valor agreg. : {self.impacto_va_total:,.2f}")
        return "\n".join(lineas)


# ---------------------------------------------------------------------------
# Motores de simulacion
# ---------------------------------------------------------------------------

def choque_demanda(
    mip: MIP,
    choques: ChoqueSpec,
    modo: str = "pct",
) -> ResultadoChoque:
    """
    Choque de demanda final (modelo de cantidades de Leontief).

        Delta_x = L @ Delta_f

    Devuelve el efecto sobre la produccion de cada sector. Si la matriz
    trae valor agregado, estima el efecto sobre VA via coeficiente
    directo w = W / g aplicado a Delta_x.
    """
    delta_f = construir_delta(mip, choques, base=mip.f, modo=modo)
    delta_x = pd.Series(mip.L.values @ delta_f.values, index=mip.sectores)

    delta_va = None
    if mip.tiene_va():
        g_safe = mip.g.replace(0, np.nan)
        w = (mip.W / g_safe).fillna(0.0)          # VA directo por unidad producida
        delta_va = (w * delta_x).rename("delta_va")

    return ResultadoChoque(
        tipo="demanda", modo=modo, choques=dict(choques),
        delta_input=delta_f.rename("delta_f"),
        delta_x=delta_x.rename("delta_x"),
        x_base=mip.g.rename("x_base"),
        delta_va=delta_va,
        pais=mip.pais, anio=mip.anio,
    )


def choque_oferta(
    mip: MIP,
    choques: ChoqueSpec,
    modo: str = "pct",
) -> ResultadoChoque:
    """
    Choque de oferta / insumos primarios (modelo de precios de Ghosh).

        Delta_x' = Delta_v' @ G    (propagacion hacia adelante)

    El choque se especifica sobre el valor agregado (si existe) o, en su
    defecto, sobre la produccion bruta g como proxy del insumo primario.
    """
    base = mip.W if mip.tiene_va() else mip.g
    delta_v = construir_delta(mip, choques, base=base, modo=modo)
    delta_x = pd.Series(delta_v.values @ mip.G.values, index=mip.sectores)

    return ResultadoChoque(
        tipo="oferta", modo=modo, choques=dict(choques),
        delta_input=delta_v.rename("delta_v"),
        delta_x=delta_x.rename("delta_x"),
        x_base=mip.g.rename("x_base"),
        delta_va=None,
        pais=mip.pais, anio=mip.anio,
    )


# ---------------------------------------------------------------------------
# Exportacion trazable a Excel
# ---------------------------------------------------------------------------

def exportar_resultado(resultado: ResultadoChoque, path: str) -> str:
    """
    Escribe el resultado de un escenario en un Excel con trazabilidad:
        - escenario      : metadatos y definicion del choque
        - impacto_sector : delta por sector ordenado por magnitud
        - agregados      : totales y multiplicador
    """
    meta = pd.DataFrame({
        "campo": ["pais", "anio", "tipo_choque", "modo",
                  "choque_directo_total", "impacto_total_produccion",
                  "efecto_multiplicador", "impacto_va_total", "fuente"],
        "valor": [resultado.pais, resultado.anio, resultado.tipo, resultado.modo,
                  resultado.impacto_directo, resultado.impacto_total,
                  resultado.efecto_multiplicador,
                  resultado.impacto_va_total if resultado.impacto_va_total is not None else "n/d",
                  "Simulado sobre matriz publicada (A,L,B,G,g,f,W). No altera la MIP."],
    })

    choque_def = pd.DataFrame(
        [{"sector_especificado": k, "magnitud": v} for k, v in resultado.choques.items()]
    )

    impacto = pd.DataFrame({
        "delta_input": resultado.delta_input,
        "delta_x_produccion": resultado.delta_x,
        "x_base": resultado.x_base,
    })
    impacto["delta_x_pct_sobre_base"] = np.where(
        impacto["x_base"] != 0,
        100.0 * impacto["delta_x_produccion"] / impacto["x_base"],
        np.nan,
    )
    if resultado.delta_va is not None:
        impacto["delta_valor_agregado"] = resultado.delta_va
    impacto = impacto.reindex(
        resultado.delta_x.abs().sort_values(ascending=False).index
    )
    impacto.index.name = "sector"

    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        meta.to_excel(xw, sheet_name="escenario", index=False)
        choque_def.to_excel(xw, sheet_name="choque_definicion", index=False)
        impacto.to_excel(xw, sheet_name="impacto_sector")
    return path
