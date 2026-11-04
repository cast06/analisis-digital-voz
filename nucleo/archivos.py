# ==============================================================
# MANEJO DE RUTAS Y ARCHIVOS SIN MODULOS EXTERNOS
# ==============================================================
#
# Sustituye a pathlib usando solamente operaciones con cadenas y
# las funciones nativas open(), print() y las excepciones nativas.
#
# LIMITACION TECNICA:
# Sin os ni pathlib no es posible crear carpetas ni listar su
# contenido. Por eso las carpetas audios/, salidas/ y referencias/
# se entregan ya creadas, y las grabaciones de referencia se
# declaran en el archivo de texto referencias/indice.txt.
# ==============================================================


def es_absoluta(ruta):
    """Indica si una ruta es absoluta en Linux/Mac (/...) o Windows (C:\\...)."""
    if not ruta:
        return False
    if ruta[0] in ("/", "\\"):
        return True
    return len(ruta) > 2 and ruta[1] == ":" and ruta[2] in ("/", "\\")


def directorio_de(ruta):
    """Devuelve la carpeta que contiene a la ruta indicada."""
    posicion = max(ruta.rfind("/"), ruta.rfind("\\"))
    if posicion < 0:
        return "."
    if posicion == 0:
        return ruta[0]
    return ruta[:posicion]


def nombre_de(ruta):
    """Devuelve solo el nombre del archivo (sin carpetas)."""
    posicion = max(ruta.rfind("/"), ruta.rfind("\\"))
    return ruta[posicion + 1:]


def unir_ruta(base, *partes):
    """
    Une carpetas y nombres de archivo con '/'.
    Windows tambien acepta '/' como separador en open().
    """
    resultado = base
    for parte in partes:
        if es_absoluta(parte):
            resultado = parte
            continue
        if resultado and resultado[-1] not in ("/", "\\"):
            resultado += "/"
        resultado += parte
    return resultado


def existe_archivo(ruta):
    """Comprueba si un archivo existe intentando abrirlo en modo lectura."""
    try:
        with open(ruta, "rb"):
            return True
    except OSError:
        return False


def guardar_texto(ruta, contenido):
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)


def leer_lineas(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return [linea.rstrip("\n").rstrip("\r") for linea in archivo]
