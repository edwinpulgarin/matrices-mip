# Reconstrucción de MIP desde COU — Resumen general

Pipeline exacto al **UN Handbook on SUT and IOT (Series F No.74 Rev.1, 2018)**:
COU oficial → valoración (Cap. 7) → balanceo RAS (Cap. 11) → transformación
Modelo D industria×industria (Cap. 12) → análisis Leontief (Cap. 20) → libro Excel.

Todas las matrices cumplen, **por construcción**:
`gᵢ = Σⱼ zᵢⱼ + fᵢ` (fila) y `gⱼ = Σᵢ zᵢⱼ + zmⱼ + Wⱼ` (columna) a **~1e-15**,
`L·f = g`, `aᵢⱼ ≥ 0`, `Σᵢ aᵢⱼ < 1`, y **cero negativos**.

## Cobertura (30 matrices país-año)

| País | Años | Dim | Origen de los insumos | Estado |
|---|---|---|---|---|
| **Argentina** (INDEC) | 2004, 2018–2023 (7) | 107–162 | prorrateo | ✅ cuadran |
| **Brasil** (IBGE) | 2010–2021 (12) | 67–68 | **medido en 2010 y 2015**, prorrateo el resto | ✅ cuadran, sin negativos (incl. 2011–2014 que el repo viejo excluía) |
| **Uruguay** (BCU) | 2012, 2016, 2017 (3) | 95–107 | prorrateo | ✅ cuadran + **validado contra MIP oficial** |
| **México** (INEGI) | 2013 (1) | 262×262 | **medido** | ✅ cuadran |
| **Colombia** (DANE) | 2014–2020 (7) | 61×61 | **medido** | ✅ cuadran |

**10 de los 30 libros se reconstruyen sin ningún supuesto de reparto.** Los otros
20 usan el prorrateo proporcional del Handbook §7.77, cuyo sesgo está medido en
tres países: ver `sesgo_prorrateo.md`. Cada libro lleva la nota de método en su
portada, y `manifest_publicables.csv` (autogenerado por el validador) marca cuál
es cuál.

## Validación externa (Uruguay 2016 vs MIP oficial BCU)

- Producción bruta total: **100.0 %** (2,778,445 vs 2,778,447).
- Valor agregado bruto: **99.999 %** (1,544,203 vs 1,544,182).
- Consumo intermedio agregado: 97.8 % (Δ 2.25 %).
- Metodología idéntica: industria×industria, precios básicos, importaciones separadas.

Detalle en `uruguay_validacion.md`.

## Entregables

- `matrices/<País>/MIP_<País>_<Año>_LIBRO.xlsx` — libro de 16 pestañas por matriz
  (Índice con hipervínculos y nota de método, MIP completa con la demanda final
  abierta, Z, vectores, diag(g), balances, coeficientes A, validación, Leontief,
  B, **Auditoría COU** que reconcilia columna a columna contra la fuente,
  **Demanda final** por componente con su mapeo, y el **COU de origen**
  (oferta, utilización y demanda final con las columnas nativas de cada fuente)).
- `output/presentacion_mip.pdf` — presentación metodológica (Beamer).
- `reports/validacion_consistencia.md` — **auditoría final** de los 30 libros
  entregados: re-abre cada Excel y re-verifica dimensiones, balances de fila y
  columna, `A = Z·diag(g)⁻¹`, Leontief `L·f = g` y presencia de nombres.
  Estado: **30/30 libros consistentes**.
- `reports/sesgo_prorrateo.md` — las tres mediciones del sesgo del prorrateo.
- `reports/{argentina,brasil,uruguay,mexico,colombia}_todos.md` — gates por año.
- `manifest_publicables.csv` — inventario, regenerado por el validador.

## Cómo reproducir

```
py -3 scripts/argentina_libros.py      # 107×107 industria×industria
py -3 scripts/brasil_libros.py
py -3 scripts/uruguay_libros.py
py -3 scripts/validar_consistencia.py  # auditoría final de los libros
py -3 tests/test_sintetico.py          # identidades sobre COU sintético
```
