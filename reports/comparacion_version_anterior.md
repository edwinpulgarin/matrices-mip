# Coeficientes de Leontief: versión anterior vs. actual

Comparación por país y año entre los libros `_auditable.xlsx` de `matrices-mip/` (la versión anterior del repositorio) y los `_LIBRO.xlsx` actuales. Generado por `scripts/comparar_versiones.py`.

## Qué se está comparando

Las dos versiones **no publican el mismo objeto**, así que hay dos carriles:

- El **`Cuadro 8` viejo es la Leontief de la matriz TOTAL** (nacional + importada). Verificado: recalcular `(I−A)⁻¹` desde el `Cuadro 7` con `x = Σcolumna + valor agregado` lo reproduce con diferencia máxima **0,00000**; desde el `Cuadro 5` (nacional) no.

- El **libro actual publica SÓLO la DOMÉSTICA** (hoja «Leontief»), con el insumo importado en fila primaria. La total no se entrega: para este carril se reconstruye desde el propio libro con `Z^total = Z + D·U^imp`.

**Carril A** compara total contra total —misma definición, así que la diferencia es método y datos—. **Carril B** compara lo que cada paquete publica en su portada, que es lo que ve quien baje los dos.

## Carril A — misma definición (total vs. total)

| País | Año | n viejo | n nuevo | n común | Mult. medio viejo | Mult. medio nuevo | Dif. | Corr. celda a celda | MAE fuera de diagonal |
|:--|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Argentina | 2004 | 162 | 162 | 162 | 1,9582 | 1,9764 | 0,93 % | 0,9817 | 0,0016 |
| Argentina | 2018 | 107 | 107 | 103 | 1,9233 | 2,0110 | 4,56 % | 0,9942 | 0,0022 |
| Argentina | 2019 | 107 | 107 | 103 | 1,9257 | 1,9882 | 3,25 % | 0,9949 | 0,0021 |
| Argentina | 2020 | 107 | 107 | 103 | 1,9340 | 1,9961 | 3,21 % | 0,9943 | 0,0023 |
| Argentina | 2021 | 107 | 107 | 103 | 1,9616 | 2,0291 | 3,44 % | 0,9930 | 0,0024 |
| Argentina | 2022 | 107 | 107 | 103 | 1,9701 | 2,0398 | 3,54 % | 0,9920 | 0,0025 |
| Brasil | 2010 | 68 | 67 | 66 | 2,1220 | 2,0998 | -1,05 % | 0,9978 | 0,0021 |
| Brasil | 2015 | 68 | 67 | 66 | 2,1694 | 2,1769 | 0,34 % | 0,9966 | 0,0026 |
| Brasil | 2016 | 68 | 68 | 68 | 2,1365 | 2,0995 | -1,73 % | 0,9868 | 0,0040 |
| Brasil | 2017 | 68 | 68 | 68 | 2,1490 | 2,0989 | -2,33 % | 0,9854 | 0,0042 |
| Brasil | 2018 | 68 | 68 | 68 | 2,1839 | 2,1594 | -1,13 % | 0,9850 | 0,0043 |
| Brasil | 2019 | 68 | 68 | 68 | 2,1817 | 2,1730 | -0,40 % | 0,9847 | 0,0044 |
| Brasil | 2020 | 68 | 68 | 68 | 2,1876 | 2,1991 | 0,53 % | 0,9847 | 0,0044 |
| Brasil | 2021 | 68 | 68 | 68 | 2,2773 | 2,2976 | 0,89 % | 0,9838 | 0,0046 |
| Mexico | 2008 | 262 | 262 | 262 | 1,6554 | 1,9783 | 19,50 % | 0,9886 | 0,0013 |
| Mexico | 2013 | 262 | 262 | 262 | 1,6810 | 2,0445 | 21,62 % | 0,9903 | 0,0014 |
| Uruguay | 2012 | 107 | 107 | 107 | 8,5842 | 2,0053 | -76,64 % | 0,7788 | 0,0608 |

## Carril B — lo publicado antes vs. lo publicado ahora

El viejo es total; el nuevo, doméstico. La brecha de esta tabla es **mayoritariamente de definición**, no de error: la matriz total incluye las rondas de producción que ocurren fuera del país.

| País | Año | Mult. medio publicado antes | Mult. medio publicado ahora | Dif. | Corr. celda a celda |
|:--|--:|--:|--:|--:|--:|
| Argentina | 2004 | 1,9582 | 1,7547 | -10,39 % | 0,9822 |
| Argentina | 2018 | 1,9233 | 1,7462 | -9,21 % | 0,9955 |
| Argentina | 2019 | 1,9257 | 1,7450 | -9,38 % | 0,9958 |
| Argentina | 2020 | 1,9340 | 1,7489 | -9,57 % | 0,9952 |
| Argentina | 2021 | 1,9616 | 1,7577 | -10,40 % | 0,9949 |
| Argentina | 2022 | 1,9701 | 1,7626 | -10,53 % | 0,9943 |
| Brasil | 2010 | 2,1220 | 1,8132 | -14,55 % | 0,9974 |
| Brasil | 2015 | 2,1694 | 1,8118 | -16,48 % | 0,9971 |
| Brasil | 2016 | 2,1365 | 1,8370 | -14,02 % | 0,9867 |
| Brasil | 2017 | 2,1490 | 1,8380 | -14,48 % | 0,9852 |
| Brasil | 2018 | 2,1839 | 1,8454 | -15,50 % | 0,9851 |
| Brasil | 2019 | 2,1817 | 1,8472 | -15,33 % | 0,9853 |
| Brasil | 2020 | 2,1876 | 1,8479 | -15,53 % | 0,9865 |
| Brasil | 2021 | 2,2773 | 1,8933 | -16,86 % | 0,9865 |
| Mexico | 2008 | 1,6554 | 1,5110 | -8,72 % | 0,9985 |
| Mexico | 2013 | 1,6810 | 1,5174 | -9,73 % | 0,9984 |
| Uruguay | 2012 | 8,5842 | 1,6508 | -80,77 % | 0,7338 |

## Detalle sectorial (carril A)

Las cinco industrias que más bajan y las cinco que más suben, por multiplicador de producción.


### Argentina 2022

| Código | Industria | Viejo | Nuevo | Dif. |
|:--|:--|--:|--:|--:|
| 011/014 | Cultivos agrícolas. 014 - Servicios agrícolas y pecu | 2,2098 | 1,9541 | -0,2557 |
| 101 | Extracción y aglomeración de carbón de piedra | 2,1971 | 1,9477 | -0,2495 |
| 1531/2 | Elaboración de productos de molinería. 1532 - Elabor | 2,5619 | 2,3646 | -0,1974 |
| 641 | Servicios de correos | 1,9191 | 1,7427 | -0,1764 |
| 020 | Silvicultura, extracción de madera y servicios conex | 1,7544 | 1,5936 | -0,1608 |
| 642 | Servicios de transmisión de radio y televisión | 2,3376 | 2,5789 | 0,2413 |
| 401 | Generación captación y distribución de energía eléct | 2,8311 | 3,0819 | 0,2508 |
| 402 | Fabricación de gas ; distribución de combustibles ga | 2,2828 | 2,6605 | 0,3777 |
| 32300 | Fabricación de receptores de radio y televisión, apa | 2,1142 | 2,7235 | 0,6093 |
| 32100/32200 | Fabricación de tubos, válvulas y otros componentes e | 2,5892 | 3,3774 | 0,7882 |

### Brasil 2015

| Código | Industria | Viejo | Nuevo | Dif. |
|:--|:--|--:|--:|--:|
| 5100 | Transporte aéreo | 2,5765 | 2,4164 | -0,1601 |
| 1991 | Refino de petróleo e coquerias | 3,0904 | 2,9781 | -0,1123 |
| 4900 | Transporte terrestre | 2,2503 | 2,1585 | -0,0918 |
| 2991 | Fabricação de automóveis, caminhões e ônibus, exceto | 2,6973 | 2,6590 | -0,0383 |
| 6980 | Atividades jurídicas, contábeis, consultoria e sedes | 1,4999 | 1,4940 | -0,0060 |
| 2091 | Fabricação de químicos orgânicos e inorgânicos, resi | 2,6203 | 2,9486 | 0,3283 |
| 2200 | Fabricação de produtos de borracha e de material plá | 2,2470 | 2,5959 | 0,3489 |
| 1500 | Fabricação de calçados e de artefatos de couro | 1,9791 | 2,3290 | 0,3499 |
| 2092 | Fabricação de defensivos, desinfestantes, tintas e q | 2,3181 | 2,7603 | 0,4422 |
| 2600 | Fabricação de equipamentos de informática, produtos  | 2,2258 | 2,7873 | 0,5615 |

### Mexico 2013

| Código | Industria | Viejo | Nuevo | Dif. |
|:--|:--|--:|--:|--:|
| 8141 | Hogares con empleados domésticos | 1,0000 | 1,0000 | 0,0000 |
| 5331 | Servicios de alquiler de marcas registradas, patente | 1,0151 | 1,0192 | 0,0042 |
| 7115 | Artistas, escritores y técnicos independientes | 1,0113 | 1,0164 | 0,0051 |
| 8129 | Servicios de revelado e impresión de fotografías y o | 1,0100 | 1,0229 | 0,0129 |
| 5613 | Servicios de empleo | 1,0455 | 1,0621 | 0,0166 |
| 3345 | Fabricación de instrumentos de medición, control, na | 1,5139 | 2,9795 | 1,4656 |
| 3342 | Fabricación de equipo de comunicación | 1,6004 | 3,6274 | 2,0270 |
| 3344 | Fabricación de componentes electrónicos | 1,5560 | 3,5870 | 2,0310 |
| 3341 | Fabricación de computadoras y equipo periférico | 1,5028 | 3,5984 | 2,0956 |
| 3343 | Fabricación de equipo de audio y de video | 1,5925 | 3,8732 | 2,2808 |

### Uruguay 2012

| Código | Industria | Viejo | Nuevo | Dif. |
|:--|:--|--:|--:|--:|
| C.15 | Elaboración de bebidas malteadas y de malta | 10,8056 | 2,0637 | -8,7418 |
| C.13 | Destilación, rectificación y mezcla de bebidas alcoh | 10,7417 | 2,2716 | -8,4701 |
| C.32 | Fabricación de productos de caucho y plástico | 11,3110 | 2,8695 | -8,4415 |
| C.31 | Fabricación de productos farmaceúticos, sustancias q | 10,6973 | 2,2733 | -8,4240 |
| A.3 | Cultivo de soja; servicios agrícolas aplicados al cu | 10,0696 | 1,7530 | -8,3166 |
| A.2 | Cultivo de hortalizas de hojas y/o que dan frutos, r | 4,8736 | 1,5414 | -3,3323 |
| N.5 | Actividades de servicio a edificios y paisajes (jard | 3,9833 | 1,2969 | -2,6864 |
| S.3 | Otras actividades de servicios | 3,6953 | 1,6503 | -2,0450 |
| S.2 | Reparación de computadoras y artículos de uso person | 3,0316 | 1,5746 | -1,4571 |
| T.1 | Actividades de los hogares en calidad de empleadores | 1,0000 | 1,0000 | 0,0000 |

## Advertencias

- Cuando `n común < n`, las clasificaciones no coinciden: en Brasil 2010 y 2015 el libro nuevo es **nível 67** (viene de la MIP del IBGE, que trae el corte importado medido) y el viejo **nível 68**. Parte de la diferencia es de agregación.

- El multiplicador medio de cada versión se calcula sobre su matriz **completa**, que es la cifra que cada paquete publica; la correlación y el MAE, sobre la submatriz de códigos comunes.

- México 2008 no tiene libro reconstruido nuevo: el contraste es contra el **libro oficial de INEGI**, así que ahí la columna «nuevo» es el dato del instituto, no una reconstrucción.

