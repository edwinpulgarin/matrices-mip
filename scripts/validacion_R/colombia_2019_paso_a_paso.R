# Librerías necesarias
# install.packages("readxl")

library(readxl)

################################################################################
#                                                                              #
#            DEL CUADRO OFERTA-UTILIZACIÓN A LA MATRIZ INSUMO-PRODUCTO         #
#                              Colombia 2019 — DANE                            #
#                                                                              #
################################################################################

# Parte del COU que publica el DANE y llega a la matriz simétrica, los
# coeficientes técnicos y la inversa de Leontief. Un solo archivo de entrada y
# todos los pasos a la vista.
#
# El resultado es la matriz TOTAL (nacional + importada), que es la misma
# definición del Cuadro 7 del anexo MIP del DANE.
#
# Referencia: UN Handbook on Supply, Use and Input-Output Tables,
# Series F No.74 Rev.1 (2018), capítulos 7, 12 y 20.

ARCHIVO <- "c:/Users/edwin/Documents/MIP V2/data/raw/colombia/DANE_COU_2014_2024_corrientes.xlsx"

# Las hojas van numeradas por año: 2014+k -> oferta "Cuadro 1+2k",
# utilización "Cuadro 2+2k". Para 2019 (k=5) son los Cuadros 11 y 12.
# Para cambiar de año se cambian sólo estas dos líneas.
HOJA_OFERTA <- "Cuadro 11"
HOJA_USO    <- "Cuadro 12"

# --- 1. Cargar el COU ---
# Se leen las dos hojas completas y sin encabezado: el DANE escribe los títulos
# en cuatro filas superpuestas, así que es más claro ubicar todo por posición.

oferta <- as.data.frame(read_excel(ARCHIVO, sheet = HOJA_OFERTA,
                                   col_names = FALSE, .name_repair = "minimal"))
uso    <- as.data.frame(read_excel(ARCHIVO, sheet = HOJA_USO,
                                   col_names = FALSE, .name_repair = "minimal"))

# Las filas de producto son las que llevan código CPC en la primera columna
# ('01', '02', ..., '12 + 13'): son 66 divisiones.
#
# OJO: se buscan por SEPARADO en cada hoja. readxl recorta las filas vacías del
# principio y no recorta la misma cantidad en las dos: en este archivo la
# oferta arranca en la fila 12 y la utilización en la 13. Usar las filas de una
# para leer la otra corre todo un renglón y descuadra los balances.
filas_oferta <- which(grepl("^[0-9]", oferta[[1]]))
filas_uso    <- which(grepl("^[0-9]", uso[[1]]))
stopifnot(length(filas_oferta) == length(filas_uso))

codigo <- oferta[filas_oferta, 1]
nombre <- oferta[filas_oferta, 2]
length(codigo)         # 66 productos

# --- 2. Mapa de columnas ---
# Cuadro de OFERTA (las letras son las columnas de Excel):
#     C     Total oferta a precios de comprador
#     D     Márgenes de comercio          E   Márgenes de transporte
#     F     Impuestos y derechos a las importaciones
#     G     IVA no deducible
#     H     Impuestos a los productos     I   Subvenciones a los productos
#     K:BS  Producción por industria — las 61 actividades CIIU
#     BU    Producción total a precios básicos
#     BZ    Ajustes CIF/FOB               CA  Importaciones de bienes
#                                         CB  Importaciones de servicios
#
# Cuadro de UTILIZACIÓN:
#     F:BN  Consumo intermedio por industria — las mismas 61 actividades
#     CA    Gasto de consumo final de los hogares   (a precios de comprador)
#     CI    ISFLSH                        CS  Gobierno
#     DB    Formación bruta de capital fijo
#     DJ    Variación de existencias      DR  Objetos valiosos
#     EB    Exportaciones
#     fila 85  Valor agregado por industria

IND_OFERTA <- 11:71     # K:BS
IND_USO    <- 6:66      # F:BN

num    <- function(x) { v <- suppressWarnings(as.numeric(as.character(x)))
                        v[is.na(v)] <- 0; v }
col_of <- function(j) num(oferta[filas_oferta, j])
col_us <- function(j) num(uso[filas_uso, j])

# --- 3. Producción, utilización y demanda final ---

# V: producción de cada producto por cada industria, a precios básicos (66 x 61)
V <- as.matrix(sapply(IND_OFERTA, col_of))

# U: consumo intermedio, a precios de COMPRADOR (66 x 61)
U_comprador <- as.matrix(sapply(IND_USO, col_us))
rownames(V) <- rownames(U_comprador) <- codigo

# Demanda final a precios de comprador, con el detalle que publica el COU
Y_comprador <- cbind(
  Hogares          = col_us(79),    # CA
  ISFLSH           = col_us(87),    # CI
  Gobierno         = col_us(97),    # CS
  FBK_fijo         = col_us(106),   # DB
  Var_existencias  = col_us(114),   # DJ
  Objetos_valiosos = col_us(122),   # DR
  Exportaciones    = col_us(132))   # EB
rownames(Y_comprador) <- codigo

# Puente de valoración, por producto
oferta_comprador  <- col_of(3)                 # C
margen_comercio   <- col_of(4)                 # D
margen_transporte <- col_of(5)                 # E
imp_importacion   <- col_of(6)                 # F
iva               <- col_of(7)                 # G
imp_productos     <- col_of(8) - col_of(9)     # H menos I (subvenciones)
produccion        <- col_of(73)                # BU
ajuste_cif_fob    <- col_of(78)                # BZ
importaciones     <- col_of(79) + col_of(80)   # CA + CB

margenes  <- margen_comercio + margen_transporte
impuestos <- imp_productos + imp_importacion + iva

# VERIFICACIÓN 1 — el puente del propio cuadro cierra:
#   producción + importaciones + impuestos + márgenes = precios de comprador
cat("1. Puente de valoración, diferencia máxima:",
    max(abs(produccion + importaciones + ajuste_cif_fob +
            impuestos + margenes - oferta_comprador)), "\n")

# VERIFICACIÓN 2 — leímos toda la utilización que el cuadro declara
cat("2. Oferta declarada menos utilización leída:",
    sum(oferta_comprador - rowSums(U_comprador) - rowSums(Y_comprador)), "\n")

# --- 4. Quitar los impuestos sobre los productos (Handbook Cap. 7) ---
# El COU publica los impuestos POR PRODUCTO, no celda por celda. El §7.76
# admite repartirlos proporcionalmente dentro de la fila: cada celda conserva
# la misma fracción sin impuestos que su producto.
#
#     factor = (oferta a comprador − impuestos) / oferta a comprador
#
# ESTE ES EL ÚNICO SUPUESTO DE TODO EL PROCEDIMIENTO.

factor_sin_impuestos <- ifelse(oferta_comprador != 0,
                               (oferta_comprador - impuestos) / oferta_comprador, 0)

U_1 <- U_comprador * factor_sin_impuestos
Y_1 <- Y_comprador * factor_sin_impuestos

# Los impuestos que salieron del consumo intermedio son una fila primaria de
# la MIP: los paga la industria que compra.
impuestos_por_industria <- colSums(U_comprador) - colSums(U_1)

cat("3. Impuestos sobre los productos:", round(sum(impuestos)),
    "— en el consumo intermedio:", round(sum(impuestos_por_industria)), "\n")

# --- 5. Reasignar los márgenes de comercio y transporte (§7.77) ---
# El precio de comprador de un bien incluye el margen del comerciante que lo
# distribuye. A precios básicos ese margen NO desaparece: cambia de FILA, del
# bien al servicio de comercio, dentro de la MISMA columna. Por eso el total
# de cada columna se conserva.
#
# En el cuadro de oferta el margen viene positivo en los bienes que lo llevan
# incorporado y NEGATIVO en los servicios que lo prestan. Ese signo es el que
# dice a quién hay que devolvérselo.

precio_productor <- produccion + importaciones + ajuste_cif_fob + margenes

# qué fracción del valor de cada bien es margen
fraccion_margen <- ifelse(precio_productor != 0,
                          pmax(margenes, 0) / precio_productor, 0)

# quién presta el margen (las filas con margen negativo), normalizado a 1
presta_margen <- pmax(-margenes, 0)
presta_margen <- presta_margen / sum(presta_margen)

retirado_U <- U_1 * fraccion_margen
retirado_Y <- Y_1 * fraccion_margen

U <- U_1 - retirado_U + outer(presta_margen, colSums(retirado_U))
Y <- Y_1 - retirado_Y + outer(presta_margen, colSums(retirado_Y))

# El caso que lo muestra de un vistazo: la fila de comercio
comercio <- which(codigo == "61 + 62")
cat("4. Comercio (61 + 62) en el consumo intermedio: antes",
    round(sum(U_1[comercio, ])), "-> después", round(sum(U[comercio, ])), "\n")

# VERIFICACIÓN 3 — la reasignación no cambia ningún total de columna
cat("5. Cambio máximo en un total de columna:",
    max(abs(colSums(U) - colSums(U_1))), "\n")

# --- 6. El SUT a precios básicos ---
# U e Y ya están a precios básicos y son TOTALES: incluyen el insumo nacional
# y el importado juntos. Por eso las importaciones entran por la OFERTA y no
# como fila primaria.

M <- importaciones + ajuste_cif_fob     # importaciones por producto
q <- rowSums(V)                         # producción por producto
g <- colSums(V)                         # producción por industria

# Valor agregado: la fila se busca por su nombre, debajo del bloque de
# productos (en el archivo es la fila 85 de Excel, pero readxl la corre).
fila_va <- which(trimws(as.character(uso[[2]])) == "Valor agregado")
valor_agregado <- num(uso[fila_va, IND_USO])

# VERIFICACIÓN 4 — las dos identidades del SUT
#   por producto:  producción + importaciones = utilización + demanda final
#   por industria: producción = utilización + valor agregado + impuestos
cat("6. Balance por producto, máximo:",
    max(abs(q + M - rowSums(U) - rowSums(Y))), "\n")
cat("7. Balance por industria, máximo:",
    max(abs(g - colSums(U) - valor_agregado - impuestos_por_industria)), "\n")

# Los dos cierran, así que el balanceo RAS (Cap. 11) no interviene. Sólo hace
# falta cuando el cuadro publicado no cuadra por sí mismo.

# --- 7. Matriz de participaciones de mercado D (Cap. 12) ---
# D[i,p] = qué parte del producto p la produce la industria i. Es EL paso donde
# las celdas dejan de coincidir con la fuente: el uso de cada producto se
# reparte entre las industrias que lo producen.
#
#     D = V' * diag(q)^(-1)          (61 x 66, cada columna suma 1)

D <- t(V) %*% solve(diag(ifelse(q == 0, 1, q)))

cat("8. Columnas de D que suman 1:",
    sum(abs(colSums(D) - 1) < 1e-12), "de", ncol(D), "\n")

# --- 8. La matriz insumo-producto: Z = D * U (Modelo D) ---
# El Modelo D es el «supuesto de estructura fija de ventas de producto», el
# mismo que usa el DANE para sus Cuadros 5 a 8.

Z <- D %*% U                            # 61 x 61, industria por industria
f <- as.numeric(D %*% rowSums(Y))       # demanda final por industria
m <- as.numeric(D %*% M)                # importaciones por industria
colnames(Z) <- rownames(Z) <- paste0("s", seq_len(ncol(Z)))

cat("9. Suma de Z:", round(sum(Z)), "\n")

# VERIFICACIÓN 5 — las identidades de la MIP
cat("10. Por fila,    g + m = ΣZ + f:", max(abs(g + m - rowSums(Z) - f)), "\n")
cat("11. Por columna, g = ΣZ + VA + impuestos:",
    max(abs(g - colSums(Z) - valor_agregado - impuestos_por_industria)), "\n")
cat("12. Valor mínimo de Z (no puede ser negativo):", min(Z), "\n")

# --- 9. Coeficientes técnicos A e inversa de Leontief L (Cap. 20) ---
# A[i,j] = cuánto insumo del sector i hace falta por unidad producida por j.

X_hat <- diag(ifelse(g == 0, 1, g))
A <- Z %*% solve(X_hat)
I <- diag(nrow(A))
L <- solve(I - A)

# Multiplicador de producción: cuánto se moviliza en toda la economía por cada
# unidad de demanda final del sector.
multiplicador <- colSums(L)
cat("13. Multiplicador medio:", round(mean(multiplicador), 4),
    " mínimo:", round(min(multiplicador), 4),
    " máximo:", round(max(multiplicador), 4), "\n")

# VERIFICACIÓN 6 — la MIP reproduce la producción observada. En la matriz TOTAL
# parte de la demanda la abastece la importación, así que lo que la producción
# del país tiene que cubrir es (f − m).
cat("14. L * (f − m) = g, diferencia máxima:",
    max(abs(as.numeric(L %*% (f - m)) - g)), "\n")

# --- 10. Matriz de Ghosh (encadenamientos hacia adelante) ---
#     B = diag(g)^(-1) * Z    coeficientes de distribución
#     G = (I - B)^(-1)        inversa de Ghosh

B <- solve(X_hat) %*% Z
G <- solve(I - B)

# --- 11. Los sectores con mayor arrastre ---

# El código y el nombre de cada industria van juntos en una misma celda del
# encabezado, separados por un salto de línea: 'A0102' y abajo 'Ganadería, caza
# y actividades conexas'. Se toma la última fila del encabezado con contenido en
# la primera columna de industria y se descarta el código.
fila_ind <- max(which(!is.na(uso[seq_len(filas_uso[1] - 1), IND_USO[1]])))
nombre_industria <- trimws(sub("^[^\r\n]*[\r\n]+", "",
                               as.character(uso[fila_ind, IND_USO])))
ranking <- data.frame(actividad = substr(nombre_industria, 1, 44),
                      multiplicador = round(multiplicador, 4))
ranking <- ranking[order(-ranking$multiplicador), ]
head(ranking, 10)

# --- 12. Contraste contra la MIP que publica el DANE ---
# El Cuadro 7 del anexo es «Nacional e Importado»: la misma definición que
# acabamos de construir. Ojo con el Cuadro 5, que es sólo Nacional y da un 18 %
# menos — compararse contra ése sería comparar dos objetos distintos.
#
#   dane   <- read_excel("anex-MIP-2019.xlsx", sheet = "Cuadro 7",
#                        col_names = TRUE, skip = 11)
#   dane   <- dane[-1, ]
#   z_dane <- as.matrix(dane[1:68, 3:70])
#   sum(z_dane)      # 854.933   contra nuestros 855.707  ->  +0,09 %
#
# La comparación celda a celda necesita el puente de actividades del anexo 2 de
# la metodología DSO-MIP-MET-001: el DANE publica 68 actividades y el COU sale
# a 61. Los agregados no lo necesitan.

# --- 13. Resumen ---
# - V: producción por producto e industria, a precios básicos.
# - U: consumo intermedio a precios básicos, nacional + importado.
# - D: participaciones de mercado (quién produce cada producto).
# - Z: consumos intermedios entre industrias = D * U.
# - A: coeficientes técnicos (encadenamientos directos).
# - L: inversa de Leontief (encadenamientos totales hacia atrás).
# - G: inversa de Ghosh (encadenamientos totales hacia adelante).
#
# Un solo supuesto en todo el camino: el reparto proporcional de impuestos y
# márgenes dentro de cada fila (paso 4), porque el COU los publica por producto
# y no celda por celda.
