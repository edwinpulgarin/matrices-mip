# Colombia — MIP reconstruidas desde el COU del DANE (UN Handbook F74 Rev.1)

Industria × industria, Modelo D, **matriz doméstica** (importaciones en fila primaria), precios básicos, miles de millones de pesos corrientes, base 2015. La versión total (nacional + importada) no se publica: todo lo que trae el libro se deriva de esta matriz.

**Todo sale del COU**: oferta, utilización a precios de comprador y el puente de valoración por producto. Dos supuestos: el reparto proporcional de impuestos y márgenes dentro de cada fila (§7.76) y el de origen (§8.33), que separa lo nacional de lo importado dentro de cada celda.

**El balanceo no modifica ninguna celda, en ningún año.** Siete de los once cuadros entran cumpliendo las identidades y no hay nada que hacer; en los otros cuatro queda un residuo del propio cuadro publicado y se anota como «discrepancia estadística» en la demanda final, sin tocar la utilización. Ver `reports/estado_ras.md`.

| Año | Dim | VBP | VAB | Interm. total | Insumo importado | fila=columna | L·f=x | min Z | mult. medio |
|----:|----:|----:|----:|----:|----:|:---:|:---:|:---:|:---:|
| 2014 | 61×61 | 1,341,584 | 694,752 | 547,882 | 69,298 | 6.5e-16 | 2.2e-17 | 0.00 | 1.7445 ✅ |
| 2015 | 61×61 | 1,440,942 | 730,543 | 596,867 | 80,833 | 6.1e-16 | 1.5e-17 | 0.00 | 1.7550 ✅ |
| 2016 | 61×61 | 1,543,703 | 787,719 | 640,885 | 81,142 | 6.6e-16 | 1.9e-17 | 0.00 | 1.7618 ✅ |
| 2017 | 61×61 | 1,618,324 | 835,906 | 664,342 | 81,458 | 5.6e-16 | 1.8e-17 | 0.00 | 1.7596 ✅ |
| 2018 | 61×61 | 1,732,895 | 896,656 | 707,945 | 89,316 | 5.8e-16 | 3.4e-17 | 0.00 | 1.7511 ✅ |
| 2019 | 61×61 | 1,857,445 | 959,792 | 757,403 | 98,304 | 6.6e-16 | 3.1e-17 | 0.00 | 1.7553 ✅ |
| 2020 | 61×61 | 1,751,673 | 909,303 | 715,583 | 89,990 | 4.7e-16 | 1.7e-17 | 0.00 | 1.7728 ✅ |
| 2021 | 61×61 | 2,140,060 | 1,079,574 | 886,543 | 127,128 | 6.4e-16 | 2.0e-17 | 0.00 | 1.7728 ✅ |
| 2022 | 61×61 | 2,674,765 | 1,321,960 | 1,106,532 | 185,718 | 4.5e-16 | 2.2e-17 | 0.00 | 1.7565 ✅ |
| 2023 | 61×61 | 2,839,920 | 1,432,558 | 1,183,631 | 159,707 | 5.0e-16 | 3.1e-17 | 0.00 | 1.7785 ✅ |
| 2024 | 61×61 | 3,013,362 | 1,550,974 | 1,243,329 | 153,072 | 7.1e-16 | 3.9e-17 | 0.00 | 1.7770 ✅ |
