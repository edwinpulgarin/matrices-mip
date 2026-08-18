# ¿Dónde interviene el balanceo RAS, y cuánto?

El RAS (Handbook, Cap. 11) es el **único paso de toda la cadena que cambia celdas sin que lo mande una identidad contable**. Ajusta la utilización hasta que la oferta y el uso cierren a la vez por producto y por industria: escala las filas para que den su total, después las columnas, y repite hasta converger. Es también el único paso que no se puede rehacer con aritmética directa entre las hojas del libro, por ser iterativo.

Por eso conviene tenerlo acotado y a la vista, y por eso el pipeline lo usa lo menos posible. Hay tres formas de cerrar el cuadro y cada libro declara cuál usó:

1. **Cerraba solo** — el cuadro publicado ya cumple las dos identidades y no se toca nada.
2. **Sin tocar nada** — queda un residuo chico y se anota en una columna propia de demanda final, «discrepancia estadística», como hacen las cuentas nacionales. **Ninguna celda leída se modifica**, así que `Z = D·U` se puede rehacer a mano desde las hojas del libro.
3. **RAS** — el residuo es demasiado grande para llamarlo discrepancia (más del 2 % de la oferta de algún producto) y ahí sí se ajusta.

La columna «desbalance al entrar» mide la **calidad del cuadro publicado**, no la del pipeline: si el instituto publica un cuadro que cierra solo, no hay nada que hacer.

## Resumen

- **26 de 35 matrices se arman sin modificar una sola celda leída** (9 cerraban solas y 17 anotan el residuo como discrepancia).
- **Sólo 9 necesitan el RAS.**
- **3 más** (las MIP oficiales de INEGI) no pasan siquiera por el SUT: la matriz viene ya construida por el instituto.

## El cuadro

Ordenado de menor a mayor intervención: arriba las que se pueden cerrar sin discusión, abajo las que hay que mirar.

| # | País | Año | Cómo se cerró | Desbalance al entrar | Discrepancia | Mueve de U | Negativos fijos | fila = columna | Mult. |
|--:|:--|--:|:--|--:|--:|--:|--:|--:|--:|
| 1 | Colombia | 2021 | **cerraba solo** | 2.8e-16 | 0.0000 % | 0.0000 % | — | 6.4e-16 | 1.7728 |
| 2 | Colombia | 2016 | **cerraba solo** | 3.0e-16 | 0.0000 % | 0.0000 % | — | 6.6e-16 | 1.7618 |
| 3 | Colombia | 2017 | **cerraba solo** | 3.1e-16 | 0.0000 % | 0.0000 % | — | 5.6e-16 | 1.7596 |
| 4 | Colombia | 2019 | **cerraba solo** | 3.5e-16 | 0.0000 % | 0.0000 % | — | 6.6e-16 | 1.7553 |
| 5 | Colombia | 2018 | **cerraba solo** | 4.1e-16 | 0.0000 % | 0.0000 % | — | 5.8e-16 | 1.7511 |
| 6 | Brasil | 2019 | **cerraba solo** | 4.3e-16 | 0.0000 % | 0.0000 % | — | 8.3e-16 | 1.8472 |
| 7 | Colombia | 2020 | **cerraba solo** | 4.6e-16 | 0.0000 % | 0.0000 % | — | 4.7e-16 | 1.7728 |
| 8 | Colombia | 2022 | **cerraba solo** | 4.8e-16 | 0.0000 % | 0.0000 % | — | 4.5e-16 | 1.7565 |
| 9 | Brasil | 2018 | **cerraba solo** | 7.0e-16 | 0.0000 % | 0.0000 % | — | 6.5e-16 | 1.8454 |
| 10 | México | 2013 | **sin tocar nada** | 2.6e-05 | 0.0002 % | 0.0000 % | — | 1.2e-15 | 1.5174 |
| 11 | Argentina | 2004 | **sin tocar nada** | 7.6e-05 | 0.0000 % | 0.0000 % | — | 9.3e-16 | 1.7547 |
| 12 | Brasil | 2021 | **sin tocar nada** | 2.2e-04 | 0.0018 % | 0.0000 % | — | 6.1e-16 | 1.8933 |
| 13 | Colombia | 2015 | **sin tocar nada** | 2.4e-04 | 0.0005 % | 0.0000 % | — | 6.1e-16 | 1.7550 |
| 14 | Brasil | 2015 | **sin tocar nada** | 2.9e-04 | 0.0029 % | 0.0000 % | — | 4.3e-16 | 1.8118 |
| 15 | Brasil | 2017 | **sin tocar nada** | 6.3e-04 | 0.0056 % | 0.0000 % | — | 6.8e-16 | 1.8380 |
| 16 | Brasil | 2014 | **sin tocar nada** | 8.3e-04 | 0.0076 % | 0.0000 % | — | 6.0e-16 | 1.8401 |
| 17 | Colombia | 2024 | **sin tocar nada** | 8.6e-04 | 0.0091 % | 0.0000 % | — | 7.1e-16 | 1.7770 |
| 18 | Brasil | 2010 | **sin tocar nada** | 9.6e-04 | 0.0089 % | 0.0000 % | — | 4.1e-16 | 1.8132 |
| 19 | Brasil | 2012 | **sin tocar nada** | 1.2e-03 | 0.0099 % | 0.0000 % | — | 5.7e-16 | 1.8336 |
| 20 | Brasil | 2013 | **sin tocar nada** | 1.3e-03 | 0.0113 % | 0.0000 % | — | 6.3e-16 | 1.8307 |
| 21 | Brasil | 2011 | **sin tocar nada** | 1.4e-03 | 0.0108 % | 0.0000 % | — | 5.8e-16 | 1.8269 |
| 22 | Brasil | 2020 | **sin tocar nada** | 2.9e-03 | 0.0299 % | 0.0000 % | — | 5.8e-16 | 1.8479 |
| 23 | Colombia | 2023 | **sin tocar nada** | 5.2e-03 | 0.0569 % | 0.0000 % | — | 5.0e-16 | 1.7785 |
| 24 | Brasil | 2016 | **sin tocar nada** | 6.4e-03 | 0.0655 % | 0.0000 % | — | 5.7e-16 | 1.8370 |
| 25 | Colombia | 2014 | **sin tocar nada** | 1.1e-02 | 0.0479 % | 0.0000 % | — | 6.5e-16 | 1.7445 |
| 26 | Uruguay | 2016 | **sin tocar nada** | 1.4e-02 | 0.0418 % | 0.0000 % | — | 4.6e-16 | 1.6685 |
| 27 | Argentina | 2020 | RAS | 3.4e-02 | 0.0000 % | 0.2199 % | 97 | 6.1e-13 | 1.7489 |
| 28 | Argentina | 1997 | RAS | 4.5e-02 | 0.0000 % | 0.2539 % | 45 | 8.3e-16 | 1.7525 |
| 29 | Uruguay | 2012 | RAS | 5.5e-02 | 0.0000 % | 0.3556 % | 22 | 8.6e-13 | 1.6508 |
| 30 | Argentina | 2022 | RAS | 5.7e-02 | 0.0000 % | 0.1941 % | 68 | 6.2e-13 | 1.7626 |
| 31 | Argentina | 2023 | RAS | 7.7e-02 | 0.0000 % | 0.1256 % | 69 | 6.2e-13 | 1.7730 |
| 32 | Argentina | 2021 | RAS | 1.3e-01 | 0.0000 % | 0.2165 % | 54 | 6.3e-13 | 1.7577 |
| 33 | Uruguay | 2017 | RAS | 2.4e-01 | 0.0000 % | 0.9117 % | 14 | 6.6e-13 | 1.6023 |
| 34 | Argentina | 2019 | RAS | 2.9e-01 | 0.0000 % | 0.1066 % | 83 | 5.6e-13 | 1.7450 |
| 35 | Argentina | 2018 | RAS | 5.9e-01 | 0.0000 % | 0.1429 % | 99 | 6.0e-13 | 1.7462 |
| — | México | 2008 | no aplica | — | — | — | — | — | — |
| — | México | 2013 | no aplica | — | — | — | — | — | — |
| — | México | 2018 | no aplica | — | — | — | — | — | — |

## El patrón: son comercio y transporte

Los productos que obligan al ajuste son casi siempre los mismos: **servicios de comercio y de transporte**. No es casualidad ni ruido — son las filas que PRESTAN los márgenes. El paso de precios de comprador a básicos les saca el margen a los bienes y se lo devuelve a esas filas (§7.77), y como el reparto entre celdas es proporcional, el residuo de esa operación aterriza ahí.

Es una buena noticia para la auditoría: el RAS no está tapando un error disperso, está cerrando el residuo de un paso identificado. Si el desbalance apareciera en un producto agrícola aislado, como pasó con el tabaco, ahí sí habría que ir a mirar la lectura de la fuente.

«Negativos fijos» son las celdas que la fuente publica en negativo —variación de existencias— y que quedan **fuera** del ajuste: el RAS es multiplicativo y sólo está definido sobre celdas no negativas (Box 11.3). Se conservan con su valor exacto y su aporte se descuenta del margen de su fila y de su columna.

## Cómo leer cada bloque

### Colombia

- 11 de 11 años **no necesitan** el ajuste.
- El año que más lo necesita es **2021**: mueve el 0.0000 % de la utilización, y la celda que más cambia lo hace en 0 (miles de millones de pesos corrientes).
- El que entra **peor** es **2014**: hay un producto desbalanceado en 1.1 % de su propia oferta antes del ajuste.
- Los productos que obligan al ajuste en 2014:

  | Producto | Desbalance | Sobre su oferta |
  |:--|--:|--:|
  | 01 · Productos de la agricultura y la horticultur | 399 | 1.1 % |
  | 84 · Servicios de telecomunicaciones, transmisión | 154 | 0.5 % |
  | 61 + 62 · Servicios de comercio (venta al por mayor y  | 83 | 0.1 % |

### Brasil

- 12 de 12 años **no necesitan** el ajuste.
- El año que más lo necesita es **2019**: mueve el 0.0000 % de la utilización, y la celda que más cambia lo hace en 0 (millones de reales corrientes).
- El que entra **peor** es **2016**: hay un producto desbalanceado en 0.6 % de su propia oferta antes del ajuste.
- Los productos que obligan al ajuste en 2016:

  | Producto | Desbalance | Sobre su oferta |
  |:--|--:|--:|
  | 46801 · Comércio por atacado e a varejo, exceto veíc | -5,847 | 0.6 % |
  | 45001 · Comércio e reparação de veículos | -570 | 0.4 % |
  | 49001 · Transporte terrestre de carga | -481 | 0.2 % |

### México

- 1 de 1 años **no necesitan** el ajuste.
- El año que más lo necesita es **2013**: mueve el 0.0000 % de la utilización, y la celda que más cambia lo hace en 0 (millones de pesos corrientes).
- El que entra **peor** es **2013**: hay un producto desbalanceado en 0.0 % de su propia oferta antes del ajuste.
- Los productos que obligan al ajuste en 2013:

  | Producto | Desbalance | Sobre su oferta |
  |:--|--:|--:|
  | 4611 · Comercio al por menor de abarrotes y aliment | 48 | 0.0 % |

### Argentina

- 1 de 8 años **no necesitan** el ajuste.
- El año que más lo necesita es **1997**: mueve el 0.2539 % de la utilización, y la celda que más cambia lo hace en 11,823 (miles de pesos corrientes de 1997).
- El que entra **peor** es **2018**: hay un producto desbalanceado en 59.0 % de su propia oferta antes del ajuste.
- Los productos que obligan al ajuste en 2018:

  | Producto | Desbalance | Sobre su oferta |
  |:--|--:|--:|
  | SERVICIOS DE TRANSPORTE DE CARGA POR VIA · Servicios de transporte de carga por vía aér | 4,536,757 | 59.0 % |
  | SG SEGUROS GENERALES · 713 SG - Seguros Generales | 3,399,182 | 3.7 % |
  | C SERVICIOS DE TRANSPORTE POR CARRETERA  · 643 C - Servicios de transporte por carreter | 2,318,274 | 0.7 % |

### Uruguay

- 1 de 3 años **no necesitan** el ajuste.
- El año que más lo necesita es **2017**: mueve el 0.9117 % de la utilización, y la celda que más cambia lo hace en 257 (millones de pesos uruguayos corrientes).
- El que entra **peor** es **2017**: hay un producto desbalanceado en 23.8 % de su propia oferta antes del ajuste.
- Los productos que obligan al ajuste en 2017:

  | Producto | Desbalance | Sobre su oferta |
  |:--|--:|--:|
  | 49 · Combustibles para calderas (fuel oil y diese | 2,448 | 23.8 % |
  | 52 · Abonos y plaguicidas | 347 | 6.5 % |
  | 79 · Servicio de transporte de carga | 2,784 | 4.7 % |

