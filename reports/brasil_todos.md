# Brasil — MIP reconstruidas desde el IBGE (UN Handbook F74 Rev.1)

Industria × industria, Modelo D, precios básicos, millones de reales corrientes.

**2010 y 2015 salen sin prorrateo**: la publicación de la Matriz de Insumo-Produto del IBGE mide el consumo intermedio nacional e importado y el destino de cada impuesto y margen celda a celda (Tabelas 03-10). Es nivel 67, no 68. El resto de los años sólo tiene el COU, que publica importaciones, impuestos y márgenes por producto, así que dependen del prorrateo del Handbook §7.77.

| Año | Origen | Dim | VBP | VAB | fila=columna | L·f=x | min Z | mult. medio |
|----:|:-------|----:|----:|----:|:---:|:---:|:---:|:---:|
| 2010 | MIP n67 · **sin prorrateo** | 67×67 | 6,599,735 | 3,065,633 | 2.2e-15 | 1.6e-16 | 0.00 | 1.8132 ✅ |
| 2011 | COU n68 · prorrateo | 68×68 | 7,438,812 | 3,720,461 | 2.4e-15 | 1.3e-16 | 0.00 | 1.8270 ✅ |
| 2012 | COU n68 · prorrateo | 68×68 | 8,223,994 | 4,094,259 | 1.6e-15 | 1.3e-16 | 0.00 | 1.8334 ✅ |
| 2013 | COU n68 · prorrateo | 68×68 | 9,106,082 | 4,553,760 | 1.6e-15 | 1.2e-16 | 0.00 | 1.8305 ✅ |
| 2014 | COU n68 · prorrateo | 68×68 | 9,888,356 | 4,972,734 | 1.4e-15 | 5.9e-17 | 0.00 | 1.8399 ✅ |
| 2015 | MIP n67 · **sin prorrateo** | 67×67 | 10,227,167 | 4,755,930 | 1.5e-15 | 8.0e-17 | 0.00 | 1.8118 ✅ |
| 2016 | COU n68 · prorrateo | 68×68 | 10,542,089 | 5,419,822 | 1.4e-15 | 1.1e-16 | 0.00 | 1.8356 ✅ |
| 2017 | COU n68 · prorrateo | 68×68 | 11,021,027 | 5,671,926 | 1.5e-15 | 7.4e-17 | 0.00 | 1.8374 ✅ |
| 2018 | COU n68 · prorrateo | 68×68 | 12,010,010 | 6,011,150 | 1.3e-15 | 8.7e-17 | 0.00 | 1.8443 ✅ |
| 2019 | COU n68 · prorrateo | 68×68 | 12,741,791 | 6,356,684 | 1.2e-15 | 6.4e-17 | 0.00 | 1.8465 ✅ |
| 2020 | COU n68 · prorrateo | 68×68 | 13,306,389 | 6,594,937 | 1.4e-15 | 7.0e-17 | 0.00 | 1.8470 ✅ |
| 2021 | COU n68 · prorrateo | 68×68 | 16,582,167 | 7,713,999 | 1.2e-15 | 5.6e-17 | 0.00 | 1.8934 ✅ |

## Control: cuánto cambia el multiplicador por prorratear

Los dos años donde existe el dato medido permiten cuantificar el sesgo que cargan los otros diez. Ojo: el nivel de agregación también difiere (67 vs 68), así que parte de la diferencia es de agregación y no sólo de método.

| Año | Sin prorrateo | Con prorrateo | Diferencia |
|----:|----:|----:|----:|
| 2010 | 1.8132 (n67) | 1.8374 (n68) | **+1.34 %** |
| 2015 | 1.8118 (n67) | 1.8403 (n68) | **+1.57 %** |
