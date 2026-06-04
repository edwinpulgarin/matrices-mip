# Ajustes de cierre y revision de Uruguay 2017

**Fecha:** 4 de junio de 2026  
**Alcance:** Brasil 2000-2009, Uruguay 2016 y Uruguay 2017.

## 1. Decision aplicada

Se aplico conciliacion de cierre menor en:

- Brasil 2001-2006, sector `Tintas vernizes esmaltes e lacas`.
- Uruguay 2016, sector `P10---Cosechas de azucar`.

No se aplico ajuste a Uruguay 2017 porque los negativos son materiales:

- `A.4 — Trigo`: -633.4, equivalente a -16.5% de la produccion sectorial.
- `H.1 — Servicio de transporte de carga`: -25,062.2, equivalente a -45.9% de la produccion sectorial.

## 2. Metodo de conciliacion menor

La conciliacion no elimina cifras sin trazabilidad. El procedimiento:

1. Identifica sectores con demanda final negativa pequena.
2. Fija la produccion bruta `g`.
3. Conserva los totales de columna de `Z`, para no mover el valor agregado residual.
4. Lleva la demanda final negativa a cero.
5. Redistribuye ese cierre sobre sectores con demanda final positiva.
6. Ajusta `Z` mediante RAS para cumplir:

```text
sum_row(Z_ajustada) + f_ajustada = g
sum_col(Z_ajustada) = sum_col(Z_original)
```

7. Recalcula:

```text
A = Z * diag(g)^-1
L = (I - A)^-1
```

Cada matriz ajustada conserva las hojas:

- `ajuste_cierre`: detalle del ajuste por sector.
- `Z_pre_conciliacion`: matriz previa al cierre menor.

## 3. Resultado despues de regenerar

Se regenero:

```powershell
py -3 -X utf8 main.py
py -3 -X utf8 scripts\validar_mips.py
py -3 -X utf8 scripts\generar_paquete_matrices.py
```

Resultado de demanda final negativa:

| Serie | Negativos despues |
|---|---:|
| Brasil 2000-2009 | 0 |
| Brasil 2010-2021 | 0 |
| Argentina reconstruida | 0 |
| Uruguay 2016 | 0 |
| Uruguay 2017 | 2 |

Archivos con conciliacion trazada:

- `output/matrices_insumo_producto/Brasil/MIP_Brasil_2001.xlsx`
- `output/matrices_insumo_producto/Brasil/MIP_Brasil_2002.xlsx`
- `output/matrices_insumo_producto/Brasil/MIP_Brasil_2003.xlsx`
- `output/matrices_insumo_producto/Brasil/MIP_Brasil_2004.xlsx`
- `output/matrices_insumo_producto/Brasil/MIP_Brasil_2005.xlsx`
- `output/matrices_insumo_producto/Brasil/MIP_Brasil_2006.xlsx`
- `output/matrices_insumo_producto/Uruguay/MIP_Uruguay_2016.xlsx`

## 4. Uruguay 2017: fuentes revisadas

Fuentes oficiales revisadas:

- Pagina BCU de MIP: publica MIP 2016, incluyendo versiones industria x industria y producto x producto para 2016. No se identifica una MIP directa 2017.
  - https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Matriz-Insumo-Producto.aspx
- Pagina BCU de COU: publica `Cuadro de Oferta y Utilizacion 2016 - 2017 (version detallada)` y `Cuadro de Oferta y Utilizacion 2016 - 2021 (version agregada)`.
  - https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/COU.aspx
- Metodologia COU BCU: confirma que el COU incluye produccion a precios basicos, oferta importada, margenes, impuestos, utilizacion intermedia y utilizaciones finales a precios comprador.
  - https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Metodologa%20%20Actualizacin%202020/Cuadro%20de%20Oferta%20y%20Utilizacion%20Metodologia.pdf

Lectura:

- Para 2016 si hay MIP oficial directa BCU.
- Para 2017 tenemos COU detallado, no MIP directa equivalente.
- La solucion responsable para 2017 es mejorar la reconstruccion desde COU incorporando utilizacion final fuente si se logra descargar/extraer, o mantenerlo como caso pendiente con alerta.

## 5. Recomendacion para el equipo

Respuesta sugerida:

> Brasil 2000-2009 y Uruguay 2016 tenian cierres negativos pequenos y puntuales. Los conciliamos con una regla trazable: se conserva produccion, se mantienen totales de columna de la MIP y se redistribuye el cierre via RAS, dejando una hoja de ajuste y la matriz previa. Uruguay 2017 no se ajusto porque los negativos son materiales; estamos revisando fuente COU/BCU para incorporar demanda final completa o, si no existe MIP directa 2017, dejarlo como limitacion metodologica.

## 6. Pendiente tecnico para Uruguay 2017

Proxima ruta:

1. Descargar o recuperar desde BCU el COU 2016-2017 detallado completo.
2. Verificar si existen archivos separados de utilizacion final:
   - GCF hogares e ISFLSH;
   - GCF gobierno;
   - formacion bruta de capital;
   - exportaciones.
3. Reconstruir `Y` fuente 2017 en vez de usar residual.
4. Convertir `U` e `Y` a una base compatible con `V`.
5. Solo si persiste un negativo menor, aplicar una conciliacion documentada; si persiste un negativo material, mantener alerta.
