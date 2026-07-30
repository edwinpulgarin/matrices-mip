# México — MIP 2013 reconstruida desde el COU de INEGI

Reemplaza a `mexico_pendiente.md`, que afirmaba que faltaba la hoja de utilización.
**Sí estaba**, en `data/raw/_cepal_staging/MEX_COU_2013/` (77 tabulados). Lo que
estaba roto eran las descargas sueltas de `data/raw/mexico/` (ver más abajo).

## Resultado

| Año | Nivel | Dim | VBP | VAB | fila=columna | L·f=x | min Z | mult. medio |
|----:|:------|----:|----:|----:|:---:|:---:|:---:|:---:|
| 2013 | rama SCIAN | 262×262 | 27.642.696 | 15.642.668 | 1,9e-15 | 4,2e-17 | 0,00 | **1,5174** |

Millones de pesos corrientes. VAB/VBP = 0,566. **El libro publicado se construye
sin ningún prorrateo.** Por el camino con proporcionalidad el multiplicador medio
daría 1,6032 (+5,65 %); esa versión se conserva como control en `mexico_todos.md`. El libro pasa las seis
verificaciones del auditor independiente (`validar_consistencia.py`): 30/30 libros.

## Datos usados

`_cepal_staging/MEX_COU_2013/` publica cada concepto en su propio tabulado, en
tres niveles SCIAN (sector / subsector / rama) y con corte doméstico / importado.
Se usa el nivel **rama**, el máximo detalle (262 ramas).

Identidades verificadas contra el dato antes de escribir el parser:

| Identidad | Resultado |
|:---|:---|
| OPC − MCT − impuestos netos == OPB | exacta |
| Σ producción por industria == total CAP | exacta |
| producción + I.CIF == OPB | exacta |
| Σ utilización por industria == DI | exacta |
| Σ componentes de demanda final == DF | exacta |
| Σ U a precios de comprador == INEGI | exacta (12.000.028) |

**Ajuste C.I.F./F.O.B.**: no es un componente de la oferta por producto. INEGI lo
registra en su propia fila, fuera del bloque de ramas, junto con las compras
directas en el exterior por residentes. Por eso el parser pone `Ajuste = 0` por
producto: sumarlo rompería `producción + I.CIF == OPB`. El residuo macro que deja
(−1,7e-4 relativo) lo absorbe el RAS del balanceo y queda reportado.

## Validación del supuesto de proporcionalidad — el hallazgo importante

México publica el corte doméstico/importado **explícito**, así que permite
contrastar el supuesto de proporcionalidad. Es la medición más limpia de las tres
que se hicieron (las otras son Brasil 2010/2015 y Uruguay 2016): misma fuente,
mismo nivel y misma clasificación, así que lo único que cambia entre las dos
versiones es el origen del insumo.

Consumo intermedio, millones de pesos corrientes:

| | Total | Doméstico | Importado |
|:---|---:|---:|---:|
| INEGI (explícito, precios básicos) | 11.990.569 | 8.091.685 (**67,5 %**) | 3.898.884 (**32,5 %**) |
| Este pipeline (proporcionalidad) | 11.883.904 | 9.362.070 (**78,8 %**) | 2.521.834 (**21,2 %**) |

El total a precios de comprador coincide **exactamente** con INEGI, y el total a
precios básicos difiere solo 0,9 % (tratamiento de impuestos y márgenes). Es decir:
**el desvío no viene de la valoración ni del parser, viene del supuesto de
proporcionalidad**, que asigna 78,8 % de origen doméstico donde la realidad es
67,5 % — once puntos porcentuales de más.

Dónde falla peor (productos con casi todo el insumo importado, a los que la
proporcionalidad les asigna oferta doméstica según su participación en la oferta total):

| Rama | Producto | Proporcionalidad | INEGI |
|:---|:---|---:|---:|
| 3343 | Fabricación de equipo de audio y de video | 75.060 | 66 |
| 3336 | Fabricación de motores de combustión interna | 49.308 | 702 |
| 3345 | Fabricación de instrumentos de medición | 30.586 | 594 |

Correlación celda a celda entre ambas matrices: 0,889.

### Qué implica

La proporcionalidad **sobreestima los encadenamientos domésticos y por lo tanto
los multiplicadores**. En México el sesgo es el más grande de los tres medidos
(+5,65 %) porque la manufactura de exportación importa casi todos sus insumos;
en Brasil, mucho más cerrado, es +1,34 % (2010) y +1,57 % (2015). Argentina no
tiene ninguna fuente con el corte explícito, así que su sesgo sigue sin poder
medirse — sólo acotarse por ese rango. Ver `sesgo_prorrateo.md`.

El Handbook admite la proporcionalidad como *fallback* cuando no hay matriz de
importaciones; cuando la hay, manda usarla. Para México la hay.

**Resuelto**: el libro publicado usa el corte explícito de INEGI, sin ningún
prorrateo. La versión por proporcionalidad se conserva como control de
comparabilidad en `mexico_todos.md`, y el sesgo consolidado de los tres países
donde se pudo medir está en `sesgo_prorrateo.md`.

## Basura en `data/raw/mexico/` (no tocada)

Induce a error — de hecho produjo el reporte anterior. Conviene borrarla:

- `cou_*.xlsx` (11 archivos, 2.263 bytes cada uno): páginas HTML de error de INEGI
  («Esta liga ya no existe»), no datos.
- `cou_matricial/`: directorio vacío.

## Pendiente

- Otros años: el staging solo trae el bloque de utilización completo para **2013**.
  `MEX_COU_2014_2020/` y `MEX_COU_2003_2012/` traen **solo OFERTA**. Para extender
  la serie hace falta bajar los tabulados de demanda de esos años.
- Contraste contra la MIP oficial de INEGI (`data/raw/mexico/mip_2013_csv.zip`),
  como se hizo con Uruguay.
