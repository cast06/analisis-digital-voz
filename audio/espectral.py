# ==============================================================
# VENTANEO, VENTANA DE HANN Y DFT DESDE CERO
# ==============================================================

from config import VENTANA_MS, SALTO_MS
from nucleo.matematicas import (
    DOS_PI, seno, coseno, raiz_cuadrada, valor_absoluto, maximo_absoluto
)

# Caches internos para no recalcular coeficientes trigonometricos
# cuando se analizan muchas ventanas del mismo tamaño N
_CACHE_HANN = {}
_CACHE_TABLAS_DFT = {}


# --------------------------------------------------------------
# Division en ventanas
# --------------------------------------------------------------


def dividir_en_ventanas(
        muestras,
        frecuencia_muestreo,
        duracion_ms=VENTANA_MS,
        desplazamiento_ms=SALTO_MS):

    if not muestras or frecuencia_muestreo <= 0:
        return []

    tamano = max(1, int(frecuencia_muestreo * duracion_ms / 1000))
    desplazamiento = max(1, int(frecuencia_muestreo * desplazamiento_ms / 1000))

    ventanas = []
    inicio = 0
    total = len(muestras)

    while inicio + tamano <= total:
        ventanas.append(muestras[inicio:inicio + tamano])
        inicio += desplazamiento

    return ventanas


# --------------------------------------------------------------
# Ventana de Hann:  w[n] = 0.5 - 0.5 cos(2 pi n / (N - 1))
# --------------------------------------------------------------


def _obtener_coeficientes_hann(N):
    if N in _CACHE_HANN:
        return _CACHE_HANN[N]

    factores = []
    denom = N - 1
    for n in range(N):
        factor = 0.5 - 0.5 * coseno(DOS_PI * n / denom)
        factores.append(factor)

    _CACHE_HANN[N] = factores
    return factores


def aplicar_hann(muestras):
    N = len(muestras)
    if N <= 1:
        return muestras[:]

    factores = _obtener_coeficientes_hann(N)
    return [muestras[n] * factores[n] for n in range(N)]


# --------------------------------------------------------------
# Transformada Discreta de Fourier
#   X[k] = sum_{n=0}^{N-1} x[n] * e^{-j 2 pi k n / N}
# Complejidad: O(N^2)
# --------------------------------------------------------------


def _obtener_tablas_dft(N):
    """
    Precalcula y almacena en cache las tablas de raices de la unidad
    cos(2*pi*k*n/N) y sen(2*pi*k*n/N) para el tamaño de ventana N,
    aprovechando la simetria par del coseno e impar del seno entre
    los indices n y N - n.
    """
    if N in _CACHE_TABLAS_DFT:
        return _CACHE_TABLAS_DFT[N]

    cos_base = [coseno(DOS_PI * m / N) for m in range(N)]
    sin_base = [seno(DOS_PI * m / N) for m in range(N)]

    mitad_k = N // 2
    mitad_n = (N - 1) // 2

    filas_cos = []
    filas_sin = []

    for k in range(mitad_k):
        fila_c = [cos_base[(k * n) % N] for n in range(1, mitad_n + 1)]
        fila_s = [sin_base[(k * n) % N] for n in range(1, mitad_n + 1)]
        filas_cos.append(fila_c)
        filas_sin.append(fila_s)

    tablas = (mitad_k, mitad_n, (N % 2 == 0), filas_cos, filas_sin)
    _CACHE_TABLAS_DFT[N] = tablas
    return tablas


def dft(
        muestras,
        frecuencia_muestreo):
    """
    Implementacion manual de la Transformada Discreta de Fourier (DFT).
    Utiliza la simetria trigonometrica exacta:
      x[n]*cos(2*pi*k*n/N) + x[N-n]*cos(2*pi*k*(N-n)/N) = (x[n] + x[N-n])*cos(2*pi*k*n/N)
      x[n]*sen(2*pi*k*n/N) + x[N-n]*sen(2*pi*k*(N-n)/N) = (x[n] - x[N-n])*sen(2*pi*k*n/N)
    para reducir a la mitad el numero de multiplicaciones sin alterar el resultado.

    Salida: lista de tuplas (frecuencia en Hz, magnitud |X[k]| / N)
    para k = 0 ... N/2 - 1.
    """
    N = len(muestras)

    if N == 0 or frecuencia_muestreo <= 0:
        return []

    mitad_k = N // 2
    if mitad_k == 0:
        magnitud = valor_absoluto(muestras[0])
        return [(0.0, magnitud)]

    # Caso especial de silencio puro: evita trabajo innecesario O(N^2)
    if maximo_absoluto(muestras) == 0.0:
        factor_freq = frecuencia_muestreo / N
        return [(k * factor_freq, 0.0) for k in range(mitad_k)]

    mitad_k, mitad_n, es_par, filas_cos, filas_sin = _obtener_tablas_dft(N)

    x0 = muestras[0]
    x_mitad = muestras[N // 2] if es_par else 0.0

    suma_par = [muestras[n] + muestras[N - n] for n in range(1, mitad_n + 1)]
    resta_impar = [muestras[n] - muestras[N - n] for n in range(1, mitad_n + 1)]

    espectro = []
    inv_N = 1.0 / N
    paso_frecuencia = frecuencia_muestreo / N

    for k in range(mitad_k):
        base_real = x0 + (x_mitad * (-1.0 if (k & 1) else 1.0) if es_par else 0.0)
        real = base_real + sum(sp * c for sp, c in zip(suma_par, filas_cos[k]))
        imaginaria = -sum(ri * s for ri, s in zip(resta_impar, filas_sin[k]))

        magnitud = raiz_cuadrada(real * real + imaginaria * imaginaria) * inv_N
        frecuencia = k * paso_frecuencia

        espectro.append((frecuencia, magnitud))

    return espectro


def frecuencias_dominantes(
        espectro,
        cantidad=10,
        frecuencia_minima=20,
        frecuencia_maxima=4000):

    candidatos = []

    for frecuencia, magnitud in espectro:
        if frecuencia_minima <= frecuencia <= frecuencia_maxima:
            candidatos.append((frecuencia, magnitud))

    candidatos.sort(
        key=lambda elemento: elemento[1],
        reverse=True
    )

    return candidatos[:cantidad]
