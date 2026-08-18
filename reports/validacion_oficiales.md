# Validación contra las MIP oficiales

Cada país donde el instituto publica su propia matriz simétrica se usa como
**prueba de cierre**: partimos del COU, reconstruimos la MIP y comparamos.
Todo corre en **R**, leyendo los libros ya publicados y los archivos oficiales,
sin compartir una línea con el motor en Python.

## Cómo leer las columnas

En el Modelo D las columnas de `Z` son **invariantes al modelo**: como las
columnas de `D` suman 1, se cumple `Σᵢ Z[i,j] = Σₚ U[p,j]`. Por eso:

- una diferencia en **columnas** señala un problema de **datos** — valoración,
  corte doméstico/importado o balanceo;
- una diferencia sólo en **filas** señala el reparto producto→industria, es
  decir la matriz **D**, que depende del nivel de detalle de productos.

## Resultados

| Caso | Objeto | n | Dif. suma | Máx. dif. columna | Máx. dif. fila | Correlación | Desvío abs. |
|:--|:--|--:|--:|--:|--:|--:|--:|
| Argentina 1997 | Z | 124 | +0.0000 % | 6.82e-06 | 5.83e+02 | 0.9798 | 21.99 % |
| Brasil 2010 | D | 67 | -0.0000 % | 3.00e-06 | 9.29e-04 | 1.0000 | 0.00 % |
| Brasil 2010 | A | 67 | -0.0080 % | 1.75e-03 | 2.91e-03 | 1.0000 | 0.03 % |
| Brasil 2010 | L | 67 | -0.0058 % | 3.61e-03 | 5.16e-03 | 1.0000 | 0.01 % |
| Brasil 2015 | D | 67 | +0.0000 % | 3.00e-06 | 2.83e-04 | 1.0000 | 0.00 % |
| Brasil 2015 | A | 67 | -0.0037 % | 8.91e-04 | 1.04e-03 | 1.0000 | 0.01 % |
| Brasil 2015 | L | 67 | -0.0027 % | 1.49e-03 | 1.85e-03 | 1.0000 | 0.01 % |
| Colombia 2019 | Z | 58 | +3.8388 % | 4.89e+03 | 8.49e+03 | 0.9655 | 25.43 % |
| Colombia 2021 | Z | 58 | +4.5245 % | 7.87e+03 | 1.03e+04 | 0.9516 | 28.59 % |
| México 2013 | Z | 262 | +0.0000 % | 1.10e-05 | 4.22e+04 | 0.9998 | 3.21 % |
| Colombia 2019 | L dom. | 58 | +3.2595 % | 3.61e-01 | 6.80e-01 | 0.9918 | 13.56 % |
| Colombia 2019 | L total | 58 | -0.0131 % | 1.18e-01 | 9.39e-01 | 0.9906 | 12.18 % |
| Colombia 2021 | L dom. | 58 | +3.6089 % | 4.56e-01 | 8.54e-01 | 0.9899 | 15.00 % |
| Colombia 2021 | L total | 58 | +0.0826 % | 7.90e-02 | 1.25e+00 | 0.9887 | 13.12 % |

## Qué dice cada bloque

**Brasil es la prueba del motor.** El IBGE publica la matriz `D`, la `A` y la
Leontief, no sólo el resultado. Las tres reproducen las oficiales con
correlación 1,0000 y desvío por debajo del 0,03 %, que es el redondeo de la
propia publicación. Queda probado que `D = V·diag(q)⁻¹`, `A = Z·diag(g)⁻¹` y
`L = (I−A)⁻¹` están bien calculadas: si hubiera un error de método, aparecería
acá y no aparece.

**México mide el nivel de detalle, no el método.** Las columnas cierran exacto
—o sea que el dato, la valoración y el balanceo coinciden con el instituto— y
la diferencia queda toda en las filas, que es donde actúa `D`.

**Colombia mide el precio del §8.33, y es el hallazgo de este contraste.** La
matriz que se publica es la doméstica, así que el homólogo es el **Cuadro 5
(Nacional)** del DANE. Contra él, nuestra `Z` sale **+3,8 % en 2019 y +4,5 % en
2021**, y el espejo lo dice todo: el insumo importado nos da **98.304 donde el
DANE mide 125.530** (−21,7 %). El COU no publica el corte por celda y el
prorrateo proporcional se lo reparte a todas las industrias por igual, así que
deja en la matriz doméstica insumo que en realidad se importó. El
multiplicador medio queda **+3,26 % (2019)** y **+3,61 % (2021)** por encima
del DANE.

**Y la contraprueba, en el mismo cuadro:** la versión total —donde las dos
partes se vuelven a sumar y el §8.33 no interviene; el libro ya no la entrega,
se rearma con `Z + D·U^imp`— da **−0,01 % en 2019 y +0,08 % en 2021** contra
el Cuadro 8. O sea
que el método y el dato están bien y toda la brecha de la doméstica es el
supuesto de origen. Es la cuarta medición del §8.33 del proyecto, después de
México (+5,65 %), Brasil (+1,3/+1,6 %) y Uruguay (−15,8 % de insumo importado).
Ver `sesgo_prorrateo.md`.

**Lo que queda no se puede cerrar, y conviene decirlo.** El DANE publica su MIP
a 68 actividades y el COU trae 61. Del Anexo 2 salen 53 actividades 1:1, tres
casos donde la MIP agrupa varias del COU —agregar es trivial— y **ocho donde una
actividad del COU se PARTE en varias de la MIP** (`018 + 021` → `018` y
`021-022`; `K` → `085-086`, `087`, `088`; y seis más). Desagregar exige los
microdatos de establecimiento, que no se publican. Mientras el COU salga a 61
actividades, reproducir la matriz de 68 al último dígito es imposible por
construcción, no por método.

## Contraste contra el trabajo previo hecho en el DANE

La carpeta `Validación_Colombia` guarda las matrices de Leontief, Ghosh y los
encadenamientos calculados en R años atrás, para 2017, 2019 y 2021. **No es una
reconstrucción alternativa**: ese script lee la MIP que el DANE ya publica y
corre el análisis sobre ella. Sirve igual como prueba de cierre, pero hay que
resolver una diferencia de definición antes de comparar cualquier número.

Esa `L` es además **idéntica al Cuadro 8** que el DANE publica —el propio
instituto ya trae la inversa de Leontief calculada—, cosa que se verificó:
`Cuadro 8` vs `L(Cuadro 7)` da máx dif **5,0e-08**, que es el redondeo de la
publicación. O sea que su `L`, el Cuadro 8 y la Leontief del Cuadro 7 son el
mismo objeto.

Y ese objeto es el **total**: el Cuadro 7 es «Nacional e Importado» y trata los
insumos importados como **endógenos**. Nuestras matrices son domésticas y dejan
la importación como fila primaria exógena, que es el **Cuadro 5**. La `L` del
Cuadro 7 es por construcción mayor, y esa brecha no es error de nadie.

El origen no se dio por supuesto: invirtiendo su `L` se recupera `A = I − L⁻¹`,
y como `A = Z·diag(x)⁻¹`, los cocientes `Z[i,j]/A[i,j]` tienen que ser
constantes por columna para el `Z` correcto. Sólo el Cuadro 7 lo cumple
(dispersión 7e-14 en 2019, 9e-14 en 2021); los otros siete quedan en 1e-1 o peor.

### El total coincide; el corte por origen, no

| | Nuestro 2019 | DANE 2019 | Nuestro 2021 | DANE 2021 | |
|:--|--:|--:|--:|--:|:--|
| `Z` doméstico | 757.403 | 729.403 | 886.543 | 848.168 | Cuadro 5 |
| `Z` importado | 98.304 | 125.530 | 127.128 | 164.204 | Cuadro 7 − Cuadro 5 |
| `Z` total | 855.707 | 854.933 | 1.013.671 | 1.012.372 | Cuadro 7 |
| Producción bruta | 1.857.445 | 1.857.445 | 2.140.060 | 2.140.060 | columna «Total» |

**El consumo intermedio total coincide al 0,09 %, y la producción bruta al peso.**
Lo que se separa es el reparto entre doméstico e importado: el COU no publica ese
corte por celda, así que el prorrateo (§8.33) le aplica a cada industria la
proporción importada del producto, y eso deja **27.226 de más** en la matriz
doméstica de 2019. Es el mismo fenómeno medido en México, Brasil y Uruguay.

### Las dos Leontief, cada una contra su homólogo

| Contraste | 2019 | 2021 |
|:--|--:|--:|
| Su `L` vs `L` recalculada del Cuadro 7 | máx dif **4,4e-16** | máx dif **4,4e-16** |
| Multiplicador medio, Cuadro 7 (total) | 1,9937 | 2,0593 |
| Multiplicador medio, Cuadro 5 (doméstico) | 1,6882 | 1,6983 |
| **La definición sola explica** | **+18,1 %** | **+21,3 %** |
| **Nuestra `L` doméstica (publicada) vs Cuadro 5** | 1,7596 vs 1,7040 (**+3,26 %**) | 1,7771 vs 1,7152 (**+3,61 %**) |
| **Nuestra `L` total (hoja del libro) vs Cuadro 8** | 2,0185 vs 2,0187 (**−0,01 %**) | 2,0790 vs 2,0773 (**+0,08 %**) |

Las dos últimas filas son el mismo motor sobre el mismo COU, leídas con las dos
definiciones. La total, donde el §8.33 no interviene, cae a la milésima; la
doméstica se aparta 3,3-3,6 %, y esa distancia **es** el supuesto de origen.

**Lectura.** Reproducimos su cálculo al último dígito de la doble precisión, así
que su pipeline queda confirmado y también nuestra lectura de sus archivos. El
método y el dato están verificados —el contraste total da −0,01 %—, y lo que
queda por resolver en la matriz doméstica de Colombia no es cálculo sino un dato
que el COU no trae: qué parte de cada celda se importó. Quien necesite la cifra
exacta del corte por origen tiene que ir a la MUPNI, que lo mide pero sólo llega
a 2020 y a 66 divisiones CPC.

El aviso práctico para quien compare: si se toman los multiplicadores de ese
trabajo o del Cuadro 8 (≈2,0) contra los nuestros (≈1,76) se ve una brecha del
15 % que es **casi toda de definición**, no de método — total contra doméstico.
Comparados como el mismo objeto, la diferencia es 0,01 %.

## Pendientes

| Caso | Qué falta |
|:--|:--|
| Colombia 2017 | bajar el anexo del DANE de ese año: tenemos su `L` del trabajo previo y nuestro libro, pero sin el Cuadro 5 no se puede separar doméstico de total |
| Colombia 2015 | bajar el anexo del DANE; no está en el patrón de URL de 2019 y 2021 |
| Colombia 2021 | la MUPNI publicada llega a 2020, así que no hay libro de ese año |
| México 2008 y 2018 | INEGI no publica el COU de utilización de esos años |
| Uruguay 2016 | el BCU publica producto×producto (128×128, Modelo B); industria×industria sólo a 11 sectores |


