# Revision de fuentes para extender la serie MIP

Fecha de revision: 2026-06-10

Esta nota documenta el estado de disponibilidad de fuentes para los frentes
abiertos del handoff (secciones 9.1, 9.2, 9.3): Uruguay 2017/2018+, Argentina
2005-2017 y Brasil 2022+. El objetivo es dejar trazabilidad de que se reviso,
que se confirmo y que accion concreta queda pendiente, sin alterar matrices ni
inventar datos.

## Confirmado en esta revision

- Repositorio CEPAL COU/MIP: contiene COU para 18 paises de America Latina y
  3 del Caribe en el rango **1988-2022** y MIP para 13 paises de la region en
  el rango **1979-2022**, segun la presentacion del propio repositorio.
  - URL: `https://statistics.cepal.org/repository/cou-mip/index.html?lang=es`
  - Implicacion: existe cobertura potencial para anios mas recientes que los
    ya incorporados, sujeta a verificar pais por pais el detalle disponible.

- No fue posible descargar/verificar archivos especificos en linea durante esta
  sesion (los portales de IBGE y BCU rechazaron la conexion directa por
  certificado/firewall). Por tanto, lo de abajo son acciones a ejecutar desde
  un entorno con acceso, no datos ya obtenidos.

## Uruguay 2017 y 2018+ (handoff 9.1)

Estado: Uruguay 2017 sigue siendo el caso sensible (demanda final negativa
material, no conciliada). 

Accion concreta:

1. En el repositorio CEPAL, descargar el COU de Uruguay del anio mas reciente
   disponible y verificar si trae la demanda final completa por componente.
2. Revisar en BCU si existe MIP directa con anio base actualizado.
   - BCU MIP: `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Matriz-Insumo-Producto.aspx`
   - BCU COU: `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/COU.aspx`
3. Si aparece demanda final fuente completa para 2017, re-correr el parser
   `uruguay_cou` y revalidar; solo entonces evaluar levantar la alerta.
4. Si no aparece, mantener Uruguay 2017 con la alerta metodologica vigente.

Criterio de cierre: no conciliar negativos materiales para "forzar" resultados
(regla del handoff, seccion 6).

## Argentina 2005-2017 (handoff 9.2)

Estado: brecha de cobertura. INDEC publica COU 2018 (referenciado en busqueda),
pero la serie intermedia 2005-2017 no esta disponible de forma publica
homogenea.

Accion concreta:

1. Revisar el repositorio CEPAL por si hay COU de Argentina en anios de ese
   tramo que no esten en el portal de INDEC.
2. Si no, dejar registrada la solicitud directa a INDEC/CEPAL como dependencia
   externa (no resoluble por codigo).

## Brasil 2022+ (handoff 9.3)

Estado: la serie actual llega a 2021 (TRU/COU IBGE nivel 68). El rango CEPAL
llega hasta 2022, por lo que es el frente con mayor probabilidad de extension
inmediata.

Accion concreta:

1. Verificar en IBGE la publicacion de TRU 2022 a precios basicos nivel 68.
   - IBGE MIP: `https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9085-matriz-de-insumo-produto.html`
   - IBGE Contas Nacionais/TRU: `https://www.ibge.gov.br/estatisticas/economicas/comercio/9052-sistema-de-contas-nacionais-brasil.html`
2. Si esta disponible, reutilizar el parser `brasil` (nivel 68) que ya procesa
   2010-2021; confirmar que la estructura de columnas no cambio.
3. Regenerar 2022, validar (`scripts/validar_mips.py`) y auditar cobertura
   antes de publicar.

## Regla de actualizacion

Al concretar cualquiera de estas extensiones, actualizar de forma simultanea
(handoff seccion 3):

- `FUENTES_EXTERNAS_HISTORICO.md` (URL, fecha de revision, archivo descargado,
  ruta local)
- `CLAUDE_HANDOFF.md` (inventario de matrices)
- `METODOLOGIA.md` si cambia el metodo
- `fuente_resumen` y `fuente_notas` en los Excel regenerados
