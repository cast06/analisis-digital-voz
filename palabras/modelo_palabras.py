# ==============================================================
# ENTRENAMIENTO, EVALUACION Y USO DEL RECONOCEDOR DE PALABRAS
# ==============================================================
#
# LIMITACION: reconoce SOLO las palabras con las que fue entrenado
# (vocabulario cerrado, palabras aisladas). No transcribe frases
# ni habla continua en español abierto.
#
# Se hacen dos evaluaciones:
# 1. Por tipo de voz (independiente del hablante): se entrena con
#    dos tipos de voz y se prueba con el tercero (F, M, C).
#    Mide si reconoce la palabra en una voz que nunca escuchó.
# 2. Estratificada de 5 pliegues: todas las voces aparecen en
#    entrenamiento y prueba (dependiente del hablante).
# ==============================================================

import config
from nucleo.archivos import guardar_texto, leer_lineas, existe_archivo
from modelos.red_neuronal import RedNeuronal
from modelos.evaluacion import matriz_confusion, sumar_matrices, exactitud, f1_macro
from emociones.preparacion import (
    calcular_normalizacion, normalizar_vector, asignar_pliegues_estratificados
)
from palabras.datos_palabras import vector_palabra, dimension_vector

AVISO_PALABRAS = ("Reconocimiento de vocabulario cerrado: solo identifica las palabras "
                  "con las que se entrenó el modelo.")


def _preparar(registros, normalizacion, clases):
    X = [normalizar_vector(r["vector"], "global", normalizacion) for r in registros]
    Y = [clases.index(r["palabra"]) for r in registros]
    return X, Y


def _entrenar(capas_ocultas, X, Y, numero_clases, semilla, mostrar_cada=0):
    red = RedNeuronal([dimension_vector()] + list(capas_ocultas) + [numero_clases], semilla=semilla)
    historial = red.entrenar(
        X, Y,
        epocas=config.EPOCAS_PALABRAS,
        tasa=config.TASA_PALABRAS,
        tamano_lote=config.TAMANO_LOTE,
        momento=config.MOMENTO,
        l2=config.REGULARIZACION_L2,
        semilla=semilla,
        mostrar_cada=mostrar_cada
    )
    return red, historial


def evaluar(registros, pliegues, capas_ocultas, clases, nombre, etiquetas_pliegue=None):
    """Entrena y prueba una red por pliegue. Devuelve matriz y metricas."""
    n = len(clases)
    matriz_total = [[0] * n for _ in range(n)]
    exactitudes, f1s, historiales, detalle = [], [], [], []

    for indice, pliegue in enumerate(sorted(set(pliegues))):
        entrenamiento = [r for r, p in zip(registros, pliegues) if p != pliegue]
        prueba = [r for r, p in zip(registros, pliegues) if p == pliegue]
        if not entrenamiento or not prueba:
            continue

        normalizacion = calcular_normalizacion(entrenamiento, por_voz=False)
        X_ent, Y_ent = _preparar(entrenamiento, normalizacion, clases)
        X_pru, Y_pru = _preparar(prueba, normalizacion, clases)

        red, historial = _entrenar(capas_ocultas, X_ent, Y_ent, n, config.SEMILLA + indice)
        historiales.append(historial)

        matriz = matriz_confusion(Y_pru, [red.predecir(x) for x in X_pru], n)
        matriz_total = sumar_matrices(matriz_total, matriz)
        exactitudes.append(exactitud(matriz))
        f1s.append(f1_macro(matriz))

        etiqueta = etiquetas_pliegue.get(pliegue, pliegue) if etiquetas_pliegue else f"pliegue {pliegue + 1}"
        detalle.append((etiqueta, len(entrenamiento), len(prueba), exactitudes[-1]))
        print(f"  [{nombre}] Prueba con {etiqueta}: entrenamiento={len(entrenamiento)} "
              f"prueba={len(prueba)} exactitud={exactitudes[-1]:.3f} F1 macro={f1s[-1]:.3f}")

    return {"matriz": matriz_total, "exactitudes": exactitudes, "f1s": f1s,
            "historiales": historiales, "detalle": detalle}


def pliegues_por_voz(registros):
    tipos = sorted(set(r["voz"] for r in registros))
    indice = {v: i for i, v in enumerate(tipos)}
    nombres = {"F": "voces femeninas", "M": "voces masculinas", "C": "voces infantiles"}
    etiquetas = {i: nombres.get(v, v) for v, i in indice.items()}
    return [indice[r["voz"]] for r in registros], etiquetas


def pliegues_estratificados(registros):
    return asignar_pliegues_estratificados(registros, "palabra", config.NUMERO_PLIEGUES, config.SEMILLA)


# --------------------------------------------------------------
# Modelo final
# --------------------------------------------------------------


def entrenar_modelo_final(registros, capas_ocultas, clases):
    normalizacion = calcular_normalizacion(registros, por_voz=False)
    X, Y = _preparar(registros, normalizacion, clases)
    red, historial = _entrenar(capas_ocultas, X, Y, len(clases), config.SEMILLA, mostrar_cada=25)
    guardar_modelo(red, normalizacion, clases, config.MODELO_PALABRAS)
    return red, historial


def guardar_modelo(red, normalizacion, clases, ruta):
    medias, desviaciones = normalizacion["global"]
    lineas = [
        "clases;" + ";".join(clases),
        f"mfcc;{config.MFCC_COEFICIENTES};{config.MFCC_TRAMOS}",
        "media;" + ";".join(repr(v) for v in medias),
        "desv;" + ";".join(repr(v) for v in desviaciones)
    ] + red.a_lineas()
    guardar_texto(ruta, "\n".join(lineas) + "\n")


def cargar_modelo(ruta=None):
    ruta = ruta or config.MODELO_PALABRAS
    if not existe_archivo(ruta):
        raise FileNotFoundError(
            "No hay modelo de palabras. Ejecuta primero: python entrenar_palabras.py"
        )
    clases, medias, desviaciones, lineas_red = None, None, None, []
    for linea in leer_lineas(ruta):
        if not linea:
            continue
        clave, _, resto = linea.partition(";")
        valores = resto.split(";")
        if clave == "clases":
            clases = valores
        elif clave == "mfcc":
            if [int(v) for v in valores] != [config.MFCC_COEFICIENTES, config.MFCC_TRAMOS]:
                raise ValueError("El modelo usa otra configuracion de MFCC; vuelve a entrenarlo.")
        elif clave == "media":
            medias = [float(v) for v in valores]
        elif clave == "desv":
            desviaciones = [float(v) for v in valores]
        else:
            lineas_red.append(linea)
    return RedNeuronal.desde_lineas(lineas_red), {"global": (medias, desviaciones)}, clases


def reconocer_palabra_archivo(ruta_wav, modelo=None, mejores=3):
    red, normalizacion, clases = modelo or cargar_modelo()
    x = normalizar_vector(vector_palabra(ruta_wav), "global", normalizacion)
    probabilidades = red.predecir_probabilidades(x)
    orden = sorted(range(len(clases)), key=lambda i: -probabilidades[i])
    return {
        "palabra": clases[orden[0]],
        "candidatas": [(clases[i], probabilidades[i]) for i in orden[:mejores]],
        "aviso": AVISO_PALABRAS
    }
