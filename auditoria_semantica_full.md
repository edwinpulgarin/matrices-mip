# Auditoria semantica MIP

Esta auditoria no reemplaza la revision contable; es una puerta minima para no publicar matrices con fallas visibles.

## Resumen

- Matrices auditadas: 33
- Estados: {'PUBLICABLE_BASE': 27, 'NO_PUBLICABLE': 6}

## Principales fallas

- demanda_final_negativa_revisar: 33
- capital_negativo: 31
- valor_agregado_negativo: 5
- consumo_final_negativo: 1
- sectores_solo_codigo: 1

## Matrices no publicables

- full_normalizado | Brasil 2011: demanda_final_negativa_revisar; capital_negativo; valor_agregado_negativo
- full_normalizado | Brasil 2012: demanda_final_negativa_revisar; capital_negativo; valor_agregado_negativo
- full_normalizado | Brasil 2013: demanda_final_negativa_revisar; capital_negativo; valor_agregado_negativo
- full_normalizado | Brasil 2014: demanda_final_negativa_revisar; capital_negativo; valor_agregado_negativo
- full_normalizado | Uruguay 2016: sectores_solo_codigo; demanda_final_negativa_revisar; capital_negativo
- full_normalizado | Uruguay 2017: demanda_final_negativa_revisar; valor_agregado_negativo

## Peores hojas por nombres/negativos/vacios

- full_normalizado | Uruguay 2016 | Cuadro 5: nombres_blank=0, solo_codigo=95, fd_vacias=0, fd_neg=10, matriz_neg=0
- full_normalizado | Uruguay 2016 | Cuadro 7: nombres_blank=0, solo_codigo=95, fd_vacias=0, fd_neg=10, matriz_neg=0
- full_normalizado | Uruguay 2016 | Cuadro 6: nombres_blank=0, solo_codigo=95, fd_vacias=0, fd_neg=0, matriz_neg=0
- full_normalizado | Argentina 2018 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=69, matriz_neg=0
- full_normalizado | Argentina 2018 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=69, matriz_neg=0
- full_normalizado | Argentina 2020 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=69, matriz_neg=0
- full_normalizado | Argentina 2020 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=69, matriz_neg=0
- full_normalizado | Argentina 2019 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=60, matriz_neg=0
- full_normalizado | Argentina 2019 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=60, matriz_neg=0
- full_normalizado | Brasil 2003 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=49, matriz_neg=0
- full_normalizado | Brasil 2003 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=49, matriz_neg=0
- full_normalizado | Argentina 2022 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=48, matriz_neg=0
- full_normalizado | Argentina 2022 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=48, matriz_neg=0
- full_normalizado | Brasil 2016 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=48, matriz_neg=0
- full_normalizado | Brasil 2016 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=48, matriz_neg=0
- full_normalizado | Brasil 2002 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=47, matriz_neg=0
- full_normalizado | Brasil 2002 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=47, matriz_neg=0
- full_normalizado | Brasil 2015 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=46, matriz_neg=0
- full_normalizado | Brasil 2015 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=46, matriz_neg=0
- full_normalizado | Brasil 2005 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=44, matriz_neg=0
- full_normalizado | Brasil 2005 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=44, matriz_neg=0
- full_normalizado | Brasil 2004 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=41, matriz_neg=0
- full_normalizado | Brasil 2004 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=41, matriz_neg=0
- full_normalizado | Argentina 2021 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=39, matriz_neg=0
- full_normalizado | Argentina 2021 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=39, matriz_neg=0
- full_normalizado | Brasil 2000 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=39, matriz_neg=0
- full_normalizado | Brasil 2000 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=39, matriz_neg=0
- full_normalizado | Brasil 2001 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=38, matriz_neg=0
- full_normalizado | Brasil 2001 | Cuadro 3: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=38, matriz_neg=0
- full_normalizado | Brasil 2018 | Cuadro 1: nombres_blank=0, solo_codigo=0, fd_vacias=0, fd_neg=38, matriz_neg=0
