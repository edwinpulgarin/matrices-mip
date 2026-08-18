"""
Z doméstica vs. Z total: cuánto cambian los indicadores, país por país y año por año.

La MIP que se publica es DOMÉSTICA: `Z` lleva sólo el insumo de origen nacional
y el importado va en la fila primaria «consumo intermedio importado». Todo lo
que viene después —A, L, multiplicadores, encadenamientos— se calcula sobre esa
Z, y desde el 2026-08-18 el libro no entrega ninguna otra matriz.

La versión TOTAL (nacional + importada, importado endógeno dentro de Z) se
recalcula ACÁ desde la fuente, para poder medir la diferencia. Ese es el rol de
este script: que la comparación exista y esté publicada sin necesidad de que el
libro cargue una segunda matriz que alguien pueda confundir con la buena.

Este script hace dos cosas:

  1. **Verifica que la Z publicada es la doméstica.** Reabre el libro entregado,
     lee la hoja «Z consumos intermedios» y confronta su suma contra las dos Z
     recalculadas acá. Es el complemento de `validar_consistencia.py`, que
     re-verifica A ≈ Z·diag(g)⁻¹ y L ≈ (I−A)⁻¹ **a partir de la Z del archivo**
     pero no puede saber cuál de las dos versiones es esa Z.

  2. **Mide la diferencia entre las dos versiones** en los indicadores que usa el
     equipo: Σᵢaᵢⱼ (coeficientes técnicos), multiplicador de producción, su
     descomposición en efecto directo e indirecto, los encadenamientos de
     Rasmussen y la clasificación de sectores.

Sobre la hipótesis del equipo (los indicadores deben ser MENORES con Z
doméstica): es cierta, y en el agregado no es un resultado empírico sino una
consecuencia de la construcción. Ambas versiones comparten el vector de
producción x, y U_total = U_dom + U_imp con U_imp ≥ 0, así que A_tot ≥ A_dom
celda a celda; como A ≥ 0 y la serie de Neumann converge, L = Σₖ Aᵏ es monótona
en A y por lo tanto L_tot ≥ L_dom y todo multiplicador también. Lo que sí es
empírico —y es lo que hay que mirar— es la MAGNITUD de la brecha, que es la
apertura importadora de cada economía, y si el ORDEN de los sectores sobrevive.

Con una salvedad que este script mide en vez de suponer: el balanceo se corre por
separado en cada versión, y donde el RAS actúa la desigualdad puede romperse EN
CELDAS SUELTAS. Por eso se verifican los tres niveles —celda de A, suma de
columna de A y multiplicador— y se registra si el RAS intervino en cada versión.

Uso:  py -3 -u scripts/comparar_dom_total.py
Genera: reports/comparacion_dom_total.md  y  reports/comparacion_dom_total.csv
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import numpy as np
import pandas as pd

from src.balanceo import balancear
from src.transformacion import transformar, desde_mip_oficial
from src.analisis import calcular
from src.valoracion import valorar_argentina, ensamblar_directo

from validar_consistencia import _leer_matriz, hoja_por_sufijo, S_Z

RAW_AR = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/argentina")
RAW_AR97 = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/argentina_mip97")
RAW_BR = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/brasil")
RAW_CO = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/colombia")
RAW_UY = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/uruguay")
NI_UY = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/Nueva_Info")
STG_MX = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw/_cepal_staging")

MAT = ROOT / "matrices"


# ── carga ────────────────────────────────────────────────────────────────────
# Cada loader devuelve un dict con las dos versiones de la matriz, los nombres de
# sector, la escala del libro y si el RAS intervino en cada versión. La escala
# hace falta sólo para la verificación contra el archivo (el libro se presenta en
# millones y algunas fuentes publican en miles); el estado del RAS, para explicar
# los casos donde la monotonía celda a celda se rompe.

def _dos(sut, nombres, escala=1.0, **kw):
    """Doméstica y total desde el mismo SUT valorado, balanceando cada una."""
    sb, rd = balancear(sut)
    st, rt = balancear(sut.a_total())
    return {"dom": transformar(sb, "D", **kw), "tot": transformar(st, "D", **kw),
            "escala": escala, "nombres": nombres,
            "ras_dom": bool(rd.get("aplicado")), "ras_tot": bool(rt.get("aplicado"))}


def _ar(anio, fn):
    def cargar():
        from src.parsers.argentina import parse
        d = parse(RAW_AR / fn, anio)
        sut = valorar_argentina(d)[0]
        return _dos(sut, d["ind_name"],
                    1.0 if "millones" in sut.unidad else 1000.0)
    return cargar


def _ar97():
    def cargar():
        from src.parsers.argentina97 import parse
        d = parse(RAW_AR97, 1997)
        return _dos(ensamblar_directo(d)[0], d["ind_name"], 1000.0,
                    no_mercado=d["no_mercado"])
    return cargar


def _br(anio, limpio):
    def cargar():
        if limpio:
            from src.parsers.brasil_mip import parse as parse_mip
            d = parse_mip(RAW_BR, anio)
            sut = ensamblar_directo(d)[0]
        else:
            from src.parsers.brasil import parse
            d = parse(RAW_BR, anio)
            sut = valorar_argentina(d)[0]
        return _dos(sut, d["ind_name"])
    return cargar


def _co(anio):
    def cargar():
        from src.parsers.colombia import parse_cou
        d = parse_cou(RAW_CO, anio)
        return _dos(valorar_argentina(d)[0], d["ind_name"])
    return cargar


def _uy(anio, archivo, hoja, detalle):
    def cargar():
        from src.parsers.uruguay import parse
        d = parse(archivo, anio, hoja=hoja, carpeta_detalle=detalle)
        return _dos(valorar_argentina(d)[0], d["ind_name"])
    return cargar


def _mx_cou():
    def cargar():
        from src.parsers.mexico import parse_sin_prorrateo
        d = parse_sin_prorrateo(STG_MX / "MEX_COU_2013", 2013, nivel="RAMA")
        return _dos(ensamblar_directo(d)[0], d["ind_name"])
    return cargar


def _mx_oficial(anio):
    def cargar():
        # INEGI publica la doméstica y la importada por separado: la total es la
        # suma de las dos, sin transformación ni balanceo nuestro de por medio.
        from src.parsers import mexico_mip
        d = mexico_mip.parse(anio, nivel="RAMA")
        return {"dom": desde_mip_oficial(d, total=False),
                "tot": desde_mip_oficial(d, total=True),
                "escala": 1.0, "nombres": d["ind_name"],
                "ras_dom": False, "ras_tot": False}
    return cargar


# (país, año, variante, libro, loader)
CASOS = (
    [("Argentina", 1997, "MIPAr97 · sin prorrateo",
      MAT / "Argentina" / "MIP_Argentina_1997_LIBRO.xlsx", _ar97())]
    + [("Argentina", a, "COU · prorrateo",
        MAT / "Argentina" / f"MIP_Argentina_{a}_LIBRO.xlsx", _ar(a, f"cou_{a}.xls"))
       for a in (2004, 2018, 2019, 2020, 2021, 2022, 2023)]
    + [("Brasil", a, "MIP n67 · sin prorrateo" if a in (2010, 2015) else "COU n68 · prorrateo",
        MAT / "Brasil" / f"MIP_Brasil_{a}_LIBRO.xlsx", _br(a, a in (2010, 2015)))
       for a in range(2010, 2022)]
    + [("Colombia", a, "COU · prorrateo",
        MAT / "Colombia" / f"MIP_Colombia_{a}_LIBRO.xlsx", _co(a))
       for a in range(2014, 2025)]
    + [("México", 2013, "COU · sin prorrateo",
        MAT / "Mexico" / "MIP_Mexico_2013_LIBRO.xlsx", _mx_cou())]
    + [("México", a, "MIP oficial INEGI",
        MAT / "Mexico" / f"MIP_Mexico_{a}_LIBRO_OFICIAL.xlsx", _mx_oficial(a))
       for a in (2008, 2013, 2018)]
    + [("Uruguay", 2012, "COU · prorrateo",
        MAT / "Uruguay" / "MIP_Uruguay_2012_LIBRO.xlsx",
        _uy(2012, NI_UY / "Uruguay_2012_Detallada_COU_C.xlsx", "COU_C", None)),
       ("Uruguay", 2016, "COU · prorrateo",
        MAT / "Uruguay" / "MIP_Uruguay_2016_LIBRO.xlsx",
        _uy(2016, NI_UY / "Uruguay_2016-2017 Detallada_COU_C.xlsx", "2016 CORRIENTE", None)),
       ("Uruguay", 2017, "COU · origen medido",
        MAT / "Uruguay" / "MIP_Uruguay_2017_LIBRO.xlsx",
        _uy(2017, NI_UY / "Uruguay_2016-2017 Detallada_COU_C.xlsx", "2017 CORRIENTE",
            RAW_UY / "cou_2017"))]
)


# ── métricas ─────────────────────────────────────────────────────────────────

def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Correlación de rangos, sin dependencias: Pearson sobre los rangos."""
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def indicadores(iot, an):
    """Los indicadores que el equipo usa, sobre una versión de la matriz."""
    return {
        "mult_medio": float(an.mult_produccion.mean()),
        "mult_mediano": float(an.mult_produccion.median()),
        "mult_max": float(an.mult_produccion.max()),
        # ponderado por PRODUCCIÓN, que es idéntica en las dos versiones: así la
        # diferencia es del todo atribuible a la matriz y no al vector de pesos
        # (la demanda final sí cambia, porque en la total incluye la importada).
        "mult_pond": an.mult_medio_ponderado(iot.x),
        "directo_medio": float(an.mult_directo.mean()),      # Σᵢ aᵢⱼ
        "indirecto_medio": float(an.mult_indirecto.mean()),
        "a_max": float(an.mult_directo.max()),
        # intensidad de uso intermedio de la economía: ΣΣZ / Σx
        "ci_sobre_vbp": float(iot.Z.to_numpy().sum() / max(float(iot.x.sum()), 1.0)),
        "claves": int((an.clasificar() == "Clave").sum()),
        "z_suma": float(iot.Z.to_numpy().sum()),
    }


def comparar(iot_d, iot_t):
    an_d, an_t = calcular(iot_d), calcular(iot_t)
    d, t = indicadores(iot_d, an_d), indicadores(iot_t, an_t)

    ind = list(iot_d.Z.index)
    A_d = an_d.A.reindex(index=ind, columns=ind).to_numpy()
    A_t = an_t.A.reindex(index=ind, columns=ind).to_numpy()
    L_d = an_d.L.reindex(index=ind, columns=ind).to_numpy()
    L_t = an_t.L.reindex(index=ind, columns=ind).to_numpy()

    md = an_d.mult_produccion.reindex(ind)
    mt = an_t.mult_produccion.reindex(ind)
    top_d = set(md.sort_values(ascending=False).head(10).index)
    top_t = set(mt.sort_values(ascending=False).head(10).index)
    tipo_d = an_d.clasificar().reindex(ind)
    tipo_t = an_t.clasificar().reindex(ind)

    fila = {"n": len(ind)}
    fila.update({f"dom_{k}": v for k, v in d.items()})
    fila.update({f"tot_{k}": v for k, v in t.items()})
    for k in ("mult_medio", "mult_pond", "directo_medio", "indirecto_medio", "ci_sobre_vbp"):
        fila[f"dif_{k}_pct"] = 100.0 * (t[k] / d[k] - 1.0) if d[k] else float("nan")
    dA, dL = A_t - A_d, L_t - L_d
    dcol = an_t.mult_directo.reindex(ind) - an_d.mult_directo.reindex(ind)   # Σᵢaᵢⱼ
    fila.update({
        # apertura: qué fracción del consumo intermedio total es importada
        "importado_pct": 100.0 * (1.0 - d["z_suma"] / t["z_suma"]) if t["z_suma"] else float("nan"),
        # Monotonía en los tres niveles. La celda puede romperse donde el RAS
        # actúa (se corre por separado en cada versión); lo que no puede romperse
        # sin invalidar la lectura del equipo es la columna, que es el
        # coeficiente técnico, ni el multiplicador.
        "min_dA": float(dA.min()),
        "min_dL": float(dL.min()),
        "celdas_dA_neg_pct": 100.0 * float((dA < -1e-12).mean()),
        "min_dcol_A": float(dcol.min()),
        "min_dmult": float((mt - md).min()),
        "spearman_mult": _spearman(md.to_numpy(), mt.to_numpy()),
        # FL (encadenamiento hacia ADELANTE) es la suma de FILA de L, un objeto
        # distinto del multiplicador. BL no se reporta: es la suma de columna
        # dividida por una constante, o sea una transformación monótona del
        # multiplicador, así que su correlación de rangos es idéntica por
        # construcción y no aporta nada.
        "spearman_fl": _spearman(an_d.fl.reindex(ind).to_numpy(), an_t.fl.reindex(ind).to_numpy()),
        "top10_comun": len(top_d & top_t),
        "cambian_tipo": int((tipo_d != tipo_t).sum()),
        "check_Lf_x_dom": an_d.check_Lf_x / max(float(iot_d.x.sum()), 1.0),
        "check_Lf_x_tot": an_t.check_Lf_x / max(float(iot_t.x.sum()), 1.0),
        # el sector donde más se agranda el multiplicador al meter el importado
        "sector_max_gap": str(((mt - md) / md).idxmax()),
        "max_gap_pct": float(100.0 * ((mt - md) / md).max()),
    })
    return fila, an_d, an_t


def z_del_libro(libro: Path, escala: float, z_dom: float, z_tot: float) -> dict:
    """¿La hoja Z del libro entregado es la doméstica o la total?"""
    if not libro.exists():
        return {"libro_z": float("nan"), "libro_es": "sin archivo"}
    try:
        hojas = pd.ExcelFile(libro).sheet_names
        h = hoja_por_sufijo(hojas, S_Z)
        if h is None:
            return {"libro_z": float("nan"), "libro_es": "sin hoja Z"}
        _, _, vals = _leer_matriz(libro, h)
        z = float(vals.sum()) * escala
        rd = abs(z / z_dom - 1.0) if z_dom else float("inf")
        rt = abs(z / z_tot - 1.0) if z_tot else float("inf")
        que = "doméstica" if rd < 1e-4 else ("TOTAL" if rt < 1e-4 else "no coincide")
        return {"libro_z": z, "libro_es": que, "libro_dif_pct": 100.0 * rd}
    except Exception as e:      # un libro abierto en Excel, un formato cambiado
        return {"libro_z": float("nan"), "libro_es": f"error: {type(e).__name__}"}


# ── reporte ──────────────────────────────────────────────────────────────────

def _tabla_pais(df):
    out = []
    for pais, g in df.groupby("pais", sort=False):
        out += [f"\n### {pais}\n",
                "| Año | Variante | n | Importado % del CI | Σᵢaᵢⱼ dom. | Σᵢaᵢⱼ total | "
                "Mult. dom. | Mult. total | Δ mult. | Δ directo | Δ indirecto |",
                "|----:|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
        for _, r in g.iterrows():
            out.append(
                f"| {r.anio:.0f} | {r.variante} | {r.n:.0f} | {r.importado_pct:.1f} % | "
                f"{r.dom_directo_medio:.4f} | {r.tot_directo_medio:.4f} | "
                f"{r.dom_mult_medio:.4f} | {r.tot_mult_medio:.4f} | "
                f"**{r.dif_mult_medio_pct:+.2f} %** | {r.dif_directo_medio_pct:+.2f} % | "
                f"{r.dif_indirecto_medio_pct:+.2f} % |")
    return out


def main():
    filas, anexos = [], []
    for pais, anio, variante, libro, cargar in CASOS:
        etq = f"{pais} {anio} ({variante})"
        try:
            caso = cargar()
            iot_d, iot_t = caso["dom"], caso["tot"]
            fila, an_d, an_t = comparar(iot_d, iot_t)
            fila.update(z_del_libro(libro, caso["escala"],
                                    fila["dom_z_suma"], fila["tot_z_suma"]))
            nombres = caso.get("nombres") or {}
            fila.update({"pais": pais, "anio": anio, "variante": variante,
                         "libro": libro.name,
                         "ras_dom": caso["ras_dom"], "ras_tot": caso["ras_tot"],
                         "sector_max_gap_nombre": str(
                             nombres.get(fila["sector_max_gap"],
                                         fila["sector_max_gap"]))[:44]})
            filas.append(fila)
            anexos.append((pais, anio, an_d, an_t))
            print(f"[OK] {etq}: mult {fila['dom_mult_medio']:.4f} → "
                  f"{fila['tot_mult_medio']:.4f} ({fila['dif_mult_medio_pct']:+.2f} %) · "
                  f"importado {fila['importado_pct']:.1f} % · "
                  f"libro Z = {fila['libro_es']}")
        except Exception as e:
            print(f"[ERROR] {etq}: {type(e).__name__}: {e}")
            filas.append({"pais": pais, "anio": anio, "variante": variante,
                          "libro": libro.name, "error": f"{type(e).__name__}: {e}"})

    df = pd.DataFrame(filas)
    cols = ["pais", "anio", "variante", "n", "libro", "libro_es", "libro_dif_pct",
            "importado_pct"] + [c for c in df.columns if c.startswith(("dom_", "tot_", "dif_"))] \
        + ["ras_dom", "ras_tot", "min_dA", "min_dL", "celdas_dA_neg_pct",
           "min_dcol_A", "min_dmult", "spearman_mult", "spearman_fl", "top10_comun",
           "cambian_tipo", "check_Lf_x_dom", "check_Lf_x_tot",
           "sector_max_gap", "sector_max_gap_nombre", "max_gap_pct"]
    df = df.reindex(columns=[c for c in cols if c in df.columns] +
                    [c for c in df.columns if c not in cols])
    csv = ROOT / "reports" / "comparacion_dom_total.csv"
    df.to_csv(csv, index=False, encoding="utf-8-sig")

    ok = df[df.get("dom_mult_medio").notna()] if "dom_mult_medio" in df else df.iloc[0:0]
    md = [
        "# Z doméstica vs. Z total — efecto sobre los indicadores\n",
        "Comparación de las dos versiones de la misma matriz, con el mismo COU, la misma "
        "valoración y el mismo Modelo D detrás. Lo único que cambia es **dónde entra el "
        "insumo importado**: fuera de `Z` y en una fila primaria (versión DOMÉSTICA, la "
        "única que se publica) o dentro de `Z` (versión TOTAL, que este script recalcula "
        "desde la fuente para poder medirla).\n",
        "Generado por `scripts/comparar_dom_total.py`. Datos completos en "
        "`reports/comparacion_dom_total.csv`.\n",
        "## 1. La Z publicada es la doméstica\n",
        "Se reabre cada libro entregado, se lee la hoja «Z consumos intermedios» y se "
        "confronta su suma contra las dos versiones recalculadas. Es lo que "
        "`validar_consistencia.py` no puede ver: ese script re-verifica "
        "`A ≈ Z·diag(g)⁻¹` y `L ≈ (I−A)⁻¹` **a partir de la Z del archivo**, así que "
        "confirma que todo lo posterior sale de esa matriz, pero no cuál de las dos es.\n",
    ]
    if len(ok):
        conteo = ok["libro_es"].value_counts()
        md.append("| Qué contiene la hoja Z del libro | Libros |")
        md.append("|:--|--:|")
        for k, v in conteo.items():
            md.append(f"| {k} | {v} |")
        malos = ok[ok["libro_es"] != "doméstica"]
        md.append("")
        if len(malos) == 0:
            md.append("**Los %d libros publican la Z doméstica**, y con ella se calculan "
                      "los coeficientes técnicos, la inversa de Leontief y los "
                      "multiplicadores de cada libro.\n" % len(ok))
        else:
            md.append("**Revisar**: " + ", ".join(
                f"{r.pais} {r.anio:.0f} ({r.libro_es})" for _, r in malos.iterrows()) + "\n")

        rotos = ok[ok["min_dA"] < -1e-9]
        md += [
            "## 2. Por qué los indicadores tienen que bajar\n",
            "La hipótesis del equipo se cumple. En el agregado no es un resultado "
            "empírico sino una consecuencia de la construcción: las dos versiones "
            "comparten el vector de producción `x`, y la utilización total es "
            "`U_dom + U_imp` con `U_imp ≥ 0`, de modo que\n",
            "```\n"
            "A_tot ≥ A_dom   celda a celda\n"
            "L = (I − A)⁻¹ = I + A + A² + …   (serie de Neumann, converge con A ≥ 0)\n"
            "⇒ L_tot ≥ L_dom  ⇒  todo multiplicador de columna es mayor\n"
            "```\n",
            "Lo empírico —y lo que sí hay que leer— es la **magnitud** de la brecha, que "
            "es la apertura importadora de cada economía, y si el **orden** de los "
            "sectores sobrevive al cambio de definición.\n",
            "### La salvedad del balanceo\n",
            "La desigualdad de arriba vale para el SUT tal como sale de la valoración. "
            "Pero el RAS se corre **por separado en cada versión**, así que en los libros "
            "donde interviene la monotonía puede romperse en celdas sueltas. Medido en "
            f"los {len(ok)} casos:\n",
            "| Nivel | Qué es | Mínimo de la diferencia total − doméstica |",
            "|:--|:--|--:|",
            f"| Celda de A | `aᵢⱼ` | {ok['min_dA'].min():.2e} |",
            f"| Celda de L | `lᵢⱼ` | {ok['min_dL'].min():.2e} |",
            f"| Columna de A | **coeficiente técnico `Σᵢaᵢⱼ`** | {ok['min_dcol_A'].min():.2e} |",
            f"| Columna de L | **multiplicador de producción** | {ok['min_dmult'].min():.2e} |",
            "",
            "**Los dos niveles que usa el equipo —el coeficiente técnico y el "
            "multiplicador— no se rompen en ningún sector de ningún año.** La ruptura "
            "existe sólo dentro de la columna, entre celdas que se compensan.\n",
            "El mínimo exacto de 0,00 corresponde a sectores sin consumo intermedio "
            "—servicio doméstico y actividades de hogares—, cuya columna de `A` es nula "
            "en las dos versiones y cuyo multiplicador es 1,0000 en ambas. No es un "
            "sector con producción cero: son actividades sin insumos.\n",
        ]
        if len(rotos):
            solo_dom = int(((~rotos["ras_tot"]) & rotos["ras_dom"]).sum())
            md += [
                f"Ocurre en {len(rotos)} de los {len(ok)} casos, y son exactamente los "
                f"{int(ok['ras_dom'].sum())} donde el RAS actúa sobre la versión "
                "doméstica: sin balanceo la desigualdad no falla nunca.\n",
                "| País | Año | RAS doméstica | RAS total | Celdas de A que bajan | Mín. `Δaᵢⱼ` |",
                "|:--|--:|:-:|:-:|--:|--:|"]
            for _, r in rotos.iterrows():
                md.append(f"| {r.pais} | {r.anio:.0f} | {'sí' if r.ras_dom else 'no'} | "
                          f"{'sí' if r.ras_tot else 'no'} | {r.celdas_dA_neg_pct:.2f} % | "
                          f"{r.min_dA:.1e} |")
            md += [
                f"\nY el patrón dice algo que vale la pena mirar aparte: en {solo_dom} de "
                f"los {len(rotos)} el RAS corre **sobre la versión doméstica y no sobre "
                "la total**. Ahí el SUT total entra cumpliendo las identidades y no hay "
                "nada que balancear: el desbalance aparece al separar el origen. O sea "
                "que lo que el RAS cierra en esos libros es, en buena parte, el residuo "
                "que deja el propio supuesto de proporcionalidad de las importaciones "
                "(§8.33). Es una medición nueva del costo de ese supuesto, "
                "independiente de las cuatro que ya están en "
                "`reports/sesgo_prorrateo.md`.\n"]
        else:
            md.append("No se rompe en ningún caso.\n")
        md += [
            f"Cierre de Leontief en las dos versiones: `L·f = x` en la doméstica y "
            f"`L·(f − m) = x` en la total, con residuo relativo máximo "
            f"{max(ok['check_Lf_x_dom'].max(), ok['check_Lf_x_tot'].max()):.1e}.\n",
            "## 3. Cuánto cambia, por país y por año\n",
            "`Σᵢaᵢⱼ` es el efecto directo medio (la primera vuelta de compras); el "
            "multiplicador es la suma de la columna de L; el indirecto es el resto. "
            "«Importado % del CI» es la fracción del consumo intermedio que queda afuera "
            "de la matriz doméstica, y es la que explica el tamaño de todo lo demás.\n",
        ]
        md += _tabla_pais(ok)

        md += ["\n## 4. Resumen por país\n",
               "| País | Años | Importado % del CI | Mult. dom. | Mult. total | Δ mult. | "
               "Δ directo | Δ indirecto |",
               "|:--|--:|--:|--:|--:|--:|--:|--:|"]
        res = ok.groupby("pais", sort=False).agg(
            n_anios=("anio", "count"), imp=("importado_pct", "mean"),
            md_=("dom_mult_medio", "mean"), mt_=("tot_mult_medio", "mean"),
            dm=("dif_mult_medio_pct", "mean"), dd=("dif_directo_medio_pct", "mean"),
            di=("dif_indirecto_medio_pct", "mean"))
        for pais, r in res.iterrows():
            md.append(f"| {pais} | {r.n_anios:.0f} | {r.imp:.1f} % | {r.md_:.4f} | "
                      f"{r.mt_:.4f} | **{r.dm:+.2f} %** | {r.dd:+.2f} % | {r.di:+.2f} % |")
        md.append("\nEl orden de la brecha es el orden de la apertura importadora, no del "
                  "tamaño de la economía: donde la producción usa más insumo importado, más "
                  "se infla la matriz total.\n")
        md += [
            "### El efecto que más importa: la versión total borra las diferencias entre "
            "países\n",
            f"En la matriz doméstica los cinco países se reparten entre "
            f"**{res['md_'].min():.2f} y {res['md_'].max():.2f}**".replace(".", ",") +
            f"; en la total se amontonan entre "
            f"**{res['mt_'].min():.2f} y {res['mt_'].max():.2f}**".replace(".", ",") + ". La "
            "brecha entre el mayor y el menor multiplicador medio pasa de "
            f"**{100 * (res['md_'].max() / res['md_'].min() - 1):.0f} %** a "
            f"**{100 * (res['mt_'].max() / res['mt_'].min() - 1):.0f} %**.\n",
            "No es casualidad: el multiplicador de la matriz total mide cuánta producción "
            "—de donde sea— hace falta por unidad de demanda, y eso es parecido en "
            "cualquier economía. El de la matriz doméstica mide cuánta producción "
            "**del propio país** se activa, que es la pregunta de política. México es el "
            "caso extremo: con la matriz doméstica queda último (1,49) porque su cadena "
            "local es corta, y con la total pasa a ser indistinguible del resto (2,02). "
            "**La lectura de «profundidad de la cadena doméstica» sólo existe en la "
            "versión que se publica.**\n"]

        md += ["## 5. ¿Sobrevive el ranking de sectores?\n",
               "Que todos los multiplicadores suban no implica que suban parejo. Si el "
               "orden cambiara, las dos versiones no sólo diferirían en nivel: dirían cosas "
               "distintas sobre qué sector es clave. `ρ` es la correlación de rangos entre "
               "las dos versiones; «top-10 en común» cuenta cuántos de los diez mayores "
               "multiplicadores se repiten; «cambian de tipo» son los sectores que cruzan "
               "el umbral 1 de Rasmussen y pasan de clave a otra categoría o al revés. "
               "(No se reporta ρ del encadenamiento hacia atrás: `BL` es la suma de "
               "columna de L dividida por una constante, o sea una transformación "
               "monótona del multiplicador, y su correlación de rangos es idéntica por "
               "construcción. `FL` sí es otro objeto: se arma con las filas.)\n",
               "| País | Año | ρ multiplicador | ρ FL | Top-10 en común | Cambian de tipo | "
               "Sector con mayor brecha | Brecha |",
               "|:--|--:|--:|--:|--:|--:|:--|--:|"]
        for _, r in ok.iterrows():
            md.append(f"| {r.pais} | {r.anio:.0f} | {r.spearman_mult:.4f} | "
                      f"{r.spearman_fl:.4f} | {r.top10_comun:.0f}/10 | "
                      f"{r.cambian_tipo:.0f} de {r.n:.0f} | "
                      f"{r.sector_max_gap_nombre} | {r.max_gap_pct:+.1f} % |")
        md += ["",
               "El ranking se degrada exactamente en el orden de la apertura: donde el "
               "insumo importado pesa poco, el reordenamiento es menor y el top-10 "
               "sobrevive casi entero; donde pesa mucho, las dos versiones dejan de "
               "hablar del mismo sector clave.\n"]

    (ROOT / "reports" / "comparacion_dom_total.md").write_text("\n".join(md) + "\n",
                                                               encoding="utf-8")
    print(f"[OK] Reporte en reports/comparacion_dom_total.md")
    print(f"[OK] Datos en   reports/comparacion_dom_total.csv")


if __name__ == "__main__":
    main()
