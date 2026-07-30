# MIP Refactor — Reconstrucción de Matrices Insumo-Producto desde COU

Pipeline que reconstruye **Matrices Insumo-Producto (MIP) simétricas** a partir de los
**Cuadros de Oferta y Utilización (COU)** oficiales, siguiendo *exactamente* el
**UN Handbook on Supply, Use and Input-Output Tables** (Series F No.74 Rev.1, 2018).

Reemplaza al repositorio anterior, cuyas matrices no cuadraban (fórmulas Excel sin
calcular, valoración omitida, balanceo desactivado). Aquí cada identidad contable se
verifica **por construcción** (`fila = columna` a ~1e-15, `L·f = g`, sin negativos).

## Etapas (una por módulo en `src/`)

| Módulo | Handbook | Qué hace |
|---|---|---|
| `parsers/*` | Cap. 5-6 | COU oficial → estructura canónica (V, U, Y, VA, valoración) |
| `valoracion.py` | Cap. 7 | precios de comprador → básicos; separa importaciones e impuestos |
| `balanceo.py` | Cap. 11 | RAS biproporcional |
| `transformacion.py` | Cap. 12 | SUT → MIP simétrica (Modelo D industria×industria; B producto×producto) |
| `analisis.py` | Cap. 20 | A = Z·ĝ⁻¹, L = (I−A)⁻¹, multiplicadores |
| `demanda_final.py` | Cap. 2 | esquema armonizado de demanda final (SCN 2008) |
| `export_libro.py` | — | libro Excel auditable (16 pestañas: MIP, Auditoría COU, demanda final abierta y el COU de origen) |

## Cobertura

- **Argentina** (INDEC): 2004, 2018–2023
- **Brasil** (IBGE): 2010–2021
- **Uruguay** (BCU): 2012, 2016, 2017 — validado contra la MIP oficial
- **México** (INEGI): 2013, rama SCIAN 262×262 — **sin prorrateo** (`reports/mexico_validacion.md`)
- **Colombia** (DANE): 2014–2020, 61×61 — **sin prorrateo** (`reports/colombia_fuente.md`)

Los **30 libros publicados** viven en `matrices/<País>/MIP_<País>_<Año>_LIBRO.xlsx`.
Ver `reports/RESUMEN_GENERAL.md` para el detalle metodológico,
`manifest_publicables.csv` para el inventario y `reports/validacion_consistencia.md`
para la auditoría final (los 30 pasan las 6 verificaciones de consistencia).

### Origen de los insumos: dato medido vs. prorrateo

Para pasar de precios de comprador a básicos y separar lo doméstico de lo
importado hace falta el dato celda a celda. Donde la fuente lo publica se usa
(`valoracion.ensamblar_directo`); donde no, se reparte proporcionalmente por
producto, como prescribe el Handbook §7.77 para ese caso (`valoracion.valorar_argentina`).

| País | Impuestos y márgenes | Origen doméstico/importado |
|:---|:---|:---|
| Colombia 2014–2020 | medido | **medido** (MUPNI) |
| México 2013 | medido | **medido** (INEGI DOMESTICO) |
| Argentina, Uruguay, Brasil | prorrateo | prorrateo |

El sesgo del prorrateo está **medido** contra el dato real de México:
sobreestima el consumo intermedio doméstico un 15,7 % e **infla los
multiplicadores un 5,65 % en promedio** (hasta +58 % en manufactura de
exportación). El control queda documentado en `reports/mexico_todos.md`.

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
py -3 scripts/argentina_libros.py      # → matrices/Argentina/
py -3 scripts/brasil_libros.py         # → matrices/Brasil/
py -3 scripts/uruguay_libros.py        # → matrices/Uruguay/
py -3 scripts/mexico_libros.py         # → matrices/Mexico/
py -3 scripts/colombia_libros.py       # → matrices/Colombia/
py -3 scripts/validar_consistencia.py  # auditoría de los 30 libros
py -3 tests/test_sintetico.py
py -3 tests/test_demanda_final.py
```
