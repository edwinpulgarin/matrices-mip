# ---------------------------------------------------------------------------
# México — contra la Matriz de Insumo-Producto simétrica del INEGI.
#
# INEGI publica MIP para 2008, 2013 y 2018, pero el COU completo (con la
# utilización, no sólo la oferta) sólo existe para 2013. Así que el contraste
# posible es ese año: nuestra reconstrucción desde el COU contra la matriz
# publicada, ambas al mismo nivel de rama SCIAN y sin ningún prorrateo.
#
# Es el único caso del arnés donde las dos matrices tienen exactamente la misma
# clasificación: no hace falta puente ni agregación, se comparan celda a celda.
# ---------------------------------------------------------------------------

validar_mexico <- function() {
  res <- list()
  for (anio in c(2008, 2013, 2018)) {
    libro <- file.path(RAIZ, "matrices", "Mexico", sprintf("MIP_Mexico_%d_LIBRO.xlsx", anio))
    ofi <- file.path(RAIZ, "matrices", "Mexico", sprintf("MIP_Mexico_%d_LIBRO_OFICIAL.xlsx", anio))
    if (!file.exists(libro)) {
      cat(sprintf("  [omitido] México %d: INEGI no publica el COU de utilización de ese año\n", anio))
      next
    }
    if (!file.exists(ofi)) { cat(sprintf("  [omitido] México %d: falta la matriz oficial\n", anio)); next }

    Z_nos <- leer_matriz_libro(libro, "Z consumos intermedios")
    Z_ofi <- leer_matriz_libro(ofi, "Z consumos intermedios")

    # La reconstrucción indexa las filas por el código de rama y la oficial
    # también, pero conviene cruzarlas explícitamente y no por posición.
    fi <- intersect(rownames(Z_nos), rownames(Z_ofi))
    co <- intersect(colnames(Z_nos), colnames(Z_ofi))
    if (length(fi) < nrow(Z_ofi))
      cat(sprintf("  [aviso] México %d: coinciden %d de %d ramas\n", anio, length(fi), nrow(Z_ofi)))
    if (!length(fi)) next
    m <- metricas(Z_nos[fi, co, drop = FALSE], Z_ofi[fi, co, drop = FALSE],
                  sprintf("México %d", anio), "Z")
    imprimir(m); res[[length(res) + 1]] <- m
  }
  res
}
