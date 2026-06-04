# Respuesta técnica para el equipo: demanda final negativa y matrices directas vs reconstruidas

**Fecha:** 3 de junio de 2026  
**Tema:** origen de sectores con demanda final negativa en Argentina, Brasil y Uruguay  
**Archivo de respaldo:** `output/tablas/diagnostico_demanda_final_negativa.xlsx`

> **Actualización 4 de junio de 2026:** este memo fue el primer diagnóstico. Luego se revisó la construcción y se corrigieron errores de lectura, alineación y precios en Argentina y Brasil. La respuesta actualizada está en `docs/auditoria_construccion_matrices_mip.md`; usar ese memo como versión principal para el equipo.

## 1. Respuesta corta para la reunión

La variable que estamos observando como demanda final negativa en los entregables no siempre corresponde a una columna de demanda final descargada literalmente de cuentas nacionales. En el paquete anual, la variable `demanda_final_f` se usa como cierre sectorial:

```text
demanda_final_f = g - ventas_intermedias_Z
```

En las matrices reconstruidas desde COU, ese cierre se calcula primero como demanda final doméstica residual por producto:

```text
Y_residual_domestica = q_domestica - U_nacional.sum(axis=1)
```

y luego se transforma al espacio de industrias mediante la matriz de participación:

```text
f_industria = D * Y_residual_domestica
```

Por tanto:

- En **Brasil**, la demanda final original leída del COU no presenta productos negativos en ningún año. Los sectores negativos aparecen por el método de cierre doméstico residual y la conversión COU -> MIP.
- En **Argentina**, hay un caso mixto: algunos años ya tienen productos con demanda final negativa en la fuente COU, pero el número de negativos aumenta al construir la demanda final doméstica residual.
- En **Uruguay**, 2016 es MIP directa BCU y el negativo es prácticamente de redondeo en el cierre implícito. Uruguay 2017 fue reconstruido desde COU y la demanda final negativa proviene del cierre residual a precios básicos y su transformación a MIP.

Esto no invalida las matrices para Leontief/Ghosh: las identidades matriciales pasan. Sí significa que estos sectores deben tratarse como alertas de cierre económico, no como errores algebraicos.

## 2. Matrices descargadas tal cual vs reconstruidas

| País | Años | Tipo | Tratamiento |
|---|---:|---|---|
| Argentina | 1997 | MIP directa descargada | Se leen `Z`, `A`, `L`, `g` y `W` desde MIPAr97 INDEC. |
| Argentina | 2004, 2018, 2019, 2020, 2021 | Reconstruidas desde COU | Se parte de COU INDEC/CEPAL y se convierte a MIP industria-industria. |
| Brasil | 2000-2009 | Reconstruidas desde COU | Se parte de COU CEPAL Brasil base 2000. |
| Brasil | 2010-2021 | Reconstruidas desde COU | Se parte de COU/tablas IBGE nivel 68. |
| México | 2003, 2008, 2013, 2018 | MIP directa descargada | Se leen MIP ya construidas por CEPAL/INEGI. |
| Uruguay | 2016 | MIP directa descargada | Se lee MIP directa BCU 2016. |
| Uruguay | 2017 | Reconstruida desde COU | Se parte de COU CEPAL 2017 y se convierte a MIP. |

Resumen:

- **MIP directas:** 6 matrices.
- **MIP reconstruidas:** 28 matrices.
- **Total del repositorio:** 34 matrices.

## 3. Evidencia sobre demanda final negativa

### Argentina

| Año | Fuente original COU: productos con Y negativa | Residual doméstico producto negativo | MIP final: sectores negativos | Lectura |
|---:|---:|---:|---:|---|
| 2004 | 3 | 75 | 20 | La fuente ya trae algunos negativos, pero el residual doméstico amplifica el fenómeno. |
| 2018 | 6 | 89 | 28 | Caso mixto: fuente + reconstrucción residual. |
| 2019 | 3 | 89 | 28 | Caso mixto. |
| 2020 | 8 | 94 | 27 | Caso mixto, con mayor tensión de cierre. |
| 2021 | 0 | 89 | 26 | No viene negativo en la demanda final fuente; surge por el cierre residual doméstico. |

Sectores más negativos en la MIP final:

| Año | Sector con mínimo `demanda_final_f` | Valor mínimo |
|---:|---|---:|
| 2004 | 141/142 - Extracción de piedra, arena y arcilla; explotación de minas y canteras n.c.p. | -614,717.8 |
| 2018 | 27100 - Industrias básicas de hierro y acero | -61,382,327.0 |
| 2019 | 27100 - Industrias básicas de hierro y acero | -103,529,361.7 |
| 2020 | 24130 - Fabricación de plásticos en formas primarias y caucho sintético | -185,485,687.2 |
| 2021 | 24130 - Fabricación de plásticos en formas primarias y caucho sintético | -371,689,690.9 |

**Interpretación para el equipo:** no conviene decir que todos los negativos vienen “tal cual” de cuentas nacionales. Para Argentina hay algunos negativos en la demanda final fuente, pero la variable final de nuestro entregable es un residual doméstico que intensifica o reubica esos negativos en el espacio industria-industria.

### Brasil

| Periodo | Fuente original COU: productos con Y negativa | Residual doméstico producto negativo | MIP final: sectores negativos | Lectura |
|---|---:|---:|---:|---|
| 2000-2009 | 0 en todos los años | 29-35 productos por año | 11-14 sectores por año | No viene así en la demanda final fuente; aparece por cierre residual doméstico. |
| 2010-2021 | 0 en todos los años | 32-37 productos por año | 11-14 sectores por año | No viene así en la demanda final fuente; aparece por cierre residual doméstico y separación/estimación importada. |

Sector más negativo recurrente:

- 2000-2009: `Produtos químicos`.
- 2010-2021: `2091 - Fabricação de químicos orgânicos e inorgânicos, resinas e elastômeros`.

**Interpretación para el equipo:** en Brasil, con la evidencia actual, los negativos no parecen venir de una demanda final negativa descargada. Surgen cuando pasamos de la demanda final total del COU a una demanda final doméstica residual compatible con `Z` nacional/doméstica.

### Uruguay

| Año | Tipo | Evidencia | Lectura |
|---:|---|---|---|
| 2016 | MIP directa BCU | 1 sector negativo: `P10 - Cosechas de azúcar`, valor `-0.3` | Es un residual implícito prácticamente de redondeo en la MIP directa. |
| 2017 | Reconstruida desde COU CEPAL | 6 productos negativos en residual producto; 2 sectores negativos en MIP final | Surge del cierre residual a precios básicos y la conversión COU -> MIP. |

Sector más negativo en 2017:

- `H.1 - Servicio de transporte de carga`, con `demanda_final_f = -25,062.2`.

**Interpretación para el equipo:** Uruguay 2016 debe tratarse como un caso directo con diferencia mínima. Uruguay 2017 sí es reconstrucción; ahí la demanda final negativa está asociada al método de cierre residual y reescalamiento a precios básicos.

## 4. Paso a paso de las matrices reconstruidas

El paso a paso general aplicado a Argentina 2004/2018-2021, Brasil 2000-2021 y Uruguay 2017 fue:

1. Leer del COU las matrices de oferta/producción (`V`), utilización intermedia (`U`), demanda final (`Y`), valor agregado (`W`) e importaciones (`M`) cuando existen.
2. Alinear productos y actividades para que `V`, `U`, `Y` y `W` compartan códigos y nombres comparables.
3. Separar consumo intermedio nacional/importado:
   - si existe matriz importada explícita, se resta de `U`;
   - si solo existe vector de importaciones, se estima participación importada por producto;
   - si no existe apertura, se deja importado en cero y se documenta la limitación.
4. Recalcular demanda final doméstica residual por producto:

```text
Y_residual_domestica = q_domestica - U_nacional.sum(axis=1)
```

5. Construir la matriz de participación industria-producto:

```text
D = V * diag(q)^-1
```

6. Convertir la utilización intermedia nacional a matriz industria-industria:

```text
Z = D * U_nacional
```

7. Transformar la demanda final residual al espacio de industrias:

```text
f_industria = D * Y_residual_domestica
```

8. Calcular coeficientes técnicos e inversas:

```text
A = Z * diag(g)^-1
L = (I - A)^-1
B = diag(g)^-1 * Z
G = (I - B)^-1
```

9. Ejecutar validaciones matemáticas:
   - matrices cuadradas;
   - etiquetas alineadas;
   - no negatividad de `Z`, `A` y `g`;
   - `A = Z/g`;
   - `(I - A)L = I`;
   - `(I - B)G = I`;
   - sectores con demanda final residual negativa;
   - sectores con valor agregado residual negativo.

Importante: no se aplicó RAS para forzar balances. El parámetro quedó como `ajustar_ras=False`, porque algunos desbalances pueden responder a diferencias de valoración entre precios básicos y precios comprador.

## 5. Qué conviene responder al equipo

Propuesta de respuesta:

> Revisamos el origen de la demanda final negativa. La variable en nuestros entregables es un cierre residual sectorial, no siempre una demanda final oficial descargada. En Brasil, la demanda final original del COU no trae negativos; los negativos aparecen al construir una demanda final doméstica residual compatible con la `Z` doméstica/nacional. En Argentina hay una situación mixta: algunos años ya tienen productos negativos en la demanda final fuente, pero el residual doméstico aumenta el número de sectores negativos. En Uruguay 2016, que es MIP directa, el negativo es mínimo y probablemente de redondeo; Uruguay 2017 sí es reconstruida desde COU y el negativo proviene del cierre residual a precios básicos. Para la siguiente versión proponemos separar en los Excel la demanda final fuente, cuando exista, de la demanda final residual usada para cierre, y dejar ambas trazadas.

## 6. Recomendaciones metodológicas

1. Renombrar en los entregables `demanda_final_f` como `demanda_final_domestica_residual` cuando provenga del cierre.
2. Agregar una hoja adicional `demanda_final_fuente` para las matrices reconstruidas desde COU, preservando la demanda final original antes del cierre residual.
3. Mantener la demanda final negativa como alerta diagnóstica, no como error estructural.
4. Para Brasil, documentar explícitamente que los negativos surgen del residual doméstico y no de la demanda final fuente.
5. Para Argentina, separar los negativos que ya vienen en la fuente de los que aparecen por residual.
6. Para Uruguay 2017, documentar el reescalamiento a precios básicos y el uso de residual.
7. Si el análisis económico requiere demanda final no negativa, evaluar una alternativa de balanceo: redistribución controlada, RAS con restricciones, o uso de demanda final fuente transformada en lugar de residual doméstica.

## 7. Nota posterior: paquete robusto solo como ejercicio experimental

Se generó una segunda versión analítica de las 34 matrices, sin sobrescribir las matrices originales:

```text
output/matrices_insumo_producto_robustas/
```

Sin embargo, esta versión **no debe usarse como entregable principal ni presentarse como cifra oficial**. El método mantiene fija la producción bruta `g` y ajusta proporcionalmente la matriz `Z` para cumplir:

```text
f = g - sum_row(Z) >= 0
W = g - CI_importado - sum_col(Z) >= 0
```

Luego recalcula:

```text
A = Z * diag(g)^-1
L = (I - A)^-1
B = diag(g)^-1 * Z
G = (I - B)^-1
```

Resultados de validación del paquete robusto:

| Indicador | Resultado |
|---|---:|
| Matrices robustas | 34 |
| Celdas negativas en `Z` | 0 |
| Sectores con demanda final negativa | 0 |
| Sectores con valor agregado residual negativo | 0 |
| Máximo error de balance filas/columnas | `4.77e-07` |
| Máximo residual Leontief | `2.33e-15` |
| Máximo residual Ghosh | `2.33e-15` |

La magnitud promedio del ajuste sobre `Z` positiva fue:

| País | Promedio | Máximo |
|---|---:|---:|
| Argentina | 4.67% | 7.60% |
| Brasil | 2.56% | 4.85% |
| México | 0.01% | 0.03% |
| Uruguay | 1.36% | 2.71% |

La recomendación corregida queda en dos capas:

1. **Original/reconstruida:** capa principal para trazabilidad de fuente, auditoría metodológica y resultados oficiales del proyecto.
2. **Ajustada experimental:** solo anexo de sensibilidad, no base principal de resultados, salvo que el equipo apruebe explícitamente una metodología de conciliación.

El punto importante es que ajustar `Z` puede interpretarse como alterar cifras. Por tanto, la salida robusta queda documentada, pero la respuesta metodológica al equipo debe centrarse en:

- identificar si el negativo viene de la fuente o del residual;
- preservar la matriz original/reconstruida;
- revisar separación nacional/importado;
- revisar precios básicos vs precios comprador;
- evaluar si corresponde usar demanda final fuente en lugar de demanda residual;
- acordar formalmente cualquier ajuste antes de publicar resultados.

Documentación adicional:

```text
docs/metodologia_ajuste_demanda_final_no_negativa.md
output/tablas/resumen_ajuste_demanda_final_robusta.xlsx
output/tablas/validacion_matrices_robustas.xlsx
```
