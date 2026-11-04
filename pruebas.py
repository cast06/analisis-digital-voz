# ==============================================================
# PRUEBAS VERIFICABLES DEL MODULO DE AUDIO
# ==============================================================
# Cada prueba compara el resultado contra un valor conocido.
# Ejecutar:  python pruebas.py
# ==============================================================

from config import ruta_salida
from nucleo.matematicas import PI, raiz_cuadrada, seno, coseno, valor_absoluto, desviacion_estandar
from audio.wav import entero_little_endian, leer_wav
from audio.senales import generar_seno
from audio.espectral import dft, aplicar_hann
from audio.caracteristicas import (
    calcular_rms, zero_crossing_rate, estimar_frecuencia_fundamental,
    calcular_frecuencia_dominante, analizar_segmento_completo, VARIABLES_SEGMENTO
)
from audio.segmentacion import detectar_segmentos_voz
from visual.svg import crear_svg_espectro
from nucleo.matematicas import exponencial, logaritmo_natural, softmax, similitud_coseno
from nucleo.aleatorio import GeneradorAleatorio
from audio.remuestreo import remuestrear
from emociones.mesd import interpretar_nombre_mesd
from modelos.red_neuronal import RedNeuronal
from modelos.evaluacion import matriz_confusion, metricas_por_clase, exactitud
from audio.fft import fft_real
from audio.mfcc import hz_a_mel, mel_a_hz, dct_ii, calcular_mfcc, vector_longitud_fija
from emociones.preparacion import asignar_pliegues_estratificados
from palabras.datos_palabras import interpretar_nombre_palabra
from texto.nlp import normalizar_texto, terminos, VectorizadorTFIDF
from texto.seguridad import evaluar_prioridad
from texto.extraccion import extraer_duracion, extraer_contextos
from modelos.naive_bayes import NaiveBayesMultinomial

_resultados = {"ok": 0, "fallo": 0}


def comprobar(nombre, obtenido, esperado, tolerancia=1e-9):
    correcto = valor_absoluto(obtenido - esperado) <= tolerancia
    _resultados["ok" if correcto else "fallo"] += 1
    marca = "OK   " if correcto else "FALLO"
    print(f"[{marca}] {nombre}: obtenido={obtenido} esperado={esperado}")


def comprobar_verdadero(nombre, condicion):
    _resultados["ok" if condicion else "fallo"] += 1
    print(f"[{'OK   ' if condicion else 'FALLO'}] {nombre}")


def _entero_a_bytes(valor, cantidad):
    """Inverso de entero_little_endian (complemento a dos)."""
    if valor < 0:
        valor += 1 << (8 * cantidad)
    return bytes((valor >> (8 * i)) & 0xFF for i in range(cantidad))


def escribir_wav_prueba(ruta, muestras, fs):
    """Escribe un WAV PCM mono de 16 bits construyendo los bytes a mano."""
    datos = bytearray()
    for valor in muestras:
        entero = int(round(max(-1.0, min(1.0, valor)) * 32767))
        datos += _entero_a_bytes(entero, 2)

    cabecera = bytearray()
    cabecera += b"RIFF" + _entero_a_bytes(36 + len(datos), 4) + b"WAVE"
    cabecera += b"fmt " + _entero_a_bytes(16, 4)
    cabecera += _entero_a_bytes(1, 2) + _entero_a_bytes(1, 2)          # PCM, mono
    cabecera += _entero_a_bytes(fs, 4) + _entero_a_bytes(fs * 2, 4)    # fs, bytes/s
    cabecera += _entero_a_bytes(2, 2) + _entero_a_bytes(16, 2)         # bloque, bits
    cabecera += b"data" + _entero_a_bytes(len(datos), 4)

    with open(ruta, "wb") as archivo:
        archivo.write(bytes(cabecera + datos))


def pruebas_matematicas():
    print("\n--- Funciones matematicas ---")
    comprobar("raiz(2)", raiz_cuadrada(2.0), 1.4142135623730951, 1e-14)
    comprobar("raiz(1e-18)", raiz_cuadrada(1e-18), 1e-9, 1e-22)
    comprobar("seno(pi/6)", seno(PI / 6), 0.5, 1e-12)
    comprobar("coseno(pi/3)", coseno(PI / 3), 0.5, 1e-12)
    comprobar("seno(1000) (reduccion de angulo)", seno(1000.0), 0.8268795405320025, 1e-10)
    comprobar("sen^2 + cos^2 = 1", seno(2.3) ** 2 + coseno(2.3) ** 2, 1.0, 1e-12)
    comprobar("desviacion estandar [2,4,4,4,5,5,7,9]",
              desviacion_estandar([2, 4, 4, 4, 5, 5, 7, 9]), 2.0, 1e-12)


def pruebas_senales():
    print("\n--- Señales y espectro ---")
    fs = 16000
    senal = generar_seno(250, duracion=512 / fs, frecuencia_muestreo=fs)
    espectro = dft(senal, fs)
    comprobar("DFT: pico del seno de 250 Hz", calcular_frecuencia_dominante(espectro), 250.0)
    # Para un seno de amplitud 1 en un bin exacto, |X[k]|/N = 0.5
    magnitud_pico = max(m for _, m in espectro)
    comprobar("DFT: magnitud normalizada del pico", magnitud_pico, 0.5, 1e-9)

    comprobar("RMS de un seno de amplitud 1 = 1/sqrt(2)", calcular_rms(senal), 1 / raiz_cuadrada(2), 1e-6)
    # Un seno de 250 Hz cruza cero 500 veces por segundo
    comprobar("ZCR del seno de 250 Hz (cruces/muestra)", zero_crossing_rate(senal), 500 / fs, 0.002)
    comprobar("F0 por autocorrelacion (200 Hz)",
              estimar_frecuencia_fundamental(generar_seno(200, 0.04, frecuencia_muestreo=fs), fs),
              200.0, 1e-9)

    # Prueba de Hann: los extremos valen 0
    ventana = aplicar_hann([1.0] * 400)
    comprobar("Hann: primer coeficiente", ventana[0], 0.0, 1e-12)


def pruebas_wav_y_vad():
    print("\n--- Lectura WAV y deteccion de voz ---")
    comprobar("entero little-endian con signo (0xFFFF = -1)",
              entero_little_endian(b"\xff\xff", 0, 2, con_signo=True), -1)

    fs = 16000
    silencio = [0.0] * int(0.3 * fs)
    tono = generar_seno(200, duracion=0.5, amplitud=0.5, frecuencia_muestreo=fs)
    ruta = ruta_salida("prueba_tono.wav")
    escribir_wav_prueba(ruta, silencio + tono + silencio, fs)

    audio = leer_wav(ruta)
    comprobar("WAV: numero de muestras leidas", audio["num_muestras"], len(silencio) * 2 + len(tono))
    comprobar("WAV: frecuencia de muestreo", audio["frecuencia_muestreo"], fs)

    segmentos = detectar_segmentos_voz(audio["muestras"], fs)
    comprobar("VAD: segmentos detectados", len(segmentos), 1)
    if segmentos:
        comprobar("VAD: inicio del segmento (s)", segmentos[0]["inicio"], 0.3, 0.03)
        comprobar("VAD: fin del segmento (s)", segmentos[0]["fin"], 0.8, 0.03)
        c = analizar_segmento_completo(segmentos[0]["muestras"], fs)
        comprobar("Segmento: F0 promedio", c["frecuencia_fundamental"], 200.0, 2.0)
        comprobar("Segmento: longitud del vector", len(c["vector"]), len(VARIABLES_SEGMENTO))


def pruebas_svg():
    print("\n--- Graficas ---")
    espectro = [(f * 10.0, 1.0) for f in range(100)]
    svg = crear_svg_espectro(espectro, "", "prueba", ancho=600, alto=300)
    comprobar_verdadero("Espectro: eje X ajustado al tamaño (y=250, x2=550)",
                        'y1="250" x2="550" y2="250"' in svg)


def pruebas_matematicas_red():
    print("\n--- Funciones para la red neuronal ---")
    comprobar("exp(1)", exponencial(1.0), 2.718281828459045, 1e-14)
    comprobar("exp(-20)", exponencial(-20.0), 2.061153622438558e-09, 1e-22)
    comprobar("ln(10)", logaritmo_natural(10.0), 2.302585092994046, 1e-14)
    comprobar("ln(exp(3.7)) = 3.7", logaritmo_natural(exponencial(3.7)), 3.7, 1e-13)
    p = softmax([1000.0, 1000.0, 1000.0])
    comprobar("softmax estable con valores grandes", p[0], 1 / 3, 1e-12)
    comprobar("similitud coseno de vectores paralelos", similitud_coseno([1, 2, 3], [2, 4, 6]), 1.0, 1e-12)

    a = GeneradorAleatorio(5)
    b = GeneradorAleatorio(5)
    comprobar_verdadero("Generador reproducible con la misma semilla",
                        [a.uniforme() for _ in range(5)] == [b.uniforme() for _ in range(5)])
    g = GeneradorAleatorio(1)
    valores = [g.normal() for _ in range(20000)]
    comprobar("Box-Muller: media ~ 0", sum(valores) / len(valores), 0.0, 0.03)
    comprobar("Box-Muller: desviacion ~ 1", desviacion_estandar(valores), 1.0, 0.03)


def pruebas_red_neuronal():
    print("\n--- Red neuronal ---")
    # Verificacion de gradientes por diferencias finitas:
    #   dJ/dw ~ (J(w + h) - J(w - h)) / (2h)
    red = RedNeuronal([3, 5, 4, 3], semilla=11)
    g = GeneradorAleatorio(3)
    X = [[g.normal() for _ in range(3)] for _ in range(6)]
    Y = [0, 1, 2, 1, 0, 2]
    l2 = 0.01
    gW, gb = red.gradientes(X, Y, l2)
    h = 1e-6
    error_maximo = 0.0
    for l in range(len(red.pesos)):
        for i in range(len(red.pesos[l])):
            for j in range(len(red.pesos[l][i])):
                original = red.pesos[l][i][j]
                red.pesos[l][i][j] = original + h
                mas = red.perdida(X, Y, l2)
                red.pesos[l][i][j] = original - h
                menos = red.perdida(X, Y, l2)
                red.pesos[l][i][j] = original
                numerico = (mas - menos) / (2 * h)
                error_maximo = max(error_maximo, valor_absoluto(numerico - gW[l][i][j]))
        for i in range(len(red.sesgos[l])):
            original = red.sesgos[l][i]
            red.sesgos[l][i] = original + h
            mas = red.perdida(X, Y, l2)
            red.sesgos[l][i] = original - h
            menos = red.perdida(X, Y, l2)
            red.sesgos[l][i] = original
            error_maximo = max(error_maximo, valor_absoluto((mas - menos) / (2 * h) - gb[l][i]))
    comprobar("Retropropagacion vs diferencias finitas (error maximo)", error_maximo, 0.0, 1e-7)

    # XOR: no se puede separar con una linea, requiere capa oculta
    X = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
    Y = [0, 1, 1, 0]
    red = RedNeuronal([2, 8, 2], semilla=3)
    red.entrenar(X * 10, Y * 10, epocas=300, tasa=0.1, tamano_lote=8, momento=0.9)
    comprobar("La red aprende XOR (aciertos de 4)", sum(red.predecir(x) == y for x, y in zip(X, Y)), 4)

    lineas = red.a_lineas()
    copia = RedNeuronal.desde_lineas(lineas)
    comprobar("Guardar y cargar conserva las predicciones",
              copia.predecir_probabilidades([1.0, 0.0])[1], red.predecir_probabilidades([1.0, 0.0])[1])

    m = matriz_confusion([0, 0, 1, 1, 1, 2], [0, 1, 1, 1, 2, 2], 3)
    met = metricas_por_clase(m)
    comprobar("Exactitud de ejemplo (4/6)", exactitud(m), 4 / 6, 1e-12)
    comprobar("Precision clase 1 (2/3)", met[1]["precision"], 2 / 3, 1e-12)
    comprobar("Recall clase 1 (2/3)", met[1]["recall"], 2 / 3, 1e-12)
    comprobar("F1 clase 2 (2*0.5*1/1.5)", met[2]["f1"], 2 / 3, 1e-12)


def pruebas_emociones():
    print("\n--- Preparacion de audio para emociones ---")
    fs = 48000
    tono_bajo = generar_seno(1000, 0.1, frecuencia_muestreo=fs)
    tono_alto = generar_seno(12000, 0.1, frecuencia_muestreo=fs)
    bajo, fs_nueva = remuestrear(tono_bajo, fs, 16000)
    alto, _ = remuestrear(tono_alto, fs, 16000)
    comprobar("Remuestreo: nueva frecuencia", fs_nueva, 16000)
    comprobar("Remuestreo: 1 kHz pasa (RMS ~ 0.707)", calcular_rms(bajo[50:-50]), 0.7071, 0.01)
    comprobar_verdadero("Remuestreo: 12 kHz se atenua (evita aliasing)",
                        calcular_rms(alto[50:-50]) < 0.01)

    datos = interpretar_nombre_mesd("C:/MESD/Anger_F_A_abajo.wav")
    comprobar_verdadero("Nombre MESD: Anger_F_A_abajo.wav",
                        datos is not None and datos["emocion"] == "enojo"
                        and datos["voz"] == "F" and datos["palabra"] == "abajo")
    comprobar_verdadero("Nombre MESD: se ignoran voces infantiles",
                        interpretar_nombre_mesd("Sadness_C_B_sol.wav") is None)
    comprobar_verdadero("Nombre MESD: se ignoran emociones no usadas",
                        interpretar_nombre_mesd("Fear_M_A_casa.wav") is None)


def pruebas_palabras():
    print("\n--- FFT, MFCC y datos de palabras ---")
    g = GeneradorAleatorio(8)
    x = [g.normal() for _ in range(400)]
    real, imag = fft_real(x, 512)
    # Referencia: DFT directa de la definicion, para algunos k
    error = 0.0
    for k in (0, 1, 37, 128, 255, 256):
        re_k = sum(x[n] * coseno(2 * PI * k * n / 512) for n in range(400))
        im_k = -sum(x[n] * seno(2 * PI * k * n / 512) for n in range(400))
        error = max(error, valor_absoluto(re_k - real[k]), valor_absoluto(im_k - imag[k]))
    comprobar("FFT vs DFT directa (error maximo)", error, 0.0, 1e-9)

    comprobar("mel(1000 Hz) ~ 1000 mel", hz_a_mel(1000.0), 1000.0, 0.1)
    comprobar("mel -> Hz -> mel", hz_a_mel(mel_a_hz(1500.0)), 1500.0, 1e-9)
    # La DCT de una constante solo tiene componente en k = 0
    c = dct_ii([2.0] * 26, 13)
    comprobar("DCT de una constante: c0 = 26 * 2", c[0], 52.0, 1e-9)
    comprobar("DCT de una constante: c1 = 0", c[1], 0.0, 1e-9)

    mfcc = calcular_mfcc(generar_seno(300, 0.5, 0.5, 16000), 16000)
    comprobar("MFCC: 13 coeficientes por ventana", len(mfcc[0]), 13)
    comprobar("MFCC: ventanas en 0.5 s (25 ms / 10 ms)", len(mfcc), 48)
    comprobar("Vector de longitud fija (5 tramos x 13)", len(vector_longitud_fija(mfcc, 5)), 65)

    registros = [{"palabra": p} for p in ["a"] * 10 + ["b"] * 10]
    pliegues = asignar_pliegues_estratificados(registros, "palabra", 5, 1)
    comprobar_verdadero("Pliegues estratificados: 2 ejemplos de cada clase por pliegue",
                        all(pliegues[:10].count(k) == 2 and pliegues[10:].count(k) == 2 for k in range(5)))

    comprobar_verdadero("Palabras: se acepta corpus A con voz infantil",
                        interpretar_nombre_palabra("Fear_C_A_abajo.wav") is not None)
    comprobar_verdadero("Palabras: se ignora el corpus B",
                        interpretar_nombre_palabra("Anger_F_B_sol.wav") is None)


def pruebas_texto():
    print("\n--- Procesamiento de texto ---")
    comprobar_verdadero("Normalizacion: 'Sueño ÁNIMO' -> 'sueno animo'",
                        normalizar_texto("Sueño ÁNIMO") == "sueno animo")
    comprobar_verdadero("Raiz comun: preocupada / preocupado",
                        terminos("preocupada") == terminos("preocupado"))
    comprobar_verdadero("Negacion: 'no duermo' distinto de 'duermo'",
                        terminos("no duermo") == ["no_duerm"] and terminos("duermo") == ["duerm"])
    comprobar_verdadero("La negacion termina con 'pero'",
                        terminos("no duermo pero estudio") == ["no_duerm", "estudi"])

    v = VectorizadorTFIDF(frecuencia_minima=1, n_max=1).ajustar(["gato perro", "gato raton", "gato"])
    x = v.transformar("gato perro")
    comprobar("TF-IDF: vector con norma 1", sum(val * val for val in x.values()), 1.0, 1e-12)
    comprobar_verdadero("TF-IDF: 'perro' (raro) pesa mas que 'gato' (comun)",
                        x[v.vocabulario["perr"]] > x[v.vocabulario["gat"]])

    nb = NaiveBayesMultinomial().entrenar([{0: 3}, {0: 2}, {1: 4}], [0, 0, 1], 2, 2)
    comprobar("Naive Bayes: termino 0 -> clase 0", nb.predecir({0: 1}), 0)
    comprobar("Naive Bayes: termino 1 -> clase 1", nb.predecir({1: 1}), 1)

    print("\n--- Prioridad y extraccion ---")
    comprobar_verdadero("Prioridad: expresion de riesgo -> protocolo",
                        evaluar_prioridad("he pensado en quitarme la vida")["nivel"] == "protocolo")
    comprobar_verdadero("Prioridad: desesperanza -> prioritario",
                        evaluar_prioridad("siento que no hay salida")["nivel"] == "prioritario")
    comprobar_verdadero("Prioridad: frase comun -> ordinario",
                        evaluar_prioridad("me mata el cansancio del trabajo")["nivel"] == "ordinario")
    comprobar_verdadero("Prioridad: incluye recursos de ayuda",
                        any("800 911 2000" in r for r in evaluar_prioridad("no quiero vivir")["recursos"]))
    comprobar("Duracion: 'desde hace dos meses' = 60 dias",
              extraer_duracion("no duermo desde hace dos meses")["dias"], 60)
    comprobar("Duracion: 'llevo 3 semanas' = 21 dias", extraer_duracion("llevo 3 semanas asi")["dias"], 21)
    comprobar_verdadero("Duracion: 'dos dias a la semana' no es duracion",
                        extraer_duracion("voy al gym dos dias a la semana") is None)
    comprobar_verdadero("Contextos: jefe -> trabajo, novia -> pareja",
                        extraer_contextos("mi jefe me presiona y peleo con mi novia") == ["trabajo", "pareja"])


if __name__ == "__main__":
    pruebas_matematicas()
    pruebas_texto()
    pruebas_palabras()
    pruebas_matematicas_red()
    pruebas_red_neuronal()
    pruebas_emociones()
    pruebas_senales()
    pruebas_wav_y_vad()
    pruebas_svg()
    total = _resultados["ok"] + _resultados["fallo"]
    print(f"\nResultado: {_resultados['ok']}/{total} pruebas correctas")
