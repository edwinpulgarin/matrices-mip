# Metodologia MIP V2

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

## Matrices directas y reconstruidas

La base distingue dos rutas:

- **Matrices directas:** la fuente publica una MIP o matriz equivalente. Se parsea, normaliza, valida y empaqueta sin reconstruccion COU. En esta categoria estan Argentina 1997, Mexico 2003/2008/2013/2018 y Uruguay 2016.
- **Matrices reconstruidas:** la fuente publica cuadros de oferta y utilizacion. El pipeline reconstruye una MIP industria x industria usando el supuesto de tecnologia de industria. En esta categoria estan Argentina 2004/2018-2022, Brasil 2000-2021 y Uruguay 2017.

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
```

## Estructura de entregables

Los Excel individuales por pais/anio se publican en una version simplificada para lectura:

- `Indice`
- `COU_Tabla_Original`
- `Z_consumos_intermedios`
- `x_produccion_bruta`
- `y_demanda_final`
- `X_hat`
- `A_coef_tecnicos`
- `L_leontief`
- `B_coef_distribucion`

Las validaciones, balances diagnosticos y auditorias de cobertura se conservan en archivos consolidados separados para no sobrecargar cada libro anual.

Los Excel consolidados por pais se guardan en:

```text
output/entregables/
```

El repositorio local de matrices se arma en:

```text
output/repositorio_matrices_mip/
```

## Limitaciones actuales

- Algunas series no publican una matriz importada por industria; en esos casos se usa una estimacion proporcional por producto.
- Algunas MIP directas no traen apertura importada historica; se conserva el dato publicado y se marca `ci_importado = 0` si no hay apertura.
- Las diferencias entre precios comprador y precios basicos se documentan cuando la fuente no permite una conversion exacta por componente de uso.
- Las actividades con demanda final residual negativa requieren revision economica o sectorial antes de uso analitico sensible.
- Uruguay 2017 queda como caso pendiente: no se identifico una MIP directa equivalente para ese anio y el COU disponible no resuelve por completo la demanda final sectorial.
