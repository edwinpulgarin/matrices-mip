# ---------------------------------------------------------------------------
# Piezas compartidas del arnés de validación contra las MIP oficiales.
#
# La idea del arnés: para cada país donde el instituto publica su propia matriz
# simétrica, reconstruimos la nuestra desde el COU y las comparamos. Si cierran,
# el motor está bien; si no, la diferencia dice exactamente dónde mirar.
#
# Todo en R y leyendo los archivos ya publicados, para que la prueba no comparta
# ni una línea de código con el motor en Python.
# ---------------------------------------------------------------------------

suppressPackageStartupMessages(library(readxl))

# Los libros y las fuentes oficiales
RAIZ <- getwd()
for (.i in 1:4) {
  if (dir.exists(file.path(RAIZ, "matrices"))) break
  RAIZ <- normalizePath(file.path(RAIZ, ".."), mustWork = FALSE)
}
CRUDO <- "c:/Users/edwin/Documents/MIP V2/data/raw"

fmt <- function(x) formatC(round(x), format = "d", big.mark = ".", decimal.mark = ",")

# readxl descarta las filas vacías del principio, así que sus índices no son los
# de Excel. Todo se ubica por contenido.
fila_con <- function(df, col, valor, desde = 1) {
  i <- which(trimws(as.character(df[[col]])) == valor)
  i <- i[i >= desde]
  if (!length(i)) stop(sprintf("no encontré '%s' en la columna %d", valor, col))
  i[1]
}

leer_hoja <- function(ruta, hoja) {
  as.data.frame(read_excel(ruta, sheet = hoja, col_names = FALSE,
                           .name_repair = "minimal"))
}

#' Lee una matriz cuadrada de un libro nuestro (hojas tipo `_matriz`).
#' Encabezado en la fila que arranca con "Código"; datos desde la siguiente.
#' El libro numera sus hojas de forma correlativa según los pasos que la fuente
#' permite, así que el número cambia de país a país. Se busca por el nombre sin
#' el número.
hoja_por_sufijo <- function(libro, sufijo) {
  hojas <- excel_sheets(libro)
  i <- which(sub("^[0-9]+[.] ", "", hojas) == sufijo)
  if (!length(i)) stop(sprintf("no encontré la hoja «%s» en %s", sufijo, basename(libro)))
  hojas[i[1]]
}

#' Las filas se detectan por CONTENIDO, no contando columnas: las hojas del
#' libro no son todas cuadradas —`D` es industria × producto y `U^imp` es
#' producto × industria— y suponer que lo son recorta la matriz en silencio,
#' dejando afuera los últimos productos sin que nada falle.
leer_matriz_libro <- function(libro, sufijo) {
  hoja <- hoja_por_sufijo(libro, sufijo)
  d <- leer_hoja(libro, hoja)
  hr <- fila_con(d, 1, "Código")
  cod <- trimws(as.character(unlist(d[hr, ])))
  cols <- which(!is.na(cod) & cod != "")
  cols <- cols[cols >= 3]
  etq <- trimws(as.character(d[[1]]))
  # después de «Código» puede haber filas de encabezado sin código en la
  # columna A —la de denominaciones de columna—: se saltan hasta el primer
  # código de verdad.
  ini <- hr + 1
  while (ini <= nrow(d) && (is.na(etq[ini]) || etq[ini] == "" || etq[ini] == "NA")) ini <- ini + 1
  fin <- ini
  while (fin + 1 <= nrow(d) && !is.na(etq[fin + 1]) && etq[fin + 1] != "" &&
         !grepl("^(Total|Fuente|Nota|Las )", etq[fin + 1])) fin <- fin + 1
  filas <- ini:fin
  M <- as.matrix(sapply(d[filas, cols], as.numeric))
  dimnames(M) <- list(etq[filas], cod[cols])
  M
}

#' Lee una columna con nombre de la hoja «Vectores y diagonales» del libro.
#' Devuelve un vector con nombres = códigos de industria.
leer_vector_libro <- function(libro, columna = "Producción bruta (g)") {
  d <- leer_hoja(libro, hoja_por_sufijo(libro, "Vectores y diagonales"))
  hr <- fila_con(d, 1, "Código")
  enc <- trimws(as.character(unlist(d[hr, ])))
  cj <- which(enc == columna)
  if (!length(cj)) stop(sprintf("no encontré la columna «%s» en el libro", columna))
  cod <- trimws(as.character(d[[1]]))
  fin <- hr
  while (fin + 1 <= nrow(d) && !is.na(cod[fin + 1]) && cod[fin + 1] != "" &&
         !grepl("^(Total|Fuente)", cod[fin + 1])) fin <- fin + 1
  filas <- (hr + 1):fin
  setNames(as.numeric(unlist(d[filas, cj[1]])), cod[filas])
}

#' Agrega un vector a una partición (mismo mapa que `agregar`).
agregar_vec <- function(v, mapa, grupos) {
  g <- factor(mapa[names(v)], levels = grupos)
  out <- tapply(v, g, sum)
  out[is.na(out)] <- 0
  setNames(as.numeric(out[grupos]), grupos)
}

#' Agrega una matriz a una partición, sumando filas y columnas.
agregar <- function(M, mapa, grupos) {
  gi <- factor(mapa[rownames(M)], levels = grupos)
  gj <- factor(mapa[colnames(M)], levels = grupos)
  out <- rowsum(M, gi, reorder = FALSE)
  out <- t(rowsum(t(out), gj, reorder = FALSE))
  out[grupos, grupos, drop = FALSE]
}

#' Las métricas que se reportan igual para todos los países.
#'
#' Se separan filas y columnas a propósito: en el Modelo D las columnas de Z son
#' invariantes al modelo (las columnas de D suman 1, así que Σᵢ Z[i,j] = Σₚ U[p,j]),
#' de modo que una diferencia en columnas señala un problema de DATOS —valoración,
#' corte por origen, balanceo— y una diferencia sólo en filas señala el reparto
#' producto→industria, es decir la matriz D.
metricas <- function(nos, ofi, etiqueta, objeto = "Z") {
  stopifnot(all(dim(nos) == dim(ofi)))
  dif <- nos - ofi
  tot <- sum(abs(ofi))
  list(
    caso        = etiqueta,
    objeto      = objeto,
    n           = nrow(nos),
    suma_nos    = sum(nos),
    suma_ofi    = sum(ofi),
    dif_suma    = if (sum(ofi) != 0) 100 * (sum(nos) / sum(ofi) - 1) else NA_real_,
    max_col     = max(abs(colSums(nos) - colSums(ofi))),
    max_fila    = max(abs(rowSums(nos) - rowSums(ofi))),
    max_celda   = max(abs(dif)),
    correlacion = suppressWarnings(cor(as.vector(nos), as.vector(ofi))),
    desvio_abs  = if (tot != 0) 100 * sum(abs(dif)) / tot else NA_real_
  )
}

imprimir <- function(m) {
  cat(sprintf("  %-26s %-4s n=%-4d  dif suma %+8.4f %%   máx col %.3e   máx fila %.3e   corr %.4f   desvío %6.2f %%\n",
              m$caso, m$objeto, m$n, m$dif_suma, m$max_col, m$max_fila,
              m$correlacion, m$desvio_abs))
}

fila_md <- function(m) {
  sprintf("| %s | %s | %d | %+.4f %% | %.2e | %.2e | %.4f | %.2f %% |",
          m$caso, m$objeto, m$n, m$dif_suma, m$max_col, m$max_fila,
          m$correlacion, m$desvio_abs)
}

CABECERA_MD <- c(
  "| Caso | Objeto | n | Dif. suma | Máx. dif. columna | Máx. dif. fila | Correlación | Desvío abs. |",
  "|:--|:--|--:|--:|--:|--:|--:|--:|"
)
