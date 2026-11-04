# ==============================================================
# NORMALIZACION POR TIPO DE VOZ Y PARTICION EN PLIEGUES
# ==============================================================
#
# Normalizacion z por tipo de voz:
#     z = (x - media_voz) / desviacion_voz
# Una voz femenina tiene F0 mas alta que una masculina aunque ambas
# esten neutrales. Si no se normaliza por tipo de voz, el modelo
# aprende a distinguir hombre/mujer en lugar de emociones.
#
# Las medias y desviaciones se calculan SOLO con los datos de
# entrenamiento de cada pliegue, para no filtrar informacion de
# la prueba.
# ==============================================================

from nucleo.matematicas import media, desviacion_estandar
from nucleo.aleatorio import GeneradorAleatorio

MINIMO_POR_VOZ = 5


def _estadisticos(vectores):
    columnas = len(vectores[0])
    medias = []
    desviaciones = []
    for j in range(columnas):
        columna = [v[j] for v in vectores]
        medias.append(media(columna))
        d = desviacion_estandar(columna)
        desviaciones.append(d if d > 1e-12 else 1.0)
    return medias, desviaciones


def calcular_normalizacion(registros, por_voz=True):
    """
    Devuelve {"global": (medias, desv), "F": (...), "M": (...)}.
    Si un tipo de voz tiene muy pocos ejemplos se usa la global.
    Con por_voz=False solo se calcula la global.
    """
    if not registros:
        raise ValueError("No hay registros para calcular la normalizacion.")

    normalizacion = {"global": _estadisticos([r["vector"] for r in registros])}
    if not por_voz:
        return normalizacion
    tipos = sorted(set(r["voz"] for r in registros))
    for voz in tipos:
        vectores = [r["vector"] for r in registros if r["voz"] == voz]
        if len(vectores) >= MINIMO_POR_VOZ:
            normalizacion[voz] = _estadisticos(vectores)
    return normalizacion


def normalizar_vector(vector, voz, normalizacion):
    medias, desviaciones = normalizacion.get(voz, normalizacion["global"])
    return [(x - m) / d for x, m, d in zip(vector, medias, desviaciones)]


def asignar_pliegues_por_palabra(registros, numero_pliegues, semilla):
    """
    Asigna cada PALABRA a un pliegue. Todas las grabaciones de una misma
    palabra quedan juntas, asi el modelo nunca se evalua con una palabra
    que ya escucho al entrenar. Devuelve una lista con el pliegue de cada
    registro.
    """
    palabras = sorted(set(r["palabra"] for r in registros))
    GeneradorAleatorio(semilla).barajar(palabras)
    pliegue_de_palabra = {p: i % numero_pliegues for i, p in enumerate(palabras)}
    return [pliegue_de_palabra[r["palabra"]] for r in registros]


def asignar_pliegues_estratificados(registros, clave_clase, numero_pliegues, semilla):
    """
    k pliegues estratificados: dentro de cada clase se barajan los ejemplos
    y se reparten en orden, asi cada pliegue tiene casi la misma proporcion
    de cada clase.
    """
    generador = GeneradorAleatorio(semilla)
    pliegues = [0] * len(registros)
    clases = sorted(set(r[clave_clase] for r in registros))
    for clase in clases:
        indices = [i for i, r in enumerate(registros) if r[clave_clase] == clase]
        generador.barajar(indices)
        for posicion, i in enumerate(indices):
            pliegues[i] = posicion % numero_pliegues
    return pliegues


def contar_por(registros, clave):
    conteo = {}
    for r in registros:
        conteo[r[clave]] = conteo.get(r[clave], 0) + 1
    return conteo
