# Colombia — COU de DANE descargado (pendiente el parser)

**Archivo**: `data/raw/colombia/DANE_COU_2014_2024_corrientes.xlsx` (5,1 MB)
**Origen**: <https://www.dane.gov.co/files/operaciones/PIB/anex-CuentasNalANuales-OfertaUtilizacionPreciosCorrientes-2024p.xlsx>
**Contenido**: COU a precios corrientes, base 2015, **2014 a 2024p**, en dos niveles
(2 dígitos y 6 dígitos). Unidad: miles de millones de pesos.

Hay además una versión a precios constantes (`...PreciosConstantes-2024p.xlsx`),
no descargada.

## Mapa de hojas

45 hojas: `Índice` + `Cuadro 1..44`. Dos hojas por año-nivel (oferta, utilización):

| Nivel | Año | Oferta | Utilización |
|:---|---:|---:|---:|
| 2 dígitos | 2014 + k | Cuadro 1 + 2k | Cuadro 2 + 2k |
| 6 dígitos | 2014 + k | Cuadro 23 + 2k | Cuadro 24 + 2k |

Ejemplo: 2023 a seis dígitos = **Cuadro 41** (oferta) y **Cuadro 42** (utilización).

## Estructura (nivel 6 dígitos, verificada sobre 2023)

Encabezados en las filas 9-12; datos desde la fila 13. Productos = códigos CPC
Vers. 2 A.C. de 6 dígitos (~394). Industrias = 60 agrupaciones CIIU Rev. 4 A.C.

**Oferta (Cuadro 41)** — 417×135:

| Col | Contenido |
|---:|:---|
| 0, 1 | código CPC · concepto |
| 2 | Total oferta a precios de comprador |
| 3, 4 | márgenes de comercio · de transporte |
| 5 | impuestos y derechos a las importaciones |
| 6 | IVA no deducible |
| 7, 8 | impuestos a los productos · subvenciones |
| 9 | **oferta total a precios básicos** |
| 11–70 | producción por industria (60 columnas) |
| 72 | producción a precios básicos, total |
| 77 | ajuste CIF/FOB sobre importaciones |
| 78, 79 | importaciones de bienes · de servicios |

**Utilización (Cuadro 42)** — 425×138:

| Col | Contenido |
|---:|:---|
| 0, 1 | código CPC · concepto |
| 6–65 | consumo intermedio por industria (60 columnas) |
| 66 | total |
| 68–74 | CI a precios de comprador, **a precios básicos**, impuestos, subvenciones, márgenes, IVA |
| 76 | total gasto de consumo final |
| 78–84 | **hogares**: comprador, **básicos**, impuestos, subvenciones, márgenes, IVA |
| 86–92 | **ISFLSH**: mismo desglose |
| 94, 95 | gobierno **colectivo** · **individual** |
| 96–102 | gobierno total: mismo desglose |
| 104 | total formación bruta de capital |
| 105–111 | **FBKF**: mismo desglose |
| 113–119 | **variación de existencias**: mismo desglose |
| 129, 130 | **exportaciones**: bienes · servicios |
| 131–137 | totales y puente de valoración |

## Por qué esta fuente es la mejor de las cinco

1. **Trae cada componente ya a precios básicos**, columna por columna, con su
   puente de impuestos/subvenciones/márgenes/IVA. No hace falta el prorrateo
   proporcional que `valoracion.py` (Cap. 7) aplica a los otros cuatro países.
2. **Demanda final al máximo detalle**: hogares, ISFLSH e ISFLSH separadas del
   gobierno, y gobierno partido en colectivo e individual. Es el único país que
   permitiría la apertura C vs. G fina (ver `src/demanda_final.py`, donde se
   explica por qué el esquema armonizado igual colapsa el consumo: Uruguay y
   México no lo permiten).
3. **11 años** (2014–2024p) en un solo archivo.

## Pendiente

Escribir `src/parsers/colombia.py`. **No está hecho.** El sondeo rápido de este
documento usa cortes de columna aproximados y por eso las identidades cierran
solo a ~1 % (p. ej. `Σ industrias` vs. la columna de total difiere 2,5e4 sobre
2,7e6). Hay que detectar los límites de bloque por encabezado, como hace
`src/parsers/mexico.py`, no por índice fijo. También hay que resolver que oferta
y utilización traen distinta cantidad de filas de producto (394 vs. 396).

Decisión a tomar antes de escribirlo: aprovechar las columnas a precios básicos
que DANE ya entrega (más fiel, se salta el Cap. 7) o pasarlas por el mismo motor
que los demás (comparable). Es la misma disyuntiva que quedó abierta con México
en `reports/mexico_validacion.md`.
