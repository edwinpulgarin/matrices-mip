# Instrucciones de Descarga de COU por País

## BRASIL ✅ COMPLETADO (automático)
- **12 años disponibles: 2010–2021**
- 69 actividades × 128 productos
- MIPs y multiplicadores generados en `output/tablas/brasil/`

---

## ARGENTINA — Descarga manual (INDEC)

**Página oficial:**
https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-122

**Pasos:**
1. Ir a la URL de arriba
2. Buscar la sección **"Tablas de Recursos y Usos"** o **"TRU"**
3. Descargar los archivos `.xls` de cada año disponible
4. Guardar en: `data/raw/argentina/`
5. Renombrar como: `tru_2018.xls`, `tru_2019.xls`, etc.

**Años esperados:** 2004–2021
**Formato:** Excel (.xls o .xlsx)
**Unidad:** millones de pesos corrientes

**Alternativa si el sitio principal falla:**
- INDEC FTP: https://www.indec.gob.ar/ftp/cuadros/economia/cuentas_nacionales/
- También publicado en https://www.indec.gob.ar bajo Economía > Cuentas nacionales

---

## MÉXICO — Descarga manual (INEGI)

**Página oficial:**
https://www.inegi.org.mx/temas/mip/

**Pasos:**
1. Ir a la URL de arriba
2. Hacer clic en la pestaña **"Tabulados"** o **"Datos"**
3. Buscar **"Cuadro de Oferta"** y **"Cuadro de Utilización"** por año
4. Descargar los archivos Excel para:
   - **Serie base 2013:** años 2003–2020
   - **Serie base 2018:** años 2013–2020
5. Guardar en: `data/raw/mexico/`
6. Renombrar como: `cou_2018_b2013.xlsx`, `cou_2018_b2018.xlsx`, etc.

**Años esperados:** 2013–2020 (base 2013) y 2018–2020 (base 2018)
**Formato:** Excel (.xlsx)
**Número de actividades:** hasta 232 (SCIAN)

**Alternativa — Datos Abiertos:**
https://www.inegi.org.mx/programas/mip/2018/

---

## URUGUAY — Descarga manual (BCU)

**Página oficial:**
https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Paginas/Cuentas-Nacionales.aspx

**Pasos:**
1. Ir a la URL de arriba (puede dar error SSL en algunos navegadores — usar Chrome/Firefox)
2. Buscar la sección **"Cuadros de Oferta y Utilización"** o **"COU"**
3. Descargar los archivos disponibles (años 2012–2017)
4. Guardar en: `data/raw/uruguay/`
5. Renombrar como: `cou_2016.xlsx`, `cou_2017.xlsx`, etc.

**Años esperados:** 2012–2017
**Formato:** Excel (.xlsx)
**Número de actividades:** 95, productos: 110

---

## Una vez descargados los archivos

Ejecutar el pipeline:

```bash
py -3 -X utf8 main.py --pais argentina
py -3 -X utf8 main.py --pais mexico
py -3 -X utf8 main.py --pais uruguay

# O todos juntos:
py -3 -X utf8 main.py
```

Si el parser falla con algún archivo, ejecutar el diagnóstico:

```bash
py -3 -X utf8 src/descarga.py --diagnostico
```

Y reportar el error para ajustar el parser.
