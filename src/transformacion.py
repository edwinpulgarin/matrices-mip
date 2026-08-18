"""
Transformación SUT balanceado -> IOT simétrica  (UN Handbook, Cap. 12).

Se implementan los dos modelos que NO generan elementos negativos:

    Modelo D  industria×industria, estructura fija de ventas de producto
              D = V·q̂⁻¹        (participación de mercado, ind×prod)
              Z = D · U         (ind×ind)
    Modelo B  producto×producto, supuesto de tecnología de industria
              Z = U · ĝ⁻¹ · V   (prod×prod)

Los modelos A (tecnología de producto) y C (estructura fija de ventas de
industria) se descartan porque requieren invertir una matriz de
transformación y pueden producir negativos (Cap. 12, Anexo B).

La entrada debe ser un SUT YA BALANCEADO y a precios básicos (Cap. 7 y 11);
en caso contrario los balances de la IOT resultante no cerrarán.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .sut import SUT


@dataclass
class IOT:
    """Matriz Insumo-Producto simétrica resultante.

    `modelo` distingue cómo se obtuvo Z. Además de los dos modelos del Handbook
    está "OFICIAL", para las matrices que el instituto ya publica transformadas
    (la MIP de INEGI): ahí no hay transformación nuestra que documentar, pero el
    objeto es el mismo y todo el análisis del Cap. 20 corre igual.
    """

    modelo: str                 # "D" (ind×ind) | "B" (prod×prod) | "OFICIAL" (ind×ind)
    Z: pd.DataFrame             # flujos intermedios (n × n)
    x: pd.Series                # producción bruta por sector (n,)
    f: pd.Series                # demanda final total por sector (n,)
    va: pd.Series               # valor agregado por sector (n,)
    Y: pd.DataFrame             # demanda final desagregada (n × n_fd)
    VA: pd.DataFrame            # valor agregado desagregado (n_va × n)

    # Intermedios de la transformación, guardados para que el libro los muestre.
    # Sin la matriz de participaciones no se puede auditar el salto del COU a la
    # MIP: es el único paso donde las celdas dejan de coincidir con la fuente.
    D: pd.DataFrame = None      # participaciones de mercado, ind × prod (Modelo D)
    q: pd.Series = None         # producción por producto
    # Flujo de los productos SIN producción doméstica, que el Modelo D no puede
    # ubicar en ninguna fila: se pierde de los dos lados de la identidad y por eso
    # ningún balance lo delata. 0 en las cinco fuentes al nivel que publicamos.
    fuga_sin_produccion: float = 0.0
    # Importaciones por sector. Sólo existen en la MIP TOTAL, donde el insumo
    # importado quedó DENTRO de Z: entonces la fila ya no la abastece sólo la
    # producción del sector, y sin este término el balance no cierra.
    m: pd.Series = None

    @property
    def total(self) -> bool:
        """¿Es la versión total (importado endógeno) o la doméstica?"""
        return self.m is not None

    # balances por construcción
    def balance_fila_columna(self) -> pd.Series:
        """(Σfila Z + f) − (Σcol Z + va)  por sector; 0 = cuadra.

        En la versión total se descuenta el insumo importado que entra por la
        fila: la identidad pasa a ser  x + m = Σfila Z + f.
        """
        fila = self.Z.sum(axis=1) + self.f
        if self.m is not None:
            fila = fila - self.m.reindex(self.Z.index).fillna(0.0)
        col = self.Z.sum(axis=0) + self.va
        return fila - col

    def min_valor(self) -> float:
        return float(min(self.Z.values.min(), self.va.min()))


def _diag_inv(v: pd.Series) -> np.ndarray:
    d = v.to_numpy(dtype=float).copy()
    d[d == 0] = 1.0
    return 1.0 / d


def modelo_D(sut: SUT, no_mercado: list | None = None) -> IOT:
    """Industria×industria, estructura fija de ventas de producto (Z = D·U).

    `no_mercado` excluye actividades del reparto de la demanda intermedia. Es
    doctrina del SCN: un productor de no mercado —enseñanza y salud públicas,
    servicio doméstico— no vende a otras industrias, su producción va a consumo
    final. Sin esta exclusión, cuando una actividad pública y una privada
    comparten producto, las participaciones de mercado le asignan a la pública
    una parte del uso intermedio que en realidad abastece la privada. La
    producción de esas actividades sigue estando en la oferta y en `g`; lo único
    que cambia es que no participan del reparto de `U`.
    """
    ind = sut.industrias
    q = sut.q                                   # producción por producto
    g = sut.g                                   # producción por industria

    V_mercado = sut.V
    if no_mercado:
        faltan = [a for a in no_mercado if a not in ind]
        if faltan:
            raise ValueError(f"actividades de no mercado inexistentes: {faltan}")
        V_mercado = sut.V.copy()
        V_mercado.loc[no_mercado, :] = 0.0
    # el denominador se recalcula sobre los productores de mercado, para que las
    # participaciones sigan sumando 1 y las columnas de Z queden invariantes
    q_mercado = V_mercado.sum(axis=0)
    q_mercado = q_mercado.where(q_mercado != 0, q)

    D = V_mercado.mul(pd.Series(_diag_inv(q_mercado), index=sut.productos), axis=1)  # ind×prod
    Z = pd.DataFrame(D.to_numpy() @ sut.U.to_numpy(), index=ind, columns=ind)

    # Un producto que el país NO produce —Uruguay 2012 tiene uno, íntegramente
    # importado— tiene la columna de D en cero: no hay ninguna industria a la que
    # atribuirle su fila. En una matriz industria × industria ese producto no
    # puede tener fila, y su uso intermedio tiene que salir por algún lado o la
    # columna deja de cerrar (a Uruguay 2012 lo dejaba a 7,2e-01).
    #
    # Lo que corresponde es tratarlo como lo que es: un insumo primario
    # importado sin contraparte doméstica, igual que se hace con el insumo
    # importado en la versión doméstica de la matriz. Así la columna vuelve a
    # cerrar y el dato queda a la vista en el bloque primario en vez de
    # desaparecer.
    sin_prod = q_mercado[q_mercado == 0].index
    fuga = float(sut.U.reindex(sin_prod).to_numpy().sum()
                 + sut.Y.reindex(sin_prod).to_numpy().sum()) if len(sin_prod) else 0.0
    u_sin_contraparte = (sut.U.reindex(sin_prod).sum(axis=0).reindex(ind).fillna(0.0)
                         if len(sin_prod) else None)

    # Importaciones por industria (sólo en la versión total). Se mapean con las
    # MISMAS participaciones que el resto: la fila de la MIP agrupa el producto
    # importado con el nacional del mismo tipo, así que le toca el mismo reparto.
    m = None
    if sut.M is not None:
        m = pd.Series(D.to_numpy() @ sut.M.reindex(sut.productos).fillna(0).to_numpy(),
                      index=ind, name="importaciones")

    # Demanda final por industria. Sin regla de no mercado es f = D·y, que ya
    # cierra el balance. Con la regla hay que tomarla como RESIDUO: la actividad
    # de no mercado no vende nada a otras industrias, así que toda su producción
    # va a demanda final. En la versión doméstica ese residuo es g − Σⱼ Z[i,j];
    # en la TOTAL la fila también la abastece la importación, así que el residuo
    # es g + m − Σⱼ Z[i,j]. Omitir el término `m` dejaba a Argentina 1997 sin
    # cerrar por 3,6 unidades, que es exactamente lo que aporta el cuadro 4.
    D_full = sut.V.mul(pd.Series(_diag_inv(q), index=sut.productos), axis=1)
    Y_ind = pd.DataFrame(D_full.to_numpy() @ sut.Y.reindex(sut.productos).fillna(0).to_numpy(),
                         index=ind, columns=sut.Y.columns)
    if no_mercado:
        oferta_fila = g if m is None else g + m.reindex(ind).fillna(0.0)
        f = (oferta_fila - Z.sum(axis=1)).rename("demanda_final")
        suma = Y_ind.sum(axis=1)
        escala = (f / suma.where(suma != 0, np.nan)).fillna(0.0)
        Y_ind = Y_ind.mul(escala, axis=0)
        # si una actividad no tenía demanda final repartida pero sí residuo, se
        # deja en la primera columna para no perder el total
        huerfano = f - Y_ind.sum(axis=1)
        if float(huerfano.abs().max()) > 1e-9:
            Y_ind.iloc[:, 0] = Y_ind.iloc[:, 0] + huerfano
    else:
        y_prod = sut.Y.sum(axis=1).reindex(sut.productos).fillna(0)
        f = pd.Series(D.to_numpy() @ y_prod.to_numpy(), index=ind, name="demanda_final")

    # VA por industria queda intacto (ya está en espacio de industrias)
    VA_ind = sut.VA.reindex(columns=ind).fillna(0)
    if u_sin_contraparte is not None and float(u_sin_contraparte.abs().sum()) > 0:
        VA_ind = pd.concat([
            VA_ind,
            pd.DataFrame([u_sin_contraparte.to_numpy()],
                         index=["insumo_importado_sin_contraparte"], columns=ind)])
    va = VA_ind.sum(axis=0)
    va.name = "valor_agregado"

    iot = IOT("D", Z, g.rename("produccion"), f, va, Y_ind, VA_ind,
              D=D, q=q.rename("produccion_por_producto"), m=m)
    iot.fuga_sin_produccion = fuga
    return iot


def modelo_B(sut: SUT) -> IOT:
    """Producto×producto, supuesto de tecnología de industria (Z = U·ĝ⁻¹·V)."""
    prod = sut.productos
    q = sut.q
    g = sut.g

    Ug = sut.U.mul(pd.Series(_diag_inv(g), index=sut.industrias), axis=1)  # prod×ind
    Z = pd.DataFrame(Ug.to_numpy() @ sut.V.to_numpy(), index=prod, columns=prod)

    # demanda final se mantiene en espacio de productos
    Y_prod = sut.Y.reindex(prod).fillna(0)
    f = Y_prod.sum(axis=1)
    f.name = "demanda_final"

    # VA por producto: transformar VA de industrias a productos vía market share
    # W_prod = W · ĝ⁻¹ · V  (misma transformación de tecnología de industria)
    VA_g = sut.VA.mul(pd.Series(_diag_inv(g), index=sut.industrias), axis=1)  # va×ind
    VA_prod = pd.DataFrame(VA_g.to_numpy() @ sut.V.to_numpy(),
                           index=sut.VA.index, columns=prod)
    va = VA_prod.sum(axis=0)
    va.name = "valor_agregado"

    # El Modelo B no usa participaciones de mercado, pero sí la producción por
    # producto: se guarda para que la hoja de q exista también acá.
    return IOT("B", Z, q.rename("produccion"), f, va, Y_prod, VA_prod,
               q=q.rename("produccion_por_producto"))


def desde_mip_oficial(parsed: dict, total: bool = False) -> IOT:
    """Envuelve una MIP ya publicada por el instituto en la estructura IOT.

    No transforma nada: Z, la demanda final y el bloque primario vienen medidos.
    El único armado es el DataFrame de valor agregado, que se ordena con los tres
    nombres de fila que el resto del repo espera (`consumo_intermedio_importado`,
    `impuestos_netos_productos`, `valor_agregado_bruto`) para que el libro y la
    validación no necesiten un camino aparte.
    """
    Z = parsed["Z"]
    ind = list(Z.columns)
    x = parsed["x"].reindex(ind).astype(float).rename("produccion")
    Y = parsed["Y"].reindex(ind).fillna(0.0)

    filas_va = {"impuestos_netos_productos": parsed["imptax"].reindex(ind).astype(float),
                "valor_agregado_bruto": parsed["vab"].reindex(ind).astype(float)}
    m = None
    if total:
        # INEGI publica la matriz doméstica y la importada por separado, así que
        # la total es la suma de las dos: no hay que suponer nada. El insumo
        # importado deja de ser una fila primaria de la columna y pasa a ser
        # oferta de la fila, junto con la producción.
        M = parsed["M"].reindex(index=Z.index, columns=Z.columns).fillna(0.0)
        Y_imp = parsed["Y_imp"].reindex(index=Z.index).fillna(0.0)
        Y_imp = Y_imp.reindex(columns=Y.columns).fillna(0.0)
        m = (M.sum(axis=1) + Y_imp.sum(axis=1)).rename("importaciones")
        Z = Z + M
        Y = Y + Y_imp
    else:
        filas_va = {"consumo_intermedio_importado": parsed["zm"].reindex(ind).astype(float),
                    **filas_va}

    f = Y.sum(axis=1).rename("demanda_final")
    VA = pd.DataFrame(filas_va).T
    va = VA.sum(axis=0).rename("valor_agregado")

    return IOT("OFICIAL", Z, x, f, va, Y, VA, m=m)


def transformar(sut: SUT, modelo: str = "D", no_mercado: list | None = None) -> IOT:
    modelo = modelo.upper()
    if modelo == "D":
        return modelo_D(sut, no_mercado)
    if modelo == "B":
        return modelo_B(sut)
    raise ValueError(f"Modelo no soportado: {modelo!r} (use 'D' o 'B')")
