# Paquete de matrices insumo-producto por pais y anio

Esta carpeta contiene un Excel por pais y por anio procesado. La estructura es:

```text
MIP/
  Argentina/
  Brasil/
  Mexico/
  Uruguay/
```

Cada archivo anual contiene:

- `README`: metadatos, fuente y definiciones.
- `fuente_resumen`: fuente utilizada, tipo de matriz, archivo COU procesado cuando aplica y dimensiones de las hojas fuente.
- `cobertura_sectores`: auditoria de sectores; compara actividades del COU contra sectores de la MIP final y marca sectores con diagonal cero.
- `cobertura_productos`: auditoria de productos COU; recuerda que productos no son necesariamente sectores y se transforman con `D_market_share`.
- `fuente_notas`: notas metodologicas generadas durante el procesamiento.
- `src_*`: hojas fuente COU incorporadas cuando la matriz fue reconstruida (`src_V_oferta`, `src_U_utilizacion`, `src_Y_demanda_final`, etc.).
- `Z_MIP`: matriz de flujos intermedios sector x sector.
- `A_coef_tecnicos`: coeficientes tecnicos de Leontief, `A = Z * diag(g)^-1`.
- `L_leontief`: inversa de Leontief, `L = (I - A)^-1`.
- `B_ghosh_coef`: coeficientes de distribucion de Ghosh, `B = diag(g)^-1 * Z`.
- `G_ghosh_inversa`: inversa de Ghosh, `G = (I - B)^-1`.
- `g_produccion`: produccion bruta sectorial.
- `W_valor_agregado`: valor agregado sectorial.
- `multiplicadores`: multiplicadores Leontief y Ghosh por sector.
- `ajuste_intermedio`: ajuste fuera de `Z`; en MIP directas puede ser CI importado y en COU reconstruidos puede incluir importaciones, margenes, impuestos y diferencias de valoracion comprador-basico.
- `ajuste_cierre`: cuando aplica, traza la conciliacion menor de demanda final negativa aprobada para Brasil 2000-2009 y Uruguay 2016.
- `Z_pre_conciliacion`: cuando aplica, matriz `Z` antes de la conciliacion menor.
- `balances_sectoriales`: compras intermedias, ventas intermedias, valor agregado residual y demanda final residual.
- `validacion_resumen`: pruebas matematicas principales.
- `val_A_menos_Zg`: residual de `A - Z/g`.
- `val_Leontief`: residual de `(I - A)L - I`.
- `val_Ghosh`: residual de `(I - B)G - I`.

Nota sectorial: un sector con `Z[i,i] = 0` no debe eliminarse automaticamente. La diagonal cero solo indica que el sector no se compra a si mismo en la fuente/transformacion. Si el sector tiene produccion, valor agregado, ventas, compras o demanda final, debe conservarse y documentarse.

El paquete se regenera con:

```powershell
py -3 -X utf8 Codigo\scripts\generar_paquete_matrices.py
```
