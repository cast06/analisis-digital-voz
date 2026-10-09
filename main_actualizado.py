# ==============================================================
# SISTEMA DE ANALISIS DIGITAL DE VOZ DESDE CERO
# ==============================================================
#
# Proyecto:
# Sistema Inteligente de Orientacion y Vinculacion Psicologica
#
# Este programa:
#
# 1. Genera una onda seno.
# 2. Combina seno y coseno.
# 3. Genera una señal con muchas frecuencias.
# 4. Grafica las señales mediante SVG.
# 5. Lee una grabacion WAV manualmente.
# 6. Convierte el audio digital en muestras numericas.
# 7. Divide la voz en ventanas de 25 ms.
# 8. Aplica una ventana de Hann.
# 9. Implementa Fourier mediante DFT desde cero.
# 10. Encuentra frecuencias dominantes.
# 11. Calcula energia RMS.
# 12. Calcula cruces por cero.
# 13. Genera una pagina HTML con los resultados.
#
# IMPORTANTE:
#
# NO UTILIZA IMPORTS.
#
# No utiliza:
# numpy
# scipy
# matplotlib
# librosa
# wave
# math
# tkinter
# speech_recognition
# APIs
#
# Todo el procesamiento matematico se realiza desde cero.
# La interfaz visual se genera escribiendo HTML, CSS y SVG.
# ==============================================================


# ==============================================================
# 1. CONSTANTES
# ==============================================================

PI = 3.14159265358979323846

FRECUENCIA_MUESTREO = 16000


# ==============================================================
# 2. FUNCIONES MATEMATICAS DESDE CERO
# ==============================================================


def valor_absoluto(numero):

    if numero < 0:
        return -numero

    return numero


def raiz_cuadrada(numero):

    if numero < 0:

        raise ValueError(
            "No existe raiz cuadrada real de un numero negativo."
        )

    if numero == 0:

        return 0.0

    aproximacion = numero

    if numero < 1:

        aproximacion = 1.0

    for _ in range(25):

        aproximacion = (
            aproximacion
            +
            numero / aproximacion
        ) / 2.0

    return aproximacion


def normalizar_angulo(angulo):

    dos_pi = 2.0 * PI

    while angulo > PI:

        angulo -= dos_pi

    while angulo < -PI:

        angulo += dos_pi

    return angulo


def seno(angulo):

    x = normalizar_angulo(angulo)

    termino = x

    resultado = x

    for n in range(1, 12):

        termino *= (
            -1.0
            *
            x
            *
            x
            /
            (
                (2 * n)
                *
                (2 * n + 1)
            )
        )

        resultado += termino

    return resultado


def coseno(angulo):

    x = normalizar_angulo(angulo)

    termino = 1.0

    resultado = 1.0

    for n in range(1, 12):

        termino *= (
            -1.0
            *
            x
            *
            x
            /
            (
                (2 * n - 1)
                *
                (2 * n)
            )
        )

        resultado += termino

    return resultado


# ==============================================================
# 3. GENERAR ONDA SENO
# ==============================================================


def generar_seno(
        frecuencia,
        duracion=0.05,
        amplitud=1.0,
        frecuencia_muestreo=FRECUENCIA_MUESTREO):

    numero_muestras = int(
        frecuencia_muestreo
        *
        duracion
    )

    muestras = []

    for n in range(numero_muestras):

        tiempo = (
            n
            /
            frecuencia_muestreo
        )

        angulo = (
            2.0
            *
            PI
            *
            frecuencia
            *
            tiempo
        )

        valor = (
            amplitud
            *
            seno(angulo)
        )

        muestras.append(valor)

    return muestras


# ==============================================================
# 4. SENO + COSENO
# ==============================================================


def generar_seno_coseno(
        duracion=0.05,
        frecuencia_muestreo=FRECUENCIA_MUESTREO):

    numero_muestras = int(
        frecuencia_muestreo
        *
        duracion
    )

    muestras = []

    for n in range(numero_muestras):

        tiempo = (
            n
            /
            frecuencia_muestreo
        )

        componente_seno = seno(
            2.0
            *
            PI
            *
            250.0
            *
            tiempo
        )

        componente_coseno = (
            0.5
            *
            coseno(
                2.0
                *
                PI
                *
                500.0
                *
                tiempo
            )
        )

        valor = (
            componente_seno
            +
            componente_coseno
        )

        muestras.append(valor)

    return muestras


# ==============================================================
# 5. SEÑAL COMPLEJA
# ==============================================================


def generar_senal_compleja(
        duracion=0.05,
        frecuencia_muestreo=FRECUENCIA_MUESTREO):

    componentes = [

        (125.0, 1.00),

        (250.0, 0.70),

        (375.0, 0.50),

        (750.0, 0.40),

        (1250.0, 0.30),

        (2500.0, 0.15)

    ]

    numero_muestras = int(
        frecuencia_muestreo
        *
        duracion
    )

    muestras = []

    for n in range(numero_muestras):

        tiempo = (
            n
            /
            frecuencia_muestreo
        )

        valor_total = 0.0

        for frecuencia, amplitud in componentes:

            angulo = (
                2.0
                *
                PI
                *
                frecuencia
                *
                tiempo
            )

            valor_total += (
                amplitud
                *
                seno(angulo)
            )

        muestras.append(
            valor_total
        )

    return muestras


# ==============================================================
# 6. MAXIMO ABSOLUTO
# ==============================================================


def maximo_absoluto(muestras):

    mayor = 0.0

    for valor in muestras:

        absoluto = valor_absoluto(valor)

        if absoluto > mayor:

            mayor = absoluto

    return mayor


# ==============================================================
# 7. CREAR SVG DE UNA SEÑAL
# ==============================================================


def crear_svg(
        muestras,
        nombre_archivo,
        titulo,
        ancho=1200,
        alto=450):

    if len(muestras) < 2:

        return ""

    maximo = maximo_absoluto(muestras)

    if maximo == 0:

        maximo = 1.0

    margen = 50

    ancho_grafica = (
        ancho
        -
        2 * margen
    )

    alto_grafica = (
        alto
        -
        2 * margen
    )

    puntos = []

    for i in range(len(muestras)):

        x = (
            margen
            +
            (
                i
                /
                (len(muestras) - 1)
            )
            *
            ancho_grafica
        )

        normalizado = (
            muestras[i]
            /
            maximo
        )

        y = (
            alto / 2
            -
            normalizado
            *
            alto_grafica
            *
            0.45
        )

        punto = (
            str(round(x, 2))
            +
            ","
            +
            str(round(y, 2))
        )

        puntos.append(punto)

    contenido = ""

    contenido += (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="' +
        str(ancho) +
        '" '
        'height="' +
        str(alto) +
        '" '
        'viewBox="0 0 ' +
        str(ancho) +
        ' ' +
        str(alto) +
        '">'
    )

    contenido += (
        '<rect width="100%" '
        'height="100%" '
        'fill="white"/>'
    )

    contenido += (
        '<text x="50" y="30" '
        'font-family="Arial" '
        'font-size="18">'
        +
        titulo
        +
        '</text>'
    )

    contenido += (
        '<line '
        'x1="' +
        str(margen) +
        '" '
        'y1="' +
        str(alto / 2) +
        '" '
        'x2="' +
        str(ancho - margen) +
        '" '
        'y2="' +
        str(alto / 2) +
        '" '
        'stroke="gray"/>'
    )

    contenido += (
        '<line '
        'x1="' +
        str(margen) +
        '" '
        'y1="' +
        str(margen) +
        '" '
        'x2="' +
        str(margen) +
        '" '
        'y2="' +
        str(alto - margen) +
        '" '
        'stroke="gray"/>'
    )

    contenido += (
        '<polyline '
        'fill="none" '
        'stroke="black" '
        'stroke-width="1" '
        'points="' +
        " ".join(puntos) +
        '"/>'
    )

    contenido += "</svg>"

    with open(
        nombre_archivo,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(contenido)

    return contenido


# ==============================================================
# 8. LEER ENTEROS LITTLE-ENDIAN
# ==============================================================


def entero_little_endian(
        datos,
        posicion,
        cantidad_bytes,
        con_signo=False):

    valor = 0

    for i in range(cantidad_bytes):

        valor += (
            datos[posicion + i]
            <<
            (8 * i)
        )

    if con_signo:

        numero_bits = (
            cantidad_bytes
            *
            8
        )

        limite_signo = (
            1
            <<
            (numero_bits - 1)
        )

        if valor >= limite_signo:

            valor -= (
                1
                <<
                numero_bits
            )

    return valor


# ==============================================================
# 9. LEER WAV DESDE CERO
# ==============================================================


def leer_wav(nombre_archivo):

    with open(
        nombre_archivo,
        "rb"
    ) as archivo:

        datos = archivo.read()

    if datos[0:4] != b"RIFF":

        raise ValueError(
            "El archivo no contiene una cabecera RIFF."
        )

    if datos[8:12] != b"WAVE":

        raise ValueError(
            "El archivo no corresponde a formato WAVE."
        )

    posicion = 12

    formato_audio = None
    canales = None
    frecuencia_muestreo = None
    bits_por_muestra = None
    datos_audio = None

    while posicion + 8 <= len(datos):

        chunk_id = datos[
            posicion:
            posicion + 4
        ]

        chunk_size = entero_little_endian(
            datos,
            posicion + 4,
            4
        )

        inicio_chunk = (
            posicion
            +
            8
        )

        if chunk_id == b"fmt ":

            formato_audio = entero_little_endian(
                datos,
                inicio_chunk,
                2
            )

            canales = entero_little_endian(
                datos,
                inicio_chunk + 2,
                2
            )

            frecuencia_muestreo = entero_little_endian(
                datos,
                inicio_chunk + 4,
                4
            )

            bits_por_muestra = entero_little_endian(
                datos,
                inicio_chunk + 14,
                2
            )

        elif chunk_id == b"data":

            datos_audio = datos[
                inicio_chunk:
                inicio_chunk + chunk_size
            ]

            break

        posicion = (
            inicio_chunk
            +
            chunk_size
        )

        if chunk_size % 2 == 1:

            posicion += 1

    if formato_audio != 1:

        raise ValueError(
            "Solamente se admite audio PCM sin compresion."
        )

    if bits_por_muestra != 16:

        raise ValueError(
            "Este programa trabaja con PCM de 16 bits."
        )

    if datos_audio is None:

        raise ValueError(
            "No se encontro el bloque de audio."
        )

    bytes_por_canal = 2

    bytes_por_frame = (
        bytes_por_canal
        *
        canales
    )

    muestras = []

    posicion = 0

    while (
        posicion
        +
        bytes_por_frame
        <=
        len(datos_audio)
    ):

        suma_canales = 0.0

        for canal in range(canales):

            inicio = (
                posicion
                +
                canal
                *
                bytes_por_canal
            )

            valor = entero_little_endian(
                datos_audio,
                inicio,
                2,
                con_signo=True
            )

            suma_canales += valor

        valor_mono = (
            suma_canales
            /
            canales
        )

        normalizado = (
            valor_mono
            /
            32768.0
        )

        muestras.append(normalizado)

        posicion += bytes_por_frame

    return {

        "muestras": muestras,

        "frecuencia_muestreo":
            frecuencia_muestreo,

        "canales":
            canales,

        "bits":
            bits_por_muestra

    }


# ==============================================================
# 10. DIVIDIR EN VENTANAS
# ==============================================================


def dividir_en_ventanas(
        muestras,
        frecuencia_muestreo,
        duracion_ms=25,
        desplazamiento_ms=10):

    tamano = int(
        frecuencia_muestreo
        *
        duracion_ms
        /
        1000
    )

    desplazamiento = int(
        frecuencia_muestreo
        *
        desplazamiento_ms
        /
        1000
    )

    ventanas = []

    inicio = 0

    while (
        inicio + tamano
        <=
        len(muestras)
    ):

        ventana = muestras[
            inicio:
            inicio + tamano
        ]

        ventanas.append(ventana)

        inicio += desplazamiento

    return ventanas


# ==============================================================
# 11. VENTANA DE HANN
# ==============================================================


def aplicar_hann(muestras):

    N = len(muestras)

    if N <= 1:

        return muestras[:]

    salida = []

    for n in range(N):

        factor = (
            0.5
            -
            0.5
            *
            coseno(
                2.0
                *
                PI
                *
                n
                /
                (N - 1)
            )
        )

        valor = (
            muestras[n]
            *
            factor
        )

        salida.append(valor)

    return salida


# ==============================================================
# 12. DFT
# ==============================================================


def dft(
        muestras,
        frecuencia_muestreo):

    N = len(muestras)

    if N == 0:

        return []

    espectro = []

    mitad = N // 2

    for k in range(mitad):

        real = 0.0

        imaginaria = 0.0

        for n in range(N):

            angulo = (
                2.0
                *
                PI
                *
                k
                *
                n
                /
                N
            )

            real += (
                muestras[n]
                *
                coseno(angulo)
            )

            imaginaria -= (
                muestras[n]
                *
                seno(angulo)
            )

        magnitud = raiz_cuadrada(
            real * real
            +
            imaginaria * imaginaria
        )

        magnitud = (
            magnitud
            /
            N
        )

        frecuencia = (
            k
            *
            frecuencia_muestreo
            /
            N
        )

        espectro.append(
            (
                frecuencia,
                magnitud
            )
        )

    return espectro


# ==============================================================
# 13. FRECUENCIAS DOMINANTES
# ==============================================================


def frecuencias_dominantes(
        espectro,
        cantidad=10,
        frecuencia_minima=20,
        frecuencia_maxima=4000):

    candidatos = []

    for frecuencia, magnitud in espectro:

        if (
            frecuencia >= frecuencia_minima
            and
            frecuencia <= frecuencia_maxima
        ):

            candidatos.append(
                (
                    frecuencia,
                    magnitud
                )
            )

    candidatos.sort(
        key=lambda elemento:
            elemento[1],
        reverse=True
    )

    return candidatos[:cantidad]


# ==============================================================
# 14. RMS
# ==============================================================


def calcular_rms(muestras):

    if len(muestras) == 0:

        return 0.0

    suma = 0.0

    for valor in muestras:

        suma += (
            valor
            *
            valor
        )

    promedio = (
        suma
        /
        len(muestras)
    )

    return raiz_cuadrada(promedio)


# ==============================================================
# 15. ZERO CROSSING RATE
# ==============================================================


def zero_crossing_rate(muestras):

    if len(muestras) < 2:

        return 0.0

    cruces = 0

    for i in range(
        1,
        len(muestras)
    ):

        anterior = muestras[i - 1]

        actual = muestras[i]

        if (
            anterior >= 0
            and
            actual < 0
        ):

            cruces += 1

        elif (
            anterior < 0
            and
            actual >= 0
        ):

            cruces += 1

    tasa = (
        cruces
        /
        (len(muestras) - 1)
    )

    return tasa


# ==============================================================
# 16. CREAR SVG DEL ESPECTRO
# ==============================================================


def crear_svg_espectro(
        espectro,
        nombre_archivo,
        titulo,
        frecuencia_maxima=4000,
        ancho=1200,
        alto=450):

    frecuencias = []

    magnitudes = []

    for frecuencia, magnitud in espectro:

        if frecuencia <= frecuencia_maxima:

            frecuencias.append(frecuencia)

            magnitudes.append(magnitud)

    if len(frecuencias) < 2:

        return ""

    maximo = maximo_absoluto(magnitudes)

    if maximo == 0:

        maximo = 1.0

    margen = 50

    ancho_grafica = (
        ancho
        -
        2 * margen
    )

    alto_grafica = (
        alto
        -
        2 * margen
    )

    puntos = []

    for i in range(len(frecuencias)):

        frecuencia = frecuencias[i]

        magnitud = magnitudes[i]

        x = (
            margen
            +
            (
                frecuencia
                /
                frecuencia_maxima
            )
            *
            ancho_grafica
        )

        y = (
            alto
            -
            margen
            -
            (
                magnitud
                /
                maximo
            )
            *
            alto_grafica
        )

        puntos.append(
            str(round(x, 2))
            +
            ","
            +
            str(round(y, 2))
        )

    contenido = ""

    contenido += (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="' +
        str(ancho) +
        '" '
        'height="' +
        str(alto) +
        '" '
        'viewBox="0 0 ' +
        str(ancho) +
        ' ' +
        str(alto) +
        '">'
    )

    contenido += (
        '<rect width="100%" '
        'height="100%" '
        'fill="white"/>'
    )

    contenido += (
        '<text x="50" y="30" '
        'font-family="Arial" '
        'font-size="18">'
        +
        titulo
        +
        '</text>'
    )

    contenido += (
        '<line '
        'x1="50" '
        'y1="400" '
        'x2="1150" '
        'y2="400" '
        'stroke="gray"/>'
    )

    contenido += (
        '<line '
        'x1="50" '
        'y1="50" '
        'x2="50" '
        'y2="400" '
        'stroke="gray"/>'
    )

    contenido += (
        '<polyline '
        'fill="none" '
        'stroke="black" '
        'stroke-width="1" '
        'points="' +
        " ".join(puntos) +
        '"/>'
    )

    contenido += "</svg>"

    with open(
        nombre_archivo,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(contenido)

    return contenido


# ==============================================================
# 17. CONVERTIR FRECUENCIAS A HTML
# ==============================================================


def frecuencias_a_html(frecuencias):

    if len(frecuencias) == 0:

        return (
            "<p>No se encontraron frecuencias "
            "dominantes.</p>"
        )

    html = ""

    html += '<table class="tabla">'

    html += (
        "<tr>"
        "<th>Frecuencia</th>"
        "<th>Magnitud</th>"
        "</tr>"
    )

    for frecuencia, magnitud in frecuencias:

        html += (
            "<tr>"
            "<td>" +
            str(round(frecuencia, 2)) +
            " Hz</td>"
            "<td>" +
            str(round(magnitud, 6)) +
            "</td>"
            "</tr>"
        )

    html += "</table>"

    return html


# ==============================================================
# 18. EXPERIMENTO 1
# ==============================================================


def experimento_seno():

    senal = generar_seno(
        frecuencia=250,
        duracion=0.05
    )

    segmento = senal[:512]

    espectro = dft(
        segmento,
        FRECUENCIA_MUESTREO
    )

    dominantes = frecuencias_dominantes(
        espectro,
        cantidad=5
    )

    svg_senal = crear_svg(
        senal,
        "01_seno_250Hz.svg",
        "Onda seno pura de 250 Hz"
    )

    svg_espectro = crear_svg_espectro(
        espectro,
        "02_espectro_seno.svg",
        "Espectro de frecuencia - Seno 250 Hz"
    )

    return {

        "senal": svg_senal,

        "espectro": svg_espectro,

        "frecuencias":
            dominantes

    }


# ==============================================================
# 19. EXPERIMENTO 2
# ==============================================================


def experimento_seno_coseno():

    senal = generar_seno_coseno()

    segmento = senal[:512]

    espectro = dft(
        segmento,
        FRECUENCIA_MUESTREO
    )

    dominantes = frecuencias_dominantes(
        espectro,
        cantidad=8
    )

    svg_senal = crear_svg(
        senal,
        "03_seno_coseno.svg",
        "Combinacion seno 250 Hz + coseno 500 Hz"
    )

    svg_espectro = crear_svg_espectro(
        espectro,
        "04_espectro_seno_coseno.svg",
        "Espectro - Seno + Coseno"
    )

    return {

        "senal": svg_senal,

        "espectro": svg_espectro,

        "frecuencias":
            dominantes

    }


# ==============================================================
# 20. EXPERIMENTO 3
# ==============================================================


def experimento_senal_compleja():

    senal = generar_senal_compleja()

    segmento = senal[:512]

    espectro = dft(
        segmento,
        FRECUENCIA_MUESTREO
    )

    dominantes = frecuencias_dominantes(
        espectro,
        cantidad=10
    )

    svg_senal = crear_svg(
        senal,
        "05_senal_compleja.svg",
        "Señal formada por multiples frecuencias"
    )

    svg_espectro = crear_svg_espectro(
        espectro,
        "06_espectro_complejo.svg",
        "Espectro de señal compleja"
    )

    return {

        "senal": svg_senal,

        "espectro": svg_espectro,

        "frecuencias":
            dominantes

    }


# ==============================================================
# 21. ANALIZAR UNA VENTANA DE VOZ
# ==============================================================


def analizar_ventana(
        ventana,
        frecuencia_muestreo):

    ventana_hann = aplicar_hann(
        ventana
    )

    espectro = dft(
        ventana_hann,
        frecuencia_muestreo
    )

    dominantes = frecuencias_dominantes(
        espectro,
        cantidad=10
    )

    rms = calcular_rms(
        ventana
    )

    zcr = zero_crossing_rate(
        ventana
    )

    return {

        "rms": rms,

        "zcr": zcr,

        "espectro": espectro,

        "frecuencias":
            dominantes

    }


# ==============================================================
# 22. ANALISIS DE VOZ REAL
# ==============================================================


def analizar_voz_real(
        nombre_archivo="voz.wav"):

    resultado = {

        "existe": False,

        "mensaje":
            "No se encontro el archivo voz.wav."

    }

    try:

        audio = leer_wav(
            nombre_archivo
        )

    except FileNotFoundError:

        return resultado

    except ValueError as error:

        resultado["mensaje"] = (
            "Error al leer el archivo WAV: "
            +
            str(error)
        )

        return resultado

    muestras = audio["muestras"]

    fs = audio["frecuencia_muestreo"]

    duracion = (
        len(muestras)
        /
        fs
    )

    cantidad = int(
        fs
        *
        0.5
    )

    if cantidad > len(muestras):

        cantidad = len(muestras)

    svg_tiempo = crear_svg(
        muestras[:cantidad],
        "07_voz_tiempo.svg",
        "Forma de onda de voz real"
    )

    ventanas = dividir_en_ventanas(
        muestras,
        fs,
        duracion_ms=25,
        desplazamiento_ms=10
    )

    if len(ventanas) == 0:

        resultado["existe"] = True

        resultado["mensaje"] = (
            "El audio existe, pero es demasiado corto "
            "para generar una ventana de 25 ms."
        )

        resultado["fs"] = fs

        resultado["bits"] = audio["bits"]

        resultado["canales"] = audio["canales"]

        resultado["muestras"] = len(muestras)

        resultado["duracion"] = duracion

        resultado["svg_tiempo"] = svg_tiempo

        return resultado

    limite = len(ventanas)

    if limite > 100:

        limite = 100

    mejor_indice = 0

    mejor_rms = -1.0

    for i in range(limite):

        energia = calcular_rms(
            ventanas[i]
        )

        if energia > mejor_rms:

            mejor_rms = energia

            mejor_indice = i

    ventana_elegida = ventanas[
        mejor_indice
    ]

    datos = analizar_ventana(
        ventana_elegida,
        fs
    )

    svg_ventana = crear_svg(
        ventana_elegida,
        "08_ventana_voz.svg",
        "Ventana de voz de 25 ms"
    )

    svg_espectro = crear_svg_espectro(
        datos["espectro"],
        "09_espectro_voz.svg",
        "Espectro de frecuencias de la voz"
    )

    resultado = {

        "existe": True,

        "fs": fs,

        "bits": audio["bits"],

        "canales": audio["canales"],

        "muestras": len(muestras),

        "duracion": duracion,

        "ventanas": len(ventanas),

        "ventana_seleccionada":
            mejor_indice,

        "rms":
            datos["rms"],

        "zcr":
            datos["zcr"],

        "frecuencias":
            datos["frecuencias"],

        "svg_tiempo":
            svg_tiempo,

        "svg_ventana":
            svg_ventana,

        "svg_espectro":
            svg_espectro

    }

    return resultado


# ==============================================================
# 23. ANALISIS DE VOZ POR PALABRA O FRAGMENTO
# ==============================================================

# EDITA esta lista con las etiquetas y los tiempos reales de tu grabacion.
# Los tiempos se expresan en segundos: inicio incluido y fin excluido.
# Estos dos intervalos son SOLO ejemplos; no identifican automaticamente palabras.

FRAGMENTOS_VOZ = [
    {"etiqueta": "Hola", "inicio": 0.00, "fin": 0.65},
    {"etiqueta": "Cómo", "inicio": 0.65, "fin": 1.10},
    {"etiqueta": "Estás", "inicio": 1.10, "fin": 2.00}
]



def analizar_fragmentos_voz(nombre_archivo="voz.wav", fragmentos=None):

    if fragmentos is None:
        fragmentos = FRAGMENTOS_VOZ

    try:
        audio = leer_wav(nombre_archivo)
    except (FileNotFoundError, ValueError) as error:
        return {"existe": False, "mensaje": str(error), "fragmentos": []}

    muestras = audio["muestras"]
    fs = audio["frecuencia_muestreo"]
    duracion_total = len(muestras) / fs
    resultados = []

    for fragmento in fragmentos:
        etiqueta = str(fragmento["etiqueta"])
        inicio_seg = float(fragmento["inicio"])
        fin_seg = float(fragmento["fin"])

        if inicio_seg < 0 or fin_seg <= inicio_seg:
            resultados.append({
                "etiqueta": etiqueta,
                "error": "El tiempo de inicio y fin no es válido."
            })
            continue

        inicio_muestra = int(inicio_seg * fs)
        fin_muestra = int(fin_seg * fs)

        if inicio_muestra >= len(muestras):
            resultados.append({
                "etiqueta": etiqueta,
                "error": "El inicio queda fuera de la grabación."
            })
            continue

        if fin_muestra > len(muestras):
            fin_muestra = len(muestras)

        segmento = muestras[inicio_muestra:fin_muestra]

        if len(segmento) < 2:
            resultados.append({
                "etiqueta": etiqueta,
                "error": "El fragmento contiene muy pocas muestras."
            })
            continue

        nombre_svg = "fragmento_" + str(len(resultados) + 1) + ".svg"
        svg = crear_svg(
            segmento,
            nombre_svg,
            "Forma de onda: " + etiqueta
        )

        resultados.append({
            "etiqueta": etiqueta,
            "inicio": inicio_seg,
            "fin": fin_muestra / fs,
            "muestras": len(segmento),
            "duracion": len(segmento) / fs,
            "svg": svg
        })

    return {
        "existe": True,
        "mensaje": "",
        "fs": fs,
        "duracion_total": duracion_total,
        "fragmentos": resultados
    }


# ==============================================================
# 24. GENERAR PAGINA WEB
# ==============================================================


def generar_html(
        experimento1,
        experimento2,
        experimento3,
        voz,
        fragmentos_voz):

    html = ""

    # ----------------------------------------------------------
    # INICIO DEL DOCUMENTO
    # ----------------------------------------------------------

    html += """
<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>
Sistema de Analisis Digital de Voz
</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family: Arial, sans-serif;

    background: #eeeeee;

    color: #222222;

}

.encabezado {

    background: #222222;

    color: white;

    padding: 25px;

    text-align: center;

}

.encabezado h1 {

    margin: 0;

    font-size: 28px;

}

.encabezado p {

    margin-top: 10px;

    margin-bottom: 0;

}

.menu {

    background: #333333;

    padding: 12px;

    text-align: center;

    position: sticky;

    top: 0;

    z-index: 10;

}

.menu button {

    border: none;

    padding: 12px 18px;

    margin: 4px;

    cursor: pointer;

    background: white;

    color: #222222;

    border-radius: 5px;

    font-size: 14px;

}

.menu button:hover {

    background: #dddddd;

}

.contenedor {

    width: 94%;

    max-width: 1400px;

    margin: 25px auto;

}

.ventana {

    display: none;

    background: white;

    border: 1px solid #cccccc;

    border-radius: 8px;

    padding: 25px;

    margin-bottom: 25px;

    box-shadow: 0 3px 8px rgba(0,0,0,0.10);

}

.ventana.activa {

    display: block;

}

.ventana h2 {

    margin-top: 0;

    border-bottom: 1px solid #dddddd;

    padding-bottom: 12px;

}

.tarjetas {

    display: flex;

    flex-wrap: wrap;

    gap: 15px;

    margin: 20px 0;

}

.tarjeta {

    border: 1px solid #cccccc;

    border-radius: 6px;

    padding: 18px;

    min-width: 180px;

    flex: 1;

    background: #fafafa;

}

.tarjeta strong {

    display: block;

    font-size: 22px;

    margin-top: 7px;

}

.grafica {

    width: 100%;

    overflow-x: auto;

    border: 1px solid #dddddd;

    margin-top: 15px;

    padding: 10px;

    background: white;

}

.grafica svg {

    max-width: 100%;

    height: auto;

}

.dos_columnas {

    display: grid;

    grid-template-columns: 1fr 1fr;

    gap: 20px;

}

.tabla {

    width: 100%;

    border-collapse: collapse;

    margin-top: 15px;

}

.tabla th,
.tabla td {

    border: 1px solid #cccccc;

    padding: 10px;

    text-align: left;

}

.tabla th {

    background: #eeeeee;

}

.info {

    padding: 15px;

    border-left: 4px solid #555555;

    background: #f5f5f5;

    margin: 15px 0;

}

.pie {

    text-align: center;

    padding: 25px;

    color: #666666;

}

@media(max-width: 800px) {

    .dos_columnas {

        grid-template-columns: 1fr;

    }

    .menu button {

        width: 90%;

    }

}

</style>

<script>

function mostrarVentana(id) {

    var ventanas =
        document.getElementsByClassName("ventana");

    for (var i = 0;
         i < ventanas.length;
         i++) {

        ventanas[i].classList.remove("activa");

    }

    var seleccionada =
        document.getElementById(id);

    seleccionada.classList.add("activa");

    window.scrollTo(0, 0);

}

</script>

</head>

<body>

<div class="encabezado">

<h1>
SISTEMA DE ANÁLISIS DIGITAL DE VOZ
</h1>

<p>
Procesamiento digital de señales desde cero
</p>

</div>

<div class="menu">

<button onclick="mostrarVentana('inicio')">
Inicio
</button>

<button onclick="mostrarVentana('seno')">
Experimento 1
</button>

<button onclick="mostrarVentana('senocoseno')">
Experimento 2
</button>

<button onclick="mostrarVentana('compleja')">
Experimento 3
</button>

<button onclick="mostrarVentana('voz')">
Voz real
</button>

<button onclick="mostrarVentana('fragmentos')">
Palabras o letras
</button>

</div>

<div class="contenedor">
"""


    # ==========================================================
    # VENTANA INICIO
    # ==========================================================

    html += """

<div id="inicio" class="ventana activa">

<h2>
Inicio
</h2>

<p>
Este sistema realiza diferentes etapas de procesamiento
digital de señales utilizando implementaciones propias.
</p>

<div class="tarjetas">

<div class="tarjeta">
Procesamiento matemático
<strong>Desde cero</strong>
</div>

<div class="tarjeta">
Transformada
<strong>DFT</strong>
</div>

<div class="tarjeta">
Ventana temporal
<strong>25 ms</strong>
</div>

<div class="tarjeta">
Desplazamiento
<strong>10 ms</strong>
</div>

</div>

<div class="info">

<strong>Importante:</strong>

Este programa extrae propiedades físicas y matemáticas
de una señal de voz. Los resultados obtenidos no constituyen
un diagnóstico de emociones, trastornos o estados psicológicos.

</div>

<h3>
Procesamiento utilizado
</h3>

<ul>

<li>Generación de señales sinusoidales.</li>

<li>Funciones seno y coseno mediante Taylor.</li>

<li>Lectura manual de archivos WAV.</li>

<li>Ventanas temporales.</li>

<li>Ventana de Hann.</li>

<li>Transformada Discreta de Fourier.</li>

<li>Frecuencias dominantes.</li>

<li>RMS.</li>

<li>Zero Crossing Rate.</li>

<li>Representación gráfica mediante SVG.</li>

</ul>

</div>

"""


    # ==========================================================
    # EXPERIMENTO 1
    # ==========================================================

    html += """

<div id="seno" class="ventana">

<h2>
Experimento 1: Onda seno pura
</h2>

<p>
Se genera una señal sinusoidal de 250 Hz.
Posteriormente se analiza su contenido frecuencial
mediante la Transformada Discreta de Fourier.
</p>

<div class="tarjetas">

<div class="tarjeta">
Frecuencia
<strong>250 Hz</strong>
</div>

<div class="tarjeta">
Duración
<strong>0.05 s</strong>
</div>

<div class="tarjeta">
Frecuencia de muestreo
<strong>16000 Hz</strong>
</div>

<div class="tarjeta">
Muestras
<strong>
"""

    html += str(800)

    html += """
</strong>
</div>

</div>

<h3>
Señal en el dominio del tiempo
</h3>

<div class="grafica">
"""

    html += experimento1["senal"]

    html += """
</div>

<h3>
Espectro de frecuencia
</h3>

<div class="grafica">
"""

    html += experimento1["espectro"]

    html += """
</div>

<h3>
Frecuencias dominantes
</h3>

"""

    html += frecuencias_a_html(
        experimento1["frecuencias"]
    )

    html += """

</div>

"""


    # ==========================================================
    # EXPERIMENTO 2
    # ==========================================================

    html += """

<div id="senocoseno" class="ventana">

<h2>
Experimento 2: Seno + Coseno
</h2>

<p>
La señal está formada por una componente seno
de 250 Hz y una componente coseno de 500 Hz
con amplitud de 0.5.
</p>

<div class="tarjetas">

<div class="tarjeta">
Componente 1
<strong>250 Hz</strong>
</div>

<div class="tarjeta">
Componente 2
<strong>500 Hz</strong>
</div>

<div class="tarjeta">
Amplitud coseno
<strong>0.5</strong>
</div>

</div>

<h3>
Señal en el dominio del tiempo
</h3>

<div class="grafica">
"""

    html += experimento2["senal"]

    html += """
</div>

<h3>
Espectro de frecuencia
</h3>

<div class="grafica">
"""

    html += experimento2["espectro"]

    html += """
</div>

<h3>
Frecuencias dominantes
</h3>

"""

    html += frecuencias_a_html(
        experimento2["frecuencias"]
    )

    html += """

</div>

"""


    # ==========================================================
    # EXPERIMENTO 3
    # ==========================================================

    html += """

<div id="compleja" class="ventana">

<h2>
Experimento 3: Señal compleja
</h2>

<p>
La señal está formada por múltiples componentes
sinusoidales con diferentes frecuencias y amplitudes.
</p>

<div class="tarjetas">

<div class="tarjeta">
Componentes
<strong>6</strong>
</div>

<div class="tarjeta">
Frecuencia mínima
<strong>125 Hz</strong>
</div>

<div class="tarjeta">
Frecuencia máxima
<strong>2500 Hz</strong>
</div>

</div>

<h3>
Señal en el dominio del tiempo
</h3>

<div class="grafica">
"""

    html += experimento3["senal"]

    html += """
</div>

<h3>
Espectro de frecuencia
</h3>

<div class="grafica">
"""

    html += experimento3["espectro"]

    html += """
</div>

<h3>
Frecuencias dominantes
</h3>

"""

    html += frecuencias_a_html(
        experimento3["frecuencias"]
    )

    html += """

</div>

"""


    # ==========================================================
    # VENTANA VOZ REAL
    # ==========================================================

    html += """

<div id="voz" class="ventana">

<h2>
Análisis de voz real
</h2>
<h3>Escuchar grabación</h3>

<audio controls preload="metadata">
    <source src="voz.wav" type="audio/wav">
    Tu navegador no puede reproducir este audio.
</audio>

"""

    if not voz["existe"]:

        html += """

<div class="info">

<strong>
No se pudo realizar el análisis.
</strong>

<p>
"""

        html += voz["mensaje"]

        html += """

</p>

<p>
Agregar el archivo 
<strong>voz.wav</strong>
</p>

</div>

"""

    else:

        if "ventanas" not in voz:

            html += """

<div class="info">

"""

            html += voz["mensaje"]

            html += """

</div>

<div class="grafica">

"""

            html += voz["svg_tiempo"]

            html += """

</div>

"""

        else:

            html += """

<p>
El archivo de voz fue leído directamente mediante
el procesamiento implementado en este programa.
</p>

<div class="tarjetas">

<div class="tarjeta">
Frecuencia de muestreo
<strong>
"""

            html += str(voz["fs"])

            html += """
 Hz
</strong>
</div>

<div class="tarjeta">
Bits
<strong>
"""

            html += str(voz["bits"])

            html += """
</strong>
</div>

<div class="tarjeta">
Canales
<strong>
"""

            html += str(voz["canales"])

            html += """
</strong>
</div>

<div class="tarjeta">
Muestras
<strong>
"""

            html += str(voz["muestras"])

            html += """
</strong>
</div>

<div class="tarjeta">
Duración
<strong>
"""

            html += str(round(voz["duracion"], 3))

            html += """
 s
</strong>
</div>

<div class="tarjeta">
Ventanas
<strong>
"""

            html += str(voz["ventanas"])

            html += """
</strong>
</div>

</div>

<h3>
Forma de onda de la voz
</h3>

<div class="grafica">

"""

            html += voz["svg_tiempo"]

            html += """

</div>

<h3>
Ventana seleccionada
</h3>

<div class="info">

La ventana seleccionada corresponde al segmento con
mayor RMS dentro de las primeras ventanas analizadas.

<br><br>

<strong>
Índice de ventana:
</strong>
"""

            html += str(
                voz["ventana_seleccionada"]
            )

            html += """

<br>

<strong>
Duración de ventana:
</strong>
25 ms

<br>

<strong>
Desplazamiento:
</strong>
10 ms

</div>

<div class="dos_columnas">

<div>

<h3>
RMS
</h3>

<div class="tarjeta">

Medida de energía de la señal

<strong>
"""

            html += str(
                round(
                    voz["rms"],
                    6
                )
            )

            html += """

</strong>

</div>

</div>

<div>

<h3>
Zero Crossing Rate
</h3>

<div class="tarjeta">

Tasa de cruces por cero

<strong>
"""

            html += str(
                round(
                    voz["zcr"],
                    6
                )
            )

            html += """

</strong>

</div>

</div>

</div>

<h3>
Ventana de voz de 25 ms
</h3>

<div class="grafica">

"""

            html += voz["svg_ventana"]

            html += """

</div>

<h3>
Espectro de la voz
</h3>

<div class="grafica">

"""

            html += voz["svg_espectro"]

            html += """

</div>

<h3>
Frecuencias dominantes
</h3>

"""

            html += frecuencias_a_html(
                voz["frecuencias"]
            )

            html += """

<div class="info">

Las frecuencias dominantes representan componentes
frecuenciales con mayor magnitud dentro del fragmento
analizado. No representan por sí mismas una emoción
o diagnóstico psicológico.

</div>

"""

    html += """

</div>

<div id="fragmentos" class="ventana">

<h2>Análisis por palabra o fragmento</h2>

<p>Esta sección grafica intervalos del archivo WAV. Es necesario indicar manualmente la etiqueta y los tiempos de inicio y fin en la lista FRAGMENTOS_VOZ del archivo Python. El programa no reconoce palabras automáticamente.</p>

"""

    if not fragmentos_voz["existe"]:
        html += "<div class=\"info\">No se pudieron leer los fragmentos: " + fragmentos_voz["mensaje"] + "</div>"
    else:
        html += "<div class=\"tarjetas\"><div class=\"tarjeta\">Duración total<strong>" + str(round(fragmentos_voz["duracion_total"], 3)) + " s</strong></div><div class=\"tarjeta\">Frecuencia de muestreo<strong>" + str(fragmentos_voz["fs"]) + " Hz</strong></div></div>"
        if len(fragmentos_voz["fragmentos"]) == 0:
            html += "<div class=\"info\">No se configuraron fragmentos.</div>"
        for indice, fragmento in enumerate(fragmentos_voz["fragmentos"]):
            html += "<h3>" + fragmento["etiqueta"] + "</h3>"
            if "error" in fragmento:
                html += "<div class=\"info\">" + fragmento["error"] + "</div>"
            else:
                html += "<p>Tiempo: " + str(round(fragmento["inicio"], 3)) + " s a " + str(round(fragmento["fin"], 3)) + " s. Duración: " + str(round(fragmento["duracion"], 3)) + " s. Muestras: " + str(fragmento["muestras"]) + ".</p>"
                html += "<div class=\"grafica\">" + fragmento["svg"] + "</div>"

    html += """

</div>

</div>

<div class="pie">

Sistema de Análisis Digital de Voz desde Cero

</div>

<script>

mostrarVentana('inicio');

</script>

</body>

</html>
"""


    with open(
        "resultado.html",
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(html)


# ==============================================================
# 25. PROGRAMA PRINCIPAL
# ==============================================================


def main():

    experimento1 = experimento_seno()

    experimento2 = experimento_seno_coseno()

    experimento3 = experimento_senal_compleja()

    voz = analizar_voz_real(
    r"C:\Users\sharo\Downloads\temas selectos\nuevo\voz.wav"
    )
    fragmentos_voz = analizar_fragmentos_voz(
    r"C:\Users\sharo\Downloads\temas selectos\nuevo\voz.wav"
    )

    generar_html(
        experimento1,
        experimento2,
        experimento3,
        voz,
        fragmentos_voz
    )


# ==============================================================
# 26. EJECUCION
# ==============================================================


if __name__ == "__main__":

    main()