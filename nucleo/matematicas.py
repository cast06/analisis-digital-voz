# ==============================================================
# FUNCIONES MATEMATICAS DESDE CERO
# ==============================================================
#
# Este modulo sera la base de todo el sistema (audio, NLP,
# redes neuronales y matching). Aqui se agregaran despues exp, ln,
# producto punto, normas, similitud coseno, sigmoide y softmax.
# ==============================================================

PI = 3.14159265358979323846
DOS_PI = 2.0 * PI
MITAD_PI = PI / 2.0


def valor_absoluto(numero):
    if numero < 0:
        return -numero
    return numero


def raiz_cuadrada(numero):
    """
    Raiz cuadrada por el metodo de Newton-Raphson:
        x_{k+1} = (x_k + a / x_k) / 2
    Complejidad: O(1) (maximo 15 iteraciones).
    """
    if numero < 0:
        raise ValueError(
            "No existe raiz cuadrada real de un numero negativo."
        )

    if numero == 0:
        return 0.0

    # Escalado inicial por potencias de 4 para garantizar convergencia
    # rapida incluso con numeros muy pequeños (ej. 1e-18) o muy grandes.
    temp = float(numero)
    escala = 1.0

    while temp >= 4.0:
        temp *= 0.25
        escala *= 2.0

    while temp < 0.25:
        temp *= 4.0
        escala *= 0.5

    aproximacion = (0.5 + 0.5 * temp) * escala

    # Iteracion de Newton-Raphson con criterio de paro por precision
    for _ in range(15):
        nueva = 0.5 * (aproximacion + numero / aproximacion)
        if valor_absoluto(nueva - aproximacion) <= 1e-15 * nueva:
            return nueva
        aproximacion = nueva

    return aproximacion


def normalizar_angulo(angulo):
    """
    Normaliza cualquier angulo real (positivo, negativo o muy grande)
    al intervalo [-PI, PI) en tiempo O(1).
    """
    return (angulo + PI) % DOS_PI - PI


def seno(angulo):
    """
    Calcula sen(angulo) mediante serie de Taylor alrededor de 0,
    reduciendo primero el angulo a [-PI/2, PI/2] por simetria.
        sen(x) = x - x^3/3! + x^5/5! - ...
    """
    x = (angulo + PI) % DOS_PI - PI

    if x > MITAD_PI:
        x = PI - x
    elif x < -MITAD_PI:
        x = -PI - x

    x2 = x * x
    termino = x
    resultado = x

    for n in range(1, 9):
        termino *= -x2 / ((2 * n) * (2 * n + 1))
        resultado += termino
        if -1e-16 < termino < 1e-16:
            break

    return resultado


def coseno(angulo):
    """
    Calcula cos(angulo) mediante serie de Taylor alrededor de 0,
    reduciendo primero el angulo a [0, PI/2] por simetria.
        cos(x) = 1 - x^2/2! + x^4/4! - ...
    """
    x = (angulo + PI) % DOS_PI - PI

    if x < 0.0:
        x = -x

    signo = 1.0
    if x > MITAD_PI:
        x = PI - x
        signo = -1.0

    x2 = x * x
    termino = 1.0
    resultado = 1.0

    for n in range(1, 9):
        termino *= -x2 / ((2 * n - 1) * (2 * n))
        resultado += termino
        if -1e-16 < termino < 1e-16:
            break

    return signo * resultado


def maximo_absoluto(valores):
    mayor = 0.0

    for valor in valores:
        absoluto = -valor if valor < 0 else valor
        if absoluto > mayor:
            mayor = absoluto

    return mayor


# --------------------------------------------------------------
# Exponencial y logaritmo natural
# --------------------------------------------------------------

LN2 = 0.6931471805599453


def exponencial(x):
    """
    e^x mediante reduccion de rango y serie de Taylor:
        x = k ln2 + r,  |r| <= ln2/2
        e^x = 2^k * e^r,   e^r = sum r^n / n!
    Valores extremos se recortan para evitar desbordamiento.
    """
    if x > 709.0:
        x = 709.0
    if x < -745.0:
        return 0.0

    k = int(x / LN2 + (0.5 if x >= 0 else -0.5))
    r = x - k * LN2

    termino = 1.0
    suma = 1.0
    for n in range(1, 25):
        termino *= r / n
        suma += termino
        if -1e-17 < termino < 1e-17:
            break

    return suma * (2.0 ** k)


def logaritmo_natural(x):
    """
    ln(x) para x > 0:
        x = m * 2^e con m en [0.75, 1.5)
        ln(x) = e ln2 + ln(m)
        ln(m) = 2 * atanh(t),  t = (m - 1)/(m + 1)
        atanh(t) = t + t^3/3 + t^5/5 + ...
    """
    if x <= 0:
        raise ValueError("El logaritmo solo esta definido para x > 0.")

    e = 0
    m = float(x)
    while m >= 1.5:
        m *= 0.5
        e += 1
    while m < 0.75:
        m *= 2.0
        e -= 1

    t = (m - 1.0) / (m + 1.0)
    t2 = t * t
    termino = t
    suma = t
    n = 1
    while True:
        termino *= t2
        n += 2
        incremento = termino / n
        suma += incremento
        if -1e-18 < incremento < 1e-18:
            break

    return e * LN2 + 2.0 * suma


# --------------------------------------------------------------
# Vectores y matrices (listas de Python)
# --------------------------------------------------------------


def producto_punto(a, b):
    if len(a) != len(b):
        raise ValueError("Los vectores deben tener la misma longitud.")
    return sum(x * y for x, y in zip(a, b))


def norma(v):
    return raiz_cuadrada(producto_punto(v, v))


def similitud_coseno(a, b):
    """cos(theta) = a·b / (||a|| ||b||). Devuelve 0 si algun vector es nulo."""
    na = norma(a)
    nb = norma(b)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return producto_punto(a, b) / (na * nb)


def distancia_euclidiana(a, b):
    if len(a) != len(b):
        raise ValueError("Los vectores deben tener la misma longitud.")
    return raiz_cuadrada(sum((x - y) ** 2 for x, y in zip(a, b)))


def matriz_por_vector(matriz, vector):
    return [producto_punto(fila, vector) for fila in matriz]


def matriz_ceros(filas, columnas):
    return [[0.0] * columnas for _ in range(filas)]


# --------------------------------------------------------------
# Funciones de activacion
# --------------------------------------------------------------


def relu(x):
    return x if x > 0.0 else 0.0


def sigmoide(x):
    """1 / (1 + e^-x), escrita de forma estable para x muy negativos."""
    if x >= 0:
        return 1.0 / (1.0 + exponencial(-x))
    ex = exponencial(x)
    return ex / (1.0 + ex)


def softmax(valores):
    """
    softmax(z)_i = e^(z_i - max z) / sum_j e^(z_j - max z)
    Restar el maximo no cambia el resultado y evita desbordamiento.
    """
    maximo = max(valores)
    exps = [exponencial(v - maximo) for v in valores]
    total = sum(exps)
    return [e / total for e in exps]


def indice_maximo(valores):
    mejor = 0
    for i in range(1, len(valores)):
        if valores[i] > valores[mejor]:
            mejor = i
    return mejor


# --------------------------------------------------------------
# Estadistica descriptiva basica
# --------------------------------------------------------------


def media(valores):
    if not valores:
        return 0.0
    return sum(valores) / len(valores)


def desviacion_estandar(valores):
    """Desviacion estandar poblacional: sqrt( sum (x - media)^2 / n )."""
    if not valores:
        return 0.0
    promedio = media(valores)
    varianza = sum((v - promedio) ** 2 for v in valores) / len(valores)
    return raiz_cuadrada(varianza)
