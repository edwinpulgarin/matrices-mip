# Cuánto sesga el prorrateo proporcional — tres mediciones independientes

Para convertir un COU en MIP hay que llevar la utilización a precios básicos y
separar el insumo doméstico del importado, **celda a celda**. Casi ninguna oficina
publica ese detalle: dan impuestos, márgenes e importaciones **por producto**, un
número por fila. El Handbook (§7.77 y Tabla 7.1) prescribe entonces repartirlos
proporcionalmente: aplicar la misma tasa de la fila a todas sus celdas.

El supuesto es que todos los usuarios de un producto lo importan —y pagan
impuestos y márgenes— en la misma proporción. Es falso, y falso siempre en la
misma dirección: quien compra al por mayor importa directo, quien compra al
detalle no.

Este repositorio usa el dato medido donde existe (`valoracion.ensamblar_directo`)
y el prorrateo donde no (`valoracion.valorar_argentina`). Los tres países donde
existe el dato permiten medir el error del segundo camino.

## Las tres mediciones

| País / año | Qué se compara | Prorrateo | Dato medido | Sesgo |
|:---|:---|---:|---:|---:|
| **México 2013** | multiplicador de producción medio | 1,6032 | 1,5174 | **+5,65 %** |
| **Brasil 2010** | multiplicador de producción medio | 1,8374 | 1,8132 | **+1,34 %** |
| **Brasil 2015** | multiplicador de producción medio | 1,8403 | 1,8118 | **+1,57 %** |
| **Uruguay 2016** | insumos intermedios importados | 169.112 | 200.908 | **−15,8 %** |

Fuentes del dato medido: INEGI (tabulados PBASICOS × DOMESTICO/IMPORTADO),
IBGE (Matriz de Insumo-Produto, Tabelas 03-10), BCU (matriz `M 128 x 128` de la
MIP producto×producto).

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

| México 2013 | Residuo de márgenes (relativo) |
|:---|---:|
| Prorrateo | −1,7 · 10⁻⁴ |
| Dato medido | **1,7 · 10⁻⁶** |

La matriz medida cuadra casi sola; la prorrateada necesita que el balanceo la
empuje. Es evidencia independiente de que el supuesto está introduciendo error,
no sólo de que cambia el resultado.

## Estado por país

| País | Impuestos y márgenes | Origen doméstico/importado |
|:---|:---|:---|
| Colombia 2014–2020 | medido (COU a precios básicos por columna) | **medido** (MUPNI) |
| México 2013 | medido (tabulados PBASICOS) | **medido** (tabulados DOMESTICO) |
| Brasil 2010, 2015 | medido (Tabelas 05-10) | **medido** (Tabelas 03/04) |
| Brasil otros 10 años | prorrateo | prorrateo |
| Uruguay 2012, 2016, 2017 | prorrateo | prorrateo |
| Argentina 2004, 2018–2023 | prorrateo | prorrateo |

Cada libro lleva la nota de método en su portada, así que quien lo abra sabe
sobre qué supuesto está parado sin leer este repositorio.

## Advertencias sobre las mediciones

- **Brasil**: la MIP del IBGE es **nivel 67** y el COU **nivel 68**, así que parte
  de la diferencia entre ambas columnas es de agregación y no sólo de método. El
  sesgo real es probablemente algo menor que el reportado.
- **Uruguay**: la matriz `M` del BCU es **producto×producto** (de la MIP
  simétrica), mientras que nuestro dato sale del COU. Son objetos distintos, así
  que la comparación es indicativa a nivel agregado, no exacta celda a celda. Por
  eso Uruguay no se reconstruyó con ella, sólo se usó para medir.
- **México** es la medición más limpia: misma fuente, mismo nivel, misma
  clasificación; lo único que cambia entre las dos versiones es el origen del
  insumo.
