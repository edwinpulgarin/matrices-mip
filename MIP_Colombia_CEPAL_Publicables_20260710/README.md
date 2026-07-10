# MIP Colombia-style CEPAL publicables 2026-07-10

Este paquete contiene la reconstruccion Colombia-style con paleta CEPAL que paso la puerta semantica de publicacion base.

## Resultado

- Matrices incluidas: 27.
- Estructura de cada Excel: `Indice` y `Cuadro 1` a `Cuadro 8`.
- Unidad visible: miles de millones de moneda local.
- Celdas vacias en demanda final: 0.
- Negativos en matrices intermedias visibles: 0.
- Valor agregado negativo en matrices incluidas: 0.
- Sectores solo codigo en matrices incluidas: 0.

## Matrices excluidas

No se incluyen en este paquete:

- Brasil 2011, 2012, 2013, 2014: valor agregado negativo.
- Uruguay 2016: sectores de actividad solo codigo.
- Uruguay 2017: valor agregado negativo.

Los negativos de demanda final quedan reportados como alerta trazable, no como bloqueo automatico, porque el anexo Colombia de referencia tambien contiene negativos en componentes de demanda final.

## Archivos de control

- `manifest_publicables.csv`: inventario de las 27 matrices incluidas.
- `auditoria_semantica_full.md`: auditoria sobre los 33 libros generados antes de filtrar publicables.
- `diagnostico_reconstruccion.md`: resumen ejecutivo de reglas, cambios y recomendacion de publicacion.
