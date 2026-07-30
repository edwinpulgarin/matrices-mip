"""
Libro MIP para revisión con el equipo (UN Handbook F74 Rev.1).

Diseño: escala en millones (indicada), sin celdas vacías (ceros explícitos),
códigos de columna consistentes, índice con hipervínculos, notas de fuente en
cada hoja y trazabilidad al COU.

Pestañas: Índice, Z, Vectores, diag(g), diag(g)^-1, Balance filas, Balance
columnas, A, Validación A, Leontief, B, (Auditoría COU si es Modelo D),
Demanda final abierta, y el COU que alimenta la MIP (oferta y utilización).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as gcl

from .transformacion import IOT
from .analisis import Analisis
from .sut import SUT
from . import demanda_final as df_mod

# ── paleta y tipografía ───────────────────────────────────────────────────
FUENTE = "Calibri"
AZUL = "17375E"      # encabezados
AZUL2 = "2E75B6"     # acentos / enlaces
CLARO = "D6E4F0"     # totales
VERDE = "E2EFDA"     # ok / primarios
AMBAR = "FCE4D6"     # bloque primario
GRISCERO = "BFBFBF"  # ceros
ROJO = "F4CCCC"
TINTA = "1A1A1A"

H = Font(name=FUENTE, bold=True, color="FFFFFF", size=10)
HSUB = Font(name=FUENTE, bold=True, color=AZUL, size=11)
TIT = Font(name=FUENTE, bold=True, color=AZUL, size=14)
NOTA = Font(name=FUENTE, italic=True, color="808080", size=9)
LINKF = Font(name=FUENTE, color=AZUL2, underline="single", size=10, bold=True)
CELDA = Font(name=FUENTE, color=TINTA, size=10)
CELDAB = Font(name=FUENTE, bold=True, color=TINTA, size=10)
CERO = Font(name=FUENTE, color=GRISCERO, size=10)

FH = PatternFill("solid", fgColor=AZUL)
FTOT = PatternFill("solid", fgColor=CLARO)
FOK = PatternFill("solid", fgColor=VERDE)
FPRIM = PatternFill("solid", fgColor=AMBAR)
FBAD = PatternFill("solid", fgColor=ROJO)
_thin = Side(style="thin", color="E7E6E6")
BORDE = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)

NUM = "#,##0.0"
NUM0 = "#,##0"
COEF = "0.0000"


def _link_indice(ws):
    c = ws.cell(1, 1, "↩ Índice")
    c.font = LINKF
    c.hyperlink = "#'Índice'!A1"


def _fuente(ws, row, fuente):
    ws.cell(row, 1, f"Fuente: {fuente}. Todos los valores se derivan del COU "
                    f"(oferta y utilización); no hay datos externos.").font = NOTA


def _hcell(ws, r, c, text, center=True, wrap=False):
    cell = ws.cell(r, c, text)
    cell.font = H; cell.fill = FH
    cell.alignment = Alignment(horizontal="center" if center else "left",
                               vertical="center", wrap_text=wrap)
    return cell


def _valor(ws, r, c, v, escala=1.0, fmt=NUM, fill=None):
    """Escribe un número escalado; los ceros van en gris (no en blanco)."""
    x = float(v) / escala
    cell = ws.cell(r, c, round(x, 6))
    cell.number_format = fmt
    cell.font = CERO if abs(x) < 5e-7 else CELDA
    if fill is not None:
        cell.fill = fill
    return cell


def _matriz(ws, M: pd.DataFrame, codes: dict, names: dict, titulo, subt, fuente,
            escala=1.0, fmt=NUM):
    _link_indice(ws)
    ws.column_dimensions["A"].width = 11
    ws.column_dimensions["B"].width = 46
    ws.cell(2, 2, titulo).font = TIT
    ws.cell(3, 2, subt).font = NOTA
    hr = 5
    _hcell(ws, hr, 1, "Código", center=False)
    _hcell(ws, hr, 2, "Denominación", center=False)
    cols = list(M.columns)
    for j, k in enumerate(cols):
        cc = _hcell(ws, hr, 3 + j, codes.get(k, k))
        ws.column_dimensions[gcl(3 + j)].width = 11
    Mv = M.to_numpy()
    for i, k in enumerate(M.index):
        rr = hr + 1 + i
        a = ws.cell(rr, 1, codes.get(k, k)); a.font = CELDAB
        b = ws.cell(rr, 2, names.get(k, k)); b.font = CELDA
        for j in range(len(cols)):
            _valor(ws, rr, 3 + j, Mv[i, j], escala, fmt)
    ws.freeze_panes = ws.cell(hr + 1, 3)
    _fuente(ws, hr + 1 + len(M.index) + 1, fuente)


def _hoja_cou(ws, M: pd.DataFrame, row_codes: dict, row_names: dict, col_codes: dict,
              titulo, subt, fuente, escala):
    """Bloque del COU con etiquetas de fila y de columna distintas (V es ind×prod, U es prod×ind)."""
    _link_indice(ws)
    ws.column_dimensions["A"].width = 11
    ws.column_dimensions["B"].width = 46
    ws.cell(2, 2, titulo).font = TIT
    ws.cell(3, 2, subt).font = NOTA
    hr = 5
    _hcell(ws, hr, 1, "Código", center=False)
    _hcell(ws, hr, 2, "Denominación", center=False)
    cols = list(M.columns)
    for j, k in enumerate(cols):
        _hcell(ws, hr, 3 + j, col_codes.get(k, k))
        ws.column_dimensions[gcl(3 + j)].width = 13
    Mv = M.to_numpy()
    for i, k in enumerate(M.index):
        rr = hr + 1 + i
        ws.cell(rr, 1, row_codes.get(k, k)).font = CELDAB
        ws.cell(rr, 2, row_names.get(k, k)).font = CELDA
        for j in range(len(cols)):
            _valor(ws, rr, 3 + j, Mv[i, j], escala)
    # fila de totales por columna
    rt = hr + 1 + len(M.index)
    ws.cell(rt, 2, "Total").font = CELDAB
    for j in range(len(cols)):
        _valor(ws, rt, 3 + j, float(Mv[:, j].sum()), escala, fill=FTOT)
    ws.freeze_panes = ws.cell(hr + 1, 3)
    _fuente(ws, rt + 2, fuente)


# Puente de valoración tal como lo publica cada fuente. El orden es el del
# Handbook (Cap. 7): se parte de la producción a precios básicos y se llega a la
# oferta a precios de comprador sumando importación, impuestos y márgenes.
# Ninguna fuente trae todas las columnas: Argentina abre los márgenes en
# comercio/transporte/distribución, Brasil y Uruguay los dan combinados, y sólo
# INDEC separa el IVA de los demás impuestos a los productos.
PUENTE = [
    ("OPB",        "Producción a precios básicos"),
    ("IMPO",       "Importaciones"),
    ("Ajuste",     "Ajuste CIF/FOB"),
    ("DI",         "Derechos de importación"),
    ("IP",         "Impuestos netos sobre los productos"),
    ("IVA",        "Impuesto al valor agregado"),
    ("Comisiones", "Comisiones"),
    ("MgC",        "Márgenes de comercio"),
    ("MgT",        "Márgenes de transporte"),
    ("MgD",        "Márgenes de distribución"),
    ("Mg",         "Márgenes de comercio y transporte"),
    ("OPC",        "Oferta total a precios de comprador"),
]


def _hay(obj) -> bool:
    """¿Esta pieza del COU vino con contenido?

    Los parsers devuelven DataFrames, y `if df:` lanza ValueError en pandas. Se
    centraliza acá para no repetir el mismo tropiezo en cada punto de decisión.
    """
    if obj is None:
        return False
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return not obj.empty
    return bool(obj)


def _hoja_puente(ws, val, prod_keys, prod_codes, prod_names, subt, fuente, escala):
    """Puente de valoración por producto: de precios básicos a precios de comprador."""
    _link_indice(ws)
    ws.column_dimensions["A"].width = 11
    ws.column_dimensions["B"].width = 46
    ws.cell(2, 2, "Puente de valoración — de precios básicos a precios de comprador").font = TIT
    ws.cell(3, 2, subt).font = NOTA

    # sólo las columnas que esta fuente realmente publica con contenido
    cols = []
    for k, etiqueta in PUENTE:
        s = val.get(k)
        if s is None:
            continue
        s = s if isinstance(s, pd.Series) else pd.Series(float(s), index=prod_keys)
        s = s.reindex(prod_keys).fillna(0.0)
        if float(np.abs(s).sum()) == 0.0:
            continue
        cols.append((k, etiqueta, s))

    # "Mg" es una columna DERIVADA que los parsers agregan por conveniencia
    # (la suma de los márgenes que publique la fuente). Donde el instituto los
    # abre —Argentina— sumar ambas cosas contaría el margen dos veces.
    desagregados = {"MgC", "MgT", "MgD", "Comisiones"} & {c[0] for c in cols}
    if desagregados:
        cols = [c for c in cols if c[0] != "Mg"]

    claves = [c[0] for c in cols]
    i_opc = claves.index("OPC") if "OPC" in claves else None
    hr = 5
    _hcell(ws, hr, 1, "Código", center=False)
    _hcell(ws, hr, 2, "Producto", center=False)
    for j, (k, etiqueta, _) in enumerate(cols):
        _hcell(ws, hr, 3 + j, etiqueta, wrap=True)
        ws.column_dimensions[gcl(3 + j)].width = 17
    col_dif = 3 + len(cols)
    if i_opc is not None:
        _hcell(ws, hr, col_dif, "Diferencia (Σ componentes − oferta total)", wrap=True)
        ws.column_dimensions[gcl(col_dif)].width = 18

    peor = 0.0
    for i, k in enumerate(prod_keys):
        rr = hr + 1 + i
        ws.cell(rr, 1, prod_codes.get(k, k)).font = CELDAB
        ws.cell(rr, 2, prod_names.get(k, k)).font = CELDA
        for j, (ck, _, s) in enumerate(cols):
            # la oferta total se resalta: es la columna con la que cierra la fila
            _valor(ws, rr, 3 + j, float(s[k]), escala,
                   fill=FTOT if ck == "OPC" else None)
        if i_opc is not None:
            suma = sum(float(s[k]) for j, (_, _, s) in enumerate(cols) if j != i_opc)
            dif = suma - float(cols[i_opc][2][k])
            peor = max(peor, abs(dif))
            _valor(ws, rr, col_dif, dif, escala, fmt="0.000",
                   fill=FOK if abs(dif / escala) < 1e-6 else FBAD)
    rt = hr + 1 + len(prod_keys)
    ws.cell(rt, 2, "Total").font = CELDAB
    for j, (_, _, s) in enumerate(cols):
        _valor(ws, rt, 3 + j, float(s.sum()), escala, fill=FTOT)
    ws.freeze_panes = ws.cell(hr + 1, 3)
    ws.cell(rt + 2, 1,
            "La suma de las columnas intermedias reconstruye la oferta a precios de "
            "comprador partiendo de la producción a precios básicos. Es el dato tal "
            "como lo publica la fuente, sin ninguna transformación: la columna de "
            "diferencia muestra el residuo de redondeo del propio cuadro oficial.").font = NOTA
    _fuente(ws, rt + 4, fuente)
    return peor


def _hoja_mip(wb, Z, g, f, Yh, zm, imptax, vab, codes, names, subt, fuente, escala):
    """Tabla insumo-producto completa: Z + demanda final abierta + bloque primario + totales."""
    ws = wb.create_sheet("MIP")
    _link_indice(ws)
    ws.column_dimensions["A"].width = 11
    ws.column_dimensions["B"].width = 46
    ws.cell(2, 2, "MIP — Matriz Insumo-Producto (tabla completa)").font = TIT
    ws.cell(3, 2, subt).font = NOTA
    keys = list(Z.columns); n = len(keys)
    fdk = list(Yh.columns); nf = len(fdk)
    hr = 5
    _hcell(ws, hr, 1, "Código", center=False); _hcell(ws, hr, 2, "Denominación", center=False)
    for j, k in enumerate(keys):
        _hcell(ws, hr, 3 + j, codes.get(k, k)); ws.column_dimensions[gcl(3 + j)].width = 11
    col_di = 3 + n
    col_fd0 = col_di + 1                 # primera columna de demanda final abierta
    col_f = col_fd0 + nf                 # total de demanda final
    col_g = col_f + 1
    _hcell(ws, hr, col_di, "Demanda intermedia", wrap=True)
    for j, c in enumerate(fdk):
        _hcell(ws, hr, col_fd0 + j, df_mod.etiqueta(c), wrap=True)
        ws.cell(hr - 1, col_fd0 + j, df_mod.codigo_scn(c)).font = NOTA
        ws.column_dimensions[gcl(col_fd0 + j)].width = 17
    _hcell(ws, hr, col_f, "Demanda final (total)", wrap=True)
    _hcell(ws, hr, col_g, "Producción total", wrap=True)
    for cc in (col_di, col_f, col_g):
        ws.column_dimensions[gcl(cc)].width = 15
    Zv = Z.to_numpy(); zrow = Z.sum(axis=1)
    for i, k in enumerate(keys):
        rr = hr + 1 + i
        ws.cell(rr, 1, codes.get(k, k)).font = CELDAB
        ws.cell(rr, 2, names.get(k, k)).font = CELDA
        for j in range(n):
            _valor(ws, rr, 3 + j, Zv[i, j], escala)
        _valor(ws, rr, col_di, zrow[k], escala, fill=FTOT)
        for j, c in enumerate(fdk):
            _valor(ws, rr, col_fd0 + j, Yh.at[k, c], escala)
        _valor(ws, rr, col_f, f[k], escala, fill=FTOT)
        _valor(ws, rr, col_g, g[k], escala, fill=FTOT)
    base = hr + 1 + n
    prim = [("Consumo intermedio", Z.sum(axis=0), FTOT),
            ("Consumo intermedio importado", zm, FPRIM),
            ("Impuestos netos sobre los productos", imptax, FPRIM),
            ("Valor Agregado Bruto", vab, FPRIM),
            ("Producción total", g, FTOT)]
    for off, (label, serie, fill) in enumerate(prim):
        rr = base + off
        ws.cell(rr, 2, label).font = CELDAB
        for j, k in enumerate(keys):
            _valor(ws, rr, 3 + j, serie[k], escala, fill=fill)
    ws.freeze_panes = ws.cell(hr + 1, 3)
    _fuente(ws, base + len(prim) + 1, fuente)


def build_libro(iot: IOT, an: Analisis, ruta: str | Path, *,
                pais: str, anio: int, codes: dict, names: dict, fuente: str,
                cou_intermedio: pd.Series | None = None,
                nota_metodo: str | None = None,
                sut: SUT | None = None,
                cou_orig: dict | None = None,
                prod_codes: dict | None = None, prod_names: dict | None = None,
                escala: float = 1000.0,
                unidad: str = "millones de pesos corrientes") -> Path:
    es_D = iot.modelo == "D"
    dim_txt = "industria × industria" if es_D else "producto × producto"
    subt_base = f"{pais} {anio} · {dim_txt} · precios básicos, doméstico · {unidad}"

    Z = iot.Z
    keys = list(Z.columns)
    g = iot.x.reindex(keys)
    f = iot.f.reindex(keys)
    # Demanda final abierta. Se armoniza DESPUÉS del balanceo: el RAS opera sobre
    # [U | Y] y agregar columnas antes cambiaría el reparto. Agrupar después es
    # una reagrupación lineal pura -> Z, f, A y L quedan bit-idénticos.
    Yh = df_mod.armonizar(iot.Y).reindex(index=keys).fillna(0.0)
    prod_codes = prod_codes if prod_codes is not None else {}
    prod_names = prod_names if prod_names is not None else {}
    zm = iot.VA.loc["consumo_intermedio_importado"].reindex(keys) if "consumo_intermedio_importado" in iot.VA.index else pd.Series(0.0, index=keys)
    imptax = iot.VA.loc["impuestos_netos_productos"].reindex(keys) if "impuestos_netos_productos" in iot.VA.index else pd.Series(0.0, index=keys)
    vab = iot.VA.loc["valor_agregado_bruto"].reindex(keys) if "valor_agregado_bruto" in iot.VA.index else pd.Series(0.0, index=keys)
    W = imptax + vab
    A = an.A.reindex(index=keys, columns=keys)
    L = an.L.reindex(index=keys, columns=keys)
    gsafe = g.replace(0, np.nan)
    B = Z.div(gsafe, axis=0).fillna(0.0)
    n = len(keys)

    wb = Workbook()

    # ── 1. Índice ─────────────────────────────────────────────────────────
    ws = wb.active; ws.title = "Índice"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 74
    ws.merge_cells("B2:F2"); ws.merge_cells("B3:F3"); ws.merge_cells("B4:F4")
    ws.cell(2, 2, "MATRIZ INSUMO–PRODUCTO").font = Font(name=FUENTE, bold=True, size=24, color=AZUL)
    ws.cell(3, 2, f"{pais} · {anio} · {dim_txt}").font = Font(name=FUENTE, size=14, color=AZUL2)
    ws.cell(4, 2, f"{unidad} · precios básicos · versión doméstica (endogenous imports)").font = NOTA

    ws.cell(6, 2, "Método — Conversión de COU a MIP simétrica (UN Handbook, 2018)").font = Font(name=FUENTE, bold=True, size=11, color="FFFFFF")
    ws.cell(6, 2).fill = FH; ws.cell(6, 3).fill = FH
    pasos = ([("Paso 1 · Participaciones de mercado", "D = V · diag(q)⁻¹"),
              ("Paso 2 · Flujos intermedios (Modelo D)", "Z = D · U   (industria × industria)"),
              ("Paso 3 · Coeficientes e inversa", "A = Z · diag(g)⁻¹   ;   L = (I − A)⁻¹"),
              ("Paso 4 · Demanda final doméstica", "f = D · y_dom")]
             if es_D else
             [("Paso 1 · Participaciones de mercado", "D = V · diag(q)⁻¹"),
              ("Paso 2 · Flujos intermedios (Modelo B)", "Z = U · diag(g)⁻¹ · V   (producto × producto)"),
              ("Paso 3 · Coeficientes e inversa", "A = Z · diag(g)⁻¹   ;   L = (I − A)⁻¹"),
              ("Paso 4 · Demanda final doméstica", "f  (residual)")])
    r = 7
    for tit, formula in pasos:
        ws.cell(r, 2, tit).font = Font(name=FUENTE, bold=True, size=10, color=AZUL)
        ws.cell(r, 2).fill = FTOT
        ws.cell(r, 3, formula).font = Font(name="Consolas", size=10, color=TINTA)
        ws.cell(r, 3).fill = FTOT
        r += 1

    r += 1
    ws.cell(r, 2, "Contenido — clic para navegar").font = Font(name=FUENTE, bold=True, size=11, color="FFFFFF")
    ws.cell(r, 2).fill = PatternFill("solid", fgColor=AZUL2)
    ws.cell(r, 3).fill = PatternFill("solid", fgColor=AZUL2)
    r += 1
    toc = [("MIP", "★ Tabla insumo-producto completa (Z + demanda final + valor agregado + totales)"),
           ("2. Z", "Matriz de consumos intermedios"),
           ("3. Vectores", "g producción · f demanda final · W valor agregado · zm importado"),
           ("4. diag(g)", "Diagonal de la producción bruta"),
           ("5. diag(g)^-1", "Inversa de la diagonal"),
           ("6. Balance filas", "gᵢ = Σⱼ zᵢⱼ + fᵢ   (oferta = demanda)"),
           ("7. Balance columnas", "gⱼ = Σᵢ zᵢⱼ + zmⱼ + Wⱼ   (valor agregado)"),
           ("8. A", "Coeficientes técnicos  A = Z · diag(g)⁻¹"),
           ("9. Validación A", "aᵢⱼ ≥ 0 · aᵢⱼ ≤ 1 · Σᵢ aᵢⱼ < 1"),
           ("10. Leontief", "L = (I − A)⁻¹   y   L·f = g"),
           ("11. B", "Coeficientes de distribución  B = diag(g)⁻¹ · Z")]
    if es_D and cou_intermedio is not None:
        toc.append(("12. Auditoría COU", "Reconciliación por industria contra el COU"))
    toc.append(("13. Demanda final", "Y abierta por componente (P.3 · P.51 · P.52+P.53 · P.6) y su mapeo al COU"))
    # El COU ORIGINAL, tal como lo publica el instituto: es el punto de partida y
    # permite auditar el libro entero de punta a punta sin salir del archivo.
    # Las entradas se agregan sólo si la hoja se va a escribir: si no, el índice
    # queda con hipervínculos rotos. No toda fuente publica todas las piezas
    # —Colombia y la MIP del IBGE ya entregan precios básicos y no traen puente—.
    if cou_orig is not None:
        if _hay(cou_orig.get("V_pi")):
            toc.append(("14. COU orig · Oferta", "Producción por producto × industria, tal como la publica la fuente"))
        if _hay(cou_orig.get("val")):
            toc.append(("15. COU orig · Valoración", "Puente por producto: de precios básicos a precios de comprador"))
        if _hay(cou_orig.get("U_pc")):
            toc.append(("16. COU orig · Utilización", "Utilización intermedia a precios de comprador: producto × industria"))
        if _hay(cou_orig.get("Y_pc")) or _hay(cou_orig.get("Y_dom")):
            toc.append(("17. COU orig · Demanda final", "Demanda final con las columnas originales de la fuente"))
    # El SUT derivado: el mismo cuadro ya valorado a precios básicos, con el
    # insumo importado separado y balanceado. Es lo que entra en la MIP.
    if sut is not None:
        toc += [("18. SUT · Oferta (V)", "Oferta ya valorada y balanceada: industria × producto"),
                ("19. SUT · Utilización (U)", "Utilización doméstica a precios básicos, balanceada"),
                ("20. SUT · Demanda final", "Demanda final doméstica a precios básicos, balanceada")]
    for tab, desc in toc:
        cell = ws.cell(r, 2, tab); cell.font = LINKF
        cell.hyperlink = f"#'{tab}'!A1"
        ws.cell(r, 3, desc).font = CELDA
        r += 1
    r += 2
    if nota_metodo:
        ws.cell(r, 2, "Método").font = Font(name=FUENTE, bold=True, size=9, color=AZUL)
        ws.cell(r, 2).fill = FPRIM
        c = ws.cell(r, 3, nota_metodo)
        c.font = Font(name=FUENTE, size=9, color=TINTA); c.fill = FPRIM
        c.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 58
        r += 2

    ws.cell(r, 2, "Unidad").font = Font(name=FUENTE, bold=True, size=9, color="808080")
    ws.cell(r, 3, f"Cifras en {unidad} (salvo coeficientes A, L, B, que son adimensionales).").font = NOTA
    ws.cell(r + 1, 2, "Fuente").font = Font(name=FUENTE, bold=True, size=9, color="808080")
    ws.cell(r + 1, 3, f"{fuente}. Todo se deriva del COU; sin datos externos.").font = NOTA

    # ── MIP completa (tabla insumo-producto) ──────────────────────────────
    _hoja_mip(wb, Z, g, f, Yh, zm, imptax, vab, codes, names, subt_base, fuente, escala)

    # ── 2. Z ──────────────────────────────────────────────────────────────
    _matriz(wb.create_sheet("2. Z"), Z, codes, names,
            "Z — Matriz de consumos intermedios", subt_base, fuente, escala=escala)

    # ── 3. Vectores ───────────────────────────────────────────────────────
    ws = wb.create_sheet("3. Vectores")
    _link_indice(ws)
    ws.cell(2, 1, "Vectores de la MIP").font = TIT
    ws.cell(3, 1, subt_base).font = NOTA
    ws.column_dimensions["A"].width = 11; ws.column_dimensions["B"].width = 46
    heads = ["Código", "Denominación", "Producción bruta (g)", "Demanda final doméstica (f)",
             "Valor agregado (W)", "Consumo intermedio importado (zm)",
             "Valor Agregado Bruto", "Impuestos netos sobre los productos"]
    for j, h in enumerate(heads):
        _hcell(ws, 5, 1 + j, h, center=(j >= 2), wrap=True)
        if j >= 2:
            ws.column_dimensions[gcl(1 + j)].width = 16
    for i, k in enumerate(keys):
        rr = 6 + i
        ws.cell(rr, 1, codes.get(k, k)).font = CELDAB
        ws.cell(rr, 2, names.get(k, k)).font = CELDA
        for j, val in enumerate([g[k], f[k], W[k], zm[k], vab[k], imptax[k]]):
            _valor(ws, rr, 3 + j, val, escala)
    ws.freeze_panes = ws.cell(6, 3)
    _fuente(ws, 6 + n + 1, fuente)

    # ── 4 y 5. diag(g) y diag(g)^-1 ───────────────────────────────────────
    for hoja, titulo, serie, fmt, nota in [
        ("4. diag(g)", "diag(g) — diagonal de la producción bruta", g, NUM,
         "Matriz diagonal: estos valores en la diagonal (i = i), 0 fuera de ella."),
        ("5. diag(g)^-1", "diag(g)⁻¹ — inversa de la diagonal", (1.0 / gsafe).fillna(0.0), "0.000000000",
         "Matriz diagonal inversa: 1/gᵢ en la diagonal, 0 fuera de ella. (adimensional)")]:
        ws = wb.create_sheet(hoja)
        _link_indice(ws)
        ws.cell(2, 1, titulo).font = TIT
        ws.cell(3, 1, nota).font = NOTA
        ws.column_dimensions["A"].width = 11; ws.column_dimensions["B"].width = 46
        ws.column_dimensions["C"].width = 22
        esc = escala if hoja == "4. diag(g)" else 1.0
        _hcell(ws, 5, 1, "Código", center=False); _hcell(ws, 5, 2, "Denominación", center=False)
        _hcell(ws, 5, 3, "Valor en la diagonal")
        for i, k in enumerate(keys):
            rr = 6 + i
            ws.cell(rr, 1, codes.get(k, k)).font = CELDAB
            ws.cell(rr, 2, names.get(k, k)).font = CELDA
            _valor(ws, rr, 3, serie[k], esc, fmt, fill=FTOT)
        ws.freeze_panes = ws.cell(6, 3)
        _fuente(ws, 6 + n + 1, fuente)

    # ── 6. Balance filas ──────────────────────────────────────────────────
    ws = wb.create_sheet("6. Balance filas")
    _link_indice(ws)
    ws.cell(2, 1, "Balance oferta = demanda (filas)").font = TIT
    ws.cell(3, 1, "gᵢ = Σⱼ zᵢⱼ + fᵢ   para todo sector i   ·   " + unidad).font = NOTA
    ws.column_dimensions["A"].width = 11; ws.column_dimensions["B"].width = 46
    heads = ["Código", "Denominación", "Σⱼ zᵢⱼ ventas interm.", "fᵢ demanda final",
             "Suma", "gᵢ producción", "Diferencia"]
    for j, h in enumerate(heads):
        _hcell(ws, 5, 1 + j, h, center=(j >= 2), wrap=True)
        if j >= 2:
            ws.column_dimensions[gcl(1 + j)].width = 16
    zrow = Z.sum(axis=1)
    for i, k in enumerate(keys):
        rr = 6 + i
        suma = zrow[k] + f[k]; dif = g[k] - suma
        ws.cell(rr, 1, codes.get(k, k)).font = CELDAB
        ws.cell(rr, 2, names.get(k, k)).font = CELDA
        _valor(ws, rr, 3, zrow[k], escala); _valor(ws, rr, 4, f[k], escala)
        _valor(ws, rr, 5, suma, escala, fill=FTOT); _valor(ws, rr, 6, g[k], escala, fill=FTOT)
        _valor(ws, rr, 7, dif, escala, fmt="0.000",
               fill=FOK if abs(dif / escala) < 1e-3 else FBAD)
    ws.freeze_panes = ws.cell(6, 3)
    _fuente(ws, 6 + n + 1, fuente)

    # ── 7. Balance columnas ───────────────────────────────────────────────
    ws = wb.create_sheet("7. Balance columnas")
    _link_indice(ws)
    ws.cell(2, 1, "Balance de valor agregado (columnas)").font = TIT
    ws.cell(3, 1, "gⱼ = Σᵢ zᵢⱼ + zmⱼ + Wⱼ   para todo sector j   ·   " + unidad).font = NOTA
    ws.column_dimensions["A"].width = 11; ws.column_dimensions["B"].width = 46
    heads = ["Código", "Denominación", "Σᵢ zᵢⱼ compras interm.", "zmⱼ importado",
             "Wⱼ valor agregado", "Suma", "gⱼ producción", "Diferencia"]
    for j, h in enumerate(heads):
        _hcell(ws, 5, 1 + j, h, center=(j >= 2), wrap=True)
        if j >= 2:
            ws.column_dimensions[gcl(1 + j)].width = 15
    zcol = Z.sum(axis=0)
    for i, k in enumerate(keys):
        rr = 6 + i
        suma = zcol[k] + zm[k] + W[k]; dif = g[k] - suma
        ws.cell(rr, 1, codes.get(k, k)).font = CELDAB
        ws.cell(rr, 2, names.get(k, k)).font = CELDA
        _valor(ws, rr, 3, zcol[k], escala); _valor(ws, rr, 4, zm[k], escala); _valor(ws, rr, 5, W[k], escala)
        _valor(ws, rr, 6, suma, escala, fill=FTOT); _valor(ws, rr, 7, g[k], escala, fill=FTOT)
        _valor(ws, rr, 8, dif, escala, fmt="0.000",
               fill=FOK if abs(dif / escala) < 1e-3 else FBAD)
    ws.freeze_panes = ws.cell(6, 3)
    _fuente(ws, 6 + n + 1, fuente)

    # ── 8. A ──────────────────────────────────────────────────────────────
    _matriz(wb.create_sheet("8. A"), A, codes, names,
            "A — Coeficientes técnicos", "A = Z · diag(g)⁻¹   ·   aᵢⱼ = zᵢⱼ / gⱼ   (adimensional)",
            fuente, escala=1.0, fmt=COEF)

    # ── 9. Validación A ───────────────────────────────────────────────────
    ws = wb.create_sheet("9. Validación A")
    _link_indice(ws)
    ws.cell(2, 1, "Validación de los coeficientes técnicos").font = TIT
    ws.cell(3, 1, "Condiciones de una MIP bien construida").font = NOTA
    ws.column_dimensions["A"].width = 50
    for col in "BCD":
        ws.column_dimensions[col].width = 20
    colsum = A.sum(axis=0)
    checks = [("aᵢⱼ ≥ 0  (no negatividad)", float(A.values.min()), "≥ 0", A.values.min() >= -1e-12),
              ("aᵢⱼ ≤ 1  (ningún coeficiente absurdo)", float(A.values.max()), "≤ 1", A.values.max() <= 1 + 1e-9),
              ("Σᵢ aᵢⱼ < 1  (hay valor agregado)", float(colsum.max()), "< 1", colsum.max() < 1 - 1e-12)]
    for j, h in enumerate(["Condición", "Valor observado", "Umbral", "Resultado"]):
        _hcell(ws, 5, 1 + j, h, center=(j >= 1))
    for i, (cond, val, umb, ok) in enumerate(checks):
        rr = 6 + i
        ws.cell(rr, 1, cond).font = CELDA
        ws.cell(rr, 2, round(val, 5)).number_format = COEF
        ws.cell(rr, 3, umb).alignment = Alignment(horizontal="center")
        c = ws.cell(rr, 4, "CUMPLE ✔" if ok else "REVISAR ✗")
        c.font = CELDAB; c.fill = FOK if ok else FBAD
        c.alignment = Alignment(horizontal="center")
    ws.cell(10, 1, f"Productos/industrias con Σᵢ aᵢⱼ ≥ 1: {int((colsum >= 1).sum())}").font = NOTA
    _fuente(ws, 12, fuente)

    # ── 10. Leontief ──────────────────────────────────────────────────────
    _matriz(wb.create_sheet("10. Leontief"), L, codes, names,
            "L — Inversa de Leontief", "L = (I − A)⁻¹   (adimensional)", fuente, escala=1.0, fmt=COEF)
    ws = wb["10. Leontief"]
    Lf = pd.Series(L.to_numpy() @ f.to_numpy(), index=keys)
    base = 3 + n + 1
    for j, t in enumerate(["L·f", "g", "dif"]):
        _hcell(ws, 5, base + j, t)
        ws.column_dimensions[gcl(base + j)].width = 15
    for i, k in enumerate(keys):
        rr = 6 + i
        _valor(ws, rr, base, Lf[k], escala)
        _valor(ws, rr, base + 1, g[k], escala)
        _valor(ws, rr, base + 2, g[k] - Lf[k], escala, fmt="0.000")

    # ── 11. B ─────────────────────────────────────────────────────────────
    _matriz(wb.create_sheet("11. B"), B, codes, names,
            "B — Coeficientes de distribución", "B = diag(g)⁻¹ · Z   ·   bᵢⱼ = zᵢⱼ / gᵢ   (adimensional)",
            fuente, escala=1.0, fmt=COEF)

    # ── 12. Auditoría COU (solo Modelo D) ─────────────────────────────────
    if es_D and cou_intermedio is not None:
        ws = wb.create_sheet("12. Auditoría COU")
        _link_indice(ws)
        ws.cell(2, 1, "Auditoría — Reconciliación contra el COU").font = TIT
        ws.cell(3, 1, "Por industria: COU (util. intermedia, comprador) = Σ Z + importaciones + impuestos   ·   " + unidad).font = NOTA
        ws.column_dimensions["A"].width = 11; ws.column_dimensions["B"].width = 46
        heads = ["Código", "Denominación", "COU util. interm. (comprador)",
                 "Σ Z interm. básico dom.", "+ Importaciones", "+ Impuestos", "Suma", "Diferencia"]
        for j, h in enumerate(heads):
            _hcell(ws, 5, 1 + j, h, center=(j >= 2), wrap=True)
            if j >= 2:
                ws.column_dimensions[gcl(1 + j)].width = 15
        zc = Z.sum(axis=0)
        for i, k in enumerate(keys):
            rr = 6 + i
            cou = float(cou_intermedio.get(k, 0.0)); z = float(zc.get(k, 0.0))
            m = float(zm.get(k, 0.0)); t = float(imptax.get(k, 0.0)); suma = z + m + t
            ws.cell(rr, 1, codes.get(k, k)).font = CELDAB
            ws.cell(rr, 2, names.get(k, k)).font = CELDA
            _valor(ws, rr, 3, cou, escala)
            _valor(ws, rr, 4, z, escala); _valor(ws, rr, 5, m, escala); _valor(ws, rr, 6, t, escala)
            _valor(ws, rr, 7, suma, escala, fill=FTOT)
            _valor(ws, rr, 8, cou - suma, escala, fmt="0.000",
                   fill=FOK if abs((cou - suma) / escala) < 1e-3 else FBAD)
        ws.freeze_panes = ws.cell(6, 3)
        _fuente(ws, 6 + n + 1, fuente)

    # ── 13. Demanda final abierta ─────────────────────────────────────────
    ws = wb.create_sheet("13. Demanda final")
    _link_indice(ws)
    ws.cell(2, 1, "Demanda final por componente").font = TIT
    ws.cell(3, 1, "Y — esquema armonizado SCN 2008 · precios básicos, doméstico · " + unidad).font = NOTA
    ws.column_dimensions["A"].width = 11; ws.column_dimensions["B"].width = 46
    fdk = list(Yh.columns)
    heads = ["Código", "Denominación"] + [df_mod.etiqueta(c) for c in fdk] + ["Total (f)", "Diferencia"]
    for j, h in enumerate(heads):
        _hcell(ws, 5, 1 + j, h, center=(j >= 2), wrap=True)
        if j >= 2:
            ws.column_dimensions[gcl(1 + j)].width = 17
    for j, c in enumerate(fdk):
        ws.cell(4, 3 + j, df_mod.codigo_scn(c)).font = NOTA
    for i, k in enumerate(keys):
        rr = 6 + i
        ws.cell(rr, 1, codes.get(k, k)).font = CELDAB
        ws.cell(rr, 2, names.get(k, k)).font = CELDA
        for j, c in enumerate(fdk):
            _valor(ws, rr, 3 + j, Yh.at[k, c], escala)
        suma = float(Yh.loc[k].sum()); dif = float(f[k]) - suma
        _valor(ws, rr, 3 + len(fdk), suma, escala, fill=FTOT)
        _valor(ws, rr, 4 + len(fdk), dif, escala, fmt="0.000",
               fill=FOK if abs(dif / escala) < 1e-6 else FBAD)
    rt = 6 + n
    ws.cell(rt, 2, "Total").font = CELDAB
    for j, c in enumerate(fdk):
        _valor(ws, rt, 3 + j, float(Yh[c].sum()), escala, fill=FTOT)
    _valor(ws, rt, 3 + len(fdk), float(Yh.to_numpy().sum()), escala, fill=FTOT)
    ws.freeze_panes = ws.cell(6, 3)

    # trazabilidad: qué columnas del COU original caen en cada componente
    r = rt + 2
    ws.cell(r, 1, "Mapeo desde las columnas del COU de origen").font = HSUB
    r += 1
    _hcell(ws, r, 1, "Columna en el COU original", center=False)
    _hcell(ws, r, 2, "Componente armonizado", center=False)
    for origen, clave in df_mod.trazabilidad(iot.Y):
        r += 1
        ws.cell(r, 1, str(origen)).font = CELDA
        ws.cell(r, 2, df_mod.etiqueta(clave)).font = CELDA
    r += 2
    ws.cell(r, 1, "Dos componentes van colapsados porque no son armonizables entre países: el "
                  "consumo, porque las ISFLSH caen de lados distintos (Uruguay las agrupa con "
                  "gobierno; México, con consumo privado), y la formación de capital, porque la "
                  "MUPNI de Colombia no separa la fija de la variación de existencias. El detalle "
                  "original de esta fuente está en la hoja «17. COU orig · Demanda final». "
                  "Ver src/demanda_final.py.").font = NOTA
    _fuente(ws, r + 2, fuente)

    # ── 14-17. El COU ORIGINAL, tal como lo publica el instituto ──────────
    # Sin valorar, sin balancear y sin separar el insumo importado: es la materia
    # prima del libro. Con esto el archivo se audita entero sin abrir otra fuente.
    if cou_orig is not None:
        subt_orig = (f"{pais} {anio} · COU original de {fuente}, sin transformar · {unidad}")
        # Contrato de los parsers: V_pi y U_pc vienen ambos PRODUCTO × INDUSTRIA,
        # que es como publican el cuadro los cinco institutos. (La V del SUT
        # derivado sí es industria × producto, porque el Modelo D la usa así.)
        # En México la matriz es cuadrada —productos e industrias comparten la
        # clasificación SCIAN—, así que la orientación no se puede deducir de la
        # forma: se toma el índice de U_pc como la lista de productos.
        V_pi = cou_orig.get("V_pi")
        U_pc = cou_orig.get("U_pc")
        prod_keys = list(U_pc.index) if _hay(U_pc) else (list(V_pi.index) if _hay(V_pi) else [])
        if _hay(V_pi) and list(V_pi.index) != prod_keys and list(V_pi.columns) == prod_keys:
            V_pi = V_pi.T
        if _hay(V_pi):
            _hoja_cou(wb.create_sheet("14. COU orig · Oferta"), V_pi,
                      prod_codes, prod_names, codes,
                      "V — Cuadro de oferta original (producción a precios básicos)",
                      "Filas: productos · Columnas: industrias · " + subt_orig, fuente, escala)
        val = cou_orig.get("val")
        if _hay(val):
            _hoja_puente(wb.create_sheet("15. COU orig · Valoración"), val, prod_keys,
                         prod_codes, prod_names, subt_orig, fuente, escala)
        if _hay(U_pc):
            _hoja_cou(wb.create_sheet("16. COU orig · Utilización"), U_pc,
                      prod_codes, prod_names, codes,
                      "U — Utilización intermedia original (precios de comprador)",
                      "Filas: productos · Columnas: industrias · " + subt_orig, fuente, escala)
        # Y_pc donde la fuente publica a precios de comprador; Y_dom donde ya
        # entrega el corte doméstico a precios básicos (Colombia, MIP del IBGE).
        Y_or = cou_orig.get("Y_pc")
        etiqueta_y = "Y — Demanda final original (precios de comprador)"
        if not _hay(Y_or):
            Y_or = cou_orig.get("Y_dom")
            etiqueta_y = "Y — Demanda final original (doméstica, precios básicos)"
        if _hay(Y_or):
            _hoja_cou(wb.create_sheet("17. COU orig · Demanda final"), Y_or,
                      prod_codes, prod_names, {}, etiqueta_y,
                      "Filas: productos · Columnas: componentes tal como los publica la "
                      "fuente · " + subt_orig, fuente, escala)

    # ── 18-20. El SUT derivado que alimenta esta MIP ──────────────────────
    if sut is not None:
        subt_cou = (f"{pais} {anio} · SUT doméstico a precios básicos, balanceado "
                    f"(el que alimenta esta MIP) · {unidad}")
        _hoja_cou(wb.create_sheet("18. SUT · Oferta (V)"), sut.V,
                  codes, names, prod_codes,
                  "V — Cuadro de oferta valorado y balanceado",
                  "Filas: industrias · Columnas: productos · " + subt_cou, fuente, escala)
        _hoja_cou(wb.create_sheet("19. SUT · Utilización (U)"), sut.U,
                  prod_codes, prod_names, codes,
                  "U — Utilización intermedia doméstica, a precios básicos",
                  "Filas: productos · Columnas: industrias · " + subt_cou, fuente, escala)
        # columnas NATIVAS de la fuente: acá se conserva el detalle que el esquema
        # armonizado colapsa (FBKF vs existencias, ISFLSH vs gobierno, etc.)
        _hoja_cou(wb.create_sheet("20. SUT · Demanda final"), sut.Y,
                  prod_codes, prod_names, {},
                  "Y — Demanda final doméstica a precios básicos (columnas de la fuente)",
                  "Filas: productos · Columnas: componentes tal como los publica la fuente · "
                  + subt_cou, fuente, escala)

    ruta = Path(ruta); ruta.parent.mkdir(parents=True, exist_ok=True)
    wb.save(ruta)
    return ruta
