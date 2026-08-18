# ---------------------------------------------------------------------------
# Argentina — contra la matriz simétrica de la MIPAr97 del INDEC (cuadro 12).
#
# Es el único año de Argentina contrastable: el INDEC publica el COU completo de
# 1997 (cuadros 1 a 4) y su propia matriz simétrica (cuadro 12), todo en la
# misma clasificación de 124 ramas. No hace falta puente.
#
# La metodología del INDEC (sección 12) describe el Modelo D: «la traspuesta de
# la matriz de oferta a precios básicos transformada en estructura expresada en
# tanto por uno —matriz de cuota de mercado— por la matriz 3 de utilización a
# precios básicos».
# ---------------------------------------------------------------------------

validar_argentina <- function() {
  libro <- file.path(RAIZ, "matrices", "Argentina", "MIP_Argentina_1997_LIBRO.xlsx")
  ofi <- file.path(CRUDO, "argentina_mip97", "mip_matriz12.xls")
  if (!file.exists(libro) || !file.exists(ofi)) {
    cat("  [omitido] Argentina 1997: falta el libro o el cuadro 12
")
    return(list())
  }
  d <- leer_hoja(ofi, 1)
  # las columnas de actividad son la secuencia 1..124 de la fila 6 (1-based en
  # readxl, que descarta filas vacías del principio)
  fila_num <- which(vapply(seq_len(nrow(d)),
                           function(r) identical(trimws(as.character(d[r, 3])), "1"),
                           logical(1)))[1]
  cols <- 3:(2 + 124)
  r0 <- fila_con(d, 1, "1", desde = fila_num + 1)
  filas <- r0:(r0 + 123)
  # el INDEC identifica las ramas por número de orden (columna A), no por código
  orden <- as.character(as.integer(as.numeric(d[filas, 1])))
  Z_ofi <- as.matrix(sapply(d[filas, cols], as.numeric))
  dimnames(Z_ofi) <- list(orden, orden)

  # El cuadro 12 está en MILES de pesos y el libro se presenta en MILLONES
  # (escala = 1000). Sin este factor la comparación da −99,9 %.
  Z_ofi <- Z_ofi / 1000

  # El cuadro 12 del INDEC es la matriz NACIONAL: su suma, 167.856.141, es
  # exactamente la del cuadro 3 (utilización a precios básicos de producción
  # nacional). Ojo con la convención, que cambia de país a país: el Cuadro 7 del
  # DANE es la total y éste no. Nuestro libro publica la DOMÉSTICA —el insumo
  # importado va en fila primaria—, que es el mismo objeto, así que la hoja «Z
  # consumos intermedios» se compara directo. (El libro no entrega la total; si
  # hiciera falta se rearma con Z + D·U^imp, como en colombia_trabajo_previo.R.)
  Z_nos <- leer_matriz_libro(libro, "Z consumos intermedios")
  fi <- intersect(rownames(Z_nos), rownames(Z_ofi))
  if (length(fi) != nrow(Z_ofi))
    cat(sprintf("  [aviso] Argentina 1997: coinciden %d de %d ramas
", length(fi), nrow(Z_ofi)))
  if (!length(fi)) return(list())
  m <- metricas(Z_nos[fi, fi, drop = FALSE], Z_ofi[fi, fi, drop = FALSE],
                "Argentina 1997", "Z")
  imprimir(m)
  list(m)
}
