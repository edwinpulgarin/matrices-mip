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
  Presentacion_Reconstruccion_MIP_Simulador.html
  Prueba_Reconstruccion_MIP_Dummies.xlsx
  Prueba_Reconstruccion_MIP_Finalizadas.xlsx
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

## Matrices directas vs reconstruidas

El repositorio separa dos tipos de matrices:

- **Directas:** la entidad fuente publica una MIP o matriz equivalente que se parsea, normaliza, valida y empaqueta. Incluye Argentina 1997, Mexico 2003/2008/2013/2018 y Uruguay 2016.
- **Reconstruidas desde COU:** la fuente publica cuadros de oferta y utilizacion, y el pipeline reconstruye una MIP industria x industria bajo el supuesto de tecnologia de industria. Incluye Argentina 2004/2018-2021, Brasil 2000-2021 y Uruguay 2017.

La presentacion `Presentacion_Reconstruccion_MIP_Simulador.html` explica esta separacion, el paso a paso de reconstruccion, los cierres menores documentados y la ruta del simulador de choques.

## Como navegar

Abrir `MIP/{Pais}/` y seleccionar el Excel del anio requerido. Cada archivo incluye hojas con matriz de flujos, coeficientes tecnicos, inversa de Leontief, Ghosh, produccion, valor agregado, consumo intermedio importado, multiplicadores y validaciones.

## Criterios metodologicos

- Las matrices se trabajan a precios basicos cuando la fuente lo permite.
- `Z` representa consumo intermedio nacional/domestico.
- El ajuste intermedio fuera de `Z` se conserva separado. En MIP directas puede ser consumo intermedio importado; en COU reconstruidos con puente comprador-basico puede incluir importaciones, margenes, impuestos y diferencias de valoracion.
- Las filas y columnas conservan nombres de sectores economicos.
- Se validan estructura, alineacion sectorial, Leontief, Ghosh y cierres macro.
- Los cierres menores de demanda final solo se aplican si son pequenos y quedan trazados en `ajuste_cierre` y `Z_pre_conciliacion`.

Ver `METODOLOGIA.md` para el detalle completo.

## Excel piloto de reconstruccion y simulador

Para una lectura introductoria, usar primero:

```text
Prueba_Reconstruccion_MIP_Dummies.xlsx
```

Este archivo toma un solo caso reconstruido, Brasil 2001, y explica una celda de `Z`, el cierre menor, el paso a `A/L` y un simulador sencillo de choque.

La version tecnica es:

`Prueba_Reconstruccion_MIP_Finalizadas.xlsx` contiene:

- inventario de matrices directas y reconstruidas;
- paso a paso metodologico;
- ejemplo de cierre menor en Brasil 2001;
- alerta documentada de Uruguay 2017;
- resumen de validaciones matematicas;
- simulador piloto de choque de demanda con `Delta g = L @ Delta f`.

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
