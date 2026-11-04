# ==============================================================
# CLASIFICACION DE MOTIVOS DE CONSULTA
# ==============================================================
#
# Dos modelos:
#   - Naive Bayes multinomial sobre conteos de terminos (linea base)
#   - Red neuronal MLP sobre vectores TF-IDF dispersos
#
# El resultado es una INFERENCIA del sistema sobre el tema principal
# de lo que la persona escribio. No es un diagnostico.
# ==============================================================

import config
from nucleo.archivos import existe_archivo, guardar_texto, leer_lineas
from nucleo.tabla import leer_texto_flexible
from texto.nlp import VectorizadorTFIDF
from modelos.naive_bayes import NaiveBayesMultinomial
from modelos.red_neuronal import RedNeuronal


def leer_corpus(ruta):
    """Lee lineas 'categoria|frase'. Ignora comentarios y lineas vacias."""
    if not existe_archivo(ruta):
        raise FileNotFoundError(f"No se encontro el corpus: {ruta}")
    datos = []
    for numero, linea in enumerate(leer_texto_flexible(ruta).splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        categoria, separador, frase = linea.partition("|")
        if not separador or not frase.strip():
            print(f"Linea {numero} de {ruta} ignorada (formato invalido).")
            continue
        datos.append((categoria.strip(), frase.strip()))
    return datos


def clases_ordenadas():
    return list(config.CATEGORIAS_MOTIVO.keys())


def _indices(etiquetas, clases):
    desconocidas = sorted(set(e for e in etiquetas if e not in clases))
    if desconocidas:
        raise ValueError(f"Categorias no definidas en config: {desconocidas}")
    return [clases.index(e) for e in etiquetas]


def entrenar_modelos(frases, etiquetas, semilla=None):
    """Ajusta el vectorizador y entrena Naive Bayes y la MLP."""
    clases = clases_ordenadas()
    Y = _indices(etiquetas, clases)

    vectorizador = VectorizadorTFIDF(config.TFIDF_FRECUENCIA_MINIMA, config.TFIDF_NGRAMAS)
    vectorizador.ajustar(frases)

    nb = NaiveBayesMultinomial(alfa=1.0)
    nb.entrenar([vectorizador.conteos(f) for f in frases], Y, len(clases), vectorizador.tamano())

    red = RedNeuronal([vectorizador.tamano()] + config.CAPAS_OCULTAS_TEXTO + [len(clases)],
                      semilla=semilla if semilla is not None else config.SEMILLA)
    historial = red.entrenar(
        [vectorizador.transformar(f) for f in frases], Y,
        epocas=config.EPOCAS_TEXTO, tasa=config.TASA_TEXTO,
        tamano_lote=config.TAMANO_LOTE, momento=config.MOMENTO,
        l2=config.REGULARIZACION_L2, semilla=config.SEMILLA
    )
    return {"vectorizador": vectorizador, "nb": nb, "red": red,
            "clases": clases, "historial": historial}


def predecir(modelos, frase, tipo="red"):
    """Devuelve la lista de probabilidades por clase."""
    vectorizador = modelos["vectorizador"]
    if tipo == "nb":
        return modelos["nb"].predecir_probabilidades(vectorizador.conteos(frase))
    x = vectorizador.transformar(frase)
    if not x:
        # Ninguna palabra conocida: no hay informacion para decidir
        n = len(modelos["clases"])
        return [1.0 / n] * n
    return modelos["red"].predecir_probabilidades(x)


def guardar_modelo(modelos, ruta=None):
    ruta = ruta or config.MODELO_TEXTO
    lineas = ["clases;" + ";".join(modelos["clases"])]
    lineas += modelos["vectorizador"].a_lineas()
    lineas += modelos["red"].a_lineas()
    guardar_texto(ruta, "\n".join(lineas) + "\n")


def cargar_modelo(ruta=None):
    ruta = ruta or config.MODELO_TEXTO
    if not existe_archivo(ruta):
        raise FileNotFoundError("No hay modelo de texto. Ejecuta primero: python entrenar_texto.py")
    clases = None
    lineas_vectorizador, lineas_red = [], []
    for linea in leer_lineas(ruta):
        if not linea:
            continue
        clave = linea.split(";", 1)[0]
        if clave == "clases":
            clases = linea.split(";")[1:]
        elif clave in ("tfidf", "vocabulario", "idf"):
            lineas_vectorizador.append(linea)
        else:
            lineas_red.append(linea)
    return {
        "clases": clases,
        "vectorizador": VectorizadorTFIDF.desde_lineas(lineas_vectorizador),
        "red": RedNeuronal.desde_lineas(lineas_red)
    }


def interpretar_motivos(modelos, frase):
    """
    Motivo principal y secundarios (probabilidad >= umbral), ordenados.
    Devuelve lista de (clave, nombre, probabilidad).
    """
    probabilidades = predecir(modelos, frase, "red")
    orden = sorted(range(len(probabilidades)), key=lambda i: -probabilidades[i])
    resultado = []
    for posicion, i in enumerate(orden):
        if posicion == 0 or probabilidades[i] >= config.UMBRAL_MOTIVO_SECUNDARIO:
            clave = modelos["clases"][i]
            resultado.append((clave, config.CATEGORIAS_MOTIVO.get(clave, clave), probabilidades[i]))
    return resultado
