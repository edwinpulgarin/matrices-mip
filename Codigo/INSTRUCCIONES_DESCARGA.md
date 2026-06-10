# Instrucciones de descarga de fuentes

Este repositorio publico contiene entregables, codigo y documentacion. No incluye necesariamente los archivos pesados de `data/raw` ni todos los intermedios de `data/processed`. Para regenerar la base desde cero se requiere reponer las fuentes oficiales en el workspace completo.

## Estructura esperada

```text
data/
  raw/
    argentina/
    argentina_mip97/
    brasil/
    mexico/
    uruguay/
  processed/
```

Despues de descargar o reponer fuentes, ejecutar desde la raiz del workspace completo:

```powershell
py -3 -X utf8 main.py
py -3 -X utf8 scripts\validar_mips.py
py -3 -X utf8 scripts\generar_paquete_matrices.py
py -3 -X utf8 scripts\auditar_cobertura_matrices.py
```

## Argentina

Fuentes oficiales:

- INDEC, COU: `https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-114`
- INDEC, pagina historica: `https://sitioanterior.indec.gob.ar/informacion-de-archivo.asp`
- INDEC, biblioteca MIPAr97:
  - `https://biblioteca.indec.gob.ar/cgi-bin/wxis.exe/iah/scripts/?IsisScript=iah.xis&base=minde&exprSearch=MATRIZ+INSUMO+PRODUCTO&indexSearch=DD&lang=es&nextAction=lnk`

Uso actual:

- Argentina 1997: MIPAr97 directa.
- Argentina 2004 y 2018-2021: COU/TRU procesado y convertido a MIP.

Rutas esperadas:

```text
data/raw/argentina/
data/raw/argentina_mip97/
```

Notas:

- No se incorporaron anos 2005-2017 por falta de fuente publica comparable localizada.
- Si se consigue nueva fuente, registrar URL, fecha, archivo descargado y cambios de parser.

## Brasil

Fuentes oficiales y de referencia:

- CEPAL, repositorio COU/MIP: `https://statistics.cepal.org/repository/cou-mip/index.html?lang=es`
- IBGE, Sistema de Contas Nacionais / TRU: `https://www.ibge.gov.br/estatisticas/economicas/comercio/9052-sistema-de-contas-nacionais-brasil.html`
- IBGE, Matriz de Insumo-Produto: `https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9085-matriz-de-insumo-produto.html`

Uso actual:

- Brasil 2000-2009: `brasil_early`, COU CEPAL Brasil base 2000, 51 actividades.
- Brasil 2010-2021: `brasil`, TRU/COU IBGE nivel 68.

Ruta esperada:

```text
data/raw/brasil/
```

Notas:

- Los parsers de 2000-2009 y 2010-2021 son distintos.
- No empalmar Brasil 2022+ sin revisar nivel de productos, actividades y valoracion.

## Mexico

Fuentes oficiales:

- INEGI, MIP general: `https://www.inegi.org.mx/temas/mip/`
- INEGI, MIP 2003: `https://www.inegi.org.mx/programas/mip/2003/`
- INEGI, MIP 2008: `https://www.inegi.org.mx/programas/mip/2008/`
- INEGI, MIP 2013: `https://www.inegi.org.mx/programas/mip/2013/`
- INEGI, MIP 2018: `https://www.inegi.org.mx/programas/mip/2018/`

Uso actual:

- Mexico 2003, 2008, 2013 y 2018 son MIP directas o equivalentes de fuente.

Ruta esperada:

```text
data/raw/mexico/
```

Notas:

- No se localizo una MIP nacional 2023 lista para incorporar al mismo nivel en esta version.
- COU/COUE pueden servir para analisis complementario, pero no reemplazan automaticamente una MIP directa sin reconstruccion y validacion.

## Uruguay

Fuentes oficiales y de referencia:

- BCU, Cuentas Nacionales: `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Cuentas-Nacionales.aspx`
- BCU, COU: `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/COU.aspx`
- BCU, MIP: `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Matriz-Insumo-Producto.aspx`
- CEPAL, repositorio COU/MIP: `https://statistics.cepal.org/repository/cou-mip/index.html?lang=es`

Uso actual:

- Uruguay 2016: MIP directa BCU.
- Uruguay 2017: COU detallado convertido a MIP.

Ruta esperada:

```text
data/raw/uruguay/
```

Notas:

- Uruguay 2017 sigue como caso metodologico sensible porque no se identifico MIP directa equivalente y los negativos remanentes son materiales.
- Uruguay 2018+ debe tratarse como brecha hasta conseguir MIP directa o COU suficientemente detallado.

## Despues de descargar

Verificar que cada nueva fuente quede documentada en:

- `Codigo/FUENTES_EXTERNAS_HISTORICO.md`
- `CLAUDE_HANDOFF.md`
- `METODOLOGIA.md`, si cambia el metodo
- `fuente_resumen` y `fuente_notas`, despues de regenerar los Excel anuales

No subir una matriz nueva sin correr:

```powershell
py -3 -X utf8 scripts\validar_mips.py
py -3 -X utf8 scripts\generar_paquete_matrices.py
py -3 -X utf8 scripts\auditar_cobertura_matrices.py
```
