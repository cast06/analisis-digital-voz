# ==============================================================
# DETECCION DE ACTIVIDAD DE VOZ (VAD) Y ANALISIS CONTINUO
# ==============================================================

from nucleo.matematicas import raiz_cuadrada
from audio.caracteristicas import (
    calcular_rms, analizar_segmento_completo, UMBRAL_SILENCIO_RMS
)
from audio.referencias import comparar_con_referencias

DURACION_MINIMA_SEGMENTO = 0.060   # s
PAUSA_TOLERADA = 0.100             # s
UMBRAL_RELATIVO = 0.15             # fraccion del RMS maximo
LIMITE_PALABRA_DURACION = 0.85     # s
LIMITE_PALABRA_NUCLEOS = 4


def detectar_segmentos_voz(muestras, fs):
    """
    Detecta segmentos continuos de voz activa mediante:
    1. Division en ventanas de 25 ms con desplazamiento de 10 ms.
    2. Envolvente RMS por ventana (sumas prefijas, O(N)).
    3. Umbral adaptativo  u = max(0.005, 0.15 * RMS_max).
    4. Fusion de ventanas activas separadas por pausas <= 100 ms.
    5. Rechazo de segmentos demasiado cortos (< 60 ms).
    """
    if len(muestras) == 0 or fs <= 0:
        return []

    desplazamiento = 0.010
    tam_ventana = max(1, int(0.025 * fs))
    salto = max(1, int(desplazamiento * fs))

    if len(muestras) < tam_ventana:
        rms_total = calcular_rms(muestras)
        duracion_total = len(muestras) / fs
        if rms_total >= UMBRAL_SILENCIO_RMS and duracion_total >= DURACION_MINIMA_SEGMENTO:
            return [{
                "inicio": 0.0,
                "fin": duracion_total,
                "duracion": duracion_total,
                "muestras": muestras[:]
            }]
        return []

    # Sumas prefijas de cuadrados para calcular el RMS de todas las ventanas en O(N)
    prefijo_cuadrados = [0.0] * (len(muestras) + 1)
    acumulado = 0.0
    for i, muestra in enumerate(muestras):
        acumulado += muestra * muestra
        prefijo_cuadrados[i + 1] = acumulado

    niveles = []
    posiciones = []
    inv_tam = 1.0 / tam_ventana
    inicio = 0
    limite = len(muestras) - tam_ventana

    while inicio <= limite:
        energia_ventana = prefijo_cuadrados[inicio + tam_ventana] - prefijo_cuadrados[inicio]
        niveles.append(raiz_cuadrada(max(0.0, energia_ventana * inv_tam)))
        posiciones.append(inicio)
        inicio += salto

    if not niveles:
        return []

    nivel_maximo = max(niveles)
    if nivel_maximo < UMBRAL_SILENCIO_RMS:
        return []

    umbral = max(UMBRAL_SILENCIO_RMS, nivel_maximo * UMBRAL_RELATIVO)

    activos = [i for i, nivel in enumerate(niveles) if nivel >= umbral]
    if not activos:
        return []

    # Agrupar ventanas activas cercanas permitiendo pausas breves
    tolerancia = int(PAUSA_TOLERADA / desplazamiento)

    grupos = []
    grupo_inicio = activos[0]
    grupo_fin = activos[0]

    for indice in activos[1:]:
        if indice - grupo_fin <= tolerancia + 1:
            grupo_fin = indice
        else:
            grupos.append((grupo_inicio, grupo_fin))
            grupo_inicio = indice
            grupo_fin = indice

    grupos.append((grupo_inicio, grupo_fin))

    segmentos = []
    for primero, ultimo in grupos:
        inicio_muestra = posiciones[primero]
        fin_muestra = min(posiciones[ultimo] + tam_ventana, len(muestras))

        inicio_seg = inicio_muestra / fs
        fin_seg = fin_muestra / fs
        duracion_seg = fin_seg - inicio_seg

        if duracion_seg >= DURACION_MINIMA_SEGMENTO:
            segmentos.append({
                "inicio": inicio_seg,
                "fin": fin_seg,
                "duracion": duracion_seg,
                "muestras": muestras[inicio_muestra:fin_muestra]
            })

    return segmentos


def _estado_reconocimiento(duracion_seg, nucleos, caracteristicas, referencias):
    """Devuelve (estado, palabra_reconocida, coincidencia)."""
    es_continuo = duracion_seg > LIMITE_PALABRA_DURACION or nucleos > LIMITE_PALABRA_NUCLEOS

    if not referencias:
        if es_continuo:
            return ("Segmento continuo multi-palabra (sin banco de referencias "
                    "ni modelo lexico cargado)"), None, None
        return ("Segmento aislado detectado (sin banco de referencias cargado "
                "para reconocimiento)"), None, None

    if es_continuo:
        return ("Segmento continuo con multiples palabras; no se clasifica "
                "como una sola silaba/palabra aislada"), None, None

    coincidencia = comparar_con_referencias(caracteristicas, referencias)
    if coincidencia and coincidencia["aceptada"]:
        palabra = coincidencia["silaba"]
        return (f"Coincidencia acustica cercana: '{palabra}' "
                f"(distancia={coincidencia['distancia']:.4f})"), palabra, coincidencia
    if coincidencia:
        return (f"Sin coincidencia confiable (mas cercano: "
                f"'{coincidencia['silaba']}', distancia={coincidencia['distancia']:.4f})"), None, coincidencia
    return "Sin coincidencia en el banco de referencias", None, None


def analizar_audio_continuo(
        muestras,
        frecuencia_muestreo,
        referencias=None,
        mostrar_progreso=True,
        nombre_archivo=""):
    """
    Detecta segmentos de voz activa en una grabacion continua y extrae
    sus caracteristicas acusticas. Un segmento detectado puede abarcar
    una frase completa; no equivale a una palabra reconocida.
    """
    if not muestras or frecuencia_muestreo <= 0:
        return []

    segmentos = detectar_segmentos_voz(muestras, frecuencia_muestreo)
    total_segmentos = len(segmentos)
    resultados = []

    for numero, segmento in enumerate(segmentos, start=1):
        if mostrar_progreso:
            prefijo = f"[{nombre_archivo}] " if nombre_archivo else ""
            print(
                f"  {prefijo}Procesando segmento {numero}/{total_segmentos} "
                f"({segmento['inicio']:.3f} s - {segmento['fin']:.3f} s)..."
            )

        caracteristicas = analizar_segmento_completo(segmento["muestras"], frecuencia_muestreo)
        if caracteristicas is None:
            continue

        duracion_seg = segmento["fin"] - segmento["inicio"]
        nucleos = caracteristicas.get("nucleos_silabicos", 1)
        estado, palabra, coincidencia = _estado_reconocimiento(
            duracion_seg, nucleos, caracteristicas, referencias
        )

        resultados.append({
            "id_segmento": numero,
            "inicio": segmento["inicio"],
            "fin": segmento["fin"],
            "duracion": duracion_seg,
            "muestras": segmento["muestras"],
            "tipo_segmento": caracteristicas.get("tipo_segmento", "Segmento de voz"),
            "nucleos_silabicos": nucleos,
            "caracteristicas": caracteristicas,
            "palabra": palabra,
            "coincidencia": coincidencia,
            "estado": estado
        })

    return resultados
