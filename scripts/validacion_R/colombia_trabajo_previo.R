# ---------------------------------------------------------------------------
# Colombia — contraste contra el trabajo previo hecho en el DANE
# (carpeta `Validación_Colombia`: L, Ghosh y encadenamientos para 2017/2019/2021).
#
# QUÉ ES ESE TRABAJO. El script original no reconstruye la MIP: lee la que el
# DANE ya publica y sobre ella calcula A, L, Ghosh y una extensión ambiental. No
# es una reconstrucción alternativa a la nuestra, es la matriz oficial más el
# análisis. Por eso el contraste no dice «quién tiene razón» sino si nuestra
# reconstrucción llega al mismo lugar que el dato publicado.
#
# DE QUÉ CUADRO SALE SU L. El script dice «Cuadro 7» y se verificó que así es,
# sin depender de esa etiqueta: invirtiendo su L se recupera A = I − L⁻¹, y como
# A = Z·diag(x)⁻¹, los cocientes Z[i,j]/A[i,j] tienen que ser constantes dentro
# de cada columna para el Z correcto. Sólo el Cuadro 7 lo cumple (dispersión
# 7e-14 en 2019 y 9e-14 en 2021); los otros siete quedan en 1e-1 o peor.
#
# EL PUNTO QUE HAY QUE RESOLVER ANTES DE COMPARAR NADA. El Cuadro 7 es
# «Nacional e Importado»: trata los insumos importados como ENDÓGENOS. Nuestras
# matrices son domésticas y dejan la importación como fila primaria exógena, que
# es el Cuadro 5. Son dos objetos distintos y la L del Cuadro 7 es
# necesariamente mayor. Compararlas de frente mostraría una brecha que no es
# error de nadie: es la definición.
#
# Contrastes, en orden:
#   (1) su L vs L recalculada del Cuadro 7   -> ¿reproducimos su cálculo?
#   (2) L del Cuadro 7 vs L del Cuadro 5     -> cuánto pesa doméstico/total
#   (3) nuestra L vs L del Cuadro 5          -> LA validación que importa
#
# Sobre agregar: L no se agrega sumando. Para (3) se agregan Z y x a la
# partición común y recién ahí se recalculan A y L, que es la operación correcta.
# ---------------------------------------------------------------------------

PREVIO <- file.path(RAIZ, "Validación_Colombia")

#' Z (68x68) y producción bruta de un cuadro actividad × actividad del DANE.
#' Cuadro 5 = Nacional (doméstico) · Cuadro 7 = Nacional e Importado (total).
#' La columna «Total» es la producción bruta y es la MISMA en ambos cuadros: lo
#' que cambia entre ellos es el interior de Z, no el denominador.
leer_dane_cuadro <- function(ruta, cuadro) {
  d <- leer_hoja(ruta, cuadro)
  s <- as.data.frame(lapply(d, function(v) trimws(as.character(v))), stringsAsFactors = FALSE)
  hr <- which(apply(s, 1, function(f) any(f == "A0101", na.rm = TRUE)))[1]
  cols <- which(!is.na(s[hr, ]) & s[hr, ] != "" & s[hr, ] != "NA")
  cols <- cols[cols >= 3]
  cols <- cols[seq_len(68)]
  cod <- as.character(s[hr, cols])
  filas <- which(s[[1]] %in% cod)
  filas <- filas[filas > hr][seq_len(68)]
  stopifnot(identical(as.character(s[filas, 1]), cod))

  Z <- as.matrix(sapply(d[filas, cols], as.numeric))
  dimnames(Z) <- list(cod, cod)
  ctot <- which(s[hr, ] == "Total")
  x <- as.numeric(unlist(d[filas, tail(ctot, 1)]))
  names(x) <- cod
  list(Z = Z, x = x)
}

#' Las dos versiones de Z a partir del libro.
#'
#' El libro publica la matriz DOMÉSTICA (el insumo importado va en fila
#' primaria), que es el homólogo del Cuadro 5. La total —homóloga del Cuadro 7—
#' se arma sumando la parte importada, con las mismas hojas que el libro trae:
#' Z_total = Z_dom + D · U^imp. La `D` es la misma matriz de cuotas de mercado
#' con la que se obtuvo Z_dom, así que el insumo importado se reparte de
#' producto a industria con el mismo criterio, que es lo que hace el DANE. El
#' libro NO entrega la matriz total —todo lo que publica se deriva de la Z
#' doméstica—, así que rearmarla acá desde las piezas publicadas es la única
#' vía, y de paso verifica que esas piezas alcanzan.
z_total_libro <- function(libro) {
  Zd <- leer_matriz_libro(libro, "Z consumos intermedios")
  D <- leer_matriz_libro(libro, "D participaciones")      # ind x prod
  Ui <- leer_matriz_libro(libro, "SUT importado")         # prod x ind
  # los códigos de producto tienen que casar entre D y U^imp; si no casan, el
  # producto de matrices daría un número plausible pero equivocado
  pd_ <- trimws(colnames(D)); pu <- trimws(rownames(Ui))
  comunes <- intersect(pd_, pu)
  if (length(comunes) < 0.95 * length(pd_))
    stop(sprintf("D y U^imp no comparten códigos de producto (%d de %d)",
                 length(comunes), length(pd_)))
  Zi <- D[, comunes, drop = FALSE] %*% Ui[comunes, , drop = FALSE]
  Zi <- Zi[rownames(Zd), colnames(Zd), drop = FALSE]
  list(dom = Zd, imp = Zi, total = Zd + Zi)
}

#' A = Z·diag(x)⁻¹ y L = (I−A)⁻¹.
leontief <- function(Z, x) {
  x2 <- ifelse(abs(x) < 1e-12, 1, x)
  A <- sweep(Z, 2, x2, "/")
  L <- solve(diag(nrow(A)) - A)
  dimnames(L) <- dimnames(A) <- dimnames(Z)
  list(A = A, L = L)
}

#' La hoja «Leontief» del libro generado en el DANE: fila 1 códigos, fila 2
#' nombres, filas 3-70 datos; columna 1 código, columna 2 nombre.
leer_L_previa <- function(anio) {
  f <- file.path(PREVIO, sprintf("MIP_Colombia_%d.xlsx", anio))
  if (!file.exists(f)) return(NULL)
  d <- leer_hoja(f, "Leontief")
  M <- as.matrix(sapply(d[3:70, 3:70], as.numeric))
  if (nrow(M) != 68 || ncol(M) != 68) return(NULL)
  M
}

validar_colombia_previo <- function() {
  res <- list()
  for (anio in c(2017, 2019, 2021)) {
    L_prev <- leer_L_previa(anio)
    ofi <- file.path(CRUDO, "colombia", sprintf("DANE_MIP_%d.xlsx", anio))
    libro <- file.path(RAIZ, "matrices", "Colombia",
                       sprintf("MIP_Colombia_%d_LIBRO.xlsx", anio))
    cat(sprintf("\n--- Colombia %d ---\n", anio))
    if (is.null(L_prev)) { cat("  [omitido] no está la L del trabajo previo\n"); next }
    if (!file.exists(ofi)) {
      cat("  [omitido] no está descargada la MIP oficial del DANE de ese año,\n",
          "            así que no se puede separar el efecto doméstico/total\n", sep = "")
      next
    }

    c5 <- leer_dane_cuadro(ofi, "Cuadro 5")   # Nacional
    c7 <- leer_dane_cuadro(ofi, "Cuadro 7")   # Nacional e Importado
    L5 <- leontief(c5$Z, c5$x)$L
    L7 <- leontief(c7$Z, c7$x)$L

    # (1) ¿reproducimos su cálculo?
    d1 <- max(abs(L_prev - L7))
    cat(sprintf("  (1) su L vs L del Cuadro 7:  máx dif %.2e  %s\n",
                d1, if (d1 < 1e-8) "-> reproducido exacto" else "-> REVISAR"))

    # (2) cuánto de la brecha es definición
    m7 <- mean(colSums(L7)); m5 <- mean(colSums(L5))
    cat(sprintf("  (2) multiplicador medio: Cuadro 7 (total) %.4f · Cuadro 5 (doméstico) %.4f  -> la definición sola explica %+.1f %%\n",
                m7, m5, 100 * (m7 / m5 - 1)))

    # (3) la validación que importa
    if (!file.exists(libro)) {
      cat("  (3) [omitido] no tenemos libro de ese año (la MUPNI llega a 2020)\n")
      next
    }
    zt <- z_total_libro(libro)
    Z_nos <- zt$dom
    x_nos <- leer_vector_libro(libro)
    cat(sprintf("      Z doméstico: nuestro %s · DANE Cuadro 5 %s   |   Z importado: nuestro %s · DANE C7−C5 %s   |   Z total: nuestro %s · DANE Cuadro 7 %s\n",
                fmt(sum(zt$dom)), fmt(sum(c5$Z)), fmt(sum(zt$imp)),
                fmt(sum(c7$Z) - sum(c5$Z)), fmt(sum(zt$total)), fmt(sum(c7$Z))))
    p <- puente_dane(rownames(c5$Z))
    grupos <- sort(unique(c(p$cou, p$dane)))
    Zn <- agregar(Z_nos, p$cou, grupos); xn <- agregar_vec(x_nos, p$cou, grupos)
    Zo <- agregar(c5$Z, p$dane, grupos); xo <- agregar_vec(c5$x, p$dane, grupos)
    cat(sprintf("      producción bruta: nuestra %s · DANE %s (dif %+.4f %%)\n",
                fmt(sum(xn)), fmt(sum(xo)), 100 * (sum(xn) / sum(xo) - 1)))
    Ln <- leontief(Zn, xn)$L; Lo <- leontief(Zo, xo)$L
    m <- metricas(Ln, Lo, sprintf("Colombia %d", anio), "L dom.")
    cat("  (3) "); imprimir(m); res[[length(res) + 1]] <- m
    cat(sprintf("      multiplicador medio: nuestro %.4f · DANE doméstico %.4f (%+.2f %%)\n",
                mean(colSums(Ln)), mean(colSums(Lo)),
                100 * (mean(colSums(Ln)) / mean(colSums(Lo)) - 1)))

    # (4) el contraste directo contra el Cuadro 8. Éste es ahora el homólogo
    # natural: el libro publica la matriz total, igual que el Cuadro 7.
    Ztn <- agregar(zt$total, p$cou, grupos)
    Zt7 <- agregar(c7$Z, p$dane, grupos)
    Ltn <- leontief(Ztn, xn)$L; Lt7 <- leontief(Zt7, xo)$L
    m4 <- metricas(Ltn, Lt7, sprintf("Colombia %d", anio), "L total")
    cat("  (4) "); imprimir(m4); res[[length(res) + 1]] <- m4
    cat(sprintf("      multiplicador medio: nuestro %.4f · DANE Cuadro 8 %.4f (%+.2f %%)\n",
                mean(colSums(Ltn)), mean(colSums(Lt7)),
                100 * (mean(colSums(Ltn)) / mean(colSums(Lt7)) - 1)))
  }
  invisible(res)
}
