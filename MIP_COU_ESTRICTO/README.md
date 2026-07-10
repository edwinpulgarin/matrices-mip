# Paquete COU estricto con estructura Colombia

Esta carpeta contiene la version recomendada para auditoria contable de corto plazo.

El paquete publica 33 matrices que cumplen una regla fuerte: la informacion se reconstruye desde cuadros de oferta y utilizacion procesados localmente (`V_oferta`, `U_utilizacion`, `Y_demanda_final`, `W_valor_agregado` y, cuando existe, `U_importada`). No usa variables adicionales fuera de la estructura del anexo MIP de Colombia.

## Cobertura

- Argentina: 6 matrices COU (2004, 2018-2022).
- Brasil: 22 matrices COU (2000-2021).
- Mexico: 2 matrices con COU de referencia (2008, 2013).
- Uruguay: 3 matrices COU/referencia (2012, 2016, 2017).

Total publicado: 33 matrices.

Quedan excluidas del paquete COU estricto por falta de COU local comparable: Argentina 1997, Mexico 2003 y Mexico 2018.

## Estructura

Cada libro replica la organizacion de Colombia:

- `Índice`
- `Cuadro 1`: producto por producto, nacional.
- `Cuadro 2`: producto por producto, importada.
- `Cuadro 3`: producto por producto, nacional e importada.
- `Cuadro 4`: producto por producto, multiplicadores.
- `Cuadro 5`: actividad por actividad, nacional.
- `Cuadro 6`: actividad por actividad, importada.
- `Cuadro 7`: actividad por actividad, nacional e importada.
- `Cuadro 8`: actividad por actividad, multiplicadores.

Los valores se publican en miles de millones de moneda local.

## Validacion

Archivos de control:

```text
auditoria_matrices_colombia.xlsx
validacion_estructural_colombia.xlsx
indice_matrices_colombia_auditables.xlsx
```

Resultado vigente: 33/33 matrices publicadas con validacion estructural OK. Uruguay 2012 y Uruguay 2017 quedan marcadas como COU estricto con demanda final residual porque el COU disponible no trae apertura compatible de consumo final y formacion bruta de capital.
