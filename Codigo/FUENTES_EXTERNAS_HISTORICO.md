# Fuentes externas revisadas para ampliar historico MIP

Fecha de revision: 2026-06-10

## Argentina

### Incorporado

- INDEC, biblioteca MIPAr97:
  - `https://sitioanterior.indec.gob.ar/informacion-de-archivo.asp`
  - `https://biblioteca.indec.gob.ar/cgi-bin/wxis.exe/iah/scripts/?IsisScript=iah.xis&base=minde&exprSearch=MATRIZ+INSUMO+PRODUCTO&indexSearch=DD&lang=es&nextAction=lnk`
  - `https://biblioteca.indec.gob.ar/bases/minde/mip_matriz12.xls`
  - `https://biblioteca.indec.gob.ar/bases/minde/mip_matriz13.xls`
  - `https://biblioteca.indec.gob.ar/bases/minde/mip_matriz14.xls`
  - `https://biblioteca.indec.gob.ar/bases/minde/mip_matriz16.xls`
- Resultado integrado:
  - `data/raw/argentina_mip97/`
  - `data/processed/argentina_mip97/mip_argentina_mip97_1997.xlsx`
  - `output/entregables/MIP_Argentina_1997.xlsx`

Nota metodologica: MIPAr97 es una MIP directa de INDEC, no un COU convertido por
el pipeline. Se mantiene como serie separada (`argentina_mip97`) para evitar
compararla directamente con los COU 2004 y 2018-2021 sin una tabla puente.

### No encontrado en fuente publica directa

- Argentina 2005-2017: no aparecen archivos COU/MIP oficiales descargables en
la carpeta publica revisada ni en los ZIP CEPAL disponibles localmente.
- La busqueda en paginas estatales de INDEC localizo documentacion y matrices
  de MIPAr97, pero no una serie anual posterior comparable entre 2005 y 2017.
- Recomendacion: mantener como brecha institucional. Requiere solicitud directa
a INDEC/CEPAL o acceso a series internas no publicadas.

## Brasil

### Incorporado

- CEPAL, repositorio COU/MIP:
  - `https://statistics.cepal.org/repository/cou-mip/index.html?lang=es`
  - Serie usada: Brasil base 2000, anos 2000-2009.
  - Resultado integrado:
    - `data/processed/brasil_early/cou_brasil_early_2000.xlsx` a `cou_brasil_early_2009.xlsx`
    - `data/processed/brasil_early/mip_brasil_early_2000.xlsx` a `mip_brasil_early_2009.xlsx`
    - `MIP/Brasil/MIP_Brasil_2000.xlsx` a `MIP_Brasil_2009.xlsx`
- IBGE, Sistema de Contas Nacionais / Tabelas de Recursos e Usos:
  - `https://www.ibge.gov.br/estatisticas/economicas/comercio/9052-sistema-de-contas-nacionais-brasil.html`
  - Serie usada: TRU nivel 68, anos 2010-2021.
  - Resultado integrado:
    - `data/processed/brasil/cou_brasil_2010.xlsx` a `cou_brasil_2021.xlsx`
    - `data/processed/brasil/mip_brasil_2010.xlsx` a `mip_brasil_2021.xlsx`
    - `MIP/Brasil/MIP_Brasil_2010.xlsx` a `MIP_Brasil_2021.xlsx`
- IBGE, Matriz de Insumo-Produto:
  - `https://www.ibge.gov.br/estatisticas/economicas/contas-nacionais/9085-matriz-de-insumo-produto.html`
  - Usada como referencia institucional/metodologica, no como fuente unica de toda la serie anual 2000-2021.

### Decisiones metodologicas aplicadas

- Brasil 2000-2009 se procesa como `brasil_early` porque usa estructura CEPAL/base 2000 y 51 actividades.
- Brasil 2010-2021 se procesa como `brasil` porque usa estructura IBGE nivel 68.
- En 2010-2021 se excluye `Total do produto` como actividad economica y se excluyen columnas agregadas `Demanda final` y `Demanda total` como componentes de demanda final.
- En 2000-2009 se alinean actividades por posicion para conservar las 51 actividades de la fuente.
- Los cierres menores aplicados en Brasil 2001-2006 quedan trazados en `ajuste_cierre` y `Z_pre_conciliacion`.

### Pendiente

- Brasil 2022+ no esta incorporado. Si se encuentra fuente detallada comparable, debe revisarse si conserva el mismo nivel de actividades, productos y puentes de valoracion antes de empalmarla.

## Mexico

### Confirmado en fuente estatal

- INEGI, Matriz de Insumo Producto:
  - `https://www.inegi.org.mx/programas/mip/2003/`
  - `https://www.inegi.org.mx/programas/mip/2008/`
  - `https://www.inegi.org.mx/programas/mip/2013/`
  - `https://www.inegi.org.mx/programas/mip/2018/`
- INEGI, Cuadros de Oferta y Utilizacion:
  - `https://www.inegi.org.mx/programas/cou/2013/`
  - `https://www.inegi.org.mx/programas/coue/2013/`
- Metodologia MIP 2018:
  - `https://www.inegi.org.mx/contenidos/programas/mip/2018/doc/met_cab2018.pdf`

### Estado actual

- Integrado:
  - 2003, 2008, 2013 y 2018.
- El manual de correccion de estilo de INEGI documenta la referencia oficial al
  ZIP de datos abiertos 2018:
  - `https://www.inegi.org.mx/contenidos/programas/mip/2018/datosabiertos/mip_csv.zip`
- No se localizo, en busqueda publica estatal, una pagina o ZIP oficial de MIP
  nacional 2023 listo para incorporar.
- COU/COUE pueden servir para analisis complementario, pero no sustituyen una
  MIP nacional directa adicional sin convertir y validar supuestos.

## Uruguay

### Revisado localmente

- `data/raw/uruguay/URY_COU_2005_2016.zip`
  - 2005-2008: COU anual agregado, 20 columnas. No tiene desagregacion sectorial
    comparable con las MIPs actuales.
  - 2012 y 2016: archivos de produccion por industria, pero no incluyen el
    bloque completo de utilizacion intermedia necesario para construir una MIP.
- `data/raw/uruguay/URY_COU_2017.zip` y carpeta `cou_2017/`
  - Ya integrado como `uruguay_cou` 2017.
- `mip_producto_detallada_2016.xlsx` y `leontief_producto_2016.xlsx`
  - Ya integrado como `uruguay` 2016.

### Fuentes externas revisadas

- Banco Central del Uruguay, Cuentas Nacionales / COU:
  - `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Cuentas-Nacionales.aspx`
  - `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/COU.aspx`
- Banco Central del Uruguay, MIP:
  - `https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Matriz-Insumo-Producto.aspx`
  - `https://www.bcu.gub.uy/Comunicaciones/Paginas/Detalle-Noticia.aspx?noticia=208&title=El-BCU-presenta-una-herramienta-estad%C3%ADstica-que-contribuye-al-an%C3%A1lisis-econ%C3%B3mico-y-la-evaluaci%C3%B3n-de-pol%C3%ADticas`
- Documentacion metodologica BCU localizada, pero sin matrices detalladas
  descargables suficientes para incorporar 2018+ en este pipeline.
- La pagina oficial de MIP del BCU lista productos solo para el periodo 2016.

### Recomendacion

- Mantener Uruguay en dos entregables:
  - `MIP_Uruguay_2016.xlsx` (MIP directa BCU)
  - `MIP_Uruguay_2017.xlsx` (COU CEPAL convertido)
- Uruguay 2018+ debe tratarse como brecha institucional hasta conseguir archivos
  detallados de produccion, utilizacion intermedia y demanda final por producto
  y actividad.
