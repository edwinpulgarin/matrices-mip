# Matrices Insumo-Producto CEPAL

Repositorio publico con 27 matrices insumo-producto auditables para Argentina,
Brasil, Mexico y Uruguay.

Esta version deja solo las matrices que pasaron la puerta semantica de
publicacion base. Los libros siguen la estructura visual del anexo MIP de
Colombia (`Índice` y `Cuadro 1` a `Cuadro 8`) con paleta CEPAL.

## Contenido

```text
.
  matrices/
    Argentina/
    Brasil/
    Mexico/
    Uruguay/
  manifest_publicables.csv
  auditoria_semantica_full.md
  diagnostico_reconstruccion.md
```

## Cobertura Publicable

- Argentina: 6 matrices, anios 2004, 2018, 2019, 2020, 2021 y 2022.
- Brasil: 18 matrices, anios 2000 a 2010 y 2015 a 2021.
- Mexico: 2 matrices, anios 2008 y 2013.
- Uruguay: 1 matriz, anio 2012.

Total: 27 matrices.

## Criterios De Publicacion

Una matriz queda incluida solo si cumple las reglas minimas para auditoria:

- estructura exacta de hojas Colombia-style: `Índice` y `Cuadro 1` a
  `Cuadro 8`;
- unidad visible en miles de millones de moneda local;
- nombres sectoriales presentes, no solo codigos;
- demanda final no vacia;
- matrices intermedias visibles sin valores negativos;
- valor agregado visible sin valores negativos;
- sin errores de formulas en el libro Excel.

Las alertas de demanda final negativa quedan reportadas, no ocultas, porque el
anexo Colombia usado como referencia tambien contiene negativos en componentes
de demanda final.

## Matrices Excluidas

No se publican en esta version:

- Brasil 2011, 2012, 2013 y 2014: valor agregado negativo.
- Uruguay 2016: sectores de actividad solo con codigo.
- Uruguay 2017: valor agregado negativo.

El detalle esta documentado en `diagnostico_reconstruccion.md` y
`auditoria_semantica_full.md`.

## Archivos De Control

- `manifest_publicables.csv`: inventario de las 27 matrices incluidas.
- `auditoria_semantica_full.md`: auditoria sobre los 33 libros generados antes
  de filtrar los publicables.
- `diagnostico_reconstruccion.md`: resumen ejecutivo de reglas, cambios y
  recomendacion de publicacion.
