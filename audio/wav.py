# ==============================================================
# LECTURA MANUAL DE ARCHIVOS WAV (PCM SIN COMPRESION)
# ==============================================================

from nucleo.archivos import existe_archivo


def entero_little_endian(
        datos,
        posicion,
        cantidad_bytes,
        con_signo=False):
    """
    Convierte 'cantidad_bytes' bytes en orden little-endian a entero:
        valor = sum( byte_i * 2^(8 i) )
    Si con_signo=True se interpreta en complemento a dos.
    """
    if posicion < 0 or posicion + cantidad_bytes > len(datos):
        raise ValueError("Lectura fuera de los limites del bloque binario.")

    valor = 0

    for i in range(cantidad_bytes):
        valor += datos[posicion + i] << (8 * i)

    if con_signo:
        numero_bits = cantidad_bytes * 8
        limite_signo = 1 << (numero_bits - 1)
        if valor >= limite_signo:
            valor -= 1 << numero_bits

    return valor


def leer_wav(nombre_archivo):
    """
    Lector manual de archivos WAV sin compresion (PCM).
    Inspecciona los bloques RIFF/WAVE, valida 'fmt ' y 'data',
    convierte audio estereo/multicanal a mono y normaliza las muestras
    en el rango [-1.0, 1.0].
    Soporta explicitamente PCM de 8, 16, 24 y 32 bits.
    """
    if not existe_archivo(nombre_archivo):
        raise FileNotFoundError(
            f"No se encontro el archivo de audio: {nombre_archivo}"
        )

    with open(nombre_archivo, "rb") as archivo:
        datos = archivo.read()

    if len(datos) < 44:
        raise ValueError(
            "El archivo es demasiado pequeño o esta vacio (menos de 44 bytes)."
        )

    if datos[0:4] != b"RIFF":
        raise ValueError(
            "El archivo no contiene una cabecera RIFF valida."
        )

    if datos[8:12] != b"WAVE":
        raise ValueError(
            "El archivo no corresponde al formato WAVE."
        )

    posicion = 12

    formato_audio = None
    canales = None
    frecuencia_muestreo = None
    bits_por_muestra = None
    datos_audio = None

    while posicion + 8 <= len(datos):
        chunk_id = datos[posicion:posicion + 4]
        chunk_size = entero_little_endian(datos, posicion + 4, 4)
        inicio_chunk = posicion + 8

        if chunk_size < 0 or inicio_chunk > len(datos):
            break

        if chunk_id == b"fmt ":
            if chunk_size < 16 or inicio_chunk + 16 > len(datos):
                raise ValueError(
                    "El bloque 'fmt ' del archivo WAV esta incompleto o dañado."
                )

            formato_audio = entero_little_endian(datos, inicio_chunk, 2)
            canales = entero_little_endian(datos, inicio_chunk + 2, 2)
            frecuencia_muestreo = entero_little_endian(datos, inicio_chunk + 4, 4)
            bits_por_muestra = entero_little_endian(datos, inicio_chunk + 14, 2)

        elif chunk_id == b"data":
            fin_datos = min(inicio_chunk + chunk_size, len(datos))
            datos_audio = datos[inicio_chunk:fin_datos]
            break

        posicion = inicio_chunk + chunk_size
        if chunk_size % 2 == 1:
            posicion += 1

    if formato_audio is None:
        raise ValueError("El archivo WAV no contiene el bloque 'fmt '.")

    if formato_audio != 1:
        raise ValueError(
            f"Formato de audio WAV no soportado (codigo {formato_audio}). "
            "Solamente se admite audio PCM sin compresion (codigo 1)."
        )

    if canales is None or canales < 1:
        raise ValueError(
            f"Numero de canales invalido en el archivo WAV: {canales}."
        )

    if frecuencia_muestreo is None or frecuencia_muestreo <= 0:
        raise ValueError(
            f"Frecuencia de muestreo invalida en el archivo WAV: {frecuencia_muestreo}."
        )

    if bits_por_muestra not in (8, 16, 24, 32):
        raise ValueError(
            f"Profundidad de bits no soportada ({bits_por_muestra} bits). "
            "Este lector admite PCM sin compresion de 8, 16, 24 o 32 bits."
        )

    if datos_audio is None:
        raise ValueError(
            "No se encontro el bloque 'data' con muestras de audio."
        )

    bytes_por_canal = bits_por_muestra // 8
    bytes_por_frame = bytes_por_canal * canales
    total_frames = len(datos_audio) // bytes_por_frame
    limite_bytes = total_frames * bytes_por_frame

    muestras = []

    # Rutas rapidas para PCM de 16 bits (formato estandar del proyecto)
    if bits_por_muestra == 16 and canales == 1:
        escala = 1.0 / 32768.0
        for pos in range(0, limite_bytes, 2):
            valor = datos_audio[pos] | (datos_audio[pos + 1] << 8)
            if valor >= 32768:
                valor -= 65536
            muestras.append(valor * escala)

    elif bits_por_muestra == 16 and canales == 2:
        escala = 1.0 / (2.0 * 32768.0)
        for pos in range(0, limite_bytes, 4):
            izq = datos_audio[pos] | (datos_audio[pos + 1] << 8)
            if izq >= 32768:
                izq -= 65536
            der = datos_audio[pos + 2] | (datos_audio[pos + 3] << 8)
            if der >= 32768:
                der -= 65536
            muestras.append((izq + der) * escala)

    elif bits_por_muestra == 8:
        # En WAV PCM de 8 bits las muestras son enteras sin signo [0, 255]
        escala = 1.0 / 128.0
        for pos in range(0, limite_bytes, bytes_por_frame):
            suma_canales = 0.0
            for c in range(canales):
                suma_canales += (datos_audio[pos + c] - 128) * escala
            muestras.append(suma_canales / canales)

    else:
        # PCM con signo de 16 bits (>2 canales), 24 bits o 32 bits
        max_positivo = float(1 << (bits_por_muestra - 1))
        escala = 1.0 / (canales * max_positivo)
        for pos in range(0, limite_bytes, bytes_por_frame):
            suma_canales = 0
            for c in range(canales):
                inicio = pos + c * bytes_por_canal
                valor = entero_little_endian(
                    datos_audio,
                    inicio,
                    bytes_por_canal,
                    con_signo=True
                )
                suma_canales += valor
            muestras.append(suma_canales * escala)

    duracion = len(muestras) / frecuencia_muestreo if frecuencia_muestreo > 0 else 0.0

    return {
        "muestras": muestras,
        "frecuencia_muestreo": frecuencia_muestreo,
        "canales": canales,
        "bits": bits_por_muestra,
        "num_muestras": len(muestras),
        "duracion": duracion
    }
