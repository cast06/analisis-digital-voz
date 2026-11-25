# ==============================================================
# PAGINA DE INICIO: salidas/inicio.html
# ==============================================================
# Reune en una sola pagina los reportes de los modelos y los
# paneles de los profesionales. Sin el modulo os no se puede
# listar la carpeta salidas/, asi que se revisa cada archivo
# conocido con existe_archivo().
# ==============================================================

import config
from nucleo.archivos import existe_archivo, guardar_texto
from visual.html import ESTILOS_CSS

REPORTES = [
    ("reporte_emociones.html", "Emociones en la voz",
     "Red neuronal con 11 variables acústicas · MESD · 4 emociones", "python entrenar_emociones.py"),
    ("reporte_palabras.html", "Palabras aisladas",
     "MFCC + FFT + red neuronal · 24 palabras del corpus A", "python entrenar_palabras.py"),
    ("reporte_texto.html", "Motivos de consulta y prioridad",
     "Naive Bayes y red neuronal sobre TF-IDF · módulo de seguridad", "python entrenar_texto.py"),
    ("reporte_vinculacion.html", "Extracción y matching",
     "Exactitud por campo · precision@3 contra el orden del equipo", "python evaluar_vinculacion.py"),
    ("resultado.html", "Análisis de señales",
     "Fourier, ventanas, detección de voz y experimentos sintéticos", "python analisis_senales.py"),
]

ESTILOS_INICIO = """
.cuadricula { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 18px; }
.enlace { display: block; text-decoration: none; color: var(--texto); background: white;
          border: 1px solid var(--borde); border-radius: 14px; padding: 20px; box-shadow: var(--sombra);
          transition: transform 0.15s, box-shadow 0.15s; border-top: 4px solid var(--primario); }
.enlace:hover { transform: translateY(-3px); box-shadow: 0 10px 26px rgba(20, 40, 60, 0.14); }
.enlace h3 { margin: 0 0 6px; color: var(--primario); font-size: 17px; }
.enlace p { margin: 0; color: var(--suave); font-size: 14px; }
.enlace.inactivo { opacity: 0.55; border-top-color: #b8c2cc; cursor: default; }
.enlace.inactivo:hover { transform: none; box-shadow: var(--sombra); }
.enlace .meta { margin-top: 10px; font-size: 12px; color: var(--suave); }
.flujo { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; margin: 6px 0 4px; }
.flujo span { background: var(--primario-claro); color: var(--primario); padding: 8px 14px;
              border-radius: 999px; font-size: 14px; font-weight: 600; }
.flujo b { color: var(--suave); }
"""


def escapar(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _tarjeta(href, titulo, descripcion, meta, activo):
    if activo:
        return (f'<a class="enlace" href="{href}"><h3>{titulo}</h3><p>{descripcion}</p>'
                f'<div class="meta">{meta}</div></a>')
    return (f'<div class="enlace inactivo"><h3>{titulo}</h3><p>{descripcion}</p>'
            f'<div class="meta">{meta}</div></div>')


def generar_inicio():
    """Escribe salidas/inicio.html y devuelve su ruta."""
    from vinculacion.registro import cargar_psicologos   # aqui para evitar importacion circular

    reportes = "".join(
        _tarjeta(archivo, titulo, descripcion,
                 "Abrir reporte →" if existe_archivo(config.ruta_salida(archivo))
                 else f"Aún no generado: <code>{comando}</code>",
                 existe_archivo(config.ruta_salida(archivo)))
        for archivo, titulo, descripcion, comando in REPORTES)

    paneles = ""
    for p in cargar_psicologos():
        archivo = f"panel_{p['id']}.html"
        existe = existe_archivo(config.ruta_salida(archivo))
        costo = "Gratuito" if p["costo"] == 0 else f"${p['costo']}"
        areas = ", ".join(config.CATEGORIAS_MOTIVO.get(t, t)
                          for t, w in sorted(p["areas"].items(), key=lambda x: -x[1])[:2])
        paneles += _tarjeta(archivo, f"{p['nombre']}", f"{areas} · {costo}",
                            f"{p['id']} · " + ("Ver panel →" if existe else
                                                "Panel aún no generado (opción 7 del menú)"),
                            existe)

    from vinculacion.almacen import leer_registros
    recomendaciones = ""
    for r in leer_registros(config.REGISTRO_PACIENTES):
        archivo = f"recomendacion_{r['id']}.html"
        if existe_archivo(config.ruta_salida(archivo)):
            recomendaciones += _tarjeta(archivo, escapar(r.get("alias", r["id"])),
                                        config.CATEGORIAS_MOTIVO.get(r.get("motivo_principal", ""), ""),
                                        f"{r['id']} · {r.get('alcaldia') or 'sin alcaldía'} · Ver mapa →", True)
    seccion_recomendaciones = (f'<div class="ventana"><h2>Recomendaciones con mapa</h2>'
                               f'<div class="cuadricula">{recomendaciones}</div></div>'
                               if recomendaciones else "")

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sistema de Orientación y Vinculación Psicológica</title>
<style>{ESTILOS_CSS} .ventana {{ display: block; }} {ESTILOS_INICIO}</style></head>
<body>
<div class="encabezado"><h1>Sistema Inteligente de Orientación y Vinculación Psicológica</h1>
<p>Prototipo académico · Temas Selectos de Aprendizaje Profundo · ESCOM-IPN · algoritmos propios, sin librerías</p></div>
<div class="contenedor">
<div class="ventana">
<h2>Cómo funciona</h2>
<div class="flujo"><span>Consentimiento</span><b>→</b><span>Relato por texto o voz</span><b>→</b>
<span>Revisión de seguridad</span><b>→</b><span>Perfil preliminar</span><b>→</b>
<span>Profesionales compatibles</span><b>→</b><span>Solicitud y resumen</span><b>→</b><span>Seguimiento</span></div>
<div class="aviso">El sistema orienta; no diagnostica ni atiende emergencias. En caso de peligro:
911 o Línea de la Vida 800 911 2000 (24 horas).</div>
</div>
<div class="ventana"><h2>Reportes de los modelos</h2><div class="cuadricula">{reportes}</div></div>
{seccion_recomendaciones}
<div class="ventana"><h2>Paneles de los profesionales</h2>
<p style="color:var(--suave)">Perfiles ficticios para el prototipo.</p>
<div class="cuadricula">{paneles}</div></div>
</div>
<div class="pie">Página generada por <code>python main.py</code></div>
</body></html>
"""
    ruta = config.ruta_salida("inicio.html")
    guardar_texto(ruta, html)
    return ruta
