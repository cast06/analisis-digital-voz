# ==============================================================
# GRABACION CON EL MICROFONO (usa la libreria externa sounddevice)
# ==============================================================
# sounddevice entrega bloques de bytes PCM de 16 bits desde el
# microfono. Los juntamos y los guardamos con nuestro propio
# escritor WAV (audio/escritura_wav.py). No se usa NumPy.
# Instalar:  pip install sounddevice
# ==============================================================

import config
from audio.escritura_wav import escribir_wav_pcm16


def disponible():
    """(True, "") si se puede usar el microfono; (False, motivo) si no."""
    try:
        import sounddevice
        sounddevice.query_devices(kind="input")
        return True, ""
    except ImportError:
        return False, "falta instalar la librería: pip install sounddevice"
    except Exception as error:
        return False, f"no se encontró un micrófono ({error})"


def grabar(ruta, fs=None, segundos_maximos=None):
    """
    Graba hasta que la persona presiona Enter (o hasta el maximo).
    Devuelve la duracion en segundos. Lanza ValueError si no se grabo nada.
    """
    import sounddevice
    fs = fs or config.FS_GRABACION
    segundos_maximos = segundos_maximos or config.SEGUNDOS_MAXIMOS_GRABACION
    bloques = []

    def recibir(datos, cuadros, tiempo, estado):
        bloques.append(bytes(datos))

    input("\nPresiona Enter y empieza a hablar...")
    with sounddevice.RawInputStream(samplerate=fs, channels=1, dtype="int16", callback=recibir):
        input(f"Grabando (máximo {segundos_maximos} s). Presiona Enter cuando termines.")
    datos = b"".join(bloques)[:fs * 2 * segundos_maximos]
    if len(datos) < fs * 2 // 2:                      # menos de medio segundo
        raise ValueError("La grabación quedó vacía o fue demasiado corta.")
    escribir_wav_pcm16(ruta, datos, fs)
    return len(datos) / (2 * fs)
