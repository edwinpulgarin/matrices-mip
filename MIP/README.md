# Paquete de matrices insumo-producto por pais y anio

Esta carpeta contiene 36 Excel anuales auditables:

```text
MIP/
  Argentina/
  Brasil/
  Mexico/
  Uruguay/
```

Cada archivo anual esta organizado con diseno institucional CEPAL, inspirado en el anexo MIP de Colombia. La estructura es:

- `Indice`: portada con pais, anio, tipo de matriz, fuente y resumen de validaciones.
- `Cuadro 1`: matriz actividad x actividad nacional/domestica.
- `Cuadro 2`: matriz importada o ajuste intermedio fuera de `Z`.
- `Cuadro 3`: matriz total auditable, con demanda final, ajuste, valor agregado, produccion total y check contra produccion fuente.
- `Cuadro 4`: multiplicadores de Leontief/Ghosh y validacion contable.
- `Notas`: convenciones, fuente y advertencias metodologicas.

En `Cuadro 3`, los componentes de demanda final se completan solo cuando existe fuente compatible. Si no hay desglose, el total queda en `Sin desglose fuente`; no se imputa a un componente macro sin respaldo. Las diferencias de cierre y los ajustes intermedios quedan visibles en el mismo cuadro.

Las validaciones no se incluyen dentro de cada libro anual. Estan en la raiz del repositorio:

```text
validacion_matematica_mip.xlsx
validacion_matematica_mip.md
validacion_inversa_mip.xlsx
validacion_inversa_mip.md
auditoria_cobertura_sectores_mip.xlsx
auditoria_cobertura_sectores_mip.md
```

Nota sectorial: un sector con `Z[i,i] = 0` no debe eliminarse automaticamente. La diagonal cero solo indica que el sector no se compra a si mismo en la fuente/transformacion. Si el sector tiene produccion, valor agregado, ventas, compras o demanda final, debe conservarse y documentarse.

Para regenerar la version auditable despues de construir el paquete tecnico completo:

```powershell
py -3 -X utf8 Codigo\scripts\generar_matrices_auditables.py
```
