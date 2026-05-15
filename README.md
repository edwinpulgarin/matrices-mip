# Matrices Insumo-Producto CEPAL

Repositorio publico de matrices insumo-producto para Argentina, Brasil, Mexico y Uruguay, con archivos Excel por pais/anio, documentacion metodologica, validaciones y codigo del pipeline usado para construir la base.

```text
.
  MIP/
    Argentina/
    Brasil/
    Mexico/
    Uruguay/
  Codigo/
  Presentacion_MIP_CEPAL.html
  METODOLOGIA.md
  indice_matrices.xlsx
  validacion_matematica_mip.xlsx
```

## Cobertura

- Argentina: 6 matrices (1997-2021).
- Brasil: 22 matrices (2000-2021).
- Mexico: 4 matrices (2003-2018).
- Uruguay: 2 matrices (2016-2017).

Total de matrices: 34

## Como navegar

Abrir `MIP/{Pais}/` y seleccionar el Excel del anio requerido. Cada archivo incluye hojas con matriz de flujos, coeficientes tecnicos, inversa de Leontief, Ghosh, produccion, valor agregado, consumo intermedio importado, multiplicadores y validaciones.

## Criterios metodologicos

- Las matrices se trabajan a precios basicos cuando la fuente lo permite.
- `Z` representa consumo intermedio nacional/domestico.
- El consumo intermedio importado se conserva separado.
- Las filas y columnas conservan nombres de sectores economicos.
- Se validan estructura, alineacion sectorial, Leontief, Ghosh y cierres macro.

Ver `METODOLOGIA.md` para el detalle completo.

## Codigo

La carpeta `Codigo/` contiene el pipeline, parsers, scripts de validacion y scripts de generacion de paquetes. No incluye archivos fuente pesados de `data/raw`.

## Validacion

El resumen de validacion esta en:

```text
validacion_matematica_mip.xlsx
validacion_matematica_mip.md
```

Resultado de la ultima corrida: 34/34 matrices con validacion estructural OK y nombres sectoriales OK.

## Nota de fuentes

La base se construye a partir de fuentes oficiales nacionales y bases CEPAL disponibles localmente en el proyecto original. Revisar `METODOLOGIA.md` y `Codigo/FUENTES_EXTERNAS_HISTORICO.md` para trazabilidad.
