# ---------------------------------------------------------------------------
# Arnés de validación: nuestras MIP contra las que publica cada instituto.
#
# La regla del plan: donde el país publica su propia matriz simétrica, partimos
# del COU, la reconstruimos y comparamos. La MIP oficial se usa como PRUEBA DE
# CIERRE del motor, no como fuente.
#
# Uso:  "C:/Program Files/R/R-4.5.1/bin/Rscript.exe" scripts/validacion_R/validar_todo.R
# Sale: reports/validacion_oficiales.md
# ---------------------------------------------------------------------------

AQUI <- "scripts/validacion_R"
if (!file.exists(file.path(AQUI, "_comun.R"))) AQUI <- "."
source(file.path(AQUI, "_comun.R"))
for (f in c("argentina.R", "brasil.R", "colombia.R", "mexico.R",
            "colombia_trabajo_previo.R")) source(file.path(AQUI, f))

cat("Validación contra las MIP oficiales\n")
cat("===================================\n\n")

resultados <- list()
for (pais in list(list("Argentina (INDEC, MIPAr97)", validar_argentina),
                  list("Brasil (IBGE, nível 67)", validar_brasil),
                  list("Colombia (DANE)", validar_colombia),
                  list("México (INEGI)", validar_mexico))) {
  cat(pais[[1]], "\n")
  r <- tryCatch(pais[[2]](), error = function(e) {
    cat("  [ERROR]", conditionMessage(e), "\n"); list()
  })
  resultados <- c(resultados, r)
  cat("\n")
}

# Contraste extra: el trabajo hecho en el DANE años atrás (carpeta
# `Validación_Colombia`). No es otra reconstrucción sino la matriz oficial más
# el análisis, y está armado sobre el Cuadro 7 (Nacional e Importado), así que
# el módulo separa primero el efecto doméstico/total antes de comparar.
cat("Colombia — contraste contra el trabajo previo del DANE\n")
resultados <- c(resultados, tryCatch(validar_colombia_previo(), error = function(e) {
  cat("  [ERROR]", conditionMessage(e), "\n"); list()
}))
cat("\n")

# ── Reporte consolidado ────────────────────────────────────────────────────
md <- c(
  "# Validación contra las MIP oficiales", "",
  "Cada país donde el instituto publica su propia matriz simétrica se usa como",
  "**prueba de cierre**: partimos del COU, reconstruimos la MIP y comparamos.",
  "Todo corre en **R**, leyendo los libros ya publicados y los archivos oficiales,",
  "sin compartir una línea con el motor en Python.", "",
  "## Cómo leer las columnas", "",
  "En el Modelo D las columnas de `Z` son **invariantes al modelo**: como las",
  "columnas de `D` suman 1, se cumple `Σᵢ Z[i,j] = Σₚ U[p,j]`. Por eso:", "",
  "- una diferencia en **columnas** señala un problema de **datos** — valoración,",
  "  corte doméstico/importado o balanceo;",
  "- una diferencia sólo en **filas** señala el reparto producto→industria, es",
  "  decir la matriz **D**, que depende del nivel de detalle de productos.", "",
  "## Resultados", "",
  CABECERA_MD,
  vapply(resultados, fila_md, character(1)),
  "",
  "## Qué dice cada bloque", "",
  "**Brasil es la prueba del motor.** El IBGE publica la matriz `D`, la `A` y la",
  "Leontief, no sólo el resultado. Las tres reproducen las oficiales con",
  "correlación 1,0000 y desvío por debajo del 0,03 %, que es el redondeo de la",
  "propia publicación. Queda probado que `D = V·diag(q)⁻¹`, `A = Z·diag(g)⁻¹` y",
  "`L = (I−A)⁻¹` están bien calculadas: si hubiera un error de método, aparecería",
  "acá y no aparece.", "",
  "**México mide el nivel de detalle, no el método.** Las columnas cierran exacto",
  "—o sea que el dato, la valoración y el balanceo coinciden con el instituto— y",
  "la diferencia queda toda en las filas, que es donde actúa `D`.", "",
  "**Colombia mide el precio del §8.33, y es el hallazgo de este contraste.** La",
  "matriz que se publica es la doméstica, así que el homólogo es el **Cuadro 5",
  "(Nacional)** del DANE. Contra él, nuestra `Z` sale **+3,8 % en 2019 y +4,5 % en",
  "2021**, y el espejo lo dice todo: el insumo importado nos da **98.304 donde el",
  "DANE mide 125.530** (−21,7 %). El COU no publica el corte por celda y el",
  "prorrateo proporcional se lo reparte a todas las industrias por igual, así que",
  "deja en la matriz doméstica insumo que en realidad se importó. El",
  "multiplicador medio queda **+3,26 % (2019)** y **+3,61 % (2021)** por encima",
  "del DANE.", "",
  "**Y la contraprueba, en el mismo cuadro:** la versión total —donde las dos",
  "partes se vuelven a sumar y el §8.33 no interviene; el libro ya no la entrega,",
  "se rearma con `Z + D·U^imp`— da **−0,01 % en 2019 y +0,08 % en 2021** contra",
  "el Cuadro 8. O sea",
  "que el método y el dato están bien y toda la brecha de la doméstica es el",
  "supuesto de origen. Es la cuarta medición del §8.33 del proyecto, después de",
  "México (+5,65 %), Brasil (+1,3/+1,6 %) y Uruguay (−15,8 % de insumo importado).",
  "Ver `sesgo_prorrateo.md`.", "",
  "**Lo que queda no se puede cerrar, y conviene decirlo.** El DANE publica su MIP",
  "a 68 actividades y el COU trae 61. Del Anexo 2 salen 53 actividades 1:1, tres",
  "casos donde la MIP agrupa varias del COU —agregar es trivial— y **ocho donde una",
  "actividad del COU se PARTE en varias de la MIP** (`018 + 021` → `018` y",
  "`021-022`; `K` → `085-086`, `087`, `088`; y seis más). Desagregar exige los",
  "microdatos de establecimiento, que no se publican. Mientras el COU salga a 61",
  "actividades, reproducir la matriz de 68 al último dígito es imposible por",
  "construcción, no por método.", "",
  "## Contraste contra el trabajo previo hecho en el DANE", "",
  "La carpeta `Validación_Colombia` guarda las matrices de Leontief, Ghosh y los",
  "encadenamientos calculados en R años atrás, para 2017, 2019 y 2021. **No es una",
  "reconstrucción alternativa**: ese script lee la MIP que el DANE ya publica y",
  "corre el análisis sobre ella. Sirve igual como prueba de cierre, pero hay que",
  "resolver una diferencia de definición antes de comparar cualquier número.", "",
"Esa `L` es además **idéntica al Cuadro 8** que el DANE publica —el propio",
  "instituto ya trae la inversa de Leontief calculada—, cosa que se verificó:",
  "`Cuadro 8` vs `L(Cuadro 7)` da máx dif **5,0e-08**, que es el redondeo de la",
  "publicación. O sea que su `L`, el Cuadro 8 y la Leontief del Cuadro 7 son el",
  "mismo objeto.", "",
  "Y ese objeto es el **total**: el Cuadro 7 es «Nacional e Importado» y trata los",
  "insumos importados como **endógenos**. Nuestras matrices son domésticas y dejan",
  "la importación como fila primaria exógena, que es el **Cuadro 5**. La `L` del",
  "Cuadro 7 es por construcción mayor, y esa brecha no es error de nadie.", "",
  "El origen no se dio por supuesto: invirtiendo su `L` se recupera `A = I − L⁻¹`,",
  "y como `A = Z·diag(x)⁻¹`, los cocientes `Z[i,j]/A[i,j]` tienen que ser",
  "constantes por columna para el `Z` correcto. Sólo el Cuadro 7 lo cumple",
  "(dispersión 7e-14 en 2019, 9e-14 en 2021); los otros siete quedan en 1e-1 o peor.", "",
  "### El total coincide; el corte por origen, no", "",
  "| | Nuestro 2019 | DANE 2019 | Nuestro 2021 | DANE 2021 | |",
  "|:--|--:|--:|--:|--:|:--|",
  "| `Z` doméstico | 757.403 | 729.403 | 886.543 | 848.168 | Cuadro 5 |",
  "| `Z` importado | 98.304 | 125.530 | 127.128 | 164.204 | Cuadro 7 − Cuadro 5 |",
  "| `Z` total | 855.707 | 854.933 | 1.013.671 | 1.012.372 | Cuadro 7 |",
  "| Producción bruta | 1.857.445 | 1.857.445 | 2.140.060 | 2.140.060 | columna «Total» |",
  "",
  "**El consumo intermedio total coincide al 0,09 %, y la producción bruta al peso.**",
  "Lo que se separa es el reparto entre doméstico e importado: el COU no publica ese",
  "corte por celda, así que el prorrateo (§8.33) le aplica a cada industria la",
  "proporción importada del producto, y eso deja **27.226 de más** en la matriz",
  "doméstica de 2019. Es el mismo fenómeno medido en México, Brasil y Uruguay.", "",
  "### Las dos Leontief, cada una contra su homólogo", "",
  "| Contraste | 2019 | 2021 |",
  "|:--|--:|--:|",
  "| Su `L` vs `L` recalculada del Cuadro 7 | máx dif **4,4e-16** | máx dif **4,4e-16** |",
  "| Multiplicador medio, Cuadro 7 (total) | 1,9937 | 2,0593 |",
  "| Multiplicador medio, Cuadro 5 (doméstico) | 1,6882 | 1,6983 |",
  "| **La definición sola explica** | **+18,1 %** | **+21,3 %** |",
  "| **Nuestra `L` doméstica (publicada) vs Cuadro 5** | 1,7596 vs 1,7040 (**+3,26 %**) | 1,7771 vs 1,7152 (**+3,61 %**) |",
  "| **Nuestra `L` total (hoja del libro) vs Cuadro 8** | 2,0185 vs 2,0187 (**−0,01 %**) | 2,0790 vs 2,0773 (**+0,08 %**) |",
  "",
  "Las dos últimas filas son el mismo motor sobre el mismo COU, leídas con las dos",
  "definiciones. La total, donde el §8.33 no interviene, cae a la milésima; la",
  "doméstica se aparta 3,3-3,6 %, y esa distancia **es** el supuesto de origen.", "",
  "**Lectura.** Reproducimos su cálculo al último dígito de la doble precisión, así",
  "que su pipeline queda confirmado y también nuestra lectura de sus archivos. El",
  "método y el dato están verificados —el contraste total da −0,01 %—, y lo que",
  "queda por resolver en la matriz doméstica de Colombia no es cálculo sino un dato",
  "que el COU no trae: qué parte de cada celda se importó. Quien necesite la cifra",
  "exacta del corte por origen tiene que ir a la MUPNI, que lo mide pero sólo llega",
  "a 2020 y a 66 divisiones CPC.", "",
  "El aviso práctico para quien compare: si se toman los multiplicadores de ese",
  "trabajo o del Cuadro 8 (≈2,0) contra los nuestros (≈1,76) se ve una brecha del",
  "15 % que es **casi toda de definición**, no de método — total contra doméstico.",
  "Comparados como el mismo objeto, la diferencia es 0,01 %.", "",
  "## Pendientes", "",
  "| Caso | Qué falta |",
  "|:--|:--|",
  "| Colombia 2017 | bajar el anexo del DANE de ese año: tenemos su `L` del trabajo previo y nuestro libro, pero sin el Cuadro 5 no se puede separar doméstico de total |",
  "| Colombia 2015 | bajar el anexo del DANE; no está en el patrón de URL de 2019 y 2021 |",
  "| Colombia 2021 | la MUPNI publicada llega a 2020, así que no hay libro de ese año |",
  "| México 2008 y 2018 | INEGI no publica el COU de utilización de esos años |",
  "| Uruguay 2016 | el BCU publica producto×producto (128×128, Modelo B); industria×industria sólo a 11 sectores |",
  "",
  ""
)
ruta <- file.path(RAIZ, "reports", "validacion_oficiales.md")
writeLines(md, ruta)

# Además del reporte legible, un CSV para que el status consolidado no tenga que
# parsear markdown.
if (length(resultados)) {
  tab <- do.call(rbind, lapply(resultados, function(m)
    data.frame(caso = m$caso, objeto = m$objeto, n = m$n,
               suma_nuestra = m$suma_nos, suma_oficial = m$suma_ofi,
               dif_suma_pct = m$dif_suma, max_dif_columna = m$max_col,
               max_dif_fila = m$max_fila, correlacion = m$correlacion,
               desvio_abs_pct = m$desvio_abs, stringsAsFactors = FALSE)))
  write.csv(tab, file.path(RAIZ, "reports", "validacion_oficiales.csv"),
            row.names = FALSE, fileEncoding = "UTF-8")
}
cat(sprintf("[OK] %d comparaciones. Reporte en %s\n", length(resultados), basename(ruta)))
