# -*- coding: utf-8 -*-
"""Genera presentacion HTML y Excel piloto de reconstruccion MIP.

Los artefactos se alimentan de las matrices finales ya procesadas:

- output/matrices_insumo_producto/
- output/tablas/validacion_matematica_mip.xlsx

Uso:
    py -3 -X utf8 scripts/generar_presentacion_y_prueba_reconstruccion.py
"""

from __future__ import annotations

from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


ROOT = Path(__file__).resolve().parents[1]
VALIDACION = ROOT / "output" / "tablas" / "validacion_matematica_mip.xlsx"
MIP_ROOT = ROOT / "output" / "matrices_insumo_producto"
OUT_PRESENTACIONES = ROOT / "output" / "presentaciones"
OUT_PRUEBAS = ROOT / "output" / "pruebas"

HTML_NAME = "Presentacion_Reconstruccion_MIP_Simulador.html"
XLSX_NAME = "Prueba_Reconstruccion_MIP_Finalizadas.xlsx"


SOURCE_META = {
    "argentina": {
        "pais": "Argentina",
        "tipo": "Reconstruida",
        "fuente": "COU INDEC/CEPAL",
        "metodo": "COU a MIP industria x industria con tecnologia de industria",
        "decision": "Y fuente depurada, exclusion de UF y puente comprador-basico.",
    },
    "argentina_mip97": {
        "pais": "Argentina",
        "tipo": "Directa",
        "fuente": "MIPAr97 INDEC",
        "metodo": "MIP oficial directa",
        "decision": "Se normaliza, valida y empaqueta sin reconstruccion COU.",
    },
    "brasil_early": {
        "pais": "Brasil",
        "tipo": "Reconstruida",
        "fuente": "COU CEPAL Brasil base 2000",
        "metodo": "COU a MIP industria x industria; serie 2000-2009",
        "decision": "Alineacion por posicion, exclusion de totales y cierre menor trazable.",
    },
    "brasil": {
        "pais": "Brasil",
        "tipo": "Reconstruida",
        "fuente": "COU IBGE nivel 68",
        "metodo": "COU a MIP industria x industria; serie 2010-2021",
        "decision": "Exclusion de Total do produto y puente domestico/precios basicos.",
    },
    "mexico": {
        "pais": "Mexico",
        "tipo": "Directa",
        "fuente": "MIP CEPAL/INEGI",
        "metodo": "MIP oficial/directa publicada",
        "decision": "Se parsea, valida y empaqueta; no se reconstruye desde COU.",
    },
    "uruguay": {
        "pais": "Uruguay",
        "tipo": "Directa",
        "fuente": "MIP BCU 2016",
        "metodo": "MIP oficial directa",
        "decision": "Se aplica solo conciliacion menor por redondeo documentado.",
    },
    "uruguay_cou": {
        "pais": "Uruguay",
        "tipo": "Reconstruida",
        "fuente": "COU Uruguay 2017",
        "metodo": "COU a MIP industria x industria",
        "decision": "Se conserva alerta: no hay MIP directa 2017 y los negativos son materiales.",
    },
}


def country_file_name(source_key: str, year: int) -> tuple[str, str]:
    pais = SOURCE_META[source_key]["pais"]
    return pais, f"MIP_{pais}_{year}.xlsx"


def read_final_demand_summary(source_key: str, year: int) -> dict:
    pais, filename = country_file_name(source_key, year)
    path = MIP_ROOT / pais / filename
    if not path.exists():
        return {"negativos": np.nan, "minimo": np.nan, "tiene_ajuste": False, "archivo": ""}

    sheets = pd.ExcelFile(path).sheet_names
    f = pd.read_excel(path, sheet_name="f_demanda_final")
    value_col = [c for c in f.columns if c != f.columns[0]][0]
    values = pd.to_numeric(f[value_col], errors="coerce")
    return {
        "negativos": int((values < -1e-8).sum()),
        "minimo": float(values.min()),
        "tiene_ajuste": "ajuste_cierre" in sheets,
        "archivo": str(path.relative_to(ROOT)),
    }


def build_inventory() -> pd.DataFrame:
    validation = pd.read_excel(VALIDACION)
    rows = []
    for _, row in validation.iterrows():
        source_key = row["pais"]
        year = int(row["anio"])
        meta = SOURCE_META[source_key]
        demand = read_final_demand_summary(source_key, year)
        rows.append(
            {
                "pais": meta["pais"],
                "serie_fuente": source_key,
                "anio": year,
                "tipo_matriz": meta["tipo"],
                "fuente": meta["fuente"],
                "metodo": meta["metodo"],
                "decision_metodologica": meta["decision"],
                "n_sectores": int(row["n_sectores"]),
                "validacion_estructural": row["validacion_estructural"],
                "validacion_diagnostica": row["validacion_diagnostica"],
                "sectores_demanda_final_negativa": demand["negativos"],
                "min_demanda_final": demand["minimo"],
                "ajuste_cierre_documentado": "Si" if demand["tiene_ajuste"] else "No",
                "archivo_final": demand["archivo"],
            }
        )
    return pd.DataFrame(rows).sort_values(["pais", "anio", "serie_fuente"]).reset_index(drop=True)


def fmt_int(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


def fmt_float(value: float, digits: int = 2) -> str:
    if pd.isna(value):
        return "n.d."
    return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mini_table(rows: list[list[str]], headers: list[str]) -> str:
    head = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def generate_html(inventory: pd.DataFrame) -> Path:
    OUT_PRESENTACIONES.mkdir(parents=True, exist_ok=True)
    total = len(inventory)
    direct = int((inventory["tipo_matriz"] == "Directa").sum())
    reconstructed = int((inventory["tipo_matriz"] == "Reconstruida").sum())
    structural_ok = int((inventory["validacion_estructural"] == "OK").sum())

    by_country = (
        inventory.groupby(["pais", "tipo_matriz"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    country_rows = []
    for _, row in by_country.iterrows():
        country_rows.append(
            [
                row["pais"],
                str(int(row.get("Directa", 0))),
                str(int(row.get("Reconstruida", 0))),
                str(int(row.get("Directa", 0) + row.get("Reconstruida", 0))),
            ]
        )

    reconstructed_rows = []
    for source_key in ["argentina", "brasil_early", "brasil", "uruguay_cou"]:
        meta = SOURCE_META[source_key]
        subset = inventory[inventory["serie_fuente"] == source_key]
        reconstructed_rows.append(
            [
                meta["pais"],
                f"{int(subset['anio'].min())}-{int(subset['anio'].max())}" if len(subset) > 1 else str(int(subset["anio"].iloc[0])),
                str(len(subset)),
                str(int(subset["sectores_demanda_final_negativa"].sum())),
                meta["fuente"],
            ]
        )

    validation_rows = [
        ["cuadrada_Z_A_L", "Z, A y L tienen la misma dimension n x n.", "Bloqueante"],
        ["etiquetas_alineadas", "Filas, columnas y vectores comparten los mismos sectores.", "Bloqueante"],
        ["no_negatividad_Z_A_g", "Z, A y produccion bruta no tienen negativos relevantes.", "Bloqueante"],
        ["max_abs_A_menos_Z_sobre_g", "A coincide con Z normalizada por produccion.", "Bloqueante"],
        ["max_abs_Leontief", "(I - A)L - I cercano a cero.", "Bloqueante"],
        ["max_abs_Ghosh", "(I - B)G - I cercano a cero.", "Bloqueante"],
        ["celdas_negativas_Z", "Cuenta flujos negativos en Z.", "Diagnostico"],
        ["sectores_demanda_final_residual_negativa", "Detecta cierres de demanda final por sector.", "Diagnostico"],
        ["sectores_va_residual_negativo", "Detecta valor agregado residual negativo.", "Diagnostico"],
    ]

    slides = [
        {
            "kicker": "Matrices insumo-producto",
            "title": "Reconstruccion, validacion y simulador de choques",
            "claim": "El repositorio ya separa matrices descargadas directamente de matrices reconstruidas desde COU, con trazabilidad suficiente para explicar cada cierre.",
            "body": f"""
                <div class="hero-grid">
                  <div class="metric"><b>{fmt_int(total)}</b><span>matrices finales</span></div>
                  <div class="metric"><b>{fmt_int(reconstructed)}</b><span>reconstruidas desde COU</span></div>
                  <div class="metric"><b>{fmt_int(direct)}</b><span>descargadas directas</span></div>
                  <div class="metric"><b>{structural_ok}/{total}</b><span>validacion estructural OK</span></div>
                </div>
                <p class="note">Corte metodologico: las conciliaciones menores quedan documentadas en hojas de ajuste; Uruguay 2017 se mantiene como alerta porque el desbalance es material.</p>
            """,
        },
        {
            "kicker": "Inventario",
            "title": "Que se descargo directo y que se reconstruyo",
            "claim": "La diferencia metodologica central esta en si la fuente ya publica la MIP o si entrega COU que debemos transformar.",
            "body": mini_table(country_rows, ["Pais", "Directas", "Reconstruidas", "Total"]),
        },
        {
            "kicker": "Arquitectura",
            "title": "Del COU a una MIP auditable",
            "claim": "La reconstruccion no es un ajuste visual: es una cadena reproducible de lectura, depuracion, transformacion y validacion.",
            "body": """
              <div class="flow">
                <div><b>1. Fuente</b><span>COU o MIP oficial</span></div>
                <div><b>2. Parser</b><span>lectura por pais y anio</span></div>
                <div><b>3. Depuracion</b><span>excluir totales y alinear sectores</span></div>
                <div><b>4. Base nacional</b><span>separar importado, margenes e impuestos</span></div>
                <div><b>5. STI</b><span>D @ U produce Z industria x industria</span></div>
                <div><b>6. Validacion</b><span>A, L, Ghosh y cierres</span></div>
              </div>
            """,
        },
        {
            "kicker": "Nucleo matematico",
            "title": "La reconstruccion usa tecnologia de industria",
            "claim": "El supuesto distribuye cada producto hacia industrias segun su participacion en la oferta y luego transforma usos por producto en flujos industria x industria.",
            "body": """
              <div class="formula-grid">
                <div><code>D[i,p] = V[i,p] / q[p]</code><span>Participacion de la industria i en el producto p.</span></div>
                <div><code>B[p,j] = U[p,j] / g[j]</code><span>Insumos por producto usados por la industria j.</span></div>
                <div><code>Z = D @ U</code><span>Flujos intermedios industria x industria.</span></div>
                <div><code>A = Z @ diag(g)^-1</code><span>Coeficientes tecnicos.</span></div>
                <div><code>L = (I - A)^-1</code><span>Inversa de Leontief.</span></div>
                <div><code>f = D @ Y</code><span>Demanda final transformada a industrias.</span></div>
              </div>
            """,
        },
        {
            "kicker": "Reconstruidas",
            "title": "Cobertura final de matrices reconstruidas",
            "claim": "Argentina y Brasil quedan cerradas sin demanda final negativa; Uruguay 2017 queda como caso tecnico pendiente, no como cifra maquillada.",
            "body": mini_table(reconstructed_rows, ["Pais", "Anios", "Matrices", "Sectores negativos finales", "Fuente"]),
        },
        {
            "kicker": "Argentina",
            "title": "Correccion de lectura antes de cualquier ajuste",
            "claim": "Los negativos iniciales se explicaban por totales incluidos como componentes y por codigos no alineados; corregir la construccion resolvio el problema.",
            "body": """
              <div class="two-col">
                <ul>
                  <li>Se excluyo <code>UF</code>, que era total de utilizacion final y no categoria adicional.</li>
                  <li>Se recuperaron actividades con codigos equivalentes, como <code>1512</code> frente a <code>15120</code>.</li>
                  <li>Se conserva la demanda final fuente depurada y se convierte con factor producto.</li>
                </ul>
                <div class="result-card"><b>Resultado</b><span>2004 y 2018-2021 quedan con 0 sectores de demanda final negativa y validacion estructural OK.</span></div>
              </div>
            """,
        },
        {
            "kicker": "Brasil",
            "title": "Dos series, una regla comun de trazabilidad",
            "claim": "Brasil 2000-2009 y 2010-2021 se reconstruyen desde COU, pero con parsers distintos por estructura de fuente.",
            "body": """
              <div class="two-col">
                <ul>
                  <li>2010-2021: se excluyen <code>Total do produto</code>, <code>Demanda final</code> y <code>Demanda total</code>.</li>
                  <li>2000-2009: se alinean actividades por posicion para recuperar 51 actividades.</li>
                  <li>La conversion comprador-basico usa factores publicados por producto.</li>
                  <li>2001-2006 requirio cierre menor en un sector, trazado con RAS.</li>
                </ul>
                <div class="result-card"><b>Resultado</b><span>Brasil 2000-2021 queda con 0 sectores de demanda final negativa en los archivos finales.</span></div>
              </div>
            """,
        },
        {
            "kicker": "Uruguay",
            "title": "2016 directo; 2017 reconstruido y bajo alerta",
            "claim": "El BCU publica MIP directa para 2016; para 2017 identificamos COU detallado, pero no una MIP directa equivalente.",
            "body": """
              <div class="two-col">
                <ul>
                  <li>Uruguay 2016: MIP directa BCU, con conciliacion menor por redondeo.</li>
                  <li>Uruguay 2017: reconstruccion desde COU, sin demanda final fuente completa equivalente.</li>
                  <li>Los negativos de 2017 son materiales: Trigo y transporte de carga.</li>
                  <li>No se fuerza ajuste: queda como caso para fuente adicional o reconstruccion de Y.</li>
                </ul>
                <div class="result-card warn"><b>Decision</b><span>Mantener 2017 como alerta metodologica hasta incorporar Y fuente o confirmar limitacion oficial.</span></div>
              </div>
            """,
        },
        {
            "kicker": "Cierre menor",
            "title": "Conciliar no significa maquillar",
            "claim": "La regla solo aplica cuando el negativo es pequeno, localizado y documentable; conserva produccion y valor agregado residual.",
            "body": """
              <div class="formula-grid">
                <div><code>f_negativa -> 0</code><span>Solo si el negativo no supera umbral relativo.</span></div>
                <div><code>sum_col(Z)</code><span>Se conserva para no mover valor agregado residual.</span></div>
                <div><code>RAS(Z)</code><span>Ajusta filas y columnas con masas objetivo.</span></div>
                <div><code>A, L</code><span>Se recalculan desde la nueva Z documentada.</span></div>
              </div>
              <p class="note">Cada archivo conciliado contiene <code>ajuste_cierre</code> y <code>Z_pre_conciliacion</code>.</p>
            """,
        },
        {
            "kicker": "Validaciones",
            "title": "Pruebas matematicas que quedan en cada Excel",
            "claim": "Separamos validaciones estructurales, que habilitan el uso, de alertas diagnosticas, que orientan revision economica.",
            "body": mini_table(validation_rows, ["Prueba", "Que garantiza", "Uso"]),
        },
        {
            "kicker": "Entregable",
            "title": "Cada matriz anual es autocontenida",
            "claim": "El Excel por pais y anio permite auditar la matriz, derivar multiplicadores y revisar los cierres sin regresar al codigo.",
            "body": """
              <div class="sheet-grid">
                <span>Z_MIP</span><span>A_coef_tecnicos</span><span>L_leontief</span>
                <span>B_ghosh_coef</span><span>G_ghosh_inversa</span><span>g_produccion</span>
                <span>f_demanda_final</span><span>ajuste_intermedio</span><span>multiplicadores</span>
                <span>balances_sectoriales</span><span>validacion_resumen</span><span>val_Leontief</span>
              </div>
            """,
        },
        {
            "kicker": "Simulador",
            "title": "La siguiente capa estima choques sectoriales",
            "claim": "Con A, L y Ghosh ya calculadas, el simulador puede transformar choques de demanda u oferta en impactos de produccion.",
            "body": """
              <div class="two-col">
                <ul>
                  <li>Choque de demanda: <code>Delta g = L @ Delta f</code>.</li>
                  <li>Choque por oferta/costos: usar extension de Ghosh para propagacion hacia adelante.</li>
                  <li>Escenarios: sector, magnitud, pais, anio y tipo de choque.</li>
                  <li>Salidas: impacto bruto, multiplicadores, sectores criticos y alertas de consistencia.</li>
                </ul>
                <div class="result-card"><b>Piloto Excel</b><span>Incluye una muestra editable con formulas para probar un choque simple antes de construir la interfaz final.</span></div>
              </div>
            """,
        },
        {
            "kicker": "Siguientes pasos",
            "title": "Ruta de trabajo para robustecer la version 2",
            "claim": "La prioridad es cerrar Uruguay 2017 con una fuente de Y mas completa y formalizar el simulador con escenarios reproducibles.",
            "body": """
              <div class="steps">
                <div><b>1</b><span>Extraer demanda final completa del COU 2017 o confirmar ausencia de fuente.</span></div>
                <div><b>2</b><span>Versionar matrices directas y reconstruidas con metodologia separada.</span></div>
                <div><b>3</b><span>Convertir el piloto de choque en simulador con seleccion pais-anio-sector.</span></div>
                <div><b>4</b><span>Agregar comparaciones historicas y sensibilidad por tipo de cierre.</span></div>
              </div>
            """,
        },
    ]

    slides_html = []
    for i, slide in enumerate(slides, start=1):
        slides_html.append(
            f"""
            <section class="slide" id="s{i:02d}">
              <div class="slide-num">{i:02d}</div>
              <p class="kicker">{escape(slide['kicker'])}</p>
              <h1>{escape(slide['title'])}</h1>
              <p class="claim">{escape(slide['claim'])}</p>
              <div class="body">{slide['body']}</div>
            </section>
            """
        )

    nav = "".join(f"<a href=\"#s{i:02d}\">{i:02d}</a>" for i in range(1, len(slides) + 1))
    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reconstruccion MIP y simulador</title>
<style>
:root {{
  --ink:#172033; --muted:#667085; --paper:#fbfcff; --line:#d9e2ef;
  --blue:#1557a6; --teal:#0f8b8d; --green:#2f9e44; --amber:#c47f17;
  --red:#b42318; --lilac:#6654c7; --soft:#eef4fb; --soft2:#f6efe5;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{
  margin:0; background:#e8edf5; color:var(--ink);
  font-family:Segoe UI, Arial, sans-serif; line-height:1.45;
}}
nav {{
  position:fixed; top:0; left:0; right:0; z-index:10;
  height:48px; display:flex; align-items:center; gap:6px;
  padding:0 18px; background:#101828; color:white; box-shadow:0 8px 24px rgba(16,24,40,.18);
}}
nav b {{ margin-right:12px; font-size:13px; letter-spacing:.04em; }}
nav a {{ color:#d0d5dd; text-decoration:none; font-size:12px; padding:4px 7px; border-radius:5px; }}
nav a:hover {{ background:#344054; color:white; }}
main {{ padding:72px 0 48px; }}
.slide {{
  width:min(1180px, calc(100vw - 44px)); min-height:680px; margin:0 auto 26px;
  background:var(--paper); border:1px solid var(--line); border-radius:8px;
  padding:46px 54px; position:relative; overflow:hidden; box-shadow:0 16px 40px rgba(16,24,40,.14);
}}
.slide:before {{
  content:""; position:absolute; inset:0 auto 0 0; width:10px;
  background:linear-gradient(180deg,var(--blue),var(--teal) 55%,var(--amber));
}}
.slide-num {{ position:absolute; right:32px; top:26px; color:#98a2b3; font-weight:800; }}
.kicker {{ color:var(--teal); font-size:13px; text-transform:uppercase; letter-spacing:.12em; font-weight:800; }}
h1 {{ font-size:42px; line-height:1.08; margin:8px 0 14px; max-width:900px; letter-spacing:0; }}
.claim {{ font-size:21px; max-width:930px; color:#344054; margin:0 0 30px; }}
.body {{ font-size:16px; }}
.note {{ color:var(--muted); margin-top:22px; max-width:880px; }}
.hero-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-top:34px; }}
.metric {{ background:var(--soft); border:1px solid var(--line); border-radius:8px; padding:22px; min-height:126px; }}
.metric b {{ display:block; font-size:40px; color:var(--blue); line-height:1; }}
.metric span {{ display:block; margin-top:10px; color:#344054; font-weight:650; }}
table {{ width:100%; border-collapse:collapse; background:white; border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
th {{ background:#173b73; color:white; text-align:left; padding:12px; font-size:13px; }}
td {{ padding:12px; border-top:1px solid var(--line); vertical-align:top; }}
tr:nth-child(even) td {{ background:#f8fafc; }}
.flow {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:28px; }}
.flow div, .formula-grid div, .steps div, .result-card {{
  background:white; border:1px solid var(--line); border-radius:8px; padding:18px;
}}
.flow b, .steps b {{ display:block; color:var(--blue); margin-bottom:6px; }}
.flow span, .formula-grid span, .steps span, .result-card span {{ color:#475467; display:block; }}
.formula-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:24px; }}
code {{ background:#f2f4f7; border:1px solid #e4e7ec; padding:2px 5px; border-radius:5px; font-family:Cascadia Code, Consolas, monospace; }}
.two-col {{ display:grid; grid-template-columns:1.25fr .75fr; gap:24px; align-items:start; }}
ul {{ margin:0; padding-left:22px; }}
li {{ margin:0 0 12px; }}
.result-card b {{ display:block; color:var(--green); font-size:28px; margin-bottom:10px; }}
.result-card.warn b {{ color:var(--red); }}
.sheet-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }}
.sheet-grid span {{ padding:14px; border:1px solid var(--line); border-radius:8px; background:#fff; font-weight:750; color:#173b73; }}
.steps {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-top:24px; }}
@media (max-width:900px) {{
  nav {{ overflow-x:auto; }}
  .slide {{ width:calc(100vw - 20px); padding:34px 24px; min-height:auto; }}
  h1 {{ font-size:30px; }}
  .claim {{ font-size:18px; }}
  .hero-grid, .flow, .formula-grid, .steps, .sheet-grid, .two-col {{ grid-template-columns:1fr; }}
}}
@media print {{
  nav {{ display:none; }}
  main {{ padding:0; }}
  .slide {{ page-break-after:always; width:100%; min-height:100vh; margin:0; box-shadow:none; border-radius:0; }}
}}
</style>
</head>
<body>
<nav><b>MIP V2</b>{nav}</nav>
<main>
{''.join(slides_html)}
</main>
<script>
document.addEventListener('keydown', (event) => {{
  const ids = [...document.querySelectorAll('.slide')].map(s => s.id);
  const current = ids.findIndex(id => {{
    const rect = document.getElementById(id).getBoundingClientRect();
    return rect.top >= -80 && rect.top < window.innerHeight / 2;
  }});
  if (event.key === 'ArrowRight' || event.key === 'PageDown') {{
    const next = Math.min(ids.length - 1, Math.max(0, current) + 1);
    document.getElementById(ids[next]).scrollIntoView();
  }}
  if (event.key === 'ArrowLeft' || event.key === 'PageUp') {{
    const prev = Math.max(0, Math.max(0, current) - 1);
    document.getElementById(ids[prev]).scrollIntoView();
  }}
}});
</script>
</body>
</html>
"""
    out_path = OUT_PRESENTACIONES / HTML_NAME
    out_path.write_text(html, encoding="utf-8")
    (ROOT / HTML_NAME).write_text(html, encoding="utf-8")
    return out_path


def sheet_title(ws, title: str, subtitle: str | None = None) -> None:
    ws["A1"] = title
    ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor="173B73")
    ws["A1"].alignment = Alignment(vertical="center")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
    ws.row_dimensions[1].height = 30
    if subtitle:
        ws["A2"] = subtitle
        ws["A2"].font = Font(size=10, color="475467")
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=8)


def append_table(ws, start_row: int, headers: list[str], rows: list[list], style: dict) -> int:
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(start_row, col, header)
        cell.fill = style["header_fill"]
        cell.font = style["header_font"]
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = style["border"]
    for r, row in enumerate(rows, start=start_row + 1):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(r, c, value)
            cell.border = style["border"]
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cell.number_format = "#,##0.00"
        if (r - start_row) % 2 == 0:
            for c in range(1, len(headers) + 1):
                ws.cell(r, c).fill = style["alt_fill"]
    ws.auto_filter.ref = f"A{start_row}:{get_column_letter(len(headers))}{start_row + len(rows)}"
    return start_row + len(rows) + 2


def style_sheet(ws, widths: dict[int, int] | None = None) -> None:
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"
    if widths:
        for col, width in widths.items():
            ws.column_dimensions[get_column_letter(col)].width = width
    else:
        for col in range(1, min(ws.max_column, 12) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 18


def load_package_sheet(country: str, year: int, sheet_name: str) -> pd.DataFrame:
    path = MIP_ROOT / country / f"MIP_{country}_{year}.xlsx"
    return pd.read_excel(path, sheet_name=sheet_name, index_col=0)


def sample_matrix(country: str, year: int, n: int = 8) -> dict:
    z = load_package_sheet(country, year, "Z_MIP")
    l = load_package_sheet(country, year, "L_leontief")
    g = load_package_sheet(country, year, "g_produccion").iloc[:, 0]
    f = load_package_sheet(country, year, "f_demanda_final").iloc[:, 0]
    sectors = list(g.sort_values(ascending=False).head(n).index)
    return {
        "sectors": sectors,
        "Z": z.loc[sectors, sectors],
        "L": l.loc[sectors, sectors],
        "g": g.loc[sectors],
        "f": f.loc[sectors],
    }


def generate_workbook(inventory: pd.DataFrame) -> Path:
    OUT_PRUEBAS.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    default = wb.active
    wb.remove(default)

    thin = Side(style="thin", color="D9E2EC")
    style = {
        "border": Border(left=thin, right=thin, top=thin, bottom=thin),
        "header_fill": PatternFill("solid", fgColor="173B73"),
        "header_font": Font(bold=True, color="FFFFFF", size=10),
        "alt_fill": PatternFill("solid", fgColor="F8FAFC"),
    }

    # README
    ws = wb.create_sheet("README")
    sheet_title(ws, "Prueba de reconstruccion MIP finalizadas", "Workbook piloto para explicar matrices reconstruidas, cierres y simulador de choques.")
    readme_rows = [
        ["Objetivo", "Mostrar, con datos del paquete final, como se separan matrices directas y reconstruidas."],
        ["Reconstruidas", "Argentina 2004/2018-2021, Brasil 2000-2021 y Uruguay 2017."],
        ["Directas", "Argentina 1997, Mexico 2003/2008/2013/2018 y Uruguay 2016."],
        ["Trazabilidad", "Los cierres menores quedan en ajuste_cierre y Z_pre_conciliacion cuando aplican."],
        ["Simulador", "La hoja Simulador_piloto muestra un choque de demanda con Delta g = L @ Delta f."],
    ]
    append_table(ws, 4, ["Campo", "Descripcion"], readme_rows, style)
    style_sheet(ws, {1: 24, 2: 105})

    # Inventario
    ws = wb.create_sheet("Inventario")
    sheet_title(ws, "Inventario de matrices finales", "Separacion de matrices directas y reconstruidas, con estado de validacion y demanda final negativa.")
    inv_headers = list(inventory.columns)
    inv_rows = inventory.replace({np.nan: ""}).values.tolist()
    append_table(ws, 4, inv_headers, inv_rows, style)
    style_sheet(ws, {1: 14, 2: 17, 3: 10, 4: 15, 5: 28, 6: 34, 7: 48, 8: 12, 9: 18, 10: 18, 11: 18, 12: 18, 13: 18, 14: 46})

    # Paso a paso
    ws = wb.create_sheet("Paso_a_paso")
    sheet_title(ws, "Paso a paso de reconstruccion", "Ruta metodologica para matrices que no se descargaron directamente como MIP.")
    steps = [
        [1, "Lectura de fuente", "Se cargan V, U, Y, W, importaciones y puentes de valoracion cuando existen.", "parser por pais"],
        [2, "Depuracion", "Se excluyen columnas totales que no son sectores ni componentes de demanda final.", "Argentina UF; Brasil Total do produto"],
        [3, "Alineacion", "Se alinean codigos, acentos y nombres para que V, U, Y y W compartan universo sectorial.", "Argentina 1512/15120; Brasil 51 sectores"],
        [4, "Base compatible", "U e Y se llevan a base nacional/precios basicos usando factores publicados por producto.", "factor = produccion domestica pb / oferta total pc"],
        [5, "Transformacion STI", "Se calcula D, Z, A, L y f_ind bajo tecnologia de industria.", "Z = D @ U"],
        [6, "Cierre menor", "Solo si el negativo es pequeno, se aplica RAS preservando g y sum_col(Z).", "Brasil 2001-2006; Uruguay 2016"],
        [7, "Validacion", "Se verifican cuadratura, etiquetas, no negatividad, Leontief, Ghosh y cierres sectoriales.", "validacion_resumen"],
        [8, "Empaque", "Cada anio queda en un Excel final autocontenido con matrices, multiplicadores y validaciones.", "output/matrices_insumo_producto"],
    ]
    append_table(ws, 4, ["Paso", "Bloque", "Que se hace", "Evidencia"], steps, style)
    style_sheet(ws, {1: 9, 2: 24, 3: 82, 4: 42})

    # Brasil 2001 closure sample
    ws = wb.create_sheet("Brasil_2001_cierre")
    sheet_title(ws, "Brasil 2001: ejemplo de cierre menor", "La hoja compara demanda final original y final conciliada, preservando produccion y documentando ajuste.")
    b_path = MIP_ROOT / "Brasil" / "MIP_Brasil_2001.xlsx"
    ajuste = pd.read_excel(b_path, sheet_name="ajuste_cierre")
    ajuste = ajuste.rename(columns={ajuste.columns[0]: "sector"})
    focus = ajuste.sort_values("ajuste_demanda_final").head(8)
    rows = focus[[
        "sector",
        "produccion_bruta_g",
        "demanda_final_original",
        "demanda_final_conciliada",
        "ajuste_demanda_final",
        "ventas_intermedias_original",
        "ventas_intermedias_conciliadas",
        "ajuste_ventas_intermedias",
    ]].values.tolist()
    append_table(
        ws,
        4,
        [
            "Sector",
            "g",
            "Demanda final original",
            "Demanda final final",
            "Ajuste f",
            "Ventas Z original",
            "Ventas Z final",
            "Ajuste ventas Z",
        ],
        rows,
        style,
    )
    style_sheet(ws, {1: 45, 2: 16, 3: 18, 4: 18, 5: 15, 6: 18, 7: 18, 8: 18})

    # Uruguay 2017 alert
    ws = wb.create_sheet("Uruguay_2017_alerta")
    sheet_title(ws, "Uruguay 2017: alerta no conciliada", "Los negativos son materiales; se conserva la alerta mientras se busca Y fuente o una MIP directa 2017.")
    u_path = MIP_ROOT / "Uruguay" / "MIP_Uruguay_2017.xlsx"
    f_ury = pd.read_excel(u_path, sheet_name="f_demanda_final")
    f_ury = f_ury.rename(columns={f_ury.columns[0]: "sector", f_ury.columns[1]: "demanda_final"})
    g_ury = pd.read_excel(u_path, sheet_name="g_produccion")
    g_ury = g_ury.rename(columns={g_ury.columns[0]: "sector", g_ury.columns[1]: "produccion_bruta_g"})
    neg = f_ury[f_ury["demanda_final"] < -1e-8].merge(g_ury, on="sector", how="left")
    neg["negativo_sobre_g"] = neg["demanda_final"] / neg["produccion_bruta_g"]
    neg["decision"] = "No ajustar mecanicamente; revisar fuente COU/Y"
    append_table(
        ws,
        4,
        ["Sector", "Demanda final", "Produccion bruta g", "f/g", "Decision"],
        neg[["sector", "demanda_final", "produccion_bruta_g", "negativo_sobre_g", "decision"]].values.tolist(),
        style,
    )
    style_sheet(ws, {1: 46, 2: 18, 3: 18, 4: 12, 5: 46})

    # Validation summary
    ws = wb.create_sheet("Validaciones")
    sheet_title(ws, "Validaciones matematicas", "Resumen generado desde output/tablas/validacion_matematica_mip.xlsx.")
    val_cols = [
        "pais",
        "anio",
        "n_sectores",
        "validacion_estructural",
        "validacion_diagnostica",
        "A_vs_Zg_abs_max",
        "leontief_abs_max",
        "oferta_vs_demanda_abs_max",
        "Lf_vs_g_abs_max",
        "demanda_final_neg_share",
    ]
    validation = pd.read_excel(VALIDACION)
    append_table(ws, 4, val_cols, validation[val_cols].replace({np.nan: ""}).values.tolist(), style)
    style_sheet(ws, {1: 18, 2: 10, 3: 12, 4: 20, 5: 20, 6: 18, 7: 18, 8: 20, 9: 18, 10: 18})

    # Simulator pilot
    ws = wb.create_sheet("Simulador_piloto")
    sheet_title(ws, "Simulador piloto: choque de demanda", "Muestra reducida con Brasil 2001. En la version final se usara la matriz completa por pais/anio.")
    sample = sample_matrix("Brasil", 2001, n=8)
    sectors = sample["sectors"]
    headers = ["Sector", "g_base", "f_base", "shock_pct_editable", "Delta_f", "Delta_g_formula", "g_escenario", "Delta_g_control_python"]
    for c, h in enumerate(headers, 1):
        cell = ws.cell(4, c, h)
        cell.fill = style["header_fill"]
        cell.font = style["header_font"]
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = style["border"]

    l_values = sample["L"].to_numpy(dtype=float)
    f_values = sample["f"].to_numpy(dtype=float)
    shock = np.array([0.05 if i == 0 else 0.0 for i in range(len(sectors))])
    delta_f = f_values * shock
    delta_g = l_values @ delta_f
    for r, sector in enumerate(sectors, start=5):
        i = r - 5
        ws.cell(r, 1, sector)
        ws.cell(r, 2, float(sample["g"].iloc[i]))
        ws.cell(r, 3, float(sample["f"].iloc[i]))
        ws.cell(r, 4, 0.05 if i == 0 else 0.0)
        ws.cell(r, 5, f"=C{r}*D{r}")
        ws.cell(r, 6, f"=SUMPRODUCT($N{r}:$U{r},$E$5:$E$12)")
        ws.cell(r, 7, f"=B{r}+F{r}")
        ws.cell(r, 8, float(delta_g[i]))
        for c in range(1, 9):
            ws.cell(r, c).border = style["border"]
            ws.cell(r, c).alignment = Alignment(vertical="center", wrap_text=True)
        ws.cell(r, 4).number_format = "0.0%"
    ws["J4"] = "Matriz L muestral"
    ws["J4"].font = Font(bold=True, color="173B73")
    for c, sector in enumerate(sectors, start=14):
        ws.cell(4, c, sector)
        ws.cell(4, c).fill = style["header_fill"]
        ws.cell(4, c).font = style["header_font"]
        ws.cell(4, c).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.cell(4, c).border = style["border"]
    for r, sector in enumerate(sectors, start=5):
        ws.cell(r, 13, sector)
        ws.cell(r, 13).fill = PatternFill("solid", fgColor="EEF4FB")
        ws.cell(r, 13).font = Font(bold=True, color="173B73")
        ws.cell(r, 13).border = style["border"]
        for c, value in enumerate(l_values[r - 5], start=14):
            ws.cell(r, c, float(value))
            ws.cell(r, c).number_format = "0.0000"
            ws.cell(r, c).border = style["border"]
    for row in ws.iter_rows(min_row=5, max_row=12, min_col=2, max_col=8):
        for cell in row:
            if cell.column != 4:
                cell.number_format = "#,##0.00"
    style_sheet(ws, {1: 36, 2: 14, 3: 14, 4: 16, 5: 14, 6: 16, 7: 16, 8: 18, 13: 36})
    for col in range(14, 22):
        ws.column_dimensions[get_column_letter(col)].width = 13

    # Small chart for simulated delta_g
    chart = BarChart()
    chart.title = "Delta g por sector de muestra"
    chart.y_axis.title = "Impacto"
    chart.x_axis.title = "Sector"
    data = Reference(ws, min_col=8, min_row=4, max_row=12)
    cats = Reference(ws, min_col=1, min_row=5, max_row=12)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.height = 7
    chart.width = 14
    ws.add_chart(chart, "A15")

    # Formulas sheet
    ws = wb.create_sheet("Formulas")
    sheet_title(ws, "Formulas clave", "Resumen de identidades usadas por la reconstruccion, validacion y simulacion.")
    formulas = [
        ["Market share", "D[i,p] = V[i,p] / q[p]", "Distribuye productos hacia industrias."],
        ["Flujos intermedios", "Z = D @ U", "Convierte usos por producto en matriz industria x industria."],
        ["Coeficientes tecnicos", "A = Z @ diag(g)^-1", "Cada columna se normaliza por produccion del comprador."],
        ["Leontief", "L = (I - A)^-1", "Propaga choques de demanda final."],
        ["Ghosh", "B = diag(g)^-1 @ Z; G = (I - B)^-1", "Propaga lectura de encadenamientos hacia adelante."],
        ["Demanda final", "f = D @ Y", "Transforma demanda final por producto a industrias."],
        ["Simulador", "Delta g = L @ Delta f", "Impacto estimado de un choque de demanda."],
    ]
    append_table(ws, 4, ["Bloque", "Formula", "Lectura"], formulas, style)
    style_sheet(ws, {1: 24, 2: 42, 3: 70})

    # Workbook-wide polish
    for ws in wb.worksheets:
        ws.sheet_view.showGridLines = False
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.freeze_panes = "A4"

    wb.calculation.fullCalcOnLoad = True
    wb.calculation.forceFullCalc = True

    out_path = OUT_PRUEBAS / XLSX_NAME
    wb.save(out_path)
    wb.save(ROOT / XLSX_NAME)
    return out_path


def main() -> None:
    inventory = build_inventory()
    html_path = generate_html(inventory)
    xlsx_path = generate_workbook(inventory)
    print(f"[OK] {html_path}")
    print(f"[OK] {ROOT / HTML_NAME}")
    print(f"[OK] {xlsx_path}")
    print(f"[OK] {ROOT / XLSX_NAME}")


if __name__ == "__main__":
    main()
