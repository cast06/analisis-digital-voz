# ==============================================================
# PROCESAMIENTO POR LOTES Y GENERACION DEL INFORME TXT
# ==============================================================

from config import (
    ARCHIVOS_AUDIO_LOTE, DIRECTORIO_AUDIOS, DIRECTORIO_AUDIOS_RESPALDO,
    DIRECTORIO_PROYECTO, ruta_salida
)
from nucleo.archivos import unir_ruta, existe_archivo, guardar_texto
from audio.wav import leer_wav
from audio.segmentacion import analizar_audio_continuo
from visual.svg import crear_svg_segmentacion, crear_svg_barras_segmentos
from reportes.formato import formatear_bloque_segmento_txt

ENCABEZADO_INFORME = [
    "=" * 70,
    "INFORME DE ANÁLISIS DIGITAL DE VOZ CONTINUA DESDE CERO",
    "=" * 70,
    "Nota sobre reconocimiento de palabras:",
    "La detección de actividad de voz (VAD) identifica segmentos con habla",
    "activa (sílabas, palabras o frases completas), pero no equivale a un",
    "reconocedor de vocabulario abierto en español. Cada segmento indica su",
    "estructura estimada y su estado de comparación contra referencias.",
    "=" * 70
]


def buscar_ruta_audio(nombre_archivo):
    """
    Busca la grabacion en este orden:
    1. audios/ del proyecto
    2. carpeta de respaldo (C:\\Users\\sharo\\Downloads\\nuevo)
    3. carpeta raiz del proyecto
    Si no aparece, devuelve la ruta de audios/ para reportar el error.
    """
    candidatas = [
        unir_ruta(DIRECTORIO_AUDIOS, nombre_archivo),
        unir_ruta(DIRECTORIO_AUDIOS_RESPALDO, nombre_archivo),
        unir_ruta(DIRECTORIO_PROYECTO, nombre_archivo)
    ]
    for ruta in candidatas:
        if existe_archivo(ruta):
            return ruta
    return candidatas[0]


def _resultado_error(nombre, ruta, mensaje):
    return {"archivo": nombre, "ruta": ruta, "exito": False, "error": mensaje, "segmentos": []}


def _procesar_un_audio(indice, nombre_archivo, ruta_audio, referencias, lineas_informe):
    print(f"  Leyendo encabezado y muestras WAV de '{nombre_archivo}'...")
    audio = leer_wav(ruta_audio)

    fs = audio["frecuencia_muestreo"]
    muestras = audio["muestras"]

    print(
        f"  Formato WAV validado: {fs} Hz | {audio['canales']} canal(es) | "
        f"{audio['bits']} bits | {len(muestras)} muestras ({audio['duracion']:.3f} s)"
    )
    print("  Detectando segmentos de voz activa y extrayendo características...")

    segmentos = analizar_audio_continuo(
        muestras, fs, referencias=referencias,
        mostrar_progreso=True, nombre_archivo=nombre_archivo
    )

    resumen = (
        f"Frecuencia de muestreo: {fs} Hz\n"
        f"Canales originales: {audio['canales']} (procesado en mono normalizado)\n"
        f"Profundidad de bits: {audio['bits']} bits PCM\n"
        f"Muestras totales: {len(muestras)}\n"
        f"Duración total: {audio['duracion']:.3f} s\n"
        f"Segmentos de voz detectados: {len(segmentos)}"
    )
    print("\n" + resumen)
    lineas_informe.append(resumen)

    if not segmentos:
        aviso = ("Aviso: No se detectaron segmentos con actividad de voz "
                 "por encima del umbral de silencio.")
        print(aviso)
        lineas_informe.append(aviso)

    for seg in segmentos:
        bloque = formatear_bloque_segmento_txt(seg)
        print(bloque, end="")
        lineas_informe.append(bloque.rstrip("\n"))

    return {
        "archivo": nombre_archivo,
        "ruta": ruta_audio,
        "exito": True,
        "fs": fs,
        "canales": audio["canales"],
        "bits": audio["bits"],
        "num_muestras": len(muestras),
        "duracion": audio["duracion"],
        "segmentos": segmentos,
        "svg_segmentacion": crear_svg_segmentacion(
            muestras, fs, segmentos,
            f"lote_segmentacion_{indice}.svg",
            f"Forma de onda y segmentación automática: {nombre_archivo}"
        ),
        "svg_barras_f0": crear_svg_barras_segmentos(
            segmentos,
            f"Frecuencia Fundamental (F0) por segmento: {nombre_archivo}"
        )
    }


def procesar_lote_audios(
        archivos_audio=None,
        referencias=None,
        nombre_informe="resultado_analisis.txt"):
    """
    Procesa cada grabacion de la lista, extrae segmentos de voz y sus
    caracteristicas, imprime el reporte y lo guarda en salidas/.
    Si un archivo falla, registra el error y continua con los demas.
    """
    if archivos_audio is None:
        archivos_audio = ARCHIVOS_AUDIO_LOTE

    resultados_lote = []
    lineas_informe = ENCABEZADO_INFORME[:]

    for indice, nombre_archivo in enumerate(archivos_audio, start=1):
        ruta_audio = buscar_ruta_audio(nombre_archivo)

        encabezado = (
            "\n" + "=" * 60 + "\n"
            f"ARCHIVO [{indice}/{len(archivos_audio)}]: {nombre_archivo}\n"
            f"Ruta: {ruta_audio}\n"
            + "=" * 60
        )
        print(encabezado)
        lineas_informe.append(encabezado)

        if not existe_archivo(ruta_audio):
            mensaje = f"ERROR: No se encontró el archivo en {ruta_audio}"
            print(mensaje)
            lineas_informe.append(mensaje)
            resultados_lote.append(_resultado_error(nombre_archivo, ruta_audio, mensaje))
            continue

        try:
            resultados_lote.append(
                _procesar_un_audio(indice, nombre_archivo, ruta_audio, referencias, lineas_informe)
            )
        except Exception as error:
            mensaje = f"ERROR al procesar '{nombre_archivo}': {error}"
            print(mensaje)
            lineas_informe.append(mensaje)
            resultados_lote.append(_resultado_error(nombre_archivo, ruta_audio, mensaje))

    ruta_informe = ruta_salida(nombre_informe)
    guardar_texto(ruta_informe, "\n".join(lineas_informe) + "\n")

    print("\n" + "=" * 60)
    print("Análisis por lotes terminado.")
    print("Informe guardado en:", ruta_informe)
    print("=" * 60)

    return resultados_lote
