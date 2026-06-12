# Plan: incluir COU en las MIP directas

Fecha: 2026-06-10 (actualizado 2026-06-12)

Decision del equipo: todas las matrices deben quedar con su COU en el mismo
Excel; lo que no tenga COU se busca y se descarga. Las 29 matrices
reconstruidas ya lo cumplen. Falta resolver las 6 MIP
directas.

## Estado al 2026-06-12

Implementado el mecanismo de COU de referencia y un pase de calidad/diseno
sobre las 35 matrices:

- **Mecanismo `couref`**: si una serie es MIP directa y existe
  `data/processed/{serie}/couref_{serie}_{anio}.xlsx`, el generador adjunta sus
  hojas como `src_*` de REFERENCIA, fija `tipo_matriz =
  MIP_directa_con_COU_referencia` y NO dispara la logica de reconstruccion ni la
  auditoria producto->sector (la cobertura sigue en modo MIP directa). No
  introduce sectores pendientes.
- **Hoja `Indice`** (portada) como primera hoja de cada Excel: identificacion
  (pais, anio, tipo, fuente) + guia de todas las hojas. La fuente o COU queda
  al inicio en `COU_Tabla_Original`.
- **Mexico 2013: COU adjunto y verificado.** Parser
  `Codigo/scripts/parser_cou_mexico_2013.py` lee el COU matricial INEGI/CEPAL
  (oferta rama SCIAN + demanda p.basicos domestico/importado) y produce
  `couref_mexico_2013.xlsx`. El COU comparte el nivel rama SCIAN (262 ramas) de
  la MIP directa, asi que alinea 1:1. Identidad del COU verificada:
  g (27.64M) = CI dom (8.09M) + CI imp (3.90M) + VA (15.65M); 0 VA negativos.
- **Validacion 35/35 estructural OK; auditoria 0 sectores pendientes**
  (fuente_no_mip = mip_no_fuente = revisar = 0). Mexico 2013 queda como
  `MIP_directa_con_COU_referencia`, 262 sectores.

Estado por caso de las 6 directas (descargas via repositorio CEPAL, ver
`CHECKLIST_DESCARGA_COU_DIRECTAS.md`):

| Caso | COU matricial | Estado |
|---|---|---|
| Mexico 2013 | Completo (CEPAL) | HECHO: COU de referencia adjunto y verificado. |
| Mexico 2018 | ZIP CEPAL corrupto en el servidor | Bloqueado. Demanda matricial hay que sacarla de INEGI directo. |
| Mexico 2003/2008 | Solo oferta en CEPAL | Bloqueado. Falta demanda matricial -> INEGI. |
| Uruguay 2016 | Solo produccion/oferta en CEPAL | Bloqueado. Falta utilizacion -> BCU. |
| Argentina 1997 | No existe COU publico (CEPAL arranca 2004) | Resuelto por documentacion: sin COU separado. |

Bonus disponible: el COU detallado de Uruguay 2017 (`URY_COU_2017.zip`) esta
completo (utilizacion nacional/importada, produccion, oferta) y puede usarse
para revisar la alerta de demanda final negativa de Uruguay 2017.

## Marco metodologico (regla de no mezclar tipos)

Las MIP de Mexico, Uruguay 2016 y Argentina 1997 son MIP DIRECTAS u oficiales,
no reconstruidas desde el COU. Por eso, al adjuntar el COU:

- La MIP publicada sigue siendo la oficial directa; NO se relabela como
  "reconstruida_desde_COU".
- El COU se adjunta como REFERENCIA del mismo marco estadistico y anio
  (COU oficial INEGI/BCU/INDEC), con etiqueta `tipo_matriz =
  MIP_directa_con_COU_referencia`.
- La auditoria de cobertura sigue evaluando los sectores de la MIP directa
  como hasta ahora; el COU de referencia no introduce "sectores pendientes".

## Disponibilidad de datos (revisado en data/raw)

| Caso | COU local | Estado | Accion |
|---|---|---|---|
| Mexico 2003/2008/2013/2018 | Parcial | Los `cou_*_b*.xlsx` son HTML del visor INEGI (no parsean como tabla). Los ZIP CEPAL `MEX_COU_*` traen cuentas AGREGADas por actividad-anio (Produccion, Consumo intermedio, Valor agregado), NO la matriz COU completa producto x industria. | Descargar COU matricial INEGI/CEPAL o construir V/U desde la fuente detallada. |
| Uruguay 2016 | Incompleto | `cou_2016` solo tiene `URY_2016_Produccion_pb_C.xlsx` (oferta). Falta la tabla de utilizacion; por eso `uruguay_cou.parsear` falla. | Descargar utilizacion COU 2016 (BCU/CEPAL). |
| Argentina 1997 | No | Solo estan las MIP `mip_matriz*.xls`; no hay COU 1997. | Descargar COU/MIPAr97 fuente de INDEC o confirmar que 1997 no tiene COU publico. |

Nota: los portales oficiales (IBGE, BCU, INDEC) rechazaron la conexion directa
desde el entorno de ejecucion actual (certificado/firewall). Las descargas
deben hacerse desde la maquina del equipo o reponerse los archivos en
`data/raw`.

## Fuentes para descargar el COU matricial faltante

- Mexico COU/TRU detallado: `https://www.inegi.org.mx/temas/cn/` (Cuenta de
  Bienes y Servicios) y repositorio CEPAL COU/MIP.
- Uruguay COU 2016 utilizacion: BCU COU
  `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/COU.aspx` y
  repositorio CEPAL.
- Argentina COU/MIP 1997: INDEC biblioteca MIPAr97 y repositorio CEPAL.
- Repositorio CEPAL COU/MIP (regional, COU 1988-2022):
  `https://statistics.cepal.org/repository/cou-mip/index.html?lang=es`

## Implementacion prevista (una vez esten los COU matriciales)

1. Parser por fuente que devuelva V_oferta, U_utilizacion, Y_demanda_final,
   W_valor_agregado, M_importaciones para el anio.
2. Guardar COU de referencia en `data/processed/{serie}/couref_{serie}_{anio}.xlsx`.
3. En `generar_paquete_matrices.py`: si la serie es directa y existe el
   `couref_*`, adjuntar hojas `src_*` de referencia y fijar
   `tipo_matriz = MIP_directa_con_COU_referencia`, sin disparar la logica de
   reconstruccion ni la auditoria producto->sector.
4. Regenerar paquete, revalidar y reauditar (debe mantener 34/34 OK y
   0 pendientes).
5. Sincronizar al repo publico y actualizar handoff.

## Interim opcional

Para Mexico se puede adjuntar, mientras llega el COU matricial, las cuentas
agregadas CEPAL (Produccion, Consumo intermedio, Valor agregado por actividad)
como hoja de referencia claramente rotulada "cuentas agregadas, no es la matriz
COU completa". Requiere aprobacion explicita para no inducir a leerlo como COU.
