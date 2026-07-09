# Metodologia MIP V2/V3

## Objetivo

Construir un repositorio comparable de matrices insumo-producto para Argentina, Brasil, Mexico y Uruguay, usando fuentes oficiales de COU/MIP y dejando trazabilidad de los ajustes contables necesarios para el analisis de multiplicadores.

## Principios de procesamiento

1. Las matrices se trabajan a precios basicos cuando la fuente lo permite directamente.
2. La matriz `Z` se interpreta como consumo intermedio nacional o domestico.
3. El ajuste intermedio fuera de `Z` se conserva separado. En MIP directas puede ser consumo intermedio importado; en COU reconstruidos con puente comprador-basico puede incluir importaciones, margenes, impuestos y diferencias de valoracion.
4. La demanda final se conserva desde la fuente cuando existe y es compatible; se usa residual solo como fallback documentado.
5. Las actividades con demanda final residual negativa quedan marcadas como actividades a reconsiderar.
6. Antes de ajustar cifras se revisan parsers, columnas totales, codigos sectoriales y puentes de precios.
7. Los cierres menores solo se concilian cuando el negativo es pequeno, localizado y metodologicamente justificable.
8. Los multiplicadores de empleo solo se calculan cuando la fuente trae un vector de trabajo u ocupaciones.
9. Toda matriz publicada debe tener nombres de sectores economicos en filas y columnas. Los codigos se conservan como prefijo cuando existen, pero no reemplazan el nombre.

## Capa auditable V3

La V3 es la capa de publicacion contable y visual. No reemplaza el procesamiento base ni oculta alertas: reorganiza cada matriz en cuadros auditables para que el usuario vea en el mismo libro la matriz nacional/domestica, el ajuste intermedio importado o de valoracion, la demanda final, el valor agregado, la produccion total y los checks contra la fuente.

Cada libro V3 usa una estructura inspirada en el anexo MIP de Colombia, con paleta CEPAL y seis hojas: `Indice`, `Cuadro 1`, `Cuadro 2`, `Cuadro 3`, `Cuadro 4` y `Notas`. Los sectores con demanda final negativa, valor agregado negativo o ajuste intermedio negativo quedan marcados como alertas diagnosticas, no corregidos automaticamente.

## Matrices directas y reconstruidas

La base distingue dos rutas:

- **Matrices directas:** la fuente publica una MIP o matriz equivalente. Se parsea, normaliza, valida y empaqueta sin reconstruccion COU. En esta categoria estan Argentina 1997, Mexico 2003/2008/2013/2018 y Uruguay 2016.
- **Matrices reconstruidas:** la fuente publica cuadros de oferta y utilizacion. El pipeline reconstruye una MIP industria x industria usando el supuesto de tecnologia de industria. En esta categoria estan Argentina 2004/2018-2022, Brasil 2000-2021 y Uruguay 2012/2017.

Esta separacion permite responder que matrices vienen directamente de la fuente y cuales dependen de supuestos de transformacion.

## Identidades macro

Para cada pais y anio se revisan dos cierres:

```text
Oferta = demanda:
g_i = ventas_intermedias_nacionales_i + demanda_final_i

Valor agregado:
g_j = compras_intermedias_nacionales_j + consumo_intermedio_importado_j + valor_agregado_j
```

Donde:

- `g` es la produccion bruta por industria.
- `Z` son los flujos intermedios nacionales/domesticos.
- `ci_importado` es el consumo intermedio importado por industria compradora.
- `W` es el valor agregado.
- `f` es la demanda final domestica residual por industria.

## Conversion COU a MIP

Para paises que parten de cuadros de oferta y utilizacion, se usa el supuesto de tecnologia de industria:

```text
D = V * diag(q)^-1
Z = D * U_nacional
A = Z * diag(g)^-1
L = (I - A)^-1
f = D * y_domestica
```

Donde:

- `V` es la matriz de produccion/oferta por industria y producto.
- `q` es la produccion por producto.
- `U_nacional` es la utilizacion intermedia nacional por producto e industria.
- `A` es la matriz de coeficientes tecnicos.
- `L` es la inversa de Leontief.
- `D` distribuye cada producto entre industrias segun su participacion en la oferta del producto.
- `f` es la demanda final transformada a la clasificacion sectorial de la MIP cuando la fuente permite hacerlo.

Para las MIP directas, no se reconstruye `Z` desde `V` y `U`. Si existe un COU de referencia compatible, se adjunta para trazabilidad y para completar componentes que puedan alinearse con la MIP; si no existe correspondencia sectorial suficiente, no se fuerza la transformacion.

## Demanda final homologada

La hoja `y_demanda_final` separa el cierre sectorial de la MIP de una lectura macro homologada:

```text
XN = X - M
DA = C + I + G + XN
DA = C + I + G + (X - M)
```

Donde:

- `C_consumo` es consumo de hogares/privado e ISFLSH cuando la fuente lo identifica.
- `I_inversion` agrupa formacion bruta de capital fijo, variacion de existencias y objetos de valor.
- `G_gasto_publico` corresponde a consumo/gasto de gobierno.
- `X_exportaciones` son exportaciones totales.
- `M_importaciones` son importaciones finales estimadas o mapeadas cuando la fuente trae importaciones por producto.
- `XN_exportaciones_netas = X_exportaciones - M_importaciones`.
- `DA_C_I_G_XN = C + I + G + XN`.
- `y_demanda_final_total_mip` es el cierre sectorial usado por la MIP.
- `diferencia_y_mip_menos_DA` deja visible la diferencia entre el cierre de la MIP y la identidad homologada.

Si la fuente no trae desglose compatible, el total no se asigna artificialmente a consumo, inversion, gobierno o exportaciones. En esos casos se conserva en `sin_desglose_fuente`. Esto ocurre, por ejemplo, en MIP directas sin COU publico separado o en fuentes cuya demanda final esta en una clasificacion no homologable con seguridad.

## Ghosh y encadenamientos

Ademas de Leontief, cada Excel incluye:

```text
B = diag(x)^-1 * Z
G = (I - B)^-1
```

`B` normaliza cada fila de `Z` por la produccion del sector vendedor; por eso se interpreta como una matriz de distribucion de ventas. `G` es la inversa de Ghosh y permite una lectura de propagacion hacia adelante en ejercicios de oferta/costos.

Los encadenamientos no son la inversa completa en si misma, sino indicadores derivados de sus sumas:

- Encadenamiento hacia atras Leontief: suma por columnas de `L`.
- Indice hacia atras Leontief: suma por columnas de `L` dividida por el promedio.
- Encadenamiento hacia adelante Leontief: suma por filas de `L`.
- Encadenamiento hacia adelante Ghosh: suma por filas de `G`.
- Tambien se reporta suma por columnas de `G` como lectura complementaria.

## Correcciones aplicadas a matrices reconstruidas

Durante la auditoria se encontro que varios negativos de demanda final venian de la construccion, no necesariamente de cuentas nacionales. Las principales correcciones fueron:

- Argentina: exclusion de `UF`, porque es total de utilizacion final y no un componente adicional; alineacion de codigos equivalentes como `1512` y `15120`.
- Brasil 2010-2021: exclusion de `Total do produto`, `Demanda final` y `Demanda total` como sectores/componentes.
- Brasil 2000-2009: alineacion por posicion para preservar 51 actividades y exclusion de columnas agregadas.
- COU con puente comprador-basico: conversion de `U` e `Y` con factores publicados por producto, conservando demanda final fuente depurada.

Con estas correcciones Argentina reconstruida y Brasil 2010-2021 quedan sin demanda final negativa. Brasil 2001-2006 requirio ademas una conciliacion menor documentada.

## Conciliacion de cierre menor

La conciliacion no se aplica para ocultar problemas. Solo se usa cuando el negativo es pequeno frente a la produccion sectorial y hay una explicacion de cierre/redondeo. El procedimiento:

1. Se fija la produccion bruta `g`.
2. Se conserva `sum_col(Z)`, por lo tanto no se mueve el valor agregado residual.
3. La demanda final negativa se lleva a cero.
4. El cierre se redistribuye sobre sectores con demanda final positiva.
5. `Z` se ajusta con RAS para cumplir los nuevos totales de fila y los totales de columna originales.
6. Se recalculan `A` y `L`.

Cada archivo conciliado incluye:

- `ajuste_cierre`: demanda final original, demanda final final y ajuste por sector.
- `Z_pre_conciliacion`: matriz previa a la conciliacion.

Uruguay 2017 no se concilia porque los negativos son materiales. Se conserva como alerta hasta contar con demanda final fuente completa o una MIP directa 2017.

## Separacion nacional/importado

La prioridad es usar la apertura explicita de la fuente. Si existe matriz de utilizacion importada, se usa directamente.

Cuando solo existe un vector de importaciones por producto, el consumo intermedio importado se estima de manera proporcional:

```text
participacion_importada_p = M_p / (produccion_domestica_p + M_p)
U_importada_pj = U_total_pj * participacion_importada_p
U_nacional_pj = U_total_pj - U_importada_pj
```

Esta aproximacion queda documentada en las notas del COU procesado y en la PPT metodologica.

## Vector de trabajo

Cuando la fuente incluye ocupaciones por industria, el pipeline calcula multiplicadores de empleo:

```text
coef_empleo_i = ocupaciones_i / g_i
mult_empleo_j = coef_empleo' * L_j
```

Actualmente el vector esta disponible para Brasil 2000-2021 como `Fator trabalho (ocupacoes)`. En paises sin vector de trabajo, no se imputan ocupaciones.

## Validaciones

Cada archivo se valida con:

- Estructura cuadrada de `Z`, `A`, `L`.
- Etiquetas alineadas entre matrices y vectores.
- Nombres sectoriales descriptivos en filas y columnas.
- No negatividad central de `Z`, `A` y `g`.
- Consistencia `A = Z / g`.
- Consistencia `(I - A)L = I`.
- Cierre oferta-demanda.
- Cierre de valor agregado incluyendo `ci_importado`.
- Demanda final residual negativa como alerta diagnostica.

Los resultados se guardan en:

```text
output/tablas/validacion_matematica_mip.xlsx
output/tablas/validacion_matematica_mip.md
output/tablas/validacion_inversa_mip.xlsx
output/tablas/validacion_inversa_mip.md
```

## Estructura de entregables

Los Excel individuales por pais/anio se publican en una version auditable V3:

- `Indice`: portada, fuente, tipo de matriz y resumen de validaciones.
- `Cuadro 1`: matriz actividad x actividad nacional/domestica.
- `Cuadro 2`: matriz importada o ajuste intermedio fuera de `Z`.
- `Cuadro 3`: matriz total auditable con demanda final, ajuste, valor agregado, produccion total y check contra produccion fuente.
- `Cuadro 4`: multiplicadores de Leontief/Ghosh y validacion contable.
- `Notas`: convenciones, fuente y advertencias metodologicas.

Las validaciones, balances diagnosticos y auditorias de cobertura se conservan en archivos consolidados separados para no sobrecargar cada libro anual.

Los Excel consolidados por pais se guardan en:

```text
output/entregables/
```

El repositorio local de matrices se arma en:

```text
output/repositorio_matrices_mip/
output/matrices_insumo_producto_auditables/
```

## Limitaciones actuales

- Algunas series no publican una matriz importada por industria; en esos casos se usa una estimacion proporcional por producto.
- Algunas MIP directas no traen apertura importada historica; se conserva el dato publicado y se marca `ci_importado = 0` si no hay apertura.
- Las diferencias entre precios comprador y precios basicos se documentan cuando la fuente no permite una conversion exacta por componente de uso.
- Las actividades con demanda final residual negativa requieren revision economica o sectorial antes de uso analitico sensible.
- Uruguay 2012 y Uruguay 2017 quedan como casos con alertas diagnosticas: no se identifico una MIP directa equivalente para esos anios y el COU disponible no resuelve por completo la demanda final sectorial.
