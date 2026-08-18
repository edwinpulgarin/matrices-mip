# Cobertura de la fuente — ¿leemos toda la utilización que se publica?

Para cada producto, la oferta que la fuente declara a precios de comprador tiene que ser igual a la utilización que leímos:

```
OPC_p  ==  Σ_j U_pc[p,j] + Σ_c Y_pc[p,c]
```

Es la identidad contable del propio COU, así que no supone nada. Si no cierra, o leímos de menos o la fuente no cuadra.

**Por qué existe este control.** Los parsers eligen columnas por palabras clave. Si la fuente agrega una columna que ningún patrón reclama, se descarta sin error y el producto queda con oferta pero sin uso; el balanceo (Cap. 11) cierra esa fila igual y el resultado se ve normal. Pasó: el INDEC abre desde 2018 una columna de demanda final «Trabajos en curso» —los cultivos en pie— que el parser de Argentina no leía. En tabaco sin elaborar 2023 era el 33 % de la oferta del producto.

**Neto vs bruto.** Una columna perdida falta siempre en el mismo sentido, así que se ve en el **neto**. El bruto además recoge reasignaciones de la fuente entre productos vecinos, que vienen en pares que se cancelan y no son un error de lectura. El disparador es el neto, con tolerancia 1e-04.

¹ Colombia ya publica a precios básicos y sin puente de valoración, así que no hay OPC contra qué contrastar. El control equivalente es el **balance de producto antes del balanceo**: si leyéramos de menos, la oferta no igualaría al uso y el desvío aparecería igual.

| País | Año | Productos | Neto | Bruto | Estado |
|:---|---:|---:|---:|---:|:---:|
| Argentina | 2004 | 271 | -1.22e-09 | 6.37e-08 | ✅ |
| Argentina | 2018 | 223 | 5.13e-12 | 1.96e-09 | ✅ |
| Argentina | 2019 | 224 | -1.17e-11 | 1.44e-09 | ✅ |
| Argentina | 2020 | 223 | -8.11e-12 | 1.15e-09 | ✅ |
| Argentina | 2021 | 222 | -1.22e-11 | 6.95e-11 | ✅ |
| Argentina | 2022 | 222 | 3.05e-11 | 3.11e-10 | ✅ |
| Argentina | 2023 | 222 | -9.76e-09 | 1.42e-07 | ✅ |
| Brasil | 2010 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2011 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2012 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2013 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2014 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2015 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2016 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2017 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2018 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2019 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2020 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Brasil | 2021 | 128 | 0.00e+00 | 0.00e+00 | ✅ |
| Uruguay | 2012 | 134 | 5.59e-09 | 8.55e-08 | ✅ |
| Uruguay | 2016 | 110 | 6.96e-06 | 4.15e-04 | ✅ |
| Uruguay | 2017 | 110 | 6.75e-06 | 6.75e-06 | ✅ |
| México | 2013 | 262 | -2.59e-18 | 1.35e-16 | ✅ |
| Colombia | 2014 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2015 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2016 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2017 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2018 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2019 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2020 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2021 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2022 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2023 | 66 | 0.00e+00 | 0.00e+00 | ✅ |
| Colombia | 2024 | 66 | 0.00e+00 | 0.00e+00 | ✅ |

## Desvíos declarados (revisados: no son error de lectura)

- **Colombia 2020** — La MUPNI 2020 es **provisional** (`DANE_MUPNI_2020p.xlsx`) y no cierra contra el COU: la producción supera al uso doméstico en 9.173 (1,1 % de la oferta). Verificado que NO es lectura: 2020 tiene exactamente las mismas cuatro columnas de demanda final que 2014-2019, que cierran a cero. El desvío está en la fuente y lo absorbe el balanceo; conviene rehacer el año cuando el DANE publique la versión definitiva. En la versión a 392 productos se ve amplificado, porque el cierre intra-grupo sólo puede correr donde los márgenes del grupo son consistentes, y en 2020 no lo son.

**Sin hallazgos.** El peor faltante neto de todo el conjunto es 6.96e-06 de la oferta, contra una tolerancia de 1e-04: tres órdenes de magnitud de margen. Ninguna fuente tiene columnas con datos sin leer.

## Qué NO cubre este control

Verifica que leímos todo lo publicado, no que lo publicado sea correcto ni que lo hayamos clasificado bien. Una columna leída pero mapeada a la categoría equivocada de demanda final pasa este control sin problema: eso lo cubre la hoja «COU Demanda final» de cada libro, que conserva los nombres nativos de la fuente al lado del esquema armonizado.
