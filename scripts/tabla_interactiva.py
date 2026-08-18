"""
Tabla interactiva de control: una fila por matriz, con todo su detalle.

Cruza los CSV que ya emiten los controles y arma una página autocontenida —sin
dependencias externas, para que abra desde el disco o desde cualquier lado— con
la tabla ordenable, filtros por país y estado, buscador, y un panel de detalle
por matriz.

    manifest_publicables.csv           inventario y las siete verificaciones
    reports/estado_ras.csv             cómo se cerró el cuadro
    reports/cobertura.csv              ¿leímos toda la utilización publicada?
    reports/validacion_oficiales.csv   contraste contra la MIP del instituto

No calcula nada: si un número no está en esos CSV, no aparece.

Emite dos archivos, por la misma razón que la presentación:
    output/tabla_matrices.html            documento completo, abre en el navegador
    output/tabla_matrices_fragmento.html  sin <html>/<head>/<body>, para publicar

Uso:  py -3 scripts/tabla_interactiva.py
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def _leer(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _f(x, por_defecto=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return por_defecto


# Años en que cada instituto publica su propia matriz simétrica. Sin esto, una
# matriz quedaba castigada por «no contrastada» cuando no hay contra qué
# contrastarla: un requisito imposible de cumplir no es un requisito.
PUBLICAN_MIP = {
    "Argentina": {1997},
    "Brasil": {2010, 2015},
    "Colombia": {2015, 2017, 2019, 2021},
    "México": {2008, 2013, 2018},
    "Uruguay": {2016},
}


def _valoracion(metodo: str | None, oficial: bool) -> str:
    """Cómo se llevó el cuadro a precios básicos, dicho sin jerga.

    El inventario guarda la etiqueta técnica; acá se traduce a lo que
    efectivamente pasó con los datos, que es lo que el equipo necesita ver.
    """
    if oficial:
        return "la publica el instituto, ya construida"
    if (metodo or "").startswith("sin"):
        return "todo medido celda a celda"
    return "impuestos y márgenes repartidos dentro de cada fila"


def datos():
    libros = _leer(ROOT / "manifest_publicables.csv")
    ras = {(r["pais"], r["anio"]): r for r in _leer(ROOT / "reports" / "estado_ras.csv")}
    cob = {(r["pais"], r["anio"]): r for r in _leer(ROOT / "reports" / "cobertura.csv")}

    ofi = {}
    for r in _leer(ROOT / "reports" / "validacion_oficiales.csv"):
        ofi.setdefault(r["caso"], []).append(r)

    filas = []
    for lb in libros:
        pais, anio = lb["pais"], lb["anio"]
        pais_es = "México" if pais == "Mexico" else pais
        k = (pais_es, anio)
        r_ras, r_cob = ras.get(k, {}), cob.get(k, {})
        oficial = lb.get("variante") == "OFICIAL"

        modo = "matriz publicada" if oficial else r_ras.get("modo", "—")

        # Avance: cinco criterios, cada uno vale lo mismo. Los que no aplican
        # —el contraste, cuando el instituto no publica MIP de ese año— salen
        # del denominador en vez de contar como incumplidos. La fórmula está en
        # la página: un porcentaje que nadie puede reconstruir no sirve de nada.
        criterios = [
            ("Las siete verificaciones sobre el Excel",
             lb["estado"] == "CONSISTENTE", True),
            # Tampoco aplica a las oficiales: no hay COU que leer, la matriz
            # viene construida. Ojo que comparten (país, año) con la
            # reconstrucción del mismo año y heredaban su control.
            ("Leer toda la utilización que publica la fuente",
             r_cob.get("ok") == "si", not oficial and bool(r_cob)),
            ("Armarla sin modificar ninguna celda leída",
             oficial or modo in ("no hizo falta", "discrepancia"), True),
            # No aplica a las que publica el instituto —son la referencia— ni a
            # los años en que el instituto no publica matriz: pedir un contraste
            # imposible no es un requisito, es una penalización.
            ("Contrastarla contra la matriz del instituto",
             bool(ofi.get(f"{pais_es} {anio}")),
             not oficial and int(anio) in PUBLICAN_MIP.get(pais_es, set())),
        ]
        aplican = [c for c in criterios if c[2]]
        cumple = [c for c in aplican if c[1]]
        avance = round(100 * len(cumple) / len(aplican))
        falta = [c[0] for c in aplican if not c[1]]

        # Qué requisitos NO aplicaron y por qué. Sin esto, un 100 % sobre tres
        # requisitos se lee igual que un 100 % sobre cuatro, y no son lo mismo:
        # el primero llegó ahí porque la lista era más corta.
        no_aplican = []
        for etq, _, aplica in criterios:
            if aplica:
                continue
            if etq.startswith("Contrastarla"):
                no_aplican.append(
                    "es la matriz del instituto: no se contrasta contra sí misma"
                    if oficial else
                    f"el instituto no publica matriz de {anio}, no hay contra qué "
                    "contrastarla")
            elif etq.startswith("Leer toda"):
                no_aplican.append("no hay cuadro que leer: la matriz viene construida")
            else:
                no_aplican.append(etq)

        filas.append({
            "pais": pais_es,
            "anio": int(anio),
            "id": f"{pais_es} {anio}" + (" oficial" if oficial else ""),
            "variante": lb.get("variante", ""),
            "oficial": oficial,
            "dim": int(lb["dimension"]) if lb.get("dimension") else None,
            "valoracion": _valoracion(lb.get("metodo"), oficial),
            "archivo": lb.get("archivo", ""),
            "verificaciones": lb["estado"] == "CONSISTENTE",
            "modo": modo,
            "desbalance": _f(r_ras.get("desbalance")),
            "residuo": _f(r_ras.get("discrepancia"), 0.0),
            "mueve": _f(r_ras.get("mueve"), 0.0),
            "negativos": int(_f(r_ras.get("negativos"), 0) or 0),
            "filacol": _f(r_ras.get("fila_col")),
            "mult": _f(r_ras.get("mult")),
            "cobertura": None if oficial else r_cob.get("ok"),
            "contrastes": [{
                "objeto": c["objeto"],
                "n": int(_f(c["n"], 0) or 0),
                "dif": _f(c["dif_suma_pct"]),
                "corr": _f(c["correlacion"]),
                "desvio": _f(c["desvio_abs_pct"]),
            } for c in ([] if oficial else ofi.get(f"{pais_es} {anio}", []))],
            "falta": falta,
            "avance": avance,
            "cumple_n": len(cumple),
            "aplican_n": len(aplican),
            "no_aplican": no_aplican,
        })

    filas.sort(key=lambda r: (-r["avance"], r["pais"], r["anio"]))
    return filas


CSS = """
:root{
  --tinta:#10161F; --suave:#5A6675; --papel:#F6F8FB; --panel:#FFFFFF;
  --linea:#DCE3EC; --linea-fuerte:#B9C6D6;
  --azul:#0B4EA2; --azul-hondo:#17375E; --azul-tenue:#E8F0FA;
  --ok:#146B45; --ok-fondo:#E4F2EA;
  --aviso:#9A5B08; --aviso-fondo:#FBEEDC;
  --sombra:0 1px 2px rgba(16,22,31,.06), 0 8px 24px rgba(16,22,31,.05);
}
@media (prefers-color-scheme: dark){
  :root{
    --tinta:#E8EDF4; --suave:#95A3B4; --papel:#0E1218; --panel:#161C25;
    --linea:#273140; --linea-fuerte:#3A475A;
    --azul:#6BA5EC; --azul-hondo:#9CC2F0; --azul-tenue:#17222F;
    --ok:#5FD09B; --ok-fondo:#122A1F;
    --aviso:#E2A44B; --aviso-fondo:#2A2114;
    --sombra:0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
  }
}
:root[data-theme="dark"]{
  --tinta:#E8EDF4; --suave:#95A3B4; --papel:#0E1218; --panel:#161C25;
  --linea:#273140; --linea-fuerte:#3A475A;
  --azul:#6BA5EC; --azul-hondo:#9CC2F0; --azul-tenue:#17222F;
  --ok:#5FD09B; --ok-fondo:#122A1F;
  --aviso:#E2A44B; --aviso-fondo:#2A2114;
  --sombra:0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
}
:root[data-theme="light"]{
  --tinta:#10161F; --suave:#5A6675; --papel:#F6F8FB; --panel:#FFFFFF;
  --linea:#DCE3EC; --linea-fuerte:#B9C6D6;
  --azul:#0B4EA2; --azul-hondo:#17375E; --azul-tenue:#E8F0FA;
  --ok:#146B45; --ok-fondo:#E4F2EA;
  --aviso:#9A5B08; --aviso-fondo:#FBEEDC;
  --sombra:0 1px 2px rgba(16,22,31,.06), 0 8px 24px rgba(16,22,31,.05);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--papel); color:var(--tinta);
  font-family:"Segoe UI",-apple-system,BlinkMacSystemFont,Roboto,"Helvetica Neue",Arial,sans-serif;
  font-size:15px; line-height:1.5;
}
.envoltura{max-width:1180px; margin:0 auto; padding:0 24px 72px}

.barra-inst{height:6px; background:var(--azul)}
header.cabecera{padding:34px 0 22px; border-bottom:1px solid var(--linea)}
h1{
  margin:0; font-size:31px; font-weight:700; letter-spacing:-.022em;
  text-wrap:balance;
}
.bajada{margin:8px 0 0; color:var(--suave); max-width:66ch}
.sello{
  display:inline-block; margin-bottom:12px; font-size:11px; font-weight:700;
  letter-spacing:.1em; text-transform:uppercase; color:var(--azul);
}

.fichas{display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:26px 0 28px}
@media (max-width:820px){.fichas{grid-template-columns:repeat(2,1fr)}}
.ficha{
  background:var(--panel); border:1px solid var(--linea); border-radius:10px;
  padding:16px 18px; box-shadow:var(--sombra);
}
.ficha .n{
  font-size:32px; font-weight:700; letter-spacing:-.03em; line-height:1.05;
  font-variant-numeric:tabular-nums;
}
.ficha .r{
  margin-top:4px; font-size:11px; text-transform:uppercase; letter-spacing:.08em;
  color:var(--suave); font-weight:600;
}
.ficha.acento .n{color:var(--azul)}
.ficha.buena .n{color:var(--ok)}
.ficha.ojo .n{color:var(--aviso)}

.controles{display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:14px}
input[type="search"], select{
  font:inherit; font-size:14px; color:var(--tinta); background:var(--panel);
  border:1px solid var(--linea-fuerte); border-radius:8px; padding:8px 12px;
}
input[type="search"]{min-width:230px}
input:focus-visible, select:focus-visible, .chip:focus-visible, tr.fila:focus-visible{
  outline:2px solid var(--azul); outline-offset:2px;
}
.chips{display:flex; flex-wrap:wrap; gap:6px}
.chip{
  font:inherit; font-size:13px; cursor:pointer; padding:7px 13px; border-radius:999px;
  border:1px solid var(--linea-fuerte); background:var(--panel); color:var(--suave);
}
.chip[aria-pressed="true"]{background:var(--azul); border-color:var(--azul); color:#fff; font-weight:600}
.cuenta{margin-left:auto; font-size:13px; color:var(--suave); font-variant-numeric:tabular-nums}

.marco{
  background:var(--panel); border:1px solid var(--linea); border-radius:10px;
  box-shadow:var(--sombra); overflow-x:auto;
}
table{border-collapse:collapse; width:100%; font-size:13.5px}
thead th{
  position:sticky; top:0; z-index:2; background:var(--azul-hondo); color:#fff;
  text-align:left; font-size:11px; letter-spacing:.06em; text-transform:uppercase;
  font-weight:600; padding:11px 12px; white-space:nowrap; cursor:pointer;
  user-select:none;
}
thead th:hover{background:var(--azul)}
thead th .fl{opacity:.45; margin-left:5px; font-size:10px}
thead th[aria-sort] .fl{opacity:1}
td{padding:10px 12px; border-top:1px solid var(--linea); vertical-align:middle}
.num{text-align:right; font-variant-numeric:tabular-nums}
tr.fila{cursor:pointer}
tr.fila:hover td{background:var(--azul-tenue)}
tr.fila[aria-expanded="true"] td{background:var(--azul-tenue); font-weight:600}
.pais{font-weight:600; white-space:nowrap}
.anio{font-variant-numeric:tabular-nums; color:var(--suave)}

.pin{
  display:inline-flex; align-items:center; gap:6px; font-size:11.5px; font-weight:600;
  padding:3px 9px; border-radius:999px; white-space:nowrap;
}
.pin.ok{background:var(--ok-fondo); color:var(--ok)}
.pin.ojo{background:var(--aviso-fondo); color:var(--aviso)}
.pin::before{content:""; width:6px; height:6px; border-radius:50%; background:currentColor}

tr.detalle td{background:var(--papel); padding:0; border-top:0}
.panel{padding:20px 22px 24px; display:grid; gap:20px; grid-template-columns:1.1fr 1fr}
@media (max-width:820px){.panel{grid-template-columns:1fr}}
.panel h3{
  margin:0 0 10px; font-size:11px; letter-spacing:.09em; text-transform:uppercase;
  color:var(--suave); font-weight:700;
}
dl{margin:0; display:grid; grid-template-columns:auto 1fr; gap:7px 16px; font-size:13.5px}
dt{color:var(--suave)}
dd{margin:0; text-align:right; font-variant-numeric:tabular-nums}
.pendiente{
  margin-top:14px; padding:11px 14px; border-radius:8px; font-size:13.5px;
  background:var(--aviso-fondo); color:var(--aviso); border:1px solid currentColor;
}
.pendiente b{display:block; margin-bottom:3px}
.ruta{
  margin-top:12px; font-size:12px; color:var(--suave); word-break:break-all;
  font-family:ui-monospace,SFMono-Regular,Consolas,monospace;
}
table.mini{width:100%; font-size:13px; border-collapse:collapse}
table.mini th{
  text-align:left; font-size:10.5px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--suave); padding:0 8px 6px 0; font-weight:700; background:none; position:static;
}
table.mini td{padding:5px 8px 5px 0; border-top:1px solid var(--linea)}
.avance{display:flex; align-items:center; gap:9px; min-width:132px}
.pista{flex:1; height:7px; border-radius:99px; background:var(--linea); overflow:hidden}
.pista i{display:block; height:100%; background:var(--azul); border-radius:99px;
  transition:width .28s ease}
@media (prefers-reduced-motion:reduce){.pista i{transition:none}}
.pista i.casi{background:var(--aviso)}
.pista i.llena{background:var(--ok)}
.pc{font-size:12.5px; font-variant-numeric:tabular-nums; color:var(--suave);
  min-width:38px; text-align:right}
.de{font-size:11px; font-variant-numeric:tabular-nums; color:var(--suave);
  opacity:.72; min-width:26px}

.visto{
  font:inherit; font-size:12px; font-weight:600; cursor:pointer; white-space:nowrap;
  padding:5px 11px; border-radius:999px; border:1px dashed var(--linea-fuerte);
  background:transparent; color:var(--suave);
}
.visto:hover{border-style:solid; color:var(--azul); border-color:var(--azul)}
.visto.si{background:var(--ok-fondo); border:1px solid var(--ok); color:var(--ok)}
.visto:focus-visible{outline:2px solid var(--azul); outline-offset:2px}

.pendiente ul{margin:6px 0 0; padding-left:18px}
.pendiente li{margin:2px 0}
.listo{
  margin-top:14px; padding:11px 14px; border-radius:8px; font-size:13.5px;
  background:var(--ok-fondo); color:var(--ok); border:1px solid currentColor;
}
.listo b{display:block; margin-bottom:2px}
.noaplica{
  margin-top:10px; padding:10px 14px; border-radius:8px; font-size:13px;
  border:1px dashed var(--linea-fuerte); color:var(--suave);
}
.noaplica b{display:block; margin-bottom:3px; color:var(--tinta)}
.noaplica ul{margin:4px 0 0; padding-left:18px}
.vacio{color:var(--suave); font-size:13.5px; font-style:italic}
footer{margin-top:26px; font-size:12.5px; color:var(--suave)}
footer code{font-size:12px}
"""

JS = r"""
const DATOS = __DATOS__;
const $ = (s, e=document) => e.querySelector(s);
const num = (v, d=4) => v === null || v === undefined ? "—" : v.toFixed(d);
const pct = (v, d=3) => v === null || v === undefined ? "—" : (v*100).toFixed(d) + " %";
const exp = v => v === null || v === undefined ? "—" : v.toExponential(1).replace("e", "e");

let orden = {col:"avance", asc:false};   // primero las más cerca de cerrar
let filtros = {pais:"todos", estado:"todos", texto:""};
let abierta = null;

const COLS = [
  {k:"pais",  t:"País",           v:r=>`<span class="pais">${r.pais}</span>`},
  {k:"anio",  t:"Año",            v:r=>`<span class="anio">${r.anio}</span>`, num:true},
  {k:"dim",   t:"Dim.",           v:r=>r.dim ? `${r.dim}×${r.dim}` : "—", num:true},
  {k:"modo",  t:"Cómo se cerró",  v:r=>etiquetaModo(r)},
  {k:"avance",t:"Avance",         v:r=>barra(r)},
  {k:"filacol", t:"Fila = columna", v:r=>exp(r.filacol), num:true},
  {k:"mult",  t:"Multiplicador",  v:r=>num(r.mult), num:true},
  {k:"visto", t:"Visto del equipo", v:r=>casilla(r)},
];

// El visto bueno del equipo vive en el navegador de quien revisa: la página es
// estática y no hay dónde guardarlo del otro lado. Es lo que hace falta para
// ir marcando durante la reunión.
const CLAVE = "mip.vistos";
let vistos = new Set(JSON.parse(localStorage.getItem(CLAVE) || "[]"));
const guardar = () => localStorage.setItem(CLAVE, JSON.stringify([...vistos]));

// El avance mide lo verificable; el visto del equipo es una decisión de
// personas y se cuenta aparte. Mezclarlos en un solo número dejaba a Colombia
// en 80 % teniendo todos sus controles en verde.
const avanceDe = r => r.avance;

function barra(r){
  const a = Math.min(100, avanceDe(r));
  const cl = a >= 100 ? "llena" : a >= 80 ? "casi" : "";
  return `<div class="avance"><div class="pista"><i class="${cl}" style="width:${a}%"></i></div>
          <span class="pc">${a} %</span>
          <span class="de">${r.cumple_n}/${r.aplican_n}</span></div>`;
}

function casilla(r){
  const m = vistos.has(r.id);
  return `<button class="visto ${m ? "si" : ""}" data-visto="${r.id}"
            aria-pressed="${m}" title="Marcar como revisada por el equipo">
            ${m ? "✓ revisada" : "marcar"}</button>`;
}

function etiquetaModo(r){
  const m = {
    "no hizo falta":"cerraba solo",
    "discrepancia":"sin tocar celdas",
    "RAS":"RAS",
    "matriz publicada":"publicada por el instituto",
  }[r.modo] || r.modo;
  return m;
}

function visibles(){
  const t = filtros.texto.trim().toLowerCase();
  let f = DATOS.filter(r =>
    (filtros.pais === "todos" || r.pais === filtros.pais) &&
    (filtros.estado === "todos"
      || (filtros.estado === "completa" && avanceDe(r) >= 100)
      || (filtros.estado === "curso" && avanceDe(r) < 100)
      || (filtros.estado === "sinvisto" && !vistos.has(r.id))) &&
    (!t || r.id.toLowerCase().includes(t) || r.valoracion.toLowerCase().includes(t)
        || etiquetaModo(r).toLowerCase().includes(t))
  );
  const c = orden.col;
  const val = (r) => c === "avance" ? avanceDe(r)
                   : c === "visto"  ? (vistos.has(r.id) ? 1 : 0)
                   : r[c];
  f.sort((a,b) => {
    let x = val(a), y = val(b);
    if (x === null || x === undefined) x = -Infinity;
    if (y === null || y === undefined) y = -Infinity;
    if (typeof x === "string") return orden.asc ? x.localeCompare(y) : y.localeCompare(x);
    return orden.asc ? x - y : y - x;
  });
  return f;
}

function detalle(r){
  const contrastes = r.contrastes.length
    ? `<table class="mini"><thead><tr><th>Objeto</th><th>n</th><th>Dif. suma</th>
         <th>Correlación</th><th>Desvío</th></tr></thead><tbody>` +
      r.contrastes.map(c => `<tr><td>${c.objeto}</td><td>${c.n}</td>
        <td class="num">${c.dif.toFixed(4)} %</td>
        <td class="num">${c.corr.toFixed(4)}</td>
        <td class="num">${c.desvio.toFixed(2)} %</td></tr>`).join("") +
      `</tbody></table>`
    : r.oficial
      ? `<p class="vacio">Es la matriz que publica el instituto: es la referencia contra
         la que se contrastan las demás, no se compara contra sí misma.</p>`
      : `<p class="vacio">El instituto no publica una matriz para este año, o falta bajar
         el anexo para contrastarla.</p>`;

  const pend = r.falta.length
    ? `<div class="pendiente"><b>Falta para llegar al 100 %</b>` +
      `<ul>${r.falta.map(f => `<li>${f}</li>`).join("")}</ul></div>`
    : vistos.has(r.id)
      ? `<div class="listo"><b>Cerrada.</b> Pasó todos los controles que le
         corresponden y tiene el visto del equipo.</div>`
      : `<div class="listo"><b>Técnicamente lista.</b> Pasó todos los controles que le
         corresponden. Falta sólo el visto del equipo.</div>`;

  return `<div class="panel">
    <div>
      <h3>Cómo se armó</h3>
      <dl>
        <dt>Cómo se llevó a precios básicos</dt><dd>${r.valoracion}</dd>
        <dt>Cierre del cuadro</dt><dd>${etiquetaModo(r)}</dd>
        <dt>Desbalance al entrar</dt><dd>${exp(r.desbalance)}</dd>
        <dt>Residuo anotado aparte</dt><dd>${r.oficial ? "—" : pct(r.residuo)}</dd>
        <dt>Celdas movidas por el RAS</dt><dd>${r.oficial ? "—" : pct(r.mueve)}</dd>
        <dt>Negativos de la fuente conservados</dt><dd>${r.negativos || "—"}</dd>
      </dl>
      <h3 style="margin-top:18px">Controles</h3>
      <dl>
        <dt>Siete verificaciones sobre el Excel</dt>
        <dd>${r.verificaciones ? "pasa" : "no pasa"}</dd>
        <dt>Cobertura de la fuente</dt>
        <dd>${r.cobertura === "si" ? "completa" : r.cobertura === "no" ? "revisar" : "—"}</dd>
        <dt>Fila = columna</dt><dd>${exp(r.filacol)}</dd>
        <dt>Multiplicador medio</dt><dd>${num(r.mult)}</dd>
      </dl>
      ${pend}
      ${r.no_aplican.length ? `<div class="noaplica"><b>No le aplican</b>
        <ul>${r.no_aplican.map(x => `<li>${x}</li>`).join("")}</ul></div>` : ""}
      <p class="ruta">${r.archivo}</p>
    </div>
    <div>
      <h3>Contra la matriz que publica el instituto</h3>
      ${contrastes}
    </div>
  </div>`;
}

function pintar(){
  const f = visibles();
  const cuerpo = $("#cuerpo");
  cuerpo.innerHTML = f.map(r => {
    const ab = abierta === r.id;
    const celdas = COLS.map(c =>
      `<td class="${c.num ? "num" : ""}">${c.v(r)}</td>`).join("");
    return `<tr class="fila" tabindex="0" data-id="${r.id}" aria-expanded="${ab}">${celdas}</tr>` +
      (ab ? `<tr class="detalle"><td colspan="${COLS.length}">${detalle(r)}</td></tr>` : "");
  }).join("");
  const completas = DATOS.filter(r => avanceDe(r) >= 100).length;
  const medio = Math.round(DATOS.reduce((a, r) => a + Math.min(100, avanceDe(r)), 0) / DATOS.length);
  $("#cuenta").textContent = `${f.length} de ${DATOS.length} matrices`;
  $("#n-completas").textContent = completas;
  $("#n-medio").textContent = medio + " %";
  $("#n-vistos").textContent = vistos.size;
  document.querySelectorAll("thead th").forEach(th => {
    const k = th.dataset.col;
    if (k === orden.col) th.setAttribute("aria-sort", orden.asc ? "ascending" : "descending");
    else th.removeAttribute("aria-sort");
    const fl = th.querySelector(".fl");
    if (fl) fl.textContent = k === orden.col ? (orden.asc ? "▲" : "▼") : "◆";
  });
}

function alternar(id){
  abierta = abierta === id ? null : id;
  pintar();
}

document.addEventListener("click", e => {
  const th = e.target.closest("thead th");
  if (th){
    const k = th.dataset.col;
    orden = {col:k, asc: orden.col === k ? !orden.asc : true};
    return pintar();
  }
  const btn = e.target.closest("[data-visto]");
  if (btn){
    const id = btn.dataset.visto;
    vistos.has(id) ? vistos.delete(id) : vistos.add(id);
    guardar();
    return pintar();
  }
  const tr = e.target.closest("tr.fila");
  if (tr) return alternar(tr.dataset.id);
  const chip = e.target.closest(".chip");
  if (chip){
    const [campo, valor] = [chip.dataset.campo, chip.dataset.valor];
    filtros[campo] = valor;
    document.querySelectorAll(`.chip[data-campo="${campo}"]`).forEach(c =>
      c.setAttribute("aria-pressed", c.dataset.valor === valor));
    pintar();
  }
});
document.addEventListener("keydown", e => {
  if ((e.key === "Enter" || e.key === " ") && e.target.matches("tr.fila")){
    e.preventDefault();
    alternar(e.target.dataset.id);
  }
});
$("#buscar").addEventListener("input", e => { filtros.texto = e.target.value; pintar(); });

pintar();
"""


def html(filas):
    paises = sorted({r["pais"] for r in filas})
    sin_ras = sum(1 for r in filas if r["modo"] in ("no hizo falta", "discrepancia"))
    medidas = sum(1 for r in filas if not r["oficial"])

    chips_pais = "".join(
        f'<button class="chip" data-campo="pais" data-valor="{p}" '
        f'aria-pressed="false">{p}</button>' for p in paises)

    encabezados = "".join(
        f'<th data-col="{c}" scope="col">{t}<span class="fl">◆</span></th>'
        for c, t in [("pais", "País"), ("anio", "Año"), ("dim", "Dim."),
                     ("modo", "Cómo se cerró"), ("avance", "Avance"),
                     ("filacol", "Fila = columna"), ("mult", "Multiplicador"),
                     ("visto", "Visto del equipo")])

    cuerpo_js = JS.replace("__DATOS__", json.dumps(filas, ensure_ascii=False))

    return f"""<style>{CSS}</style>
<div class="barra-inst"></div>
<div class="envoltura">
  <header class="cabecera">
    <span class="sello">Matrices insumo-producto · control de calidad</span>
    <h1>Las {len(filas)} matrices, una por una</h1>
    <p class="bajada">Cada fila es una matriz publicada. Hacé clic para ver cómo se armó,
      qué controles pasó y cómo se compara contra la matriz que publica el instituto.
      Las columnas ordenan; los filtros acotan.</p>
  </header>

  <section class="fichas">
    <div class="ficha acento"><div class="n" id="n-medio">—</div>
      <div class="r">Avance promedio</div></div>
    <div class="ficha buena"><div class="n" id="n-completas">—</div>
      <div class="r">Técnicamente al 100 %</div></div>
    <div class="ficha ojo"><div class="n" id="n-vistos">—</div>
      <div class="r">Cerradas por el equipo</div></div>
    <div class="ficha"><div class="n">{sin_ras}<span style="font-size:18px">/{medidas}</span></div>
      <div class="r">Sin modificar una celda</div></div>
  </section>

  <div class="controles">
    <input id="buscar" type="search" placeholder="Buscar país, año o método…"
           aria-label="Buscar">
    <div class="chips">
      <button class="chip" data-campo="pais" data-valor="todos"
              aria-pressed="true">Todos</button>{chips_pais}
    </div>
    <div class="chips">
      <button class="chip" data-campo="estado" data-valor="todos"
              aria-pressed="true">Todas</button>
      <button class="chip" data-campo="estado" data-valor="completa"
              aria-pressed="false">Al 100 %</button>
      <button class="chip" data-campo="estado" data-valor="curso"
              aria-pressed="false">Les falta algo</button>
      <button class="chip" data-campo="estado" data-valor="sinvisto"
              aria-pressed="false">Sin visto</button>
    </div>
    <span class="cuenta" id="cuenta"></span>
  </div>

  <div class="marco">
    <table>
      <thead><tr>{encabezados}</tr></thead>
      <tbody id="cuerpo"></tbody>
    </table>
  </div>

  <footer>
    <p><strong>Cómo se calcula el avance.</strong> Cuatro requisitos verificables, cada
      uno vale lo mismo: pasar las siete verificaciones sobre el Excel, leer toda la
      utilización que publica la fuente, armarla sin modificar ninguna celda leída, y
      contrastarla contra la matriz del instituto. Los que no aplican salen del
      denominador: no se penaliza a una matriz por no tener contra qué compararse
      cuando el instituto no publica matriz de ese año, ni a las matrices oficiales por
      no compararse contra sí mismas. Cada fila dice exactamente qué le falta.</p>
    <p><strong>El visto del equipo va aparte, a propósito.</strong> El avance mide lo
      que se puede verificar solo; el visto es una decisión de personas. Mezclarlos en
      un mismo número deja a una matriz impecable en 80 % por una firma que falta.</p>
    <p><strong>Cómo se cerró el cuadro.</strong> «Cerraba solo»: el cuadro publicado ya
      cumple las dos identidades contables. «Sin tocar celdas»: quedó un residuo chico y
      se anotó aparte, en su propia columna de demanda final, sin modificar ningún dato
      leído. «RAS»: el ajuste del Cap. 11 del Handbook, que sí reescribe celdas — hoy
      sólo lo necesitan dos matrices.</p>
    <p><strong>Las marcas del equipo se guardan en este navegador.</strong> La página es
      estática y no hay servidor donde dejarlas: si se abre en otra máquina, hay que
      volver a marcar.</p>
    <p>Se genera con <code>py -3 scripts/tabla_interactiva.py</code> a partir de
      <code>manifest_publicables.csv</code>, <code>estado_ras.csv</code>,
      <code>cobertura.csv</code> y <code>validacion_oficiales.csv</code>. No recalcula
      nada: si un número no está en esos archivos, acá no aparece.</p>
  </footer>
</div>
<script>{cuerpo_js}</script>"""


def main():
    filas = datos()
    frag = html(filas)
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    (out / "tabla_matrices_fragmento.html").write_text(frag, encoding="utf-8")
    completo = ("<!doctype html>\n<html lang=\"es\">\n<head>\n"
                "<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                "<title>Matrices insumo-producto · control de calidad</title>\n"
                "</head>\n<body>\n" + frag + "\n</body>\n</html>\n")
    (out / "tabla_matrices.html").write_text(completo, encoding="utf-8")
    print(f"[OK] output/tabla_matrices.html  ({len(filas)} matrices)")
    print(f"[OK] output/tabla_matrices_fragmento.html  (para publicar)")


if __name__ == "__main__":
    main()
