"""
Pipeline principal: COU → MIP → Multiplicadores

Uso:
    # 1. Descargar datos
    py -3 src/descarga.py --pais todos

    # 2. Procesar todos los países y años
    py -3 main.py

    # 3. Solo un país
    py -3 main.py --pais argentina

    # 4. Solo un año específico
    py -3 main.py --pais brasil --anio 2018
"""

import sys
import argparse
import warnings
import traceback
import numpy as np
import pandas as pd
from pathlib import Path

warnings.filterwarnings('ignore', category=UserWarning)

# ── Rutas ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent
SRC        = ROOT / "src"
DATA_RAW   = ROOT / "data" / "raw"
DATA_PROC  = ROOT / "data" / "processed"
OUTPUT_TAB = ROOT / "output" / "tablas"
OUTPUT_GRA = ROOT / "output" / "graficos"

sys.path.insert(0, str(ROOT))

from src.parsers import argentina, argentina_mip97, brasil, mexico, uruguay
from src.parsers import mexico_mip, uruguay_mip, uruguay_cou, brasil_early
from src.cou_to_mip import sut_a_iot_industria, verificar_leontief, ras
from src.multiplicadores import tabla_multiplicadores_completa, clasificar_sectores

# ── Configuración por país ────────────────────────────────────────────────────
# 'modo_brasil': True  → el parser recibe carpeta+anio (dos archivos tab1/tab2)
#               False → recibe una sola ruta de archivo
# 'modo_mip'  : True  → el parser ya devuelve un dict con Z, A, L, g
#               (no pasa por sut_a_iot_industria)
#               El parser recibe (ruta_zip, anio, verbose) para México
#               o (carpeta, anio, verbose) para Uruguay
CONFIG = {
    'argentina': {
        'parser'      : argentina.parsear,
        'carpeta'     : DATA_RAW / 'argentina',
        'anios'       : list(range(2004, 2022)),
        'moneda'      : 'ARS',
        'exts'        : ['.xls', '.xlsx'],
        'modo_brasil' : False,
        'modo_mip'    : False,
    },
    'argentina_mip97': {
        'parser'      : argentina_mip97.parsear,
        'carpeta'     : DATA_RAW / 'argentina_mip97',
        'anios'       : [1997],
        'moneda'      : 'ARS',
        'modo_mip'    : True,
        'modo_carpeta': True,
    },
    'brasil': {
        'parser'      : brasil.parsear,
        'carpeta'     : DATA_RAW / 'brasil',
        'anios'       : list(range(2010, 2022)),
        'moneda'      : 'BRL',
        'exts'        : ['.xls', '.xlsx'],
        'modo_brasil' : True,   # usa carpeta+anio con 68_tab1/tab2
        'modo_mip'    : False,
    },
    'mexico': {
        'parser'      : mexico_mip.parsear,
        'carpeta'     : DATA_RAW / 'mexico',
        'anios'       : [2003, 2008, 2013, 2018],
        'moneda'      : 'MXN',
        'modo_mip'    : True,   # MIP ya construida por INEGI/CEPAL
        # 2003: MEX_MIP_2003.zip (CEPAL Excel IxI 20x20)
        # 2008: MEX_MIP_2008.zip (CEPAL Excel IxI)
        # 2013: mip_2013_csv.zip (INEGI CSV)
        # 2018: mip_2018_csv.zip (INEGI CSV)
        'zip_patron'  : {
            2003: 'MEX_MIP_2003.zip',
            2008: 'MEX_MIP_2008.zip',
            2013: 'mip_2013_csv.zip',
            2018: 'mip_2018_csv.zip',
        },
    },
    'brasil_early': {
        'parser'      : brasil_early.parsear,
        'carpeta'     : DATA_RAW / 'brasil',
        'anios'       : list(range(2000, 2010)),
        'moneda'      : 'BRL',
        'modo_mip'    : False,
        'modo_carpeta': True,   # parser recibe (carpeta, anio)
    },
    'uruguay': {
        'parser'      : uruguay_mip.parsear,
        'carpeta'     : DATA_RAW / 'uruguay',
        'anios'       : [2016],
        'moneda'      : 'UYU',
        'modo_mip'    : True,   # MIP ya construida por BCU
        'modo_carpeta': True,   # el parser recibe carpeta (no archivo)
    },
    'uruguay_cou': {
        'parser'      : uruguay_cou.parsear,
        'carpeta'     : DATA_RAW / 'uruguay',
        'anios'       : [2017],
        'moneda'      : 'UYU',
        'exts'        : ['.xlsx'],
        'modo_brasil' : False,
        'modo_mip'    : False,
        'modo_carpeta': True,   # el parser recibe carpeta+anio (no archivo)
    },
}

CONCILIACION_CIERRE_MENOR = {
    # Negativos pequenos y concentrados encontrados despues de corregir parsers.
    # Se concilian con RAS para preservar g y totales de columna de Z.
    'brasil_early': {'max_rel_g': 0.02, 'descripcion': 'Brasil 2000-2009: cierre menor de demanda final'},
    'uruguay': {'max_rel_g': 0.001, 'descripcion': 'Uruguay 2016: redondeo de MIP directa BCU'},
}


def encontrar_archivo(carpeta: Path, anio: int, exts: list) -> Path | None:
    """Busca el archivo de COU para un año dado, probando extensiones."""
    for ext in exts:
        for patron in [f'*{anio}*{ext}', f'*{ext}']:
            matches = list(carpeta.glob(patron))
            for m in matches:
                if str(anio) in m.name:
                    return m
    return None


def preparar_cou_nacional(cou):
    """
    Normaliza un COU para construir una MIP domestica:
    - U queda como consumo intermedio nacional/domestico.
    - U_importada conserva el consumo intermedio importado, explicito o estimado.
    - Si la fuente trae un puente de precios, U e Y se convierten con ese factor
      y se conserva la demanda final fuente depurada.
    - Solo se usa demanda final residual como fallback o para productos sin uso
      comprador publicado pero con produccion domestica positiva.
    """
    productos = [p for p in cou.V.columns if p in cou.U.index]
    industrias = [a for a in cou.V.index if a in cou.U.columns]
    cou.V = cou.V.loc[industrias, productos].clip(lower=0)
    U_total = cou.U.reindex(index=productos, columns=industrias).fillna(0).clip(lower=0)

    notas = list(getattr(cou, 'notas', []))
    q_dom = cou.V.sum(axis=0).reindex(productos).fillna(0)
    factor_domestico_pb = getattr(cou, 'factor_domestico_pb', None)

    if factor_domestico_pb is not None:
        factor = factor_domestico_pb.reindex(productos).fillna(0).clip(lower=0)
        U_nacional = U_total.mul(factor, axis=0)
        ajuste_intermedio = U_total - U_nacional
        Y_fuente = cou.Y.reindex(index=productos).fillna(0) if cou.Y is not None else pd.DataFrame(
            0.0, index=productos, columns=['demanda_final_fuente']
        )
        Y_domestica = Y_fuente.mul(factor, axis=0)

        demanda_total_pc = getattr(cou, 'demanda_total_pc', None)
        if demanda_total_pc is not None:
            demanda_total_pc = demanda_total_pc.reindex(productos).fillna(0)
            sin_uso_pc = (demanda_total_pc.abs() <= 1e-8) & (q_dom > 1e-8)
        else:
            sin_uso_pc = pd.Series(False, index=productos)

        # Algunos productos de margen/valoracion tienen produccion domestica,
        # pero no aparecen como fila de uso a precios comprador. En esos casos
        # el residual explicito cierra el producto sin alterar Z.
        if sin_uso_pc.any():
            residual = q_dom - U_nacional.sum(axis=1)
            Y_domestica.loc[sin_uso_pc, :] = 0
            Y_domestica.loc[sin_uso_pc, 'ajuste_residual_sin_uso_pc'] = residual.loc[sin_uso_pc]

        cou.U = U_nacional
        cou.U_importada = ajuste_intermedio
        cou.Y = Y_domestica
        notas.append('U e Y se convierten a base domestica/precios basicos con factor publicado por producto.')
        notas.append('Y conserva componentes fuente depurados; no se reemplaza por residual general.')
    else:
        ya_nacional = any('U usa solo consumo intermedio nacional' in str(n) for n in notas)
        if getattr(cou, 'U_importada', None) is not None:
            U_importada = cou.U_importada.reindex(index=productos, columns=industrias).fillna(0).clip(lower=0)
            U_nacional = U_total if ya_nacional else (U_total - U_importada).clip(lower=0)
            notas.append('CI importado separado desde matriz explicita de la fuente.')
        else:
            M = cou.M.reindex(productos).fillna(0) if cou.M is not None else pd.Series(0.0, index=productos)
            oferta_total = (q_dom + M.abs()).replace(0, np.nan)
            share_importado = (M.abs() / oferta_total).fillna(0).clip(lower=0, upper=0.95)
            U_importada = U_total.mul(share_importado, axis=0)
            U_nacional = (U_total - U_importada).clip(lower=0)
            if float(M.abs().sum()) > 0:
                notas.append('CI importado estimado por producto con participacion abs(M)/(produccion domestica+abs(M)).')
            else:
                notas.append('Sin apertura de importaciones intermedias en la fuente; CI importado se deja en cero.')

        cou.U = U_nacional
        cou.U_importada = U_importada
        if cou.Y is not None and not cou.Y.empty:
            # Fallback conservador: si no hay puente de precios, se mantiene Y fuente
            # cuando su balance por producto es compatible; si no, se usa residual.
            Y_fuente = cou.Y.reindex(index=productos).fillna(0)
            balance_fuente = q_dom - U_nacional.sum(axis=1) - Y_fuente.sum(axis=1)
            if balance_fuente.abs().max() <= max(1.0, float(q_dom.max()) * 1e-6):
                cou.Y = Y_fuente
                notas.append('Y fuente conservada: balance compatible con U nacional y produccion domestica.')
            else:
                cou.Y = (q_dom - U_nacional.sum(axis=1)).to_frame('demanda_final_domestica_residual')
                notas.append('Y fuente no compatible sin puente de precios; se usa residual documentado.')
        else:
            cou.Y = (q_dom - U_nacional.sum(axis=1)).to_frame('demanda_final_domestica_residual')

    U_importada = cou.U_importada
    cou.W = cou.W.reindex(columns=industrias).fillna(0) if cou.W is not None else pd.DataFrame(
        [cou.V.sum(axis=1) - cou.U.sum(axis=0) - U_importada.sum(axis=0)],
        index=['valor_agregado_residual'],
        columns=industrias,
    )
    if getattr(cou, 'empleo', None) is not None:
        cou.empleo = cou.empleo.reindex(industrias).fillna(0)
    cou.M = cou.M.reindex(productos).fillna(0) if cou.M is not None else pd.Series(0.0, index=productos, name='importaciones')
    notas.append('Z/A/L se calculan con consumo intermedio nacional; importaciones quedan fuera de Z.')
    notas.append('Chequeo VA: g = CI nacional + CI importado + valor agregado.')
    cou.notas = notas
    return cou


def recalcular_matrices_desde_Z(mip: dict) -> dict:
    """Recalcula A y L manteniendo Z y g."""
    Z = mip['Z'].astype(float)
    g = mip['g'].reindex(Z.index).fillna(0).astype(float)
    g_safe = g.copy()
    g_safe[g_safe == 0] = 1

    A_arr = Z.to_numpy(dtype=float) / g_safe.to_numpy(dtype=float)[np.newaxis, :]
    mip['A'] = pd.DataFrame(A_arr, index=Z.index, columns=Z.columns)

    I = np.eye(len(Z))
    try:
        L_arr = np.linalg.inv(I - A_arr)
    except np.linalg.LinAlgError:
        L_arr = np.linalg.pinv(I - A_arr)
    mip['L'] = pd.DataFrame(L_arr, index=Z.index, columns=Z.columns)
    return mip


def conciliar_demanda_final_menor(mip: dict, pais: str, anio: int) -> dict:
    """
    Corrige cierres negativos pequenos y aprobados:
    - fija g;
    - conserva totales de columna de Z, por tanto no mueve W residual;
    - redistribuye el cierre negativo sobre sectores con demanda final positiva;
    - ajusta Z por RAS y recalcula A/L.

    No se aplica a negativos materiales ni a paises no incluidos en
    CONCILIACION_CIERRE_MENOR.
    """
    regla = CONCILIACION_CIERRE_MENOR.get(pais)
    if regla is None:
        return mip

    Z = mip['Z'].astype(float).copy()
    g = mip['g'].reindex(Z.index).fillna(0).astype(float)
    f = mip.get('f_ind', g - Z.sum(axis=1)).reindex(Z.index).fillna(0).astype(float)

    neg_mask = f < -1e-8
    if not neg_mask.any():
        return mip

    rel_neg = (-f[neg_mask] / g[neg_mask].replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).fillna(np.inf)
    if float(rel_neg.max()) > float(regla['max_rel_g']):
        mip['ajuste_cierre'] = pd.DataFrame({
            'sector': f.index,
            'demanda_final_original': f.values,
            'demanda_final_conciliada': f.values,
            'ajuste_demanda_final': 0.0,
            'estado': 'no_aplicado_negativo_material',
        }).set_index('sector')
        return mip

    delta = float(-f[neg_mask].sum())
    elegibles = (f > 1e-8) & (Z.sum(axis=1) > 1e-8)
    base_redistribucion = float(f[elegibles].sum())
    if delta <= 0 or base_redistribucion <= delta:
        return mip

    f_original = f.copy()
    f_adj = f.copy()
    f_adj[neg_mask] = 0.0
    f_adj[elegibles] = f_adj[elegibles] - delta * (f[elegibles] / base_redistribucion)

    if (f_adj < -1e-8).any():
        return mip

    row_targets = (g - f_adj).clip(lower=0)
    col_targets = Z.sum(axis=0).reindex(Z.columns).fillna(0)
    diff = float(row_targets.sum() - col_targets.sum())
    if abs(diff) > 1e-6:
        # Ajuste numerico sobre el mayor row target para igualar masas RAS.
        idx = row_targets.idxmax()
        row_targets.loc[idx] = row_targets.loc[idx] - diff

    Z_adj_arr = ras(
        Z.to_numpy(dtype=float),
        row_targets.to_numpy(dtype=float),
        col_targets.to_numpy(dtype=float),
        max_iter=2000,
        tol=1e-7,
    )
    Z_adj = pd.DataFrame(Z_adj_arr, index=Z.index, columns=Z.columns)

    mip['Z_original_pre_conciliacion'] = Z
    mip['f_ind_original_pre_conciliacion'] = f_original
    mip['Z'] = Z_adj
    mip['f_ind'] = f_adj
    mip = recalcular_matrices_desde_Z(mip)

    mip['ajuste_cierre'] = pd.DataFrame({
        'demanda_final_original': f_original,
        'demanda_final_conciliada': f_adj,
        'ajuste_demanda_final': f_adj - f_original,
        'ventas_intermedias_original': Z.sum(axis=1),
        'ventas_intermedias_conciliadas': Z_adj.sum(axis=1),
        'ajuste_ventas_intermedias': Z_adj.sum(axis=1) - Z.sum(axis=1),
        'produccion_bruta_g': g,
        'regla': regla['descripcion'],
    })
    return mip


def procesar_pais_anio(pais: str, anio: int, cfg: dict,
                       verbose: bool = True) -> dict | None:
    """
    Ejecuta el pipeline completo para un país y año.
    Retorna dict con resultados o None si falla.
    """
    carpeta = cfg['carpeta']

    try:
        # ── 1. Parsear ───────────────────────────────────────────────────────
        if cfg.get('modo_mip'):
            # México / Uruguay: el INEGI/BCU ya publica MIPs directas.
            if cfg.get('modo_carpeta'):
                # Uruguay: el parser recibe la carpeta (no un ZIP)
                mip = cfg['parser'](carpeta=carpeta, anio=anio, verbose=False)
            else:
                # México: el parser recibe la ruta al ZIP
                patron = cfg.get('zip_patron', 'mip_{anio}_csv.zip')
                if isinstance(patron, dict):
                    nombre_zip = patron.get(anio)
                    if nombre_zip is None:
                        if verbose:
                            print(f"    [NO ENCONTRADO] {pais} {anio}: sin patrón ZIP")
                        return None
                    ruta_zip = carpeta / nombre_zip
                else:
                    ruta_zip = carpeta / patron.format(anio=anio)
                if not ruta_zip.exists():
                    if verbose:
                        print(f"    [NO ENCONTRADO] {pais} {anio}: {ruta_zip.name}")
                    return None
                mip = cfg['parser'](ruta_zip, anio=anio, verbose=False)

            # Normalizar: asegurar W_total (puede llamarse 'W')
            if 'W_total' not in mip and 'W' in mip:
                mip['W_total'] = mip['W']
            elif 'W_total' not in mip:
                mip['W_total'] = pd.Series(0.0, index=mip['g'].index,
                                           name='valor_agregado')
            if 'Z_m' in mip:
                mip['Z_m'] = mip['Z_m'].reindex(index=mip['Z'].index, columns=mip['Z'].columns).fillna(0)
                mip['M_intermedia_ind'] = mip['Z_m'].sum(axis=0).reindex(mip['Z'].columns).fillna(0)
                mip['M_intermedia_ind'].name = 'consumo_intermedio_importado'
            else:
                mip['M_intermedia_ind'] = pd.Series(0.0, index=mip['g'].index,
                                                    name='consumo_intermedio_importado')

            # Calcular f_ind (demanda final sectorial) para verificación.
            # Se conserva el signo para que las validaciones muestren desbalances.
            mip['f_ind'] = mip['g'] - mip['Z'].sum(axis=1)
            mip = conciliar_demanda_final_menor(mip, pais, anio)

            ok = verificar_leontief(mip)

            tabla_mult = tabla_multiplicadores_completa(
                L=mip['L'],
                g=mip['g'],
                W_total=mip['W_total'],
            )
            tabla_mult['clasificacion'] = clasificar_sectores(tabla_mult)
            tabla_mult['anio'] = anio
            tabla_mult['pais'] = pais

            guardar_mip_directo(pais, anio, mip, tabla_mult)

            n_ind = len(mip['g'])
            mult_prom = tabla_mult['mult_produccion'].mean()
            if verbose:
                print(f"    [OK] {pais} {anio}: {n_ind} sectores, "
                      f"mult. medio={mult_prom:.3f}, leontief={'OK' if ok else 'AVISO'}")

            return {
                'mip'      : mip,
                'mult'     : tabla_mult,
                'cou'      : None,
                'n_ind'    : n_ind,
                'mult_mean': mult_prom,
            }

        # ── COU pipeline (Argentina, Brasil, Uruguay 2017) ───────────────────
        if cfg.get('modo_brasil'):
            # Brasil: el parser recibe carpeta y año (busca tab1/tab2 internamente)
            tab1 = carpeta / f"68_tab1_{anio}.xls"
            if not tab1.exists():
                if verbose:
                    print(f"    [NO ENCONTRADO] {pais} {anio}")
                return None
            cou = cfg['parser'](carpeta=carpeta, anio=anio, verbose=False)
        elif cfg.get('modo_carpeta'):
            # Uruguay COU: el parser recibe carpeta y año (busca archivos internamente)
            try:
                cou = cfg['parser'](carpeta=carpeta, anio=anio, verbose=False)
            except FileNotFoundError:
                if verbose:
                    print(f"    [NO ENCONTRADO] {pais} {anio}")
                return None
        else:
            archivo = encontrar_archivo(carpeta, anio, cfg.get('exts', ['.xlsx']))
            if archivo is None:
                if verbose:
                    print(f"    [NO ENCONTRADO] {pais} {anio}")
                return None
            cou = cfg['parser'](archivo, anio, verbose=False)

        if cou.V is None or cou.V.empty:
            print(f"    [VACÍO] {pais} {anio}: tabla V vacía")
            return None

        # ── 2. Convertir COU → MIP ────────────────────────────────────────────
        # ajustar_ras=False: el desbalance V vs U+Y puede ser por diferencias
        # de niveles de precios (básicos vs. comprador), lo cual es normal en
        # sistemas de cuentas nacionales con dos niveles de precios (IBGE).
        # La conversión D @ U es válida sin RAS en estos casos.
        cou = preparar_cou_nacional(cou)
        mip = sut_a_iot_industria(
            V=cou.V, U=cou.U, Y=cou.Y, W=cou.W, M=None,
            U_importada=cou.U_importada,
            ajustar_ras=False
        )
        mip = conciliar_demanda_final_menor(mip, pais, anio)

        # ── 3. Verificar ──────────────────────────────────────────────────────
        ok = verificar_leontief(mip)

        # ── 4. Multiplicadores ────────────────────────────────────────────────
        tabla_mult = tabla_multiplicadores_completa(
            L=mip['L'],
            g=mip['g'],
            W_total=mip['W_total'],
            empleo=getattr(cou, 'empleo', None),
        )
        tabla_mult['clasificacion'] = clasificar_sectores(tabla_mult)
        tabla_mult['anio'] = anio
        tabla_mult['pais'] = pais

        # ── 5. Guardar ────────────────────────────────────────────────────────
        guardar_resultados(pais, anio, mip, tabla_mult, cou)

        n_ind = len(mip['g'])
        mult_prom = tabla_mult['mult_produccion'].mean()
        if verbose:
            print(f"    [OK] {pais} {anio}: {n_ind} sectores, "
                  f"mult. medio={mult_prom:.3f}, leontief={'OK' if ok else 'AVISO'}")

        return {
            'mip'      : mip,
            'mult'     : tabla_mult,
            'cou'      : cou,
            'n_ind'    : n_ind,
            'mult_mean': mult_prom,
        }

    except Exception as e:
        print(f"    [ERROR] {pais} {anio}: {e}")
        if verbose:
            traceback.print_exc()
        return None


def guardar_mip_directo(pais: str, anio: int, mip: dict,
                        tabla_mult: pd.DataFrame) -> None:
    """Guarda MIP ya construida (México/Uruguay) en archivos Excel."""
    carpeta = DATA_PROC / pais
    carpeta.mkdir(parents=True, exist_ok=True)
    out_tab  = OUTPUT_TAB / pais
    out_tab.mkdir(parents=True, exist_ok=True)

    ruta_mip = carpeta / f"mip_{pais}_{anio}.xlsx"
    with pd.ExcelWriter(ruta_mip, engine='openpyxl') as writer:
        mip['Z'].to_excel(writer, sheet_name='Z_flujos')
        if 'Z_m' in mip:
            mip['Z_m'].to_excel(writer, sheet_name='Z_importada')
        if 'Z_t' in mip:
            mip['Z_t'].to_excel(writer, sheet_name='Z_total')
        mip['A'].to_excel(writer, sheet_name='A_coeficientes')
        mip['L'].to_excel(writer, sheet_name='L_leontief')
        mip['g'].to_frame('produccion_bruta').to_excel(writer, sheet_name='produccion')
        if 'W_total' in mip:
            mip['W_total'].to_frame('valor_agregado').to_excel(writer, sheet_name='valor_agregado')
        if 'f_ind' in mip:
            mip['f_ind'].to_frame('demanda_final').to_excel(writer, sheet_name='demanda_final')
        if 'M_intermedia_ind' in mip:
            mip['M_intermedia_ind'].to_frame('ci_importado').to_excel(writer, sheet_name='ci_importado')
        if 'ajuste_cierre' in mip:
            mip['ajuste_cierre'].to_excel(writer, sheet_name='ajuste_cierre')
        if 'Z_original_pre_conciliacion' in mip:
            mip['Z_original_pre_conciliacion'].to_excel(writer, sheet_name='Z_pre_conciliacion')
        _diagnosticos_mip(mip).to_excel(writer, sheet_name='diagnosticos_macro')

    ruta_mult = out_tab / f"multiplicadores_{pais}_{anio}.xlsx"
    tabla_mult.to_excel(ruta_mult)


def guardar_resultados(pais: str, anio: int, mip: dict,
                       tabla_mult: pd.DataFrame, cou) -> None:
    """Guarda MIP y multiplicadores en archivos Excel."""
    carpeta = DATA_PROC / pais
    carpeta.mkdir(parents=True, exist_ok=True)
    out_tab  = OUTPUT_TAB / pais
    out_tab.mkdir(parents=True, exist_ok=True)

    # MIP completa (Z, A, L)
    ruta_mip = carpeta / f"mip_{pais}_{anio}.xlsx"
    with pd.ExcelWriter(ruta_mip, engine='openpyxl') as writer:
        mip['Z'].to_excel(writer, sheet_name='Z_flujos')
        mip['A'].to_excel(writer, sheet_name='A_coeficientes')
        mip['L'].to_excel(writer, sheet_name='L_leontief')
        mip['g'].to_frame('produccion_bruta').to_excel(writer, sheet_name='produccion')
        mip['W_total'].to_frame('valor_agregado').to_excel(writer, sheet_name='valor_agregado')
        mip['f_ind'].to_frame('demanda_final').to_excel(writer, sheet_name='demanda_final')
        mip['M_intermedia_ind'].to_frame('ci_importado').to_excel(writer, sheet_name='ci_importado')
        if 'ajuste_cierre' in mip:
            mip['ajuste_cierre'].to_excel(writer, sheet_name='ajuste_cierre')
        if 'Z_original_pre_conciliacion' in mip:
            mip['Z_original_pre_conciliacion'].to_excel(writer, sheet_name='Z_pre_conciliacion')
        _diagnosticos_mip(mip).to_excel(writer, sheet_name='diagnosticos_macro')

    # Tabla de multiplicadores
    ruta_mult = out_tab / f"multiplicadores_{pais}_{anio}.xlsx"
    tabla_mult.to_excel(ruta_mult)

    # COU procesado
    ruta_cou = carpeta / f"cou_{pais}_{anio}.xlsx"
    with pd.ExcelWriter(ruta_cou, engine='openpyxl') as writer:
        if cou.V is not None:
            cou.V.to_excel(writer, sheet_name='V_oferta')
        if cou.U is not None:
            cou.U.to_excel(writer, sheet_name='U_utilizacion')
        if cou.Y is not None:
            cou.Y.to_excel(writer, sheet_name='Y_demanda_final')
        if cou.W is not None:
            cou.W.to_excel(writer, sheet_name='W_valor_agregado')
        if cou.M is not None:
            cou.M.to_frame('importaciones').to_excel(writer, sheet_name='M_importaciones')
        if getattr(cou, 'U_importada', None) is not None:
            cou.U_importada.to_excel(writer, sheet_name='U_importada')
        if getattr(cou, 'empleo', None) is not None:
            cou.empleo.to_excel(writer, sheet_name='empleo')
        if getattr(cou, 'T', None) is not None:
            cou.T.to_frame('margenes').to_excel(writer, sheet_name='T_margenes')
        if getattr(cou, 'imp_ind', None) is not None:
            cou.imp_ind.to_frame('impuestos_netos').to_excel(writer, sheet_name='IMP_impuestos')
        if getattr(cou, 'notas', None):
            pd.DataFrame({'nota': cou.notas}).to_excel(writer, sheet_name='notas', index=False)


def _diagnosticos_mip(mip: dict) -> pd.DataFrame:
    """Chequeos macro: oferta=demanda por filas y valor agregado por columnas."""
    Z = mip['Z']
    g = mip['g'].reindex(Z.index).fillna(0)
    f = mip.get('f_ind', g - Z.sum(axis=1)).reindex(Z.index).fillna(0)
    W = mip.get('W_total', g - Z.sum(axis=0)).reindex(Z.index).fillna(0)
    Mci = mip.get('M_intermedia_ind', pd.Series(0.0, index=Z.index)).reindex(Z.index).fillna(0)
    demanda_total = Z.sum(axis=1) + f
    va_residual = g - Z.sum(axis=0) - Mci
    return pd.DataFrame({
        'produccion_bruta_oferta_g': g,
        'demanda_intermedia_ventas_Z': Z.sum(axis=1),
        'demanda_final_f': f,
        'demanda_total': demanda_total,
        'oferta_menos_demanda': g - demanda_total,
        'compras_intermedias_Z': Z.sum(axis=0),
        'consumo_intermedio_importado': Mci,
        'valor_agregado_W': W,
        'valor_agregado_residual_g_menos_Zcol_menos_CIimp': va_residual,
        'W_menos_VA_residual': W - va_residual,
    })


def compilar_serie_tiempo(resultados: dict) -> pd.DataFrame:
    """
    Genera tabla de multiplicadores para toda la serie de tiempo de un país.
    """
    frames = []
    for (pais, anio), res in resultados.items():
        if res is not None:
            df = res['mult'].copy()
            df['pais'] = pais
            df['anio'] = anio
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=False)


def main():
    parser = argparse.ArgumentParser(description='Pipeline COU → MIP → Multiplicadores')
    parser.add_argument('--pais', default='todos',
                        choices=['argentina', 'argentina_mip97', 'brasil', 'brasil_early',
                                 'mexico', 'uruguay', 'uruguay_cou', 'todos'])
    parser.add_argument('--anio', type=int, default=None,
                        help='Año específico (default: todos los disponibles)')
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    paises = list(CONFIG.keys()) if args.pais == 'todos' else [args.pais]

    print("\n" + "="*65)
    print("  PIPELINE: COU → MIP → MULTIPLICADORES")
    print("="*65)

    resultados = {}
    resumen = []

    for pais in paises:
        cfg = CONFIG[pais]
        anios = [args.anio] if args.anio else cfg['anios']

        print(f"\n{'─'*50}")
        print(f"  País: {pais.upper()}  ({len(anios)} años a procesar)")
        print(f"{'─'*50}")

        for anio in anios:
            res = procesar_pais_anio(pais, anio, cfg, verbose=True)
            resultados[(pais, anio)] = res
            if res:
                resumen.append({
                    'pais': pais,
                    'anio': anio,
                    'n_sectores': res['n_ind'],
                    'mult_produccion_medio': round(res['mult_mean'], 4),
                    'estado': 'OK',
                })
            else:
                resumen.append({'pais': pais, 'anio': anio, 'estado': 'NO_PROCESADO'})

        # Guardar serie de tiempo del país
        serie = compilar_serie_tiempo({k: v for k, v in resultados.items() if k[0] == pais})
        if not serie.empty:
            ruta_serie = OUTPUT_TAB / pais / f"serie_multiplicadores_{pais}.xlsx"
            (OUTPUT_TAB / pais).mkdir(parents=True, exist_ok=True)
            serie.to_excel(ruta_serie)
            print(f"  → Serie guardada: {ruta_serie.name}")

    # Resumen final
    print("\n" + "="*65)
    print("  RESUMEN FINAL")
    print("="*65)
    df_res = pd.DataFrame(resumen)
    print(df_res.to_string(index=False))

    # Guardar resumen
    ruta_res = OUTPUT_TAB / "resumen_procesamiento.xlsx"
    df_res.to_excel(ruta_res, index=False)
    print(f"\n  Resumen guardado en: {ruta_res}")


if __name__ == '__main__':
    main()
