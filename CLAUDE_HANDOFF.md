# Handoff para Claude y siguientes colaboradores

Fecha de corte: 2026-06-10

Este documento es la puerta de entrada para continuar el proyecto sin perder trazabilidad. El objetivo es que cualquier colaborador pueda distinguir que esta publicado, que fue reconstruido, que fuentes se usaron, que validaciones ya pasaron y donde quedan riesgos metodologicos.

## 1. Estado actual

Repositorio: `edwinpulgarin/matrices-mip`

Entrega vigente:

- 34 archivos Excel anuales en `MIP/{Pais}/`.
- 6 matrices directas o equivalentes de fuente.
- 28 matrices reconstruidas desde COU.
- Todas las matrices publicadas tienen trazabilidad al inicio del libro:
  - `README`
  - `fuente_resumen`
  - `cobertura_sectores`
  - `cobertura_productos` cuando aplica
  - `fuente_notas`
  - `src_*` cuando la matriz fue reconstruida desde COU
- Validacion estructural: 34/34 OK.
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
| Argentina | 2004, 2018-2021 | Reconstruida desde COU | COU INDEC/CEPAL |
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
5. Simulador de choques: construirlo sobre las matrices publicadas con trazabilidad, usando `A`, `L`, `B`, `G`, `g` y `f`.

## 10. Reglas de colaboracion para no romper trazabilidad

- No reemplazar una matriz publicada sin regenerar validaciones.
- No borrar sectores por diagonal cero.
- No mezclar matrices directas con reconstruidas sin marcar el tipo.
- No presentar ajustes generales de `Z` como cifras oficiales.
- Si se modifica un parser, documentar el cambio en `Codigo/docs/` y regenerar al menos un caso de prueba.
- Si se agrega una fuente externa, guardar URL, fecha de revision, archivo descargado y ruta local.
