# Reconstrucción de MIP desde COU — Resumen general

Pipeline exacto al **UN Handbook on SUT and IOT (Series F No.74 Rev.1, 2018)**:
COU oficial → valoración (Cap. 7) → balanceo RAS (Cap. 11) → transformación
Modelo D industria×industria (Cap. 12) → análisis Leontief (Cap. 20) → libro Excel.

Las matrices que se publican son la **versión DOMÉSTICA**: `Z` lleva sólo el insumo
de origen nacional y el importado va en la fila primaria «consumo intermedio
importado». Es la definición de la MIP de INEGI, del cuadro 12 del INDEC y de la MIP
del BCU, y es la que hace que el multiplicador mida profundidad de cadena doméstica.
La **versión total** (nacional + importada, definición del Cuadro 7 del DANE) **no se
publica**: todo lo que trae el libro se deriva de la Z doméstica. Sigue siendo
reconstruible desde el propio libro —`Z^total = Z + D · U^imp`, con las tres piezas
en las hojas «MIP completa», «D participaciones» y «SUT importado»— y
`reports/comparacion_dom_total.md` mide, indicador por indicador, cuánto cambiaría
cada resultado con esa definición.

Todas cumplen, **por construcción**:
`gᵢ = Σⱼ zᵢⱼ + fᵢ` (fila) y `gⱼ = Σᵢ zᵢⱼ + zmⱼ + impuestosⱼ + VABⱼ` (columna) a **~1e-12**,
`L·f = g`, `aᵢⱼ ≥ 0`, `Σᵢ aᵢⱼ < 1`, y **`Z` sin negativos** — sin forzar el dato:
los negativos que publica la fuente (variación de existencias) se conservan con su
valor exacto y caen en la demanda final, no en el consumo intermedio.

Que las identidades cierren no prueba que el dato de entrada esté completo: el
balanceo cierra igual una fila a la que le falta uso. Ese riesgo lo cubre un
control aparte, `cobertura.py`, que contrasta la utilización leída contra la
oferta que declara cada fuente. Ver `cobertura_fuentes.md`.

## Cobertura (38 libros)

| País | Años | Dim | Origen de los insumos | Estado |
|---|---|---|---|---|
| **Argentina** (INDEC) | **1997** (1) | 124×124 | **medido** | ✅ cuadra · contrastable contra la simétrica oficial |
| **Argentina** (INDEC) | 2004, 2018–2023 (7) | 107–162 | prorrateo | ✅ cuadran |
| **Brasil** (IBGE) | 2010–2021 (12) | 67–68 | **medido en 2010 y 2015**, prorrateo el resto | ✅ cuadran, sin negativos (incl. 2011–2014 que el repo viejo excluía) |
| **Uruguay** (BCU) | 2012, 2016, 2017 (3) | 95–107 | **origen medido en 2017**, prorrateo el resto | ✅ cuadran + **validado contra MIP oficial** |
| **México** (INEGI) | 2013 (1) | 262×262 | **medido** | ✅ cuadran |
| **México** (INEGI) | 2008, 2013, 2018 **oficiales** (3) | 262–263 | **medido** | ✅ es la MIP publicada por el instituto |
| **Colombia** (DANE) | **2014–2024p (11)** | 61×61 | sólo COU, un archivo | ✅ cuadran |

**Como la matriz publicada es doméstica, los dos supuestos intervienen**: el del
Cap. 7 (impuestos y márgenes dentro de la fila) y el del §8.33 (corte por origen),
que es el caro. Está medido en cuatro fuentes: México **+5,65 %** en el
multiplicador medio, Brasil **+1,32 %** (2010) y **+1,61 %** (2015), Colombia
**+2,81 %** (2019, COU contra MUPNI) y Uruguay **−15,8 %** de insumo importado.
El origen está **medido** en Argentina 1997, Brasil 2010 y 2015, Uruguay 2017 y
los cuatro libros de México; prorrateado en los demás, y cada libro lo declara en
la hoja «SUT importado» (`sesgo_prorrateo.md`).

En la **versión total** ese supuesto no interviene, porque las dos partes se vuelven
a sumar: contra el Cuadro 8 del DANE, Colombia da **−0,01 % (2019)** y **+0,08 %
(2021)**. Es la contraprueba de que el método y el dato están bien y de que toda la
brecha de la doméstica contra el Cuadro 5 es el supuesto de origen.

Cada libro lleva la nota de método en su portada, y `manifest_publicables.csv`
(autogenerado por el validador) marca cuál es cuál.

## Validación externa (Uruguay 2016 vs MIP oficial BCU)

- Producción bruta total: **100.0 %** (2,778,445 vs 2,778,447).
- Valor agregado bruto: **99.999 %** (1,544,203 vs 1,544,182).
- Consumo intermedio agregado: 97.8 % (Δ 2.25 %).
- Metodología idéntica: industria×industria, precios básicos, importaciones separadas.

Detalle en `uruguay_validacion.md`.

## Entregables

- `matrices/<País>/MIP_<País>_<Año>_LIBRO.xlsx` — un libro por matriz, ordenado
  como se calcula: la hoja del instituto **copiada con su formato y sus logos** →
  COU original → `V` → `q` → `D` → `U` → `Z = D·U` → MIP → `A` → `L` → `B`, más
  las guías «Paso a paso», «Cómo auditar» y «Ejemplo resuelto». Cada hoja declara
  su fórmula, el capítulo del Handbook que la manda y de qué hojas sale. La
  cantidad de pestañas cambia por país, según los pasos que la fuente permita
  documentar.
- `output/presentacion.html` — presentación de resultados (todas las cifras salen
  de `output/resultados.json`, que genera `scripts/resultados_presentacion.py`).
- `output/presentacion_mip.pdf` — presentación metodológica (Beamer).
- `reports/validacion_consistencia.md` — **auditoría final** de los 38 libros
  entregados: re-abre cada Excel y re-verifica dimensiones, balances de fila y
  columna, `A = Z·diag(g)⁻¹`, Leontief `L·f = g` y presencia de nombres.
  Estado: **38/38 libros consistentes**.
- `reports/comparacion_dom_total.md` — **Z doméstica vs. Z total**: confirma que los
  38 libros publican la matriz doméstica y que de ella salen `A`, `L` y los
  multiplicadores, y mide cuánto cambiaría cada indicador con la versión total,
  por país y por año. Datos en `reports/comparacion_dom_total.csv`.
- `reports/sesgo_prorrateo.md` — las mediciones del sesgo del prorrateo.
- `reports/STATUS_vs_MIP_oficiales.md` — qué matrices reproducen la MIP oficial y cuáles no.
- `reports/validacion_oficiales.md` — el arnés en R contra las MIP publicadas.
- `reports/{argentina,brasil,uruguay,mexico,colombia}_todos.md` — gates por año.
- `manifest_publicables.csv` — inventario, regenerado por el validador.

## Cómo reproducir

```
py -3 scripts/argentina_libros.py      # 107×107 industria×industria
py -3 scripts/brasil_libros.py
py -3 scripts/uruguay_libros.py
py -3 scripts/colombia_libros.py
py -3 scripts/mexico_libros.py
py -3 scripts/mexico_mip_libros.py
py -3 scripts/argentina97_libros.py
py -3 scripts/validar_consistencia.py  # auditoría final de los libros
py -3 scripts/comparar_dom_total.py    # Z doméstica vs. Z total, por país y año
py -3 scripts/auditar_cobertura.py     # ¿leemos toda la utilización publicada?
py -3 tests/test_sintetico.py          # identidades sobre COU sintético
```
