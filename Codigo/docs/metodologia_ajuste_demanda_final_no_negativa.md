# Metodologia de ajuste para matrices robustas sin demanda final negativa

**Fecha:** 3 de junio de 2026  
**Script:** `scripts/generar_matrices_robustas.py`  
**Salida:** `output/matrices_insumo_producto_robustas/`

> **Nota critica:** este documento describe un ejercicio experimental que modifica la matriz `Z`. No debe usarse como metodologia oficial del proyecto sin aprobacion explicita. El criterio metodologico principal debe ser conservar las cifras de fuente/reconstruccion y documentar los problemas de cierre. Alterar `Z` para eliminar demanda final negativa puede interpretarse como maquillar cifras si no se presenta como escenario de sensibilidad.

## 1. Motivacion

El equipo solicito fortalecer las matrices para que, en la medida de lo posible, no presenten sectores con demanda final negativa. En el paquete original, la demanda final de varios paises no siempre es una variable descargada literalmente, sino una demanda final residual:

```text
f = g - sum_row(Z)
```

Por tanto, una demanda final negativa indica que las ventas intermedias de un sector superan su produccion bruta. Para un paquete analitico robusto, esto es problematico porque dificulta la interpretacion economica de choques de demanda final, huella de carbono y encadenamientos.

## 2. Principio del ajuste

El ajuste conserva fijo el vector de produccion bruta `g`, porque es el ancla principal de cuentas nacionales. Tambien conserva `CI_importado` cuando existe.

Lo que se ajusta es la matriz de flujos intermedios `Z`, reduciendo proporcionalmente los flujos que impiden cerrar con demanda final y valor agregado no negativos.

El ajuste es de una sola direccion:

- no aumenta flujos intermedios;
- no modifica `g`;
- no inventa demanda final positiva;
- solo reduce `Z` donde se requiere para cumplir restricciones contables.

## 3. Restricciones buscadas

Para cada sector vendedor `i`:

```text
sum_j Z_ij <= g_i
```

Con esto:

```text
f_i = g_i - sum_j Z_ij >= 0
```

Para cada sector comprador `j`:

```text
sum_i Z_ij + CI_importado_j <= g_j
```

Con esto:

```text
W_j = g_j - sum_i Z_ij - CI_importado_j >= 0
```

## 4. Algoritmo aplicado

Para cada matriz:

1. Se lee la matriz original procesada desde `data/processed`.
2. Se recortan a cero las celdas negativas de `Z`.
3. Se calcula la suma por fila de `Z`.
4. Si una fila excede `g`, se aplica un factor proporcional:

```text
factor_fila_i = g_i / sum_j Z_ij
Z_ij_ajustada = Z_ij * factor_fila_i
```

5. Se calcula la suma por columna de la nueva `Z`.
6. Si una columna excede `g - CI_importado`, se aplica un factor proporcional:

```text
factor_columna_j = (g_j - CI_importado_j) / sum_i Z_ij
Z_ij_ajustada = Z_ij * factor_columna_j
```

7. Se hace una pasada adicional por filas para absorber posibles diferencias numericas.
8. Se recalculan los objetos economicos:

```text
A = Z * diag(g)^-1
L = (I - A)^-1
B = diag(g)^-1 * Z
G = (I - B)^-1
f = g - sum_row(Z)
W = g - CI_importado - sum_col(Z)
```

9. Se generan hojas de trazabilidad:

- `f_original`;
- `W_original_fuente`;
- `ajuste_balance`;
- `validacion_resumen`.

## 5. Resultados globales

Despues del ajuste:

| Indicador | Resultado |
|---|---:|
| Matrices robustas generadas | 34 |
| Celdas negativas en `Z` | 0 |
| Sectores con demanda final negativa | 0 |
| Sectores con valor agregado residual negativo | 0 |
| Maximo error de balance filas/columnas | `4.77e-07` |
| Maximo residual Leontief | `2.33e-15` |
| Maximo residual Ghosh | `2.33e-15` |

## 6. Magnitud del ajuste

La reduccion total de `Z` positiva respecto de la `Z` original es:

| Pais | Promedio | Maximo |
|---|---:|---:|
| Argentina | 4.67% | 7.60% |
| Brasil | 2.56% | 4.85% |
| Mexico | 0.01% | 0.03% |
| Uruguay | 1.36% | 2.71% |

Los mayores ajustes se concentran en Argentina 2018-2021 y Brasil 2008-2009. Esto confirma que la matriz robusta mejora la interpretacion economica, pero debe documentarse como una version balanceada, no como replica literal de la fuente.

## 7. Recomendacion de uso

No se recomienda usar esta version como entregable principal. Se recomienda mantener dos capas, con jerarquia clara:

1. **Matriz original/reconstruida:** capa principal del proyecto. Conserva lo mas cercano posible a la fuente y sirve para trazabilidad.
2. **Matriz ajustada experimental:** solo anexo de sensibilidad. No debe reportarse como matriz oficial ni como base principal de resultados.

Para presentaciones y analisis finales, conviene usar la version original/reconstruida y explicar los sectores con demanda final negativa. Si se necesita una matriz sin negativos, debe acordarse formalmente el metodo de conciliacion con el equipo antes de publicar resultados.

## 8. Respuesta sugerida al equipo

> Identificamos que la demanda final negativa no siempre proviene directamente de cuentas nacionales. En varios casos aparece porque la demanda final de los entregables se calcula como residual para cerrar la MIP domestica. No recomendamos alterar las cifras como solucion principal. La respuesta metodologicamente correcta es separar matrices directas y reconstruidas, explicar el origen del negativo, revisar la separacion nacional/importado y la valoracion, y solo construir una matriz conciliada si el equipo aprueba explicitamente un metodo de ajuste. La version ajustada existente queda como anexo experimental de sensibilidad, no como matriz oficial.
