# Diagnostico de reconstruccion MIP Colombia-style

Fecha de corte: 2026-07-10

## Resultado ejecutivo

- Libros Colombia-style generados: 33.
- Libros con puerta semantica `PUBLICABLE_BASE`: 27.
- Libros `NO_PUBLICABLE`: 6.
- Celdas vacias en demanda final: 0.
- Celdas negativas en matrices intermedias visibles: 0.
- Errores de formula detectados: 0.
- Hojas esperadas: `Índice` y `Cuadro 1` a `Cuadro 8`, siguiendo el anexo Colombia.
- Unidad visible homologada: miles de millones de moneda local.

Los negativos de demanda final se mantienen como alerta trazable, no como bloqueo automatico, porque el anexo Colombia usado como referencia tambien contiene negativos en componentes de demanda final. Los bloqueos se reservan para fallas contables/visuales fuertes: valor agregado negativo, nombres solo codigo, celdas vacias, formulas rotas o matrices intermedias negativas.

## Cambios principales

- El generador normaliza `U` y `U_importada` antes de construir los cuadros, evitando importaciones intermedias negativas o mayores al uso total.
- La auditoria se saco del Excel visible; ahora queda en CSV/Markdown separados.
- El diseno se ajusto a la estructura Colombia con paleta CEPAL, encabezado centrado, indice limpio y 9 pestanas.
- Argentina fue reprocesada para que los productos tengan codigo y nombre descriptivo; ya no quedan productos tipo `011` sin descripcion.
- Se agrego render por rango para verificar visualmente matrices grandes sin intentar pintar libros completos gigantes.
- Los multiplicadores de `Cuadro 4` y `Cuadro 8` fueron recalculados desde los cuadros totales visibles. Los sectores sin enlaces intermedios quedaron ocultos en esas hojas, no eliminados.

## Publicables base

- Argentina 2004, 2018, 2019, 2020, 2021, 2022.
- Brasil 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2015, 2016, 2017, 2018, 2019, 2020, 2021.
- Mexico 2008, 2013.
- Uruguay 2012.

## No publicables todavia

- Brasil 2011, 2012, 2013, 2014: valor agregado negativo en celdas visibles.
- Uruguay 2016: las hojas actividad por actividad tienen sectores solo codigo.
- Uruguay 2017: valor agregado negativo en celdas visibles.

## Archivos clave

- Libros publicables: `matrices/{Pais}/`
- Manifiesto: `manifest_publicables.csv`
- Auditoria completa: `auditoria_semantica_full.md`
- Resumen del paquete: `README.md`

## Recomendacion para publicacion

Publicar solo las 27 matrices `PUBLICABLE_BASE` y adjuntar la auditoria. Las 6 restantes deben quedar como pendientes con causa explicita. Publicarlas hoy mezcladas con las 27 sanas debilitaria la defensa contable del paquete.
