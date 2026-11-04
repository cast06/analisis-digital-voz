# ==============================================================
# TABLAS DE DATOS EN TEXTO (CACHE DE CARACTERISTICAS)
# ==============================================================
# Formato: primera linea con nombres de columnas separados por ';'
# y despues una fila por registro. Las columnas de texto van
# primero y al final los valores numericos del vector.
# ==============================================================

from nucleo.archivos import existe_archivo


def leer_texto_flexible(ruta):
    """Lee en UTF-8 (con o sin BOM) o, si falla, en Latin-1."""
    try:
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            return archivo.read()
    except UnicodeDecodeError:
        with open(ruta, "r", encoding="latin-1") as archivo:
            return archivo.read()


def encabezado(columnas_texto, numero_valores):
    return ";".join(columnas_texto + [f"v{i}" for i in range(numero_valores)])


def leer_tabla(ruta, columnas_texto, numero_valores, clave="ruta"):
    """Devuelve {clave: registro}. Si el encabezado no coincide devuelve {}."""
    if not existe_archivo(ruta):
        return {}
    lineas = leer_texto_flexible(ruta).splitlines()
    if not lineas or lineas[0] != encabezado(columnas_texto, numero_valores):
        return {}

    registros = {}
    n_texto = len(columnas_texto)
    for linea in lineas[1:]:
        partes = linea.split(";")
        if len(partes) != n_texto + numero_valores:
            continue
        registro = dict(zip(columnas_texto, partes[:n_texto]))
        registro["vector"] = [float(v) for v in partes[n_texto:]]
        registros[registro[clave]] = registro
    return registros


def iniciar_tabla(ruta, columnas_texto, numero_valores):
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(encabezado(columnas_texto, numero_valores) + "\n")


def agregar_fila(ruta, registro, columnas_texto):
    valores = [registro[c] for c in columnas_texto] + [repr(v) for v in registro["vector"]]
    with open(ruta, "a", encoding="utf-8") as archivo:
        archivo.write(";".join(valores) + "\n")
