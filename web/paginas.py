# ==============================================================
# PAGINAS Y ACCIONES DEL SERVIDOR WEB
# ==============================================================
# Cada funcion recibe los datos del formulario (diccionario de
# listas, como lo entrega urllib.parse.parse_qs) y devuelve HTML.
# Todas las decisiones las toman los modulos propios:
#   texto/       seguridad, motivo, duracion, contextos
#   vinculacion/ registro, compatibilidad, solicitudes, seguimiento
# Esta capa solo traduce entre formularios y esas funciones.
# ==============================================================

import config
from nucleo.archivos import existe_archivo
from texto.seguridad import evaluar_prioridad
from texto.extraccion import extraer_duracion, extraer_contextos, describir_duracion
from texto.modelo_texto import cargar_modelo as cargar_modelo_texto, interpretar_motivos, predecir
from vinculacion.registro import (registrar_paciente, cargar_paciente, cargar_psicologos,
                                  registrar_psicologo)
from vinculacion.compatibilidad import recomendar
from vinculacion.solicitudes import (crear_solicitud, generar_resumen, cambiar_estado,
                                     revocar_consentimiento, solicitudes_de)
from vinculacion.seguimiento import registrar as registrar_seguimiento, analizar_paciente, VARIABLES
from vinculacion.geografia import ALCALDIAS
from vinculacion.mapa import html_recomendacion
from vinculacion.panel import html_panel, escapar_html
from visual.svg import crear_svg_curvas
from web.diseno import (pagina, tarjeta, mensaje_error, opciones_radio, opciones_casilla,
                        lista_seleccion, navegacion)
from web.grabadora import HTML_GRABADORA, SCRIPT_GRABADORA

PESO_CORRECCION = 0.6        # igual que en orientacion.py
_modelo_texto = {}


def modelo_texto():
    """Carga el clasificador una sola vez."""
    if "modelo" not in _modelo_texto:
        _modelo_texto["modelo"] = cargar_modelo_texto()
    return _modelo_texto["modelo"]


def campo(datos, nombre, defecto=""):
    return datos.get(nombre, [defecto])[0].strip()


def lista(datos, nombre):
    return [v.strip() for v in datos.get(nombre, []) if v.strip()]


def oculto(nombre, valor):
    return f'<input type="hidden" name="{nombre}" value="{escapar_html(valor)}">'


# --------------------------------------------------------------
# Inicio y resultados
# --------------------------------------------------------------

REPORTES = [
    ("reporte_emociones.html", "Emociones en la voz", "Red neuronal con 11 variables acústicas · MESD"),
    ("reporte_palabras.html", "Palabras aisladas", "MFCC + FFT + red neuronal · 24 palabras"),
    ("reporte_texto.html", "Motivos de consulta", "Naive Bayes y red neuronal sobre TF-IDF · seguridad"),
    ("reporte_vinculacion.html", "Extracción y matching", "Exactitud por campo · precision@3"),
    ("resultado.html", "Análisis de señales", "Fourier, ventanas y detección de voz"),
]


def _tarjetas_reportes():
    html = ""
    for archivo, titulo, descripcion in REPORTES:
        if existe_archivo(config.ruta_salida(archivo)):
            html += (f'<a class="enlace" href="/salidas/{archivo}" target="_blank"><h3>{titulo}</h3>'
                     f'<p>{descripcion}</p></a>')
        else:
            html += (f'<div class="enlace inactivo"><h3>{titulo}</h3><p>{descripcion}</p>'
                     f'<p style="margin-top:8px;font-size:12px">Aún no generado</p></div>')
    return f'<div class="cuadricula">{html}</div>'


def inicio():
    portada = f"""<div class="portada"><div class="interior"><div>
<span class="etiqueta-sup">ESCOM · IPN · Temas Selectos de Aprendizaje Profundo</span>
<h1>Encuentra al profesional que mejor se adapta a ti</h1>
<p>Cuéntanos con tus palabras, por texto o voz, lo que estás viviendo. El sistema te orienta y te muestra
psicólogos compatibles, cerca de ti y dentro de tu presupuesto. Tú decides.</p>
<a class="boton" href="/orientacion">Comenzar orientación</a>
<a class="boton secundario" href="/panel">Soy psicólogo</a>
</div>
<div class="tarjeta-flotante">
<div><span>1</span><p style="margin:0">Hablas o escribes lo que te pasa</p></div>
<div><span>2</span><p style="margin:0">Revisamos si necesitas ayuda inmediata</p></div>
<div><span>3</span><p style="margin:0">Confirmas el tema y tus preferencias</p></div>
<div><span>4</span><p style="margin:0">Eliges entre opciones compatibles en el mapa</p></div>
<div><span>5</span><p style="margin:0">Das seguimiento entre sesiones</p></div>
</div></div></div>"""
    contenido = (
        '<div class="aviso">Este sistema orienta; <b>no diagnostica</b> ni atiende emergencias. '
        'Si estás en peligro llama al <b>911</b> o a la <b>Línea de la Vida 800 911 2000</b> (24 horas).</div>'
        + tarjeta("¿Qué quieres hacer?", '<div class="cuadricula">'
                  '<a class="enlace" href="/orientacion"><h3>Nueva orientación</h3><p>Texto o voz · 5 minutos</p></a>'
                  '<a class="enlace" href="/seguimiento"><h3>Registrar seguimiento</h3><p>Ánimo y sueño entre sesiones</p></a>'
                  '<a class="enlace" href="/permisos"><h3>Mis permisos</h3><p>Retirar el permiso de compartir mi resumen</p></a>'
                  '<a class="enlace" href="/panel"><h3>Panel del psicólogo</h3><p>Solicitudes, resúmenes y seguimiento</p></a>'
                  '<a class="enlace" href="/psicologos/nuevo"><h3>Registrar psicólogo</h3><p>Alta de un perfil profesional</p></a>'
                  '</div>')
        + tarjeta("Resultados de los modelos", _tarjetas_reportes()))
    return pagina("Inicio", contenido, "inicio", portada=portada)


def reportes(mensaje=""):
    contenido = (mensaje
                 + tarjeta("Reportes de evaluación", _tarjetas_reportes()
                           + '<form method="post" action="/evaluar" style="margin-top:20px">'
                             '<button class="boton dorado">Volver a evaluar extracción y matching</button></form>')
                 + tarjeta("Hoja de anotación del matching",
                           '<p>Cada integrante ordena los 3 psicólogos más adecuados por caso, sin ver la '
                           'recomendación del programa.</p><a class="boton secundario" target="_blank" '
                           'href="/salidas/hoja_anotacion_matching.html">Abrir hoja</a>'))
    return pagina("Resultados", contenido, "reportes", "Métricas calculadas con funciones propias")


def evaluar():
    import evaluar_vinculacion
    evaluar_vinculacion.main()
    return reportes('<div class="exito">Evaluación actualizada.</div>')


# --------------------------------------------------------------
# Orientacion en tres pasos
# --------------------------------------------------------------

def orientacion_paso1(error="", relato=""):
    contenido = f"""{mensaje_error(error)}
<div class="ventana"><span class="paso">Paso 1 de 3</span><h2>Cuéntanos qué te trae por aquí</h2>
<form method="post" action="/orientacion" class="formulario">
<div class="aviso">Antes de empezar: este sistema <b>no es un psicólogo</b> ni hace diagnósticos. Su función es
ayudarte a describir lo que te pasa y orientarte hacia un profesional humano. Lo que escribas o digas solo se
usa para armar un resumen que <b>tú decides</b> si se comparte. Las grabaciones se quedan en esta computadora.</div>
<div class="opciones"><label><input type="checkbox" name="acepto" value="si" required>
Acepto continuar con estas condiciones</label></div>
<label>Puedes hablar <span class="ayuda">(se transcribe y después puedes corregir el texto)</span></label>
{HTML_GRABADORA}
<label for="relato">o escribir con tus palabras</label>
<textarea id="relato" name="relato" placeholder="Por ejemplo: desde hace dos meses no puedo dormir y me siento muy presionada por la escuela..."
 required>{escapar_html(relato)}</textarea>
<p style="margin-top:20px"><button class="boton">Continuar</button></p>
</form></div>{SCRIPT_GRABADORA}"""
    return pagina("Orientación inicial", contenido, "orientacion", "Texto o voz · tú decides qué compartir")


def pagina_protocolo(resultado):
    recursos = "".join(f"<li>{escapar_html(r)}</li>" for r in resultado["recursos"])
    contenido = (f'<div class="ventana recursos"><h2>{escapar_html(resultado["mensaje"])}</h2>'
                 f'<ul>{recursos}</ul><p>La orientación automática se detiene aquí. Por favor contacta a '
                 f'una persona ahora; no tienes que pasar por esto solo/a.</p></div>')
    return pagina("Busca ayuda ahora", contenido, "orientacion")


def _barras_temas(motivos):
    return "".join(f'<div class="tema"><div class="nombre">{escapar_html(nombre)}</div>'
                   f'<div class="fondo"><div class="relleno" style="width:{p * 100:.0f}%"></div></div>'
                   f'<div class="valor">{p * 100:.0f} %</div></div>' for _, nombre, p in motivos)


def orientacion_paso2(datos, error=""):
    relato = campo(datos, "relato")
    if campo(datos, "acepto") != "si":
        return orientacion_paso1("Para continuar necesitas aceptar las condiciones.", relato)
    if len(relato) < 5:
        return orientacion_paso1("Escribe o graba un poco más sobre lo que te pasa.", relato)

    prioridad = evaluar_prioridad(relato)               # seguridad PRIMERO
    if prioridad["nivel"] == "protocolo":
        return pagina_protocolo(prioridad)

    motivos = interpretar_motivos(modelo_texto(), relato)
    duracion = extraer_duracion(relato)
    contextos = extraer_contextos(relato)
    alerta = ""
    if prioridad["nivel"] == "prioritario":
        recursos = "".join(f"<li>{escapar_html(r)}</li>" for r in prioridad["recursos"])
        alerta = f'<div class="aviso"><b>{escapar_html(prioridad["mensaje"])}</b><ul>{recursos}</ul></div>'

    temas = [(c, n) for c, n in config.CATEGORIAS_MOTIVO.items()]
    voz = ""
    if campo(datos, "voz_emocion"):
        voz = (f'<p><span class="etiqueta aceptada">Emoción percibida en tu voz: {escapar_html(campo(datos, "voz_emocion"))} '
               f'({escapar_html(campo(datos, "voz_emocion_prob"))} %)</span> <span class="ayuda">dato orientativo</span></p>')
    texto_duracion = (f'<p>Duración que mencionaste: <b>{describir_duracion(duracion["dias"])}</b></p>' if duracion
                      else '<label>¿Desde hace cuánto te sientes así? <span class="ayuda">(opcional, por ejemplo '
                           '"dos semanas")</span></label><input type="text" name="duracion_texto">')
    alcaldias = [(a, a) for a in ALCALDIAS]
    contenido = f"""{mensaje_error(error)}{alerta}
<form method="post" action="/orientacion/registrar" class="formulario">
{oculto("relato", relato)}{oculto("voz_emocion", campo(datos, "voz_emocion"))}
{oculto("voz_emocion_prob", campo(datos, "voz_emocion_prob"))}{oculto("voz_palabra", campo(datos, "voz_palabra"))}
<div class="ventana"><span class="paso">Paso 2 de 3</span><h2>Esto es lo que entendí</h2>
<p class="ayuda">Puede no ser exacto. Lo que tú digas pesa más que lo que infiere el sistema.</p>
{_barras_temas(motivos)}{voz}
<p>Contextos que mencionaste: <b>{escapar_html(", ".join(contextos) or "ninguno identificado")}</b></p>
<label>¿Se parece a lo que te pasa?</label>
{opciones_radio("confirmacion", [("si", "Sí, se parece"), ("no", "No, es otro tema")], "si")}
<label>Si no, ¿qué tema lo describe mejor?</label>
{lista_seleccion("tema_elegido", temas, vacia="(elige un tema)")}
{texto_duracion}
</div>
<div class="ventana"><span class="paso">Paso 3 de 3</span><h2>Tus preferencias</h2>
<div class="dos"><div><label>Modalidad</label>
{opciones_radio("modalidad", [("linea", "En línea"), ("presencial", "Presencial"), ("cualquiera", "Cualquiera")], "cualquiera")}
</div><div><label>Horario</label>
{opciones_radio("horario", [("manana", "Mañana"), ("tarde", "Tarde"), ("noche", "Noche"), ("cualquiera", "Cualquiera")], "cualquiera")}
</div></div>
<div class="dos"><div><label>Alcaldía para consulta presencial <span class="ayuda">(solo para calcular distancias)</span></label>
{lista_seleccion("alcaldia", alcaldias, vacia="Prefiero no decir")}</div>
<div><label>Costo máximo por sesión (pesos) <span class="ayuda">0 = solo opciones gratuitas</span></label>
<input type="number" name="costo" min="0" step="50" value="500" required></div></div>
<div class="dos"><div><label>Idioma</label>
{opciones_radio("idioma", [("espanol", "Español"), ("ingles", "Inglés"), ("otro", "Otro")], "espanol")}</div>
<div><label>¿Cómo te llamamos? <span class="ayuda">(alias, no tu nombre completo)</span></label>
<input type="text" name="alias" maxlength="40"></div></div>
<div class="opciones" style="margin-top:20px"><label><input type="checkbox" name="compartir" value="si">
Autorizo compartir mi resumen con el profesional que elija</label></div>
<p style="margin-top:22px"><button class="boton">Ver profesionales compatibles</button></p>
</div></form>"""
    return pagina("Orientación inicial", contenido, "orientacion")


def orientacion_registrar(datos):
    """Valida, registra al paciente y devuelve su ID (o lanza ValueError)."""
    relato = campo(datos, "relato")
    if not relato:
        raise ValueError("Falta el relato.")
    prioridad = evaluar_prioridad(relato)
    if prioridad["nivel"] == "protocolo":
        raise PermissionError("protocolo")
    duracion_texto = campo(datos, "duracion_texto")
    if duracion_texto and evaluar_prioridad(duracion_texto)["nivel"] == "protocolo":
        raise PermissionError("protocolo")

    modelos = modelo_texto()
    probabilidades = predecir(modelos, relato, "red")
    motivos = interpretar_motivos(modelos, relato)
    confirmacion = "si"
    claves = list(config.CATEGORIAS_MOTIVO)
    if campo(datos, "confirmacion") == "no":
        elegido = campo(datos, "tema_elegido")
        if elegido in claves:
            confirmacion = "corregido"
            probabilidades = [(1 - PESO_CORRECCION) * p for p in probabilidades]
            probabilidades[claves.index(elegido)] += PESO_CORRECCION
            orden = sorted(range(len(claves)), key=lambda i: -probabilidades[i])
            motivos = [(claves[i], config.CATEGORIAS_MOTIVO[claves[i]], probabilidades[i])
                       for k, i in enumerate(orden) if k == 0 or probabilidades[i] >= config.UMBRAL_MOTIVO_SECUNDARIO]
        else:
            confirmacion = "sin respuesta"

    duracion = extraer_duracion(relato)
    if duracion is None and duracion_texto:
        duracion = extraer_duracion(duracion_texto if "hace" in duracion_texto.lower() else "hace " + duracion_texto)

    costo = campo(datos, "costo", "0")
    if not costo.isdigit():
        raise ValueError("El costo debe ser un número entero mayor o igual a 0.")
    modalidad = campo(datos, "modalidad", "cualquiera")
    horario = campo(datos, "horario", "cualquiera")
    idioma = campo(datos, "idioma", "espanol")
    alcaldia = campo(datos, "alcaldia")
    if modalidad not in ("linea", "presencial", "cualquiera") or horario not in ("manana", "tarde", "noche", "cualquiera") \
            or idioma not in config.IDIOMAS or (alcaldia and alcaldia not in ALCALDIAS):
        raise ValueError("Alguna preferencia no es válida.")

    return registrar_paciente({
        "alias": campo(datos, "alias")[:40],
        "relato": relato,
        "probabilidades": probabilidades,
        "motivo_principal": motivos[0][0],
        "motivos_secundarios": [c for c, _, _ in motivos[1:]],
        "motivo_confirmado": confirmacion,
        "duracion_dias": duracion["dias"] if duracion else "",
        "contextos": extraer_contextos(relato),
        "prioridad": prioridad["nivel"],
        "emocion_voz": campo(datos, "voz_emocion"),
        "palabra_voz": campo(datos, "voz_palabra"),
        "preferencias": {"modalidad": modalidad, "horario": horario, "costo_maximo": int(costo),
                         "idioma": idioma, "alcaldia": alcaldia if modalidad != "linea" else ""},
        "compartir": campo(datos, "compartir") == "si",
    })


def recomendacion(id_paciente, mensaje=""):
    paciente = cargar_paciente(id_paciente)
    if paciente is None:
        return None
    opciones, _ = recomendar(paciente, cargar_psicologos())
    if not opciones:
        return pagina("Sin opciones", tarjeta("No encontramos profesionales",
                      "<p>Nadie cumple tus condiciones de idioma y disponibilidad. Intenta otra orientación "
                      "con otras preferencias.</p>"), "orientacion")
    aviso_id = (f'<div class="exito" style="max-width:1200px;margin:16px auto">Tu número de paciente es '
                f'<b>{escapar_html(id_paciente)}</b>. Guárdalo para registrar tu seguimiento. {mensaje}</div>')
    html = html_recomendacion(paciente, opciones, navegacion("orientacion") + aviso_id, web=True)
    from web.diseno import ESTILOS_WEB
    return html.replace("</style></head>", ESTILOS_WEB + "</style></head>", 1)


def solicitar(datos):
    id_paciente, id_psicologo = campo(datos, "paciente"), campo(datos, "psicologo")
    paciente = cargar_paciente(id_paciente)
    if paciente is None:
        raise ValueError("No existe ese paciente.")
    opciones, _ = recomendar(paciente, cargar_psicologos(), cantidad=50)
    elegido = next((o for o in opciones if o["psicologo"]["id"] == id_psicologo), None)
    if elegido is None:
        raise ValueError("Ese profesional no está entre tus opciones compatibles.")
    id_solicitud = crear_solicitud(id_paciente, id_psicologo, elegido["total"])
    p = elegido["psicologo"]
    if paciente["consentimiento_compartir"]:
        resumen = (f'<p>Esto es lo que recibirá el profesional:</p>'
                   f'<pre style="white-space:pre-wrap;background:#fcfafb;border:1px solid var(--borde);'
                   f'border-radius:12px;padding:16px">{escapar_html(generar_resumen(paciente, elegido["total"]))}</pre>')
    else:
        resumen = '<p>No autorizaste compartir tu resumen; el profesional solo verá tu solicitud.</p>'
    contenido = tarjeta(f"Solicitud {escapar_html(id_solicitud)} enviada",
                        f'<div class="exito">Le enviamos tu solicitud a <b>{escapar_html(p["nombre"])}</b>. '
                        f'Estado: pendiente.</div>{resumen}'
                        f'<p><a class="boton" href="/seguimiento">Registrar seguimiento</a> '
                        f'<a class="boton secundario" href="/panel/{escapar_html(p["id"])}">Ver el panel del profesional</a></p>')
    return pagina("Solicitud enviada", contenido, "orientacion")


# --------------------------------------------------------------
# Panel del psicologo
# --------------------------------------------------------------

def panel_lista():
    tarjetas = ""
    for p in cargar_psicologos():
        pendientes = sum(1 for s in solicitudes_de(p["id"]) if s["estado"] == "pendiente")
        areas = ", ".join(config.CATEGORIAS_MOTIVO[t] for t, _ in sorted(p["areas"].items(), key=lambda x: -x[1])[:2])
        etiqueta = (f'<span class="etiqueta pendiente">{pendientes} pendiente(s)</span>' if pendientes else "")
        tarjetas += (f'<a class="enlace" href="/panel/{p["id"]}"><h3>{escapar_html(p["nombre"])}</h3>'
                     f'<p>{escapar_html(areas)}</p><p style="margin-top:8px">{p["id"]} · '
                     f'{escapar_html(p.get("alcaldia") or "en línea")} {etiqueta}</p></a>')
    return pagina("Profesionales", tarjeta("Elige tu perfil (ficticios)", f'<div class="cuadricula">{tarjetas}</div>'),
                  "panel", "Solicitudes, resúmenes autorizados y seguimiento")


def panel(id_psicologo):
    html = html_panel(id_psicologo, navegacion("panel"), web=True)
    from web.diseno import ESTILOS_WEB
    return html.replace("</style></head>", ESTILOS_WEB + "</style></head>", 1)


def panel_estado(id_psicologo, datos):
    id_solicitud = campo(datos, "solicitud")
    if not any(s["id"] == id_solicitud for s in solicitudes_de(id_psicologo)):
        raise ValueError("Esa solicitud no es de este profesional.")
    cambiar_estado(id_solicitud, campo(datos, "estado"))


# --------------------------------------------------------------
# Seguimiento, permisos y registro de psicologos
# --------------------------------------------------------------

def seguimiento(datos=None, error="", resultado=""):
    datos = datos or {}
    contenido = f"""{mensaje_error(error)}{resultado}
<div class="ventana"><h2>Registro entre sesiones</h2>
<p class="ayuda">Es voluntario. Tu psicólogo solo lo ve si lo compartes y aceptó tu solicitud.</p>
<form method="post" action="/seguimiento" class="formulario">
<div class="dos"><div><label>Tu número de paciente</label>
<input type="text" name="paciente" placeholder="PA001" value="{escapar_html(campo(datos, "paciente"))}" required></div>
<div><label>Fecha de la sesión</label><input type="date" name="fecha" required></div></div>
<label>¿Cómo estuvo tu ánimo? <span class="ayuda">1 = muy bajo, 10 = muy bien</span></label>
<input type="range" name="animo" min="1" max="10" value="5" style="width:100%"
 oninput="document.getElementById('valor-animo').textContent=this.value">
<p>Ánimo: <b id="valor-animo">5</b></p>
<label>Horas de sueño por noche (promedio)</label>
<input type="number" name="sueno" min="0" max="24" step="0.5" value="7" required>
<label>¿Algo importante que quieras anotar? <span class="ayuda">(opcional)</span></label>
<input type="text" name="acontecimiento" maxlength="200">
<div class="opciones" style="margin-top:16px"><label><input type="checkbox" name="compartir" value="si" checked>
Compartir este registro con mi psicólogo</label></div>
<p style="margin-top:20px"><button class="boton">Guardar registro</button></p>
</form></div>"""
    return pagina("Seguimiento", contenido, "seguimiento", "Ánimo y sueño entre sesiones")


def seguimiento_guardar(datos):
    id_paciente = campo(datos, "paciente").upper()
    if cargar_paciente(id_paciente) is None:
        raise ValueError("No encontramos ese número de paciente.")
    nota = campo(datos, "acontecimiento")
    if nota and evaluar_prioridad(nota)["nivel"] == "protocolo":
        raise PermissionError("protocolo")
    registrar_seguimiento(id_paciente, campo(datos, "fecha"), campo(datos, "animo"),
                          campo(datos, "sueno"), nota, campo(datos, "compartir") == "si")
    analisis = analizar_paciente(id_paciente, solo_compartidos=False)
    graficas = ""
    for variable, (nombre, minimo, maximo, _) in VARIABLES.items():
        serie = analisis["series"][variable]
        if variable == "sueno":
            maximo = max(12.0, max(serie))
        svg = crear_svg_curvas([(nombre, serie, "#6c1d45")], f"{nombre} por sesión", "", etiqueta_y=nombre,
                               ancho=560, alto=260, etiqueta_x="Sesión", y_min=minimo, y_max=maximo, leyenda=False)
        graficas += f'<div class="grafica">{svg}</div>' if svg else ""
    mensajes = "".join(f'<div class="cambio{" marcado" if a["marcado"] else ""}">{escapar_html(a["mensaje"])}</div>'
                       for a in analisis["analisis"])
    resultado = tarjeta("Registro guardado", f'<div class="exito">Gracias. Tu registro quedó guardado.</div>'
                        f'<div class="graficas">{graficas}</div>{mensajes}')
    return seguimiento({"paciente": [id_paciente]}, resultado=resultado)


def permisos(error="", mensaje=""):
    contenido = f"""{mensaje_error(error)}{mensaje}
<div class="ventana"><h2>Retirar el permiso de compartir mi resumen</h2>
<p>Si lo retiras, los profesionales dejan de ver tu resumen y tu relato se borra del registro.</p>
<form method="post" action="/permisos" class="formulario">
<label>Tu número de paciente</label><input type="text" name="paciente" placeholder="PA001" required>
<div class="opciones" style="margin-top:16px"><label><input type="checkbox" name="confirmo" value="si" required>
Confirmo que quiero retirar el permiso</label></div>
<p style="margin-top:20px"><button class="boton">Retirar permiso</button></p></form></div>"""
    return pagina("Mis permisos", contenido, "inicio")


def permisos_guardar(datos):
    id_paciente = campo(datos, "paciente").upper()
    paciente = cargar_paciente(id_paciente)
    if paciente is None:
        raise ValueError("No encontramos ese número de paciente.")
    if campo(datos, "confirmo") != "si":
        raise ValueError("Confirma que quieres retirar el permiso.")
    revocar_consentimiento(id_paciente)
    return permisos(mensaje='<div class="exito">Permiso retirado. Los profesionales ya no ven tu resumen.</div>')


def psicologo_nuevo(error="", mensaje=""):
    areas = "".join(
        f'<div class="tema"><div class="nombre">{escapar_html(n)}</div>'
        f'<input type="range" name="area_{c}" min="0" max="1" step="0.1" value="0" style="flex:1" '
        f'oninput="this.nextElementSibling.textContent=this.value"><div class="valor">0</div></div>'
        for c, n in config.CATEGORIAS_MOTIVO.items())
    contenido = f"""{mensaje_error(error)}{mensaje}
<div class="ventana"><h2>Registro de profesional</h2>
<p class="ayuda">Prototipo: la cédula queda como "validación pendiente".</p>
<form method="post" action="/psicologos/nuevo" class="formulario">
<div class="dos"><div><label>Nombre</label><input type="text" name="nombre" required></div>
<div><label>Formación</label><input type="text" name="formacion"></div></div>
<div class="dos"><div><label>Enfoque terapéutico</label><input type="text" name="enfoque"></div>
<div><label>Población que atiende</label><input type="text" name="poblacion"></div></div>
<label>Experiencia por tema <span class="ayuda">(0 = nada, 1 = mucha)</span></label>{areas}
<label>Idiomas</label>{opciones_casilla("idiomas", [("espanol", "Español"), ("ingles", "Inglés"), ("otro", "Otro")], ["espanol"])}
<label>Modalidad</label>{opciones_casilla("modalidad", [("linea", "En línea"), ("presencial", "Presencial")])}
<label>Horarios</label>{opciones_casilla("horarios", [("manana", "Mañana"), ("tarde", "Tarde"), ("noche", "Noche")])}
<div class="dos"><div><label>Alcaldía del consultorio</label>{lista_seleccion("alcaldia", [(a, a) for a in ALCALDIAS], vacia="Solo en línea")}</div>
<div><label>Costo por sesión (pesos, 0 = gratuito)</label><input type="number" name="costo" min="0" step="50" value="500" required></div></div>
<p style="margin-top:20px"><button class="boton">Registrar</button></p></form></div>"""
    return pagina("Registrar psicólogo", contenido, "panel")


def psicologo_guardar(datos):
    areas = []
    for clave in config.CATEGORIAS_MOTIVO:
        valor = campo(datos, f"area_{clave}", "0")
        try:
            if float(valor) > 0:
                areas.append(f"{clave}:{float(valor):g}")
        except ValueError:
            raise ValueError(f"Valor inválido para {clave}.")
    identificador = registrar_psicologo({
        "nombre": campo(datos, "nombre"), "formacion": campo(datos, "formacion"),
        "enfoque": campo(datos, "enfoque"), "poblacion": campo(datos, "poblacion"),
        "areas": ", ".join(areas), "idiomas": ", ".join(lista(datos, "idiomas")),
        "modalidad": ", ".join(lista(datos, "modalidad")), "horarios": ", ".join(lista(datos, "horarios")),
        "costo": campo(datos, "costo"), "alcaldia": campo(datos, "alcaldia"), "acepta_pacientes": "si",
    })
    return psicologo_nuevo(mensaje=f'<div class="exito">Registrado como <b>{identificador}</b>. '
                                   f'<a href="/panel/{identificador}">Ver su panel</a></div>')
