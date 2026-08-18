"""
Calcula los resultados que alimentan la presentación HTML y los deja en JSON.

Se separa del render a propósito: la presentación no debe recalcular nada, así
que cualquier cifra que aparezca ahí sale de acá y es reproducible corriendo
este script.

Uso:  py -3 scripts/resultados_presentacion.py
Genera: output/resultados.json
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import numpy as np

from src.balanceo import balancear
from src.transformacion import transformar
from src.analisis import calcular
from src.valoracion import valorar_argentina, ensamblar_directo
from src.demanda_final import armonizar, etiqueta, COLUMNAS
from src.parsers import argentina as p_ar, brasil as p_br, uruguay as p_uy
from src.parsers import mexico as p_mx, colombia as p_co
from src.parsers import brasil_mip as p_brmip

RAW = Path(r"c:/Users/edwin/Documents/MIP V2/data/raw")
NI = RAW / "Nueva_Info"
STG = RAW / "_cepal_staging"

# (país, año) -> cómo cargarlo. `limpio` = sin ningún prorrateo.
def _ar(a):
    f = {2004: "cou_2004.xls"}.get(a, f"cou_{a}.xls")
    return p_ar.parse(RAW / "argentina" / f, a), False

def _br(a):
    if a in (2010, 2015):
        return p_brmip.parse(RAW / "brasil", a), True
    return p_br.parse(RAW / "brasil", a), False

def _uy(a):
    # El tercer elemento es la carpeta con la utilización abierta en nacional e
    # importada, que el BCU publica sólo para 2017. Sin pasarla, 2017 se
    # construía por prorrateo y la presentación mostraba un multiplicador
    # (1,6689) que no era el del libro publicado (1,6023): justo la brecha que
    # mide el sesgo. Se carga igual que en `uruguay_libros.py`.
    src = {2012: (NI / "Uruguay_2012_Detallada_COU_C.xlsx", "COU_C", None),
           2016: (NI / "Uruguay_2016-2017 Detallada_COU_C.xlsx", "2016 CORRIENTE", None),
           2017: (NI / "Uruguay_2016-2017 Detallada_COU_C.xlsx", "2017 CORRIENTE",
                  RAW / "uruguay" / "cou_2017")}[a]
    # `limpio` sigue en False incluso en 2017: el BCU mide el ORIGEN pero no
    # publica impuestos ni márgenes celda a celda, así que la valoración sigue
    # siendo la del Cap. 7 (`valorar_argentina`, que toma el corte medido por
    # `dom_share_U`) y no el ensamblado directo.
    return p_uy.parse(src[0], a, hoja=src[1], carpeta_detalle=src[2]), False

def _mx(a):
    return p_mx.parse_sin_prorrateo(STG / f"MEX_COU_{a}", a), True

def _co(a):
    # sólo el COU: la MUPNI salió del camino de entrega
    return p_co.parse_cou(RAW / "colombia", a), False

PAISES = {
    "Argentina": {"anios": [2004, 2018, 2019, 2020, 2021, 2022, 2023], "foco": 2023,
                  "carga": _ar, "moneda": "pesos argentinos", "fuente": "INDEC"},
    "Brasil":    {"anios": list(range(2010, 2022)), "foco": 2015,
                  "carga": _br, "moneda": "reales", "fuente": "IBGE"},
    "Uruguay":   {"anios": [2012, 2016, 2017], "foco": 2017,
                  "carga": _uy, "moneda": "pesos uruguayos", "fuente": "BCU"},
    "México":    {"anios": [2013], "foco": 2013,
                  "carga": _mx, "moneda": "pesos mexicanos", "fuente": "INEGI"},
    "Colombia":  {"anios": list(range(2014, 2025)), "foco": 2023,
                  "carga": _co, "moneda": "pesos colombianos", "fuente": "DANE"},
}


def construir(d, limpio):
    sut, rep = (ensamblar_directo(d) if limpio else valorar_argentina(d))
    # La presentación tiene que mostrar exactamente la matriz que se publica, y
    # la que se publica es la DOMÉSTICA: Z lleva sólo insumo de origen nacional
    # y el importado va en fila primaria. Con eso el multiplicador vuelve a
    # medir profundidad de cadena doméstica, que es la lectura económica de la
    # presentación.
    sutb, _ = balancear(sut)
    iot = transformar(sutb, "D")
    return sut, sutb, iot, calcular(iot), rep


def resumen_anio(pais, anio, cfg):
    d, limpio = cfg["carga"](anio)
    sut, sutb, iot, an, rep = construir(d, limpio)
    vab = (rep["va_total"] if limpio else float(d["VA"].values.sum()))
    imp = float(rep.get("importado_total", 0.0))
    ci = float(sut.U.to_numpy().sum())
    vbp = float(sut.g.sum())
    # Todo lo que se publica es un RATIO. Los niveles están en moneda corriente
    # de cada país y año: el VBP de Argentina "crece" 40 veces entre 2004 y 2023
    # por inflación, no por producción, así que no es comparable ni entre años ni
    # entre países. Los ratios sí.
    f = iot.f.clip(lower=0)
    return {
        "anio": anio, "n": int(iot.Z.shape[0]),
        "mult_medio": float(an.mult_produccion.mean()),
        "mult_pond": an.mult_medio_ponderado(f),
        "mult_directo": float(an.mult_directo.mean()),
        "mult_indirecto": float(an.mult_indirecto.mean()),
        "va_sobre_vbp": (vab / vbp) if vbp else 0.0,
        "part_importada": (imp / (ci + imp)) if (ci + imp) else 0.0,
    }, (d, sut, sutb, iot, an, rep, limpio)


TIPOS_Q = ("Clave", "Demandante", "Distribuidor", "Independiente")


def detalle_foco(pais, anio, paquete):
    d, sut, sutb, iot, an, rep, limpio = paquete
    nombres = d["ind_name"]
    idx = an.bl.index
    g = iot.x.reindex(idx).fillna(0.0)
    share = (g / g.sum()) if g.sum() else g
    fd = iot.f.reindex(idx).fillna(0.0).clip(lower=0)
    share_fd = (fd / fd.sum()) if fd.sum() else fd
    va = iot.va.reindex(idx).fillna(0.0)
    share_va = (va / va.sum()) if va.sum() else va
    tipos = an.clasificar()

    sectores = []
    for k in idx:
        sectores.append({
            "cod": str(k), "nombre": str(nombres.get(k, k)),
            "bl": round(float(an.bl[k]), 4), "fl": round(float(an.fl[k]), 4),
            "vj": round(float(an.vj[k]), 4),
            "tipo": tipos[k], "share": round(float(share.get(k, 0.0)), 6),
            "share_va": round(float(share_va.get(k, 0.0)), 6),
            "share_fd": round(float(share_fd.get(k, 0.0)), 6),
            "mult": round(float(an.mult_produccion[k]), 4),
            "mult_dir": round(float(an.mult_directo[k]), 4),
            "mult_ind": round(float(an.mult_indirecto[k]), 4),
        })

    # composición de la demanda final armonizada
    Y = armonizar(iot.Y)
    tot = float(Y.to_numpy().sum()) or 1.0
    demanda = {etiqueta(c): round(float(Y[c].sum()) / tot, 4) for c in COLUMNAS
               if abs(float(Y[c].sum())) > 0}

    conteo = {t: int((tipos == t).sum()) for t in TIPOS_Q}
    peso = {t: round(float(share[tipos == t].sum()), 4) for t in conteo}
    peso_va = {t: round(float(share_va[tipos == t].sum()), 4) for t in conteo}

    m = an.mult_produccion
    # Sólo sectores con peso real: un sector de 0,01 % del VBP puede tener el
    # multiplicador más alto del país y no significa nada para política.
    relevantes = [s for s in sectores if s["share"] >= 0.002] or sectores
    por_mult = sorted(relevantes, key=lambda s: -s["mult"])
    # Candidatos a sector clave en sentido de política: arrastre alto Y disperso.
    claves = sorted([s for s in relevantes if s["tipo"] == "Clave"],
                    key=lambda s: (s["vj"], -s["bl"]))

    return {
        "sectores": sectores, "conteo": conteo,
        "peso_vbp": peso, "peso_va": peso_va, "demanda_final": demanda,
        "mult": {
            "medio": round(float(m.mean()), 4),
            "pond": round(an.mult_medio_ponderado(fd), 4),
            "mediana": round(float(m.median()), 4),
            "min": round(float(m.min()), 4), "max": round(float(m.max()), 4),
            "p90": round(float(m.quantile(0.90)), 4),
            "p10": round(float(m.quantile(0.10)), 4),
            "directo": round(float(an.mult_directo.mean()), 4),
            "indirecto": round(float(an.mult_indirecto.mean()), 4),
        },
        "top_mult": por_mult[:10],
        "bajo_mult": por_mult[-5:][::-1],
        "claves_dispersas": claves[:6],
        "check": float(an.check_Lf_x),
    }


def main():
    out = {"paises": {}}

    for pais, cfg in PAISES.items():
        serie, foco_pack = [], None
        for anio in cfg["anios"]:
            try:
                r, pack = resumen_anio(pais, anio, cfg)
                serie.append(r)
                if anio == cfg["foco"]:
                    foco_pack = pack
                print(f"  [{pais} {anio}] n={r['n']} mult={r['mult_medio']:.4f} "
                      f"(dir {r['mult_directo']:.3f} + ind {r['mult_indirecto']:.3f})")
            except Exception as e:
                print(f"  [ERROR {pais} {anio}] {type(e).__name__}: {e}")
        det = detalle_foco(pais, cfg["foco"], foco_pack) if foco_pack else {}
        out["paises"][pais] = {
            "fuente": cfg["fuente"], "moneda": cfg["moneda"],
            "anios": cfg["anios"], "foco": cfg["foco"], "serie": serie, **det,
        }

    ruta = ROOT / "output" / "resultados.json"
    ruta.parent.mkdir(exist_ok=True)
    ruta.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v["serie"]) for v in out["paises"].values())
    print(f"[OK] {ruta.relative_to(ROOT)} · {len(out['paises'])} países · {n} matrices")


if __name__ == "__main__":
    main()
