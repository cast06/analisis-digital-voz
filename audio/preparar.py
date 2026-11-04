# ==============================================================
# PREPARACION COMUN DE UNA GRABACION ANTES DE ANALIZARLA
# ==============================================================
# 1. Lectura manual del WAV.
# 2. Diezmado a 16000 Hz si viene a una frecuencia multiplo (48000 Hz).
# 3. Normalizacion del pico a 1, para que el volumen del microfono
#    no influya.
# 4. Recorte de silencios iniciales y finales con el VAD.
# ==============================================================

from audio.wav import leer_wav
from audio.remuestreo import remuestrear, normalizar_pico
from audio.segmentacion import detectar_segmentos_voz

FS_ANALISIS = 16000


def cargar_audio_preparado(ruta_wav, fs_objetivo=FS_ANALISIS):
    audio = leer_wav(ruta_wav)
    muestras = audio["muestras"]
    fs = audio["frecuencia_muestreo"]

    if fs != fs_objetivo:
        muestras, fs = remuestrear(muestras, fs, fs_objetivo)

    muestras = normalizar_pico(muestras)

    segmentos = detectar_segmentos_voz(muestras, fs)
    if segmentos:
        inicio = int(segmentos[0]["inicio"] * fs)
        fin = int(segmentos[-1]["fin"] * fs)
        muestras = muestras[inicio:fin]

    if len(muestras) < int(0.05 * fs):
        raise ValueError("La grabacion no contiene voz suficiente para analizarla.")
    return muestras, fs
