# ==============================================================
# DATOS PARA EL RECONOCIMIENTO DE PALABRAS AISLADAS (MESD)
# ==============================================================
#
# Se usan las palabras del corpus A de MESD, que se repiten en las
# 6 emociones y en los 3 tipos de voz (F, M, C). Asi cada palabra
# tiene grabaciones con distintas voces y emociones, y el modelo
# aprende la palabra y no la forma de hablar.
#
# Vector de entrada: MFCC (13) con normalizacion de media cepstral,
# resumidos en 5 tramos de igual duracion = 65 valores.
# ==============================================================

import config
from nucleo.archivos import nombre_de
from nucleo.tabla import leer_tabla, iniciar_tabla, agregar_fila
from audio.preparar import cargar_audio_preparado
from audio.mfcc import calcular_mfcc, normalizar_media_cepstral, vector_longitud_fija
from emociones.mesd import leer_lista_archivos

COLUMNAS = ["ruta", "palabra", "voz", "emocion"]


def dimension_vector():
    return config.MFCC_COEFICIENTES * config.MFCC_TRAMOS


def interpretar_nombre_palabra(ruta):
    """Acepta solo archivos del corpus A con emocion y voz conocidas."""
    nombre = nombre_de(ruta)
    if not nombre.lower().endswith(".wav"):
        return None
    partes = nombre[:-4].split("_", 3)
    if len(partes) != 4:
        return None

    emocion, voz, corpus, palabra = (p.strip() for p in partes)
    emocion = config.EMOCIONES_TODAS_MESD.get(emocion.lower())
    voz = voz.upper()
    if emocion is None or voz not in config.TIPOS_VOZ_PALABRAS:
        return None
    if corpus.upper() != config.CORPUS_PALABRAS:
        return None

    return {"ruta": ruta, "palabra": palabra.lower(), "voz": voz, "emocion": emocion}


def vector_palabra(ruta_wav):
    """Audio preparado -> MFCC -> CMN -> vector de longitud fija."""
    muestras, fs = cargar_audio_preparado(ruta_wav)
    mfcc = calcular_mfcc(muestras, fs, numero_coeficientes=config.MFCC_COEFICIENTES)
    if not mfcc:
        raise ValueError("La grabacion es demasiado corta para calcular MFCC.")
    mfcc = normalizar_media_cepstral(mfcc)
    return vector_longitud_fija(mfcc, config.MFCC_TRAMOS)


def construir_tabla_palabras(ruta_lista=None, ruta_cache=None):
    ruta_lista = ruta_lista or config.LISTA_MESD
    ruta_cache = ruta_cache or config.CACHE_CARACTERISTICAS_PALABRAS
    n = dimension_vector()

    rutas = leer_lista_archivos(ruta_lista)
    if not rutas:
        return []

    candidatos = [d for d in (interpretar_nombre_palabra(r) for r in rutas) if d is not None]
    print(f"Archivos en la lista: {len(rutas)} | del corpus {config.CORPUS_PALABRAS}: {len(candidatos)}")

    cache = leer_tabla(ruta_cache, COLUMNAS, n)
    if not cache:
        iniciar_tabla(ruta_cache, COLUMNAS, n)

    registros = [cache[d["ruta"]] for d in candidatos if d["ruta"] in cache]
    pendientes = [d for d in candidatos if d["ruta"] not in cache]
    if pendientes:
        print(f"Calculando MFCC de {len(pendientes)} archivos nuevos "
              f"({len(registros)} ya estaban en cache)...")

    for numero, datos in enumerate(pendientes, start=1):
        try:
            registro = dict(datos)
            registro["vector"] = vector_palabra(datos["ruta"])
        except Exception as error:
            print(f"  Error en {nombre_de(datos['ruta'])}: {error}")
            continue
        registros.append(registro)
        agregar_fila(ruta_cache, registro, COLUMNAS)
        if numero % 25 == 0 or numero == len(pendientes):
            print(f"  {numero}/{len(pendientes)} archivos procesados")

    return registros
