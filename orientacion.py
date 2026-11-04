# ==============================================================
# FLUJO DE ORIENTACION INICIAL (TEXTO + VOZ OPCIONAL)
# ==============================================================
#
# Ejecutar desde la carpeta del proyecto:
#     python orientacion.py
#
# Requiere haber entrenado: python entrenar_texto.py
# (opcional para voz: entrenar_emociones.py y entrenar_palabras.py)
#
# Flujo:
# 1. Aviso de limites del sistema y consentimiento explicito.
# 2. La persona describe con sus palabras lo que le pasa.
# 3. Modulo de prioridad PRIMERO. Si se activa el protocolo, se
#    detiene la orientacion y se muestran recursos humanos.
# 4. Clasificacion del motivo (inferido) y extraccion de datos
#    dichos por la persona (duracion, contextos).
# 5. Voz opcional: emocion percibida y palabra reconocida.
# 6. Preferencias practicas (modalidad, horario, costo, idioma).
# 7. Perfil preliminar NO diagnostico, con consentimiento para
#    compartirlo con un profesional. Se guarda en salidas/.
# ==============================================================

import config
from nucleo.archivos import guardar_texto, existe_archivo
from texto.nlp import normalizar_texto
from texto.seguridad import evaluar_prioridad
from texto.extraccion import extraer_duracion, extraer_contextos, describir_duracion
from texto.modelo_texto import cargar_modelo as cargar_modelo_texto, interpretar_motivos

AVISO_INICIAL = """
============================================================
 ORIENTACIÓN INICIAL - SISTEMA DE VINCULACIÓN PSICOLÓGICA
============================================================
Antes de empezar:
 - Este sistema NO es un psicólogo ni hace diagnósticos.
 - Su función es ayudarte a describir lo que te pasa y
   orientarte hacia un profesional humano.
 - No atiende emergencias. Si estás en peligro llama al 911
   o a la Línea de la Vida: 800 911 2000 (gratuita, 24 horas).
 - Lo que escribas se usa solo para armar un resumen que tú
   decides si se comparte con un profesional.
"""

AVISO_PERFIL = ("Resumen generado automáticamente a partir de lo que la persona escribió. "
                "No constituye un diagnóstico y debe ser validado por un profesional.")


def preguntar(texto, opciones=None, permitir_vacio=False):
    """
    Pide una respuesta. Si hay opciones, se comparan sin acentos ni
    mayusculas: "Español", "español" y "espanol" valen lo mismo.
    """
    while True:
        respuesta = input(texto).strip()
        if not respuesta and permitir_vacio:
            return ""
        if opciones is None and respuesta:
            return respuesta
        if opciones is not None:
            normalizada = normalizar_texto(respuesta)
            if normalizada in opciones:
                return normalizada
            # tambien se acepta la primera palabra ("en linea" -> "linea")
            for opcion in opciones:
                if opcion in normalizada.split():
                    return opcion
            print("  Opciones válidas:", ", ".join(opciones))


def mostrar_prioridad(resultado):
    print("\n" + "!" * 60)
    print(resultado["mensaje"])
    for recurso in resultado["recursos"]:
        print("  •", recurso)
    print("!" * 60)


def analizar_voz_opcional():
    """Devuelve un diccionario con los resultados de voz o None."""
    ruta = preguntar("\nSi tienes una grabación .wav de tu voz, escribe su ruta "
                     "(o Enter para omitir): ", permitir_vacio=True).strip('"')
    if not ruta:
        return None
    if not existe_archivo(ruta):
        print("No se encontró el archivo; se continúa sin voz.")
        return None

    resultado = {"archivo": ruta}
    try:
        from palabras.modelo_palabras import reconocer_palabra_archivo
        palabra = reconocer_palabra_archivo(ruta)
        resultado["palabra"] = palabra["palabra"]
        resultado["palabra_probabilidad"] = palabra["candidatas"][0][1]
    except Exception as error:
        print("  (Reconocimiento de palabras no disponible:", error, ")")
    try:
        from emociones.modelo_emocion import predecir_emocion_archivo
        tipo = preguntar("Tipo de voz para la normalización (f = femenina, m = masculina): ",
                         ["f", "m"])
        emocion = predecir_emocion_archivo(ruta, tipo.upper())
        resultado["emocion"] = emocion["emocion"]
        resultado["emocion_probabilidad"] = emocion["probabilidades"][emocion["emocion"]]
    except Exception as error:
        print("  (Análisis de emoción no disponible:", error, ")")
    return resultado


def pedir_preferencias():
    print("\nAhora unas preguntas prácticas para buscar opciones de atención:")
    modalidad = preguntar("  Modalidad (en linea / presencial / cualquiera): ",
                          ["linea", "presencial", "cualquiera"])
    horario = preguntar("  Horario preferido (manana / tarde / noche / cualquiera): ",
                        ["manana", "tarde", "noche", "cualquiera"])
    while True:
        costo = preguntar("  Costo máximo por sesión en pesos (0 si buscas opciones gratuitas): ")
        if costo.isdigit():
            break
        print("  Escribe solo números.")
    idioma = preguntar("  Idioma (espanol / ingles / otro): ", ["espanol", "ingles", "otro"])
    return {"modalidad": modalidad, "horario": horario, "costo_maximo": int(costo), "idioma": idioma}


def construir_perfil(relato, prioridad, motivos, duracion, contextos, voz, preferencias, compartir):
    lineas = [
        "=" * 60,
        "PERFIL PRELIMINAR DE ORIENTACIÓN (NO DIAGNÓSTICO)",
        "=" * 60,
        AVISO_PERFIL,
        "",
        "LO QUE LA PERSONA EXPRESÓ",
        f"  Relato: {relato}",
        f"  Duración mencionada: {describir_duracion(duracion['dias']) if duracion else 'No mencionada'}"
        + (f" (\"{duracion['texto']}\")" if duracion else ""),
        f"  Contextos mencionados: {', '.join(contextos) if contextos else 'Ninguno identificado'}",
        "",
        "LO QUE EL SISTEMA INFIERE (debe confirmarlo un profesional)",
    ]
    for posicion, (_, nombre, p) in enumerate(motivos):
        etiqueta = "Motivo principal" if posicion == 0 else "Motivo secundario"
        lineas.append(f"  {etiqueta}: {nombre} ({p * 100:.0f} %)")
    lineas.append(f"  Prioridad del flujo: {prioridad['nivel']}")
    if voz:
        if "emocion" in voz:
            lineas.append(f"  Emoción percibida en la voz: {voz['emocion']} "
                          f"({voz['emocion_probabilidad'] * 100:.0f} %) - dato orientativo")
        if "palabra" in voz:
            lineas.append(f"  Palabra reconocida en la voz: {voz['palabra']} "
                          f"({voz['palabra_probabilidad'] * 100:.0f} %)")
    lineas += [
        "",
        "PREFERENCIAS PRÁCTICAS",
        f"  Modalidad: {preferencias['modalidad']}",
        f"  Horario: {preferencias['horario']}",
        f"  Costo máximo: ${preferencias['costo_maximo']}",
        f"  Idioma: {preferencias['idioma']}",
        "",
        f"Consentimiento para compartir con un profesional: {'SÍ' if compartir else 'NO'}",
    ]
    return "\n".join(lineas)


def main():
    try:
        modelo_texto = cargar_modelo_texto()
    except (FileNotFoundError, ValueError) as error:
        print(error)
        return

    print(AVISO_INICIAL)
    if preguntar("¿Aceptas continuar con estas condiciones? (si / no): ", ["si", "no"]) != "si":
        print("Está bien. Si cambias de opinión, puedes volver cuando quieras.")
        return

    relato = preguntar("\nCuéntame con tus palabras qué te trae por aquí:\n> ")

    # 1. Seguridad antes que cualquier otra cosa
    prioridad = evaluar_prioridad(relato)
    if prioridad["nivel"] == "protocolo":
        mostrar_prioridad(prioridad)
        print("\nLa orientación automática se detiene aquí. Por favor contacta a una "
              "persona ahora; no tienes que pasar por esto solo/a.")
        return
    if prioridad["nivel"] == "prioritario":
        mostrar_prioridad(prioridad)

    # 2. Motivo inferido y datos expresados
    motivos = interpretar_motivos(modelo_texto, relato)
    duracion = extraer_duracion(relato)
    contextos = extraer_contextos(relato)

    print("\nLo que entendí (puede no ser exacto):")
    for posicion, (_, nombre, p) in enumerate(motivos):
        print(f"  {'Tema principal' if posicion == 0 else 'También'}: {nombre} ({p * 100:.0f} %)")

    if duracion is None:
        respuesta = preguntar("\n¿Desde hace cuánto te sientes así? (por ejemplo: 'hace dos "
                              "semanas', o Enter para omitir): ", permitir_vacio=True)
        if respuesta:
            duracion = extraer_duracion("hace " + respuesta if "hace" not in respuesta.lower()
                                        else respuesta)
            nueva = evaluar_prioridad(respuesta)
            if nueva["nivel"] == "protocolo":
                mostrar_prioridad(nueva)
                return

    voz = analizar_voz_opcional()
    preferencias = pedir_preferencias()
    compartir = preguntar("\n¿Autorizas compartir este resumen con el profesional que elijas? "
                          "(si / no): ", ["si", "no"]) == "si"

    perfil = construir_perfil(relato, prioridad, motivos, duracion, contextos,
                              voz, preferencias, compartir)
    print("\n" + perfil)

    numero = 1
    while existe_archivo(config.ruta_salida(f"perfil_{numero:03d}.txt")):
        numero += 1
    ruta = config.ruta_salida(f"perfil_{numero:03d}.txt")
    guardar_texto(ruta, perfil + "\n")
    print("\nResumen guardado en:", ruta)
    print("Siguiente paso del sistema: buscar profesionales compatibles con este perfil.")


if __name__ == "__main__":
    main()
