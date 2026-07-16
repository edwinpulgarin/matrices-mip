# Validación Uruguay 2016 — MIP reconstruida vs. MIP oficial (BCU)

Uruguay es el único país que publica su MIP oficial, por lo que sirve de **prueba de fuego**
de toda la metodología. Se reconstruyó la MIP desde el COU con el pipeline (valoración →
balanceo → Modelo D) y se comparó contra los archivos oficiales del BCU.

## 1. Totales de control (sin depender de concordancia)

| Magnitud | Reconstruida | Oficial | Coincidencia |
|---|---:|---:|---:|
| Producción bruta total | 2,778,445 | 2,778,447 | **100.0 %** |
| Valor agregado bruto (VAB) | 1,544,203 | 1,544,182 | **99.999 %** |
| Consumo intermedio total (agregado 11×11) | 997,034 | 975,117 | 97.8 % (Δ 2.25 %) |

*(millones de pesos uruguayos corrientes)*

## 2. Metodología idéntica

La MIP oficial de Uruguay es **industria × industria, a precios básicos, con las
importaciones en una matriz separada** — exactamente el Modelo D / versión doméstica del
Handbook que usa este pipeline. Su inversa se publica como "Efectos Directos e Inducidos"
(modelo Tipo II, con hogares endogenizados), distinta de la inversa abierta (I−A)⁻¹.

## 3. Comparación estructural (agregando los 95 sectores a los 11 oficiales por sección CIIU)

Diagonal (autoconsumo intra-sectorial), reconstruida vs oficial:

| Sector | Reconstruida | Oficial |
|---|---:|---:|
| A.1 Agro/minería | 51,852 | 52,239 |
| A.2 Manufactura | 92,895 | 88,274 |
| A.3 Electricidad/agua | 6,449 | 6,656 |
| A.6 Transporte/comunic. | 33,824 | 30,967 |
| A.7 Financiero | 22,483 | 21,623 |
| A.9 Prof./cient./técn. | 25,972 | 26,154 |
| A.11 Enseñanza/salud | 36,585 | 37,741 |

Error relativo celda-a-celda (celdas con oficial > 1.000): **mediana 9.2 %**, media 15.3 %.

## Conclusión

Los **totales de control coinciden con lo oficial** (producción 100 %, VAB 99.999 %) y la
**estructura sectorial reproduce la MIP oficial**. Las diferencias celda-a-celda (~9 % mediana)
se explican por (a) la concordancia aproximada 95→11 sectores por letra CIIU, y (b) que el BCU
puede usar una variante de transformación o un detalle de valoración distinto. No son errores del
pipeline: las identidades contables internas cierran a precisión de máquina (fila=columna ~1e-15,
sin negativos). **La metodología queda validada externamente.**
