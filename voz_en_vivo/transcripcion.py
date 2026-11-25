# ==============================================================
# TRANSCRIPCION DE HABLA LIBRE (usa la libreria externa vosk)
# ==============================================================
# Vosk funciona sin internet con un modelo en espanol que se
# descarga una vez (ver LEEME.md). Leemos el WAV con nuestro propio
# lector, lo convertimos a PCM de 16 bits y se lo damos por bloques.
# El texto resultante pasa despues por NUESTRO procesamiento:
# seguridad, motivo de consulta, duracion y contextos.
# Instalar:  pip install vosk
# ==============================================================

import config
from nucleo.archivos import existe_archivo, unir_ruta
from audio.wav import leer_wav
from audio.escritura_wav import muestras_a_pcm16

TAMANO_BLOQUE = 8000          # bytes (0.25 s a 16 kHz)
_modelo = {}                  # el modelo se carga una sola vez


def disponible():
    """(True, "") si se puede transcribir; (False, motivo) si no."""
    try:
        import vosk
    except ImportError:
        return False, "falta instalar la librería: pip install vosk"
    if not existe_archivo(unir_ruta(config.MODELO_VOSK, "am", "final.mdl")):
        return False, f"falta el modelo en español en {config.MODELO_VOSK}"
    return True, ""


def transcribir(ruta_wav):
    """Devuelve el texto reconocido (en minusculas y sin puntuacion)."""
    import json
    import vosk
    vosk.SetLogLevel(-1)
    if "vosk" not in _modelo:
        _modelo["vosk"] = vosk.Model(config.MODELO_VOSK)
    modelo = _modelo["vosk"]
    audio = leer_wav(ruta_wav)
    reconocedor = vosk.KaldiRecognizer(modelo, audio["frecuencia_muestreo"])
    datos = muestras_a_pcm16(audio["muestras"])
    partes = []
    for inicio in range(0, len(datos), TAMANO_BLOQUE):
        # Cuando vosk cierra una frase, su texto queda en Result()
        if reconocedor.AcceptWaveform(datos[inicio:inicio + TAMANO_BLOQUE]):
            partes.append(json.loads(reconocedor.Result()).get("text", ""))
    partes.append(json.loads(reconocedor.FinalResult()).get("text", ""))
    return " ".join(p for p in partes if p).strip()
