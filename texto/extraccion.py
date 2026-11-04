# ==============================================================
# EXTRACCION DE INFORMACION DEL TEXTO
# ==============================================================
#
# 1. Duracion de la dificultad, convertida a dias:
#       "hace dos meses"         -> 60
#       "desde hace 3 semanas"   -> 21
#       "llevo un año asi"       -> 365
#       "desde el año pasado"    -> 365 (aproximado)
#    unidades: dia = 1, semana = 7, mes = 30, año = 365
#
# 2. Contextos mencionados (escuela, trabajo, familia, pareja,
#    amistades, salud, economia) por palabras clave.
#
# Todo lo extraido se marca como "dicho por la persona"; lo que
# infiere el clasificador se reporta aparte como "inferido".
# ==============================================================

from texto.nlp import tokenizar, FIN

NUMEROS = {
    "un": 1, "una": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
    "doce": 12, "quince": 15, "veinte": 20, "treinta": 30,
    "par": 2, "unos": 2, "unas": 2, "varios": 3, "varias": 3, "algunos": 3, "algunas": 3,
    "muchos": 6, "muchas": 6
}

UNIDADES = {
    "dia": 1, "dias": 1,
    "semana": 7, "semanas": 7,
    "mes": 30, "meses": 30,
    "ano": 365, "anos": 365   # "año" sin ñ despues de normalizar
}

INDICADORES_DURACION = {"hace", "llevo", "lleva", "durante", "desde", "tengo", "ya", "como", "casi"}

EXPRESIONES_FIJAS = [
    (["desde", "ayer"], 1, "desde ayer"),
    (["desde", "la", "semana", "pasada"], 7, "desde la semana pasada"),
    (["desde", "el", "mes", "pasado"], 30, "desde el mes pasado"),
    (["desde", "el", "ano", "pasado"], 365, "desde el año pasado"),
    (["toda", "la", "vida"], 3650, "toda la vida"),
    (["desde", "nino"], 3650, "desde la infancia"),
    (["desde", "nina"], 3650, "desde la infancia"),
    (["desde", "chico"], 3650, "desde la infancia"),
    (["desde", "chica"], 3650, "desde la infancia"),
]

CONTEXTOS = {
    "escuela": ["escuela", "universidad", "uni", "prepa", "secundaria", "clase*", "examen*",
                "maestr*", "profe*", "tarea*", "carrera", "semestre", "materia*", "tesis",
                "calificacion*", "beca", "reprob*"],
    "trabajo": ["trabajo", "trabaj*", "jefe", "jefa", "oficina", "empleo", "chamba",
                "companer*", "junta*", "despid*", "renunci*"],
    "familia": ["familia", "mama", "papa", "padre*", "madre*", "herman*", "hijo*", "hija*",
                "abuel*", "tio", "tia", "prim*", "suegr*", "madrastra", "padrastro"],
    "pareja": ["novio", "novia", "pareja", "esposo", "esposa", "matrimonio", "ex"],
    "amistades": ["amigo*", "amiga*", "roomie"],
    "salud": ["enferm*", "doctor*", "hospital", "dolor*", "diagnostic*"],
    "economia": ["dinero", "deuda*", "renta", "pagar", "gastos", "quincena"],
}


def _coincide(patron, token):
    if patron.endswith("*"):
        return token.startswith(patron[:-1])
    return token == patron


def _numero(token):
    if token.isdigit():
        return int(token)
    return NUMEROS.get(token)


def extraer_duracion(texto):
    """
    Devuelve {"dias": int, "texto": str} o None si no se menciona duracion.
    Si hay varias menciones se toma la mayor.
    """
    tokens = [t for t in tokenizar(texto) if t != FIN]
    candidatos = []

    for patron, dias, descripcion in EXPRESIONES_FIJAS:
        for i in range(len(tokens) - len(patron) + 1):
            if tokens[i:i + len(patron)] == patron:
                candidatos.append((dias, descripcion))

    for i, token in enumerate(tokens):
        if token not in UNIDADES:
            continue
        # buscar un numero justo antes (permitiendo "un par de", "unos")
        cantidad = None
        inicio = i
        for j in range(i - 1, max(-1, i - 4), -1):
            if tokens[j] == "de":
                continue
            n = _numero(tokens[j])
            if n is not None:
                cantidad = n
                inicio = j
                break
            break
        if cantidad is None:
            # "llevo meses", "hace semanas": unidad en plural sin numero
            if token.endswith("s") and i > 0 and tokens[i - 1] in INDICADORES_DURACION:
                cantidad = 2
                inicio = i - 1
            else:
                continue
        # Debe haber un indicador de duracion cerca para no confundir
        # "dos dias a la semana" con una duracion
        contexto = tokens[max(0, inicio - 3):inicio]
        if any(t in INDICADORES_DURACION for t in contexto) or (i + 1 < len(tokens) and tokens[i + 1] in ("asi", "con", "sin")):
            candidatos.append((cantidad * UNIDADES[token], " ".join(tokens[inicio:i + 1])))

    if not candidatos:
        return None
    dias, descripcion = max(candidatos)
    return {"dias": dias, "texto": descripcion}


def describir_duracion(dias):
    if dias is None:
        return "No mencionada"
    if dias >= 365 and dias % 365 == 0:
        anos = dias // 365
        return "1 año aprox." if anos == 1 else f"{anos} años aprox."
    if dias >= 30 and dias % 30 == 0 and dias < 365:
        meses = dias // 30
        return "1 mes aprox." if meses == 1 else f"{meses} meses aprox."
    if dias >= 7 and dias % 7 == 0 and dias < 60:
        semanas = dias // 7
        return "1 semana aprox." if semanas == 1 else f"{semanas} semanas aprox."
    if dias < 14:
        return "1 día aprox." if dias == 1 else f"{dias} días aprox."
    if dias < 60:
        return f"{round(dias / 7)} semanas aprox."
    if dias < 730:
        return f"{round(dias / 30)} meses aprox."
    return f"{round(dias / 365)} años aprox."


def extraer_contextos(texto):
    tokens = [t for t in tokenizar(texto) if t != FIN]
    encontrados = []
    for contexto, patrones in CONTEXTOS.items():
        if any(_coincide(p, t) for p in patrones for t in tokens):
            encontrados.append(contexto)
    return encontrados
