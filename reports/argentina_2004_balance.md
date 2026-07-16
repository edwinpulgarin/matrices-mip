# Piloto Argentina 2004 — Reconstrucción MIP (UN Handbook F74 Rev.1)

Unidades: miles de millones de pesos corrientes.

## Insumo (COU crudo)
- Productos: 271 · Industrias: 162
- Producción bruta (VBP pb): 834.6
- Consumo intermedio doméstico (pb): 356.9
- Importaciones intermedias: 40.8
- Impuestos netos a productos: 24.5
- Valor agregado bruto: 412.4
- Demanda final doméstica: 477.4

## Gates de identidades contables
| Etapa (capítulo) | Identidad | Error relativo | |
|---|---|---|---|
| Valoración (Cap. 7) | balance industria `g=IC+M+T+VA` | 8.59e-16 | ✅ |
| Balanceo (Cap. 11) | balance producto oferta=uso | 4.80e-16 | ✅ |
| Balanceo (Cap. 11) | balance industria | 2.70e-16 | ✅ |
| Transformación (Cap. 12) | **IOT fila = columna** | 9.42e-16 | ✅ |
| Análisis (Cap. 20) | Leontief `L·f = x` | 2.68e-17 | ✅ |
| Transformación (Cap. 12) | sin negativos en Z/VA | min=0.000 | ✅ |
| Análisis (Cap. 20) | inversa de Leontief `L≥0` | min=0.000 | ✅ |

## Multiplicadores de producción (encadenamiento hacia atrás)
- min=1.00 · media=1.76 · max=2.67
- Top 5:
  - Preparacion de fibras animales de uso textil;: 2.67
  - Matanza de ganado y procesamiento de su carne: 2.56
  - Curtido y terminacion de cueros; fabricacion : 2.49
  - Elaboración de aceites y grasas de origen veg: 2.41
  - Elaboración de productos lácteos: 2.34