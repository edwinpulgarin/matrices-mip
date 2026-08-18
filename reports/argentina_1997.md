# Argentina 1997 — reconstruida desde la MIPAr97 del INDEC

El INDEC publica el COU completo de 1997, con la matriz de importaciones celda a celda y la utilización nacional ya a precios básicos. Es el único año de Argentina que se construye **sin ningún prorrateo**.

- Dimensión: **124 ramas × 195 productos**
- VBP: 444,242,492 miles de pesos
- Consumo intermedio doméstico: 167,856,141
- Insumo importado: 18,382,947
- Impuestos y márgenes: 9,928,083
- Valor agregado: 248,075,322
- Balance fila = columna: 8.3e-16 · L·f = x: 1.7e-17

## Contraste contra la matriz simétrica oficial (cuadro 12)

La metodología del INDEC (sección 12) dice que su simétrica «resulta de multiplicar la traspuesta de la matriz de oferta a precios básicos transformada en estructura expresada en tanto por uno —matriz de cuota de mercado— por la matriz 3 de utilización a precios básicos». Es el Modelo D del Handbook, el mismo que aplica este motor.

| | Nuestra | Oficial | Diferencia |
|:--|--:|--:|--:|
| Suma de Z | 167,856,141 | 167,856,141 | -0.0000 % |
| Máx. diferencia por columna | | | 2.62e-05 |
| Correlación celda a celda | | | 0.9798 |
| Desvío absoluto total | | | 21.99 % |

**La suma y las columnas cierran exacto.** En el Modelo D las columnas de Z son invariantes al modelo, así que eso prueba que la lectura del COU, la valoración y el corte por origen reproducen los del INDEC.

El residuo está en las filas. Una parte se explica y está implementada: las cuatro actividades de **no mercado** —enseñanza y salud públicas, servicios sociales y servicio doméstico— tienen fila cero en la matriz oficial, porque el SCN no les atribuye ventas intermedias. El resto son ajustes propios del INDEC que su metodología no documenta; la propia publicación advierte que dejó «expuestos» valores de comercio mayorista y transporte de carga por comisionistas y transporte contratado, y que la simétrica «no se aconseja para el estudio de las estructuras de costos».

No se implementaron ajustes por actividad para forzar la coincidencia: eso sería calzar con la respuesta y dejaría al motor sin capacidad de aplicarse a años sin MIP oficial.
