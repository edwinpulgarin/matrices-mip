# Codigo del pipeline MIP CEPAL

Esta carpeta contiene el codigo necesario para regenerar las matrices desde las fuentes locales.

## Estructura

- `main.py`: entrada principal del pipeline.
- `src/`: conversion COU a MIP, multiplicadores y parsers por pais.
- `scripts/`: validacion, generacion de Excel y armado de paquetes.
- `docs/`: metodologia del pipeline.
- `FUENTES_EXTERNAS_HISTORICO.md`: fuentes oficiales revisadas, incorporadas y pendientes.
- `INSTRUCCIONES_DESCARGA.md`: rutas esperadas y paginas oficiales para reponer `data/raw`.

## Uso basico

```text
python main.py --pais argentina
python main.py --pais brasil
python main.py --pais mexico
python main.py --pais uruguay
python scripts/validar_mips.py
python scripts/validar_mip_inversa.py
python scripts/generar_paquete_matrices.py
python scripts/generar_matrices_auditables.py
python scripts/generar_matrices_colombia_auditables.py
python scripts/simplificar_excel_mip.py
python scripts/crear_paquete_drive.py
```

Nota: esta carpeta no incluye `data/raw` ni archivos fuente pesados. Es codigo y documentacion del pipeline.

Para contexto de colaboracion, leer primero `../CLAUDE_HANDOFF.md`.
