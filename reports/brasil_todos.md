# Brasil — MIP reconstruidas desde el IBGE (UN Handbook F74 Rev.1)

Industria × industria, Modelo D, precios básicos, millones de reales corrientes.

**2010 y 2015 salen sin prorrateo**: la publicación de la Matriz de Insumo-Produto del IBGE mide el consumo intermedio nacional e importado y el destino de cada impuesto y margen celda a celda (Tabelas 03-10). Es nivel 67, no 68. El resto de los años sólo tiene el COU, que publica importaciones, impuestos y márgenes por producto, así que dependen del prorrateo del Handbook §8.33.

| Año | Origen | Dim | VBP | VAB | fila=columna | L·f=x | min Z | mult. medio |
|----:|:-------|----:|----:|----:|:---:|:---:|:---:|:---:|
| 2010 | MIP n67 · **sin prorrateo** | 67×67 | 6,599,735 | 3,065,633 | 4.1e-16 | 3.5e-17 | 0.00 | 1.8132 ✅ |
| 2011 | COU n68 · prorrateo | 68×68 | 7,438,812 | 3,720,461 | 5.8e-16 | 3.5e-17 | 0.00 | 1.8269 ✅ |
| 2012 | COU n68 · prorrateo | 68×68 | 8,223,994 | 4,094,259 | 5.7e-16 | 2.8e-17 | 0.00 | 1.8336 ✅ |
| 2013 | COU n68 · prorrateo | 68×68 | 9,106,082 | 4,553,760 | 6.3e-16 | 2.6e-17 | 0.00 | 1.8307 ✅ |
| 2014 | COU n68 · prorrateo | 68×68 | 9,888,356 | 4,972,734 | 6.0e-16 | 4.7e-17 | 0.00 | 1.8401 ✅ |
| 2015 | MIP n67 · **sin prorrateo** | 67×67 | 10,227,167 | 4,755,930 | 4.3e-16 | 2.3e-17 | 0.00 | 1.8118 ✅ |
| 2016 | COU n68 · prorrateo | 68×68 | 10,542,089 | 5,419,822 | 5.7e-16 | 3.3e-17 | 0.00 | 1.8370 ✅ |
| 2017 | COU n68 · prorrateo | 68×68 | 11,021,027 | 5,671,926 | 6.8e-16 | 2.1e-17 | 0.00 | 1.8380 ✅ |
| 2018 | COU n68 · prorrateo | 68×68 | 12,010,010 | 6,011,150 | 6.5e-16 | 1.9e-17 | 0.00 | 1.8454 ✅ |
| 2019 | COU n68 · prorrateo | 68×68 | 12,741,791 | 6,356,684 | 8.3e-16 | 1.8e-17 | 0.00 | 1.8472 ✅ |
| 2020 | COU n68 · prorrateo | 68×68 | 13,306,389 | 6,594,937 | 5.8e-16 | 3.5e-17 | 0.00 | 1.8479 ✅ |
| 2021 | COU n68 · prorrateo | 68×68 | 16,582,167 | 7,713,999 | 6.1e-16 | 1.4e-17 | 0.00 | 1.8933 ✅ |

## Control: cuánto cambia el multiplicador por prorratear

Los dos años donde existe el dato medido permiten cuantificar los supuestos que cargan los otros diez. Como la matriz publicada es DOMÉSTICA, acá se miden los dos juntos: el reparto de impuestos y márgenes dentro de la fila (§7.76) y el corte por origen (§8.33). Ojo: el nivel de agregación también difiere (67 vs 68), así que parte de la diferencia es de agregación y no sólo de método.

| Año | Sin prorrateo | Con prorrateo | Diferencia |
|----:|----:|----:|----:|
| 2010 | 1.8132 (n67) | 1.8372 (n68) | **+1.32 %** |
| 2015 | 1.8118 (n67) | 1.8411 (n68) | **+1.61 %** |
