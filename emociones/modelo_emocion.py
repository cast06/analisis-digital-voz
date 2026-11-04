# ==============================================================
# ENTRENAMIENTO, VALIDACION CRUZADA Y USO DEL MODELO DE EMOCIONES
# ==============================================================
#
# IMPORTANTE: el modelo estima la emocion PERCIBIDA en la voz
# (neutral, tristeza, enojo, alegria). No es un diagnostico y no
# debe usarse como evidencia clinica (seccion 9 del protocolo).
# ==============================================================

import config
from nucleo.archivos import guardar_texto, leer_lineas, existe_archivo
from audio.caracteristicas import VARIABLES_EMOCION, construir_vector
from modelos.red_neuronal import RedNeuronal
from modelos.evaluacion import matriz_confusion, sumar_matrices, exactitud, f1_macro
from emociones.preparacion import (
    calcular_normalizacion, normalizar_vector, asignar_pliegues_por_palabra
)
from emociones.mesd import extraer_caracteristicas_emocion

AVISO = ("Resultado orientativo: emoción percibida en la voz. "
         "No es un diagnóstico ni sustituye la valoración de un profesional.")


def _preparar(registros, normalizacion):
    X = [normalizar_vector(r["vector"], r["voz"], normalizacion) for r in registros]
    Y = [config.CLASES_EMOCION.index(r["emocion"]) for r in registros]
    return X, Y


def _nueva_red(capas_ocultas, semilla):
    tamanos = [len(VARIABLES_EMOCION)] + list(capas_ocultas) + [len(config.CLASES_EMOCION)]
    return RedNeuronal(tamanos, semilla=semilla)


def _entrenar_red(red, X, Y, mostrar_cada=0):
    return red.entrenar(
        X, Y,
        epocas=config.EPOCAS,
        tasa=config.TASA_APRENDIZAJE,
        tamano_lote=config.TAMANO_LOTE,
        momento=config.MOMENTO,
        l2=config.REGULARIZACION_L2,
        semilla=config.SEMILLA,
        mostrar_cada=mostrar_cada
    )


def validacion_cruzada(registros, capas_ocultas, nombre=""):
    """
    Validacion cruzada de k pliegues agrupada por palabra.
    En cada pliegue: normalizacion calculada con entrenamiento,
    entrenamiento de una red nueva y prediccion sobre la prueba.
    """
    k = config.NUMERO_PLIEGUES
    pliegues = asignar_pliegues_por_palabra(registros, k, config.SEMILLA)
    n_clases = len(config.CLASES_EMOCION)

    matriz_total = [[0] * n_clases for _ in range(n_clases)]
    exactitudes, f1s, historiales = [], [], []

    for pliegue in range(k):
        entrenamiento = [r for r, p in zip(registros, pliegues) if p != pliegue]
        prueba = [r for r, p in zip(registros, pliegues) if p == pliegue]
        if not entrenamiento or not prueba:
            continue

        normalizacion = calcular_normalizacion(entrenamiento)
        X_ent, Y_ent = _preparar(entrenamiento, normalizacion)
        X_pru, Y_pru = _preparar(prueba, normalizacion)

        red = _nueva_red(capas_ocultas, config.SEMILLA + pliegue)
        historiales.append(_entrenar_red(red, X_ent, Y_ent))

        predichos = [red.predecir(x) for x in X_pru]
        matriz = matriz_confusion(Y_pru, predichos, n_clases)
        matriz_total = sumar_matrices(matriz_total, matriz)
        exactitudes.append(exactitud(matriz))
        f1s.append(f1_macro(matriz))

        print(f"  [{nombre}] Pliegue {pliegue + 1}/{k}: entrenamiento={len(entrenamiento)} "
              f"prueba={len(prueba)} exactitud={exactitudes[-1]:.3f} F1 macro={f1s[-1]:.3f}")

    return {
        "matriz": matriz_total,
        "exactitudes": exactitudes,
        "f1s": f1s,
        "historiales": historiales
    }


def entrenar_modelo_final(registros, capas_ocultas):
    """Entrena con TODOS los datos y guarda red + normalizacion."""
    normalizacion = calcular_normalizacion(registros)
    X, Y = _preparar(registros, normalizacion)
    red = _nueva_red(capas_ocultas, config.SEMILLA)
    historial = _entrenar_red(red, X, Y, mostrar_cada=50)
    guardar_modelo(red, normalizacion, config.MODELO_EMOCIONES)
    return red, normalizacion, historial


# --------------------------------------------------------------
# Guardar / cargar
# --------------------------------------------------------------


def guardar_modelo(red, normalizacion, ruta):
    lineas = [
        "clases;" + ";".join(config.CLASES_EMOCION),
        "variables;" + ";".join(VARIABLES_EMOCION)
    ]
    for voz, (medias, desviaciones) in normalizacion.items():
        lineas.append(f"media_{voz};" + ";".join(repr(v) for v in medias))
        lineas.append(f"desv_{voz};" + ";".join(repr(v) for v in desviaciones))
    lineas += red.a_lineas()
    guardar_texto(ruta, "\n".join(lineas) + "\n")


def cargar_modelo(ruta=None):
    ruta = ruta or config.MODELO_EMOCIONES
    if not existe_archivo(ruta):
        raise FileNotFoundError(
            "No hay modelo entrenado. Ejecuta primero: python entrenar_emociones.py"
        )

    lineas = leer_lineas(ruta)
    clases, variables = None, None
    medias, desviaciones = {}, {}
    lineas_red = []

    for linea in lineas:
        if not linea:
            continue
        clave, _, resto = linea.partition(";")
        valores = resto.split(";")
        if clave == "clases":
            clases = valores
        elif clave == "variables":
            variables = valores
        elif clave.startswith("media_"):
            medias[clave[6:]] = [float(v) for v in valores]
        elif clave.startswith("desv_"):
            desviaciones[clave[5:]] = [float(v) for v in valores]
        else:
            lineas_red.append(linea)

    if variables != VARIABLES_EMOCION:
        raise ValueError("El modelo se entreno con otras variables; vuelve a entrenarlo.")

    normalizacion = {voz: (medias[voz], desviaciones[voz]) for voz in medias}
    return RedNeuronal.desde_lineas(lineas_red), normalizacion, clases


def predecir_emocion_archivo(ruta_wav, tipo_voz, modelo=None):
    """
    Devuelve {"emocion", "probabilidades", "caracteristicas", "aviso"}.
    tipo_voz: "F" o "M" (se usa para la normalizacion por tipo de voz).
    """
    red, normalizacion, clases = modelo or cargar_modelo()
    caracteristicas = extraer_caracteristicas_emocion(ruta_wav)
    vector = construir_vector(caracteristicas, VARIABLES_EMOCION)
    x = normalizar_vector(vector, tipo_voz.upper(), normalizacion)
    probabilidades = red.predecir_probabilidades(x)
    mejor = max(range(len(clases)), key=lambda i: probabilidades[i])
    return {
        "emocion": clases[mejor],
        "probabilidades": dict(zip(clases, probabilidades)),
        "caracteristicas": caracteristicas,
        "aviso": AVISO
    }
