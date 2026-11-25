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
# 2. Elige texto o voz y describe con sus palabras lo que le pasa.
#    Despues confirma o corrige el tema que infiere el sistema.
# 3. Modulo de prioridad PRIMERO. Si se activa el protocolo, se
#    detiene la orientacion y se muestran recursos humanos.
# 4. Clasificacion del motivo (inferido) y extraccion de datos
#    dichos por la persona (duracion, contextos).
# 6. Preferencias practicas (modalidad, horario, costo, idioma).
# 7. Perfil preliminar NO diagnostico, con consentimiento para
#    compartirlo con un profesional. Se guarda en salidas/ y el
#    paciente queda registrado en datos/pacientes.txt.
# 8. Recomendacion: opciones ordenadas por compatibilidad, con sus
#    razones. La persona elige (o no) y se crea la solicitud.
# ==============================================================

import config
from nucleo.archivos import guardar_texto, existe_archivo
from texto.nlp import normalizar_texto
from texto.seguridad import evaluar_prioridad
from texto.extraccion import extraer_duracion, extraer_contextos, describir_duracion
from texto.modelo_texto import cargar_modelo as cargar_modelo_texto, interpretar_motivos, predecir
from vinculacion.registro import registrar_paciente, cargar_paciente, cargar_psicologos
from vinculacion.compatibilidad import recomendar, texto_opcion
from vinculacion.solicitudes import crear_solicitud, generar_resumen
from vinculacion.panel import generar_panel_html
from vinculacion.geografia import ALCALDIAS
from vinculacion.mapa import generar_recomendacion_html

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
 - Lo que escribas o digas se usa solo para armar un resumen que tú
   decides si se comparte con un profesional. Si grabas tu voz, el
   audio se guarda únicamente en esta computadora (carpeta salidas).
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


def analizar_voz(ruta, duracion=None):
    """
    Emocion percibida (modelo propio) y, si la grabacion es corta (una
    palabra), palabra reconocida del vocabulario cerrado.
    """
    resultado = {"archivo": ruta}
    if duracion is None or duracion <= 2.0:
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


def analizar_voz_opcional():
    """Pide la ruta de un .wav y lo analiza. Devuelve el resultado o None."""
    ruta = preguntar("\nEscribe la ruta de tu grabación .wav (o Enter para omitir): ",
                     permitir_vacio=True).strip('"')
    if not ruta:
        return None
    if not existe_archivo(ruta):
        print("No se encontró el archivo; se continúa sin voz.")
        return None
    return analizar_voz(ruta)


def entrada_por_voz():
    """
    Devuelve (resultado_voz, relato_transcrito). El relato es None si no
    hay transcripcion disponible; entonces la persona lo escribe.
    Usa el modulo opcional voz_en_vivo (librerias externas) solo si esta
    instalado; si no, explica por que y ofrece usar un archivo .wav.
    """
    from voz_en_vivo import microfono, transcripcion
    hay_microfono, motivo_mic = microfono.disponible()
    hay_transcripcion, motivo_trans = transcripcion.disponible()

    ruta, duracion = None, None
    if hay_microfono:
        modo = preguntar("¿Grabar ahora con el micrófono o usar un archivo .wav? (grabar / archivo): ",
                         ["grabar", "archivo"])
    else:
        print(f"  Grabación en vivo no disponible: {motivo_mic}.")
        modo = "archivo"

    if modo == "grabar":
        numero = 1
        while existe_archivo(config.ruta_salida(f"grabacion_{numero:03d}.wav")):
            numero += 1
        ruta = config.ruta_salida(f"grabacion_{numero:03d}.wav")
        print("Cuéntanos con tus palabras qué te trae por aquí.")
        try:
            duracion = microfono.grabar(ruta)
            print(f"Grabación guardada ({duracion:.1f} s): {ruta}")
        except Exception as error:
            print("No se pudo grabar:", error)
            ruta = None
        voz = analizar_voz(ruta, duracion) if ruta else None
    else:
        voz = analizar_voz_opcional()
        ruta = voz["archivo"] if voz else None

    if voz and ("emocion" in voz or "palabra" in voz):
        print("\nLo que se percibió en tu voz (dato orientativo, no diagnóstico):")
        if "emocion" in voz:
            print(f"  Emoción percibida: {voz['emocion']} ({voz['emocion_probabilidad'] * 100:.0f} %)")
        if "palabra" in voz:
            print(f"  Palabra reconocida: {voz['palabra']} ({voz['palabra_probabilidad'] * 100:.0f} %)")

    relato = None
    if ruta and hay_transcripcion:
        try:
            texto = transcripcion.transcribir(ruta)
        except Exception as error:
            print("No se pudo transcribir:", error)
            texto = ""
        if texto:
            print(f'\nEsto es lo que entendí de tu voz:\n  "{texto}"')
            correccion = preguntar("Presiona Enter si es correcto, o escribe tu relato corregido:\n> ",
                                   permitir_vacio=True)
            relato = correccion or texto
        else:
            print("No se entendió el audio.")
    elif ruta:
        print(f"\n  Transcripción no disponible: {motivo_trans}.")
    return voz, relato


# Peso de la eleccion de la persona cuando corrige el tema inferido.
# Lo que la persona dice pesa mas que lo que el modelo infiere.
PESO_CORRECCION = 0.6


def confirmar_motivo(motivos, probabilidades):
    """
    Pregunta si el tema inferido es correcto. Si la persona elige otro:
        n_nuevo = 0.6 * e_elegido + 0.4 * n_modelo
    (e_elegido = vector con 1 en el tema elegido). n_nuevo sigue sumando 1.
    Devuelve (motivos, probabilidades, "si" | "corregido" | "sin respuesta").
    """
    respuesta = preguntar("\n¿Se parece a lo que te pasa? (si / no): ", ["si", "no"])
    if respuesta == "si":
        return motivos, probabilidades, "si"
    claves = list(config.CATEGORIAS_MOTIVO)
    print("Elige el tema que mejor lo describe:")
    for i, clave in enumerate(claves, start=1):
        print(f"  {i}. {config.CATEGORIAS_MOTIVO[clave]}")
    eleccion = preguntar("Número (0 si ninguno se parece): ", [str(i) for i in range(len(claves) + 1)])
    if eleccion == "0":
        return motivos, probabilidades, "sin respuesta"
    elegido = int(eleccion) - 1
    nuevas = [(1 - PESO_CORRECCION) * p for p in probabilidades]
    nuevas[elegido] += PESO_CORRECCION
    orden = sorted(range(len(nuevas)), key=lambda i: -nuevas[i])
    motivos = [(claves[i], config.CATEGORIAS_MOTIVO[claves[i]], nuevas[i]) for k, i in enumerate(orden)
               if k == 0 or nuevas[i] >= config.UMBRAL_MOTIVO_SECUNDARIO]
    return motivos, nuevas, "corregido"


def pedir_preferencias():
    print("\nAhora unas preguntas prácticas para buscar opciones de atención:")
    modalidad = preguntar("  Modalidad (en linea / presencial / cualquiera): ",
                          ["linea", "presencial", "cualquiera"])
    alcaldia = ""
    if modalidad != "linea":
        alcaldia = pedir_alcaldia()
    horario = preguntar("  Horario preferido (manana / tarde / noche / cualquiera): ",
                        ["manana", "tarde", "noche", "cualquiera"])
    while True:
        costo = preguntar("  Costo máximo por sesión en pesos (0 si buscas opciones gratuitas): ")
        if costo.isdigit():
            break
        print("  Escribe solo números.")
    idioma = preguntar("  Idioma (espanol / ingles / otro): ", ["espanol", "ingles", "otro"])
    return {"modalidad": modalidad, "horario": horario, "costo_maximo": int(costo), "idioma": idioma,
            "alcaldia": alcaldia}


def pedir_alcaldia():
    """Solo se pide la alcaldia (no la direccion) para calcular distancias aproximadas."""
    nombres = list(ALCALDIAS)
    print("  ¿En qué alcaldía te queda mejor tomar la consulta? (solo se usa para calcular distancias)")
    for i in range(0, len(nombres), 4):
        print("    " + "   ".join(f"{j + 1:>2}. {nombres[j]}" for j in range(i, min(i + 4, len(nombres)))))
    eleccion = preguntar("  Número (0 = prefiero no decir): ", [str(i) for i in range(len(nombres) + 1)])
    return "" if eleccion == "0" else nombres[int(eleccion) - 1]


def construir_perfil(relato, prioridad, motivos, duracion, contextos, voz, preferencias, compartir,
                     confirmacion="sin respuesta"):
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
    lineas.append("  Confirmación del tema: " + {"si": "la persona lo confirmó",
                                                 "corregido": "la persona lo eligió al corregir"}
                  .get(confirmacion, "sin confirmar"))
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
        f"  Alcaldía para consulta presencial: {preferencias.get('alcaldia') or 'No indicada'}",
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

    # Modalidad de entrada. Con voz: emocion percibida (modelo propio) y,
    # si el modulo opcional voz_en_vivo esta instalado, grabacion con el
    # microfono y transcripcion. Sin el, la persona escribe su relato.
    voz, relato = None, None
    if preguntar("\n¿Cómo quieres empezar? (texto / voz): ", ["texto", "voz"]) == "voz":
        voz, relato = entrada_por_voz()
        if relato is None:
            print("\nPor favor escribe tu relato para continuar.")

    if relato is None:
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

    probabilidades = predecir(modelo_texto, relato, "red")
    print("\nLo que entendí (puede no ser exacto):")
    for posicion, (_, nombre, p) in enumerate(motivos):
        print(f"  {'Tema principal' if posicion == 0 else 'También'}: {nombre} ({p * 100:.0f} %)")
    motivos, probabilidades, confirmacion = confirmar_motivo(motivos, probabilidades)

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

    preferencias = pedir_preferencias()
    compartir = preguntar("\n¿Autorizas compartir este resumen con el profesional que elijas? "
                          "(si / no): ", ["si", "no"]) == "si"

    perfil = construir_perfil(relato, prioridad, motivos, duracion, contextos,
                              voz, preferencias, compartir, confirmacion)
    print("\n" + perfil)

    numero = 1
    while existe_archivo(config.ruta_salida(f"perfil_{numero:03d}.txt")):
        numero += 1
    ruta = config.ruta_salida(f"perfil_{numero:03d}.txt")
    guardar_texto(ruta, perfil + "\n")
    print("\nResumen guardado en:", ruta)

    # 3. Registro del paciente y recomendacion
    alias = preguntar("\n¿Con qué nombre o alias quieres que te identifiquemos? "
                      "(Enter para usar un número): ", permitir_vacio=True)
    id_paciente = registrar_paciente({
        "alias": alias,
        "relato": relato,
        "probabilidades": probabilidades,
        "motivo_confirmado": confirmacion,
        "motivo_principal": motivos[0][0],
        "motivos_secundarios": [clave for clave, _, _ in motivos[1:]],
        "duracion_dias": duracion["dias"] if duracion else "",
        "contextos": contextos,
        "prioridad": prioridad["nivel"],
        "emocion_voz": voz.get("emocion", "") if voz else "",
        "palabra_voz": voz.get("palabra", "") if voz else "",
        "preferencias": preferencias,
        "compartir": compartir,
    })
    print(f"Quedaste registrado/a como {id_paciente}. Guarda este número para el seguimiento.")
    recomendar_y_solicitar(id_paciente)


def recomendar_y_solicitar(id_paciente):
    """Muestra las opciones compatibles y crea la solicitud que elija la persona."""
    paciente = cargar_paciente(id_paciente)
    try:
        psicologos = cargar_psicologos()
    except ValueError as error:
        print("No se pudo leer el registro de psicólogos:", error)
        return
    opciones, excluidos = recomendar(paciente, psicologos)
    if not opciones:
        print("\nNo encontramos profesionales que cumplan tus condiciones de idioma "
              "y disponibilidad. Puedes intentar con otras preferencias.")
        return

    print("\n" + "=" * 60)
    print("PROFESIONALES COMPATIBLES (ordenados; tú decides)")
    print("=" * 60)
    for posicion, opcion in enumerate(opciones, start=1):
        print(texto_opcion(posicion, opcion) + "\n")
    ruta_mapa = generar_recomendacion_html(paciente, opciones)
    print(f"Ver las opciones en el mapa: {ruta_mapa}")
    if excluidos:
        print(f"({len(excluidos)} profesional(es) no se muestran: no atienden en tu idioma "
              "o no aceptan pacientes nuevos.)")

    validas = [str(i) for i in range(len(opciones) + 1)]
    eleccion = preguntar(f"\nElige un número (1-{len(opciones)}) para solicitar contacto, "
                         "o 0 para no solicitar por ahora: ", validas)
    if eleccion == "0":
        print("Está bien. Tu perfil queda guardado por si quieres volver.")
        return
    elegido = opciones[int(eleccion) - 1]
    psicologo = elegido["psicologo"]
    id_solicitud = crear_solicitud(id_paciente, psicologo["id"], elegido["total"])
    print(f"\nSolicitud {id_solicitud} enviada a {psicologo['nombre']}. Estado: pendiente.")
    if paciente["consentimiento_compartir"]:
        print("\nEsto es lo que recibirá el profesional:\n")
        print(generar_resumen(paciente, elegido["total"]))
    else:
        print("No autorizaste compartir tu resumen; el profesional solo verá tu solicitud.")
    generar_panel_html(psicologo["id"])


if __name__ == "__main__":
    main()
