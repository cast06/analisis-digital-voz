# ==============================================================
# DISENO COMUN DE LAS PAGINAS DEL SERVIDOR WEB (guinda y blanco)
# ==============================================================
# Solo arma HTML: barra de navegacion, encabezado, estilos de
# formularios y piezas reutilizables. No hace ningun calculo.
# ==============================================================

from visual.html import ESTILOS_CSS
from vinculacion.panel import escapar_html

ENLACES = [
    ("/", "Inicio", "inicio"),
    ("/orientacion", "Orientación", "orientacion"),
    ("/seguimiento", "Seguimiento", "seguimiento"),
    ("/panel", "Profesionales", "panel"),
    ("/reportes", "Resultados", "reportes"),
]

ESTILOS_WEB = """
.navegacion { background: white; border-bottom: 1px solid var(--borde); position: sticky; top: 0; z-index: 1000;
              box-shadow: 0 2px 12px rgba(74, 16, 48, .06); }
.navegacion .interior { max-width: 1200px; margin: 0 auto; display: flex; align-items: center;
                        justify-content: space-between; padding: 12px 3%; gap: 12px; flex-wrap: wrap; }
.marca { display: flex; align-items: center; gap: 10px; text-decoration: none; color: var(--primario); }
.marca .logo { width: 38px; height: 38px; border-radius: 10px; background: var(--primario); color: white;
               display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 18px; }
.marca b { display: block; font-size: 16px; line-height: 1.1; }
.marca small { color: var(--suave); font-size: 12px; }
.navegacion nav a { color: var(--texto); text-decoration: none; padding: 8px 14px; border-radius: 999px;
                    font-size: 14px; font-weight: 500; }
.navegacion nav a:hover { background: var(--primario-claro); color: var(--primario); }
.navegacion nav a.activo { background: var(--primario); color: white; }
.portada { background: linear-gradient(135deg, #3d0d27 0%, #6c1d45 55%, #8a2a59 100%); color: white;
           padding: 64px 3% 72px; border-bottom: 5px solid var(--acento); }
.portada .interior { max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 3fr 2fr;
                     gap: 40px; align-items: center; }
.portada h1 { font-size: 40px; line-height: 1.15; margin: 0 0 16px; }
.portada p { font-size: 18px; opacity: .9; margin: 0 0 26px; }
.portada .etiqueta-sup { display: inline-block; background: rgba(255,255,255,.14); padding: 6px 14px;
                         border-radius: 999px; font-size: 13px; margin-bottom: 18px; letter-spacing: .5px; }
.portada .boton { background: white; color: var(--primario); margin: 0 10px 10px 0; }
.portada .boton.secundario { background: transparent; color: white; border: 2px solid rgba(255,255,255,.7); }
.portada .tarjeta-flotante { background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.2);
                             border-radius: 18px; padding: 24px; backdrop-filter: blur(4px); }
.portada .tarjeta-flotante div { display: flex; gap: 12px; align-items: flex-start; margin: 12px 0; }
.portada .tarjeta-flotante span { background: var(--acento); color: white; border-radius: 50%; min-width: 28px;
                                  height: 28px; display: flex; align-items: center; justify-content: center;
                                  font-weight: 700; font-size: 14px; }
.cuadricula { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 18px; }
.enlace { display: block; text-decoration: none; color: var(--texto); background: white;
          border: 1px solid var(--borde); border-radius: 14px; padding: 20px; box-shadow: var(--sombra);
          transition: transform .15s, box-shadow .15s; border-top: 4px solid var(--primario); }
.enlace:hover { transform: translateY(-3px); box-shadow: 0 10px 26px rgba(74, 16, 48, .14); }
.enlace h3 { margin: 0 0 6px; color: var(--primario); font-size: 17px; }
.enlace p { margin: 0; color: var(--suave); font-size: 14px; }
.enlace.inactivo { opacity: .55; border-top-color: #c9bcc2; }
.formulario label { display: block; font-weight: 600; margin: 18px 0 6px; }
.formulario .ayuda { font-weight: 400; color: var(--suave); font-size: 13px; }
.formulario input[type=text], .formulario input[type=number], .formulario input[type=date],
.formulario select, .formulario textarea {
  width: 100%; padding: 12px 14px; border: 1.5px solid var(--borde); border-radius: 10px; font-size: 15px;
  font-family: inherit; background: white; }
.formulario textarea { min-height: 140px; resize: vertical; }
.formulario input:focus, .formulario select:focus, .formulario textarea:focus {
  outline: none; border-color: var(--primario); box-shadow: 0 0 0 3px var(--primario-claro); }
.opciones { display: flex; flex-wrap: wrap; gap: 10px; }
.opciones label { font-weight: 400; margin: 0; display: flex; align-items: center; gap: 8px;
                  border: 1.5px solid var(--borde); padding: 10px 14px; border-radius: 10px; cursor: pointer; }
.opciones label:has(input:checked) { border-color: var(--primario); background: var(--primario-claro); }
.dos { display: grid; grid-template-columns: 1fr 1fr; gap: 0 20px; }
.error { background: #fbeaec; color: var(--error); border-left: 4px solid var(--error); padding: 12px 16px;
         border-radius: 0 10px 10px 0; margin: 14px 0; }
.exito { background: #e7f5ec; color: var(--ok); border-left: 4px solid var(--ok); padding: 12px 16px;
         border-radius: 0 10px 10px 0; margin: 14px 0; }
.grabadora { border: 2px dashed var(--borde); border-radius: 14px; padding: 18px; margin: 10px 0;
             display: flex; align-items: center; gap: 14px; flex-wrap: wrap; background: #fcfafb; }
.grabadora .estado { color: var(--suave); font-size: 14px; flex: 1; min-width: 200px; }
.grabando { animation: latido 1s infinite; background: #a8323a !important; }
@keyframes latido { 50% { box-shadow: 0 0 0 8px rgba(168, 50, 58, .2); } }
.tema { display: flex; align-items: center; gap: 12px; margin: 8px 0; }
.tema .nombre { width: 260px; }
.tema .fondo { flex: 1; background: #f0e6ea; border-radius: 999px; height: 12px; overflow: hidden; }
.tema .relleno { background: linear-gradient(90deg, #6c1d45, #b0577f); height: 100%; }
.tema .valor { width: 50px; text-align: right; color: var(--suave); }
.paso { display: inline-block; background: var(--primario-claro); color: var(--primario); font-weight: 700;
        border-radius: 999px; padding: 4px 14px; font-size: 13px; margin-bottom: 8px; }
.recursos { background: #fbeaec; border: 2px solid var(--error); border-radius: 14px; padding: 22px; }
.recursos li { font-size: 18px; margin: 8px 0; }
.cambio { padding: 10px 14px; border-radius: 10px; margin: 8px 0; font-size: 14px; background: #f6f1f3; }
.cambio.marcado { background: #fdf3e6; border-left: 4px solid var(--alerta); }
.graficas { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 850px) { .graficas { grid-template-columns: 1fr; } }
@media (max-width: 850px) { .portada .interior, .dos { grid-template-columns: 1fr; } .portada h1 { font-size: 30px; } }
"""


def navegacion(activo=""):
    enlaces = "".join(f'<a href="{href}" class="{"activo" if clave == activo else ""}">{texto}</a>'
                      for href, texto, clave in ENLACES)
    return (f'<div class="navegacion"><div class="interior">'
            f'<a class="marca" href="/"><span class="logo">O</span><span><b>Orientación Psicológica</b>'
            f'<small>Prototipo académico · ESCOM-IPN</small></span></a>'
            f'<nav>{enlaces}</nav></div></div>')


def estilos():
    return ESTILOS_CSS + " .ventana { display: block; } " + ESTILOS_WEB


def pagina(titulo, contenido, activo="", subtitulo="", portada=""):
    """Pagina completa con navegacion, encabezado (o portada) y pie."""
    encabezado = portada or (f'<div class="encabezado"><h1>{escapar_html(titulo)}</h1>'
                             + (f'<p>{escapar_html(subtitulo)}</p>' if subtitulo else "") + '</div>')
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escapar_html(titulo)} · Orientación Psicológica</title>
<style>{estilos()}</style></head>
<body>
{navegacion(activo)}
{encabezado}
<div class="contenedor">{contenido}</div>
<div class="pie">Sistema Inteligente Multimodal de Acceso, Orientación y Vinculación Psicológica ·
Temas Selectos de Aprendizaje Profundo · ESCOM-IPN<br>
Orienta, no diagnostica. En una emergencia llama al 911 o a la Línea de la Vida 800 911 2000.</div>
</body></html>"""


def tarjeta(titulo, contenido):
    return f'<div class="ventana"><h2>{titulo}</h2>{contenido}</div>'


def mensaje_error(texto):
    return f'<div class="error">{escapar_html(texto)}</div>' if texto else ""


def opciones_radio(nombre, opciones, elegida=""):
    """opciones: lista de (valor, texto)."""
    return '<div class="opciones">' + "".join(
        f'<label><input type="radio" name="{nombre}" value="{escapar_html(v)}" '
        f'{"checked" if v == elegida else ""} required> {t}</label>' for v, t in opciones) + '</div>'


def opciones_casilla(nombre, opciones, elegidas=()):
    return '<div class="opciones">' + "".join(
        f'<label><input type="checkbox" name="{nombre}" value="{escapar_html(v)}" '
        f'{"checked" if v in elegidas else ""}> {t}</label>' for v, t in opciones) + '</div>'


def lista_seleccion(nombre, opciones, elegida="", vacia=None):
    html = f'<select name="{nombre}">'
    if vacia is not None:
        html += f'<option value="">{vacia}</option>'
    for valor, texto in opciones:
        html += f'<option value="{escapar_html(valor)}" {"selected" if valor == elegida else ""}>{escapar_html(texto)}</option>'
    return html + "</select>"
