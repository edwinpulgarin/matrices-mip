"""¿Leímos TODA la utilización que publica la fuente?

Motivación
----------
Los parsers eligen columnas por lista de palabras clave. Es robusto frente a
cambios de formato, pero tiene un modo de falla silencioso: si la fuente agrega
una columna que ningún patrón reclama, la columna se descarta **sin error** y el
producto queda con oferta pero sin uso. El balanceo (Cap. 11) cierra esa fila
igual, porque para eso está, y el resultado se ve normal: los totales cuadran,
la Leontief invierte, la validación pasa. El dato, sin embargo, salió mal.

Pasó de verdad: el INDEC abre desde 2018 una columna de demanda final «Trabajos
en curso» —los cultivos en pie, sembrados y no cosechados— que el parser de
Argentina no leía. En tabaco sin elaborar 2023 eso era el 33 % de la oferta del
producto, y el RAS lo estiraba un 50 % para cerrar la fila.

El invariante
-------------
Para cada producto, lo que la fuente declara como oferta a precios de comprador
tiene que ser igual a lo que leímos como utilización::

    OPC_p  ==  Σ_j U_pc[p,j] + Σ_c Y_pc[p,c]

Es la identidad contable del propio COU, así que no supone nada: si no se
cumple, o leímos de menos o la fuente no cierra, y las dos cosas hay que verlas
antes de publicar.

Por qué se mira el faltante NETO
--------------------------------
Una columna perdida es un faltante **de un solo signo**: falta uso en todos los
productos que la usaban. En cambio, cuando una fuente reasigna valor entre dos
productos vecinos —el BCU mueve servicios entre seguros y gastronomía— los
desvíos vienen en pares que se cancelan. Por eso el disparador es el neto y no
la suma de valores absolutos: distingue el error de lectura del ruido de
clasificación, que no es nuestro y no se arregla leyendo mejor.
"""

from __future__ import annotations

import pandas as pd

# Neto tolerado, como fracción de la oferta total. El redondeo de las fuentes
# vive en 1e-7; una columna perdida da del orden de 1e-3. 1e-4 separa las dos
# sin margen de duda.
TOL_NETO = 1e-4


class CoberturaIncompleta(RuntimeError):
    """La utilización leída no reproduce la oferta que declara la fuente."""


def verificar(parsed: dict, tol: float = TOL_NETO, estricto: bool = True) -> dict:
    """Compara la utilización leída contra la oferta declarada, producto a producto.

    Devuelve un reporte siempre; si `estricto`, además levanta
    `CoberturaIncompleta` cuando el faltante neto supera `tol`. Las fuentes que
    ya vienen a precios básicos y sin puente de valoración (Colombia, la MIP
    oficial de México) no traen `OPC`: ahí no hay nada que contrastar y el
    reporte lo dice en vez de inventar un resultado.
    """
    val = parsed.get("val")
    if val is None or "OPC" not in getattr(val, "columns", []):
        return {"aplica": False, "motivo": "la fuente no publica puente de valoración con OPC"}

    opc = val["OPC"]
    uso = (parsed["U_pc"].sum(axis=1).reindex(opc.index).fillna(0.0)
           + parsed["Y_pc"].sum(axis=1).reindex(opc.index).fillna(0.0))
    falta = opc - uso
    total = float(opc.abs().sum()) or 1.0

    neto = float(falta.sum()) / total
    bruto = float(falta.abs().sum()) / total
    # los peores en valor ABSOLUTO: en relativo mandan los productos con OPC~0
    # (comercio al por menor, donde los márgenes se netean), que no dicen nada
    peores = falta.abs().sort_values(ascending=False).head(5)
    nombres = parsed.get("prod_name", {})

    rep = {
        "aplica": True,
        "neto_rel": neto,
        "bruto_rel": bruto,
        "oferta_total": total,
        "peores": [(str(nombres.get(p, p)), float(falta[p])) for p in peores.index],
        "ok": abs(neto) <= tol,
    }
    if estricto and not rep["ok"]:
        detalle = "; ".join(f"{n[:40]}: {v:,.0f}" for n, v in rep["peores"][:3])
        raise CoberturaIncompleta(
            f"{parsed.get('pais', '?')} {parsed.get('anio', '?')}: la utilización leída "
            f"no reproduce la oferta declarada por la fuente (faltante neto "
            f"{neto:.2e} de la oferta total, tolerancia {tol:.0e}). Es la firma de una "
            f"columna del archivo que ningún patrón del parser reclamó. Peores "
            f"productos: {detalle}")
    return rep


def columnas_no_leidas(encabezados: list[str], leidas: set[str],
                       ignorar: tuple[str, ...] = ()) -> list[str]:
    """Encabezados del bloque de demanda final que ningún patrón reclamó.

    Complementa a `verificar`: esa detecta que falta valor, esta dice **qué
    columna** es. Se le pasa la lista de encabezados que el parser vio en la
    región de demanda final y el conjunto que efectivamente mapeó.
    """
    def norm(s):
        return " ".join(str(s).upper().split())

    ign = tuple(norm(x) for x in ignorar)
    return [h for h in encabezados
            if norm(h) and norm(h) not in {norm(x) for x in leidas}
            and not any(i in norm(h) for i in ign)]
