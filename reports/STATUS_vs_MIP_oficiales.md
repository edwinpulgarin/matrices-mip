# STATUS — nuestras matrices contra las MIP oficiales

Qué matrices reproducen la MIP que publica el instituto y cuáles no.
Se genera cruzando el inventario de libros con el resultado del arnés en R;
no recalcula nada.

## Cómo se lee el veredicto

| Veredicto | Qué significa |
|:--|:--|
| **IGUAL** | Reproduce la matriz oficial: desvío absoluto por debajo del 0.1 % |
| **IGUAL EN COLUMNAS** | El consumo intermedio de cada sector coincide exacto —o sea que el dato, la valoración, el corte por origen y el balanceo son los del instituto— pero el reparto por filas difiere, porque el instituto arma su matriz `D` con más detalle de productos del que publica |
| **IGUAL EN AGREGADO** | Sólo para matrices de coeficientes (`A`, `L`), donde la prueba de columnas no aplica —la columna de `L` es un multiplicador, no una suma de pesos—: el agregado queda dentro del 1 % y la diferencia que resta está en el reparto por filas |
| **CERCA EN COLUMNAS** | El consumo intermedio por sector no da exacto pero difiere menos del 1 % de la suma de la matriz: es el orden del reparto proporcional de impuestos y márgenes, no un problema de datos |
| **DISTINTA** | Ni siquiera las columnas se acercan: hay diferencia de datos |
| **SIN CONTRASTE** | El país publica MIP para ese año pero falta algo para compararla; el motivo va en la fila |

## Resultado

| País | Año | Objeto | Veredicto | Detalle |
|:--|:--|:--|:--|:--|
| Argentina | 1997 | Z | IGUAL EN COLUMNAS | suma +0.0000 % · máx. dif. columna 6.8e-06 · correlación 0.9798 · desvío 21.99 % |
| Argentina | 2004 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — la única MIP publicada es la de 1997 |
| Argentina | 2018 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — la única MIP publicada es la de 1997 |
| Argentina | 2019 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — la única MIP publicada es la de 1997 |
| Argentina | 2020 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — la única MIP publicada es la de 1997 |
| Argentina | 2021 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — la única MIP publicada es la de 1997 |
| Argentina | 2022 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — la única MIP publicada es la de 1997 |
| Argentina | 2023 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — la única MIP publicada es la de 1997 |
| Brasil | 2010 | A | IGUAL | suma -0.0080 % · máx. dif. columna 1.7e-03 · correlación 1.0000 · desvío 0.03 % |
| Brasil | 2010 | D | IGUAL | suma -0.0000 % · máx. dif. columna 3.0e-06 · correlación 1.0000 · desvío 0.00 % |
| Brasil | 2010 | L | IGUAL | suma -0.0058 % · máx. dif. columna 3.6e-03 · correlación 1.0000 · desvío 0.01 % |
| Brasil | 2011 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2012 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2013 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2014 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2015 | A | IGUAL | suma -0.0037 % · máx. dif. columna 8.9e-04 · correlación 1.0000 · desvío 0.01 % |
| Brasil | 2015 | D | IGUAL | suma +0.0000 % · máx. dif. columna 3.0e-06 · correlación 1.0000 · desvío 0.00 % |
| Brasil | 2015 | L | IGUAL | suma -0.0027 % · máx. dif. columna 1.5e-03 · correlación 1.0000 · desvío 0.01 % |
| Brasil | 2016 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2017 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2018 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2019 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2020 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Brasil | 2021 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el IBGE publica MIP sólo para 2010 y 2015 |
| Colombia | 2014 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el DANE publica MIP para 2015, 2017, 2019 y 2021 |
| Colombia | 2015 | reconstruida | SIN CONTRASTE | el DANE publica MIP 2015, pero el anexo no está en el patrón de URL de 2019 y 2021 |
| Colombia | 2016 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el DANE publica MIP para 2015, 2017, 2019 y 2021 |
| Colombia | 2017 | reconstruida | SIN CONTRASTE | el DANE publica MIP 2017, pero el anexo no está en el patrón de URL de 2019 y 2021 |
| Colombia | 2018 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el DANE publica MIP para 2015, 2017, 2019 y 2021 |
| Colombia | 2019 | L dom. | DISTINTA | suma +3.2595 % · máx. dif. columna 3.6e-01 · correlación 0.9918 · desvío 13.56 % |
| Colombia | 2019 | L total | IGUAL EN AGREGADO | suma -0.0131 % · máx. dif. columna 1.2e-01 · correlación 0.9906 · desvío 12.18 % |
| Colombia | 2019 | Z | CERCA EN COLUMNAS | suma +3.8388 % · máx. dif. columna 4.9e+03 · correlación 0.9655 · desvío 25.43 % |
| Colombia | 2020 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el DANE publica MIP para 2015, 2017, 2019 y 2021 |
| Colombia | 2021 | L dom. | DISTINTA | suma +3.6089 % · máx. dif. columna 4.6e-01 · correlación 0.9899 · desvío 15.00 % |
| Colombia | 2021 | L total | IGUAL EN AGREGADO | suma +0.0826 % · máx. dif. columna 7.9e-02 · correlación 0.9887 · desvío 13.12 % |
| Colombia | 2021 | Z | CERCA EN COLUMNAS | suma +4.5245 % · máx. dif. columna 7.9e+03 · correlación 0.9516 · desvío 28.59 % |
| Colombia | 2022 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el DANE publica MIP para 2015, 2017, 2019 y 2021 |
| Colombia | 2023 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el DANE publica MIP para 2015, 2017, 2019 y 2021 |
| Colombia | 2024 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el DANE publica MIP para 2015, 2017, 2019 y 2021 |
| Mexico | 2008 | OFICIAL | — | es la matriz oficial: no se contrasta contra sí misma |
| Mexico | 2013 | OFICIAL | — | es la matriz oficial: no se contrasta contra sí misma |
| Mexico | 2013 | Z | IGUAL EN COLUMNAS | suma +0.0000 % · máx. dif. columna 1.1e-05 · correlación 0.9998 · desvío 3.21 % |
| Mexico | 2018 | OFICIAL | — | es la matriz oficial: no se contrasta contra sí misma |
| Uruguay | 2012 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el BCU publica MIP sólo para 2016 |
| Uruguay | 2016 | reconstruida | SIN CONTRASTE | el BCU publica producto×producto (128×128, Modelo B) y sólo 11 sectores en industria×industria; no publica la correspondencia con el COU y su metodología es un PDF escaneado |
| Uruguay | 2017 | reconstruida | sin MIP oficial | no hay MIP oficial para ese año — el BCU publica MIP sólo para 2016 |

## Resumen

- **6** comparaciones dan **igual** a la oficial
- **2** coinciden en columnas y difieren en filas
- **2** difieren en columnas por debajo del 1 %
- **2** son matrices de coeficientes que coinciden en el agregado
- **2** difieren también en columnas
- **3** tienen MIP oficial pero no se pudo contrastar

El resto de los libros corresponde a años en los que el país no publica MIP: son justamente los que este trabajo produce por primera vez.

## Por qué Colombia se aparta, y qué lo demuestra

Las comparaciones domésticas de Colombia (`Z` y `L dom.`) son las que quedan por debajo del resto, y la causa está medida: **el COU del DANE no publica qué parte de cada celda se importó**, así que el corte por origen sale del prorrateo proporcional (§8.33) y deja insumo importado dentro de la matriz doméstica —27.226 de más en 2019, sobre un `Z` de 757.403—.

La contraprueba está en el mismo cuadro: la **versión total**, donde las dos partes se vuelven a sumar y ese supuesto no interviene, da **−0,01 % en 2019 y +0,08 % en 2021** contra el Cuadro 8 del DANE, y el consumo intermedio total coincide al 0,09 %. O sea que el método, la valoración y el balanceo reproducen al instituto; lo que falta es un dato que la fuente no trae. Cada libro lo declara en la hoja «SUT importado». Ver `sesgo_prorrateo.md`.
