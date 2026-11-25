# ==============================================================
# PANEL DEL PSICOLOGO: PAGINA HTML GENERADA POR EL PROGRAMA
# ==============================================================
#
# Sin librerias no hay servidor web, asi que el panel tiene dos
# partes:
#   - acciones (aceptar/rechazar) desde el menu en consola
#     (main.py, opcion 5)
#   - una pagina HTML estatica que se regenera despues de cada
#     accion: salidas/panel_<ID>.html
#
# La pagina solo muestra informacion AUTORIZADA por el paciente:
#   - el resumen, si el consentimiento sigue vigente
#   - el seguimiento, solo de solicitudes aceptadas y solo los
#     registros que el paciente marco como compartidos
# ==============================================================

import config
from nucleo.archivos import guardar_texto
from visual.html import ESTILOS_CSS
from visual.svg import crear_svg_curvas
from vinculacion.registro import cargar_psicologos, cargar_paciente
from vinculacion.solicitudes import solicitudes_de, resumen_autorizado, AVISO_RESUMEN
from vinculacion.seguimiento import analizar_paciente, VARIABLES
from visual.portal import generar_inicio

COLORES_ESTADO = {"pendiente": "#b26a00", "aceptada": "#1b7a3a", "rechazada": "#8a1c1c"}


def escapar_html(texto):
    """Evita que el texto escrito por un usuario se interprete como HTML."""
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _seccion_seguimiento(id_paciente):
    datos = analizar_paciente(id_paciente, solo_compartidos=True)
    if not datos["registros"]:
        return "<p>El paciente todavía no ha compartido registros de seguimiento.</p>"
    html = '<div class="graficas">'
    for variable, (nombre, minimo, maximo, _) in VARIABLES.items():
        if variable == "sueno":   # 24 h aplana la grafica; se usa 12 h salvo valores mayores
            maximo = max(12.0, max(datos["series"][variable]))
        svg = crear_svg_curvas([(nombre, datos["series"][variable], "#6c1d45")],
                               f"{nombre} por sesión", "", etiqueta_y=nombre,
                               ancho=560, alto=280, etiqueta_x="Sesión",
                               y_min=minimo, y_max=maximo, leyenda=False)
        if svg:
            html += f'<div class="grafica">{svg}</div>'
    html += "</div>"
    for resultado in datos["analisis"]:
        clase = "cambio marcado" if resultado["marcado"] else "cambio"
        marca = "⚠ " if resultado["marcado"] else ""
        html += f'<div class="{clase}">{marca}{escapar_html(resultado["mensaje"])}</div>'

    filas = "".join(
        f"<tr><td>{escapar_html(r['fecha'])}</td><td>{escapar_html(r['animo'])}</td>"
        f"<td>{escapar_html(r['sueno'])}</td><td>{escapar_html(r.get('acontecimiento', ''))}</td></tr>"
        for r in datos["registros"])
    html += ('<table class="tabla"><tr><th>Fecha</th><th>Ánimo</th><th>Sueño (h)</th>'
             f'<th>Acontecimiento</th></tr>{filas}</table>')
    return html


def _resumen_a_html(texto):
    """
    Convierte el resumen de texto en bloques: las lineas en mayusculas
    son titulos de seccion y las lineas con sangria son datos.
    """
    lineas = texto.splitlines()
    html, abierta = "", False
    for linea in lineas[2:]:                      # se omiten titulo y aviso (ya se muestran)
        if not linea.strip():
            continue
        if not linea.startswith(" ") and ": " not in linea:
            if abierta:
                html += "</ul></div>"
            html += f'<div class="bloque"><h4>{escapar_html(linea.strip().capitalize())}</h4><ul>'
            abierta = True
        elif linea.startswith(" "):
            clave, separador, valor = linea.strip().partition(": ")
            contenido = (f"<span>{escapar_html(clave)}</span>{escapar_html(valor)}"
                         if separador else escapar_html(linea.strip()))
            html += f"<li>{contenido}</li>"
        else:
            html += f'<p class="paciente">{escapar_html(linea.strip())}</p>'
    if abierta:
        html += "</ul></div>"
    return f'<div class="resumen">{html}</div>'


ESTILOS_PANEL = """
.perfil { display: grid; grid-template-columns: 2fr 3fr; gap: 24px; align-items: start; }
.perfil h2 { border: none; margin-bottom: 4px; padding: 0; }
.perfil .sub { color: var(--suave); margin: 0 0 14px; }
.chips span { display: inline-block; background: var(--primario-claro); color: var(--primario);
              border-radius: 999px; padding: 4px 12px; margin: 3px 4px 3px 0; font-size: 13px; }
.barra { display: flex; align-items: center; gap: 10px; margin: 7px 0; font-size: 14px; }
.barra .nombre { width: 210px; color: var(--suave); }
.barra .fondo { flex: 1; background: #f0e6ea; border-radius: 999px; height: 10px; overflow: hidden; }
.barra .relleno { background: linear-gradient(90deg, #6c1d45, #b0577f); height: 100%; }
.solicitud h2 { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.compat { font-size: 15px; color: var(--suave); font-weight: 400; }
.compat strong { color: var(--primario); font-size: 20px; }
.resumen { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 10px; }
.resumen .paciente { grid-column: 1 / -1; margin: 0; font-weight: 600; }
.bloque { border: 1px solid var(--borde); border-radius: 12px; padding: 14px 18px; background: #fcfafb; }
.bloque h4 { margin: 0 0 8px; color: var(--primario); font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; }
.bloque ul { list-style: none; padding: 0; margin: 0; }
.bloque li { padding: 5px 0; border-bottom: 1px dashed var(--borde); font-size: 14px; }
.bloque li:last-child { border-bottom: none; }
.bloque li span { display: block; color: var(--suave); font-size: 12px; }
.cambio { padding: 10px 14px; border-radius: 10px; margin: 8px 0; font-size: 14px; background: #f3f6f9; }
.cambio.marcado { background: #fdf3e6; border-left: 4px solid var(--alerta); }
.acciones { margin-top: 14px; }
.graficas { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 800px) { .perfil, .resumen, .graficas { grid-template-columns: 1fr; } }
"""


def _tarjeta_perfil(psicologo):
    nombres = config.CATEGORIAS_MOTIVO
    barras = "".join(
        f'<div class="barra"><div class="nombre">{escapar_html(nombres.get(tema, tema))}</div>'
        f'<div class="fondo"><div class="relleno" style="width:{peso * 100:.0f}%"></div></div></div>'
        for tema, peso in sorted(psicologo["areas"].items(), key=lambda par: -par[1]))
    costo = "Gratuito" if psicologo["costo"] == 0 else f"${psicologo['costo']} por sesión"
    chips = "".join(f"<span>{escapar_html(x)}</span>" for x in
                    [costo] + [("En línea" if m == "linea" else "Presencial") for m in psicologo["modalidad"]]
                    + [h.replace("manana", "mañana").capitalize() for h in psicologo["horarios"]]
                    + [i.replace("espanol", "español").capitalize() for i in psicologo["idiomas"]])
    return (f'<div class="ventana perfil"><div><h2>{escapar_html(psicologo["nombre"])}</h2>'
            f'<p class="sub">{escapar_html(psicologo["formacion"])} · enfoque '
            f'{escapar_html(psicologo["enfoque"])} · {escapar_html(psicologo["poblacion"])}</p>'
            f'<div class="chips">{chips}</div>'
            f'<p class="sub" style="margin-top:14px">Cédula: {escapar_html(psicologo["cedula"])}</p></div>'
            f'<div><h3 style="margin-top:0">Áreas de experiencia</h3>{barras}</div></div>')


def html_panel(id_psicologo, navegacion="", web=False):
    """
    Pagina completa del panel. Con web=True las solicitudes pendientes
    tienen botones para aceptar o rechazar (los atiende servidor.py).
    """
    psicologo = next((p for p in cargar_psicologos() if p["id"] == id_psicologo), None)
    if psicologo is None:
        raise ValueError(f"No existe el psicólogo {id_psicologo}.")
    solicitudes = solicitudes_de(id_psicologo)

    conteo = {e: sum(1 for s in solicitudes if s["estado"] == e) for e in COLORES_ESTADO}
    tarjetas = "".join(
        f'<div class="tarjeta" style="border-top-color:{COLORES_ESTADO[e]}">{e.capitalize()}s'
        f'<strong>{n}</strong></div>' for e, n in conteo.items())

    bloques = ""
    for s in solicitudes:
        paciente = cargar_paciente(s["paciente"])
        alias = paciente["alias"] if paciente else s["paciente"]
        bloques += (f'<div class="ventana solicitud"><h2><span>{escapar_html(alias)} '
                    f'<span class="etiqueta {s["estado"]}">{s["estado"]}</span></span>'
                    f'<span class="compat">Solicitud {escapar_html(s["id"])} · compatibilidad '
                    f'<strong>{float(s["compatibilidad"]) * 100:.0f} %</strong></span></h2>')
        resumen = resumen_autorizado(s)
        if resumen is None:
            bloques += ('<div class="aviso">El paciente no autorizó compartir su resumen '
                        '(o retiró el permiso). Solo se muestra la solicitud.</div>')
        else:
            bloques += _resumen_a_html(resumen)
        if s["estado"] == "aceptada":
            bloques += "<h3>Seguimiento entre sesiones</h3>" + _seccion_seguimiento(s["paciente"])
        elif s["estado"] == "pendiente" and web:
            bloques += (f'<form method="post" action="/panel/{escapar_html(id_psicologo)}/estado" '
                        f'class="acciones"><input type="hidden" name="solicitud" value="{escapar_html(s["id"])}">'
                        f'<button class="boton" name="estado" value="aceptada">Aceptar</button> '
                        f'<button class="boton secundario" name="estado" value="rechazada">Rechazar</button></form>')
        elif s["estado"] == "pendiente":
            bloques += ('<div class="info">Para aceptar o rechazar usa el menú: '
                        '<code>python main.py</code> → opción 5, o la página web '
                        '(<code>python servidor.py</code>).</div>')
        bloques += "</div>"
    if not solicitudes:
        bloques = '<div class="ventana"><p>Todavía no hay solicitudes para este profesional.</p></div>'

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Panel - {escapar_html(psicologo['nombre'])}</title>
<style>{ESTILOS_CSS} .ventana {{ display: block; }} {ESTILOS_PANEL}</style></head>
<body>
{navegacion}
<div class="encabezado"><h1>Panel del profesional</h1>
<p>Sistema de orientación y vinculación psicológica · prototipo académico</p></div>
<div class="contenedor">
<p><a href="{'/panel' if web else 'inicio.html'}">← {'Otros profesionales' if web else 'Volver al inicio'}</a></p>
{_tarjeta_perfil(psicologo)}
<div class="info">{AVISO_RESUMEN} Las decisiones clínicas son responsabilidad del profesional.</div>
<div class="tarjetas">{tarjetas}</div>
{bloques}
</div>
<div class="pie">Página generada por el programa · se actualiza cada vez que se usa el panel</div>
</body></html>
"""
    return html


def generar_panel_html(id_psicologo):
    """Escribe salidas/panel_<ID>.html y devuelve su ruta."""
    ruta = config.ruta_salida(f"panel_{id_psicologo}.html")
    guardar_texto(ruta, html_panel(id_psicologo))
    generar_inicio()
    return ruta
