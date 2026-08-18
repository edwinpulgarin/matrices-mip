# Z doméstica vs. Z total — efecto sobre los indicadores

Comparación de las dos versiones de la misma matriz, con el mismo COU, la misma valoración y el mismo Modelo D detrás. Lo único que cambia es **dónde entra el insumo importado**: fuera de `Z` y en una fila primaria (versión DOMÉSTICA, la única que se publica) o dentro de `Z` (versión TOTAL, que este script recalcula desde la fuente para poder medirla).

Generado por `scripts/comparar_dom_total.py`. Datos completos en `reports/comparacion_dom_total.csv`.

## 1. La Z publicada es la doméstica

Se reabre cada libro entregado, se lee la hoja «Z consumos intermedios» y se confronta su suma contra las dos versiones recalculadas. Es lo que `validar_consistencia.py` no puede ver: ese script re-verifica `A ≈ Z·diag(g)⁻¹` y `L ≈ (I−A)⁻¹` **a partir de la Z del archivo**, así que confirma que todo lo posterior sale de esa matriz, pero no cuál de las dos es.

| Qué contiene la hoja Z del libro | Libros |
|:--|--:|
| doméstica | 38 |

**Los 38 libros publican la Z doméstica**, y con ella se calculan los coeficientes técnicos, la inversa de Leontief y los multiplicadores de cada libro.

## 2. Por qué los indicadores tienen que bajar

La hipótesis del equipo se cumple. En el agregado no es un resultado empírico sino una consecuencia de la construcción: las dos versiones comparten el vector de producción `x`, y la utilización total es `U_dom + U_imp` con `U_imp ≥ 0`, de modo que

```
A_tot ≥ A_dom   celda a celda
L = (I − A)⁻¹ = I + A + A² + …   (serie de Neumann, converge con A ≥ 0)
⇒ L_tot ≥ L_dom  ⇒  todo multiplicador de columna es mayor
```

Lo empírico —y lo que sí hay que leer— es la **magnitud** de la brecha, que es la apertura importadora de cada economía, y si el **orden** de los sectores sobrevive al cambio de definición.

### La salvedad del balanceo

La desigualdad de arriba vale para el SUT tal como sale de la valoración. Pero el RAS se corre **por separado en cada versión**, así que en los libros donde interviene la monotonía puede romperse en celdas sueltas. Medido en los 38 casos:

| Nivel | Qué es | Mínimo de la diferencia total − doméstica |
|:--|:--|--:|
| Celda de A | `aᵢⱼ` | -7.50e-03 |
| Celda de L | `lᵢⱼ` | -7.06e-03 |
| Columna de A | **coeficiente técnico `Σᵢaᵢⱼ`** | 0.00e+00 |
| Columna de L | **multiplicador de producción** | 0.00e+00 |

**Los dos niveles que usa el equipo —el coeficiente técnico y el multiplicador— no se rompen en ningún sector de ningún año.** La ruptura existe sólo dentro de la columna, entre celdas que se compensan.

El mínimo exacto de 0,00 corresponde a sectores sin consumo intermedio —servicio doméstico y actividades de hogares—, cuya columna de `A` es nula en las dos versiones y cuyo multiplicador es 1,0000 en ambas. No es un sector con producción cero: son actividades sin insumos.

Ocurre en 9 de los 38 casos, y son exactamente los 9 donde el RAS actúa sobre la versión doméstica: sin balanceo la desigualdad no falla nunca.

| País | Año | RAS doméstica | RAS total | Celdas de A que bajan | Mín. `Δaᵢⱼ` |
|:--|--:|:-:|:-:|--:|--:|
| Argentina | 1997 | sí | sí | 9.50 % | -6.1e-05 |
| Argentina | 2018 | sí | no | 6.33 % | -7.5e-03 |
| Argentina | 2019 | sí | no | 7.90 % | -1.3e-03 |
| Argentina | 2020 | sí | no | 4.88 % | -2.8e-03 |
| Argentina | 2021 | sí | no | 5.88 % | -2.3e-03 |
| Argentina | 2022 | sí | no | 5.71 % | -1.8e-03 |
| Argentina | 2023 | sí | no | 5.93 % | -8.6e-04 |
| Uruguay | 2012 | sí | no | 3.43 % | -5.1e-03 |
| Uruguay | 2017 | sí | sí | 14.38 % | -3.6e-03 |

Y el patrón dice algo que vale la pena mirar aparte: en 7 de los 9 el RAS corre **sobre la versión doméstica y no sobre la total**. Ahí el SUT total entra cumpliendo las identidades y no hay nada que balancear: el desbalance aparece al separar el origen. O sea que lo que el RAS cierra en esos libros es, en buena parte, el residuo que deja el propio supuesto de proporcionalidad de las importaciones (§8.33). Es una medición nueva del costo de ese supuesto, independiente de las cuatro que ya están en `reports/sesgo_prorrateo.md`.

Cierre de Leontief en las dos versiones: `L·f = x` en la doméstica y `L·(f − m) = x` en la total, con residuo relativo máximo 3.4e-14.

## 3. Cuánto cambia, por país y por año

`Σᵢaᵢⱼ` es el efecto directo medio (la primera vuelta de compras); el multiplicador es la suma de la columna de L; el indirecto es el resto. «Importado % del CI» es la fracción del consumo intermedio que queda afuera de la matriz doméstica, y es la que explica el tamaño de todo lo demás.


### Argentina

| Año | Variante | n | Importado % del CI | Σᵢaᵢⱼ dom. | Σᵢaᵢⱼ total | Mult. dom. | Mult. total | Δ mult. | Δ directo | Δ indirecto |
|----:|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1997 | MIPAr97 · sin prorrateo | 124 | 9.9 % | 0.4418 | 0.5218 | 1.7525 | 2.0397 | **+16.39 %** | +18.09 % | +66.73 % |
| 2004 | COU · prorrateo | 162 | 10.0 % | 0.4320 | 0.4900 | 1.7547 | 1.9764 | **+12.63 %** | +13.43 % | +50.71 % |
| 2018 | COU · prorrateo | 107 | 11.3 % | 0.4256 | 0.4934 | 1.7462 | 2.0108 | **+15.15 %** | +15.91 % | +61.43 % |
| 2019 | COU · prorrateo | 107 | 10.3 % | 0.4252 | 0.4899 | 1.7450 | 1.9881 | **+13.93 %** | +15.21 % | +55.77 % |
| 2020 | COU · prorrateo | 107 | 10.4 % | 0.4274 | 0.4915 | 1.7489 | 1.9959 | **+14.12 %** | +15.01 % | +56.86 % |
| 2021 | COU · prorrateo | 107 | 11.1 % | 0.4313 | 0.4981 | 1.7577 | 2.0289 | **+15.43 %** | +15.48 % | +62.66 % |
| 2022 | COU · prorrateo | 107 | 11.0 % | 0.4324 | 0.4983 | 1.7626 | 2.0396 | **+15.71 %** | +15.24 % | +63.91 % |
| 2023 | COU · prorrateo | 107 | 10.0 % | 0.4343 | 0.4918 | 1.7730 | 2.0076 | **+13.23 %** | +13.24 % | +52.27 % |

### Brasil

| Año | Variante | n | Importado % del CI | Σᵢaᵢⱼ dom. | Σᵢaᵢⱼ total | Mult. dom. | Mult. total | Δ mult. | Δ directo | Δ indirecto |
|----:|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2010 | MIP n67 · sin prorrateo | 67 | 10.9 % | 0.4471 | 0.5137 | 1.8132 | 2.0998 | **+15.81 %** | +14.89 % | +60.11 % |
| 2011 | COU n68 · prorrateo | 68 | 9.4 % | 0.4518 | 0.5048 | 1.8269 | 2.0753 | **+13.60 %** | +11.75 % | +52.10 % |
| 2012 | COU n68 · prorrateo | 68 | 10.0 % | 0.4532 | 0.5109 | 1.8336 | 2.1087 | **+15.01 %** | +12.74 % | +57.16 % |
| 2013 | COU n68 · prorrateo | 68 | 10.7 % | 0.4526 | 0.5131 | 1.8307 | 2.1213 | **+15.87 %** | +13.36 % | +60.83 % |
| 2014 | COU n68 · prorrateo | 68 | 10.6 % | 0.4553 | 0.5158 | 1.8401 | 2.1320 | **+15.87 %** | +13.30 % | +60.13 % |
| 2015 | MIP n67 · sin prorrateo | 67 | 13.1 % | 0.4478 | 0.5303 | 1.8118 | 2.1769 | **+20.15 %** | +18.43 % | +77.58 % |
| 2016 | COU n68 · prorrateo | 68 | 9.7 % | 0.4601 | 0.5210 | 1.8370 | 2.0995 | **+14.29 %** | +13.22 % | +53.50 % |
| 2017 | COU n68 · prorrateo | 68 | 9.7 % | 0.4597 | 0.5182 | 1.8380 | 2.0989 | **+14.20 %** | +12.72 % | +53.52 % |
| 2018 | COU n68 · prorrateo | 68 | 10.8 % | 0.4573 | 0.5226 | 1.8454 | 2.1594 | **+17.02 %** | +14.29 % | +64.08 % |
| 2019 | COU n68 · prorrateo | 68 | 11.1 % | 0.4589 | 0.5270 | 1.8472 | 2.1730 | **+17.63 %** | +14.82 % | +66.36 % |
| 2020 | COU n68 · prorrateo | 68 | 11.5 % | 0.4578 | 0.5312 | 1.8479 | 2.1991 | **+19.00 %** | +16.04 % | +71.18 % |
| 2021 | COU n68 · prorrateo | 68 | 12.3 % | 0.4686 | 0.5446 | 1.8933 | 2.2976 | **+21.35 %** | +16.23 % | +77.27 % |

### Colombia

| Año | Variante | n | Importado % del CI | Σᵢaᵢⱼ dom. | Σᵢaᵢⱼ total | Mult. dom. | Mult. total | Δ mult. | Δ directo | Δ indirecto |
|----:|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2014 | COU · prorrateo | 61 | 11.2 % | 0.4311 | 0.4952 | 1.7445 | 1.9921 | **+14.20 %** | +14.85 % | +58.60 % |
| 2015 | COU · prorrateo | 61 | 11.9 % | 0.4333 | 0.5019 | 1.7550 | 2.0237 | **+15.31 %** | +15.84 % | +62.19 % |
| 2016 | COU · prorrateo | 61 | 11.2 % | 0.4358 | 0.5011 | 1.7618 | 2.0107 | **+14.13 %** | +14.98 % | +56.33 % |
| 2017 | COU · prorrateo | 61 | 10.9 % | 0.4360 | 0.5009 | 1.7596 | 2.0011 | **+13.73 %** | +14.88 % | +54.59 % |
| 2018 | COU · prorrateo | 61 | 11.2 % | 0.4318 | 0.5001 | 1.7511 | 2.0029 | **+14.38 %** | +15.81 % | +57.52 % |
| 2019 | COU · prorrateo | 61 | 11.5 % | 0.4336 | 0.5027 | 1.7553 | 2.0121 | **+14.63 %** | +15.96 % | +58.33 % |
| 2020 | COU · prorrateo | 61 | 11.2 % | 0.4393 | 0.5082 | 1.7728 | 2.0293 | **+14.47 %** | +15.68 % | +56.25 % |
| 2021 | COU · prorrateo | 61 | 12.5 % | 0.4361 | 0.5126 | 1.7728 | 2.0726 | **+16.91 %** | +17.54 % | +66.29 % |
| 2022 | COU · prorrateo | 61 | 14.4 % | 0.4297 | 0.5172 | 1.7565 | 2.1087 | **+20.05 %** | +20.35 % | +81.00 % |
| 2023 | COU · prorrateo | 61 | 11.9 % | 0.4367 | 0.5099 | 1.7785 | 2.0618 | **+15.93 %** | +16.78 % | +61.45 % |
| 2024 | COU · prorrateo | 61 | 11.0 % | 0.4375 | 0.5057 | 1.7770 | 2.0349 | **+14.52 %** | +15.59 % | +55.90 % |

### México

| Año | Variante | n | Importado % del CI | Σᵢaᵢⱼ dom. | Σᵢaᵢⱼ total | Mult. dom. | Mult. total | Δ mult. | Δ directo | Δ indirecto |
|----:|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2013 | COU · sin prorrateo | 262 | 32.5 % | 0.3581 | 0.4962 | 1.5174 | 2.0445 | **+34.74 %** | +38.58 % | +244.13 % |
| 2008 | MIP oficial INEGI | 262 | 29.7 % | 0.3482 | 0.4783 | 1.5110 | 1.9783 | **+30.92 %** | +37.35 % | +207.10 % |
| 2013 | MIP oficial INEGI | 262 | 32.5 % | 0.3581 | 0.4962 | 1.5185 | 2.0485 | **+34.90 %** | +38.58 % | +244.25 % |
| 2018 | MIP oficial INEGI | 263 | 38.2 % | 0.3130 | 0.4728 | 1.4338 | 2.0279 | **+41.44 %** | +51.06 % | +359.68 % |

### Uruguay

| Año | Variante | n | Importado % del CI | Σᵢaᵢⱼ dom. | Σᵢaᵢⱼ total | Mult. dom. | Mult. total | Δ mult. | Δ directo | Δ indirecto |
|----:|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 2012 | COU · prorrateo | 107 | 17.3 % | 0.4051 | 0.5060 | 1.6508 | 2.0054 | **+21.48 %** | +24.89 % | +103.28 % |
| 2016 | COU · prorrateo | 95 | 14.5 % | 0.4076 | 0.4930 | 1.6685 | 1.9837 | **+18.89 %** | +20.94 % | +88.09 % |
| 2017 | COU · origen medido | 95 | 16.2 % | 0.3804 | 0.4896 | 1.6023 | 1.9694 | **+22.91 %** | +28.71 % | +116.25 % |

## 4. Resumen por país

| País | Años | Importado % del CI | Mult. dom. | Mult. total | Δ mult. | Δ directo | Δ indirecto |
|:--|--:|--:|--:|--:|--:|--:|--:|
| Argentina | 8 | 10.5 % | 1.7551 | 2.0109 | **+14.58 %** | +15.20 % | +58.79 % |
| Brasil | 12 | 10.8 % | 1.8388 | 2.1451 | **+16.65 %** | +14.32 % | +62.82 % |
| Colombia | 11 | 11.7 % | 1.7623 | 2.0318 | **+15.30 %** | +16.21 % | +60.77 % |
| México | 4 | 33.2 % | 1.4952 | 2.0248 | **+35.50 %** | +41.39 % | +263.79 % |
| Uruguay | 3 | 16.0 % | 1.6405 | 1.9862 | **+21.09 %** | +24.85 % | +102.54 % |

El orden de la brecha es el orden de la apertura importadora, no del tamaño de la economía: donde la producción usa más insumo importado, más se infla la matriz total.

### El efecto que más importa: la versión total borra las diferencias entre países

En la matriz doméstica los cinco países se reparten entre **1,50 y 1,84**; en la total se amontonan entre **1,99 y 2,15**. La brecha entre el mayor y el menor multiplicador medio pasa de **23 %** a **8 %**.

No es casualidad: el multiplicador de la matriz total mide cuánta producción —de donde sea— hace falta por unidad de demanda, y eso es parecido en cualquier economía. El de la matriz doméstica mide cuánta producción **del propio país** se activa, que es la pregunta de política. México es el caso extremo: con la matriz doméstica queda último (1,49) porque su cadena local es corta, y con la total pasa a ser indistinguible del resto (2,02). **La lectura de «profundidad de la cadena doméstica» sólo existe en la versión que se publica.**

## 5. ¿Sobrevive el ranking de sectores?

Que todos los multiplicadores suban no implica que suban parejo. Si el orden cambiara, las dos versiones no sólo diferirían en nivel: dirían cosas distintas sobre qué sector es clave. `ρ` es la correlación de rangos entre las dos versiones; «top-10 en común» cuenta cuántos de los diez mayores multiplicadores se repiten; «cambian de tipo» son los sectores que cruzan el umbral 1 de Rasmussen y pasan de clave a otra categoría o al revés. (No se reporta ρ del encadenamiento hacia atrás: `BL` es la suma de columna de L dividida por una constante, o sea una transformación monótona del multiplicador, y su correlación de rangos es idéntica por construcción. `FL` sí es otro objeto: se arma con las filas.)

| País | Año | ρ multiplicador | ρ FL | Top-10 en común | Cambian de tipo | Sector con mayor brecha | Brecha |
|:--|--:|--:|--:|--:|--:|:--|--:|
| Argentina | 1997 | 0.7993 | 0.9253 | 5/10 | 33 de 124 | Vehículos automotores | +66.1 % |
| Argentina | 2004 | 0.8990 | 0.9617 | 5/10 | 24 de 162 | Fabricacion de transmisores de radio y telev | +98.6 % |
| Argentina | 2018 | 0.8986 | 0.9743 | 3/10 | 16 de 107 | Fabricación de tubos, válvulas y otros compo | +84.2 % |
| Argentina | 2019 | 0.8975 | 0.9759 | 4/10 | 16 de 107 | Fabricación de tubos, válvulas y otros compo | +77.0 % |
| Argentina | 2020 | 0.9009 | 0.9779 | 4/10 | 15 de 107 | Fabricación de tubos, válvulas y otros compo | +74.6 % |
| Argentina | 2021 | 0.9027 | 0.9741 | 5/10 | 16 de 107 | Fabricación de tubos, válvulas y otros compo | +98.4 % |
| Argentina | 2022 | 0.8927 | 0.9756 | 4/10 | 15 de 107 | Fabricación de tubos, válvulas y otros compo | +100.7 % |
| Argentina | 2023 | 0.9232 | 0.9764 | 5/10 | 9 de 107 | Fabricación de tubos, válvulas y otros compo | +89.0 % |
| Brasil | 2010 | 0.9185 | 0.9650 | 6/10 | 10 de 67 | Fabricação de equipamentos de informática, p | +66.0 % |
| Brasil | 2011 | 0.9616 | 0.9785 | 7/10 | 10 de 68 | Fabricação de químicos orgânicos e inorgânic | +45.6 % |
| Brasil | 2012 | 0.9562 | 0.9771 | 7/10 | 7 de 68 | Fabricação de químicos orgânicos e inorgânic | +49.4 % |
| Brasil | 2013 | 0.9528 | 0.9751 | 7/10 | 9 de 68 | Fabricação de químicos orgânicos e inorgânic | +52.2 % |
| Brasil | 2014 | 0.9592 | 0.9742 | 6/10 | 10 de 68 | Fabricação de químicos orgânicos e inorgânic | +50.7 % |
| Brasil | 2015 | 0.8956 | 0.9433 | 4/10 | 10 de 67 | Fabricação de equipamentos de informática, p | +79.4 % |
| Brasil | 2016 | 0.9388 | 0.9710 | 7/10 | 11 de 68 | Fabricação de equipamentos de informática, p | +46.2 % |
| Brasil | 2017 | 0.9410 | 0.9674 | 5/10 | 7 de 68 | Fabricação de equipamentos de informática, p | +49.4 % |
| Brasil | 2018 | 0.9258 | 0.9644 | 5/10 | 12 de 68 | Fabricação de equipamentos de informática, p | +59.3 % |
| Brasil | 2019 | 0.9214 | 0.9652 | 6/10 | 14 de 68 | Fabricação de equipamentos de informática, p | +62.2 % |
| Brasil | 2020 | 0.9001 | 0.9612 | 5/10 | 13 de 68 | Fabricação de equipamentos de informática, p | +73.2 % |
| Brasil | 2021 | 0.8819 | 0.9600 | 4/10 | 11 de 68 | Fabricação de equipamentos de informática, p | +88.5 % |
| Colombia | 2014 | 0.9103 | 0.9811 | 7/10 | 7 de 61 | Fabricación de vehículos automotores, remolq | +45.5 % |
| Colombia | 2015 | 0.9093 | 0.9822 | 7/10 | 11 de 61 | Fabricación de vehículos automotores, remolq | +48.1 % |
| Colombia | 2016 | 0.9204 | 0.9849 | 8/10 | 8 de 61 | Fabricación de vehículos automotores, remolq | +48.7 % |
| Colombia | 2017 | 0.9098 | 0.9772 | 8/10 | 5 de 61 | Fabricación de vehículos automotores, remolq | +49.4 % |
| Colombia | 2018 | 0.8886 | 0.9793 | 8/10 | 8 de 61 | Fabricación de vehículos automotores, remolq | +55.9 % |
| Colombia | 2019 | 0.8912 | 0.9770 | 8/10 | 8 de 61 | Fabricación de vehículos automotores, remolq | +56.1 % |
| Colombia | 2020 | 0.8868 | 0.9764 | 8/10 | 7 de 61 | Fabricación de vehículos automotores, remolq | +63.8 % |
| Colombia | 2021 | 0.8893 | 0.9775 | 6/10 | 9 de 61 | Fabricación de vehículos automotores, remolq | +60.2 % |
| Colombia | 2022 | 0.8694 | 0.9705 | 6/10 | 11 de 61 | Fabricación de vehículos automotores, remolq | +66.0 % |
| Colombia | 2023 | 0.9076 | 0.9784 | 6/10 | 11 de 61 | Fabricación de vehículos automotores, remolq | +55.0 % |
| Colombia | 2024 | 0.9125 | 0.9796 | 6/10 | 9 de 61 | Fabricación de vehículos automotores, remolq | +51.5 % |
| México | 2013 | 0.6341 | 0.8957 | 0/10 | 75 de 262 | Fabricación de equipo de audio y de video | +243.7 % |
| México | 2008 | 0.5859 | 0.8916 | 0/10 | 92 de 262 | Fabricación de equipo de audio y de video | +284.8 % |
| México | 2013 | 0.6334 | 0.8922 | 0/10 | 74 de 262 | Fabricación de equipo de audio y de video | +244.9 % |
| México | 2018 | 0.4315 | 0.9197 | 0/10 | 102 de 263 | Fabricación de computadoras y equipo perifér | +210.1 % |
| Uruguay | 2012 | 0.8878 | 0.9501 | 4/10 | 25 de 107 | Fabricación de gas, distribución de combusti | +93.0 % |
| Uruguay | 2016 | 0.8751 | 0.9515 | 5/10 | 17 de 95 | Fabricación de gas, distribución de combusti | +96.9 % |
| Uruguay | 2017 | 0.8194 | 0.9433 | 4/10 | 28 de 95 | Fabricación de abonos y compuestos de nitróg | +76.9 % |

El ranking se degrada exactamente en el orden de la apertura: donde el insumo importado pesa poco, el reordenamiento es menor y el top-10 sobrevive casi entero; donde pesa mucho, las dos versiones dejan de hablar del mismo sector clave.

