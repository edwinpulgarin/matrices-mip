"""
Descarga de Cuadros de Oferta y Utilización (COU) desde fuentes oficiales.

Fuentes:
    Argentina : INDEC — Tablas de Recursos y Usos (TRU)
    Brasil    : IBGE  — Tabelas de Recursos e Usos, nivel 68 (ZIP con serie completa)
    México    : INEGI — Cuadros de Oferta y Utilización (COU)
    Uruguay   : BCU   — Cuadros de Oferta y Utilización

Uso:
    py -3 src/descarga.py --pais todos
    py -3 src/descarga.py --pais brasil
    py -3 src/descarga.py --diagnostico
"""

import sys
import time
import zipfile
import argparse
import requests
from pathlib import Path
from tqdm import tqdm

ROOT     = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
}


# ═════════════════════════════════════════════════════════════════════════════
# CATÁLOGOS DE DESCARGA
# Cada entrada: (año, url, nombre_local)
# año=0 indica que el archivo contiene múltiples años (ZIP de serie)
# ═════════════════════════════════════════════════════════════════════════════

# ── ARGENTINA (INDEC) ─────────────────────────────────────────────────────────
# TRU publicadas anualmente. El INDEC usa el patrón:
#   /ftp/cuadros/economia/cuentas_nacionales/tru/tru_AAAA_baseAAAA.xls
# Fuente: https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-122
# NOTA: Los años 2017-2021 pueden tener nombre diferente. Si fallan, el script
#       muestra las URLs para verificación manual en el sitio del INDEC.
_AR = "https://www.indec.gob.ar/ftp/cuadros/economia/cuentas_nacionales/tru"
ARGENTINA_CATALOGO = [
    (2004, f"{_AR}/tru_2004_base2004.xls",  "tru_2004.xls"),
    (2005, f"{_AR}/tru_2005_base2004.xls",  "tru_2005.xls"),
    (2006, f"{_AR}/tru_2006_base2004.xls",  "tru_2006.xls"),
    (2007, f"{_AR}/tru_2007_base2004.xls",  "tru_2007.xls"),
    (2008, f"{_AR}/tru_2008_base2004.xls",  "tru_2008.xls"),
    (2009, f"{_AR}/tru_2009_base2004.xls",  "tru_2009.xls"),
    (2010, f"{_AR}/tru_2010_base2004.xls",  "tru_2010.xls"),
    (2011, f"{_AR}/tru_2011_base2004.xls",  "tru_2011.xls"),
    (2012, f"{_AR}/tru_2012_base2004.xls",  "tru_2012.xls"),
    (2013, f"{_AR}/tru_2013_base2004.xls",  "tru_2013.xls"),
    (2014, f"{_AR}/tru_2014_base2004.xls",  "tru_2014.xls"),
    (2015, f"{_AR}/tru_2015_base2004.xls",  "tru_2015.xls"),
    (2016, f"{_AR}/tru_2016_base2004.xls",  "tru_2016.xls"),
    # 2017-2021: el INDEC cambió el año base. Probar varios patrones:
    (2017, f"{_AR}/tru_2017_base2004.xls",  "tru_2017.xls"),
    (2018, f"{_AR}/tru_2018_base2004.xls",  "tru_2018.xls"),
    (2019, f"{_AR}/tru_2019_base2004.xls",  "tru_2019.xls"),
    (2020, f"{_AR}/tru_2020_base2004.xls",  "tru_2020.xls"),
    (2021, f"{_AR}/tru_2021_base2004.xls",  "tru_2021.xls"),
]
# URLs alternativas a probar si fallan las anteriores (mismo año, distinto nombre)
ARGENTINA_ALTERNATIVAS = {
    2017: [f"{_AR}/tru_2017.xls", f"{_AR}/tru_2017_revisada.xls"],
    2018: [f"{_AR}/tru_2018.xls", f"{_AR}/tru_2018_revisada.xls"],
    2019: [f"{_AR}/tru_2019.xls"],
    2020: [f"{_AR}/tru_2020.xls"],
    2021: [f"{_AR}/tru_2021.xls"],
}

# ── BRASIL (IBGE) ─────────────────────────────────────────────────────────────
# El IBGE publica las TRU nivel 68 (68 atividades) en UN SOLO ZIP que contiene
# todos los años 2010-2021.
# URL verificada: ftp.ibge.gov.br (acceso público sin autenticación)
_BR = "https://ftp.ibge.gov.br/Contas_Nacionais/Sistema_de_Contas_Nacionais"
BRASIL_CATALOGO = [
    # año=0 → archivo ZIP con múltiples años; se extrae automáticamente
    (0, f"{_BR}/2021/tabelas_xls/tabelas_de_recursos_e_usos/nivel_68_2010_2021_xls.zip",
        "nivel_68_2010_2021.zip"),
]

# ── MÉXICO (INEGI) ────────────────────────────────────────────────────────────
# Los COU se publican en el portal de Datos Abiertos del INEGI.
# Base 2013: serie 2003-2020 (con nomenclatura SCIAN hasta 262 actividades)
# Base 2018: serie 2013-2020 (actualización de año base)
# NOTA: Las URLs exactas del INEGI cambian frecuentemente. Se incluyen las
#       más probables; si fallan, verificar en https://www.inegi.org.mx/temas/mip/
_MX = "https://www.inegi.org.mx/contenidos/programas/mip"
MEXICO_CATALOGO = [
    # Base 2013
    (2013, f"{_MX}/2013/datosabiertos/cou_oferb2013_2013.xlsx",  "cou_2013_b2013.xlsx"),
    (2014, f"{_MX}/2013/datosabiertos/cou_oferb2013_2014.xlsx",  "cou_2014_b2013.xlsx"),
    (2015, f"{_MX}/2013/datosabiertos/cou_oferb2013_2015.xlsx",  "cou_2015_b2013.xlsx"),
    (2016, f"{_MX}/2013/datosabiertos/cou_oferb2013_2016.xlsx",  "cou_2016_b2013.xlsx"),
    (2017, f"{_MX}/2013/datosabiertos/cou_oferb2013_2017.xlsx",  "cou_2017_b2013.xlsx"),
    (2018, f"{_MX}/2013/datosabiertos/cou_oferb2013_2018.xlsx",  "cou_2018_b2013.xlsx"),
    (2019, f"{_MX}/2013/datosabiertos/cou_oferb2013_2019.xlsx",  "cou_2019_b2013.xlsx"),
    (2020, f"{_MX}/2013/datosabiertos/cou_oferb2013_2020.xlsx",  "cou_2020_b2013.xlsx"),
    # Base 2018
    (2018, f"{_MX}/2018/datosabiertos/cou_oferb2018_2018.xlsx",  "cou_2018_b2018.xlsx"),
    (2019, f"{_MX}/2018/datosabiertos/cou_oferb2018_2019.xlsx",  "cou_2019_b2018.xlsx"),
    (2020, f"{_MX}/2018/datosabiertos/cou_oferb2018_2020.xlsx",  "cou_2020_b2018.xlsx"),
]

# ── URUGUAY (BCU) ─────────────────────────────────────────────────────────────
# Los COU del BCU están disponibles en su sitio pero con certificado SSL
# no estándar. Se intenta con http y https; si falla, descarga manual.
# Años disponibles: 2012-2017 (base 2016)
# Fuente: https://www.bcu.gub.uy → Estadísticas → Cuentas Nacionales
_UY_HTTPS = "https://www.bcu.gub.uy/Estadisticas-e-Indicadores/Documentos%20de%20Cuentas%20Nacionales"
_UY_HTTP  = "http://www.bcu.gub.uy/Estadisticas-e-Indicadores/Documentos%20de%20Cuentas%20Nacionales"
URUGUAY_CATALOGO = [
    (2012, f"{_UY_HTTPS}/cou_2012.xlsx", "cou_2012.xlsx"),
    (2013, f"{_UY_HTTPS}/cou_2013.xlsx", "cou_2013.xlsx"),
    (2014, f"{_UY_HTTPS}/cou_2014.xlsx", "cou_2014.xlsx"),
    (2015, f"{_UY_HTTPS}/cou_2015.xlsx", "cou_2015.xlsx"),
    (2016, f"{_UY_HTTPS}/cou_2016.xlsx", "cou_2016.xlsx"),
    (2017, f"{_UY_HTTPS}/cou_2017.xlsx", "cou_2017.xlsx"),
]

CATALOGOS = {
    'argentina': ARGENTINA_CATALOGO,
    'brasil':    BRASIL_CATALOGO,
    'mexico':    MEXICO_CATALOGO,
    'uruguay':   URUGUAY_CATALOGO,
}


# ═════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE DESCARGA
# ═════════════════════════════════════════════════════════════════════════════

def descargar_archivo(url: str, destino: Path,
                      reintentos: int = 3, pausa: float = 1.5,
                      verify_ssl: bool = True) -> bool:
    """Descarga url → destino. Retorna True si exitoso."""
    if destino.exists() and destino.stat().st_size > 1000:
        print(f"    [EXISTE] {destino.name}")
        return True

    for intento in range(1, reintentos + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=120,
                                stream=True, verify=verify_ssl)
            resp.raise_for_status()

            total = int(resp.headers.get('content-length', 0))
            destino.parent.mkdir(parents=True, exist_ok=True)

            with open(destino, 'wb') as f, tqdm(
                total=total, unit='B', unit_scale=True,
                desc=f"    {destino.name}", leave=False
            ) as barra:
                for chunk in resp.iter_content(chunk_size=65536):
                    f.write(chunk)
                    barra.update(len(chunk))

            if destino.stat().st_size > 1000:
                print(f"    [OK] {destino.name}  ({destino.stat().st_size/1024:.0f} KB)")
                time.sleep(pausa)
                return True
            else:
                destino.unlink()
                print(f"    [VACÍO] {destino.name} — archivo demasiado pequeño")
                return False

        except requests.HTTPError as e:
            print(f"    [HTTP {e.response.status_code}] {destino.name} — intento {intento}/{reintentos}")
        except requests.SSLError:
            if verify_ssl:
                print(f"    [SSL] Reintentando sin verificación SSL...")
                return descargar_archivo(url, destino, reintentos, pausa, verify_ssl=False)
        except requests.ConnectionError:
            print(f"    [RED] {destino.name} — intento {intento}/{reintentos}")
        except Exception as e:
            print(f"    [ERROR] {destino.name}: {e}")

        if intento < reintentos:
            time.sleep(pausa * 2)

    return False


def extraer_zip(ruta_zip: Path, carpeta_destino: Path) -> list:
    """
    Extrae un ZIP y retorna lista de archivos extraídos.
    Salta archivos que ya existen.
    """
    extraidos = []
    try:
        with zipfile.ZipFile(ruta_zip, 'r') as zf:
            for nombre in zf.namelist():
                if nombre.endswith('/'):
                    continue
                destino = carpeta_destino / Path(nombre).name
                if destino.exists() and destino.stat().st_size > 1000:
                    print(f"    [EXISTE] {destino.name}")
                else:
                    data = zf.read(nombre)
                    destino.write_bytes(data)
                    print(f"    [EXTRAÍDO] {destino.name}  ({len(data)/1024:.0f} KB)")
                extraidos.append(destino)
    except zipfile.BadZipFile:
        print(f"    [ERROR] {ruta_zip.name} no es un ZIP válido")
    return extraidos


def descargar_pais(pais: str, catalogo: list) -> dict:
    """
    Descarga todos los archivos de un país.
    Para Brasil, descarga el ZIP y lo extrae automáticamente.
    Retorna {año: Path} con archivos disponibles al final.
    """
    carpeta = DATA_RAW / pais
    carpeta.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  País: {pais.upper()}")
    print(f"  Destino: {carpeta}")
    print(f"{'='*60}")

    descargados = {}
    fallidos    = []

    # Intentos alternativos para Argentina (años 2017-2021)
    alternativas = ARGENTINA_ALTERNATIVAS if pais == 'argentina' else {}

    for ano, url, nombre in catalogo:
        destino = carpeta / nombre
        ok = descargar_archivo(url, destino)

        # Si falla y hay alternativas, probarlas
        if not ok and ano in alternativas:
            for url_alt in alternativas[ano]:
                print(f"    [ALTERNATIVA] Probando: {url_alt.split('/')[-1]}")
                ok = descargar_archivo(url_alt, destino)
                if ok:
                    break

        if ok:
            # Para ZIPs (Brasil): extraer automáticamente
            if destino.suffix == '.zip':
                print(f"  Extrayendo {destino.name}...")
                archivos = extraer_zip(destino, carpeta)
                for arch in archivos:
                    # Intentar inferir año desde el nombre
                    for y in range(2000, 2025):
                        if str(y) in arch.name:
                            descargados[y] = arch
                            break
            else:
                descargados[ano] = destino
        else:
            fallidos.append((ano, nombre, url))

    print(f"\n  Resultado {pais}: {len(descargados)} años disponibles, {len(fallidos)} fallidos")

    if fallidos:
        print(f"\n  ── Archivos no descargados ──────────────────────────────")
        print(f"  Por favor, descargar manualmente y guardar en:")
        print(f"  {carpeta}")
        for ano, nombre, url in fallidos:
            if ano > 0:
                print(f"\n    Año {ano} → {nombre}")
                print(f"    URL a probar: {url}")
        if pais == 'argentina':
            print(f"\n  Página INDEC: https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-122")
        elif pais == 'mexico':
            print(f"\n  Página INEGI: https://www.inegi.org.mx/temas/mip/")
        elif pais == 'uruguay':
            print(f"\n  Página BCU: https://www.bcu.gub.uy → Estadísticas → Cuentas Nacionales")

    return descargados


def diagnostico():
    """Muestra qué archivos ya están descargados."""
    print("\n── Estado actual ───────────────────────────────────────────")
    for pais in ['argentina', 'brasil', 'mexico', 'uruguay']:
        carpeta = DATA_RAW / pais
        if not carpeta.exists():
            print(f"  {pais:12s}: carpeta no existe")
            continue
        archivos = [f for f in carpeta.iterdir()
                    if f.suffix in ('.xls', '.xlsx') and f.stat().st_size > 1000]
        anios = sorted(set(
            int(y) for f in archivos
            for y in [str(n) for n in range(2000, 2025)]
            if y in f.name
        ))
        print(f"  {pais:12s}: {len(archivos)} archivos — años: {anios if anios else 'ninguno'}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Descarga COU de Argentina, Brasil, México y Uruguay"
    )
    parser.add_argument('--pais', default='todos',
                        choices=['argentina', 'brasil', 'mexico', 'uruguay', 'todos'])
    parser.add_argument('--diagnostico', action='store_true')
    args = parser.parse_args()

    if args.diagnostico:
        diagnostico()
        sys.exit(0)

    paises = list(CATALOGOS.keys()) if args.pais == 'todos' else [args.pais]
    for pais in paises:
        descargar_pais(pais, CATALOGOS[pais])

    print("\n══ Descarga finalizada ═══════════════════════════════════")
    diagnostico()
