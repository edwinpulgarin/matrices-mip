# ---------------------------------------------------------------------------
# Brasil — contra la Matriz de Insumo-Produto del IBGE (nível 67, 2010 y 2015).
#
# Es el caso más exigente de todos, porque el IBGE no publica sólo el resultado
# sino los INTERMEDIOS del cálculo:
#
#   Tabela 13  Matriz de participação setorial na produção dos produtos
#              nacionais — Matriz D          <- nuestra matriz D
#   Tabela 14  Matriz dos coeficientes técnicos intersetoriais — D·Bn
#                                            <- nuestra matriz A
#   Tabela 15  Matriz de impacto intersetorial — Matriz de Leontief
#                                            <- nuestra matriz L
#
# En Colombia sólo se podía comparar Z y deducir que el desvío venía de D. Acá
# se compara la D directamente: si cierra, el reparto producto→industria está
# bien calculado y cualquier diferencia posterior es de datos, no de método.
# ---------------------------------------------------------------------------

validar_brasil <- function() {
  res <- list()
  for (anio in c(2010, 2015)) {
    libro <- file.path(RAIZ, "matrices", "Brasil", sprintf("MIP_Brasil_%d_LIBRO.xlsx", anio))
    ofi <- file.path(CRUDO, "brasil", sprintf("MIP_IBGE_%d_Nivel_67.xls", anio))
    if (!file.exists(libro) || !file.exists(ofi)) {
      cat(sprintf("  [omitido] Brasil %d: falta %s\n", anio,
                  if (!file.exists(libro)) basename(libro) else basename(ofi)))
      next
    }

    # Las tres tablas del IBGE comparten layout: fila 3 los códigos de columna
    # (con el nombre pegado tras un salto de línea), datos desde la fila 5.
    leer_ibge <- function(hoja) {
      d <- leer_hoja(ofi, hoja)
      r0 <- fila_con(d, 1, "0191")
      fin <- r0
      while (fin + 1 <= nrow(d) && !is.na(d[fin + 1, 1]) &&
             !grepl("^Fonte", trimws(as.character(d[fin + 1, 1])))) fin <- fin + 1
      filas <- r0:fin
      cod_fila <- trimws(as.character(d[filas, 1]))
      # los encabezados de columna traen "código\nnombre": se corta en el salto
      enc <- as.character(unlist(d[r0 - 2, ]))
      cod_col <- trimws(sub("\n.*$", "", enc))
      cols <- which(!is.na(cod_col) & cod_col != "" & seq_along(cod_col) >= 3)
      M <- as.matrix(sapply(d[filas, cols], as.numeric))
      dimnames(M) <- list(cod_fila, cod_col[cols])
      M
    }

    D_ofi <- leer_ibge("13")
    A_ofi <- leer_ibge("14")
    L_ofi <- leer_ibge("15")

    D_nos <- leer_matriz_libro(libro, "D participaciones")

    # Las Tabelas 14 y 15 del IBGE son DOMÉSTICAS (`Bn` son los coeficientes
    # nacionales) y nuestro libro publica la doméstica, así que la hoja «Z
    # consumos intermedios» es el mismo objeto y se compara directo. (El libro no
    # entrega la total; se rearma con Z + D·U^imp si alguna vez hace falta.)
    Z_dom <- leer_matriz_libro(libro, "Z consumos intermedios")
    g <- leer_vector_libro(libro)
    gv <- g[colnames(Z_dom)]
    gv[gv == 0] <- 1
    A_nos <- sweep(Z_dom, 2, gv, "/")
    L_nos <- solve(diag(nrow(A_nos)) - A_nos)
    dimnames(L_nos) <- dimnames(A_nos)

    # Los códigos del libro salen del mismo archivo del IBGE, así que deberían
    # coincidir sin puente. Si no, se avisa en vez de comparar cosas distintas.
    for (par in list(list("D", D_nos, D_ofi), list("A", A_nos, A_ofi), list("L", L_nos, L_ofi))) {
      obj <- par[[1]]; nos <- par[[2]]; of <- par[[3]]
      fi <- intersect(rownames(nos), rownames(of))
      co <- intersect(colnames(nos), colnames(of))
      if (length(fi) != nrow(of) || length(co) != ncol(of)) {
        cat(sprintf("  [aviso] Brasil %d %s: coinciden %d de %d filas y %d de %d columnas\n",
                    anio, obj, length(fi), nrow(of), length(co), ncol(of)))
      }
      if (!length(fi) || !length(co)) next
      m <- metricas(nos[fi, co, drop = FALSE], of[fi, co, drop = FALSE],
                    sprintf("Brasil %d", anio), obj)
      imprimir(m); res[[length(res) + 1]] <- m
    }
  }
  res
}
