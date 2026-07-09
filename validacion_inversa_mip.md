# Validacion inversa MIP

Esta auditoria reconstruye MIP desde los COU procesados y compara contra las MIP guardadas u oficiales cuando existe un par comparable.

Casos inventariados: 36
Estados para Z domestica: {'BENCHMARK_FUERTE': 2, 'NO_COMPARABLE': 1, 'OK_CON_AJUSTE_CIERRE': 6, 'OK_REPRODUCE': 24}

## Benchmarks contra MIP directas
- Mexico 2008: BENCHMARK_FUERTE; WMAPE=3.84%, corr=0.999855, cobertura=100.0%.
- Mexico 2013: BENCHMARK_FUERTE; WMAPE=3.21%, corr=0.999765, cobertura=100.0%.
- Uruguay 2016: no comparable (COU usado: data\processed\uruguay\couref_uruguay_2016.xlsx; MIP guardada contiene ajuste_cierre/Z_pre_conciliacion; [AVISO] Desbalance maximo: 223,751.8 (209.27%)).

## Roundtrip de MIP reconstruidas
- Resumen: {'OK_CON_AJUSTE_CIERRE': 6, 'OK_REPRODUCE': 24}
- Brasil 2001: OK_CON_AJUSTE_CIERRE; WMAPE=0.1365%, max_abs=63.1063.
- Brasil 2002: OK_CON_AJUSTE_CIERRE; WMAPE=0.1200%, max_abs=68.2057.
- Brasil 2003: OK_CON_AJUSTE_CIERRE; WMAPE=0.0178%, max_abs=25.4841.
- Brasil 2004: OK_CON_AJUSTE_CIERRE; WMAPE=0.0055%, max_abs=5.2872.
- Brasil 2005: OK_CON_AJUSTE_CIERRE; WMAPE=0.0082%, max_abs=11.4102.
- Brasil 2006: OK_CON_AJUSTE_CIERRE; WMAPE=0.0101%, max_abs=16.9995.

## Casos no comparables
- Argentina 1997: sin_cou_para_prueba_inversa.
- Mexico 2003: sin_cou_para_prueba_inversa.
- Mexico 2018: sin_cou_para_prueba_inversa.

Archivos generados:
- `output\tablas\validacion_inversa_mip.xlsx`
- `output\tablas\validacion_inversa_mip.md`
