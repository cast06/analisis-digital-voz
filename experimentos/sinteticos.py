# ==============================================================
# EXPERIMENTOS CON SEÑALES SINTETICAS (VALIDACION DE LA DFT)
# ==============================================================
# Sirven para comprobar que la DFT encuentra exactamente las
# frecuencias con las que se generaron las señales.
# Con N = 512 y fs = 16000 Hz la resolucion es 31.25 Hz, por lo
# que 125, 250, 375, 500, 750, 1250 y 2500 Hz caen en bins exactos.
# ==============================================================

from config import FRECUENCIA_MUESTREO
from audio.senales import generar_seno, generar_seno_coseno, generar_senal_compleja
from audio.espectral import dft, frecuencias_dominantes
from visual.svg import crear_svg, crear_svg_espectro, crear_svg_tres_intensidades

TAMANO_SEGMENTO_DFT = 512


def _analizar_senal(senal, cantidad, svg_senal, titulo_senal, svg_espectro, titulo_espectro):
    segmento = senal[:TAMANO_SEGMENTO_DFT]
    espectro = dft(segmento, FRECUENCIA_MUESTREO)
    return {
        "senal": crear_svg(senal, svg_senal, titulo_senal),
        "espectro": crear_svg_espectro(espectro, svg_espectro, titulo_espectro),
        "frecuencias": frecuencias_dominantes(espectro, cantidad=cantidad)
    }


def experimento_seno():
    return _analizar_senal(
        generar_seno(frecuencia=250, duracion=0.05), 5,
        "01_seno_250Hz.svg", "Onda seno pura de 250 Hz",
        "02_espectro_seno.svg", "Espectro de frecuencia - Seno 250 Hz"
    )


def experimento_seno_coseno():
    return _analizar_senal(
        generar_seno_coseno(), 8,
        "03_seno_coseno.svg", "Combinacion seno 250 Hz + coseno 500 Hz",
        "04_espectro_seno_coseno.svg", "Espectro - Seno + Coseno"
    )


def experimento_senal_compleja():
    return _analizar_senal(
        generar_senal_compleja(), 10,
        "05_senal_compleja.svg", "Señal formada por multiples frecuencias",
        "06_espectro_complejo.svg", "Espectro de señal compleja"
    )


def generar_ondas_abecedario():
    """
    DEMOSTRACION SINTETICA: a cada letra se le asigna una frecuencia
    arbitraria (200 + 20*i Hz). No representa la voz real de la letra.
    """
    abecedario = list("ABCDEFGHIJKLMNÑOPQRSTUVWXYZ")
    ondas = []

    for indice, letra in enumerate(abecedario):
        frecuencia = 200 + indice * 20
        ondas.append({
            "letra": letra,
            "frecuencia": frecuencia,
            "svg": crear_svg_tres_intensidades(letra, frecuencia)
        })

    return ondas
