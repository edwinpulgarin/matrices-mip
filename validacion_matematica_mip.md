# Validacion matematica de MIP

Archivos revisados: 35
Validacion estructural: {'OK': 35}
Validacion diagnostica: {'AVISO': 27, 'OK': 8}

Criterios estructurales OK: matrices cuadradas, etiquetas alineadas, Z/A/g no negativas, A = Z/g y (I-A)L = I.
Criterios diagnosticos: ademas revisa oferta = demanda (g = sum_row(Z nacional) + f), W = g - sum_col(Z nacional) - CI importado, Lf = g, y demanda final no negativa.

Todas las MIP pasan las validaciones estructurales.