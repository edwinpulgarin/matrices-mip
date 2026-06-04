# Auditoria de construccion de matrices MIP

**Fecha:** 4 de junio de 2026  
**Objetivo:** revisar si la demanda final negativa se originaba en la construccion de las matrices, antes de considerar cualquier ajuste numerico.

## 1. Conclusion ejecutiva

Si. Una parte importante del problema estaba en la construccion.

No era necesario "maquillar" cifras ni ajustar proporcionalmente `Z`. Encontramos errores de lectura y de armonizacion contable que explicaban buena parte de los sectores con demanda final negativa:

- columnas totales leidas como si fueran componentes de demanda final;
- una columna total de Brasil leida como si fuera actividad economica;
- actividades perdidas por diferencias menores de codigos/acentos;
- reemplazo general de la demanda final fuente por una demanda final residual;
- mezcla de usos a precios comprador con produccion a precios basicos sin usar el puente de valoracion publicado.

La correccion aplicada conserva la informacion fuente depurada y usa factores publicados de conversion por producto. La demanda final residual queda solo como recurso puntual para productos sin fila de uso a precios comprador pero con produccion domestica positiva.

## 2. Correcciones aplicadas

### Argentina

Archivos modificados:

- `src/parsers/argentina.py`
- `main.py`

Hallazgos:

- En Argentina 2004 y 2018-2021 se estaba incluyendo `UF` dentro de `Y`.
- `UF` no es una categoria adicional: es el total de utilizacion final.
- Incluir `UF` duplicaba demanda final al sumar `CH`, `CP`, `EX`, inversion/inventarios y luego el total.
- En 2018-2021 se perdian cuatro actividades por diferencias de codigo entre oferta y uso:
  - `1512` vs `15120`
  - `1513` vs `15130`
  - `1514` vs `15140`
  - `1520` vs `15200`

Correccion:

- `UF` queda excluido de la demanda final fuente.
- Los codigos con cero final se mapean a la actividad con nombre economico.
- La serie 2018-2021 recupera 107 actividades.
- La demanda final se conserva desde la fuente, convertida a base domestica/precios basicos con:

```text
factor_producto = produccion_domestica_pb / demanda_total_pc
```

### Brasil 2010-2021

Archivos modificados:

- `src/parsers/brasil.py`
- `main.py`

Hallazgos:

- La columna `Total do produto` estaba entrando como actividad.
- Por eso la serie IBGE nivel 68 salia con 69 sectores.
- Las columnas agregadas `Demanda final` y `Demanda total` estaban entrando dentro de `Y`.

Correccion:

- `Total do produto` se excluye de actividades.
- `Demanda final` y `Demanda total` se excluyen de componentes de demanda final.
- La serie queda en 68 actividades.
- `U` e `Y` se convierten a base domestica/precios basicos usando el puente:

```text
factor_producto = produccion_domestica_pb / oferta_total_precio_consumidor
```

### Brasil 2000-2009

Archivos modificados:

- `src/parsers/brasil_early.py`
- `main.py`

Hallazgos:

- La serie CEPAL base 2000 debia tener 51 actividades, pero quedaba en 49.
- Dos actividades se perdian por diferencias de acentuacion entre oferta y uso.
- Tambien se leian columnas agregadas de demanda.

Correccion:

- Las columnas de `U` se alinean por posicion con `V`, preservando nombres de oferta.
- Se excluyen `Demanda final` y `Demanda total`.
- La serie recupera 51 actividades.
- Se aplica el factor producto basado en produccion domestica y oferta total a precio consumidor.

### Uruguay

Uruguay 2016 es MIP directa BCU y no fue reconstruida.  
Uruguay 2017 sigue dependiendo de demanda final residual porque el paquete COU disponible no trae una matriz completa de demanda final fuente equivalente a la usada para Argentina/Brasil.

Por eso Uruguay 2017 conserva 2 sectores con demanda final negativa. Este caso debe explicarse como limitacion de fuente/reconstruccion, no como error algebraico.

## 3. Resultados despues de corregir y regenerar

Se regenero el pipeline completo:

```powershell
py -3 -X utf8 main.py
py -3 -X utf8 scripts\validar_mips.py
py -3 -X utf8 scripts\generar_paquete_matrices.py
```

Archivos actualizados:

- `data/processed/*/mip_*.xlsx`
- `data/processed/*/cou_*.xlsx`
- `output/tablas/validacion_matematica_mip.xlsx`
- `output/tablas/validacion_matematica_mip.md`
- `output/matrices_insumo_producto/`

Resultado de validacion:

```text
Matrices revisadas: 34
Validacion estructural: 34 OK
```

Sectores con demanda final negativa despues de la correccion:

| Grupo | Sectores negativos totales |
|---|---:|
| Argentina reconstruida | 0 |
| Brasil 2010-2021 | 0 |
| Brasil 2000-2009 | 6 |
| Mexico directo | 4 |
| Uruguay 2016 directo | 1 |
| Uruguay 2017 reconstruido | 2 |

Lectura:

- Argentina queda sin demanda final sectorial negativa en todos los anos reconstruidos.
- Brasil 2010-2021 queda sin demanda final sectorial negativa.
- Brasil 2000-2009 queda con negativos muy acotados, asociados a componentes fuente como variacion de existencias y pequenas diferencias de cierre.
- Mexico y Uruguay directos no se reconstruyen; sus negativos vienen del cierre implicito de las MIP directas.
- Uruguay 2017 requiere una revision aparte si se quiere eliminar negativos sin alterar cifras.

## 4. Comparacion contra el problema inicial

Antes de corregir la construccion, el diagnostico mostraba muchos negativos generados por el residual:

| Pais/serie | Antes | Despues |
|---|---:|---:|
| Argentina 2004 | 20 sectores negativos | 0 |
| Argentina 2018 | 28 | 0 |
| Argentina 2019 | 28 | 0 |
| Argentina 2020 | 27 | 0 |
| Argentina 2021 | 26 | 0 |
| Brasil 2010-2021 | 11-14 por ano | 0 |
| Brasil 2000-2009 | 11-14 por ano | 0-1 por ano |
| Uruguay 2017 | 2 | 2 |

Esto confirma que el problema principal no era economico ni "ilegal" de la fuente: era una combinacion de lectura de totales, alineacion y valoracion.

## 5. Recomendacion para responder al equipo

Respuesta sugerida:

> Revisamos la construccion y encontramos que parte de la demanda final negativa no venia de cuentas nacionales, sino de la forma en que estabamos reconstruyendo las matrices desde COU. Corregimos la lectura de columnas totales, recuperamos actividades perdidas por codigos/acentos y dejamos de reemplazar de forma general la demanda final fuente por un residual. Ahora usamos la demanda final fuente depurada y la convertimos a base domestica/precios basicos con los puentes publicados por producto. Con esto Argentina queda sin sectores negativos en los anos reconstruidos y Brasil 2010-2021 tambien. Uruguay 2017 sigue siendo el caso pendiente porque no tenemos una demanda final fuente completa en el COU disponible.

## 6. Nota metodologica importante

La correccion no ajusta `Z` para forzar resultados. No se redujeron flujos ni se redistribuyeron cifras para eliminar negativos.

Lo que se hizo fue:

1. leer correctamente las columnas de la fuente;
2. excluir totales agregados que no eran componentes;
3. alinear actividades equivalentes;
4. usar el puente de precios publicado para llevar `U` e `Y` a una base compatible con `V`;
5. conservar el residual solo cuando la estructura del COU no trae una fila de uso comprador para un producto con produccion domestica positiva.

Esto es una correccion metodologica y de parsing, no un maquillaje de cifras.

## 7. Pendientes

- Renombrar en los Excel la hoja/variable `ci_importado` cuando provenga de un ajuste comprador-basico, porque no representa importacion intermedia pura.
- Preparar una nota especifica para Uruguay 2017.
- Actualizar la presentacion con la correccion de construccion y los resultados antes/despues.
- Si el equipo lo aprueba, retirar o mover a anexo interno el paquete robusto experimental para evitar confusion con las matrices oficiales.
