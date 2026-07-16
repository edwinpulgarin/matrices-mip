"""
Reconstrucción de Matrices Insumo-Producto (MIP/IOT) desde Cuadros de Oferta
y Utilización (COU/SUT), siguiendo el UN Handbook on Supply, Use and
Input-Output Tables (Series F No.74 Rev.1, 2018).

Pipeline por etapas, cada una mapeada a un capítulo del Handbook:

    ingesta        (Cap. 5-6)   parsers/  -> estructura canónica SUT
    valoracion     (Cap. 7)     U_pc -> U_pb
    balanceo       (Cap. 11)    RAS/biproporcional
    transformacion (Cap. 12)    SUT balanceado -> IOT simétrica (Modelo D/B)
    analisis       (Cap. 20)    A, L=(I-A)^-1, multiplicadores
"""
