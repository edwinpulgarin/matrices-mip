# Uruguay — MIP reconstruidas desde COU BCU (UN Handbook F74 Rev.1)

Industria × industria, Modelo D, precios básicos, millones de pesos uruguayos corrientes.

**2017 sale con el origen medido**: el BCU publica la utilización intermedia nacional e importada celda a celda, así que ahí no se aplica el supuesto de proporcionalidad de las importaciones (§8.33). En 2012 y 2016 sólo hay utilización total, así que el origen se prorratea.

| Año | Origen | Dim | VBP | VAB | Interm. importado | fila=columna | L·f=x | min Z | mult. medio |
|----:|:-------|----:|----:|----:|----:|:---:|:---:|:---:|:---:|
| 2012 | prorrateo | 107×107 | 1,877,436 | 995,057 | 170,357 | 8.6e-13 | 2.8e-14 | 0.00 | 1.6508 ✅ |
| 2016 | prorrateo | 95×95 | 2,778,445 | 1,544,203 | 169,112 | 4.6e-16 | 2.1e-17 | 0.00 | 1.6685 ✅ |
| 2017 | **medido** | 95×95 | 2,931,250 | 1,655,329 | 195,209 | 6.6e-13 | 3.0e-14 | 0.00 | 1.6023 ✅ |