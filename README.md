# MIP Refactor — Reconstrucción de Matrices Insumo-Producto desde COU

Pipeline que reconstruye **Matrices Insumo-Producto (MIP) simétricas** a partir de los
**Cuadros de Oferta y Utilización (COU)** oficiales, siguiendo *exactamente* el
**UN Handbook on Supply, Use and Input-Output Tables** (Series F No.74 Rev.1, 2018).

Reemplaza al repositorio anterior, cuyas matrices no cuadraban (fórmulas Excel sin
calcular, valoración omitida, balanceo desactivado). Aquí cada identidad contable se
verifica **por construcción**, a ~1e-12:

```
por fila     x = Σⱼ zᵢⱼ + f              por columna   x = Σᵢ zᵢⱼ + zm + impuestos + VAB
Leontief     L · f = x                   y  Z sin negativos
```

## Qué matriz es

**La versión doméstica: `Z` lleva sólo el insumo de origen nacional y el
importado es exógeno, en la fila primaria «consumo intermedio importado».** Es
la definición del cuadro 12 del INDEC (MIPAr97), de la MIP de INEGI y de la MIP
del BCU, y la que hace que el multiplicador mida **profundidad de cadena
doméstica**: sólo cuenta la producción que ocurre dentro del país.

**La versión total (nacional + importada) no se publica.** Todo lo que trae el
libro —`A`, la inversa de Leontief, los multiplicadores, los encadenamientos— se
deriva de esa única `Z` doméstica, para que nadie termine leyendo indicadores
calculados sobre la definición que no es. Quien necesite la total —la del Cuadro
7 del DANE— la reconstruye desde el mismo libro: `Z^total = Z + D · U^imp`, con
las tres piezas en «MIP completa», «D participaciones» y «SUT importado». Y
`reports/comparacion_dom_total.md` ya mide, por país y por año, cuánto cambiaría
cada indicador: entre **+14,6 % y +35,5 %** en el multiplicador medio, según la
apertura importadora del país.

Consecuencias que conviene tener presentes:

- Separar el origen exige el supuesto de proporcionalidad de las importaciones
  (Handbook §8.33) en las fuentes que no lo miden celda a celda, y ese supuesto
  **infla los multiplicadores** —hasta 5,65 % en promedio en México, 58,6 % en
  una rama—. Cada libro declara en la hoja «SUT importado», en rojo, si su corte
  por origen está medido o prorrateado. Está medido en Argentina 1997, Brasil
  2010 y 2015, y los cuatro libros de México; prorrateado en el resto.
- El multiplicador de la hoja total es entre 15 % y 20 % más alto, porque
  incluye producción que ocurre fuera del país. No es comparable con el de la
  matriz doméstica ni mide lo mismo.

`Z` sin negativos no significa forzar el dato: **los negativos que publica la
fuente se conservan tal cual**. La variación de existencias puede ser negativa
—es una desacumulación de stock, no un error— y todas las fuentes la publican
así. Caen en la demanda final, no en el consumo intermedio, de modo que la MIP
queda no negativa sin tocar una sola celda del cuadro oficial. El balanceo las
aparta del ajuste porque el RAS es multiplicativo (Handbook, Box 11.3) y las
devuelve en su lugar, con su valor exacto.

## Etapas (una por módulo en `src/`)

| Módulo | Handbook | Qué hace |
|---|---|---|
| `parsers/*` | Cap. 5-6 | COU oficial → estructura canónica (V, U, Y, VA, valoración) |
| `valoracion.py` | Cap. 7 | precios de comprador → básicos; separa importaciones e impuestos |
| `cobertura.py` | — | control de lectura: ¿la utilización leída reproduce la oferta que declara la fuente? |
| `balanceo.py` | Cap. 11 | RAS biproporcional |
| `transformacion.py` | Cap. 12 | SUT → MIP simétrica (Modelo D industria×industria; B producto×producto) |
| `analisis.py` | Cap. 20 | A = Z·ĝ⁻¹, L = (I−A)⁻¹, multiplicadores |
| `demanda_final.py` | Cap. 2 | esquema armonizado de demanda final (SCN 2008) |
| `export_libro.py` | — | libro Excel auditable (hasta 20 pestañas numeradas, **en orden de auditoría**) |

### Cómo se lee un libro

Las pestañas siguen el orden del cálculo, no el de la conclusión: se empieza por
el cuadro oficial tal como lo publica el instituto y se termina en la MIP.

**El libro está ordenado como se calcula**, no como se concluye. Cada hoja es un
paso de la cadena, y declara su fórmula, el capítulo del Handbook que la manda y
de qué hojas sale. La primera pestaña, **«Paso a paso»**, trae la receta completa
en una tabla.

```
COU original  →  V  →  q  →  D  →  U  →  Z = D·U  →  A  →  L
```

| Bloque | Color | Qué contiene |
|:---|:---|:---|
| **Guías** | azul | **Paso a paso** (la receta), Cómo auditar (qué comparar y qué no) y Ejemplo resuelto (una celda seguida de punta a punta) |
| **Archivo descargado** | gris | La hoja del instituto **copiada con su formato**, sus logos y las mismas coordenadas de celda |
| COU original | verde | Oferta, puente de valoración, utilización a precios de comprador y demanda final nativa |
| SUT y transformación | ámbar y violeta | V valorado, `q`, la matriz **D**, U doméstica, U importada, demanda final, el balanceo RAS y `Z = D · U` |
| MIP y análisis | rojo | Tabla completa, vectores, balances, `A`, `L`, `B`, auditoría contra el COU y demanda final armonizada |

Los números de pestaña son **correlativos según los pasos que esa fuente
permite**, así que cambian de país a país (Colombia no publica puente de
valoración; los libros oficiales de México no tienen COU). Para localizar una
hoja desde código, buscarla **por su nombre sin el número** — así lo hacen
`validar_consistencia.py` y el arnés en R.

Una pestaña por concepto, no por fórmula: `diag(g)` y su inversa van como dos
columnas de «Vectores y diagonales», los dos balances comparten hoja porque se
leen juntos, y la validación de A encabeza la propia matriz A.

Lo único que **no** se puede rehacer con aritmética directa entre hojas es el
balanceo RAS, porque es iterativo; la hoja muestra el antes, el después y cuánto
movió cada fila y cada columna. Todo lo demás es recalculable a mano.

Cada hoja declara en su **fila 1** qué hay en las filas, qué en las columnas, en
qué valoración y con qué origen. Esa franja resuelve la confusión más común al
auditar: el COU es **rectangular** (productos × industrias) y la MIP es
**cuadrada** (industrias × industrias), así que las celdas de una y otra **no
tienen por qué coincidir** — lo que reconcilia exacto es el total por columna,
en «23. Auditoría COU». La hoja **Cómo auditar** lo explica con la lista de
comparaciones válidas y las tres trampas frecuentes.

Los números son fijos por concepto: si una fuente no publica una pieza, esa hoja
no existe y el número se saltea. Así «16. A coeficientes técnicos» es la misma
pestaña en los 38 libros.
La hoja **8. U importada** avisa en rojo cuando sus celdas salen del prorrateo en
vez de estar medidas.

Las pestañas **0** son la hoja del archivo descargado copiada con su formato
(`src/crudo.py`): tipografías, celdas combinadas, anchos de columna y las
imágenes embebidas —el logo del DANE, el del BCU—. **Las coordenadas se
conservan**, así que la celda `B14` del libro es la `B14` del archivo del
instituto y se puede citar sin traducir nada. El índice dice de qué archivo y
qué hoja salió cada una.

Dos aclaraciones honestas sobre esas pestañas:

- Es una **copia muy fiel, no el archivo original**. Un `.xlsx` no puede contener
  otro Excel byte a byte; para peritaje hay que ir al archivo del instituto.
- Argentina y Brasil publican en `.xls` (Excel 97), que openpyxl no lee. Esos se
  convierten antes con **LibreOffice headless**, que preserva valores, formatos e
  imágenes; la conversión se cachea en `data/_xls_convertidos/` y se rehace sola
  si cambia el original. Sin LibreOffice instalado, el libro cae a un volcado de
  valores en las mismas coordenadas.

Cuando la fuente es un CSV —los libros oficiales de México— no hay formato ni
logos que copiar: va la grilla de valores tal como viene.

## Cobertura

- **Argentina** (INDEC): **1997** desde la MIPAr97 — **sin prorrateo**, 124 ramas ×
  195 productos, y contrastable contra la matriz simétrica oficial
  (`reports/argentina_1997.md`); 2004 y 2018–2023 desde el COU moderno
- **Brasil** (IBGE): 2010–2021
- **Uruguay** (BCU): 2012, 2016, 2017 — validado contra la MIP oficial
- **México** (INEGI): 2013 reconstruida desde el COU, rama SCIAN 262×262 —
  **sin prorrateo** (`reports/mexico_validacion.md`); y 2008, 2013 y 2018 desde la
  **MIP simétrica oficial** (`reports/mexico_mip_oficial.md`)
- **Colombia** (DANE): **2014–2024p** (11 años), 61×61 — **todo desde el COU**, un solo archivo

Los **38 libros publicados** viven en `matrices/<País>/MIP_<País>_<Año>_LIBRO.xlsx`,
con sufijo `_OFICIAL` los tres que salen de la MIP publicada por INEGI en vez de
reconstruirse desde el COU. México 2013 tiene los dos a propósito: comparados
miden cuánto se aparta el Modelo D del método propio del instituto sobre los
mismos datos (multiplicador medio 1,5174 vs. 1,5185; correlación de Z 0,9998).
Ver `reports/RESUMEN_GENERAL.md` para el detalle metodológico,
`manifest_publicables.csv` para el inventario y `reports/validacion_consistencia.md`
para la auditoría final (los 38 pasan las 7 verificaciones de consistencia).

### Origen de los insumos: dato medido vs. prorrateo

Para pasar de precios de comprador a básicos y separar lo doméstico de lo
importado hace falta el dato celda a celda. Donde la fuente lo publica se usa
(`valoracion.ensamblar_directo`); donde no, se reparte proporcionalmente por
producto (`valoracion.valorar_argentina`). Para el origen ese reparto es el
*import proportionality assumption* del Handbook **§8.33**; para impuestos y
márgenes, el ajuste proporcional que admite el **§7.76**.

Conviene citarlo completo, porque el Handbook es más reservado de lo que suele
recordarse: el §8.33 advierte que el método «funciona mucho mejor con grandes
cantidades de productos (por ejemplo, 10.000) que con menos de cien», y el §8.38
que debe usarse **sólo después** de haber agotado la información directa. Todas
nuestras aperturas están entre 61 y 262 productos, o sea en el rango donde el
propio Handbook lo desaconseja. Por eso el criterio del repositorio es buscar el
dato medido antes que aplicar el supuesto.

Con la matriz **total** el supuesto del origen dejó de afectar lo que se publica:
sólo importa para quien recupere la versión doméstica desde el libro. El que sigue
vigente es el del **Cap. 7**, impuestos y márgenes dentro de la fila.

| País | Impuestos y márgenes (§7.76, **vigente**) | Origen (§8.33, sólo versión doméstica) |
|:---|:---|:---|
| **Colombia 2014–2024** | prorrateo | no interviene |
| México 2013 | medido (INEGI PBASICOS) | medido |
| México 2008/2013/2018 oficial | no aplica — la MIP viene ya construida | medido |
| Argentina 1997 | medido (cuadros 5-11, celda a celda) | medido (cuadro 4) |
| Brasil 2010 y 2015 | medido (Tabelas 05-10) | medido (Tabelas 03/04) |
| Uruguay 2017 | prorrateo | medido (BCU, nacional/importada) |
| Argentina moderna, Uruguay 2012 y 2016, Brasil otros 10 años | prorrateo | prorrateo |

Los dos supuestos están **medidos** contra el dato real. El caro es el del
origen: en Colombia, construir el mismo año desde el COU (que obliga a
prorratear el origen) o desde la MUPNI (que lo mide celda a celda) deja la suma
de `Z` doméstica **+3,84 % en 2019 y +5,15 % en 2020**, el insumo importado
**−21,7 %** y el multiplicador medio **+2,81 % / +4,00 %**, con correlación celda
a celda 0,993. La versión con MUPNI da 729.403 en 2019, que es **exactamente** el
Cuadro 5 del DANE ⇒ toda la brecha contra el instituto es ese supuesto, no la
clasificación ni el método. El del Cap. 7 (impuestos y márgenes dentro de la
fila) es dos órdenes de magnitud menor. Detalle en `reports/sesgo_prorrateo.md`.

Se publica igual la versión desde el COU, por decisión explícita («TODO TIENE QUE
SALIR DEL COU»): la MUPNI llega sólo hasta 2020 y a 66 divisiones CPC, y mezclar
dos archivos hace que el número deje de ser rastreable a una sola fuente.

Ojo con las unidades de Argentina: INDEC publica 2004–2022 en **miles** de pesos
y 2023 en **millones**. El parser lee la unidad del encabezado del archivo.

### Demanda final

Cada fuente publica la demanda final con su propia granularidad e idioma. Los
libros la presentan en un **esquema único** (P.3 consumo final · P.5 formación
bruta de capital · P.6 exportaciones · discrepancia estadística), con el mapeo
desde las columnas de origen documentado en la hoja «13. Demanda final».

Dos componentes van colapsados a propósito, porque no son armonizables:
el **consumo** (las ISFLSH caen de lados distintos según el país: Uruguay las
agrupa con gobierno, México con consumo privado) y la **formación de capital**
(la MUPNI de Colombia no separa la fija de la variación de existencias).
El detalle no se pierde: la hoja «16. COU Demanda final» conserva las columnas
nativas de cada fuente. Ver `src/demanda_final.py`.

La armonización se aplica **después** del balanceo: el RAS opera sobre `[U | Y]`,
así que agrupar columnas antes cambiaría el reparto. Agrupadas después, `Z`, `f`,
`A` y `L` quedan idénticas.

## Reproducir

```
py -3 scripts/argentina_libros.py      # → matrices/Argentina/  (COU moderno)
py -3 scripts/argentina97_libros.py    # → matrices/Argentina/  (MIPAr97, sin prorrateo)
py -3 scripts/brasil_libros.py         # → matrices/Brasil/
py -3 scripts/uruguay_libros.py        # → matrices/Uruguay/
py -3 scripts/mexico_libros.py         # → matrices/Mexico/  (reconstruida desde el COU)
py -3 scripts/mexico_mip_libros.py     # → matrices/Mexico/  (MIP oficial de INEGI)
py -3 scripts/colombia_libros.py       # → matrices/Colombia/
py -3 scripts/validar_consistencia.py  # auditoría de los libros (identidades + auditabilidad)
py -3 scripts/auditar_cobertura.py     # ¿leemos toda la utilización que publica cada fuente?

# validación contra las MIP que publica cada instituto (necesita R)
"C:/Program Files/R/R-4.5.1/bin/Rscript.exe" scripts/validacion_R/validar_todo.R
py -3 tests/test_sintetico.py
py -3 tests/test_demanda_final.py
```
