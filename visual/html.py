# ==============================================================
# PAGINA WEB DE RESULTADOS (HTML + SVG) SIN FRAMEWORKS
# ==============================================================
# El documento se arma por secciones; cada seccion es una funcion
# que devuelve su bloque de HTML.
# ==============================================================

from config import ruta_salida
from nucleo.archivos import guardar_texto
from reportes.formato import formatear_valor_caracteristica
from visual.svg import crear_svg, crear_svg_tres_intensidades


ESTILOS_CSS = """
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, sans-serif; background: #eeeeee; color: #222222; }
.encabezado { background: #222222; color: white; padding: 25px; text-align: center; }
.encabezado h1 { margin: 0; font-size: 28px; }
.encabezado p { margin-top: 10px; margin-bottom: 0; }
.menu { background: #333333; padding: 12px; text-align: center; position: sticky; top: 0; z-index: 10; }
.menu button { border: none; padding: 12px 18px; margin: 4px; cursor: pointer; background: white;
               color: #222222; border-radius: 5px; font-size: 14px; }
.menu button:hover { background: #dddddd; }
.contenedor { width: 94%; max-width: 1400px; margin: 25px auto; }
.ventana { display: none; background: white; border: 1px solid #cccccc; border-radius: 8px;
           padding: 25px; margin-bottom: 25px; box-shadow: 0 3px 8px rgba(0,0,0,0.10); }
.ventana.activa { display: block; }
.ventana h2 { margin-top: 0; border-bottom: 1px solid #dddddd; padding-bottom: 12px; }
.tarjetas { display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0; }
.tarjeta { border: 1px solid #cccccc; border-radius: 6px; padding: 18px; min-width: 180px;
           flex: 1; background: #fafafa; }
.tarjeta strong { display: block; font-size: 22px; margin-top: 7px; }
.grafica { width: 100%; overflow-x: auto; border: 1px solid #dddddd; margin-top: 15px;
           padding: 10px; background: white; }
.grafica svg { max-width: 100%; height: auto; }
.dos_columnas { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.cuadricula_letras { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 15px; }
.cuadricula_letras .tarjeta { min-width: 0; overflow: hidden; }
.tabla { width: 100%; border-collapse: collapse; margin-top: 15px; }
.tabla th, .tabla td { border: 1px solid #cccccc; padding: 10px; text-align: left; }
.tabla th { background: #eeeeee; }
.info { padding: 15px; border-left: 4px solid #555555; background: #f5f5f5; margin: 15px 0; }
.pie { text-align: center; padding: 25px; color: #666666; }
@media (max-width: 800px) {
    .dos_columnas, .cuadricula_letras { grid-template-columns: 1fr; }
    .menu button { width: 90%; }
}
"""

SCRIPT_JS = """
function mostrarVentana(id) {
    var ventanas = document.getElementsByClassName("ventana");
    for (var i = 0; i < ventanas.length; i++) {
        ventanas[i].classList.remove("activa");
    }
    var seleccionada = document.getElementById(id);
    if (seleccionada) {
        seleccionada.classList.add("activa");
    }
    window.scrollTo(0, 0);
}
"""

# (id de la seccion, texto del boton)
SECCIONES_MENU = [
    ("inicio", "Inicio"),
    ("lote", "Análisis Continuo por Lotes"),
    ("referencias", "Referencias de Sílabas"),
    ("seno", "Experimento 1"),
    ("senocoseno", "Experimento 2"),
    ("compleja", "Experimento 3"),
    ("voz", "Voz real"),
    ("fragmentos", "Fragmentos marcados"),
    ("abecedario", "Abecedario (demo)")
]


# --------------------------------------------------------------
# Piezas reutilizables
# --------------------------------------------------------------


def _tarjetas(pares):
    html = '<div class="tarjetas">'
    for etiqueta, valor in pares:
        html += f'<div class="tarjeta">{etiqueta}<strong>{valor}</strong></div>'
    return html + '</div>'


def _ventana(id_seccion, titulo, contenido, activa=False):
    clase = "ventana activa" if activa else "ventana"
    return f'<div id="{id_seccion}" class="{clase}">\n<h2>{titulo}</h2>\n{contenido}\n</div>\n'


def frecuencias_a_html(frecuencias):
    if len(frecuencias) == 0:
        return "<p>No se encontraron frecuencias dominantes.</p>"

    html = '<table class="tabla"><tr><th>Frecuencia</th><th>Magnitud</th></tr>'
    for frecuencia, magnitud in frecuencias:
        html += f"<tr><td>{round(frecuencia, 2)} Hz</td><td>{round(magnitud, 6)}</td></tr>"
    return html + "</table>"


def caracteristicas_a_html(caracteristicas):
    if caracteristicas is None:
        return "<p>No se pudieron calcular las características.</p>"

    etiquetas = [
        ("Amplitud máxima", "amplitud_maxima"),
        ("Amplitud pico a pico", "pico_a_pico"),
        ("RMS", "rms"),
        ("Energía de la señal", "energia"),
        ("Cruces por cero (ZCR)", "zcr"),
        ("Duración", "duracion"),
        ("Tiempo hablado estimado", "tiempo_hablado"),
        ("Tiempo de silencio interno", "tiempo_silencio"),
        ("Frecuencia dominante", "frecuencia_dominante"),
        ("Centroide espectral", "centroide_espectral"),
        ("Ancho de banda espectral", "ancho_banda_espectral"),
        ("Frecuencia fundamental estimada (F0)", "frecuencia_fundamental"),
        ("Variación de F0 (desv. estándar)", "variacion_f0"),
        ("Frecuencia de muestreo", "frecuencia_muestreo")
    ]

    html = '<h4>Vector de características acústicas</h4><table class="tabla">'
    html += "<tr><th>Variable</th><th>Valor</th></tr>"
    for etiqueta, nombre in etiquetas:
        if nombre in caracteristicas:
            texto = formatear_valor_caracteristica(nombre, caracteristicas)
            html += f"<tr><td>{etiqueta}</td><td>{texto}</td></tr>"
    html += "</table>"

    if "vector" in caracteristicas:
        valores = [str(round(v, 6)) for v in caracteristicas["vector"]]
        html += "<h4>Vector numérico en orden fijo</h4>"
        html += "<p><code>[" + ", ".join(valores) + "]</code></p>"

    return html


# --------------------------------------------------------------
# Secciones
# --------------------------------------------------------------


def _seccion_inicio():
    contenido = (
        "<p>Este sistema realiza diferentes etapas de procesamiento digital de señales "
        "utilizando implementaciones propias desde cero.</p>"
        + _tarjetas([
            ("Procesamiento matemático", "Desde cero"),
            ("Transformada", "DFT manual"),
            ("Ventana temporal", "25 ms"),
            ("Desplazamiento", "10 ms")
        ])
        + """
<div class="info">
<strong>Importante:</strong>
Este programa extrae propiedades físicas y matemáticas de señales de voz y detecta actividad
vocal (VAD). La detección de segmentos de voz no equivale por sí sola al reconocimiento
automático de cualquier palabra en español abierto.
</div>
<h3>Procesamiento implementado manualmente</h3>
<ul>
<li>Generación de señales sinusoidales y compuestas.</li>
<li>Funciones seno, coseno, raíz cuadrada y normalización de ángulos.</li>
<li>Lectura manual de cabeceras y muestras PCM en archivos WAV.</li>
<li>Segmentación automática de voz continua (VAD por energía RMS y fusión de pausas).</li>
<li>Ventana de Hann y Transformada Discreta de Fourier (DFT).</li>
<li>Frecuencia dominante, centroide espectral y ancho de banda espectral.</li>
<li>Energía total, RMS, tasa de cruces por cero (ZCR) y frecuencia fundamental (F0 por autocorrelación).</li>
<li>Representación gráfica mediante SVG generados manualmente.</li>
</ul>
"""
    )
    return _ventana("inicio", "Inicio", contenido, activa=True)


def _tabla_segmentos(segmentos):
    html = '<table class="tabla"><tr>'
    for encabezado in ("Seg.", "Inicio - Fin (s)", "Duración (s)", "Onda del Segmento", "RMS",
                       "Energía", "ZCR", "Frec. Dominante", "Centroide", "Ancho de Banda",
                       "F0 Estimada", "Tipo de Unidad / Estado"):
        html += f"<th>{encabezado}</th>"
    html += "</tr>"

    for seg in segmentos:
        c = seg["caracteristicas"]
        svg_mini = crear_svg(
            seg["muestras"], "", f"S{seg['id_segmento']} ({seg['duracion']:.2f}s)",
            ancho=260, alto=90
        )
        html += (
            f"<tr>"
            f"<td><strong>S{seg['id_segmento']}</strong></td>"
            f"<td>{seg['inicio']:.3f} - {seg['fin']:.3f}</td>"
            f"<td>{seg['duracion']:.3f}</td>"
            f"<td style=\"min-width:180px;\">{svg_mini}</td>"
            f"<td>{c['rms']:.4f}</td>"
            f"<td>{c['energia']:.2f}</td>"
            f"<td>{c['zcr']:.4f}</td>"
            f"<td>{c['frecuencia_dominante']:.2f} Hz</td>"
            f"<td>{c['centroide_espectral']:.2f} Hz</td>"
            f"<td>{c['ancho_banda_espectral']:.2f} Hz</td>"
            f"<td>{formatear_valor_caracteristica('frecuencia_fundamental', c)}</td>"
            f"<td>{seg['tipo_segmento']}<br><small>{seg['estado']}</small></td>"
            f"</tr>"
        )
    return html + "</table>"


def _seccion_lote(resultados_lote):
    contenido = ("<p>Resultados de la segmentación automática de actividad vocal y extracción "
                 "de características acústicas para las grabaciones configuradas.</p>")

    if not resultados_lote:
        contenido += '<div class="info">No se procesaron archivos por lotes.</div>'

    for item in resultados_lote:
        contenido += f"<h3>Archivo: {item['archivo']}</h3>"

        if not item["exito"]:
            contenido += f'<div class="info"><strong>Error:</strong> {item["error"]}</div>'
            continue

        contenido += _tarjetas([
            ("Frecuencia de muestreo", f"{item['fs']} Hz"),
            ("Canales", item["canales"]),
            ("Bits por muestra", f"{item['bits']} bits"),
            ("Duración total", f"{round(item['duracion'], 3)} s"),
            ("Segmentos detectados", len(item["segmentos"]))
        ])

        if not item["segmentos"]:
            contenido += '<div class="info">No se detectaron segmentos de voz activa en esta grabación.</div>'
            continue

        if item.get("svg_segmentacion"):
            contenido += (
                f'<h4>Forma de onda completa y segmentos de voz detectados '
                f'(S1 - S{len(item["segmentos"])})</h4>'
                f'<div class="grafica">{item["svg_segmentacion"]}</div>'
            )
        if item.get("svg_barras_f0"):
            contenido += (
                '<h4>Comparativa de Frecuencia Fundamental (F0 en Hz) por segmento</h4>'
                f'<div class="grafica">{item["svg_barras_f0"]}</div>'
            )
        contenido += _tabla_segmentos(item["segmentos"])

    return _ventana("lote", "Análisis de Grabaciones Continuas por Lotes", contenido)


def _seccion_referencias(referencias):
    contenido = "<p>Patrones de audio precargados para comparación acústica de vocabulario limitado.</p>"

    if not referencias:
        contenido += """
<div class="info">
<strong>No hay referencias cargadas.</strong>
<p>El sistema incluye el comparador acústico <code>comparar_con_referencias()</code> para
vocabulario limitado, pero no hay grabaciones declaradas en <code>referencias/indice.txt</code>.</p>
</div>
"""
        return _ventana("referencias", "Banco de Referencias de Sílabas", contenido)

    contenido += '<div class="tarjetas">'
    for ref in referencias:
        c = ref.get("caracteristicas", {}) or {}
        contenido += f"""
<div class="tarjeta">
    <h3>Sílaba/Palabra: {ref['silaba']}</h3>
    <p><strong>Voz:</strong> {ref['voz']}</p>
    <p><strong>Archivo:</strong> {ref['archivo']}</p>
    <p>RMS: {round(c.get('rms', 0.0), 4)}</p>
    <p>F0: {formatear_valor_caracteristica('frecuencia_fundamental', c)}</p>
    <p>Centroide: {round(c.get('centroide_espectral', 0.0), 2)} Hz</p>
</div>
"""
    contenido += '</div>'
    return _ventana("referencias", "Banco de Referencias de Sílabas", contenido)


def _seccion_experimento(id_seccion, titulo, descripcion, pares, experimento):
    contenido = (
        f"<p>{descripcion}</p>"
        + _tarjetas(pares)
        + f'<h3>Señal en el dominio del tiempo</h3><div class="grafica">{experimento["senal"]}</div>'
        + f'<h3>Espectro de frecuencia</h3><div class="grafica">{experimento["espectro"]}</div>'
        + "<h3>Frecuencias dominantes</h3>"
        + frecuencias_a_html(experimento["frecuencias"])
    )
    return _ventana(id_seccion, titulo, contenido)


def _seccion_voz(voz):
    contenido = f"""
<h3>Escuchar grabación</h3>
<audio controls preload="metadata">
    <source src="{voz.get('src_audio', '')}" type="audio/wav">
    Tu navegador no puede reproducir este audio.
</audio>
"""
    titulo = f"Análisis de voz real ({voz.get('archivo', '')})"

    if not voz.get("existe", False):
        contenido += f'<div class="info"><strong>No se pudo realizar el análisis.</strong><p>{voz.get("mensaje", "")}</p></div>'
        return _ventana("voz", titulo, contenido)

    if "ventanas" not in voz:
        contenido += f'<div class="info">{voz.get("mensaje", "")}</div>'
        contenido += f'<div class="grafica">{voz.get("svg_tiempo", "")}</div>'
        return _ventana("voz", titulo, contenido)

    contenido += (
        "<p>El archivo de voz fue leído directamente mediante el lector WAV implementado desde cero.</p>"
        + _tarjetas([
            ("Frecuencia de muestreo", f"{voz['fs']} Hz"),
            ("Bits", voz["bits"]),
            ("Canales", voz["canales"]),
            ("Muestras", voz["muestras"]),
            ("Duración", f"{round(voz['duracion'], 3)} s"),
            ("Ventanas", voz["ventanas"])
        ])
        + f'<h3>Forma de onda de la voz</h3><div class="grafica">{voz["svg_tiempo"]}</div>'
        + f"""
<h3>Ventana seleccionada</h3>
<div class="info">
La ventana seleccionada corresponde al segmento con mayor RMS dentro de las primeras ventanas analizadas.<br><br>
<strong>Índice de ventana:</strong> {voz["ventana_seleccionada"]}<br>
<strong>Duración de ventana:</strong> 25 ms<br>
<strong>Desplazamiento:</strong> 10 ms
</div>
<div class="dos_columnas">
<div><h3>RMS</h3><div class="tarjeta">Medida de energía de la señal<strong>{round(voz["rms"], 6)}</strong></div></div>
<div><h3>Zero Crossing Rate</h3><div class="tarjeta">Tasa de cruces por cero<strong>{round(voz["zcr"], 6)}</strong></div></div>
</div>
"""
        + f'<h3>Ventana de voz de 25 ms</h3><div class="grafica">{voz["svg_ventana"]}</div>'
        + f'<h3>Espectro de la voz</h3><div class="grafica">{voz["svg_espectro"]}</div>'
        + "<h3>Frecuencias dominantes</h3>"
        + frecuencias_a_html(voz["frecuencias"])
        + caracteristicas_a_html(voz["caracteristicas"])
    )
    return _ventana("voz", titulo, contenido)


def _tarjeta_coincidencia(coincidencia):
    if not coincidencia:
        return ('<div class="info" style="font-size: 13px; padding: 8px 12px;">'
                'Sin comparación automática (no hay referencias cargadas para contrastar).</div>')

    estado = ("Coincidencia dentro del umbral" if coincidencia.get("aceptada")
              else "Distancia alta (coincidencia débil)")
    return f"""
<div class="tarjetas" style="margin-bottom: 10px;">
    <div class="tarjeta" style="border-left: 5px solid #2878B5; background: #f0f7fc;">
        <span style="font-size: 13px; color: #555;">Sílaba/patrón más cercano ({estado}):</span>
        <strong style="color: #2878B5; font-size: 26px;">{coincidencia['silaba'].upper()}</strong>
        <p style="margin: 5px 0 0 0; font-size: 13px;">
            Voz patrón: <b>{coincidencia['voz']}</b> |
            Distancia acústica: <b>{round(coincidencia['distancia'], 4)}</b>
        </p>
    </div>
</div>
"""


def _seccion_fragmentos(fragmentos_voz):
    contenido = (
        "<p>Esta sección analiza intervalos marcados manualmente en "
        "<code>config.FRAGMENTOS_MANUALES</code>. Las etiquetas las escribió el equipo; "
        "el programa no reconoce esas palabras. Si hay referencias cargadas, se calcula la "
        "distancia acústica al patrón más cercano.</p>"
    )

    if not fragmentos_voz.get("existe", False):
        contenido += f'<div class="info">No se pudieron leer los fragmentos: {fragmentos_voz.get("mensaje", "")}</div>'
        return _ventana("fragmentos", "Análisis de fragmentos marcados manualmente", contenido)

    contenido += _tarjetas([
        ("Duración total", f"{round(fragmentos_voz['duracion_total'], 3)} s"),
        ("Frecuencia de muestreo", f"{fragmentos_voz['fs']} Hz")
    ])

    if not fragmentos_voz.get("fragmentos"):
        contenido += '<div class="info">No se configuraron fragmentos.</div>'

    for frag in fragmentos_voz.get("fragmentos", []):
        contenido += f"<h3>Fragmento: {frag['etiqueta']}</h3>"
        if "error" in frag:
            contenido += f'<div class="info">{frag["error"]}</div>'
            continue
        contenido += _tarjeta_coincidencia(frag.get("coincidencia"))
        contenido += (
            f"<p>Tiempo: {round(frag['inicio'], 3)} s a {round(frag['fin'], 3)} s | "
            f"Duración: {round(frag['duracion'], 3)} s | Muestras: {frag['muestras']}</p>"
            f'<div class="grafica">{frag["svg"]}</div>'
            + caracteristicas_a_html(frag["caracteristicas"])
        )

    return _ventana("fragmentos", "Análisis de fragmentos marcados manualmente", contenido)


def _seccion_abecedario(ondas):
    contenido = """
<p>Cada letra tiene una frecuencia de ejemplo y se representa con tres amplitudes.</p>
<div class="info">
Demostración sintética: las frecuencias de las letras son valores asignados para este
experimento (200 + 20·i Hz) y no corresponden a la voz real. Las amplitudes de 0.3, 0.6 y 1.0
representan intensidad baja, media y fuerte.
</div>
<h3>Comparación general del abecedario</h3>
<div class="cuadricula_letras">
"""
    for dato in ondas:
        contenido += (
            f'<div class="tarjeta"><h3>Letra {dato["letra"]}</h3>'
            f'<p>Frecuencia: {dato["frecuencia"]} Hz</p><div class="grafica">'
            + crear_svg_tres_intensidades(dato["letra"], dato["frecuencia"],
                                          ancho=500, alto=190, cantidad_muestras=100)
            + '</div></div>'
        )
    contenido += '</div><h3>Gráficas individuales</h3>'

    for dato in ondas:
        contenido += (
            f'<div class="tarjeta"><h3>Letra {dato["letra"]}</h3>'
            f'<p>Frecuencia asignada: {dato["frecuencia"]} Hz</p>'
            f'<div class="grafica">{dato["svg"]}</div></div>'
        )

    return _ventana("abecedario", "Ondas matemáticas del abecedario (demostración)", contenido)


# --------------------------------------------------------------
# Documento completo
# --------------------------------------------------------------


def generar_html(
        experimento1,
        experimento2,
        experimento3,
        voz,
        fragmentos_voz,
        ondas_abecedario,
        referencias=None,
        resultados_lote=None,
        nombre_archivo="resultado.html"):

    botones = "".join(
        f"<button onclick=\"mostrarVentana('{id_s}')\">{texto}</button>"
        for id_s, texto in SECCIONES_MENU
    )

    secciones = (
        _seccion_inicio()
        + _seccion_lote(resultados_lote or [])
        + _seccion_referencias(referencias or [])
        + _seccion_experimento(
            "seno", "Experimento 1: Onda seno pura",
            "Se genera una señal sinusoidal de 250 Hz y se analiza su contenido frecuencial "
            "mediante la Transformada Discreta de Fourier.",
            [("Frecuencia", "250 Hz"), ("Duración", "0.05 s"),
             ("Frecuencia de muestreo", "16000 Hz"), ("Muestras", "800")],
            experimento1)
        + _seccion_experimento(
            "senocoseno", "Experimento 2: Seno + Coseno",
            "La señal está formada por una componente seno de 250 Hz y una componente "
            "coseno de 500 Hz con amplitud de 0.5.",
            [("Componente 1", "250 Hz"), ("Componente 2", "500 Hz"), ("Amplitud coseno", "0.5")],
            experimento2)
        + _seccion_experimento(
            "compleja", "Experimento 3: Señal compleja",
            "La señal está formada por múltiples componentes sinusoidales con diferentes "
            "frecuencias y amplitudes.",
            [("Componentes", "6"), ("Frecuencia mínima", "125 Hz"), ("Frecuencia máxima", "2500 Hz")],
            experimento3)
        + _seccion_voz(voz)
        + _seccion_fragmentos(fragmentos_voz)
        + _seccion_abecedario(ondas_abecedario)
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sistema de Análisis Digital de Voz</title>
<style>{ESTILOS_CSS}</style>
<script>{SCRIPT_JS}</script>
</head>
<body>
<div class="encabezado">
<h1>SISTEMA DE ANÁLISIS DIGITAL DE VOZ</h1>
<p>Procesamiento digital de señales implementado desde cero</p>
</div>
<div class="menu">{botones}</div>
<div class="contenedor">
{secciones}
</div>
<div class="pie">Sistema de Análisis Digital de Voz desde Cero</div>
<script>mostrarVentana('inicio');</script>
</body>
</html>
"""

    ruta_html = ruta_salida(nombre_archivo)
    guardar_texto(ruta_html, html)
    return ruta_html
