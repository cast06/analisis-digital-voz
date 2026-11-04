# ==============================================================
# LECTURA DE LA BASE MESD Y TABLA DE CARACTERISTICAS
# ==============================================================
#
# Mexican Emotional Speech Database (Duville, Alonso-Valerdi e
# Ibarra-Zarate, 2021). Los archivos se nombran:
#
#     <emocion>_<tipo de voz>_<corpus>_<palabra>.wav
#     ej. Anger_F_A_abajo.wav
#
# tipo de voz: F (mujer adulta), M (hombre adulto), C (niño/a)
#
# Como el programa no puede listar carpetas, la lista de archivos
# se lee de datos/lista_mesd.txt (ver LEEME.md para generarla).
# ==============================================================

from config import (
    LISTA_MESD, CACHE_CARACTERISTICAS_MESD, EMOCIONES_MESD,
    TIPOS_VOZ_EMOCION, FS_ANALISIS_EMOCION, F0_MAXIMA_EMOCION
)
from nucleo.archivos import nombre_de, existe_archivo
from audio.preparar import cargar_audio_preparado
from audio.caracteristicas import analizar_segmento_completo, VARIABLES_EMOCION, construir_vector


def interpretar_nombre_mesd(ruta):
    """
    Obtiene emocion, tipo de voz, corpus y palabra a partir del nombre.
    Devuelve None si el archivo no sigue el formato o si su emocion o
    tipo de voz no se usan en este proyecto.
    """
    nombre = nombre_de(ruta)
    if not nombre.lower().endswith(".wav"):
        return None
    partes = nombre[:-4].split("_", 3)
    if len(partes) != 4:
        return None

    emocion_original, voz, corpus, palabra = partes
    emocion = EMOCIONES_MESD.get(emocion_original.strip().lower())
    voz = voz.strip().upper()

    if emocion is None or voz not in TIPOS_VOZ_EMOCION:
        return None

    return {
        "ruta": ruta,
        "emocion": emocion,
        "voz": voz,
        "corpus": corpus.strip().upper(),
        "palabra": palabra.strip().lower()
    }


def _leer_texto_flexible(ruta):
    """Lee un archivo de texto en UTF-8 (con o sin BOM) o, si falla, en Latin-1."""
    try:
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            return archivo.read()
    except UnicodeDecodeError:
        with open(ruta, "r", encoding="latin-1") as archivo:
            return archivo.read()


def leer_lista_archivos(ruta_lista=LISTA_MESD):
    if not existe_archivo(ruta_lista):
        return []
    lineas = _leer_texto_flexible(ruta_lista).splitlines()
    return [linea.strip().strip('"') for linea in lineas if linea.strip()]


def extraer_caracteristicas_emocion(ruta_wav):
    """
    Lee y prepara el audio (16 kHz, pico = 1, sin silencios en los
    extremos) y calcula las variables acusticas sobre la parte con voz.
    """
    muestras, fs = cargar_audio_preparado(ruta_wav, FS_ANALISIS_EMOCION)
    caracteristicas = analizar_segmento_completo(muestras, fs, f0_maxima=F0_MAXIMA_EMOCION)
    if caracteristicas is None:
        raise ValueError("El audio no contiene muestras utiles.")
    return caracteristicas


# --------------------------------------------------------------
# Cache de caracteristicas (archivo de texto separado por ';')
# --------------------------------------------------------------

_COLUMNAS_FIJAS = ["ruta", "emocion", "voz", "corpus", "palabra"]


def _encabezado_cache():
    return ";".join(_COLUMNAS_FIJAS + VARIABLES_EMOCION)


def _leer_cache(ruta_cache):
    """Devuelve {ruta: registro}. Si el encabezado no coincide, se ignora el cache."""
    if not existe_archivo(ruta_cache):
        return {}
    lineas = _leer_texto_flexible(ruta_cache).splitlines()
    if not lineas or lineas[0] != _encabezado_cache():
        print("El cache de caracteristicas es de otra version; se recalculara.")
        return {}

    registros = {}
    for linea in lineas[1:]:
        partes = linea.split(";")
        if len(partes) != len(_COLUMNAS_FIJAS) + len(VARIABLES_EMOCION):
            continue
        registro = dict(zip(_COLUMNAS_FIJAS, partes[:len(_COLUMNAS_FIJAS)]))
        registro["vector"] = [float(v) for v in partes[len(_COLUMNAS_FIJAS):]]
        registros[registro["ruta"]] = registro
    return registros


def _linea_cache(registro):
    valores = [registro[c] for c in _COLUMNAS_FIJAS] + [repr(v) for v in registro["vector"]]
    return ";".join(valores)


def construir_tabla_mesd(ruta_lista=LISTA_MESD, ruta_cache=CACHE_CARACTERISTICAS_MESD):
    """
    Devuelve la lista de registros {ruta, emocion, voz, corpus, palabra, vector}.
    Los archivos ya procesados se toman del cache; los nuevos se calculan
    y se agregan al cache al momento (si el programa se interrumpe, no se
    pierde lo avanzado).
    """
    rutas = leer_lista_archivos(ruta_lista)
    if not rutas:
        return []

    candidatos = []
    ignorados = 0
    for ruta in rutas:
        datos = interpretar_nombre_mesd(ruta)
        if datos is None:
            ignorados += 1
        else:
            candidatos.append(datos)

    print(f"Archivos en la lista: {len(rutas)} | usados: {len(candidatos)} | "
          f"ignorados (otra emocion, voz infantil o nombre no valido): {ignorados}")

    cache = _leer_cache(ruta_cache)
    if not cache:
        with open(ruta_cache, "w", encoding="utf-8") as archivo:
            archivo.write(_encabezado_cache() + "\n")

    registros = []
    pendientes = [d for d in candidatos if d["ruta"] not in cache]
    if pendientes:
        print(f"Calculando caracteristicas de {len(pendientes)} archivos nuevos "
              f"({len(candidatos) - len(pendientes)} ya estaban en cache)...")

    for datos in candidatos:
        if datos["ruta"] in cache:
            registros.append(cache[datos["ruta"]])

    for numero, datos in enumerate(pendientes, start=1):
        try:
            caracteristicas = extraer_caracteristicas_emocion(datos["ruta"])
        except Exception as error:
            print(f"  Error en {nombre_de(datos['ruta'])}: {error}")
            continue

        registro = dict(datos)
        registro["vector"] = construir_vector(caracteristicas, VARIABLES_EMOCION)
        registros.append(registro)

        with open(ruta_cache, "a", encoding="utf-8") as archivo:
            archivo.write(_linea_cache(registro) + "\n")

        if numero % 20 == 0 or numero == len(pendientes):
            print(f"  {numero}/{len(pendientes)} archivos procesados")

    return registros
