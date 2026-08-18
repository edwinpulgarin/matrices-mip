"""
Informe HTML por INDICADOR → PAÍS → AÑO, para compartir con el equipo.

No calcula nada: lee los dos CSV que ya emiten otros scripts y los renderiza.
Misma separación de responsabilidades que `presentacion_html.py`.

  reports/comparacion_dom_total.csv   <- scripts/comparar_dom_total.py
  reports/estado_ras.csv              <- scripts/estado_ras.py

Tres indicadores, y dentro de cada uno los cinco países con todos sus años:

  1. Multiplicador de producción   Σᵢ lᵢⱼ
  2. Coeficiente técnico           Σᵢ aᵢⱼ  (y su apertura directo / indirecto)
  3. Efecto del balanceo RAS       cuánto movió el único paso no reproducible
                                   con aritmética directa entre hojas

Uso:  py -3 scripts/informe_dom_total_html.py
Sale: output/informe_dom_total.html
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import pandas as pd

SALIDA = ROOT / "output" / "informe_dom_total.html"
PAISES = ["Argentina", "Brasil", "Colombia", "México", "Uruguay"]
OFICIAL = "MIP oficial INEGI"


# ── formato ──────────────────────────────────────────────────────────────────

def num(x, dec=4):
    if pd.isna(x):
        return "—"
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def pct(x, dec=1, signo=False):
    if pd.isna(x):
        return "—"
    s = f"{x:+.{dec}f}" if signo else f"{x:.{dec}f}"
    return s.replace(".", ",") + " %"


def sci(x):
    return "—" if pd.isna(x) else f"{x:.1e}".replace(".", ",")


# ── datos ────────────────────────────────────────────────────────────────────

def cargar():
    d = pd.read_csv(ROOT / "reports" / "comparacion_dom_total.csv")
    r = pd.read_csv(ROOT / "reports" / "estado_ras.csv")
    r = r.rename(columns={"mult": "ras_mult"})
    # Los libros oficiales de INEGI no pasan por el balanceo —la matriz ya viene
    # construida— así que no tienen fila en estado_ras y no deben heredar la del
    # año reconstruido: la clave del cruce excluye esa variante.
    d["_k"] = d.pais + "|" + d.anio.astype(str)
    r["_k"] = r.pais + "|" + r.anio.astype(str)
    cols = ["_k", "modo", "desbalance", "discrepancia", "mueve", "negativos"]
    d = d.merge(r[cols], on="_k", how="left")
    d.loc[d.variante == OFICIAL, ["modo", "desbalance", "discrepancia",
                                  "mueve", "negativos"]] = None
    d.loc[d.variante == OFICIAL, "modo"] = "no aplica"
    return d.drop(columns="_k")


# ── gráfico: un pequeño múltiplo por país ────────────────────────────────────
# Años equiespaciados y rotulados, NO un eje temporal continuo: Argentina salta
# de 1997 a 2004 y a 2018, y una línea entre esos puntos inventaría una
# trayectoria que no medimos. Dos puntos por año, unidos, es lo que hay.

W, H = 720, 168
MI, MD, MT, MB = 52, 14, 16, 30


def mini(g, col_dom, col_tot, lo, hi, uid):
    n = len(g)
    px = lambda i: MI + (W - MI - MD) * ((i + 0.5) / n)
    py = lambda v: MT + (H - MT - MB) * (1 - (v - lo) / (hi - lo))

    paso = (hi - lo) / 4
    grid, ejes = [], []
    for k in range(5):
        v = lo + k * paso
        y = py(v)
        grid.append(f'<line class="g" x1="{MI}" y1="{y:.1f}" x2="{W - MD}" y2="{y:.1f}"/>')
        ejes.append(f'<text class="ay" x="{MI - 9}" y="{y + 3.5:.1f}">{num(v, 2)}</text>')

    marcas = []
    for i, (_, r) in enumerate(g.iterrows()):
        x, yd, yt = px(i), py(r[col_dom]), py(r[col_tot])
        marcas.append(
            f'<g class="par"><title>{r.anio:.0f} · doméstica {num(r[col_dom])} · '
            f'total {num(r[col_tot])} ({pct(100 * (r[col_tot] / r[col_dom] - 1), 1, True)})</title>'
            f'<line class="con" x1="{x:.1f}" y1="{yt:.1f}" x2="{x:.1f}" y2="{yd:.1f}"/>'
            f'<circle class="mk tot" cx="{x:.1f}" cy="{yt:.1f}" r="4.5"/>'
            f'<circle class="mk dom" cx="{x:.1f}" cy="{yd:.1f}" r="4.5"/>'
            f'<rect class="hit" x="{x - 14:.1f}" y="{MT}" width="28" '
            f'height="{H - MT - MB}"/></g>')
        marcas.append(f'<text class="ax" x="{x:.1f}" y="{H - 9}">{r.anio:.0f}</text>')

    return (f'<svg viewBox="0 0 {W} {H}" class="mini" role="img" '
            f'aria-labelledby="t{uid}"><title id="t{uid}">Serie por año</title>'
            + "".join(grid) + "".join(ejes) + "".join(marcas) + "</svg>")


# ── bloques ──────────────────────────────────────────────────────────────────

def bloque_mult(d, lo, hi):
    out = []
    for i, pais in enumerate(PAISES):
        g = d[d.pais == pais].sort_values(["anio", "variante"])
        fs = "".join(f"""<tr>
        <td class="yr">{r.anio:.0f}</td><td class="var">{r.variante}</td>
        <td class="n">{num(r.dom_mult_medio)}</td>
        <td class="n">{num(r.dom_mult_mediano)}</td>
        <td class="n">{num(r.dom_mult_max)}</td>
        <td class="n">{num(r.dom_mult_pond)}</td>
        <td class="n sep">{num(r.tot_mult_medio)}</td>
        <td class="n gap">{pct(r.dif_mult_medio_pct, 2, True)}</td>
        <td class="n">{pct(r.importado_pct)}</td></tr>""" for _, r in g.iterrows())
        out.append(f"""<article class="pais" id="mult-{i}">
      <h3>{pais}<span class="meta">{len(g)} años · {g.n.max():.0f} sectores</span></h3>
      {mini(g, 'dom_mult_medio', 'tot_mult_medio', lo, hi, f'm{i}')}
      <div class="scroll"><table>
        <thead><tr><th>Año</th><th>Fuente</th>
          <th class="n">Medio</th><th class="n">Mediano</th><th class="n">Máximo</th>
          <th class="n">Ponderado</th><th class="n sep">Si fuera total</th>
          <th class="n">Δ</th><th class="n">Importado % CI</th></tr></thead>
        <tbody>{fs}</tbody></table></div>
    </article>""")
    return out


def bloque_coef(d, lo, hi):
    out = []
    for i, pais in enumerate(PAISES):
        g = d[d.pais == pais].sort_values(["anio", "variante"])
        fs = "".join(f"""<tr>
        <td class="yr">{r.anio:.0f}</td><td class="var">{r.variante}</td>
        <td class="n">{num(r.dom_directo_medio)}</td>
        <td class="n">{num(r.dom_a_max)}</td>
        <td class="n">{num(r.dom_indirecto_medio)}</td>
        <td class="n">{num(r.dom_ci_sobre_vbp)}</td>
        <td class="n sep">{num(r.tot_directo_medio)}</td>
        <td class="n gap">{pct(r.dif_directo_medio_pct, 2, True)}</td>
        <td class="n gap">{pct(r.dif_indirecto_medio_pct, 1, True)}</td></tr>"""
                       for _, r in g.iterrows())
        out.append(f"""<article class="pais" id="coef-{i}">
      <h3>{pais}<span class="meta">{len(g)} años · {g.n.max():.0f} sectores</span></h3>
      {mini(g, 'dom_directo_medio', 'tot_directo_medio', lo, hi, f'c{i}')}
      <div class="scroll"><table>
        <thead><tr><th>Año</th><th>Fuente</th>
          <th class="n">Σᵢaᵢⱼ medio</th><th class="n">Σᵢaᵢⱼ máx.</th>
          <th class="n">Indirecto</th><th class="n">CI / VBP</th>
          <th class="n sep">Σᵢaᵢⱼ total</th><th class="n">Δ directo</th>
          <th class="n">Δ indirecto</th></tr></thead>
        <tbody>{fs}</tbody></table></div>
    </article>""")
    return out


CHIP = {"no hizo falta": ("ok", "no hizo falta"),
        "discrepancia": ("med", "sólo discrepancia"),
        "RAS": ("alto", "RAS completo"),
        "no aplica": ("na", "no aplica")}


def bloque_ras(d):
    out = []
    mx = d.mueve.max()
    for i, pais in enumerate(PAISES):
        g = d[d.pais == pais].sort_values(["anio", "variante"])
        fs = []
        for _, r in g.iterrows():
            cl, txt = CHIP.get(r.modo if isinstance(r.modo, str) else "no aplica",
                               ("na", "—"))
            if pd.isna(r.mueve):
                barra = '<span class="cero">—</span>'
            else:
                ancho = 0.0 if mx == 0 else 100 * r.mueve / mx
                barra = (f'<span class="bar"><i style="width:{ancho:.1f}%"></i></span>'
                         if ancho > 0 else '<span class="cero">no movió</span>')
            fs.append(f"""<tr>
        <td class="yr">{r.anio:.0f}</td><td class="var">{r.variante}</td>
        <td><span class="chip {cl}">{txt}</span></td>
        <td class="n">{sci(r.desbalance)}</td>
        <td class="n">{pct(100 * r.mueve, 4) if not pd.isna(r.mueve) else "—"}</td>
        <td class="bc">{barra}</td>
        <td class="n">{"—" if pd.isna(r.negativos) else f"{r.negativos:.0f}"}</td>
        <td class="n">{pct(r.celdas_dA_neg_pct, 2)}</td>
        <td class="n">{sci(r.min_dcol_A)}</td></tr>""")
        out.append(f"""<article class="pais" id="ras-{i}">
      <h3>{pais}<span class="meta">{len(g)} años</span></h3>
      <div class="scroll"><table>
        <thead><tr><th>Año</th><th>Fuente</th><th>Balanceo</th>
          <th class="n">Desbalance de entrada</th><th class="n">Movió</th>
          <th>&nbsp;</th><th class="n">Celdas fijadas</th>
          <th class="n">Celdas de A que bajan</th>
          <th class="n">Mín. Δ Σᵢaᵢⱼ</th></tr></thead>
        <tbody>{"".join(fs)}</tbody></table></div>
    </article>""")
    return out


# ── página ───────────────────────────────────────────────────────────────────

def main():
    d = cargar()
    lo_m = min(d.dom_mult_medio.min(), d.tot_mult_medio.min())
    hi_m = max(d.dom_mult_medio.max(), d.tot_mult_medio.max())
    pad = 0.06 * (hi_m - lo_m)
    lo_m, hi_m = lo_m - pad, hi_m + pad
    lo_c = min(d.dom_directo_medio.min(), d.tot_directo_medio.min())
    hi_c = max(d.dom_directo_medio.max(), d.tot_directo_medio.max())
    padc = 0.06 * (hi_c - lo_c)
    lo_c, hi_c = lo_c - padc, hi_c + padc

    ras_si = int((d.modo == "RAS").sum())
    ras_no = int((d.modo == "no hizo falta").sum())
    ras_disc = int((d.modo == "discrepancia").sum())
    nav_p = "".join(f'<a href="#{{k}}-{i}">{p}</a>' for i, p in enumerate(PAISES))

    html = PLANTILLA.format(
        n=len(d),
        paises=len(PAISES),
        anios_min=int(d.anio.min()), anios_max=int(d.anio.max()),
        mult_dom_lo=num(d.dom_mult_medio.min(), 2), mult_dom_hi=num(d.dom_mult_medio.max(), 2),
        mult_tot_lo=num(d.tot_mult_medio.min(), 2), mult_tot_hi=num(d.tot_mult_medio.max(), 2),
        d_lo=pct(d.dif_mult_medio_pct.min(), 1, True),
        d_hi=pct(d.dif_mult_medio_pct.max(), 1, True),
        coef_lo=num(d.dom_directo_medio.min()), coef_hi=num(d.dom_directo_medio.max()),
        ras_si=ras_si, ras_disc=ras_disc, ras_no=ras_no,
        ras_rotos=int((d.min_dA < -1e-9).sum()),
        min_col=num(d.min_dcol_A.min(), 2), min_mult=num(d.min_dmult.min(), 2),
        nav_mult=nav_p.replace("{k}", "mult"),
        nav_coef=nav_p.replace("{k}", "coef"),
        nav_ras=nav_p.replace("{k}", "ras"),
        b_mult="\n".join(bloque_mult(d, lo_m, hi_m)),
        b_coef="\n".join(bloque_coef(d, lo_c, hi_c)),
        b_ras="\n".join(bloque_ras(d)),
    )
    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(html, encoding="utf-8")
    print(f"[OK] {SALIDA.relative_to(ROOT)}  ({len(html):,} bytes, {len(d)} matrices)")


PLANTILLA = """<title>Indicadores de las 38 matrices</title>
<style>
  :root {{
    --ground:#F4F6F5; --surface:#FFFFFF; --sunk:#EDF1F0; --raise:#FBFCFC;
    --ink:#131B1A; --ink-2:#3D4A48; --muted:#5C6A68; --hair:#DCE3E1;
    --dom:#009486; --tot:#B0561F;
    /* El teal de las marcas da 3,76:1 sobre blanco: alcanza para un punto de
       11 px y para un número de 26 px, no para texto chico. Los textos usan
       este paso más oscuro (5,37:1) y las marcas siguen con --dom. */
    --dom-ink:#00786D;
    --ok:#2F7D5B; --med:#8A6D1F; --alto:#A33B1E;
    --serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
    --sans:"Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,sans-serif;
    --mono:ui-monospace,"Cascadia Mono",Consolas,"DejaVu Sans Mono",monospace;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --ground:#0D1211; --surface:#151D1C; --sunk:#111817; --raise:#1A2322;
      --ink:#E8EDEB; --ink-2:#C2CCCA; --muted:#94A3A0; --hair:#26302E;
      --dom:#1F9E90; --tot:#C87A38; --dom-ink:#4FBFB0;
      --ok:#5DAE86; --med:#C3A24E; --alto:#DB7C5E;
    }}
  }}
  :root[data-theme="dark"] {{
    --ground:#0D1211; --surface:#151D1C; --sunk:#111817; --raise:#1A2322;
    --ink:#E8EDEB; --ink-2:#C2CCCA; --muted:#94A3A0; --hair:#26302E;
    --dom:#1F9E90; --tot:#C87A38; --dom-ink:#4FBFB0;
    --ok:#5DAE86; --med:#C3A24E; --alto:#DB7C5E;
  }}

  body {{
    background:var(--ground); color:var(--ink); font-family:var(--sans);
    font-size:16px; line-height:1.6; margin:0;
    padding:0 clamp(16px,4vw,44px) 90px; -webkit-font-smoothing:antialiased;
  }}
  .wrap {{ max-width:1060px; margin:0 auto; }}
  p {{ max-width:66ch; color:var(--ink-2); }}
  b {{ color:var(--ink); font-weight:600; }}
  code {{ font-family:var(--mono); font-size:0.87em; background:var(--sunk);
    padding:0.1em 0.34em; border-radius:3px; color:var(--ink); }}

  header {{ padding:54px 0 32px; }}
  .eyebrow {{ font-family:var(--mono); font-size:11.5px; letter-spacing:0.13em;
    text-transform:uppercase; color:var(--muted); margin:0 0 16px; }}
  h1 {{ font-family:var(--serif); font-size:clamp(32px,5vw,50px); font-weight:600;
    line-height:1.08; letter-spacing:-0.015em; margin:0 0 16px; max-width:20ch;
    text-wrap:balance; }}
  .lede {{ font-size:18px; max-width:64ch; margin:0; }}

  .cifras {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(196px,1fr));
    gap:1px; background:var(--hair); border:1px solid var(--hair);
    border-radius:5px; overflow:hidden; margin:30px 0 0; }}
  .cif {{ background:var(--surface); padding:18px 20px; }}
  .cif b {{ display:block; font-family:var(--serif); font-size:26px; line-height:1.15;
    color:var(--dom); font-variant-numeric:tabular-nums; font-weight:600; }}
  .cif span {{ font-size:13px; color:var(--muted); }}

  .ind {{ margin-top:64px; }}
  .ind > h2 {{ font-family:var(--serif); font-size:30px; font-weight:600; margin:0;
    letter-spacing:-0.012em; display:flex; align-items:baseline; gap:14px; }}
  .ind > h2 .k {{ font-family:var(--mono); font-size:12px; letter-spacing:0.09em;
    color:var(--muted); border:1px solid var(--hair); border-radius:99px;
    padding:3px 10px; flex:none; }}
  .formula {{ font-family:var(--mono); font-size:13.5px; color:var(--dom-ink);
    margin:10px 0 0; }}
  .nav {{ display:flex; flex-wrap:wrap; gap:7px; margin:18px 0 4px;
    padding-bottom:16px; border-bottom:1px solid var(--hair); }}
  .nav a {{ font-size:12.5px; color:var(--ink-2); text-decoration:none;
    border:1px solid var(--hair); background:var(--surface);
    border-radius:99px; padding:4px 13px; }}
  .nav a:hover, .nav a:focus-visible {{ border-color:var(--dom); color:var(--dom-ink); }}

  .pais {{ margin-top:34px; scroll-margin-top:20px; }}
  .pais h3 {{ font-size:15.5px; font-weight:600; margin:0 0 12px;
    display:flex; align-items:baseline; gap:12px; }}
  .pais h3::before {{ content:""; width:3px; height:13px; background:var(--dom);
    border-radius:1px; flex:none; }}
  .pais h3 .meta {{ font-family:var(--mono); font-size:11px; color:var(--muted);
    font-weight:400; letter-spacing:0.03em; }}

  .mini {{ width:100%; height:auto; display:block; background:var(--surface);
    border:1px solid var(--hair); border-radius:5px 5px 0 0; border-bottom:0; }}
  .mini .g {{ stroke:var(--hair); stroke-width:1; }}
  .mini .ay, .mini .ax {{ font-family:var(--mono); font-size:10px; fill:var(--muted); }}
  .mini .ay {{ text-anchor:end; }}
  .mini .ax {{ text-anchor:middle; }}
  .mini .con {{ stroke:var(--tot); stroke-width:2; opacity:0.38; }}
  .mini .mk {{ stroke:var(--surface); stroke-width:2; }}
  .mini .mk.dom {{ fill:var(--dom); }}
  .mini .mk.tot {{ fill:var(--tot); }}
  .mini .hit {{ fill:transparent; }}
  .mini .par:hover .mk {{ stroke-width:3; }}
  .mini .par:hover .con {{ opacity:0.8; }}
  .mini + .scroll {{ border-radius:0 0 5px 5px; }}

  .leyenda {{ display:flex; gap:18px; align-items:center; font-size:12.5px;
    color:var(--ink-2); margin:14px 0 0; flex-wrap:wrap; }}
  .leyenda i {{ width:10px; height:10px; border-radius:50%; display:inline-block;
    margin-right:6px; vertical-align:-1px; }}

  .scroll {{ overflow-x:auto; border:1px solid var(--hair); border-radius:5px;
    background:var(--surface); }}
  table {{ border-collapse:collapse; width:100%; font-size:13px; }}
  th, td {{ padding:8px 12px; text-align:left; border-bottom:1px solid var(--hair);
    white-space:nowrap; }}
  thead th {{ font-family:var(--mono); font-size:10px; letter-spacing:0.06em;
    text-transform:uppercase; color:var(--muted); font-weight:400;
    background:var(--sunk); vertical-align:bottom; }}
  tbody tr:last-child td {{ border-bottom:0; }}
  tbody tr:hover td {{ background:var(--raise); }}
  .n {{ text-align:right; font-family:var(--mono); font-variant-numeric:tabular-nums; }}
  td.yr {{ font-family:var(--mono); font-variant-numeric:tabular-nums; }}
  td.var {{ color:var(--muted); font-size:12px; }}
  .sep {{ border-left:1px solid var(--hair); }}
  td.gap {{ color:var(--tot); }}

  .chip {{ font-size:11.5px; padding:2px 9px; border-radius:99px;
    border:1px solid currentColor; white-space:nowrap; }}
  .chip.ok {{ color:var(--ok); }}
  .chip.med {{ color:var(--med); }}
  .chip.alto {{ color:var(--alto); }}
  .chip.na {{ color:var(--muted); }}
  td.bc {{ width:120px; }}
  .bar {{ display:block; width:100px; height:7px; background:var(--sunk);
    border-radius:2px; overflow:hidden; }}
  .bar i {{ display:block; height:100%; background:var(--alto); border-radius:2px; }}
  .cero {{ font-family:var(--mono); font-size:11px; color:var(--muted); }}

  .cap {{ font-size:12.5px; color:var(--muted); margin:9px 0 0; max-width:74ch; }}
  footer {{ margin-top:70px; border-top:1px solid var(--hair); padding-top:20px;
    font-size:12.5px; color:var(--muted); }}
  footer p {{ color:var(--muted); margin:0 0 6px; }}
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">CEPAL · Reconstrucción de MIP desde COU · UN Handbook F74 Rev. 1</p>
    <h1>Los indicadores de las {n} matrices, indicador por indicador</h1>
    <p class="lede">Todo lo que se publica se deriva de la <b>Z doméstica</b>: las celdas
    llevan sólo insumo de origen nacional y el importado va en una fila primaria. Acá
    está cada indicador abierto por país y por año, y al lado, cuánto valdría si se
    hubiera usado la matriz total.</p>
    <div class="cifras">
      <div class="cif"><b>{n}</b><span>matrices, {paises} países, {anios_min}–{anios_max}</span></div>
      <div class="cif"><b>{mult_dom_lo}–{mult_dom_hi}</b><span>rango del multiplicador medio (doméstica)</span></div>
      <div class="cif"><b>{d_lo} a {d_hi}</b><span>cuánto subiría con la matriz total</span></div>
      <div class="cif"><b>{ras_no} · {ras_disc} · {ras_si}</b><span>sin balanceo · sólo discrepancia · RAS completo</span></div>
    </div>
  </header>

  <section class="ind">
    <h2><span class="k">INDICADOR 1</span>Multiplicador de producción</h2>
    <p class="formula">mⱼ = Σᵢ lᵢⱼ &nbsp;·&nbsp; L = (I − A)⁻¹ &nbsp;·&nbsp; UN Handbook Cap. 20</p>
    <p>Cuánta producción total se activa por cada unidad de demanda final del sector
    <code>j</code>. Sobre la matriz doméstica mide producción <b>del propio país</b>:
    es la lectura de profundidad de la cadena local. El «ponderado» pesa cada sector
    por su producción, así que responde a cuánto se mueve el país si la demanda crece
    como está repartida hoy.</p>
    <div class="leyenda">
      <span><i style="background:var(--dom)"></i>Z doméstica <b>(publicado)</b></span>
      <span><i style="background:var(--tot)"></i>Z total (nacional + importada)</span>
      <span style="color:var(--muted)">Eje vertical común a los cinco países. Pasá el
      cursor por cada año para ver las cifras.</span>
    </div>
    <div class="nav">{nav_mult}</div>
    {b_mult}
  </section>

  <section class="ind">
    <h2><span class="k">INDICADOR 2</span>Coeficiente técnico</h2>
    <p class="formula">aᵢⱼ = zᵢⱼ / xⱼ &nbsp;·&nbsp; A = Z · diag(g)⁻¹ &nbsp;·&nbsp; UN Handbook Cap. 20</p>
    <p>Cuánto insumo nacional del sector <code>i</code> hace falta por unidad producida
    por el sector <code>j</code>. La suma de la columna, <code>Σᵢaᵢⱼ</code>, es el
    <b>efecto directo</b>: la primera vuelta de compras. El resto del multiplicador
    —<code>m − 1 − Σᵢaᵢⱼ</code>— es el <b>efecto indirecto</b>, las vueltas siguientes,
    y es el que más se altera al cambiar la definición de la matriz.</p>
    <div class="leyenda">
      <span><i style="background:var(--dom)"></i>Z doméstica <b>(publicado)</b></span>
      <span><i style="background:var(--tot)"></i>Z total (nacional + importada)</span>
    </div>
    <div class="nav">{nav_coef}</div>
    {b_coef}
  </section>

  <section class="ind">
    <h2><span class="k">INDICADOR 3</span>Efecto del balanceo RAS</h2>
    <p class="formula">min Σ |uᵢⱼ − u⁰ᵢⱼ| sujeto a las dos identidades &nbsp;·&nbsp; UN Handbook Cap. 11</p>
    <p>El RAS es el <b>único paso de toda la cadena que no se puede rehacer con
    aritmética directa entre hojas</b>, así que es el que un auditor quiere ver acotado.
    Sólo corre si el cuadro publicado entra sin cumplir las identidades: el «desbalance
    de entrada» mide la calidad del cuadro del instituto, no la del pipeline. Cuando el
    residuo es macro y no estructural se anota como discrepancia estadística en la
    demanda final, sin tocar ninguna celda de la utilización.</p>
    <p>Las dos últimas columnas son la consecuencia medida: correr el balanceo por
    separado en cada versión de la matriz rompe la monotonía <b>en celdas sueltas</b> de
    <code>A</code> —en {ras_rotos} de las {n} matrices, y son exactamente aquellas donde
    el RAS actúa—, pero <b>nunca en la suma de la columna</b>, que es el coeficiente
    técnico, ni en el multiplicador: el mínimo de las dos es {min_col} en las {n}.</p>
    <div class="leyenda">
      <span><span class="chip ok">no hizo falta</span> el cuadro cierra solo</span>
      <span><span class="chip med">sólo discrepancia</span> residuo macro a demanda final</span>
      <span><span class="chip alto">RAS completo</span> se ajustaron celdas de U</span>
      <span><span class="chip na">no aplica</span> matriz ya publicada por el instituto</span>
    </div>
    <div class="nav">{nav_ras}</div>
    {b_ras}
    <p class="cap">«Movió» es el cambio máximo de una celda de la utilización como
    fracción del total; la barra lo escala contra el mayor de las {n} matrices.
    «Celdas fijadas» son las negativas que quedan fuera del RAS —variación de
    existencias legítima— y vuelven con su valor exacto.</p>
  </section>

  <footer>
    <p>Generado por <code>scripts/informe_dom_total_html.py</code> desde
    <code>reports/comparacion_dom_total.csv</code> y <code>reports/estado_ras.csv</code>.
    La página no calcula: todas las cifras salen de esos dos archivos.</p>
    <p>Industria × industria, Modelo D (estructura fija de ventas de producto), precios
    básicos, matriz doméstica. Argentina 1997 y 2004–2023 · Brasil 2010–2021 ·
    Colombia 2014–2024 · México 2008, 2013 y 2018 · Uruguay 2012, 2016 y 2017.</p>
  </footer>
</div>
"""

if __name__ == "__main__":
    main()
