# México — pendiente (situación de los datos)

El pipeline es idéntico al de los demás países; lo que falta es **ensamblar el COU
completo** de INEGI, porque las fuentes disponibles están fragmentadas:

- `data/raw/mexico/cou_*_b2013.xlsx` y `cou_*_b2018.xlsx` — **descargas fallidas**:
  el contenido es una página HTML de error de INEGI ("Esta liga ya no existe"),
  no datos.
- `MEX_COU_2014_2020.zip` — trae **solo la hoja de OFERTA** por año
  (`MEX_COU_AAAA_PRECIOSCORRIENTES_OFERTA.xlsx`); **falta la utilización**.
- `Nueva_Info/MeXICO_tabulados_cou.zip` — 76 archivos `COU_NN.xlsx` (tabulados por
  concepto/nivel; cada uno es HTML/Excel con "Utilización de bienes…" a distintos
  niveles de agregación). Requiere descifrar el esquema de numeración para emparejar
  oferta + utilización + valoración a un mismo nivel.
- `mip_2018_csv.zip`, `mip_2013_csv.zip` — **MIP oficiales** de INEGI (industria×industria
  y producto×producto). Útiles como **validación** (como Uruguay), no como insumo.

## Qué se necesita para completar México

1. Descargar/localizar la **hoja de utilización** (uso) del COU de INEGI a precios de
   comprador, con la matriz de producción (oferta) y el puente de valoración (márgenes,
   impuestos), para un año y nivel consistentes (p.ej. 2018 base 2013).
2. Escribir `src/parsers/mexico.py` que produzca la estructura canónica
   (`V_pi, U_pc, Y_pc, val, VA`), igual que `brasil.py`/`uruguay.py`.
3. Validar identidades y comparar contra la **MIP oficial 2018** (`mip_2018_csv.zip`).

Una vez con la utilización, México toma ~1 sesión (el motor ya está listo y probado).
