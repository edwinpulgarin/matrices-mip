# Checklist de descarga: COU para las MIP directas

Fecha: 2026-06-10 (actualizado 2026-06-11)

Objetivo: que las 6 MIP directas lleven su COU adjunto como referencia. Estado:

| Caso | Estado COU | Que falta |
|---|---|---|
| **Mexico 2013** | ✅ HECHO | COU matricial INEGI/CEPAL adjunto y verificado (rama SCIAN 262). |
| **Mexico 2008** | ✅ HECHO | COU INEGI 2008 (Tabulados_cou2008) adjunto; U_dom reconcilia con Z (ratio 1.0000). |
| **Uruguay 2016** | ✅ HECHO | COU BCU 2016 detallado adjunto (95 ind x 110 prod), como referencia oficial. |
| Mexico 2018 | ✅ Documentado | El release de la MIP 2018 de INEGI (tabulados_MIP.zip y datos abiertos mip_csv.zip, revisados 2026-06-11) trae solo la MIP simetrica y sus componentes, NO el COU. No hay COU 2018 separado disponible. Queda con fuente al inicio. |
| Mexico 2003 | ✅ Documentado | La MIP 2003 es de 20 sectores (marco viejo); no hay COU producto x rama compatible. Se mantiene con fuente al inicio. |
| Argentina 1997 | ✅ Documentado | No existe COU publico (CEPAL arranca 2004). Fuente al inicio. |

Estado: **31/34 matrices con COU adjunto** (28 reconstruidas + Mexico 2008/2013 + Uruguay 2016). Las 3 restantes (Mexico 2003, Mexico 2018, Argentina 1997) NO tienen COU publico disponible y llevan su fuente claramente explicada al inicio (README + fuente_resumen + metodologia + fuente_notas con el detalle del caso). Esto cumple la regla del equipo: cada MIP lleva su COU o su fuente al inicio.

Flujo acordado: **tu descargas, yo integro**. Deja cada archivo en la ruta
indicada (crea las subcarpetas si no existen) y avisame; yo escribo el parser,
construyo `couref_{serie}_{anio}.xlsx`, regenero, valido y audito.

Necesito el DETALLE matricial (producto x actividad), no cuentas agregadas.

---

## 1. Mexico 2003, 2008, 2018

Que necesito: el Cuadro de Oferta y Utilizacion (COU) detallado de INEGI con la
tabla de **OFERTA** (produccion por producto x actividad) y la de
**UTILIZACION/DEMANDA** (consumo intermedio por producto x actividad), con
separacion domestico/importado si esta disponible. Es exactamente el formato
que ya funciono para 2013 (hoja `Tabulado`, nivel rama SCIAN).

Fuentes (desde tu maquina/red):
- INEGI MIP por anio (incluye COU del mismo marco):
  - 2003: `https://www.inegi.org.mx/programas/mip/2003/`
  - 2008: `https://www.inegi.org.mx/programas/mip/2008/`
  - 2018: `https://www.inegi.org.mx/programas/mip/2018/`
- INEGI Cuenta de Bienes y Servicios / COU: `https://www.inegi.org.mx/temas/cn/`
- Repositorio CEPAL COU/MIP: `https://statistics.cepal.org/repository/cou-mip/index.html?lang=es`
  (para 2018, el archivo de CEPAL llega truncado; bajar de INEGI directo).

Donde dejarlo:
```
data/raw/mexico/cou_matricial/COU_Mexico_2003_oferta.xlsx
data/raw/mexico/cou_matricial/COU_Mexico_2003_utilizacion.xlsx
data/raw/mexico/cou_matricial/COU_Mexico_2008_oferta.xlsx
data/raw/mexico/cou_matricial/COU_Mexico_2008_utilizacion.xlsx
data/raw/mexico/cou_matricial/COU_Mexico_2018_oferta.xlsx
data/raw/mexico/cou_matricial/COU_Mexico_2018_utilizacion.xlsx
```
Si la utilizacion viene separada domestico/importado, nombrala
`..._utilizacion_domestico.xlsx` y `..._utilizacion_importado.xlsx`.

---

## 2. Uruguay 2016 (falta la utilizacion)

Que necesito: la tabla de **UTILIZACION** (uso) del COU 2016. La oferta ya la
tenemos (`data/raw/uruguay/cou_2016/URY_2016_Produccion_pb_C.xlsx`).

Fuentes:
- BCU, COU: `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/COU.aspx`
- Repositorio CEPAL COU/MIP (Uruguay 2016).

Donde dejarlo (junto a la oferta que ya esta):
```
data/raw/uruguay/cou_2016/URY_2016_Utilizacion_pb_C.xlsx
```
Si consigues tambien valor agregado e importaciones del COU 2016, agregalos con
nombres analogos (`..._ValorAgregado_...`, `..._Importaciones_...`).

Bonus ya disponible: el COU detallado de Uruguay 2017 esta completo en
`data/raw/_cepal_staging/URY_COU_2017/` (utilizacion nacional/importada,
produccion, oferta) y puede usarse para revisar la alerta de demanda final
negativa de Uruguay 2017.

---

## 3. Argentina 1997

Sin descarga: no existe COU publico separado para 1997 (los COU de Argentina en
CEPAL arrancan en 2004). Queda documentado en el README/fuente_notas de la MIP
de Argentina 1997.

---

## Verificacion minima que hare por archivo

- Que la oferta sea una matriz (filas = productos, columnas = actividades), con
  mas de una columna de actividad.
- Que la utilizacion exista con la misma estructura producto x actividad.
- Que los totales de produccion por actividad cuadren con la `x` (produccion
  bruta) de la MIP directa del mismo anio: confirma que es el mismo marco.
  (En 2013 esta verificacion dio exacta: uso intermedio domestico del COU =
  total de Z de la MIP, correlacion 1.0.)
