# ==============================================================
# MODULO DE PRIORIDAD Y SEGURIDAD (INDEPENDIENTE DEL CLASIFICADOR)
# ==============================================================
#
# Se ejecuta ANTES que cualquier otro analisis. No diagnostica:
# decide si la conversacion puede seguir como orientacion ordinaria.
#
# Niveles:
#   protocolo   -> expresiones de riesgo para la vida o de violencia.
#                  Se detiene la orientacion automatica y se muestran
#                  recursos de atencion humana inmediata.
#   prioritario -> malestar intenso o desesperanza. Se continua, pero
#                  el caso se marca para atencion pronta.
#   ordinario   -> orientacion normal.
#
# Metodo: reglas sobre la secuencia de palabras normalizadas (sin
# acentos y SIN quitar palabras vacias ni aplicar raiz, para no
# perder expresiones como "no quiero vivir").
#
# Cada regla es una lista de elementos que deben aparecer EN ORDEN
# dentro de una ventana corta. Un elemento puede tener alternativas
# separadas por "|" y terminar en "*" para aceptar cualquier final:
#     ["quitar*", "vida"]  ->  "quitarme la vida", "quitarse la vida"
#
# Criterio de diseño: ante la duda se prefiere una falsa alarma a un
# caso de riesgo no detectado. Por eso la negacion NO desactiva las
# reglas ("no quiero hacerme daño" tambien se marca) y la decision
# final siempre debe revisarla una persona.
# ==============================================================

from texto.nlp import tokenizar, FIN

ORDEN_NIVELES = ["ordinario", "prioritario", "protocolo"]

# Holgura: palabras extra permitidas entre los elementos de una regla
HOLGURA = 3

REGLAS = {
    "protocolo": [
        ["suicid*"],
        ["quitar*", "vida"],
        ["matarme"],
        ["quiero|voy|pienso|pensado|pensando", "matar*"],
        ["no", "quiero", "vivir|seguir"],
        ["ganas", "vivir"],
        ["sentido", "vivir|viviendo"],
        ["quisiera|quiero|deseo", "morir*"],
        ["morirme"],
        ["no", "despertar"],
        ["desaparecer"],
        ["mejor|mejores", "sin", "mi"],
        ["hacerme|hecho|hago", "dano"],
        ["lastimarme"],
        ["me", "lastimo|corto|lastime|corte"],
        ["autolesi*"],
        ["hacerle|hacerles|hacer", "dano"],
        ["matar*", "a"],
        ["me", "pega|pegan|golpea|golpean|golpeo|pego"],
        ["golpea|golpeo", "me"],
        ["abus*", "de", "mi"],
        ["abusaron|abuso|abusa"],
        ["me", "amenaza*"],
        ["violencia", "en", "mi|casa"],
        ["vivo", "violencia"],
        ["me", "viol*"],
    ],
    "prioritario": [
        ["no", "puedo", "mas"],
        ["no", "aguanto"],
        ["no", "hay", "salida"],
        ["sin", "salida"],
        ["nada", "tiene", "sentido"],
        ["no", "tiene", "sentido"],
        ["sin", "esperanza"],
        ["desesperanz*"],
        ["ataque*", "panico"],
        ["dias", "sin", "dormir|comer"],
        ["no", "he", "dormido|comido"],
        ["alcohol"],
        ["drogas|droga"],
        ["perder", "el", "control"],
        ["volviendo", "loc*"],
        ["me", "rendi"],
        ["no", "veo", "futuro"],
        ["ningun", "futuro"],
        ["dejar", "de", "llorar"],
    ]
}

# Ejemplos de recursos verificados (noviembre de 2026)
RECURSOS = [
    "Línea de la Vida (gratuita, 24 horas): 800 911 2000",
    "Emergencias: 911, o acude al servicio de urgencias más cercano",
]

MENSAJE_PROTOCOLO = (
    "Lo que escribiste indica que podrías estar en riesgo o viviendo una situación de "
    "violencia. Este sistema no puede atender emergencias. Por favor busca ayuda humana "
    "ahora mismo:"
)
MENSAJE_PRIORITARIO = (
    "Lo que describes suena muy difícil. Tu caso se marcará para que un profesional lo "
    "atienda con prioridad. Si en algún momento sientes que estás en peligro, busca ayuda "
    "inmediata:"
)


def _coincide_elemento(elemento, token):
    for alternativa in elemento.split("|"):
        if alternativa.endswith("*"):
            if token.startswith(alternativa[:-1]):
                return True
        elif token == alternativa:
            return True
    return False


def _buscar_regla(tokens, regla):
    """Devuelve la posicion (inicio, fin) si la regla aparece en orden con poca separacion."""
    limite = len(regla) + HOLGURA
    for inicio in range(len(tokens)):
        if not _coincide_elemento(regla[0], tokens[inicio]):
            continue
        posicion = inicio
        completo = True
        for elemento in regla[1:]:
            encontrado = False
            for j in range(posicion + 1, min(len(tokens), inicio + limite)):
                if tokens[j] == FIN:
                    break
                if _coincide_elemento(elemento, tokens[j]):
                    posicion = j
                    encontrado = True
                    break
            if not encontrado:
                completo = False
                break
        if completo:
            return inicio, posicion
    return None


def evaluar_prioridad(texto):
    """
    Devuelve {"nivel", "coincidencias", "mensaje", "recursos"}.
    coincidencias: fragmentos del texto que activaron alguna regla.
    """
    tokens = tokenizar(texto)
    nivel = "ordinario"
    coincidencias = []

    for nivel_regla in ("protocolo", "prioritario"):
        for regla in REGLAS[nivel_regla]:
            encontrado = _buscar_regla(tokens, regla)
            if encontrado:
                inicio, fin = encontrado
                coincidencias.append((nivel_regla, " ".join(tokens[inicio:fin + 1])))
                if ORDEN_NIVELES.index(nivel_regla) > ORDEN_NIVELES.index(nivel):
                    nivel = nivel_regla

    if nivel == "protocolo":
        mensaje = MENSAJE_PROTOCOLO
    elif nivel == "prioritario":
        mensaje = MENSAJE_PRIORITARIO
    else:
        mensaje = ""

    return {
        "nivel": nivel,
        "coincidencias": coincidencias,
        "mensaje": mensaje,
        "recursos": RECURSOS if nivel != "ordinario" else []
    }
