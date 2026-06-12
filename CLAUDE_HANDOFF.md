# Handoff para Claude y siguientes colaboradores

Fecha de corte: 2026-06-12

## Novedades 2026-06-12

- Las 35 matrices publicadas fueron regeneradas con una estructura simplificada
  ampliada de **15 hojas**:
  `Indice`, `COU_Tabla_Original`, `V_oferta`, `q_produccion_producto`,
  `U_nacional`, `D_market_share`, `Z_consumos_intermedios`,
  `x_produccion_bruta`, `y_demanda_final`, `X_hat`, `A_coef_tecnicos`,
  `L_leontief`, `B_coef_distribucion`, `G_ghosh_inversa` y
  `encadenamientos`.
- La hoja `y_demanda_final` fue homologada a la lectura
  `DA = C + I + G + XN`, con `XN = X - M`. Tambien conserva
  `y_demanda_final_total_mip` y `diferencia_y_mip_menos_DA` para no ocultar
  brechas entre la identidad macro y el cierre sectorial de la MIP.
- No se imputan componentes macro sin fuente. Si una matriz no trae COU o
  desglose compatible, el total queda en `sin_desglose_fuente`. Casos sin COU
  publico separado: Argentina 1997, Mexico 2003 y Mexico 2018.
- Se agrego `G_ghosh_inversa = (I - B)^-1` y una hoja `encadenamientos`. Los
  encadenamientos son indicadores derivados de sumas por fila/columna de `L` y
  `G`; no son la inversa completa en si mismos.
- Se ajusto `Codigo/src/simulador.py` para leer `y_demanda_final_total_mip`
  como columna total de demanda final. Pruebas realizadas:
  - demanda Mexico 2013, choque `1111=1%`, multiplicador 1.2549;
  - oferta Brasil 2015, choque `0191=1%`, multiplicador 1.8107.
- Verificacion posterior a la regeneracion: 35/35 archivos con las 15 hojas
  esperadas, 0 problemas de nombres en `Z`, 0 problemas de columnas en
  `y_demanda_final` y 0 problemas de cuadratura en `A`, `L`, `B`, `G`.

## Novedades 2026-06-11

- **Serie extendida: Argentina 2022** reconstruida desde COU INDEC
  (`Argentina_sh_cou_2022_06_25.xls` -> `data/raw/argentina/cou_2022.xls`;
  parser argentina `_parsear_2018_gen`, formato Mat_Of_pc/Mat_Ut_pc). 107
  sectores, Leontief OK. La entrega pasa de 34 a **35 matrices**. Config en
  `main.py`: argentina `anios = range(2004, 2023)`. Regenerado/validado/auditado:
  35/35 estructural OK, 0 pendientes.


- Las 35 matrices publicadas quedaron inicialmente en formato simplificado de 9 hojas
  (actualizado el 2026-06-12 a 15 hojas):
  `Indice`, `COU_Tabla_Original`, `Z_consumos_intermedios`,
  `x_produccion_bruta`, `y_demanda_final`, `X_hat`, `A_coef_tecnicos`,
  `L_leontief`, `B_coef_distribucion`. Las validaciones quedan fuera del libro
  anual, en `validacion_matematica_mip.*` y
  `auditoria_cobertura_sectores_mip.*`.
- Nuevo mecanismo de COU de REFERENCIA para MIP directas (`couref`): adjunta el
  COU oficial del mismo marco como `src_*`, marca
  `tipo_matriz = MIP_directa_con_COU_referencia` y no toca la auditoria.
  Detalle en `Codigo/docs/plan_cou_en_mip_directas.md`.
- Mexico 2013 ya lleva su COU matricial INEGI/CEPAL adjunto (parser
  `Codigo/scripts/parser_cou_mexico_2013.py`). El resto de directas siguen
  bloqueadas por disponibilidad de fuente (ver el plan y el checklist).
- Regenerado y verificado: validacion 35/35 estructural OK, auditoria 0
  sectores pendientes.
- Notacion alineada al documento CEPAL "Metodologia MIP Extendida
  Ambientalmente y Huella de Carbono" (2025): se renombraron las hojas de
  vectores a la convencion del marco (g_produccion -> x_produccion_bruta;
  f_demanda_final -> y_demanda_final; W_valor_agregado -> v_valor_agregado) y
  se agrego una hoja `metodologia` con simbolos y ecuaciones (Z, x, y, A, L,
  B, G, multiplicadores, BL/FL). El simulador (`Codigo/src/simulador.py`) se
  actualizo para leer los nombres nuevos (con respaldo a los antiguos) y para
  tomar la columna total de la demanda final cuando viene desglosada.
- La extension ambiental del documento (D1, D, Da, huella de carbono) NO se
  implemento: requiere vectores de emisiones por sector que aun no tenemos
  para Argentina/Brasil/Mexico/Uruguay. Queda descrita en la hoja
  `metodologia` como marco de referencia.
- Cobertura de COU/fuente: **32/35 con COU o COU de referencia** (29
  reconstruidas + Mexico 2008, Mexico 2013, Uruguay 2016). Parsers:
  `Codigo/scripts/parser_cou_mexico_2008.py`
  (COU INEGI 2008, U_dom reconcilia con Z ratio 1.0000) y
  `parser_cou_uruguay_2016.py` (COU BCU 2016 detallado, 95 ind x 110 prod,
  adjunto como referencia oficial; se omite VA por desalineacion del subcuadro).
  Las 3 restantes NO tienen COU publico disponible y llevan su fuente explicada
  al inicio (README + fuente_resumen + metodologia + fuente_notas detallada):
  Mexico 2018 (el release MIP 2018 de INEGI -tabulados_MIP.zip y datos abiertos
  mip_csv.zip, revisados 2026-06-11- trae solo la MIP simetrica, sin COU),
  Mexico 2003 (MIP de 20 sectores, sin COU rama compatible) y Argentina 1997
  (no existe COU publico; CEPAL arranca 2004). Esto cumple la regla del equipo:
  cada MIP lleva su COU o su fuente al inicio. Ver
  `Codigo/docs/CHECKLIST_DESCARGA_COU_DIRECTAS.md`.

Fecha de corte anterior: 2026-06-10

Este documento es la puerta de entrada para continuar el proyecto sin perder trazabilidad. El objetivo es que cualquier colaborador pueda distinguir que esta publicado, que fue reconstruido, que fuentes se usaron, que validaciones ya pasaron y donde quedan riesgos metodologicos.

## 1. Estado actual

Repositorio: `edwinpulgarin/matrices-mip`

Entrega vigente:

- 35 archivos Excel anuales en `MIP/{Pais}/`.
- 6 matrices directas o equivalentes de fuente.
- 29 matrices reconstruidas desde COU.
- Todas las matrices publicadas tienen trazabilidad al inicio del libro. En la
  entrega publica simplificada se condensa en `Indice` y
  `COU_Tabla_Original`; la estructura tecnica completa queda en el pipeline.
- Validacion estructural: 35/35 OK.
- Auditoria de cobertura sectorial: 0 sectores de fuente pendientes por incorporar en la MIP final.

Archivos que conviene leer primero:

1. `README.md`
2. `METODOLOGIA.md`
3. `MIP/README.md`
4. `auditoria_cobertura_sectores_mip.md`
5. `validacion_matematica_mip.md`
6. `Codigo/docs/auditoria_construccion_matrices_mip.md`
7. `Codigo/docs/ajustes_cierre_brasil_uruguay_y_fuentes_uruguay2017.md`
8. `Codigo/FUENTES_EXTERNAS_HISTORICO.md`

## 2. Inventario de matrices

| Pais | Anios | Tipo | Fuente base documentada |
|---|---:|---|---|
| Argentina | 1997 | MIP directa | MIPAr97 INDEC |
| Argentina | 2004, 2018-2022 | Reconstruida desde COU | COU INDEC/CEPAL |
| Brasil | 2000-2009 | Reconstruida desde COU | COU CEPAL Brasil base 2000 |
| Brasil | 2010-2021 | Reconstruida desde COU | COU/TRU IBGE nivel 68 |
| Mexico | 2003, 2008, 2013, 2018 | MIP directa | MIP CEPAL/INEGI |
| Uruguay | 2016 | MIP directa | MIP BCU 2016 |
| Uruguay | 2017 | Reconstruida desde COU | COU CEPAL/BCU 2017 |

El repo publico contiene los entregables y el codigo, pero no necesariamente todo `data/raw` ni `data/processed` pesado. Para regenerar desde cero se necesita el workspace completo local `C:\Users\edwin\Documents\MIP V2` o reponer las fuentes crudas desde las paginas oficiales.

## 3. Fuentes oficiales y paginas de referencia

Argentina:

- INDEC, COU: `https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-114`
- INDEC, MIPAr97/biblioteca: `https://biblioteca.indec.gob.ar/cgi-bin/wxis.exe/iah/scripts/?IsisScript=iah.xis&base=minde&exprSearch=MATRIZ+INSUMO+PRODUCTO&indexSearch=DD&lang=es&nextAction=lnk`
- INDEC, documentacion MIPAr97: `https://biblioteca.indec.gob.ar/bases/minde/2mi441_5.pdf`

Brasil:

- IBGE, Sistema de Contas Nacionais / Tabelas de Recursos e Usos: `https://www.ibge.gov.br/estatisticas/economicas/comercio/9052-sistema-de-contas-nacionais-brasil.html`
- IBGE, Matriz de Insumo-Produto: `https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9085-matriz-de-insumo-produto.html`
- CEPAL, repositorio COU/MIP: `https://statistics.cepal.org/repository/cou-mip/index.html?lang=es`

Mexico:

- INEGI, MIP general: `https://www.inegi.org.mx/temas/mip/`
- INEGI, MIP 2003: `https://www.inegi.org.mx/programas/mip/2003/`
- INEGI, MIP 2008: `https://www.inegi.org.mx/programas/mip/2008/`
- INEGI, MIP 2013: `https://www.inegi.org.mx/programas/mip/2013/`
- INEGI, MIP 2018: `https://www.inegi.org.mx/programas/mip/2018/`

Uruguay:

- BCU, MIP: `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Matriz-Insumo-Producto.aspx`
- BCU, COU: `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/COU.aspx`
- CEPAL, repositorio COU/MIP: `https://statistics.cepal.org/repository/cou-mip/index.html?lang=es`

Si se agrega una fuente nueva, actualizar simultaneamente:

- `Codigo/FUENTES_EXTERNAS_HISTORICO.md`
- este archivo
- `METODOLOGIA.md` si cambia el metodo
- `fuente_resumen` y `fuente_notas` en los Excel regenerados

## 4. Logica de reconstruccion desde COU

Para matrices reconstruidas se usa el supuesto de tecnologia de industria:

```text
D = V * diag(q)^-1
Z = D * U_nacional
A = Z * diag(g)^-1
L = (I - A)^-1
B = diag(g)^-1 * Z
G = (I - B)^-1
f = D * y_domestica
```

Donde:

- `V` es oferta/produccion por industria y producto.
- `q` es produccion por producto.
- `U_nacional` es utilizacion intermedia nacional/domestica.
- `g` es produccion bruta por industria.
- `Z` es la MIP industria x industria.
- `A` son coeficientes tecnicos.
- `L` es inversa de Leontief.
- `B` son coeficientes de Ghosh.
- `G` es inversa de Ghosh.

Punto metodologico delicado: no confundir productos COU con sectores MIP. Un producto puede aparecer en `cobertura_productos` y no como sector final, porque la transformacion COU -> MIP pasa por `D_market_share`.

## 5. Sectores con diagonal cero

Un sector con `Z[i,i] = 0` no debe eliminarse automaticamente.

Regla vigente:

- Si el sector tiene produccion, valor agregado, ventas, compras o demanda final, se conserva.
- La diagonal cero solo indica que no registra autoconsumo en la fuente o en la transformacion.
- Estos casos se documentan en `cobertura_sectores` como `diagonal_cero_con_flujos`.

Ejemplo mencionado por el equipo: Servicios Domesticos en Argentina. Debe permanecer si aparece como actividad con produccion/VA/flujos, aunque no se compre a si mismo.

## 6. Demanda final negativa y ajustes

Hubo una preocupacion fuerte del equipo sobre demanda final negativa. La decision metodologica vigente es:

- Primero revisar construccion, parsers, totales leidos por error, codigos, acentos y puentes de precios.
- No alterar cifras para "forzar" resultados.
- Solo aplicar conciliacion menor cuando el negativo sea pequeno, localizado y justificable como cierre/redondeo.
- Toda conciliacion debe dejar trazabilidad en:
  - `ajuste_cierre`
  - `Z_pre_conciliacion`

Correcciones ya aplicadas:

- Argentina: exclusion de `UF` como componente de demanda final; recuperacion de actividades por codigos equivalentes.
- Brasil 2010-2021: exclusion de `Total do produto`, `Demanda final` y `Demanda total` como sectores/componentes.
- Brasil 2000-2009: alineacion por posicion y exclusion de columnas agregadas.
- Uruguay 2016: MIP directa con conciliacion menor por redondeo.
- Uruguay 2017: queda como caso sensible; no se concilio porque los negativos son materiales.
- Mexico 2013 y 2018 (2026-06-10): correccion de origen del encoding. Los CSV de
  INEGI vienen en UTF-8 con BOM y el parser los leia como latin-1, produciendo
  mojibake en las etiquetas ('Mineria' -> 'MinerÃ­a') y dejando el BOM pegado al
  encabezado. Se corrigio `Codigo/src/parsers/mexico_mip.py` (lee utf-8-sig con
  fallback a latin-1) y se regeneraron las matrices, el paquete, la validacion y
  la auditoria. Solo cambiaron etiquetas de texto; ningun valor numerico se altero.
  Verificacion: 0 mojibake en las 35 matrices publicadas y en la auditoria.

No usar como entregable principal cualquier paquete "robusto" que ajuste `Z` de forma general. Ese enfoque solo puede quedar como anexo experimental si el equipo lo aprueba explicitamente.

## 7. Validaciones publicadas

Archivos:

- `validacion_matematica_mip.xlsx`
- `validacion_matematica_mip.md`
- `auditoria_cobertura_sectores_mip.xlsx`
- `auditoria_cobertura_sectores_mip.md`

Pruebas principales:

- `cuadrada_Z_A_L`
- `etiquetas_alineadas`
- `no_negatividad_Z_A_g`
- `max_abs_A_menos_Z_sobre_g`
- `max_abs_Leontief`
- `max_abs_Ghosh`
- `celdas_negativas_Z`
- `sectores_demanda_final_residual_negativa`
- `sectores_va_residual_negativo`
- cobertura de actividades fuente vs sectores MIP final

Resultado clave al corte: todas las matrices pasan validaciones estructurales. Algunas validaciones son diagnosticas y pueden marcar avisos economicos sin invalidar la algebra matricial.

## 8. Como regenerar en el workspace completo

Desde `C:\Users\edwin\Documents\MIP V2`, con `data/raw` y `data/processed` disponibles:

```powershell
py -3 -X utf8 main.py
py -3 -X utf8 scripts\validar_mips.py
py -3 -X utf8 scripts\generar_paquete_matrices.py
py -3 -X utf8 scripts\auditar_cobertura_matrices.py
```

Luego sincronizar al repo publico:

```powershell
# Copiar scripts actualizados a Codigo/scripts/
# Copiar output/matrices_insumo_producto/{Pais}/*.xlsx a MIP/{Pais}/
# Copiar output/matrices_insumo_producto/indice_matrices_insumo_producto.xlsx a indice_matrices.xlsx
# Copiar output/tablas/validacion_matematica_mip.* a la raiz
# Copiar output/tablas/auditoria_cobertura_sectores_mip.* a la raiz
```

Antes de subir:

```powershell
py -3 -m py_compile Codigo\scripts\generar_paquete_matrices.py Codigo\scripts\validar_mips.py Codigo\scripts\auditar_cobertura_matrices.py
git status --short
```

Verificacion minima de Excel:

- Abrir una matriz directa, por ejemplo `MIP/Mexico/MIP_Mexico_2018.xlsx`.
- Abrir una reconstruida, por ejemplo `MIP/Brasil/MIP_Brasil_2001.xlsx`.
- Confirmar que las primeras pestanas sean de trazabilidad.

## 9. Proximos pasos recomendados

1. Uruguay 2017: buscar demanda final fuente completa o MIP directa equivalente. Si no existe, mantener alerta metodologica.
2. Argentina 2005-2017: requiere solicitud directa a INDEC/CEPAL o fuente publica adicional comparable.
3. Brasil 2022+ y Uruguay 2018+: revisar si existen COU/MIP detallados compatibles con el nivel actual.
4. Presentacion: mantenerla sincronizada con validaciones y auditoria de cobertura si cambian resultados.
5. Simulador de choques: PRIMERA VERSION CONSTRUIDA. Ver seccion 11. Pendiente: integrar vectores de empleo/emisiones por sector cuando esten disponibles y conectar con la presentacion del simulador.

## 10. Reglas de colaboracion para no romper trazabilidad

- No reemplazar una matriz publicada sin regenerar validaciones.
- No borrar sectores por diagonal cero.
- No mezclar matrices directas con reconstruidas sin marcar el tipo.
- No presentar ajustes generales de `Z` como cifras oficiales.
- Si se modifica un parser, documentar el cambio en `Codigo/docs/` y regenerar al menos un caso de prueba.
- Si se agrega una fuente externa, guardar URL, fecha de revision, archivo descargado y ruta local.

## 11. Simulador de choques (nuevo, 2026-06-10)

Se construyo la primera version del simulador sobre las matrices ya publicadas.
No reconstruye ni altera matrices: solo las usa como insumo, preservando
trazabilidad.

Archivos:

- `Codigo/src/simulador.py`: motor puro (numpy/pandas).
- `Codigo/scripts/simular_choques.py`: CLI ejecutable.

Dos familias de choque:

- Demanda (modelo de cantidades de Leontief): `Delta_x = L @ Delta_f`.
  Propaga efectos hacia atras (backward linkages) ante un cambio en la
  demanda final.
- Oferta/costos (modelo de precios de Ghosh): `Delta_x' = Delta_v' @ G`.
  Propaga efectos hacia adelante (forward linkages) ante un cambio en
  insumos primarios / valor agregado.

El sector del choque se indica por etiqueta exacta o coincidencia parcial;
el matcher es insensible a mayusculas, acentos y al mojibake de las etiquetas
de origen (no altera las etiquetas, solo facilita el match).

Verificaciones algebraicas pasadas:

- Choque absoluto unitario a la demanda del sector j reproduce exactamente la
  columna j de `L` (error 0).
- Choque de oferta unitario al sector j reproduce exactamente la fila j de `G`
  (error 0).
- El efecto multiplicador de demanda coincide con la suma de columna de `L`.

Ejemplo de uso:

```powershell
py -3 -X utf8 Codigo\scripts\simular_choques.py `
  --mip "MIP\Mexico\MIP_Mexico_2018.xlsx" `
  --pais Mexico --anio 2018 --tipo demanda --modo pct `
  --choque "Edificacion residencial=10" `
  --salida output\simulaciones\demanda_mexico_2018.xlsx
```

Salida: resumen en consola (choque directo, impacto total, multiplicador) y
Excel trazable con hojas `escenario`, `choque_definicion` e `impacto_sector`.

Limitacion actual: el efecto sobre valor agregado solo se estima si la matriz
trae `v_valor_agregado`/valor agregado con datos (las MIP directas tipo Mexico
vienen con VA en 0). Los efectos de empleo y emisiones quedan listos en
`Codigo/src/multiplicadores.py` pero requieren vectores por sector aun no
incorporados.

## 12. Revision de fuentes 2026-06-10

Ver `Codigo/docs/revision_fuentes_2026-06_extension_series.md`. Resumen:

- Repositorio CEPAL COU/MIP cubre COU 1988-2022 y MIP 1979-2022 para la region:
  es la via concreta para extender Brasil hacia 2022 y revisar anios adicionales
  de Uruguay y Argentina.
- No se pudieron descargar archivos en esta sesion (IBGE/BCU rechazaron
  conexion directa). Las acciones quedan documentadas, no ejecutadas.
- Uruguay 2017 sigue con alerta metodologica hasta conseguir demanda final
  fuente completa o MIP directa equivalente.
