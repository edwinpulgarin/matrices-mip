# ---------------------------------------------------------------------------
# Colombia — contra la Matriz insumo producto del DANE (Cuadro 5, Nacional), que
# es la que corresponde: la matriz que publicamos es la DOMÉSTICA, con el insumo
# importado en fila primaria. El Cuadro 7 (Nacional e Importado) es el homólogo
# de la versión total, que el libro ya no entrega y que se rearma con
# Z + D·U^imp (ver colombia_trabajo_previo.R), no de su matriz principal.
#
# El DANE publica a 68 actividades y el COU está a 61, y las clasificaciones
# están cruzadas. El puente NO lo armamos nosotros: sale de la «Tabla correlativa
# de actividades económicas», anexo 2 de la metodología DSO-MIP-MET-001.
# ---------------------------------------------------------------------------

ANEXO_CORRELATIVA <- file.path(
  CRUDO, "colombia",
  "DANE_MIP_DSO-MIP-MET-001-anexo2-nomenclatura-actividades-economicas.xlsx")

#' Z doméstica del Cuadro 5 (Nacional), 68 x 68.
leer_dane <- function(ruta, cuadro = "Cuadro 5") {
  d <- leer_hoja(ruta, cuadro)
  r0 <- fila_con(d, 1, "A0101")
  hdr <- fila_con(d, 3, "A0101")
  cod <- trimws(as.character(d[, 1]))
  fin <- r0
  while (fin + 1 <= nrow(d) && !is.na(cod[fin + 1]) && cod[fin + 1] != "" &&
         !grepl("^(Fuente|Actualizado)", cod[fin + 1])) fin <- fin + 1
  cod <- cod[r0:fin]
  cols <- 3:(2 + length(cod))
  stopifnot(identical(trimws(as.character(unlist(d[hdr, cols]))), cod))
  M <- as.matrix(sapply(d[r0:fin, cols], as.numeric))
  dimnames(M) <- list(cod, cod)
  M
}

#' Partición común entre las 61 del COU y las 68 de la MIP, desde la tabla
#' correlativa oficial. Las celdas combinadas llegan como NA y se arrastran.
puente_dane <- function(codigos_matriz) {
  tc <- leer_hoja(ANEXO_CORRELATIVA, "Anexo 2")
  r0 <- fila_con(tc, 1, "A0101-01")
  arrastrar <- function(v) {
    v <- trimws(as.character(v)); v[v == "" | v == "NA"] <- NA
    for (i in seq_along(v)) if (is.na(v[i]) && i > 1) v[i] <- v[i - 1]
    v
  }
  p <- data.frame(cou = arrastrar(tc[r0:nrow(tc), 1]),
                  dane = arrastrar(tc[r0:nrow(tc), 3]), stringsAsFactors = FALSE)
  p <- p[!is.na(p$cou) & !is.na(p$dane), ]
  # el COU rotula el grupo con su primer componente ('018 + 021' -> '018')
  p$cou <- sub(" \\+.*$", "", p$cou)
  # el DANE no rotula igual en los dos archivos: la correlativa dice '041 - 042'
  # donde el Cuadro 7 dice '041'. Se resuelve contra lo que la matriz trae.
  p$dane <- vapply(p$dane, function(x) {
    y <- gsub("\\s+", "", x)
    if (y %in% codigos_matriz) return(y)
    z <- sub("[-+].*$", "", y)
    if (z %in% codigos_matriz) return(z)
    stop("código de la MIP sin correspondencia en el cuadro leído: ", x)
  }, character(1))

  padre <- new.env(hash = TRUE, parent = emptyenv())
  raiz <- function(x) { while (!identical(get(x, envir = padre), x)) x <- get(x, envir = padre); x }
  for (x in unique(c(paste0("C|", p$cou), paste0("D|", p$dane)))) assign(x, x, envir = padre)
  for (i in seq_len(nrow(p))) {
    a <- raiz(paste0("C|", p$cou[i])); b <- raiz(paste0("D|", p$dane[i]))
    if (!identical(a, b)) assign(a, b, envir = padre)
  }
  etiqueta <- function(pref, cod) {
    r <- raiz(paste0(pref, "|", cod))
    paste(unique(sort(p$cou[vapply(p$cou, function(z) identical(raiz(paste0("C|", z)), r), logical(1))])),
          collapse = "+")
  }
  list(cou  = setNames(vapply(unique(p$cou), function(c) etiqueta("C", c), character(1)), unique(p$cou)),
       dane = setNames(vapply(unique(p$dane), function(c) etiqueta("D", c), character(1)), unique(p$dane)))
}

validar_colombia <- function() {
  res <- list()
  for (anio in c(2015, 2017, 2019, 2021)) {
    libro <- file.path(RAIZ, "matrices", "Colombia", sprintf("MIP_Colombia_%d_LIBRO.xlsx", anio))
    ofi <- file.path(CRUDO, "colombia", sprintf("DANE_MIP_%d.xlsx", anio))
    if (!file.exists(libro) || !file.exists(ofi)) {
      cat(sprintf("  [omitido] Colombia %d: %s\n", anio,
                  if (!file.exists(libro)) "no tenemos libro de ese año (la MUPNI llega a 2020)"
                  else "no está descargada la MIP oficial"))
      next
    }
    Z_ofi <- leer_dane(ofi)
    Z_nos <- leer_matriz_libro(libro, "Z consumos intermedios")
    p <- puente_dane(rownames(Z_ofi))
    faltan <- c(setdiff(rownames(Z_ofi), names(p$dane)), setdiff(rownames(Z_nos), names(p$cou)))
    if (length(faltan)) { cat("  [aviso] códigos sin puente:", paste(faltan, collapse = ", "), "\n"); next }
    grupos <- sort(unique(c(p$cou, p$dane)))
    m <- metricas(agregar(Z_nos, p$cou, grupos), agregar(Z_ofi, p$dane, grupos),
                  sprintf("Colombia %d", anio), "Z")
    imprimir(m); res[[length(res) + 1]] <- m
  }
  res
}
