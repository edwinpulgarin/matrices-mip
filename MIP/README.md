# Paquete de matrices insumo-producto por pais y anio

Esta carpeta contiene 35 Excel anuales procesados:

```text
MIP/
  Argentina/
  Brasil/
  Mexico/
  Uruguay/
```

Cada archivo anual esta simplificado para lectura y explicacion. La estructura es:

- `Indice`: portada con pais, anio, tipo de matriz, fuente y guia de hojas.
- `COU_Tabla_Original`: COU/fuente original. Cuando no hay COU publico separado, contiene notas de fuente.
- `V_oferta`: matriz de oferta/produccion por industria y producto.
- `q_produccion_producto`: vector de produccion/oferta total por producto.
- `U_nacional`: utilizacion intermedia nacional/domestica por producto e industria.
- `D_market_share`: matriz de participaciones `D = V * diag(q)^-1`.
- `Z_consumos_intermedios`: matriz `Z`, sector vendedor x sector comprador.
- `x_produccion_bruta`: vector `x` de produccion bruta y componentes disponibles.
- `y_demanda_final`: demanda final homologada como `DA = C + I + G + XN`, con `XN = X - M`.
- `X_hat`: matriz diagonal de produccion bruta, `diag(x)`.
- `A_coef_tecnicos`: coeficientes tecnicos, `A = Z * X_hat^-1`.
- `L_leontief`: inversa de Leontief, `L = (I - A)^-1`.
- `B_coef_distribucion`: coeficientes de distribucion de Ghosh, `B = X_hat^-1 * Z`.
- `G_ghosh_inversa`: inversa de Ghosh, `G = (I - B)^-1`.
- `encadenamientos`: encadenamientos hacia atras y adelante derivados de `L` y `G`.

En `y_demanda_final`, las columnas `C_consumo`, `I_inversion`, `G_gasto_publico`, `X_exportaciones` y `M_importaciones` se completan solo cuando existe fuente compatible. Si no hay desglose, el total queda en `sin_desglose_fuente`; no se imputa a un componente macro sin respaldo. La columna `diferencia_y_mip_menos_DA` deja visible la brecha entre el cierre sectorial de la MIP y la identidad homologada.

Las validaciones no se incluyen dentro de cada libro anual. Estan en la raiz del repositorio:

```text
validacion_matematica_mip.xlsx
validacion_matematica_mip.md
auditoria_cobertura_sectores_mip.xlsx
auditoria_cobertura_sectores_mip.md
```

Nota sectorial: un sector con `Z[i,i] = 0` no debe eliminarse automaticamente. La diagonal cero solo indica que el sector no se compra a si mismo en la fuente/transformacion. Si el sector tiene produccion, valor agregado, ventas, compras o demanda final, debe conservarse y documentarse.

Para regenerar la version simplificada despues de construir el paquete tecnico:

```powershell
py -3 -X utf8 Codigo\scripts\simplificar_excel_mip.py
```
