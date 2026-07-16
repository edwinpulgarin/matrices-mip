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
| `export_libro.py` | — | libro Excel auditable (13 pestañas, con Auditoría COU) |

## Cobertura

- **Argentina** (INDEC): 2004, 2018–2022
- **Brasil** (IBGE): 2010–2021
- **Uruguay** (BCU): 2012, 2016, 2017 — validado contra la MIP oficial
- México (INEGI): pendiente (ver `reports/mexico_pendiente.md`)

Ver `reports/RESUMEN_GENERAL.md` para el detalle y `output/` para los libros.

## Reproducir

```
py -3 scripts/argentina_libros.py
py -3 scripts/brasil_libros.py
py -3 scripts/uruguay_libros.py
py -3 tests/test_sintetico.py
```
