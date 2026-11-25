# ==============================================================
# ALMACEN DE REGISTROS EN ARCHIVOS DE TEXTO (SIN BASE DE DATOS)
# ==============================================================
#
# Formato por bloques, legible y editable a mano:
#
#     [PS01]
#     nombre = Psic. Ana Ruiz (ficticia)
#     idiomas = espanol, ingles
#     costo = 600
#
# - Cada bloque empieza con [ID] y termina donde empieza el siguiente.
# - Cada campo es "clave = valor". Las lineas con # son comentarios.
# - Las listas se escriben separadas por comas.
#
# Lectura:  O(L) con L = numero de lineas del archivo.
# Escritura: se reescribe el archivo completo, O(R*C) con R registros
# y C campos. Es suficiente para un prototipo de decenas o cientos
# de registros; una base de datos real seria necesaria para mas.
# ==============================================================

from nucleo.archivos import existe_archivo, guardar_texto
from nucleo.tabla import leer_texto_flexible


def limpiar_valor(valor):
    """
    Quita saltos de linea y el caracter '[' inicial para que un valor
    escrito por el usuario no pueda romper el formato del archivo.
    """
    texto = str(valor).replace("\r", " ").replace("\n", " ").strip()
    while texto.startswith("["):
        texto = texto[1:].strip()
    return texto


def leer_registros(ruta):
    """
    Devuelve una lista de diccionarios; cada uno incluye la clave "id".
    Si el archivo no existe devuelve una lista vacia.
    Lanza ValueError si hay un campo fuera de un bloque o un ID repetido.
    """
    if not existe_archivo(ruta):
        return []
    registros = []
    actual = None
    vistos = set()
    for numero, linea in enumerate(leer_texto_flexible(ruta).splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if linea.startswith("[") and linea.endswith("]"):
            identificador = linea[1:-1].strip()
            if not identificador:
                raise ValueError(f"{ruta}, línea {numero}: bloque sin identificador.")
            if identificador in vistos:
                raise ValueError(f"{ruta}, línea {numero}: identificador repetido '{identificador}'.")
            vistos.add(identificador)
            actual = {"id": identificador}
            registros.append(actual)
            continue
        clave, separador, valor = linea.partition("=")
        if not separador:
            raise ValueError(f"{ruta}, línea {numero}: se esperaba 'clave = valor'.")
        if actual is None:
            raise ValueError(f"{ruta}, línea {numero}: campo fuera de un bloque [ID].")
        actual[clave.strip()] = valor.strip()
    return registros


def guardar_registros(ruta, registros, comentario=""):
    """Reescribe el archivo completo con los registros dados."""
    lineas = []
    if comentario:
        lineas += ["# " + c for c in comentario.splitlines()] + [""]
    for registro in registros:
        lineas.append(f"[{limpiar_valor(registro['id'])}]")
        for clave, valor in registro.items():
            if clave != "id":
                lineas.append(f"{clave} = {limpiar_valor(valor)}")
        lineas.append("")
    guardar_texto(ruta, "\n".join(lineas))


def siguiente_id(registros, prefijo, digitos=3):
    """PS + registros [PS01, PS07] -> PS08. Ignora IDs con otro prefijo."""
    mayor = 0
    for registro in registros:
        identificador = registro["id"]
        if identificador.startswith(prefijo) and identificador[len(prefijo):].isdigit():
            mayor = max(mayor, int(identificador[len(prefijo):]))
    return f"{prefijo}{mayor + 1:0{digitos}d}"


def buscar(registros, identificador):
    for registro in registros:
        if registro["id"] == identificador:
            return registro
    return None


# --------------------------------------------------------------
# Conversion de campos de texto a tipos de Python
# --------------------------------------------------------------

def a_lista(valor):
    """'linea, presencial' -> ['linea', 'presencial']"""
    return [parte.strip() for parte in valor.split(",") if parte.strip()]


def de_lista(valores):
    return ", ".join(valores)


def a_pesos(valor):
    """
    'ansiedad:1, estres:0.5' -> {'ansiedad': 1.0, 'estres': 0.5}
    Lanza ValueError si un peso no es numero o esta fuera de [0, 1].
    """
    pesos = {}
    for parte in a_lista(valor):
        clave, separador, numero = parte.partition(":")
        if not separador:
            raise ValueError(f"Peso sin ':' en '{parte}' (formato: tema:valor).")
        try:
            peso = float(numero)
        except ValueError:
            raise ValueError(f"El peso de '{clave.strip()}' no es un número: '{numero}'.")
        if not 0.0 <= peso <= 1.0:
            raise ValueError(f"El peso de '{clave.strip()}' debe estar entre 0 y 1.")
        pesos[clave.strip()] = peso
    return pesos


def de_pesos(pesos):
    return ", ".join(f"{clave}:{valor:g}" for clave, valor in pesos.items())
