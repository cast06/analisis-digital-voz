# ==============================================================
# COEFICIENTES CEPSTRALES EN FRECUENCIA MEL (MFCC) DESDE CERO
# ==============================================================
#
# Los MFCC resumen la forma del espectro (el timbre) en cada
# instante. Como la forma del espectro depende de la posicion de
# la lengua y los labios, distinguen sonidos como "a", "i", "s".
#
# Pasos por cada ventana de 25 ms (salto de 10 ms):
# 1. Preenfasis:      y[n] = x[n] - 0.97 x[n-1]
# 2. Ventana de Hann
# 3. Espectro de potencia con FFT de 512 puntos
# 4. Banco de 26 filtros triangulares en escala mel:
#        mel(f) = 2595 log10(1 + f/700)
#    (el oido distingue mejor diferencias en frecuencias bajas)
# 5. Logaritmo de la energia de cada filtro
# 6. DCT-II para obtener 13 coeficientes:
#        c_k = sum_{m=0}^{M-1} ln(E_m) cos(pi k (m + 0.5) / M)
#
# Despues:
# - Normalizacion de media cepstral (CMN): se resta a cada
#   coeficiente su promedio en la palabra; reduce el efecto del
#   microfono y de la persona que habla.
# - Vector de longitud fija: la palabra se divide en S tramos de
#   igual duracion y se promedian los MFCC de cada tramo. Asi
#   palabras de distinta duracion dan vectores del mismo tamaño
#   (S x 13) para la red neuronal.
# ==============================================================

from nucleo.matematicas import PI, logaritmo_natural, exponencial, coseno
from audio.espectral import dividir_en_ventanas, aplicar_hann
from audio.fft import espectro_potencia

LN10 = logaritmo_natural(10.0)

_CACHE_BANCO_MEL = {}
_CACHE_DCT = {}


def hz_a_mel(f):
    return 2595.0 * logaritmo_natural(1.0 + f / 700.0) / LN10


def mel_a_hz(m):
    return 700.0 * (exponencial(m * LN10 / 2595.0) - 1.0)


def banco_filtros_mel(numero_filtros, n_fft, fs, f_min=20.0, f_max=None):
    """
    Devuelve una lista de filtros; cada filtro es una lista de pesos
    para los bins 0 ... n_fft/2 del espectro de potencia.
    """
    clave = (numero_filtros, n_fft, fs, f_min, f_max)
    if clave in _CACHE_BANCO_MEL:
        return _CACHE_BANCO_MEL[clave]

    if f_max is None:
        f_max = fs / 2.0
    mel_min = hz_a_mel(f_min)
    mel_max = hz_a_mel(f_max)

    # numero_filtros + 2 puntos equiespaciados en mel
    puntos_mel = [mel_min + (mel_max - mel_min) * i / (numero_filtros + 1)
                  for i in range(numero_filtros + 2)]
    puntos_bin = [mel_a_hz(m) * n_fft / fs for m in puntos_mel]

    n_bins = n_fft // 2 + 1
    filtros = []
    for m in range(1, numero_filtros + 1):
        izquierda, centro, derecha = puntos_bin[m - 1], puntos_bin[m], puntos_bin[m + 1]
        pesos = []
        for k in range(n_bins):
            if izquierda < k <= centro:
                pesos.append((k - izquierda) / (centro - izquierda))
            elif centro < k < derecha:
                pesos.append((derecha - k) / (derecha - centro))
            else:
                pesos.append(0.0)
        filtros.append(pesos)

    _CACHE_BANCO_MEL[clave] = filtros
    return filtros


def _tabla_dct(numero_entradas, numero_coeficientes):
    clave = (numero_entradas, numero_coeficientes)
    if clave not in _CACHE_DCT:
        _CACHE_DCT[clave] = [
            [coseno(PI * k * (m + 0.5) / numero_entradas) for m in range(numero_entradas)]
            for k in range(numero_coeficientes)
        ]
    return _CACHE_DCT[clave]


def dct_ii(valores, numero_coeficientes):
    tabla = _tabla_dct(len(valores), numero_coeficientes)
    return [sum(c * v for c, v in zip(fila, valores)) for fila in tabla]


def calcular_mfcc(muestras, fs, numero_coeficientes=13, numero_filtros=26,
                  n_fft=512, preenfasis=0.97):
    """Devuelve una lista de vectores MFCC, uno por ventana."""
    if fs <= 0 or len(muestras) < 2:
        return []

    enfatizada = [muestras[0]] + [muestras[n] - preenfasis * muestras[n - 1]
                                  for n in range(1, len(muestras))]
    ventanas = dividir_en_ventanas(enfatizada, fs)
    if not ventanas:
        return []
    if len(ventanas[0]) > n_fft:
        raise ValueError("La ventana es mas larga que la FFT; aumenta n_fft.")

    filtros = banco_filtros_mel(numero_filtros, n_fft, fs)
    coeficientes = []

    for ventana in ventanas:
        potencia = espectro_potencia(aplicar_hann(ventana), n_fft)
        energias = []
        for pesos in filtros:
            e = sum(p * s for p, s in zip(pesos, potencia) if p > 0.0)
            energias.append(logaritmo_natural(e if e > 1e-10 else 1e-10))
        coeficientes.append(dct_ii(energias, numero_coeficientes))

    return coeficientes


def normalizar_media_cepstral(mfcc):
    if not mfcc:
        return []
    n = len(mfcc)
    medias = [sum(fila[j] for fila in mfcc) / n for j in range(len(mfcc[0]))]
    return [[v - m for v, m in zip(fila, medias)] for fila in mfcc]


def vector_longitud_fija(mfcc, numero_tramos=5):
    """Promedio de los MFCC en 'numero_tramos' partes iguales de la palabra."""
    if not mfcc:
        raise ValueError("No hay ventanas MFCC para resumir.")
    n = len(mfcc)
    dimension = len(mfcc[0])
    vector = []
    for t in range(numero_tramos):
        inicio = int(t * n / numero_tramos)
        fin = max(inicio + 1, int((t + 1) * n / numero_tramos))
        tramo = mfcc[inicio:fin]
        vector += [sum(fila[j] for fila in tramo) / len(tramo) for j in range(dimension)]
    return vector
