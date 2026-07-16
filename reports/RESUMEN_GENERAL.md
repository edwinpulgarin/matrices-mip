# Reconstrucción de MIP desde COU — Resumen general

Pipeline exacto al **UN Handbook on SUT and IOT (Series F No.74 Rev.1, 2018)**:
COU oficial → valoración (Cap. 7) → balanceo RAS (Cap. 11) → transformación
Modelo D industria×industria (Cap. 12) → análisis Leontief (Cap. 20) → libro Excel.

Todas las matrices cumplen, **por construcción**:
`gᵢ = Σⱼ zᵢⱼ + fᵢ` (fila) y `gⱼ = Σᵢ zᵢⱼ + zmⱼ + Wⱼ` (columna) a **~1e-15**,
`L·f = g`, `aᵢⱼ ≥ 0`, `Σᵢ aᵢⱼ < 1`, y **cero negativos**.

## Cobertura (21 matrices país-año)

| País | Años | Dim | Estado |
|---|---|---|---|
| **Argentina** (INDEC) | 2004, 2018–2022 (6) | 107–162 | ✅ cuadran, libros generados |
| **Brasil** (IBGE nível 68) | 2010–2021 (12) | 68×68 | ✅ cuadran, sin negativos (incl. 2011–2014 que el repo viejo excluía) |
| **Uruguay** (BCU) | 2012, 2016, 2017 (3) | 95–107 | ✅ cuadran + **validado contra MIP oficial** |
| México (INEGI) | — | — | ⏳ pendiente (datos fragmentados, ver `mexico_pendiente.md`) |

## Validación externa (Uruguay 2016 vs MIP oficial BCU)

- Producción bruta total: **100.0 %** (2,778,445 vs 2,778,447).
- Valor agregado bruto: **99.999 %** (1,544,203 vs 1,544,182).
- Consumo intermedio agregado: 97.8 % (Δ 2.25 %).
- Metodología idéntica: industria×industria, precios básicos, importaciones separadas.

Detalle en `uruguay_validacion.md`.

## Entregables

- `output/MIP_<País>_<Año>_LIBRO*.xlsx` — libro de 13 pestañas por matriz
  (Índice con hipervínculos, MIP completa, Z, vectores, diag(g), balances,
  coeficientes A, validación, Leontief, B, y **Auditoría COU** que reconcilia
  columna a columna contra la fuente).
- `output/presentacion_mip.pdf` — presentación metodológica (Beamer).
- `reports/<país>_todos.md` — tabla de gates por año.

## Cómo reproducir

```
py -3 scripts/argentina_libros.py      # 107×107 industria×industria
py -3 scripts/brasil_libros.py
py -3 scripts/uruguay_libros.py
py -3 tests/test_sintetico.py          # identidades sobre COU sintético
```
