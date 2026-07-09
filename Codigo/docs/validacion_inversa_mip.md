# Validacion inversa de matrices insumo-producto

Fecha: 2026-07-06

## Objetivo

Agregar una prueba auditable para los casos en que existe una MIP observada o
directa y, en paralelo, existe un COU procesado del mismo pais y anio.

La prueba no reemplaza las validaciones contables tradicionales. Las
complementa midiendo si la transformacion COU -> MIP reproduce:

- la matriz de flujos intermedios domesticos/nacionales;
- los coeficientes tecnicos;
- la inversa de Leontief;
- la produccion, demanda final y valor agregado sectorial.

## Dos tipos de prueba

### 1. Roundtrip de matrices reconstruidas

Para las matrices construidas por el proyecto desde COU, se vuelve a ejecutar
la transformacion sobre el COU procesado y se compara contra la MIP guardada.

Lectura esperada:

- `OK_REPRODUCE`: la MIP guardada reproduce numericamente el COU y el algoritmo.
- `OK_CON_AJUSTE_CIERRE`: hay una diferencia pequena y trazable porque la MIP
  guardada contiene conciliacion de cierre (`ajuste_cierre` o
  `Z_pre_conciliacion`).
- `REVISAR_ROUNDTRIP`: la MIP guardada no reproduce el algoritmo actual y debe
  revisarse.

### 2. Benchmark contra MIP directa

Para las MIP directas/oficiales con COU de referencia, se reconstruye una MIP
desde el COU y se compara contra la MIP observada.

Esta prueba no exige igualdad celda a celda: una MIP oficial puede usar
hipotesis, conciliaciones o informacion institucional que no esta contenida en
el COU procesado. El resultado mide la cercania del supuesto de transformacion.

Lectura esperada:

- `BENCHMARK_FUERTE`: buena reproduccion de magnitudes y estructura.
- `BENCHMARK_ACEPTABLE`: usable, pero con diferencias materiales.
- `REVISAR_BENCHMARK`: diferencias demasiado grandes para usar como respaldo
  metodologico sin investigar.
- `NO_COMPARABLE`: no hay COU o la clasificacion sectorial no se puede alinear.

## Metricas principales

- `WMAPE`: suma de diferencias absolutas dividida por la suma absoluta
  observada. Es la metrica central para matrices dispersas.
- `sesgo_rel_sobre_abs_observado`: diferencia agregada relativa; detecta
  sobre/subestimacion sistematica.
- `corr_todas`: correlacion de Pearson celda a celda; mide similitud
  estructural.
- `max_abs`: mayor diferencia absoluta celda a celda.
- `signos_distintos_obs_no_cero`: celdas donde el signo reconstruido difiere
  del observado en celdas observadas no nulas.

## Alineacion sectorial

La comparacion intenta primero etiquetas exactas. Si no coinciden, usa el
codigo sectorial al inicio de la etiqueta. Esto permite alinear, por ejemplo,
`3334---Fabricacion...` con `3334 - Fabricacion...`.

Si no hay suficientes claves comunes, el caso queda como `NO_COMPARABLE` y no
se fuerza una correspondencia artificial.

## Salidas

El script reproducible es:

```powershell
python scripts\validar_mip_inversa.py
```

Genera:

- `output/tablas/validacion_inversa_mip.xlsx`
- `output/tablas/validacion_inversa_mip.md`
