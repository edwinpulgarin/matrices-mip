# Metodología, avances y siguientes pasos del repositorio de matrices insumo-producto

**Proyecto:** repositorio de matrices insumo-producto para Argentina, Brasil, México y Uruguay  
**Fecha de actualización:** 29 de mayo de 2026  
**Documento base revisado:** `C:\Users\edwin\Downloads\Metodología (1).pdf`

## 1. Propósito del documento

Este documento sistematiza la metodología aplicada para construir, validar y entregar el repositorio de matrices insumo-producto (MIP), tomando como referencia conceptual el documento base de metodología para la estimación de matrices insumo-producto extendidas ambientalmente y huella de carbono.

La metodología base del PDF plantea una arquitectura completa para pasar de matrices económicas a matrices extendidas ambientalmente: MIP, coeficientes técnicos, inversa de Leontief, modelo de Ghosh, intensidades ambientales, multiplicadores de emisiones, huella de carbono, análisis temporal y difusión de resultados. En el trabajo realizado hasta ahora se consolidó primero la capa económica y contable de las MIP para cuatro países. La extensión ambiental queda definida como siguiente fase natural.

## 2. Alcance actual del proyecto

El alcance ejecutado se concentra en la construcción de un repositorio económico comparable de MIP por país y año, con énfasis en trazabilidad de fuentes, procesamiento reproducible, validaciones matemáticas y entrega de archivos Excel autosuficientes.

| País | Años incorporados | Número de matrices | Estado |
|---|---:|---:|---|
| Argentina | 1997, 2004, 2018, 2019, 2020, 2021 | 6 | Integrado |
| Brasil | 2000-2021 | 22 | Integrado, serie histórica completa en el alcance disponible |
| México | 2003, 2008, 2013, 2018 | 4 | Integrado |
| Uruguay | 2016, 2017 | 2 | Integrado, con alerta técnica en 2017 |
| **Total** | **1997-2022 segun disponibilidad por pais** | **35** | **Repositorio entregable** |

El proyecto no estima todavía matrices ambientalmente extendidas. Sin embargo, los Excel generados ya incluyen los objetos económicos necesarios para una fase posterior de extensión ambiental: `V`, `q`, `U_nacional`, `D`, `Z`, `A`, `L`, `B`, `G`, producción bruta, demanda final homologada y encadenamientos.

## 3. Relación con la metodología base

El PDF de referencia está estructurado alrededor de una MIP extendida ambientalmente para Colombia, con horizonte 2017, 2019 y 2021. De ese documento se toman cinco componentes metodológicos como guía:

1. **Marco MIP:** matriz de transacciones intermedias, vector de producción bruta y demanda final.
2. **Modelo de Leontief:** coeficientes técnicos, inversa de Leontief y multiplicadores hacia atrás.
3. **Modelo de Ghosh:** coeficientes de distribución, inversa de Ghosh y encadenamientos hacia adelante.
4. **Separación doméstica/importada:** tratamiento de transacciones nacionales e importadas cuando la fuente lo permite.
5. **Extensión ambiental futura:** incorporación de matrices de presiones ambientales, intensidades directas, multiplicadores ambientales y huella de carbono.

La adaptación realizada cambia el foco geográfico y operativo. En lugar de partir de Colombia y de una MIP ambiental, el trabajo construido parte de fuentes oficiales de Argentina, Brasil, México y Uruguay y consolida primero la base económica comparable. Esta decisión es metodológicamente importante: una extensión ambiental confiable requiere que las matrices económicas estén cuadradas, alineadas y validadas antes de integrar emisiones u otros indicadores físicos.

## 4. Conceptos y notación usados

Para cada país y año se usa la siguiente notación:

| Símbolo | Descripción |
|---|---|
| `Z` | Matriz de flujos intermedios sector por sector. |
| `g` | Vector de producción bruta sectorial. |
| `W` | Vector de valor agregado sectorial. |
| `A` | Matriz de coeficientes técnicos de Leontief. |
| `L` | Inversa de Leontief. |
| `B` | Matriz de coeficientes de distribución de Ghosh. |
| `G` | Inversa de Ghosh. |
| `f` | Demanda final residual sectorial cuando la fuente no entrega una apertura compatible. |
| `CI_importado` | Consumo intermedio importado, explícito o residual según disponibilidad de fuente. |

Las identidades centrales son:

```text
A = Z * diag(g)^-1
L = (I - A)^-1
B = diag(g)^-1 * Z
G = (I - B)^-1
```

La lectura económica es complementaria:

- `L` mide requerimientos directos e indirectos ante cambios en la demanda final.
- `G` mide la propagación hacia adelante de cambios asociados a la oferta o al valor agregado primario.
- Los multiplicadores de producción se derivan de las sumas de columnas de `L`.
- Los multiplicadores de distribución se derivan de la estructura de `G`.

## 5. Fuentes y estrategia de acopio

El procesamiento se apoyó en fuentes oficiales y archivos institucionales ya disponibles en el proyecto:

| País | Fuente principal | Tratamiento |
|---|---|---|
| Argentina | INDEC y CEPAL | MIP directa 1997; COU/MIP procesadas para 2004 y 2018-2021. |
| Brasil | IBGE y CEPAL | Serie 2000-2009 desde base temprana CEPAL; 2010-2021 desde matrices IBGE/SCN. |
| México | INEGI y CEPAL | MIP oficiales 2003, 2008, 2013 y 2018. |
| Uruguay | Banco Central del Uruguay y CEPAL | MIP directa 2016; COU 2017 convertido a MIP. |

Además, se hizo una revisión externa de fuentes estatales para ampliar histórico. El resultado quedó documentado en `FUENTES_EXTERNAS_HISTORICO.md`. Las principales brechas identificadas fueron:

- Argentina 2005-2017: no se localizaron matrices oficiales públicas directamente descargables.
- Brasil 2022-2023: disponibilidad pública a niveles agregados que no reemplazan la serie detallada usada.
- México 2023: no se localizó un paquete oficial de MIP comparable listo para integrar.
- Uruguay 2018 en adelante: no se localizaron matrices detalladas suficientes para incorporar al pipeline.

## 6. Procesamiento económico realizado

El pipeline distingue dos familias de entrada:

1. **MIP directas:** matrices ya publicadas como producto final por el instituto estadístico. En estos casos se preserva la estructura original y se normaliza el formato para análisis.
2. **COU convertidos a MIP:** cuadros de oferta y utilización que requieren transformar producto por industria hacia una matriz sector por sector.

Cuando se parte de COU, se usa una tecnología compatible con el enfoque industria/producto disponible en las fuentes. De forma general:

```text
D = V * diag(q)^-1
Z = D * U_nacional
A = Z * diag(g)^-1
L = (I - A)^-1
```

Donde:

- `V` es la matriz de producción/oferta.
- `q` es la producción por producto.
- `U_nacional` es la utilización intermedia nacional.
- `D` es una matriz de transformación producto-industria.

La separación nacional/importado se resuelve con prioridad en la fuente:

1. Si la fuente entrega matriz importada explícita, se usa directamente.
2. Si solo hay vector de importaciones, se aplica una asignación proporcional documentada.
3. Si no hay apertura importada, se conserva la MIP nacional disponible y se marca la limitación.

## 7. Estructura de los archivos Excel entregados

Cada Excel país-año fue generado para lectura y trazabilidad. Las hojas incluidas son:

| Hoja | Contenido |
|---|---|
| `Indice` | Metadatos, país, año, fuente, serie y guía de hojas. |
| `COU_Tabla_Original` | COU/fuente original o notas cuando no hay COU público separado. |
| `V_oferta` | Matriz V de oferta/producción por industria y producto. |
| `q_produccion_producto` | Vector q de producción/oferta por producto. |
| `U_nacional` | Utilización intermedia nacional/doméstica. |
| `D_market_share` | Matriz D de participaciones industria-producto. |
| `Z_consumos_intermedios` | Flujos intermedios sector por sector. |
| `A_coef_tecnicos` | Coeficientes técnicos: `A = Z * diag(g)^-1`. |
| `L_leontief` | Inversa de Leontief: `L = (I - A)^-1`. |
| `B_coef_distribucion` | Coeficientes de distribución: `B = diag(g)^-1 * Z`. |
| `G_ghosh_inversa` | Inversa de Ghosh: `G = (I - B)^-1`. |
| `x_produccion_bruta` | Producción bruta sectorial y componentes disponibles. |
| `y_demanda_final` | Demanda final homologada: `DA = C + I + G + (X - M)`. |
| `X_hat` | Matriz diagonal de producción bruta. |
| `encadenamientos` | Indicadores hacia atrás y hacia adelante derivados de `L` y `G`. |

Las validaciones detalladas (`val_A_menos_Zg`, `val_Leontief`, `val_Ghosh`, balances y auditorías) quedan en archivos consolidados separados para no sobrecargar cada Excel anual.

El paquete principal quedó organizado en:

```text
output/matrices_insumo_producto/
  Argentina/
  Brasil/
  Mexico/
  Uruguay/
  indice_matrices_insumo_producto.xlsx
```

## 8. Validaciones matemáticas aplicadas

La validación se diseñó para diferenciar fallas estructurales de alertas diagnósticas. Las pruebas estructurales determinan si una matriz es usable para multiplicadores; las diagnósticas orientan revisiones económicas posteriores.

| Indicador | Qué valida | Criterio | Interpretación |
|---|---|---|---|
| `cuadrada_Z_A_L` | Dimensión sector por sector | `Z`, `A` y `L` son matrices cuadradas y compatibles | Condición mínima para invertir matrices y calcular multiplicadores. |
| `etiquetas_alineadas` | Coherencia sectorial | Filas, columnas y vectores comparten sectores y orden | Evita asignar producción o coeficientes a sectores incorrectos. |
| `no_negatividad_Z_A_g` | Signo económico básico | `Z >= 0`, `A >= 0`, `g > 0` | Negativos se marcan como alerta contable. |
| `max_abs_A_menos_Z_sobre_g` | Consistencia de coeficientes técnicos | Máximo residual de `A - Z * diag(g)^-1` | Debe ser cercano a cero. |
| `max_abs_Leontief` | Validez algebraica de Leontief | Máximo residual de `(I - A)L - I` | Confirma que `L` es inversa de `I - A`. |
| `max_abs_Ghosh` | Validez algebraica de Ghosh | Máximo residual de `(I - B)G - I` | Confirma que `G` es inversa de `I - B`. |
| `celdas_negativas_Z` | Localización de negativos en `Z` | Conteo de celdas `Z_ij < 0` | Permite ubicar problemas de conversión o fuente. |
| `sectores_demanda_final_residual_negativa` | Cierre por ventas | Conteo de sectores donde `g - ventas intermedias < 0` | Alerta de cierre por demanda final residual. |
| `sectores_va_residual_negativo` | Cierre por compras | Conteo de sectores donde `g - compras intermedias - CI_importado < 0` | Alerta de cierre de valor agregado. |

## 9. Resultados de validación obtenidos

| País | Matrices | Resultado estructural | Alertas diagnósticas |
|---|---:|---|---|
| Argentina | 6 | Todas cuadradas, alineadas, no negativas y con Leontief/Ghosh consistente. Mayor residual `A - Z/g`: `6.91e-04` en 1997. | 158 sectores acumulados con demanda final residual negativa; 0 celdas negativas en `Z`; 0 sectores con valor agregado residual negativo. |
| Brasil | 22 | Todas cuadradas, alineadas, no negativas y con residuales de precisión numérica. | 337 sectores acumulados con demanda final residual negativa; 4 sectores acumulados con valor agregado residual negativo, concentrados en 2011-2014. |
| México | 4 | Todas las matrices pasan las identidades principales; residuales de Leontief y Ghosh en magnitud de máquina. | 4 sectores acumulados con demanda final residual negativa; 0 celdas negativas en `Z`; 0 sectores con valor agregado residual negativo. |
| Uruguay | 2 | 2016 pasa todas las pruebas. 2017 mantiene cuadratura, etiquetas, Leontief y Ghosh. | Uruguay 2017 tiene 47 celdas negativas en `Z`; 19 sectores acumulados con demanda final residual negativa; 0 sectores con valor agregado residual negativo. |

Resumen global:

- 35 matrices revisadas.
- 35 matrices cuadradas.
- 35 matrices con etiquetas alineadas.
- 34 matrices con no negatividad completa en `Z`, `A` y `g`.
- 47 celdas negativas en `Z`, todas asociadas a Uruguay 2017.
- Máximo residual global de `A - Z/g`: `6.91e-04`.
- Máximo residual global de Leontief: `9.86e-04`.
- Máximo residual global de Ghosh: `2.11e-15`.

## 10. Avances concretos logrados

Los avances del proyecto pueden resumirse en siete bloques:

1. **Consolidación de histórico:** se amplió el inventario inicial y se incorporaron nuevas matrices oficiales, incluyendo Argentina 1997 y México 2003.
2. **Brasil completo:** se integró una serie continua 2000-2021 con archivos país-año y consolidado.
3. **Repositorio por país y año:** se generaron 34 Excel individuales con estructura homogénea.
4. **Validación matemática:** se diseñaron y aplicaron pruebas reproducibles sobre estructura, etiquetas, no negatividad, Leontief, Ghosh y cierres sectoriales.
5. **Trazabilidad de fuentes:** se documentó qué fuentes estatales fueron revisadas, qué años se incorporaron y qué brechas permanecen.
6. **Presentación técnica:** se actualizó la presentación HTML con cobertura, metodología, validaciones y resultados.
7. **Paquete publicable:** se preparó un repositorio de entrega con `MIP/`, `Codigo/`, índices, validaciones y presentación.

## 11. Limitaciones actuales

Las principales limitaciones no invalidan el repositorio, pero deben quedar explícitas:

- **Comparabilidad entre fuentes:** no todos los países usan la misma base de precios, clasificación sectorial o año de referencia.
- **Brechas temporales:** Argentina 2005-2017, México 2023, Uruguay 2018+ y Brasil 2022+ detallado permanecen como brechas de información pública.
- **Uruguay 2017:** la matriz convertida desde COU conserva 47 celdas negativas en `Z`; se recomienda revisar tratamiento de negativos antes de análisis económico sensible.
- **Demanda final residual:** en varios años aparecen sectores con demanda final residual negativa. Esto es una alerta de cierre y no una falla algebraica de Leontief/Ghosh.
- **Extensión ambiental pendiente:** todavía no se integran matrices de emisiones, intensidades ambientales ni huella de carbono.
- **Homologación sectorial:** no se ha construido una tabla puente única para comparar todos los países al mismo nivel sectorial.

## 12. Siguientes pasos recomendados

### 12.1. Cierre del repositorio económico

1. Incorporar al repositorio publicado el archivo `validacion_detallada_mip.xlsx`, ya que la presentación lo referencia.
2. Actualizar el `README.md` del repositorio para explicar claramente la estructura `MIP/`, `Codigo/`, índices y validaciones.
3. Crear una tabla de homologación sectorial mínima entre países para análisis comparativo.
4. Separar las validaciones en dos categorías: estructurales y diagnósticas, para evitar que alertas de cierre se interpreten como errores bloqueantes.
5. Documentar explícitamente el caso Uruguay 2017 y decidir si se conserva, ajusta o entrega como matriz experimental.

### 12.2. Ampliación de fuentes

1. Solicitar a INDEC/CEPAL información no pública o tabulados puente para Argentina 2005-2017.
2. Verificar periódicamente si INEGI publica MIP 2023 en formato descargable comparable.
3. Revisar actualizaciones del BCU para Uruguay 2018+.
4. Explorar si Brasil 2022+ puede obtenerse a nivel compatible con la serie 2000-2021.

### 12.3. Extensión ambiental de la MIP

Siguiendo el documento base, la siguiente fase debería construir una MIP extendida ambientalmente. Para cada país y año seleccionado se requiere:

1. Definir los indicadores ambientales: CO2, CH4, N2O, GEI en CO2eq u otros indicadores disponibles.
2. Conseguir matrices o vectores de emisiones por sector económico.
3. Homologar sectores ambientales con sectores MIP.
4. Construir la matriz de presiones ambientales absolutas `E`.
5. Calcular intensidades directas:

```text
D_env = E * diag(g)^-1
```

6. Calcular multiplicadores ambientales de demanda:

```text
M_env = D_env * L
```

7. Estimar huella de carbono basada en consumo:

```text
HC = m * y
```

8. Separar, si la fuente lo permite, huella por hogares, gobierno, inversión y exportaciones.
9. Comparar huella de productor y consumidor cuando existan datos de comercio e importaciones ambientales.

### 12.4. Análisis temporal y comparativo

1. Construir series de multiplicadores por país.
2. Identificar sectores con mayores encadenamientos hacia atrás y hacia adelante.
3. Comparar cambios pre y post pandemia en países con años 2019-2021.
4. Aplicar descomposición estructural (SDA) cuando haya matrices comparables en el tiempo.
5. Construir mapas de sectores clave: altos multiplicadores económicos, altas intensidades ambientales y alta relevancia en demanda final.

### 12.5. Difusión y mantenimiento

1. Publicar una versión metodológica en Word y Markdown.
2. Agregar una guía de uso para usuarios no técnicos.
3. Versionar el repositorio con etiquetas: `v1.0-economico`, `v1.1-validaciones`, `v2.0-ambiental`.
4. Automatizar una prueba de consistencia que se ejecute cada vez que se agregue una nueva matriz.
5. Mantener una bitácora de fuentes revisadas y decisiones metodológicas.

## 13. Hoja de ruta sugerida

| Fase | Objetivo | Producto esperado |
|---|---|---|
| 1. Cierre económico | Completar documentación y resolver archivos faltantes del repo publicado | Repositorio económico `v1.0` |
| 2. Homologación sectorial | Crear tabla puente entre países y fuentes | Clasificador común o tabla de correspondencia |
| 3. Acopio ambiental | Obtener emisiones por sector y año | Base ambiental por país-año |
| 4. Integración MIP-EA | Calcular intensidades y multiplicadores ambientales | Excel MIP-EA por país-año |
| 5. Huella de carbono | Estimar huella por demanda final y componentes | Tablas de huella y descomposición |
| 6. Análisis comparativo | Evaluar tendencias, sectores clave y cambios temporales | Informe técnico y presentación |
| 7. Publicación | Preparar paquete final documentado | Repositorio, documento metodológico y visualizaciones |

## 14. Conclusión metodológica

El trabajo realizado dejó construida la base económica necesaria para avanzar hacia una MIP extendida ambientalmente. La contribución principal no es solo reunir matrices, sino convertirlas en un repositorio auditable: cada archivo contiene matrices, coeficientes, inversas, multiplicadores y validaciones.

La metodología base del PDF proporciona el marco para la siguiente capa: emisiones, intensidades ambientales, multiplicadores de carbono y huella por demanda final. Para llegar a esa etapa con solidez, el avance actual resolvió primero la parte crítica: estructura económica, trazabilidad de fuentes, consistencia algebraica y empaquetamiento reproducible.

## 15. Archivos relacionados

| Archivo o carpeta | Uso |
|---|---|
| `output/matrices_insumo_producto/` | Paquete anual país-año con 34 Excel. |
| `output/tablas/validacion_detallada_mip.xlsx` | Validación matemática por país y año. |
| `output/tablas/validacion_matematica_mip.xlsx` | Reporte agregado de validación. |
| `FUENTES_EXTERNAS_HISTORICO.md` | Trazabilidad de búsqueda de información oficial adicional. |
| `presentacion.html` | Presentación técnica del proyecto. |
| `scripts/generar_paquete_matrices.py` | Generación del paquete país-año. |
| `scripts/validar_mips.py` | Validaciones matemáticas reproducibles. |

