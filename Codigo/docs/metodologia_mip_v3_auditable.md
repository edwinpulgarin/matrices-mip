# MIP V3 auditable

Fecha: 2026-07-06

## Objetivo

Construir una capa de entregables MIP contablemente auditable y visualmente
similar al anexo MIP de Colombia. La V3 no reemplaza los datos procesados ni
maquilla cifras: reorganiza la informacion para que los cierres de oferta,
demanda, valor agregado y ajustes intermedios sean visibles en el mismo cuadro.

## Estructura del libro

Cada libro V3 contiene:

- `Indice`: portada, fuente, tipo de matriz y resumen de validaciones.
- `Cuadro 1`: matriz actividad x actividad nacional/domestica.
- `Cuadro 2`: matriz importada o ajuste intermedio fuera de `Z`.
- `Cuadro 3`: matriz total auditable, con demanda final, ajuste, valor
  agregado, produccion total y check contra produccion fuente.
- `Cuadro 4`: multiplicadores de Leontief/Ghosh y validacion contable.
- `Notas`: convenciones, fuente y advertencias metodologicas.

## Principios contables

1. `Z` nacional/domestica queda separada de importaciones o ajustes de
   valoracion.
2. El ajuste intermedio se conserva con signo. Si es negativo, queda visible.
3. El valor agregado se toma de la fuente/procesamiento y se compara contra el
   residual contable.
4. La demanda final se muestra como:
   - gasto de consumo final;
   - formacion bruta de capital;
   - exportaciones netas;
   - sin desglose fuente;
   - total.
5. Para evitar errores de signo en importaciones, `Exportaciones netas` se
   calcula como residuo frente al total MIP cuando hay componentes C/G/I.
6. Si una fuente no trae apertura compatible, el total queda en
   `Sin desglose fuente`; no se imputa artificialmente a consumo, inversion o
   exportaciones.

## Validaciones nuevas

La validacion matematica ahora reporta explicitamente:

- sectores con demanda final negativa;
- minimo de demanda final;
- sectores con valor agregado negativo;
- minimo de valor agregado;
- sectores con valor agregado residual negativo;
- sectores con ajuste intermedio negativo.

Esto evita que una matriz pase como "diagnostico OK" solo porque las identidades
algebraicas cierran.

## Generacion

Desde la raiz del proyecto:

```powershell
py -3 -X utf8 scripts\generar_matrices_auditables.py
```

Salida:

```text
output/matrices_insumo_producto_auditables/
```

Para un piloto:

```powershell
py -3 -X utf8 scripts\generar_matrices_auditables.py --pais brasil --anio 2021
```

El piloto escribe `indice_matrices_auditables_filtrado.xlsx` para no sobrescribir
el indice completo.

## Estado inicial

La primera corrida genero 36 libros auditables:

- Argentina: 7
- Brasil: 22
- Mexico: 4
- Uruguay: 3

Alertas contables principales:

- Brasil 2011-2014: 1 sector con valor agregado negativo por ano
  (`Refino de petroleo e coquerias`).
- Uruguay 2017: 1 sector con valor agregado negativo y 2 con demanda final
  negativa.
- Uruguay 2012: 13 sectores con demanda final negativa.
- Mexico 2008 y 2013: demanda final negativa puntual.

Estas alertas no se corrigen automaticamente. Quedan expuestas para revision de
fuente, valoracion, importaciones y componentes de demanda final.
