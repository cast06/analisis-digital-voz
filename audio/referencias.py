# ==============================================================
# BANCO DE REFERENCIAS Y COMPARACION DE VOCABULARIO LIMITADO
# ==============================================================
#
# Sin os/pathlib no se puede recorrer la carpeta referencias/.
# Por eso las grabaciones se declaran en referencias/indice.txt:
#
#     voz_01;ma;voz_01/ma/ma_01.wav
#     voz_01;me;voz_01/me/me_01.wav
#
# (identificador de voz ; etiqueta ; ruta relativa a referencias/)
# ==============================================================

from config import DIRECTORIO_REFERENCIAS, INDICE_REFERENCIAS
from nucleo.archivos import unir_ruta, existe_archivo, leer_lineas
from nucleo.matematicas import raiz_cuadrada
from audio.wav import leer_wav
from audio.caracteristicas import analizar_segmento_completo


# (variable, escala de normalizacion, peso)
VARIABLES_COMPARACION = [
    ("frecuencia_fundamental", 250.0, 1.5),
    ("centroide_espectral", 2500.0, 1.5),
    ("ancho_banda_espectral", 1500.0, 1.2),
    ("frecuencia_dominante", 2000.0, 1.2),
    ("zcr", 0.15, 1.0),
    ("rms", 0.15, 0.6),
    ("duracion", 0.50, 0.8)
]


def leer_indice_referencias(ruta_indice=INDICE_REFERENCIAS):
    """Devuelve una lista de (voz, etiqueta, ruta_absoluta)."""
    if not existe_archivo(ruta_indice):
        return []

    entradas = []
    for numero, linea in enumerate(leer_lineas(ruta_indice), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = [p.strip() for p in linea.split(";")]
        if len(partes) != 3:
            print(f"Linea {numero} del indice ignorada (formato invalido): {linea}")
            continue
        voz, etiqueta, ruta = partes
        entradas.append((voz, etiqueta, unir_ruta(DIRECTORIO_REFERENCIAS, ruta)))
    return entradas


def cargar_referencias(ruta_indice=INDICE_REFERENCIAS):
    """
    Carga audios etiquetados de diferentes voces para comparacion acustica
    de vocabulario limitado (silabas o palabras cortas aisladas).
    """
    referencias = []

    for voz, silaba, ruta in leer_indice_referencias(ruta_indice):
        try:
            audio = leer_wav(ruta)
            caracteristicas = analizar_segmento_completo(
                audio["muestras"],
                audio["frecuencia_muestreo"]
            )
            if caracteristicas is None:
                continue

            referencias.append({
                "voz": voz,
                "silaba": silaba,
                "archivo": ruta,
                "caracteristicas": caracteristicas
            })
            print("Referencia cargada:", voz, "| Silaba/Palabra:", silaba, "| Archivo:", ruta)
        except Exception as error:
            print("Error al cargar referencia:", ruta)
            print("Detalle:", error)

    print("Total de referencias cargadas:", len(referencias))
    return referencias


def comparar_con_referencias(caracteristicas, referencias, umbral_distancia=0.65):
    """
    Compara el vector acustico de un segmento contra el banco de referencias
    con distancia euclidiana ponderada y normalizada:
        d = sqrt( sum w_i ((a_i - b_i)/s_i)^2 / sum w_i )

    LIMITACION IMPORTANTE:
    - Solo aplica a silabas o palabras cortas aisladas que existan en el banco.
    - No constituye reconocimiento de habla continua en español abierto.
    """
    if not caracteristicas or not referencias:
        return None

    mejor_ref = None
    menor_distancia = None

    for ref in referencias:
        c_ref = ref.get("caracteristicas")
        if not c_ref:
            continue

        suma_cuadrados = 0.0
        suma_pesos = 0.0

        for nombre, escala, peso in VARIABLES_COMPARACION:
            v_seg = float(caracteristicas.get(nombre, 0.0))
            v_ref = float(c_ref.get(nombre, 0.0))

            # Si en alguno no se pudo estimar F0, no penalizar con 0 artificial
            if nombre == "frecuencia_fundamental" and (v_seg <= 0.0 or v_ref <= 0.0):
                continue

            diferencia_norm = (v_seg - v_ref) / escala
            suma_cuadrados += peso * (diferencia_norm * diferencia_norm)
            suma_pesos += peso

        if suma_pesos <= 0.0:
            continue

        distancia = raiz_cuadrada(suma_cuadrados / suma_pesos)

        if menor_distancia is None or distancia < menor_distancia:
            menor_distancia = distancia
            mejor_ref = ref

    if mejor_ref is None:
        return None

    return {
        "silaba": mejor_ref["silaba"],
        "voz": mejor_ref["voz"],
        "archivo": mejor_ref["archivo"],
        "distancia": menor_distancia,
        "aceptada": menor_distancia <= umbral_distancia
    }
