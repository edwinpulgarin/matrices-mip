# Librerías necesarias

install.packages("knitr")
install.packages("readxl")
install.packages("dplyr")
install.packages("writexl")

library(writexl)
library(knitr)
library(readxl)
library(dplyr)

################################################################################
#                                                                              #
#                     ANÁLISIS DE MATRIZ INSUMO-PRODUCTO                       #
#                                                                              # 
#                                                                              #
################################################################################

# --- 1. Cargar datos de la Matriz Insumo-Producto (MIP) ---
# Se lee el archivo Excel con la MIP de Colombia (tomada del DANE).
# - sheet = "Cuadro 7": selecciona la hoja donde está la matriz.
# - col_names = TRUE: usa la primera fila como nombres de columna.
# - skip = 11: omite las primeras 11 filas (cabeceras y notas).
# Se debe cambiar el año a lo largo del documento
matriz_inicial <- read_excel("anex-MIP-2021.xlsx", 
                             sheet = "Cuadro 7", 
                             col_names = TRUE, skip = 11)

# --- 2. Limpieza de datos ---
# Se elimina la primera fila sobrante.
matriz_inicial <- matriz_inicial %>% slice(-1)

# Revisar nombres de columnas (para ubicar variables relevantes).
colnames(matriz_inicial)

# --- 3. Construcción de la matriz de consumos intermedios Z ---
# Z contiene los consumos intermedios (insumos utilizados entre sectores productivos).
# Seleccionamos las filas y columnas correspondientes (68 sectores productivos).
z <- as.matrix(matriz_inicial[1:68, 3:70 ])  # filas = sectores, columnas = sectores

# Dimensiones de la matriz Z (debe ser 68x68 en este caso).
dim(z)

# Visualización rápida
View(z)

# --- 4. Vector de producción bruta x ---
# Columna ...76 (o la que corresponda) contiene la producción bruta total de cada sector.
x <- as.numeric(matriz_inicial[1:68, ]$...76)
x

# Verificamos la longitud del vector (debe coincidir con número de sectores).
length(x)

# --- 5. Matriz diagonal de producción bruta ---
# Se convierte x en una matriz diagonal (X̂).
# Esto se usa para normalizar consumos intermedios.
X_hat <- diag(x)

# --- 6. Matriz de coeficientes técnicos A ---
# Relaciona insumos requeridos con la producción total.
# A = Z * X̂^(-1)
# Cada elemento a_ij indica cuántas unidades del sector i se necesitan
# para producir 1 unidad del sector j.
A <- z %*% solve(X_hat)

View(round(A,4))

View(round(z,4))

# --- 7. Matriz inversa de Leontief L ---
# L = (I - A)^(-1)
# - I: matriz identidad
# - (I - A): matriz de requerimientos directos y totales
# - L: permite estimar los encadenamientos hacia atrás (efectos en la demanda).
I <- diag(nrow(A))
L <- solve(I - A)

# Visualizar la inversa de Leontief redondeada a 4 decimales.
View(round(L,4))


# --- 8. Matriz de Ghosh G ---
# Mientras que la matriz de Leontief analiza los encadenamientos hacia atrás 
# (impactos de la demanda final en la producción), 
# la matriz de Ghosh se centra en los encadenamientos hacia adelante 
# (cómo se distribuye la oferta sectorial hacia otros sectores).
# Fórmula:
#   B = X̂^(-1) * Z      (matriz de coeficientes de distribución)
#   G = (I - B)^(-1)     (inversa de Ghosh)

B <- solve(X_hat) %*% z   # coeficientes de distribución
G <- solve(I - B)         # inversa de Ghosh

View(round(G,4))


# --- 9. Resumen interpretativo ---
# - Z: consumos intermedios (quién le compra a quién).
# - x: producción bruta total de cada sector.
# - A: coeficientes técnicos (encadenamientos directos).
# - L: matriz de Leontief (encadenamientos totales hacia atrás).
# - B: coeficientes de distribución (cómo se reparte la oferta).
# - G: matriz de Ghosh (encadenamientos totales hacia adelante).

################################################################################
#                                                                              #
#           ANÁLISIS DE EXTENSIÓN AMBIENTAL DE MATRIZ INSUMO-PRODUCTO          #
#                                                                              # 
#                                                                              #
################################################################################


################################################################################
# 1. CARGA DE DATOS AMBIENTALES
################################################################################

# Cargar datos de cuentas ambientales (emisiones y otros indicadores ambientales)
# Fuente: Cuentas Ambientales del DANE
# Las filas representan diferentes tipos de presiones ambientales
# Las columnas representan los 68 sectores productivos de la economía

env_ <- read_excel(
  "CAEFM-EA68aVALORADO.xlsx",
  sheet = "2021", 
  range = "A3:BR10"
)


# Nota: Se espera que env_ tenga la siguiente estructura:
# - Columnas 1-2: Identificadores (código y nombre de la variable ambiental)
# - Columnas 3-70: Valores de presiones ambientales por cada uno de los 68 sectores


################################################################################
# 2. PREPARACIÓN DE MATRICES DE COEFICIENTES AMBIENTALES
################################################################################

# --- 2.1 Extraer matriz de presiones ambientales totales ---
# D1: Matriz de presiones ambientales ABSOLUTAS (valores totales)
# Dimensión: 7 tipos de indicadores × 68 sectores
# Se excluyen las primeras 2 columnas (identificadores)
D1 <- as.matrix(env_[, -c(1:2)])

# --- 2.2 Calcular coeficientes de intensidad ambiental directa ---
# D: Matriz de coeficientes de intensidad ambiental DIRECTA
# Fórmula: D = D1 × (X_hat)^(-1)
# Donde X_hat = diag(x), con x = vector de producción total
# Resultado: Presión ambiental por unidad monetaria de producción
# Dimensión: 7 indicadores × 68 sectores
# Unidades ejemplo: ton CO2 / millón de pesos producidos

D <- D1 %*% solve(X_hat)

# Visualizar primeros coeficientes (7 indicadores ambientales, 10 primeros sectores)
round(D[1:7, 1:10], 4)

# --- 2.3 Verificar emisiones totales ---
# Multiplicar coeficientes por vector de producción para recuperar emisiones totales
# Debe ser igual a rowSums(D1)
emisiones_totales <- D %*% x
print(emisiones_totales)

################################################################################
# 3. MATRIZ EXTENDIDA: ECONOMÍA + AMBIENTE (Enfoque Productor)
################################################################################

# --- 3.1 Matriz G: Combinar coeficientes ambientales y económicos ---
# G representa el sistema combinado: ambiente + economía
# Estructura:
#   - Primeras 7 filas: Coeficientes ambientales directos (D)
#   - Siguientes 68 filas: Matriz inversa de Leontief (L)
# Dimensión: (7 + 68) × 68 = 75 × 68

G <- rbind(D, L)

# Visualizar esquina superior izquierda de G
round(G[1:10, 1:10], 4)

# --- 3.2 Calcular impactos ambientales y económicos directos ---
# s: Vector de impactos totales (ambientales + económicos) por sector
# s = G × x, donde x = vector de producción
# Resultado: 
#   - Primeros 7 elementos: emisiones/presiones totales por indicador
#   - Elementos 8-75: producción total por sector (debe coincidir con x)

s <- G %*% x
round(s, 4)

################################################################################
# 4. MULTIPLICADORES AMBIENTALES TOTALES (Enfoque Consumidor)
################################################################################

# --- 4.1 Multiplicadores ambientales (directos + indirectos) ---
# D_a: Matriz de multiplicadores ambientales tipo Leontief
# Fórmula: D_a = D × L
# Donde L = (I - A)^(-1) es la inversa de Leontief
# Interpretación: Presión ambiental total (directa + cadenas productivas)
#                 por unidad de demanda final en cada sector
# Dimensión: 7 indicadores × 68 sectores

D_a <- D %*% L

# --- 4.2 Matriz extendida con multiplicadores totales ---
# H: Similar a G, pero con efectos totales en lugar de directos
# Estructura:
#   - Primeras 7 filas: Multiplicadores ambientales totales (D_a)
#   - Siguientes 68 filas: Inversa de Leontief (L)

H <- rbind(D_a, L)

# Visualizar multiplicadores
round(H[1:10, 1:10], 4)


################################################################################
# 5. AGREGACIÓN DE INDICADORES AMBIENTALES
################################################################################

# --- 5.1 Gamma_1: Suma de Gases de Efecto Invernadero (GEI) ---
# Sumar las primeras 3 filas de D1 (ej: CO2, CH4, N2O)
# Resultado: Vector de emisiones GEI totales por sector
# Dimensión: 1 × 68

Gamma_1 <- as.matrix(colSums(D1[1:3, ]))
Gamma_1[1:10, ]  # Visualizar primeros 10 sectores

# --- 5.2 Gamma_2: Suma de otros indicadores ambientales ---
# Sumar filas 4-7 de D1 (ej: agua, residuos, energía, materiales)
# Resultado: Vector con total de otros indicadores por sector
# Dimensión: 1 × 68

Gamma_2 <- as.matrix(colSums(D1[4:7, ]))
Gamma_2[1:10, ]  # Visualizar primeros 10 sectores

################################################################################
# 6. COEFICIENTES DE INTENSIDAD AMBIENTAL POR SECTOR (Diagonal)
################################################################################

# Número de sectores en la economía
t <- 68

# --- 6.1 alpha_1: Coeficientes de intensidad de GEI por sector ---
# Fórmula: alpha_1[i,i] = Gamma_1[i] / g[i]
# Interpretación: Emisiones GEI por unidad monetaria de producción del sector i
# Se usa matriz diagonal para facilitar operaciones matriciales posteriores
# Dimensión: 68 × 68 (diagonal)

alpha_1 <- diag(diag(matrix(Gamma_1 / x, ncol = t, nrow = t)))
alpha_1[1:10, 1:10]  # Visualizar esquina superior izquierda

# --- 6.2 alpha_2: Coeficientes de intensidad de otros indicadores ---
# Similar a alpha_1, pero para otros indicadores ambientales
# Dimensión: 68 × 68 (diagonal)

alpha_2 <- diag(diag(matrix(Gamma_2 / x, ncol = t, nrow = t)))
alpha_2[1:10, 1:10]  # Visualizar esquina superior izquierda

################################################################################
# 7. MULTIPLICADORES TIPO LEONTIEF (Demand-Driven / Backward Linkages)
################################################################################

# Los multiplicadores Leontief capturan efectos hacia atrás en la cadena productiva
# Pregunta: ¿Cuántas emisiones se generan si aumenta la DEMANDA FINAL del sector j?

# --- 7.1 Leon_amb1: Multiplicadores ambientales Leontief para GEI ---
# Fórmula: Leon_amb1 = alpha_1 × L
# Interpretación: Emisiones GEI totales (directas + indirectas) generadas
#                 por una unidad adicional de demanda final en cada sector
# Dimensión: 68 × 68

Leon_amb1 <- alpha_1 %*% L
Leon_amb1[1:10, 1:10]  # Visualizar multiplicadores

# --- 7.2 Leon_amb2: Multiplicadores ambientales Leontief para otros indicadores ---
# Similar a Leon_amb1, pero para otros indicadores ambientales
# Dimensión: 68 × 68

Leon_amb2 <- alpha_2 %*% L
Leon_amb2[1:10, 1:10]  # Visualizar multiplicadores

################################################################################
# 8. MODELO DE GHOSH Y MULTIPLICADORES TIPO GHOSH (Supply-Driven / Forward Linkages)
################################################################################

# El modelo de Ghosh captura efectos hacia adelante en la cadena productiva
# Pregunta: ¿Cómo se distribuyen las emisiones si aumenta la OFERTA primaria del sector i?

# --- 8.1 Matriz de coeficientes de distribución (B) ---
# B[i,j] = proporción del output del sector i que va al sector j
# Fórmula: B = Z × diag(g)^(-1), donde cada fila de Z se divide por g[i]
# sweep() divide cada fila i de la matriz z por el elemento i del vector g
# Dimensión: 68 × 68

B <- sweep(z, 1, x, "/")

# --- 8.2 Inversa de Ghosh ---
# G_inv = (I - B)^(-1)
# Similar a la inversa de Leontief, pero para el modelo de oferta
# Interpretación: Efectos de distribución acumulados en la cadena productiva
# Dimensión: 68 × 68

G_inv <- solve(diag(nrow(B)) - B)

# --- 8.3 Ghost_amb1: Multiplicadores ambientales Ghosh para GEI ---
# Fórmula: Ghost_amb1 = G_inv × t(alpha_1)
# Interpretación: Cómo las emisiones de un sector se distribuyen hacia adelante
#                 cuando aumenta su producción primaria
# Dimensión: 68 × 68

Ghost_amb1 <- G_inv %*% t(alpha_1)
Ghost_amb1[1:10, 1:10]  # Visualizar multiplicadores
View(Ghost_amb1)  # Ver matriz completa

# --- 8.4 Ghost_amb2: Multiplicadores ambientales Ghosh para otros indicadores ---
# Similar a Ghost_amb1, pero para otros indicadores ambientales
# Dimensión: 68 × 68

Ghost_amb2 <- G_inv %*% t(alpha_2)
Ghost_amb2[1:10, 1:10]  # Visualizar multiplicadores

################################################################################
# 9. ÍNDICES DE ENCADENAMIENTO AMBIENTAL (Environmental Linkages)
################################################################################

# Los índices de encadenamiento miden la importancia relativa de cada sector
# en términos de sus impactos ambientales directos e indirectos

# --- 9.1 BL_1: Backward Linkage ambiental para GEI (Leontief) ---
# Mide el efecto multiplicador HACIA ATRÁS (cuánto contamina la demanda del sector)
# Fórmula: BL_i = (suma de columna i) / (promedio de todas las columnas)
# BL > 1: El sector tiene encadenamientos hacia atrás superiores al promedio
# BL < 1: El sector tiene encadenamientos hacia atrás inferiores al promedio

frac_2 <- sum(Leon_amb1) / 68         # Promedio general de multiplicadores
frac_1 <- rowSums(Leon_amb1)          # Suma por fila (efecto total del sector i)
BL_1 <- frac_1 / frac_2               # Índice de encadenamiento hacia atrás
round(BL_1, 4)

# --- 9.2 BL_2: Backward Linkage ambiental para otros indicadores ---
frac_2 <- sum(Leon_amb2) / 68
frac_1 <- rowSums(Leon_amb2)
BL_2 <- frac_1 / frac_2
round(BL_2, 4)

# --- 9.3 FL_1: Forward Linkage ambiental para GEI (Ghosh) ---
# Mide el efecto multiplicador HACIA ADELANTE (cómo distribuye su contaminación)
# Fórmula: FL_j = (suma de fila j) / (promedio de todas las filas)
# FL > 1: El sector distribuye más contaminación que el promedio
# FL < 1: El sector distribuye menos contaminación que el promedio

frac_2 <- sum(Ghost_amb1) / 68        # Promedio general
frac_1 <- colSums(Ghost_amb1)         # Suma por columna (distribución del sector j)
FL_1 <- frac_1 / frac_2               # Índice de encadenamiento hacia adelante
round(FL_1, 4)

# --- 9.4 FL_2: Forward Linkage ambiental para otros indicadores ---
frac_2 <- sum(Ghost_amb2) / 68
frac_1 <- colSums(Ghost_amb2)
FL_2 <- frac_1 / frac_2
round(FL_2, 4)

# --- 9.5 Resumen de linkages promedio ---
# Comparar promedios de encadenamientos hacia adelante y hacia atrás
linkages_promedio <- c(
  FL_GEI = mean(FL_1),      # Forward Linkage promedio GEI
  FL_Otros = mean(FL_2),    # Forward Linkage promedio otros
  BL_GEI = mean(BL_1),      # Backward Linkage promedio GEI
  BL_Otros = mean(BL_2)     # Backward Linkage promedio otros
)
print(linkages_promedio)

################################################################################
# 10. PONDERADORES DE DEMANDA FINAL Y CONSUMO INTERMEDIO
################################################################################

# Estos ponderadores se usan para análisis estructural de la economía

# --- 10.1 p_F: Ponderadores de demanda final ---
# Proporción que representa cada elemento de la demanda final sobre el total
# Útil para descomponer impactos por tipo de demanda (consumo, inversión, etc.)
# Suma = 1

p_F <- abs(F) / sum(abs(F))

# --- 10.2 p_U: Ponderadores de consumo intermedio ---
# Proporción que representa cada sector en el consumo intermedio total
# U = matriz de consumos intermedios (uso de insumos)
# Suma = 1

p_U <- as.matrix(colSums(U) / sum(colSums(U)))

# Verificar dimensiones y que sumen 1
verificacion_ponderadores <- c(
  dim(p_F), 
  dim(p_U), 
  sum(p_F), 
  sum(p_U)
)
print(verificacion_ponderadores)

################################################################################
# 11. CARGA DE MATRICES INSUMO-PRODUCTO DOMÉSTICAS E IMPORTADAS
################################################################################

# --- 11.1 Cargar matriz de transacciones domésticas ---
# Cuadro 5: Matriz de Utilización (Producción Doméstica)
# Contiene el uso de productos nacionales por sector y por demanda final

domestica <- read_excel(
  "anex-MIP-2021.xlsx", 
  sheet = "Cuadro 5",
  col_names = TRUE, 
  skip = 11  # Saltar filas de encabezado
)

# Eliminar primera fila (puede contener subtítulos)
domestica <- domestica %>% slice(-1)

# Revisar estructura
colnames(domestica)

# --- 11.2 Extraer matriz Bd de coeficientes domésticos ---
# Bd: Matriz de coeficientes técnicos de producción DOMÉSTICA
# Filas 1-68: Productos
# Columnas 3-70: Sectores (68 sectores)
# Las primeras 2 columnas son identificadores

Bd <- as.matrix(domestica[1:68, 3:70])

# --- 11.3 Cargar matriz de importaciones ---
# Cuadro 6: Matriz de Utilización (Importaciones)
# Contiene el uso de productos importados por sector y por demanda final

importaciones <- read_excel(
  "anex-MIP-2021.xlsx", 
  sheet = "Cuadro 6",
  col_names = TRUE, 
  skip = 11
)

importaciones <- importaciones %>% slice(-1)

# Revisar estructura
colnames(importaciones)

# --- 11.4 Extraer matriz Bm de coeficientes importados ---
# Bm_2: Matriz de coeficientes técnicos de productos IMPORTADOS
# Estructura igual a Bd
# Dimensión: 68 × 68

Bm <- as.matrix(importaciones[1:68, 3:70])
View(Bm)

################################################################################
# 12. CÁLCULO DE MATRICES TÉCNICAS DESAGREGADAS
################################################################################

# --- 12.1 Matriz de coeficientes técnicos domésticos ---
# Ad = Bd × X_hat^(-1)
# Representa requerimientos de insumos NACIONALES por unidad de producción
# Dimensión: 68 × 68

Ad <- Bd %*% solve(X_hat)

# --- 12.2 Matriz de coeficientes técnicos importados ---
# At = Bm × X_hat^(-1)
# Representa requerimientos de insumos IMPORTADOS por unidad de producción
# Dimensión: 68 × 68

At <- Bm %*% solve(X_hat)

# --- 12.3 Verificación de consistencia ---
# La suma Ad + At debe ser igual a la matriz A de coeficientes totales
# A = Ad + At

verificacion_A <- all(round(A, 4) == round(Ad + At, 4))
cat("Verificación: A == Ad + At:", verificacion_A, "\n")


################################################################################
# NOTAS FINALES
################################################################################

# Este script implementa la metodología estándar de extensión ambiental
# de matrices insumo-producto, siguiendo el enfoque de Miller & Blair (2009)
# y las guías de Eurostat para cuentas satélite ambientales.

# Resultados principales:
# 1. Leon_amb1 y Leon_amb2: Multiplicadores tipo Leontief (demand-driven)
# 2. Ghost_amb1 y Ghost_amb2: Multiplicadores tipo Ghosh (supply-driven)
# 3. BL_1, BL_2: Índices de encadenamiento hacia atrás (backward linkages)
# 4. FL_1, FL_2: Índices de encadenamiento hacia adelante (forward linkages)
# 5. Pd y Pt: Responsabilidad del productor vs consumidor


# Crear una lista con los dataframes a exportar
lista_dfs <- list(
"Leon" = as.data.frame(L),
"H" = as.data.frame(H),
"Leon_amb1" = as.data.frame(Leon_amb1),
"Leon_amb2" = as.data.frame(Leon_amb2),
"Ghost_amb1" = as.data.frame(Ghost_amb1),
"Ghost_amb2" = as.data.frame(Ghost_amb2),
"BL_1" = as.data.frame(BL_1),
"BL_2" = as.data.frame(BL_1),
"FL_1" = as.data.frame(FL_1),
"FL_2" = as.data.frame(FL_2)
)

# Guardar en Excel con múltiples hojas
write_xlsx(lista_dfs, "MIP_Colombia_2021.xlsx")

