# ==============================================================
# EXTRACCION DEL VECTOR DE CARACTERISTICAS ACUSTICAS
# ==============================================================
#
# Variables elegidas por el equipo para describir cada segmento de
# voz. Se definen aqui UNA SOLA VEZ para que el orden del vector sea
# el mismo en todo el programa (reportes, comparacion y, despues,
# los modelos).
#
# Estas variables describen propiedades fisicas de la señal. No se
# interpretan como indicadores de un estado clinico.
# ==============================================================

from nucleo.matematicas import raiz_cuadrada, maximo_absoluto, media, desviacion_estandar
from audio.espectral import dividir_en_ventanas, aplicar_hann, dft


# Vector oficial de 12 variables por segmento de voz (orden fijo)
VARIABLES_SEGMENTO = [
    "amplitud_maxima",          # max |x[n]|
    "pico_a_pico",              # max x[n] - min x[n]
    "rms",                      # sqrt( (1/N) sum x[n]^2 ), promedio por ventana
    "zcr",                      # cruces por cero / (N - 1), promedio por ventana
    "frecuencia_dominante",     # f con mayor |X[k]|, promedio por ventana
    "frecuencia_fundamental",   # F0 por autocorrelacion, promedio en ventanas sonoras
    "variacion_f0",             # desviacion estandar de F0
    "duracion",                 # N / fs
    "tiempo_hablado",           # ventanas con RMS >= umbral
    "tiempo_silencio",          # ventanas con RMS < umbral
    "centroide_espectral",      # sum f*|X| / sum |X|
    "ancho_banda_espectral"     # sqrt( sum (f - c)^2 |X| / sum |X| )
]

# Vector auxiliar por ventana de 25 ms (se conserva el orden original).
# Nota: 'energia' depende de la longitud y 'frecuencia_muestreo' es
# constante, por lo que este vector no debe usarse para comparar
# segmentos; para eso se usa VARIABLES_SEGMENTO.
VARIABLES_VENTANA = [
    "amplitud_maxima",
    "rms",
    "energia",
    "zcr",
    "duracion",
    "frecuencia_dominante",
    "centroide_espectral",
    "ancho_banda_espectral",
    "frecuencia_fundamental",
    "frecuencia_muestreo"
]

# Vector para reconocimiento de emociones (11 variables).
# Cambios respecto a VARIABLES_SEGMENTO y por que:
# - Sin amplitud maxima ni pico a pico: dependen del volumen del
#   microfono (en MESD todas las grabaciones tienen pico = 1).
# - Sin energia: es RMS^2 * N y crece con la duracion.
# - Duracion, tiempo hablado y silencio se sustituyen por
#   proporcion_silencio y tasa_silabica, que no dependen de lo
#   larga que sea la frase.
# - Se agregan rango_f0 y variacion_rms (dinamica de la voz).
VARIABLES_EMOCION = [
    "rms",                      # intensidad media (relativa al pico)
    "variacion_rms",            # desv. estandar del RMS entre ventanas
    "zcr",
    "frecuencia_dominante",
    "centroide_espectral",
    "ancho_banda_espectral",
    "frecuencia_fundamental",   # F0 media
    "variacion_f0",             # desv. estandar de F0
    "rango_f0",                 # F0 max - F0 min
    "proporcion_silencio",      # tiempo_silencio / duracion
    "tasa_silabica"             # nucleos silabicos / tiempo hablado
]

# Umbral de RMS por debajo del cual se considera silencio (~ -46 dBFS)
UMBRAL_SILENCIO_RMS = 0.005


def construir_vector(caracteristicas, nombres):
    return [caracteristicas[nombre] for nombre in nombres]


# --------------------------------------------------------------
# Medidas en el dominio del tiempo
# --------------------------------------------------------------


def calcular_rms(muestras):
    n = len(muestras)
    if n == 0:
        return 0.0

    suma = sum(valor * valor for valor in muestras)
    return raiz_cuadrada(suma / n)


def zero_crossing_rate(muestras):
    n = len(muestras)
    if n < 2:
        return 0.0

    cruces = 0
    anterior = muestras[0]

    for i in range(1, n):
        actual = muestras[i]
        if (anterior >= 0.0 and actual < 0.0) or (anterior < 0.0 and actual >= 0.0):
            cruces += 1
        anterior = actual

    return cruces / (n - 1)


def calcular_amplitud_maxima(muestras):
    return maximo_absoluto(muestras)


def calcular_energia(muestras):
    return sum(muestra * muestra for muestra in muestras)


# --------------------------------------------------------------
# Medidas en el dominio de la frecuencia
# --------------------------------------------------------------


def calcular_frecuencia_dominante(espectro):
    if not espectro:
        return 0.0

    frecuencia_mayor = 0.0
    magnitud_mayor = 0.0

    for frecuencia, magnitud in espectro:
        if frecuencia > 0.0 and magnitud > magnitud_mayor:
            magnitud_mayor = magnitud
            frecuencia_mayor = frecuencia

    return frecuencia_mayor


def calcular_centroide_espectral(espectro):
    if not espectro:
        return 0.0

    suma_magnitudes = 0.0
    suma_ponderada = 0.0

    for frecuencia, magnitud in espectro:
        suma_magnitudes += magnitud
        suma_ponderada += frecuencia * magnitud

    if suma_magnitudes == 0.0:
        return 0.0

    return suma_ponderada / suma_magnitudes


def calcular_ancho_banda_espectral(espectro, centroide=None):
    if not espectro:
        return 0.0

    if centroide is None:
        centroide = calcular_centroide_espectral(espectro)

    suma_magnitudes = 0.0
    suma_ponderada = 0.0

    for frecuencia, magnitud in espectro:
        diferencia = frecuencia - centroide
        suma_ponderada += diferencia * diferencia * magnitud
        suma_magnitudes += magnitud

    if suma_magnitudes == 0.0:
        return 0.0

    return raiz_cuadrada(suma_ponderada / suma_magnitudes)


def estimar_frecuencia_fundamental(
        muestras,
        frecuencia_muestreo,
        f0_maxima=400.0):
    """
    Estima la frecuencia fundamental (F0) mediante autocorrelacion normalizada
    en el rango vocal humano [70 Hz, f0_maxima] (400 Hz por defecto):
        r(L) = sum x[n] x[n+L] / sqrt( sum x[n]^2 * sum x[n+L]^2 )
        F0 = fs / L*,   L* = argmax r(L)
    Optimizada mediante sumas prefijas de cuadrados para evaluar la energia
    de los segmentos desplazados en O(1) por cada lag.
    """
    N = len(muestras)
    if N < 64 or frecuencia_muestreo <= 0:
        return 0.0

    lag_minimo = max(1, int(frecuencia_muestreo / f0_maxima))
    lag_maximo = min(N // 2, int(frecuencia_muestreo / 70.0))

    if lag_minimo > lag_maximo:
        return 0.0

    # Precalcular sumas acumuladas de cuadrados en O(N)
    prefijo_cuadrados = [0.0] * (N + 1)
    energia_total = 0.0
    for i, valor in enumerate(muestras):
        energia_total += valor * valor
        prefijo_cuadrados[i + 1] = energia_total

    # Ignorar silencio o ruido de fondo insignificante
    if energia_total / N < 1e-8:
        return 0.0

    mejor_lag = 0
    mejor_correlacion = -1.0

    for lag in range(lag_minimo, lag_maximo + 1):
        limite = N - lag
        suma_a = prefijo_cuadrados[limite]
        suma_b = energia_total - prefijo_cuadrados[lag]

        producto_energias = suma_a * suma_b
        if producto_energias <= 0.0:
            continue

        suma_producto = sum(
            a * b for a, b in zip(muestras[:limite], muestras[lag:])
        )
        denominador = raiz_cuadrada(producto_energias)
        if denominador == 0.0:
            continue

        correlacion = suma_producto / denominador
        if correlacion > mejor_correlacion:
            mejor_correlacion = correlacion
            mejor_lag = lag

    if mejor_lag == 0 or mejor_correlacion < 0.30:
        return 0.0

    return frecuencia_muestreo / mejor_lag


# --------------------------------------------------------------
# Caracteristicas de una ventana
# --------------------------------------------------------------


def extraer_caracteristicas(
        muestras,
        frecuencia_muestreo,
        espectro_precalculado=None,
        f0_maxima=400.0):

    if frecuencia_muestreo <= 0 or len(muestras) == 0:
        caracteristicas = {
            "amplitud_maxima": 0.0,
            "pico_a_pico": 0.0,
            "rms": 0.0,
            "energia": 0.0,
            "zcr": 0.0,
            "duracion": 0.0,
            "frecuencia_dominante": 0.0,
            "centroide_espectral": 0.0,
            "ancho_banda_espectral": 0.0,
            "frecuencia_fundamental": 0.0,
            "variacion_f0": 0.0,
            "tiempo_hablado": 0.0,
            "tiempo_silencio": 0.0,
            "frecuencia_muestreo": max(0, frecuencia_muestreo)
        }
    else:
        duracion = len(muestras) / frecuencia_muestreo

        if espectro_precalculado is not None:
            espectro = espectro_precalculado
        else:
            muestras_hann = aplicar_hann(muestras)
            espectro = dft(muestras_hann, frecuencia_muestreo)

        centroide = calcular_centroide_espectral(espectro)
        ancho_banda = calcular_ancho_banda_espectral(espectro, centroide=centroide)
        rms = calcular_rms(muestras)
        f0 = estimar_frecuencia_fundamental(muestras, frecuencia_muestreo, f0_maxima)
        hay_voz = rms > UMBRAL_SILENCIO_RMS

        caracteristicas = {
            "amplitud_maxima": calcular_amplitud_maxima(muestras),
            "pico_a_pico": max(muestras) - min(muestras),
            "rms": rms,
            "energia": calcular_energia(muestras),
            "zcr": zero_crossing_rate(muestras),
            "duracion": duracion,
            "frecuencia_dominante": calcular_frecuencia_dominante(espectro),
            "centroide_espectral": centroide,
            "ancho_banda_espectral": ancho_banda,
            "frecuencia_fundamental": f0,
            "variacion_f0": 0.0,
            "tiempo_hablado": duracion if hay_voz else 0.0,
            "tiempo_silencio": 0.0 if hay_voz else duracion,
            "frecuencia_muestreo": frecuencia_muestreo
        }

    caracteristicas["vector"] = construir_vector(caracteristicas, VARIABLES_VENTANA)
    return caracteristicas


# --------------------------------------------------------------
# Nucleos silabicos y tipo de segmento
# --------------------------------------------------------------


def estimar_nucleos_silabicos(niveles_rms, desplazamiento_seg=0.010):
    """
    Cuenta picos locales de energia vocal separados por al menos 120 ms
    para estimar cuantos nucleos silabicos contiene un segmento de voz.
    Permite distinguir entre una silaba/palabra aislada y una frase
    continua con varias palabras consecutivas.
    """
    if not niveles_rms:
        return 0

    max_rms = max(niveles_rms)
    if max_rms < UMBRAL_SILENCIO_RMS:
        return 0

    umbral_pico = max_rms * 0.30
    separacion_min = max(1, int(0.120 / desplazamiento_seg))

    picos = 0
    ultimo_pico = -separacion_min - 1

    for i in range(len(niveles_rms)):
        actual = niveles_rms[i]
        if actual < umbral_pico:
            continue

        izq = niveles_rms[i - 1] if i > 0 else actual
        der = niveles_rms[i + 1] if i + 1 < len(niveles_rms) else actual

        if actual >= izq and actual >= der:
            if i - ultimo_pico >= separacion_min:
                picos += 1
                ultimo_pico = i

    if picos == 0 and max_rms >= UMBRAL_SILENCIO_RMS:
        picos = 1

    return picos


def clasificar_tipo_segmento(duracion, nucleos_silabicos):
    """
    Clasifica la unidad acustica detectada para no confundir un segmento
    continuo de varias palabras con una sola palabra reconocida.
    """
    if duracion < 0.35 and nucleos_silabicos <= 2:
        return "Silaba o vocablo corto aislado"
    if duracion <= 0.85 and nucleos_silabicos <= 4:
        return "Palabra o locucion breve"
    return f"Frase o secuencia continua (~{nucleos_silabicos} nucleos silabicos)"


# --------------------------------------------------------------
# Caracteristicas de un segmento completo (vector oficial)
# --------------------------------------------------------------


def _seleccionar_uniformes(ventanas, cantidad=20):
    """Toma hasta 'cantidad' ventanas repartidas uniformemente."""
    if len(ventanas) <= cantidad:
        return ventanas
    seleccionadas = []
    for i in range(cantidad):
        indice = int(i * (len(ventanas) - 1) / (cantidad - 1))
        seleccionadas.append(ventanas[indice])
    return seleccionadas


def analizar_segmento_completo(muestras, frecuencia_muestreo, f0_maxima=400.0):
    if len(muestras) == 0 or frecuencia_muestreo <= 0:
        return None

    duracion = len(muestras) / frecuencia_muestreo
    energia_total_segmento = calcular_energia(muestras)

    ventanas_tiempo = dividir_en_ventanas(muestras, frecuencia_muestreo)
    if not ventanas_tiempo:
        ventanas_tiempo = [muestras]

    # Solo 20 ventanas pasan por la DFT para limitar el costo O(N^2)
    ventanas_dft = _seleccionar_uniformes(ventanas_tiempo, 20)
    resultados = [
        extraer_caracteristicas(v, frecuencia_muestreo, f0_maxima=f0_maxima)
        for v in ventanas_dft
    ]

    nombres_promedio = [
        "amplitud_maxima",
        "rms",
        "zcr",
        "frecuencia_dominante",
        "centroide_espectral",
        "ancho_banda_espectral"
    ]

    promedios = {}
    for nombre in nombres_promedio:
        promedios[nombre] = media([datos[nombre] for datos in resultados])

    # F0 promedio y desviacion estandar solo en ventanas sonoras (F0 > 0)
    valores_f0 = [
        datos["frecuencia_fundamental"]
        for datos in resultados
        if datos["frecuencia_fundamental"] > 0
    ]
    f0_promedio = media(valores_f0)
    variacion_f0 = desviacion_estandar(valores_f0)

    # Tiempo hablado, silencio interno y nucleos silabicos mediante RMS
    niveles_rms = [calcular_rms(ventana) for ventana in ventanas_tiempo]

    max_rms = max(niveles_rms) if niveles_rms else 0.0
    umbral = max_rms * 0.15 if max_rms > 0 else 0.0

    tiempo_hablado = 0.0
    tiempo_silencio = 0.0
    paso_segundos = 0.010

    for nivel in niveles_rms:
        if nivel >= umbral and umbral > 0:
            tiempo_hablado += paso_segundos
        else:
            tiempo_silencio += paso_segundos

    tiempo_total = tiempo_hablado + tiempo_silencio
    if tiempo_total > duracion and tiempo_total > 0:
        factor = duracion / tiempo_total
        tiempo_hablado *= factor
        tiempo_silencio *= factor

    nucleos_silabicos = estimar_nucleos_silabicos(niveles_rms, paso_segundos)

    promedios["energia"] = energia_total_segmento
    promedios["pico_a_pico"] = max(muestras) - min(muestras)
    promedios["frecuencia_fundamental"] = f0_promedio
    promedios["variacion_f0"] = variacion_f0
    promedios["duracion"] = duracion
    promedios["tiempo_hablado"] = tiempo_hablado
    promedios["tiempo_silencio"] = tiempo_silencio
    promedios["frecuencia_muestreo"] = frecuencia_muestreo
    promedios["nucleos_silabicos"] = nucleos_silabicos
    promedios["tipo_segmento"] = clasificar_tipo_segmento(duracion, nucleos_silabicos)
    promedios["f0_disponible"] = len(valores_f0) > 0
    promedios["espectro_disponible"] = promedios["rms"] > 0.0

    # Variables adicionales para reconocimiento de emociones
    promedios["rango_f0"] = (max(valores_f0) - min(valores_f0)) if valores_f0 else 0.0
    promedios["variacion_rms"] = desviacion_estandar(niveles_rms)
    promedios["proporcion_silencio"] = tiempo_silencio / duracion if duracion > 0 else 0.0
    promedios["tasa_silabica"] = (
        nucleos_silabicos / tiempo_hablado if tiempo_hablado > 0 else 0.0
    )

    promedios["vector"] = construir_vector(promedios, VARIABLES_SEGMENTO)
    return promedios
