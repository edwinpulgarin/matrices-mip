# Matrices Insumo-Producto CEPAL

Repositorio publico de matrices insumo-producto para Argentina, Brasil, Mexico y Uruguay, con archivos Excel por pais/anio, documentacion metodologica, validaciones y codigo del pipeline usado para construir la base.

## Version auditable V3

Los Excel publicados en `MIP/` corresponden a la version auditable V3: libros con diseno institucional inspirado en el anexo MIP de Colombia y paleta CEPAL. La capa V3 conserva las cifras procesadas, pero reorganiza cada matriz para que los cierres de oferta, demanda, ajuste intermedio, valor agregado y produccion sean visibles en cuadros contables auditables.

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
  CLAUDE_HANDOFF.md
  indice_matrices.xlsx
  indice_matrices.csv
  validacion_matematica_mip.xlsx
  validacion_inversa_mip.xlsx
  auditoria_cobertura_sectores_mip.xlsx
```

## Cobertura

- Argentina: 7 matrices (1997-2022).
- Brasil: 22 matrices (2000-2021).
- Mexico: 4 matrices (2003-2018).
- Uruguay: 3 matrices (2012, 2016-2017).

Total de matrices: 36

## Matrices directas vs reconstruidas

El repositorio separa dos tipos de matrices:

- **Directas:** la entidad fuente publica una MIP o matriz equivalente que se parsea, normaliza, valida y empaqueta. Incluye Argentina 1997, Mexico 2003/2008/2013/2018 y Uruguay 2016.
- **Reconstruidas desde COU:** la fuente publica cuadros de oferta y utilizacion, y el pipeline reconstruye una MIP industria x industria bajo el supuesto de tecnologia de industria. Incluye Argentina 2004/2018-2022, Brasil 2000-2021 y Uruguay 2012/2017.

La presentacion `Presentacion_Reconstruccion_MIP_Simulador.html` explica esta separacion, el paso a paso de reconstruccion, los cierres menores documentados y la ruta del simulador de choques.

## Como navegar

Abrir `MIP/{Pais}/` y seleccionar el Excel del anio requerido. Cada libro anual tiene seis hojas:

- `Indice`: portada, fuente, tipo de matriz, resumen contable y guia de hojas.
- `Cuadro 1`: matriz actividad x actividad nacional/domestica.
- `Cuadro 2`: matriz importada o ajuste intermedio fuera de `Z`.
- `Cuadro 3`: matriz total auditable, con demanda final, ajuste, valor agregado, produccion total y check contra produccion fuente.
- `Cuadro 4`: multiplicadores de Leontief/Ghosh y validacion contable.
- `Notas`: convenciones, fuente y advertencias metodologicas.

Las validaciones matematicas y auditorias se dejan en archivos consolidados separados, no dentro de cada Excel anual.

## Criterios metodologicos

- Las matrices se trabajan a precios basicos cuando la fuente lo permite.
- `Z` representa consumo intermedio nacional/domestico.
- El ajuste intermedio fuera de `Z` se conserva separado. En MIP directas puede ser consumo intermedio importado; en COU reconstruidos con puente comprador-basico puede incluir importaciones, margenes, impuestos y diferencias de valoracion.
- Las filas y columnas conservan nombres de sectores economicos.
- Se validan estructura, alineacion sectorial, Leontief, Ghosh y cierres macro.
- Los cierres menores de demanda final solo se aplican si son pequenos y quedan trazados en `ajuste_cierre` y `Z_pre_conciliacion`.
- Un sector con `Z[i,i] = 0` no se elimina automaticamente. Si tiene produccion, valor agregado, ventas, compras o demanda final, debe conservarse; la diagonal cero solo indica que no registra autoconsumo sectorial.
- Cuando una MIP directa no trae COU o desglose compatible de demanda final, el total sectorial se conserva en `sin_desglose_fuente` y no se imputa artificialmente a consumo, inversion, gobierno o exportaciones.
- `diferencia_y_mip_menos_DA` documenta la brecha entre el cierre sectorial usado por la MIP y la identidad macro homologada `DA = C + I + G + (X - M)`. Esta brecha puede reflejar valoracion, clasificacion, importaciones o componentes fuente no desagregados.

Ver `METODOLOGIA.md` para el detalle completo.

## Handoff para colaboradores

Para que otro colaborador o asistente entre al proyecto sin perder contexto, revisar primero:

```text
CLAUDE_HANDOFF.md
```

Ese archivo resume fuentes, matrices directas vs reconstruidas, comandos de reproduccion, validaciones vigentes, puntos sensibles y siguientes pasos.

## Excel piloto de reconstruccion y simulador

Para una lectura introductoria, usar primero:

```text
Prueba_Reconstruccion_MIP_Dummies.xlsx
```

Este archivo toma un solo caso reconstruido, Brasil 2001, incluye una hoja con el nombre de cada matriz (`V_oferta`, `U_utilizacion`, `D_market_share`, `Z_MIP`, `A_coef_tecnicos`, `L_leontief`, etc.), y explica una celda de `Z`, el cierre menor, el paso a `A/L` y un simulador sencillo de choque.

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

La generacion V3 esta documentada en `Codigo/docs/metodologia_mip_v3_auditable.md`. La validacion inversa contra COU/MIP directa esta documentada en `Codigo/docs/validacion_inversa_mip.md`.

## Validacion

El resumen de validacion esta en:

```text
validacion_matematica_mip.xlsx
validacion_matematica_mip.md
validacion_inversa_mip.xlsx
validacion_inversa_mip.md
auditoria_cobertura_sectores_mip.xlsx
auditoria_cobertura_sectores_mip.md
```

Resultado de la ultima corrida: 36/36 matrices con validacion estructural OK. Las alertas diagnosticas de valor agregado o demanda final negativa quedan expuestas en los cuadros auditables y en los reportes consolidados.

## Nota de fuentes

La base se construye a partir de fuentes oficiales nacionales y bases CEPAL disponibles localmente en el proyecto original. Revisar `METODOLOGIA.md`, `CLAUDE_HANDOFF.md` y `Codigo/FUENTES_EXTERNAS_HISTORICO.md` para trazabilidad.
