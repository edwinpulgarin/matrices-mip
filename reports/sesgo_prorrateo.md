# Cuánto sesga el prorrateo proporcional

> **Nota de estado (2026-08-12).** Las matrices que se publican son la **versión
> doméstica**: `Z` lleva sólo insumo de origen nacional y el importado va en fila
> primaria. En esa definición **los dos supuestos intervienen**: el §7.76
> (impuestos y márgenes dentro de la fila) y el §8.33 (corte por origen), que es
> el caro y el que mide este documento.
>
> Está medido en Argentina 1997, Brasil 2010 y 2015, y los cuatro libros de
> México; prorrateado en los demás. Cada libro lo declara en la hoja «SUT
> importado», en rojo cuando sale del prorrateo.
>
> La **versión total** (nacional + importada), donde el §8.33 no interviene
> porque las dos partes se vuelven a sumar, **ya no se publica**: desde el
> 2026-08-18 el libro entrega sólo la doméstica y lo que se deriva de ella.
> `reports/comparacion_dom_total.md` mide la diferencia entre las dos por país y
> por año. Entre el 2026-08-07 y el 2026-08-12 fue al revés: la total era la
> matriz publicada.

Para convertir un COU en MIP hay que llevar la utilización a precios básicos y
—si se quiere la versión doméstica— separar el insumo importado, **celda a
celda**. Casi ninguna oficina publica ese detalle: dan impuestos, márgenes e
importaciones **por producto**, un número por fila. La salida es repartirlos
proporcionalmente: aplicar la misma tasa de la fila a todas sus celdas.

Para el **origen** eso es el *import proportionality assumption* del Handbook
**§8.33**; para **impuestos y márgenes**, el ajuste proporcional que admite el
**§7.76**. Conviene citar el §8.33 entero, porque no es un aval entusiasta:

> *"this procedure works much better with large numbers of products (for example,
> 10,000) as opposed to, say, fewer than 100 products."* (§8.33)

> *"It is important that the import proportionality assumption or related ratio
> procedures be used only after direct information about import use has been
> compiled."* (§8.38)

Nuestras aperturas van de **66 a 262 productos** —Colombia 66, Uruguay 110,
Brasil 128, Argentina 222, México 262— contra los ~10.000 que el manual pone como
referencia de «funciona bien». Estamos dos órdenes de magnitud por debajo, en el
rango donde el propio Handbook dice que el método rinde mal, y su indicación es
usarlo **sólo después** de agotar el dato directo. De ahí el criterio del
repositorio.

(Ojo con la cifra: son **productos**, no industrias. Colombia tiene 66 productos
—divisiones CPC— y 61 industrias —CIIU—; el COU es rectangular 66 × 61 y la MIP,
cuadrada 61 × 61. Lo que gobierna la calidad del prorrateo es el detalle de
**productos**, porque el supuesto se aplica sobre la fila del producto.)

El supuesto es que todos los usuarios de un producto lo importan —y pagan
impuestos y márgenes— en la misma proporción. Es falso, y falso siempre en la
misma dirección: quien compra al por mayor importa directo, quien compra al
detalle no.

Este repositorio usa el dato medido donde existe (`valoracion.ensamblar_directo`,
y el corte por celda de `valorar_argentina` cuando la fuente lo publica) y el
prorrateo donde no. Los casos con dato permiten medir el error del segundo camino.

## Las mediciones

| País / año | Qué se compara | Prorrateo | Dato medido | Sesgo |
|:---|:---|---:|---:|---:|
| **México 2013** | multiplicador de producción medio | 1,6032 | 1,5174 | **+5,65 %** |
| **Uruguay 2017** | multiplicador de producción medio | 1,6689 | 1,6023 | **+4,16 %** |
| **Colombia 2020** | multiplicador de producción medio | 1,7728 | 1,7046 | **+4,00 %** |
| **Colombia 2019** | multiplicador de producción medio | 1,7553 | 1,7073 | **+2,81 %** |
| **Brasil 2015** | multiplicador de producción medio | 1,8411 | 1,8118 | **+1,61 %** |
| **Brasil 2010** | multiplicador de producción medio | 1,8372 | 1,8132 | **+1,32 %** |
| **Colombia 2020** | insumos intermedios importados | 89.990 | 114.978 | **−21,7 %** |
| **Colombia 2019** | insumos intermedios importados | 98.304 | 125.530 | **−21,7 %** |
| **Uruguay 2017** | insumos intermedios importados | 161.676 | 195.209 | **−17,2 %** |
| **Uruguay 2016** | insumos intermedios importados | 169.112 | 200.908 | **−15,8 %** |

Fuentes del dato medido: INEGI (tabulados PBASICOS × DOMESTICO/IMPORTADO),
IBGE (Matriz de Insumo-Produto, Tabelas 03-10), BCU (utilización intermedia
nacional e importada publicada por separado para 2017; matriz `M 128 x 128` de la
MIP producto×producto para 2016), DANE (MUPNI, matriz de utilización de productos
nacionales e importados, 2014-2020).

La medición de **Uruguay 2017 es la más limpia después de la de México**: misma
fuente, mismo año, misma apertura 110×95, y lo único que cambia entre las dos
columnas es si el origen del insumo se lee del dato o se supone. Las matrices
`nacional` e `importada` del BCU reproducen la utilización total del COU celda a
celda (diferencia máxima 0,0000), así que no hay ningún empalme de por medio.

## Lectura

**El sesgo es sistemático y siempre en la misma dirección**: el prorrateo asigna
de más al origen doméstico, infla los coeficientes técnicos, y por lo tanto los
multiplicadores. En Uruguay se ve por el otro lado del mismo fenómeno: subestima
los insumos importados un 15,8 %.

**Su magnitud depende de cuán abierta sea la economía.** México, con manufactura
de exportación que importa casi todos sus insumos, tiene el sesgo más grande de
los tres (+5,65 %). Brasil, mucho más cerrado, apenas +1,3 a +1,6 %. Ese rango es
la mejor referencia disponible para acotar lo que cargan Argentina y los diez años
de Brasil que sólo tienen COU.

**Por eso «mismo método» no equivale a «mismo sesgo».** Comparar países
reconstruidos todos por prorrateo no cancela el error: cada uno lo carga en la
medida de su apertura comercial.

### El caso extremo, para ver el mecanismo

México 2013, componentes electrónicos (rama 3344). De la oferta total del
producto, sólo el **19,7 %** es de origen doméstico, y eso es lo único que ve el
prorrateo:

| Industria que los usa como insumo | Usa | Doméstico real | % real | % que asume |
|:---|---:|---:|---:|---:|
| Fabricación de computadoras | 126.467 | 0 | **0,0 %** | 19,7 % |
| Fabricación de componentes electrónicos | 65.376 | 34 | 0,1 % | 19,7 % |
| Fabricación de equipo de audio y video | 37.784 | 82 | 0,2 % | 19,7 % |
| Fabricación de partes para vehículos | 36.283 | 0 | **0,0 %** | 19,7 % |
| Operadores de telecomunicaciones | 27.622 | 2.016 | 7,3 % | 19,7 % |

A la fábrica de computadoras el prorrateo le acredita unas 24.900 unidades de
compras a proveedores mexicanos que en la realidad son cero.

## Señal secundaria: el dato limpio cierra mejor

El residuo que el balanceo RAS (Cap. 11) tiene que absorber cae un orden de
magnitud largo cuando se usa el dato medido:

| Caso | Residuo de márgenes (relativo) | Σ\|desbalance de producto\| |
|:---|---:|---:|
| México 2013 · prorrateo | −1,7 · 10⁻⁴ | |
| México 2013 · **dato medido** | **1,7 · 10⁻⁶** | |
| Uruguay 2017 · prorrateo | −4,5 · 10⁻³ | 12.814 |
| Uruguay 2017 · **origen medido** | **2,1 · 10⁻³** | **7.857** |

La matriz medida cuadra casi sola; la prorrateada necesita que el balanceo la
empuje. Es evidencia independiente de que el supuesto está introduciendo error,
no sólo de que cambia el resultado.

En Uruguay 2017 esto **sólo se cumple si la demanda final acompaña al cambio**.
Al medir que menos del consumo intermedio es doméstico, esa oferta doméstica
tiene que reaparecer en la demanda final: si se la sigue repartiendo con la
proporción de la fila, el desbalance de producto se dispara a 71.420 y el residuo
sube a 7,0 · 10⁻³, peor que con prorrateo. Por eso, cuando el origen del uso
intermedio es medido, la demanda final doméstica se deriva por residuo de la fila
(`valoracion.valorar_argentina`, paso 3).

## Estado por país

La matriz que se publica es la **doméstica**, así que las dos columnas cuentan.
(La versión total, que ya no se publica, no lleva la segunda: ahí las dos partes
se vuelven a sumar.)

| País | Impuestos y márgenes (§7.76) | Origen (§8.33) |
|:---|:---|:---|
| **Colombia 2014–2024** | prorrateo · error medido **+0,09 %** en `Z` | prorrateo · error medido **+3,84 %** en `Z` doméstica (2019) |
| México 2013 | medido (tabulados PBASICOS) | medido (tabulados DOMESTICO) |
| México 2008/2013/2018 oficiales | medido (los publica INEGI) | medido |
| Argentina 1997 | medido (cuadros 5-11, celda a celda) | medido (cuadro 4) |
| Brasil 2010, 2015 | medido (Tabelas 05-10) | medido (Tabelas 03/04) |
| Brasil otros 10 años | prorrateo | prorrateo |
| Uruguay 2017 | prorrateo | medido (utilización nacional/importada) |
| Uruguay 2012, 2016 | prorrateo | prorrateo |
| Argentina 2004, 2018–2023 | prorrateo | prorrateo |

Cada libro lleva la nota de método en su portada, así que quien lo abra sabe
sobre qué supuesto está parado sin leer este repositorio.

## Advertencias sobre las mediciones

- **Brasil**: la MIP del IBGE es **nivel 67** y el COU **nivel 68**, así que parte
  de la diferencia entre ambas columnas es de agregación y no sólo de método. El
  sesgo real es probablemente algo menor que el reportado.
- **Uruguay 2016**: la matriz `M` del BCU es **producto×producto** (de la MIP
  simétrica), mientras que nuestro dato sale del COU. Son objetos distintos, así
  que la comparación es indicativa a nivel agregado, no exacta celda a celda. Esa
  matriz se usó sólo para medir, no para reconstruir.
- **Uruguay 2017**: acá no hay esa objeción —el desglose es del propio COU y
  reconcilia exacto— pero quedan dos supuestos vivos. Primero, el corte medido
  está a **precios de comprador** y se aplica a celdas ya llevadas a básicos, lo
  que supone que la cuña de impuestos y márgenes es igual para el insumo nacional
  y el importado. Segundo, el BCU **no** abre el origen de la demanda final:
  ninguna fuente lo hace. El supuesto se retira del consumo intermedio, que es de
  donde salen los coeficientes técnicos, no de todo el cuadro.
- **México** es la medición más limpia: misma fuente, mismo nivel, misma
  clasificación; lo único que cambia entre las dos versiones es el origen del
  insumo.
- **Brasil**: no hay margen para mejorar con lo publicado. Las `Tabela 3` y
  `Tabela 4` del COU nível 68 no son precios básicos sino **preços do ano
  anterior** (medidas de volumen), y el IBGE sólo publica la Matriz de
  Insumo-Produto completa cada cinco años: 2010 y 2015. Los otros diez años
  dependen del supuesto hasta que salga la MIP siguiente.

## Colombia: los dos supuestos, separados

Colombia permite separarlos, porque el DANE publica las dos cosas: el COU con su
puente de valoración, y la MUPNI con la utilización ya a precios básicos **y con
el origen medido** celda a celda. Construyendo el mismo año por los dos caminos
se aísla cada supuesto según en qué versión se mire.

### En la matriz doméstica, que es la que se publica: los dos juntos

| | Sólo COU | Con la MUPNI (origen medido) | Diferencia |
|:---|---:|---:|---:|
| Suma de `Z` doméstica, 2019 | 757.403 | 729.403 | **+3,84 %** |
| Suma de `Z` doméstica, 2020 | 715.583 | 680.554 | **+5,15 %** |
| Consumo intermedio importado, 2019 | 98.304 | 125.530 | **−21,69 %** |
| Consumo intermedio importado, 2020 | 89.990 | 114.978 | **−21,73 %** |
| Multiplicador medio, 2019 | 1,7553 | 1,7073 | **+2,81 %** |
| Multiplicador medio, 2020 | 1,7728 | 1,7046 | **+4,00 %** |
| Correlación celda a celda | — | — | 0,993 / 0,991 |

**El dato que cierra el diagnóstico**: la versión con MUPNI da 729.403 en 2019,
que es **exactamente** la suma del Cuadro 5 (Nacional) del DANE. O sea que la
distancia contra el instituto **es** el prorrateo del origen, y no la
clasificación, ni el Modelo D, ni el balanceo.

### En la matriz total: sólo el §7.76

Ahí el corte por origen se cancela —las dos partes se vuelven a sumar—, así que
lo que queda medido es sólo el reparto de impuestos y márgenes dentro de la fila
(2019, 61 × 61):

| | Sólo COU (§7.76) | Con la MUPNI (medido) | Diferencia |
|:---|---:|---:|---:|
| Suma de `Z` | 855.707 | 854.933 | **+0,09 %** |
| Multiplicador de producción medio | 2,0121 | 2,0174 | **−0,26 %** |
| Correlación celda a celda | — | — | **0,9975** |
| Desvío absoluto celda a celda | — | — | 5,56 % |

Y contra el puente que el propio COU publica, los totales de cada componente de
demanda final quedan a **−0,30 %**. El peor caso son las **exportaciones,
−3,4 %**: el reparto proporcional les asigna una parte de los impuestos del
producto cuando en realidad no los pagan.

La medición vieja contra INEGI 2013 apunta en el mismo sentido: correlación
celda a celda **0,990**, error mediano por industria **1,64 %**, desvío agregado
**−0,89 %**.

**Lectura.** Dos órdenes de magnitud menos que el supuesto de origen (+5,65 % en
México, +2,81 % en Colombia). El §7.76 es barato; el §8.33 es el que hay que
declarar. Los dos están medidos, y cada libro dice sobre cuál está parado.

## Por qué se publica igual desde el COU

Porque la MUPNI llega sólo hasta 2020 y a 66 divisiones CPC, mientras que el COU
llega a 2024 y sale de un solo archivo. La decisión («TODO TIENE QUE SALIR DEL
COU») privilegia que cada número sea rastreable a una sola fuente publicada, con
el supuesto declarado y medido, antes que mezclar dos archivos para ganar cuatro
puntos en una comparación. Quien necesite el corte por origen exacto para
2014-2020 tiene la medición de arriba para corregir, y puede rearmar la versión
total —donde el supuesto no interviene— desde el propio libro, con
`Z^total = Z + D · U^imp`.
