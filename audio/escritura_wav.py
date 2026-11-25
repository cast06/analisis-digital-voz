# ==============================================================
# ESCRITURA MANUAL DE ARCHIVOS WAV (PCM 16 BITS, MONO)
# ==============================================================
# Cabecera RIFF de 44 bytes construida byte por byte:
#   "RIFF" | tamano-8 | "WAVE" | "fmt " | 16 | formato=1 (PCM)
#   | canales | fs | bytes/s | bytes por muestra | bits
#   | "data" | tamano de los datos | muestras little-endian
# ==============================================================


def _entero_a_bytes(valor, cantidad):
    """Entero a bytes little-endian (complemento a dos si es negativo)."""
    if valor < 0:
        valor += 1 << (8 * cantidad)
    return bytes((valor >> (8 * i)) & 0xFF for i in range(cantidad))


def muestras_a_pcm16(muestras):
    """Muestras en [-1, 1] -> bytes PCM de 16 bits con signo."""
    datos = bytearray()
    for valor in muestras:
        entero = int(round(max(-1.0, min(1.0, valor)) * 32767))
        datos += _entero_a_bytes(entero, 2)
    return bytes(datos)


def escribir_wav_pcm16(ruta, datos_pcm, fs):
    """Escribe bytes PCM de 16 bits mono como archivo WAV."""
    if fs <= 0:
        raise ValueError("La frecuencia de muestreo debe ser positiva.")
    if len(datos_pcm) % 2:
        raise ValueError("Los datos PCM de 16 bits deben tener un número par de bytes.")
    canales, bits = 1, 16
    bytes_por_muestra = canales * bits // 8
    cabecera = (b"RIFF" + _entero_a_bytes(36 + len(datos_pcm), 4) + b"WAVE"
                + b"fmt " + _entero_a_bytes(16, 4) + _entero_a_bytes(1, 2)
                + _entero_a_bytes(canales, 2) + _entero_a_bytes(fs, 4)
                + _entero_a_bytes(fs * bytes_por_muestra, 4) + _entero_a_bytes(bytes_por_muestra, 2)
                + _entero_a_bytes(bits, 2) + b"data" + _entero_a_bytes(len(datos_pcm), 4))
    with open(ruta, "wb") as archivo:
        archivo.write(cabecera + datos_pcm)
