# ==============================================================
# GENERACION DE SEÑALES SINTETICAS
# ==============================================================
# x[n] = A * sen(2*pi*f*n / fs)
# ==============================================================

from config import FRECUENCIA_MUESTREO
from nucleo.matematicas import DOS_PI, seno, coseno


def generar_seno(
        frecuencia,
        duracion=0.05,
        amplitud=1.0,
        frecuencia_muestreo=FRECUENCIA_MUESTREO):

    if frecuencia_muestreo <= 0 or duracion <= 0:
        return []

    numero_muestras = int(frecuencia_muestreo * duracion)
    muestras = []
    paso_angulo = DOS_PI * frecuencia / frecuencia_muestreo

    for n in range(numero_muestras):
        angulo = paso_angulo * n
        valor = amplitud * seno(angulo)
        muestras.append(valor)

    return muestras


def generar_seno_coseno(
        duracion=0.05,
        frecuencia_muestreo=FRECUENCIA_MUESTREO):
    """x[n] = sen(2*pi*250*n/fs) + 0.5 * cos(2*pi*500*n/fs)"""

    if frecuencia_muestreo <= 0 or duracion <= 0:
        return []

    numero_muestras = int(frecuencia_muestreo * duracion)
    muestras = []

    paso_250 = DOS_PI * 250.0 / frecuencia_muestreo
    paso_500 = DOS_PI * 500.0 / frecuencia_muestreo

    for n in range(numero_muestras):
        componente_seno = seno(paso_250 * n)
        componente_coseno = 0.5 * coseno(paso_500 * n)
        muestras.append(componente_seno + componente_coseno)

    return muestras


# Componentes (frecuencia en Hz, amplitud) de la señal compleja
COMPONENTES_SENAL_COMPLEJA = [
    (125.0, 1.00),
    (250.0, 0.70),
    (375.0, 0.50),
    (750.0, 0.40),
    (1250.0, 0.30),
    (2500.0, 0.15)
]


def generar_senal_compleja(
        duracion=0.05,
        frecuencia_muestreo=FRECUENCIA_MUESTREO,
        componentes=COMPONENTES_SENAL_COMPLEJA):

    if frecuencia_muestreo <= 0 or duracion <= 0:
        return []

    numero_muestras = int(frecuencia_muestreo * duracion)
    muestras = []

    for n in range(numero_muestras):
        tiempo = n / frecuencia_muestreo
        valor_total = 0.0

        for frecuencia, amplitud in componentes:
            angulo = DOS_PI * frecuencia * tiempo
            valor_total += amplitud * seno(angulo)

        muestras.append(valor_total)

    return muestras
