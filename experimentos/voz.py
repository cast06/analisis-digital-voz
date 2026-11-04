# ==============================================================
# ANALISIS DETALLADO DE UNA GRABACION REAL
# ==============================================================

from config import FRAGMENTOS_MANUALES, DIRECTORIO_AUDIOS
from nucleo.archivos import nombre_de
from audio.wav import leer_wav
from audio.espectral import dividir_en_ventanas, aplicar_hann, dft, frecuencias_dominantes
from audio.caracteristicas import calcular_rms, extraer_caracteristicas, analizar_segmento_completo
from audio.referencias import comparar_con_referencias
from visual.svg import crear_svg, crear_svg_espectro


def ruta_audio_para_html(ruta):
    """
    El HTML se guarda en salidas/, por lo que un audio de audios/ se
    referencia como ../audios/nombre.wav. Para otras carpetas se usa
    una ruta file:/// absoluta.
    """
    if ruta.replace("\\", "/").startswith(DIRECTORIO_AUDIOS.replace("\\", "/")):
        return "../audios/" + nombre_de(ruta)
    return "file:///" + ruta.replace("\\", "/").lstrip("/")


def analizar_ventana(ventana, frecuencia_muestreo):
    espectro = dft(aplicar_hann(ventana), frecuencia_muestreo)

    # Se reutiliza el espectro para no ejecutar la DFT dos veces
    caracteristicas = extraer_caracteristicas(
        ventana, frecuencia_muestreo, espectro_precalculado=espectro
    )

    return {
        "rms": caracteristicas["rms"],
        "zcr": caracteristicas["zcr"],
        "espectro": espectro,
        "frecuencias": frecuencias_dominantes(espectro, cantidad=10),
        "caracteristicas": caracteristicas
    }


def analizar_voz_real(ruta_audio):
    resultado = {
        "existe": False,
        "archivo": nombre_de(ruta_audio),
        "src_audio": ruta_audio_para_html(ruta_audio),
        "mensaje": f"No se encontro el archivo {ruta_audio}."
    }

    try:
        audio = leer_wav(ruta_audio)
    except FileNotFoundError:
        return resultado
    except Exception as error:
        resultado["mensaje"] = "Error al leer el archivo WAV: " + str(error)
        return resultado

    muestras = audio["muestras"]
    fs = audio["frecuencia_muestreo"]

    resultado.update({
        "existe": True,
        "fs": fs,
        "bits": audio["bits"],
        "canales": audio["canales"],
        "muestras": len(muestras),
        "duracion": audio["duracion"],
        "svg_tiempo": crear_svg(
            muestras[:min(len(muestras), int(fs * 0.5))],
            "07_voz_tiempo.svg", "Forma de onda de voz real"
        )
    })

    ventanas = dividir_en_ventanas(muestras, fs)
    if not ventanas:
        resultado["mensaje"] = (
            "El audio existe, pero es demasiado corto para generar una ventana de 25 ms."
        )
        return resultado

    # Ventana de mayor RMS entre las primeras 100
    limite = min(len(ventanas), 100)
    mejor_indice = 0
    mejor_rms = -1.0
    for i in range(limite):
        energia = calcular_rms(ventanas[i])
        if energia > mejor_rms:
            mejor_rms = energia
            mejor_indice = i

    ventana_elegida = ventanas[mejor_indice]
    datos = analizar_ventana(ventana_elegida, fs)

    resultado.update({
        "mensaje": "",
        "ventanas": len(ventanas),
        "ventana_seleccionada": mejor_indice,
        "rms": datos["rms"],
        "zcr": datos["zcr"],
        "caracteristicas": datos["caracteristicas"],
        "frecuencias": datos["frecuencias"],
        "svg_ventana": crear_svg(ventana_elegida, "08_ventana_voz.svg", "Ventana de voz de 25 ms"),
        "svg_espectro": crear_svg_espectro(
            datos["espectro"], "09_espectro_voz.svg", "Espectro de frecuencias de la voz"
        )
    })
    return resultado


def analizar_fragmentos_voz(ruta_audio, fragmentos=None, referencias=None):
    """
    Analiza intervalos marcados A MANO (config.FRAGMENTOS_MANUALES).
    Las etiquetas las escribe el equipo; el programa no reconoce las palabras.
    """
    if fragmentos is None:
        fragmentos = FRAGMENTOS_MANUALES

    try:
        audio = leer_wav(ruta_audio)
    except (FileNotFoundError, ValueError) as error:
        return {"existe": False, "mensaje": str(error), "fragmentos": []}

    muestras = audio["muestras"]
    fs = audio["frecuencia_muestreo"]
    resultados = []

    for fragmento in fragmentos:
        etiqueta = str(fragmento["etiqueta"])
        inicio_seg = float(fragmento["inicio"])
        fin_seg = float(fragmento["fin"])

        if inicio_seg < 0 or fin_seg <= inicio_seg:
            resultados.append({"etiqueta": etiqueta, "error": "El tiempo de inicio y fin no es válido."})
            continue

        inicio_muestra = int(inicio_seg * fs)
        fin_muestra = min(int(fin_seg * fs), len(muestras))

        if inicio_muestra >= len(muestras):
            resultados.append({"etiqueta": etiqueta, "error": "El inicio queda fuera de la grabación."})
            continue

        segmento = muestras[inicio_muestra:fin_muestra]
        if len(segmento) < 2:
            resultados.append({"etiqueta": etiqueta, "error": "El fragmento contiene muy pocas muestras."})
            continue

        caracteristicas = analizar_segmento_completo(segmento, fs)
        coincidencia = None
        if referencias and caracteristicas:
            coincidencia = comparar_con_referencias(caracteristicas, referencias)

        resultados.append({
            "etiqueta": etiqueta,
            "inicio": inicio_seg,
            "fin": fin_muestra / fs,
            "muestras": len(segmento),
            "duracion": len(segmento) / fs,
            "svg": crear_svg(segmento, f"fragmento_{len(resultados) + 1}.svg",
                             f"Forma de onda: {etiqueta}"),
            "caracteristicas": caracteristicas,
            "coincidencia": coincidencia
        })

    return {
        "existe": True,
        "mensaje": "",
        "fs": fs,
        "duracion_total": audio["duracion"],
        "fragmentos": resultados
    }
