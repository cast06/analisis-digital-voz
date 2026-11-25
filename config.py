# ==============================================================
# CONFIGURACION GENERAL DEL PROYECTO
# ==============================================================
#
# Todas las constantes, rutas y listas de archivos estan aqui para
# no tener valores repartidos dentro de las funciones.
# ==============================================================

from nucleo.archivos import directorio_de, unir_ruta, es_absoluta


# --------------------------------------------------------------
# Parametros de procesamiento de señales
# --------------------------------------------------------------

FRECUENCIA_MUESTREO = 16000     # Hz, usada en los experimentos sinteticos
VENTANA_MS = 25                 # duracion de cada ventana de analisis
SALTO_MS = 10                   # desplazamiento entre ventanas


# --------------------------------------------------------------
# Carpetas del proyecto (relativas a este archivo)
# --------------------------------------------------------------

DIRECTORIO_PROYECTO = directorio_de(__file__)
DIRECTORIO_AUDIOS = unir_ruta(DIRECTORIO_PROYECTO, "audios")
DIRECTORIO_SALIDAS = unir_ruta(DIRECTORIO_PROYECTO, "salidas")
DIRECTORIO_REFERENCIAS = unir_ruta(DIRECTORIO_PROYECTO, "referencias")
INDICE_REFERENCIAS = unir_ruta(DIRECTORIO_REFERENCIAS, "indice.txt")

# Carpeta anterior donde estaban las grabaciones. Se conserva solo
# como respaldo: primero se busca en audios/ y despues aqui.
DIRECTORIO_AUDIOS_RESPALDO = r"C:\Users\sharo\Downloads\nuevo"


# --------------------------------------------------------------
# Grabaciones a procesar
# --------------------------------------------------------------

ARCHIVOS_AUDIO_LOTE = [
    "narracion (2).wav",
    "narracion_femenina_suave.wav",
    "narracion_masculina (2).wav"
]

# Grabacion para la vista detallada "Voz real". Si no existe, se
# usa la primera grabacion del lote que se haya procesado bien.
ARCHIVO_VOZ_DETALLE = "voz.wav"

# Intervalos marcados A MANO por el equipo. No son reconocimiento
# automatico de palabras: solo indican que fragmento se analiza.
FRAGMENTOS_MANUALES = [
    {"etiqueta": "Hola", "inicio": 0.00, "fin": 0.65},
    {"etiqueta": "Cómo", "inicio": 0.65, "fin": 1.10},
    {"etiqueta": "Estás", "inicio": 1.10, "fin": 2.00}
]


def ruta_salida(nombre_archivo):
    """Coloca los archivos generados (SVG, HTML, TXT) dentro de salidas/."""
    if es_absoluta(nombre_archivo):
        return nombre_archivo
    return unir_ruta(DIRECTORIO_SALIDAS, nombre_archivo)


# --------------------------------------------------------------
# Reconocimiento de emociones en la voz (MESD)
# --------------------------------------------------------------

DIRECTORIO_DATOS = unir_ruta(DIRECTORIO_PROYECTO, "datos")

# Lista con la ruta completa de cada .wav de MESD (una por linea).
# Se genera con PowerShell; ver LEEME.md.
LISTA_MESD = unir_ruta(DIRECTORIO_DATOS, "lista_mesd.txt")

# Tabla de caracteristicas ya calculadas (evita recalcular cada vez)
CACHE_CARACTERISTICAS_MESD = unir_ruta(DIRECTORIO_DATOS, "caracteristicas_mesd.csv")

# Modelo entrenado (pesos de la red y parametros de normalizacion)
MODELO_EMOCIONES = unir_ruta(DIRECTORIO_DATOS, "modelo_emociones.txt")

# Emociones de MESD que se usan -> nombre en el sistema
EMOCIONES_MESD = {
    "neutral": "neutral",
    "sadness": "tristeza",
    "anger": "enojo",
    "happiness": "alegria"
}
CLASES_EMOCION = ["neutral", "tristeza", "enojo", "alegria"]

# Solo voces adultas: F (femenina) y M (masculina). Se excluye C (niños).
TIPOS_VOZ_EMOCION = ["F", "M"]

FS_ANALISIS_EMOCION = 16000     # Hz, se diezma desde 48000 Hz
F0_MAXIMA_EMOCION = 500.0       # Hz, el enojo y la alegria pueden superar 400 Hz

# Entrenamiento
SEMILLA = 2026
NUMERO_PLIEGUES = 5             # validacion cruzada agrupada por palabra
ARQUITECTURAS_EMOCION = [
    # (nombre, capas ocultas)
    ("Regresión softmax (sin capas ocultas)", []),
    ("Red neuronal MLP (16-8)", [16, 8])
]
EPOCAS = 300
TASA_APRENDIZAJE = 0.02
TAMANO_LOTE = 16
MOMENTO = 0.9
REGULARIZACION_L2 = 0.001


# --------------------------------------------------------------
# Reconocimiento de palabras aisladas (MESD, corpus A)
# --------------------------------------------------------------
# Las palabras del corpus A se repiten en todas las emociones y
# tipos de voz, por eso sirven para entrenar un reconocedor que no
# dependa de la emocion ni de la persona.

CACHE_CARACTERISTICAS_PALABRAS = unir_ruta(DIRECTORIO_DATOS, "caracteristicas_palabras.csv")
MODELO_PALABRAS = unir_ruta(DIRECTORIO_DATOS, "modelo_palabras.txt")

CORPUS_PALABRAS = "A"
TIPOS_VOZ_PALABRAS = ["F", "M", "C"]   # se incluyen voces infantiles: mas variedad de voces
EMOCIONES_TODAS_MESD = {
    "neutral": "neutral", "sadness": "tristeza", "anger": "enojo",
    "happiness": "alegria", "fear": "miedo", "disgust": "asco"
}

# Palabras con menos grabaciones se descartan: no se pueden aprender
# ni evaluar (en MESD hay archivos sueltos con corpus "A" en el nombre).
MINIMO_GRABACIONES_POR_PALABRA = 8

MFCC_COEFICIENTES = 13
MFCC_TRAMOS = 5                        # vector final: 5 x 13 = 65 valores

ARQUITECTURAS_PALABRAS = [
    ("Regresión softmax (sin capas ocultas)", []),
    ("Red neuronal MLP (32)", [32])
]
EPOCAS_PALABRAS = 150
TASA_PALABRAS = 0.02


# --------------------------------------------------------------
# Texto: motivos de consulta
# --------------------------------------------------------------

DIRECTORIO_CORPUS = unir_ruta(DIRECTORIO_PROYECTO, "corpus")
CORPUS_ENTRENAMIENTO = unir_ruta(DIRECTORIO_CORPUS, "motivos_entrenamiento.txt")
CORPUS_PRUEBA = unir_ruta(DIRECTORIO_CORPUS, "motivos_prueba.txt")
CASOS_SEGURIDAD = unir_ruta(DIRECTORIO_CORPUS, "casos_seguridad.txt")
MODELO_TEXTO = unir_ruta(DIRECTORIO_DATOS, "modelo_texto.txt")

# Nombre interno -> nombre para mostrar
CATEGORIAS_MOTIVO = {
    "estres": "Estrés",
    "ansiedad": "Ansiedad percibida",
    "sueno": "Problemas de sueño",
    "duelo": "Duelo o pérdida",
    "relaciones": "Relaciones (pareja, familia, amistades)",
    "soledad": "Soledad o aislamiento",
    "academico_laboral": "Escuela o trabajo",
    "animo_bajo": "Ánimo bajo"
}

TFIDF_FRECUENCIA_MINIMA = 2     # un termino debe aparecer en 2+ frases
TFIDF_NGRAMAS = 2               # palabras sueltas y pares
CAPAS_OCULTAS_TEXTO = [16]
EPOCAS_TEXTO = 120
TASA_TEXTO = 0.1
# Se muestran tambien los motivos secundarios con probabilidad >= este valor
UMBRAL_MOTIVO_SECUNDARIO = 0.25


# --------------------------------------------------------------
# Vinculacion: registros, compatibilidad, solicitudes y seguimiento
# --------------------------------------------------------------
# Los registros son archivos de texto por bloques (ver
# vinculacion/almacen.py). Los de pacientes, solicitudes y
# seguimiento contienen datos personales: no se suben a GitHub.

REGISTRO_PSICOLOGOS = unir_ruta(DIRECTORIO_DATOS, "psicologos.txt")
REGISTRO_PACIENTES = unir_ruta(DIRECTORIO_DATOS, "pacientes.txt")
REGISTRO_SOLICITUDES = unir_ruta(DIRECTORIO_DATOS, "solicitudes.txt")
REGISTRO_SEGUIMIENTO = unir_ruta(DIRECTORIO_DATOS, "seguimiento.txt")

# Valores validos de los campos categoricos
MODALIDADES = ["linea", "presencial"]
HORARIOS = ["manana", "tarde", "noche"]
IDIOMAS = ["espanol", "ingles", "otro"]

# Pesos del puntaje de compatibilidad (deben sumar 1)
PESOS_COMPATIBILIDAD = {
    "tema": 0.55,       # similitud coseno necesidad-experiencia
    "costo": 0.20,
    "modalidad": 0.15,
    "horario": 0.10
}
# Cuantas opciones se muestran al usuario
OPCIONES_RECOMENDADAS = 5

# Seguimiento: se comparan las ultimas N sesiones contra las anteriores
SESIONES_RECIENTES = 3
SESIONES_ANTERIORES_MINIMAS = 2
# Diferencia de promedios a partir de la cual se marca un cambio
UMBRAL_CAMBIO = {"animo": 2.0, "sueno": 1.5}


# --------------------------------------------------------------
# Voz en vivo (modulo opcional con librerias externas)
# --------------------------------------------------------------
# Carpeta del modelo de Vosk en espanol descomprimido (ver LEEME.md)
MODELO_VOSK = unir_ruta(DIRECTORIO_DATOS, "vosk-model-small-es-0.42")
FS_GRABACION = 16000
SEGUNDOS_MAXIMOS_GRABACION = 90
