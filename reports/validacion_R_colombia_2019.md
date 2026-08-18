# Validación independiente en R — Colombia 2019

Prueba manual escrita en **R**, fuera del motor en Python, que lee el libro
publicado y la MIP oficial del DANE y las compara sin recalcular nada.

| | Nuestra | Oficial DANE |
|:--|--:|--:|
| Fuente | `MIP_Colombia_2019_LIBRO.xlsx` · hoja «12. Z consumos intermedios» | `DANE_MIP_2019.xlsx` · «Cuadro 5» |
| Dimensión original | 61 × 61 | 68 × 68 |
| Supuesto | Modelo D (Handbook Cap. 12) | «estructura fija de ventas de productos» |
| Valoración | precios básicos, doméstica | precios básicos, Nacional |
| Suma de Z | 729.403 | 729.403 |

Ambas se agregan a la partición común de **58 grupos**, porque las
clasificaciones están cruzadas: el DANE abre servicios que el COU agrupa y el
COU abre educación y papel/impresión que el DANE agrupa. El puente **no es
nuestro**: sale de la *Tabla correlativa de actividades económicas* que el DANE
publica como anexo 2 de la metodología `DSO-MIP-MET-001`.

## Resultado

- Diferencia en la suma de Z: **+0.0000 %**
- Consumo intermedio **por columna**: máxima diferencia absoluta **0.000086**
- Ventas intermedias **por fila**: máxima diferencia absoluta **4268.2**
- Correlación celda a celda: **0.9710**
- Desvío absoluto total (Σ|dif| / Σ oficial): **17.32 %**

El patrón es exactamente el que predice la teoría. El Modelo D reparte entre
**filas** (de producto a industria) y deja intactas las **columnas**, que son el
consumo intermedio de cada sector. Que las columnas coincidan hasta el último
decimal prueba que partimos del mismo dato y que la valoración y el balanceo
reproducen los del DANE; que las filas difieran es el efecto de transformar a
68 actividades y agregar, en vez de agregar a 61 y transformar.

## Las 10 filas con mayor diferencia

| Grupo | Nuestra | Oficial | Diferencia | % |
|:--|--:|--:|--:|--:|
| A0101-02 | 4057.2 | 8325.4 | -4268.2 | -51.3 % |
| 072 | 41359.8 | 45587.2 | -4227.5 | -9.3 % |
| 075 | 9266.2 | 5121.2 | +4145.0 | +80.9 % |
| 058 | 38815.0 | 34912.2 | +3902.8 | +11.2 % |
| 028 | 9374.3 | 13075.3 | -3701.0 | -28.3 % |
| A0101-01 | 22798.9 | 20004.0 | +2794.8 | +14.0 % |
| 029 | 3788.8 | 1174.7 | +2614.0 | +222.5 % |
| 018+022 | 27901.5 | 30514.4 | -2612.9 | -8.6 % |
| R | 7044.9 | 9317.1 | -2272.2 | -24.4 % |
| 023 | 8062.9 | 6308.1 | +1754.9 | +27.8 % |

## Qué NO prueba esta comparación

El DANE construye su matriz desde un COU interno más detallado y después
agrega; nosotros partimos del COU publicado a 61 industrias. Agregar antes o
después de transformar **no da lo mismo**, así que la igualdad exacta no es
esperable ni sería buena señal. Lo que la prueba mide es si el desvío está en
el orden del sesgo de agregación o si hay un error de método.
