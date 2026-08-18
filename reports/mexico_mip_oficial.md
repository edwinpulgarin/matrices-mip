# México — MIP simétrica OFICIAL de INEGI

Industria × industria, precios básicos, **matriz doméstica** (el insumo importado va en fila primaria), millones de pesos corrientes. Nivel rama SCIAN. La versión total (nacional + importada) no se publica: todo lo que trae el libro se deriva de esta matriz.

**Sin ningún prorrateo y sin transformación propia.** INEGI publica la matriz simétrica ya construida y con la doméstica y la importada medidas por separado, así que no interviene ni el supuesto del Cap. 7 (impuestos y márgenes) ni el del Cap. 8 (origen), ni el Modelo D del Cap. 12.

| Año | Dim | VBP | VAB | Importaciones | fila=columna | L·f=x | mult. medio |
|----:|----:|----:|----:|----:|:---:|:---:|:---:|
| 2008 | 262×262 | 20,682,566 | 11,941,199 | 2,647,781 | 4.5e-17 | 3.4e-17 | 1.5110 ✅ |
| 2013 | 262×262 | 27,642,648 | 15,642,620 | 3,898,884 | 3.4e-17 | 3.4e-17 | 1.5185 ✅ |
| 2018 | 263×263 | 41,959,242 | 22,873,646 | 7,162,501 | 1.1e-17 | 2.8e-17 | 1.4338 ✅ |

**Cuidado al comparar 2008 contra los otros dos.** La MIP 2008 está en SCIAN 2007 y las de 2013 y 2018 en SCIAN 2013, así que la clasificación no es la misma: a nivel sector 2007 trae el comercio junto (`43-46`) donde 2013 lo parte en `43` y `46`, y a nivel rama hay seis códigos que entran o salen (`7221`/`7222` se reagrupan en `7225`, aparecen `4611` y `4922`, desaparece `9321`). Los agregados y los multiplicadores medios sí son comparables; el cruce rama por rama entre 2008 y los otros años, no, sin un puente de clasificaciones.


## Contraste 2013 — oficial vs. reconstruida desde el COU

Mismo año, mismo instituto, mismo nivel de agregación y los mismos datos de base. Lo único que cambia es quién hizo la transformación de COU a matriz simétrica: INEGI con su método, o nosotros con el Modelo D del Handbook. Es la prueba más exigente del motor, porque no hay diferencia de fuente detrás de la que esconderse.

| | MIP oficial INEGI | Reconstruida (Modelo D) | Diferencia |
|:--|--:|--:|--:|
| Ramas en común | 262 | 262 | — |
| Suma de Z | 8,091,685 | 8,091,685 | +0.00 % |
| Producción total | 27,642,648 | 27,642,696 | +0.00 % |
| Multiplicador medio | 1.5185 | 1.5174 | -0.07 % |

Correlación celda a celda de Z: **0.9998**.

Los agregados coinciden y la correlación es casi perfecta. La dispersión que queda en las celdas chicas es la diferencia entre dos métodos de transformación legítimos —no un error de lectura—, y da la medida de cuánta incertidumbre de método cargan los libros de los países que sólo publican el COU y no la MIP.


## Filas que sólo publica INEGI

El COU de los otros cuatro países trae el valor agregado en una sola fila agregada, y por eso el multiplicador de valor agregado no es calculable: sale por identidad y da 1,0000 en todos los sectores (ver el docstring de `analisis.py`). INEGI sí abre remuneraciones y puestos de trabajo, así que para México quedan habilitados los multiplicadores de ingreso y de empleo.

Estos datos los lee el parser y quedan en `parse(...)['extra']`. Todavía no se escriben en el libro, para que México conserve la misma estructura de pestañas que los demás países.

| Año | Remuneraciones (D.1) | Excedente bruto (B.2b) | Puestos de trabajo (PT) |
|----:|----:|----:|----:|
| 2008 | 3,411,296 | 8,460,012 | 47,439,094 |
| 2013 | 4,542,853 | 11,012,348 | 57,465,990 |
| 2018 | 5,974,564 | 16,768,396 | 59,505,022 |
