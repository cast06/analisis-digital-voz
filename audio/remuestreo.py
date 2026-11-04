# ==============================================================
# CAMBIO DE FRECUENCIA DE MUESTREO (DIEZMADO) Y NORMALIZACION
# ==============================================================
#
# MESD esta grabada a 48000 Hz. Para analizar todo a 16000 Hz se
# diezma por un factor q = 3, pero antes se aplica un filtro pasa
# bajas para que las frecuencias mayores a 8000 Hz no se "doblen"
# sobre las bajas (aliasing).
#
# Filtro FIR de sinc con ventana de Hann (diseño propio):
#   h[n] = 2 fc * sinc(2 fc (n - M/2)) * w[n],  n = 0..M
#   sinc(x) = sen(pi x) / (pi x),   fc = corte / fs (normalizada)
# Los coeficientes se normalizan para que la ganancia en 0 Hz sea 1.
#
# Solo se calcula la salida en las muestras que se conservan, por
# lo que el costo es O(N/q * M) en lugar de O(N * M).
# ==============================================================

from nucleo.matematicas import PI, DOS_PI, seno, coseno, maximo_absoluto


def disenar_filtro_pasa_bajas(frecuencia_corte, frecuencia_muestreo, numero_coeficientes=63):
    if numero_coeficientes < 3 or numero_coeficientes % 2 == 0:
        raise ValueError("El numero de coeficientes debe ser impar y mayor que 2.")
    if not 0 < frecuencia_corte < frecuencia_muestreo / 2:
        raise ValueError("La frecuencia de corte debe estar entre 0 y fs/2.")

    fc = frecuencia_corte / frecuencia_muestreo
    M = numero_coeficientes - 1
    coeficientes = []

    for n in range(numero_coeficientes):
        x = n - M / 2
        if x == 0:
            sinc = 2.0 * fc
        else:
            sinc = seno(DOS_PI * fc * x) / (PI * x)
        ventana = 0.5 - 0.5 * coseno(DOS_PI * n / M)
        coeficientes.append(sinc * ventana)

    total = sum(coeficientes)
    return [c / total for c in coeficientes]


def remuestrear(muestras, fs_original, fs_objetivo, numero_coeficientes=63):
    """
    Reduce la frecuencia de muestreo cuando fs_original es multiplo
    entero de fs_objetivo. Devuelve (muestras_nuevas, fs_objetivo).
    """
    if fs_original == fs_objetivo:
        return muestras[:], fs_original
    if fs_original < fs_objetivo or fs_original % fs_objetivo != 0:
        raise ValueError(
            f"Solo se admite diezmado por factor entero "
            f"({fs_original} Hz -> {fs_objetivo} Hz no es valido)."
        )

    q = fs_original // fs_objetivo
    # Corte al 90 % de la nueva frecuencia de Nyquist
    h = disenar_filtro_pasa_bajas(0.45 * fs_objetivo, fs_original, numero_coeficientes)
    mitad = len(h) // 2
    total = len(muestras)
    salida = []

    for centro in range(0, total, q):
        acumulado = 0.0
        for k, coef in enumerate(h):
            indice = centro + mitad - k
            if 0 <= indice < total:
                acumulado += coef * muestras[indice]
        salida.append(acumulado)

    return salida, fs_objetivo


def normalizar_pico(muestras):
    """Escala la señal para que su maximo absoluto sea 1 (como en MESD)."""
    maximo = maximo_absoluto(muestras)
    if maximo == 0.0:
        return muestras[:]
    return [m / maximo for m in muestras]
