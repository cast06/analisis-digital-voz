# ==============================================================
# TRANSFORMADA RAPIDA DE FOURIER (FFT) RADIX-2 DESDE CERO
# ==============================================================
#
# Algoritmo de Cooley-Tukey iterativo (decimacion en el tiempo):
#
#   X[k]       = E[k] + W^k O[k]
#   X[k + N/2] = E[k] - W^k O[k],     W = e^{-j 2 pi / N}
#
# donde E y O son las DFT de las muestras pares e impares.
# Complejidad: O(N log2 N), contra O(N^2) de la DFT directa.
# Para N = 512: ~2 300 mariposas contra ~262 000 productos.
#
# Requiere N potencia de 2; si la ventana es mas corta (400
# muestras = 25 ms a 16 kHz) se completa con ceros.
# ==============================================================

from nucleo.matematicas import DOS_PI, seno, coseno

_CACHE_FFT = {}


def es_potencia_de_dos(n):
    return n > 0 and (n & (n - 1)) == 0


def _tablas_fft(n):
    """Indices en orden de bits invertidos y factores de giro W^k."""
    if n in _CACHE_FFT:
        return _CACHE_FFT[n]

    bits = 0
    while (1 << bits) < n:
        bits += 1

    invertidos = []
    for i in range(n):
        r = 0
        x = i
        for _ in range(bits):
            r = (r << 1) | (x & 1)
            x >>= 1
        invertidos.append(r)

    cos_w = [coseno(DOS_PI * k / n) for k in range(n // 2)]
    sen_w = [-seno(DOS_PI * k / n) for k in range(n // 2)]   # signo de e^{-j...}

    _CACHE_FFT[n] = (invertidos, cos_w, sen_w)
    return _CACHE_FFT[n]


def fft_real(muestras, n=None):
    """
    FFT de una señal real. Devuelve (parte_real, parte_imaginaria),
    ambas de longitud n.
    """
    if n is None:
        n = 1
        while n < len(muestras):
            n <<= 1
    if not es_potencia_de_dos(n):
        raise ValueError("El tamaño de la FFT debe ser potencia de 2.")
    if len(muestras) > n:
        raise ValueError("La señal es mas larga que el tamaño de la FFT.")

    x = list(muestras) + [0.0] * (n - len(muestras))
    invertidos, cos_w, sen_w = _tablas_fft(n)

    real = [x[i] for i in invertidos]
    imag = [0.0] * n

    tamano = 2
    while tamano <= n:
        mitad = tamano // 2
        paso = n // tamano
        for inicio in range(0, n, tamano):
            for k in range(mitad):
                wr = cos_w[k * paso]
                wi = sen_w[k * paso]
                i = inicio + k
                j = i + mitad
                tr = wr * real[j] - wi * imag[j]
                ti = wr * imag[j] + wi * real[j]
                real[j] = real[i] - tr
                imag[j] = imag[i] - ti
                real[i] += tr
                imag[i] += ti
        tamano *= 2

    return real, imag


def espectro_potencia(muestras, n):
    """|X[k]|^2 / n para k = 0 ... n/2 (frecuencias no negativas)."""
    real, imag = fft_real(muestras, n)
    return [(real[k] * real[k] + imag[k] * imag[k]) / n for k in range(n // 2 + 1)]
