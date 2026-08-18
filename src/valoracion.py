"""
Valoración: utilización a precios de comprador -> SUT doméstico a precios
básicos  (UN Handbook, Cap. 7 y Cap. 8).

Los dos supuestos de reparto que aplica este módulo están transcritos
LITERALMENTE del manual en `CITAS_HANDBOOK`, más abajo, con el comentario de
cómo se lee cada párrafo contra lo que medimos. Si se va a discutir un número de
este archivo, ése es el lugar por donde empezar.

Partiendo de la utilización a precios de comprador y del puente de valoración
por producto (OPB, importaciones, ajuste CIF/FOB, derechos, impuestos a
productos, márgenes de comercio y transporte), se construye un SUT doméstico a
precios básicos en tres pasos, conservando totales por columna (usuario):

  1. Impuestos: se retiran los impuestos sobre los productos (IP+DI+IVA) de las
     celdas de uso y se acumulan en una fila primaria 'impuestos_netos_productos'.
  2. Márgenes: los márgenes de comercio y transporte incorporados al precio de
     cada bien se retiran de la fila del bien y se reasignan a las filas de los
     productos-servicio que los proveen (aquellos con margen neto negativo en la
     tabla de oferta), en la MISMA columna -> se conserva la suma por columna.
  3. Importaciones: cada fila de uso a precios básicos se separa en parte
     doméstica (proporción OPB/(OPB+IMPO+Ajuste)) e importada; la parte importada
     se acumula en una fila primaria 'consumo_intermedio_importado'.

Identidad resultante por industria j:
    g_j = Σ_p U_dom[p,j] + importado_j + impuestos_j + VAB_j
y por producto p (fila):
    OPB_p = Σ_j U_dom[p,j] + Σ demanda_final_dom[p]
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import cobertura as _cobertura
from .sut import SUT


# ─── Lo que dice el Handbook, textual ────────────────────────────────────────
# Los dos repartos que hace este módulo —márgenes e impuestos dentro de la fila,
# y el corte doméstico/importado— no son criterio nuestro: están prescritos por
# el manual. Se transcriben literalmente, en el inglés en que están publicados,
# para que quien audite no dependa de nuestra paráfrasis. Fuente:
# `SUT_IOT_HB_Final_Cover.pdf` (Series F No. 74 Rev. 1, 2018), párrafos 7.76
# (pág. impresa 226), 8.33 (258) y 8.38-8.39 (259).

CITAS_HANDBOOK = {
    "7.76": (
        "Having established a set of product-specific margin ratios, the multiplication "
        "of the trade turnover matrix could then be performed on the assumption that "
        "these product-specific margin ratios are valid in all industries trading in "
        "that product (as primary and as secondary). […] These differences must be "
        "eliminated either by proportional adjustments or, if appropriate, by more "
        "refined methods."),
    "8.33": (
        "A widely used approach in estimating import use by product across using "
        "industries and categories of final uses is the application of the import "
        "proportionality or comparability assumption. This assumes that imports are "
        "used in the same proportion across all industry intermediate inputs and final "
        "uses (except exports and allowing for imports for re-export purposes). […] "
        "For example, if imports of semi-conductors represent 50 per cent of the "
        "domestic supply of semi-conductors, then it is assumed that each industry "
        "that purchases semi-conductors purchases 50 per cent of them from foreign "
        "sources. This procedure results in the same distribution of imported products "
        "across a given row in the use table, thus providing another reason to work at "
        "the most detailed level of products available within the SUTs system, where "
        "there are likely to be fewer users of very specific products. Thus this "
        "procedure works much better with large numbers of products (for example, "
        "10,000) as opposed to, say, fewer than 100 products."),
    "8.38": (
        "It is important that the import proportionality assumption or related ratio "
        "procedures be used only after direct information about import use has been "
        "compiled. Lastly, once the proportionality assumptions have been applied, it "
        "is essential to evaluate the generalized results for reasonableness, and to "
        "adjust these percentages in the light of an understanding of how the specific "
        "economy operates with regard to production chains and purchases of products "
        "by final use."),
    "8.39": (
        "The product imbalances, and the balancing process, can often be used to "
        "correct for implausible results from an initial allocation based on "
        "proportions."),
}

# Cómo se lee cada una contra lo que hace este módulo, y contra lo que medimos:
#
# §7.76 AUTORIZA el paso 1-2. El reparto proporcional de márgenes e impuestos
#   dentro de la fila es literalmente el método del manual, no un atajo. Y es el
#   barato: contra el dato medido de INEGI 2013 da correlación 0,990 celda a
#   celda y 1,64 % de error mediano por industria.
#
# §8.33 DESCRIBE el paso 3, y su propio ejemplo es el que nos falla. El manual
#   ilustra con semiconductores al 50 %; nuestra medición contra INEGI encuentra
#   que la rama 3344 (componentes electrónicos) tiene 19,7 % de oferta doméstica
#   y que la fábrica de computadoras usa 0,0 % doméstico. El supuesto no falla en
#   los márgenes: falla en el caso que el manual eligió para explicarlo.
#
#   Y el mismo párrafo pone la condición que ninguna de nuestras fuentes cumple:
#   el procedimiento «works much better with large numbers of products (for
#   example, 10,000) as opposed to, say, fewer than 100 products». Publicamos con
#   66 productos (Colombia), 110 (Uruguay), 128 (Brasil), 195-222 (Argentina),
#   262 (México). Estamos en el régimen del que el manual advierte, y por eso el
#   sesgo medido es grande y no marginal (`reports/sesgo_prorrateo.md`).
#
# §8.38 ORDENA el orden de preferencia: el supuesto se usa «only after direct
#   information about import use has been compiled». De ahí `ensamblar_directo`,
#   y de ahí que se haya ido a buscar la matriz de importaciones en cada fuente
#   antes de prorratear. Donde hay dato, se usa el dato.
#
# §8.39 EXPLICA algo que medimos sin buscarlo: «the product imbalances, and the
#   balancing process, can often be used to correct for implausible results from
#   an initial allocation based on proportions». En 7 de los 9 libros donde el
#   RAS interviene, el SUT TOTAL entra cumpliendo las identidades y el doméstico
#   no: el desbalance lo crea el corte por origen, y el balanceo lo está
#   corrigiendo. Es exactamente el mecanismo que describe el párrafo
#   (`reports/comparacion_dom_total.md`, sección 2).


def _row_scale(df: pd.DataFrame, factor: pd.Series) -> pd.DataFrame:
    return df.mul(factor.reindex(df.index).fillna(0.0), axis=0)


# Notas de método que se estampan en la portada de cada libro, para que quien lo
# abra sepa sobre qué supuesto está parado sin tener que leer el repositorio.
NOTA_DIRECTO = (
    "SIN PRORRATEO. La fuente publica la utilización a precios básicos y el corte "
    "doméstico/importado medido celda a celda, así que no se aplica ningún supuesto de "
    "reparto: ni el del Cap. 7 (impuestos y márgenes) ni el del Cap. 8 (origen). Cada "
    "celda de esta matriz sale de una celda publicada."
)

NOTA_OFICIAL = (
    "SIN PRORRATEO. Esta MIP no la reconstruimos: es la matriz simétrica que publica el "
    "propio instituto, con la matriz doméstica y la de importaciones medidas por "
    "separado, así que no interviene ninguno de los dos supuestos de reparto (Cap. 7 "
    "impuestos y márgenes, Cap. 8 origen). Se calculan sólo A, L y B a partir de esas "
    "mismas cifras."
)

# Nota del experimento a seis dígitos de Colombia. NO se usa en la entrega: el
# libro publicado sale del COU al nivel en que el DANE lo publica (66 divisiones
# CPC × 61 actividades), porque bajar a 392 productos exige repartir la MUPNI
# —que existe sólo a 66— entre subproductos, y ese reparto no sale de ninguna
# celda publicada. Se conserva porque documenta el experimento: mide que la
# distancia contra la matriz del DANE es GRANULARIDAD y no método.
NOTA_CO_DETALLE = (
    "SIN PRORRATEO, sobre el COU de 392 productos. El DANE construye su matriz D a partir "
    "del COU a seis dígitos CPC (Anexo 1 de DSO-MIP-MET-001), y `Z = D·U` no es invariante "
    "a agregar productos, así que trabajar a dos dígitos aleja el resultado de la matriz "
    "publicada. El corte doméstico/importado y los precios básicos siguen siendo los "
    "MEDIDOS por la MUPNI, que existe sólo a 66 productos: se reparten entre los "
    "subproductos de cada grupo con la estructura del propio COU detallado, ponderada por "
    "la participación doméstica de la oferta, y se cierra la fila de cada subproducto con "
    "un ajuste biproporcional intra-grupo. Los totales por columna de la MUPNI y los "
    "totales por grupo quedan EXACTOS. Contra el Cuadro 5 del DANE el desvío baja de "
    "17,3 % a 8,7 % y la correlación sube de 0,971 a 0,997."
)

NOTA_ORIGEN_MEDIDO = (
    "PRORRATEO SÓLO EN LA VALORACIÓN. El corte doméstico/importado del consumo intermedio "
    "es MEDIDO celda a celda: el BCU publica la utilización intermedia nacional e "
    "importada por separado. Sigue prorrateado el reparto de impuestos y márgenes "
    "(Cap. 7), que la fuente sólo da por producto. El corte medido cambia la matriz que "
    "se publica, que es la doméstica: medir el origen sube el insumo importado un 20,7 % "
    "respecto de lo que daría el prorrateo del §8.33."
)

NOTA_PRORRATEO = (
    "DOS PRORRATEOS. (1) Esta fuente publica impuestos y márgenes sólo POR PRODUCTO, no "
    "celda a celda, así que se reparten proporcionalmente por fila: es el ajuste "
    "proporcional que admite el Handbook §7.76, y medido contra el dato real de INEGI "
    "2013 da correlación 0,990 celda a celda y 1,64 % de error mediano por industria. "
    "(2) Tampoco publica el corte nacional/importado por celda, así que se aplica a cada "
    "fila la proporción doméstica de la oferta de ese producto (§8.33). Éste es el caro: "
    "medido contra INEGI 2013 infla el multiplicador medio 5,65 % —hasta 58,6 % en una "
    "rama—, porque supone que todas las industrias importan en la misma proporción. "
    "Detalle en reports/sesgo_prorrateo.md."
)

NOTA_TOTAL = (
    "MIP TOTAL (nacional + importada). El insumo importado es ENDÓGENO: está dentro de "
    "la matriz, no en una fila primaria. Es la definición del Cuadro 7 del DANE. (El "
    "cuadro 12 del INDEC, en cambio, es la NACIONAL: su suma coincide exactamente con la "
    "del cuadro 3.) El multiplicador que sale de acá incluye la producción que se genera "
    "fuera del país, así que es entre 15 % y 20 % más alto que el de la versión doméstica "
    "y NO mide profundidad de cadena local. Los libros de este paquete NO usan esta "
    "definición: publican la matriz doméstica y todo lo que se deriva de ella."
)

def ensamblar_directo(parsed: dict, verbose: bool = False) -> tuple[SUT, dict]:
    """
    Arma el SUT SIN NINGÚN PRORRATEO, para fuentes que ya publican la utilización
    a precios básicos y con el corte doméstico/importado medido celda a celda.

    Es la alternativa a `valorar_argentina`, que tiene que repartir impuestos,
    márgenes e importaciones proporcionalmente por fila porque la fuente sólo los
    da por producto. Ese reparto es el «import proportionality assumption» del
    Handbook §8.33 (texto literal en `CITAS_HANDBOOK`), que el propio §8.38
    califica de recurso a usar *sólo después* de haber agotado el dato directo
    —«only after direct information about import use has been compiled»—, que es
    exactamente lo que hace esta función; medido contra el dato real de INEGI
    sobreestima el
    consumo intermedio doméstico un 15,7 % e infla los multiplicadores un 5,65 %
    en promedio (hasta +58 % en manufactura de exportación). Donde hay dato, se
    usa el dato.

    Espera en `parsed`:
        V_pi     producto × industria, producción a precios básicos
        U_dom    producto × industria, utilización DOMÉSTICA a precios básicos
        Y_dom    producto × componentes, demanda final DOMÉSTICA a precios básicos
        U_imp    producto × industria, utilización IMPORTADA a precios básicos
        imptax_j impuestos netos sobre productos por industria (opcional)
    """
    V_pi = parsed["V_pi"]
    U_dom = parsed["U_dom"]
    Y_dom = parsed["Y_dom"]
    U_imp = parsed["U_imp"]
    ind = list(U_dom.columns)

    V = V_pi.T.clip(lower=0.0)
    g = V.sum(axis=1)

    importado_j = U_imp.sum(axis=0).reindex(ind).fillna(0.0)
    if "imptax_j" in parsed:
        impuestos_j = parsed["imptax_j"].reindex(ind).fillna(0.0)
    else:
        impuestos_j = pd.Series(0.0, index=ind)
    # el VAB cierra la columna por identidad contable, sin supuestos:
    #   g_j = Σ_p U_dom[p,j] + importado_j + impuestos_j + VAB_j
    vab_j = (g.reindex(ind).fillna(0.0) - U_dom.sum(axis=0).reindex(ind).fillna(0.0)
             - importado_j - impuestos_j)

    VA = pd.concat([
        pd.DataFrame([importado_j.to_numpy()], index=["consumo_intermedio_importado"], columns=ind),
        pd.DataFrame([impuestos_j.to_numpy()], index=["impuestos_netos_productos"], columns=ind),
        pd.DataFrame([vab_j.to_numpy()], index=["valor_agregado_bruto"], columns=ind),
    ])

    sut = SUT(V=V, U=U_dom, Y=Y_dom, VA=VA, M=None,
              pais=parsed["pais"], anio=parsed["anio"], unidad=parsed["unidad"],
              valoracion="básicos",
              meta={"prod_labels": parsed.get("prod_labels", {}),
                    "ind_labels": parsed.get("ind_labels", {}),
                    "sin_prorrateo": True,
                    # la utilización importada acompaña al SUT para que el libro
                    # pueda mostrarla: es el otro lado del corte por origen, y
                    # sin ella la fila primaria 'importado' no se puede auditar.
                    "U_imp": U_imp,
                    # la demanda final importada es lo que falta para poder armar
                    # la versión total de la MIP (`SUT.a_total`)
                    "Y_imp": parsed.get("Y_imp"),
                    "U_imp_medida": True})

    rep = {
        "metodo": "directo (sin prorrateo)",
        "importado_total": float(importado_j.sum()),
        "impuestos_total": float(impuestos_j.sum()),
        "va_total": float(vab_j.sum()),
        "balance": sut.resumen_balance(),
    }
    if verbose:
        print(f"  [directo] importado {rep['importado_total']:,.0f} · "
              f"VAB {rep['va_total']:,.0f} · balanceado={rep['balance']['balanceado']}")
    return sut, rep


def valorar_argentina(parsed: dict, verbose: bool = False) -> tuple[SUT, dict]:
    """Construye el SUT doméstico a precios básicos desde el dict del parser AR."""
    # Antes de valorar nada: verificar que leímos toda la utilización que la
    # fuente publica. Si falta una columna, el balanceo la taparía y el error
    # llegaría hasta la entrega sin que nada chille. Ver src/cobertura.py.
    cob = _cobertura.verificar(parsed)

    U = parsed["U_pc"].copy()          # prod × ind (precios comprador)
    Y = parsed["Y_pc"].copy()          # prod × fd
    val = parsed["val"]                # prod × columnas de valoración
    V_pi = parsed["V_pi"]              # prod × ind (oferta pb)
    VA_ind = parsed["VA"]              # 1 × ind  (VAB pb)
    prod = U.index
    ind = U.columns

    OPB = val["OPB"]; IMPO = val["IMPO"]; Ajuste = val["Ajuste"]
    IP = val["IP"]; DI = val["DI"]; IVA = val["IVA"]; Com = val.get("Comisiones", 0.0)
    Mg = val["Mg"]; OPC = val["OPC"]

    basic = OPB + IMPO + Ajuste                       # oferta a precios básicos (dom+imp)
    tax = (IP + DI + IVA + Com)                       # cuña de impuestos y comisiones sobre productos
    pm = (basic + Mg).replace(0, np.nan)              # precio productor incl. márgenes
    opc_safe = OPC.replace(0, np.nan)

    # ── Paso 1: retirar impuestos (proporcional por fila) ────────────────
    # Los pasos 1 y 2 son el ajuste proporcional que prescribe el Handbook §7.76
    # («these differences must be eliminated either by proportional adjustments
    # or, if appropriate, by more refined methods»; texto completo en
    # CITAS_HANDBOOK). La fuente publica el puente de valoración POR PRODUCTO y
    # no celda a celda, así que el método refinado no está disponible. Es el
    # reparto barato: corr. 0,990 celda a celda contra el dato medido de INEGI.
    keep_tax = ((OPC - tax) / opc_safe).fillna(0.0)   # fracción sin impuestos
    U1 = _row_scale(U, keep_tax)
    Y1 = _row_scale(Y, keep_tax)
    impuestos_j = (U.sum(axis=0) - U1.sum(axis=0))     # por industria (fila primaria)

    # ── Paso 2: reasignar márgenes de bienes a servicios (por columna) ────
    def reasignar(mg: pd.Series, U1, Y1):
        frac = (mg.clip(lower=0) / pm).fillna(0.0)     # sólo bienes (mg>0)
        w = (-mg.clip(upper=0))                        # proveedores de margen (mg<0)
        w = (w / w.sum()) if w.sum() != 0 else w
        # margen retirado por columna (intermedio + demanda final)
        remU = _row_scale(U1, frac)
        remY = _row_scale(Y1, frac)
        U2 = U1 - remU
        Y2 = Y1 - remY
        # añadir el total retirado por columna a las filas-servicio (peso w)
        addU = np.outer(w.reindex(U1.index).fillna(0.0).to_numpy(), remU.sum(axis=0).to_numpy())
        addY = np.outer(w.reindex(Y1.index).fillna(0.0).to_numpy(), remY.sum(axis=0).to_numpy())
        U2 = U2 + pd.DataFrame(addU, index=U1.index, columns=U1.columns)
        Y2 = Y2 + pd.DataFrame(addY, index=Y1.index, columns=Y1.columns)
        return U2, Y2

    U2, Y2 = reasignar(Mg, U1, Y1)
    # ── Negativos: los de la fuente se CONSERVAN ──────────────────────────
    # Acá había un clip(lower=0) sobre las dos matrices, con el comentario de
    # que eran «negativos minúsculos». No lo son: la variación de existencias
    # puede ser negativa —es una desacumulación de stock, no un error— y el
    # INDEC la publica. En Argentina 2019 son 84 celdas y −151.936.885, el
    # 0,36 % de lo leído. Llevarlas a cero era inventar dato, y después el RAS
    # repartía la diferencia por toda la matriz sin que se viera.
    #
    # Lo único que se corrige son los negativos que CREA el paso 2, cuando el
    # margen retirado supera el valor de la celda. Ésos no están en la fuente:
    # son un artefacto del reparto proporcional, y quedan registrados en el
    # reporte para que el ajuste sea visible en vez de silencioso.
    art_U = (U2 < 0) & (U >= 0)
    art_Y = (Y2 < 0) & (Y >= 0)
    artefactos = {
        "celdas": int(art_U.to_numpy().sum() + art_Y.to_numpy().sum()),
        "monto": float(U2.where(art_U, 0.0).to_numpy().sum()
                       + Y2.where(art_Y, 0.0).to_numpy().sum()),
    }
    U2 = U2.mask(art_U, 0.0)
    Y2 = Y2.mask(art_Y, 0.0)
    negativos = {
        "celdas_fuente": int((U < 0).to_numpy().sum() + (Y < 0).to_numpy().sum()),
        "monto_fuente": float(U.where(U < 0, 0.0).to_numpy().sum()
                              + Y.where(Y < 0, 0.0).to_numpy().sum()),
        "celdas_conservadas": int((U2 < 0).to_numpy().sum() + (Y2 < 0).to_numpy().sum()),
        "monto_conservado": float(U2.where(U2 < 0, 0.0).to_numpy().sum()
                                  + Y2.where(Y2 < 0, 0.0).to_numpy().sum()),
        "artefactos_margenes": artefactos,
    }

    # ── Paso 3: separar doméstico / importado ─────────────────────────────
    # Por defecto, la proporción de la fila: el «import proportionality or
    # comparability assumption» del Handbook §8.33, transcrito en CITAS_HANDBOOK
    # junto con la condición que ninguna de nuestras fuentes cumple (el manual lo
    # quiere sobre ~10.000 productos y acá hay entre 66 y 262). Es el reparto
    # caro: +5,65 % en el multiplicador medio de México, hasta +58,6 % en una
    # rama. Si la fuente mide el corte celda a celda —Uruguay 2017— se usa el
    # dato, como pide §8.38, y el supuesto queda sólo para las celdas que la
    # fuente no cubre y para la demanda final, que ninguna fuente abre.
    dom_share = (OPB / basic.replace(0, np.nan)).fillna(0.0).clip(0, 1)
    share_celda = parsed.get("dom_share_U")
    if share_celda is not None:
        share_celda = share_celda.reindex(index=U2.index, columns=U2.columns)
        # donde no hay medición (celda vacía en la fuente) cae a la fila
        share_U = share_celda.where(share_celda.notna(),
                                    other=pd.DataFrame(
                                        np.tile(dom_share.reindex(U2.index).fillna(0.0)
                                                .to_numpy()[:, None], (1, U2.shape[1])),
                                        index=U2.index, columns=U2.columns))
        U_dom = U2 * share_U
        # Con el uso intermedio doméstico MEDIDO, la demanda final doméstica ya
        # no puede salir de la proporción de fila: la oferta doméstica que no se
        # consumió como insumo tiene que aparecer en demanda final, o la fila del
        # producto deja de cerrar. Se reparte entre las columnas de demanda final
        # respetando su composición. El factor se acota a [0,1] porque pasarse de
        # 1 implicaría demanda final importada negativa; lo que quede sin cerrar
        # después del tope lo absorbe el balanceo (Cap. 11).
        resto = (OPB - U_dom.sum(axis=1)).reindex(Y2.index).fillna(0.0)
        y_fila = Y2.sum(axis=1).replace(0, np.nan)
        Y_dom = _row_scale(Y2, (resto / y_fila).fillna(0.0).clip(0, 1))
    else:
        U_dom = _row_scale(U2, dom_share)
        Y_dom = _row_scale(Y2, dom_share)
    U_imp = U2 - U_dom                                   # el otro lado del corte
    importado_j = (U2.sum(axis=0) - U_dom.sum(axis=0))   # importado intermedio por ind

    # ── SUT canónico (ind × prod para V) ──────────────────────────────────
    # ind × prod (oferta pb). Se llevan a 0 los negativos de la matriz de
    # producción (p.ej. IBGE tiene ~4 ajustes negativos): una producción
    # negativa no tiene sentido económico y generaría negativos en la MIP.
    V = V_pi.T.clip(lower=0.0)
    VA = pd.concat([
        pd.DataFrame([importado_j.reindex(ind).fillna(0.0).to_numpy()],
                     index=["consumo_intermedio_importado"], columns=ind),
        pd.DataFrame([impuestos_j.reindex(ind).fillna(0.0).to_numpy()],
                     index=["impuestos_netos_productos"], columns=ind),
        VA_ind.reindex(columns=ind).fillna(0.0).rename(index={VA_ind.index[0]: "valor_agregado_bruto"}),
    ])

    sut = SUT(V=V, U=U_dom, Y=Y_dom, VA=VA, M=None,
              pais=parsed["pais"], anio=parsed["anio"], unidad=parsed["unidad"],
              valoracion="básicos",
              meta={"prod_labels": parsed.get("prod_labels", {}),
                    "ind_labels": parsed.get("ind_labels", {}),
                    # Cuando la fuente no mide el origen, U_imp es RESULTADO del
                    # prorrateo del paso 3 y no un dato. Se marca como tal para
                    # que el libro no la presente con la misma autoridad que la
                    # de Colombia o México.
                    "U_imp": U_imp,
                    # Para la versión total sólo hace falta la SUMA de las dos
                    # partes, y `U_dom + U_imp = U2` por construcción: o sea que
                    # la MIP total no arrastra el supuesto de origen ni siquiera
                    # acá, donde el corte es prorrateado.
                    "Y_imp": Y2 - Y_dom,
                    # Importaciones por producto TAL COMO LAS DECLARA la fuente,
                    # incluido el ajuste CIF/FOB. Es lo que la identidad de la
                    # versión total exige, y no coincide con `U_imp + Y_imp`
                    # cuando el reparto por origen topa en 0 o en 1.
                    "M_prod": (IMPO + Ajuste).reindex(U2.index).fillna(0.0),
                    "U_imp_medida": share_celda is not None})

    rep = {
        "balance": sut.resumen_balance(),
        "importado_total": float(importado_j.sum()),
        "impuestos_total": float(impuestos_j.sum()),
        "va_total": float(VA_ind.values.sum()),
        "margen_neto_residual": float(Mg.sum()),
        "origen_medido": share_celda is not None,
        "cobertura": cob,
        "negativos": negativos,
    }
    if verbose:
        b = rep["balance"]
        print(f"  [valoración AR {parsed['anio']}] "
              f"balanceado={b['balanceado']} "
              f"(max_rel prod={b['max_rel_producto']:.1e}, ind={b['max_rel_industria']:.1e})")
    return sut, rep
