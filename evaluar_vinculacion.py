# ==============================================================
# EVALUACION DE LA EXTRACCION Y DEL MATCHING
# ==============================================================
#
# Ejecutar desde la carpeta del proyecto (o con la opcion 8 de main.py):
#     python evaluar_vinculacion.py
#
# Genera:
#   salidas/reporte_vinculacion.txt / .html   resultados
#   salidas/hoja_anotacion_matching.html      hoja para que el equipo
#       ordene a los psicologos SIN ver lo que recomienda el programa
#
# La evaluacion del matching solo se calcula cuando hay anotaciones
# en corpus/evaluacion_matching.txt. El programa no inventa el orden
# "correcto": lo deben dar personas.
# ==============================================================

import config
from nucleo.archivos import unir_ruta, guardar_texto
from visual.html import ESTILOS_CSS
from vinculacion.registro import cargar_psicologos
from vinculacion.evaluacion import (
    leer_casos_extraccion, evaluar_extraccion, leer_casos_matching, evaluar_matching
)
from vinculacion.panel import escapar_html

CASOS_EXTRACCION = unir_ruta(config.DIRECTORIO_CORPUS, "extraccion_prueba.txt")
CASOS_MATCHING = unir_ruta(config.DIRECTORIO_CORPUS, "evaluacion_matching.txt")


def _tabla(encabezados, filas):
    html = '<table class="tabla"><tr>' + "".join(f"<th>{h}</th>" for h in encabezados) + "</tr>"
    for fila in filas:
        html += "<tr>" + "".join(f"<td>{escapar_html(c)}</td>" for c in fila) + "</tr>"
    return html + "</table>"


def _tarjetas(pares):
    return '<div class="tarjetas">' + "".join(
        f'<div class="tarjeta">{e}<strong>{v}</strong></div>' for e, v in pares) + "</div>"


def generar_hoja_anotacion(casos, psicologos):
    """Pagina con los casos y los perfiles, sin resultados del algoritmo."""
    nombres = config.CATEGORIAS_MOTIVO
    filas_psi = []
    for p in psicologos:
        areas = ", ".join(f"{nombres[t]} ({w:g})" for t, w in sorted(p["areas"].items(), key=lambda x: -x[1]))
        filas_psi.append([p["id"], p["nombre"], areas, "Gratuito" if p["costo"] == 0 else f"${p['costo']}",
                          ", ".join(p["modalidad"]), ", ".join(p["horarios"]), ", ".join(p["idiomas"]),
                          "sí" if p["acepta_pacientes"] else "no"])
    bloques = ""
    for c in casos:
        pac = c["paciente"]
        temas = ", ".join(f"{nombres[t]} ({v:g})" for t, v in zip(nombres, pac["probabilidades"]) if v > 0)
        bloques += (f'<div class="ventana"><h2>{c["id"]}</h2><p>{escapar_html(c["descripcion"])}</p>'
                    f'<p><b>Temas:</b> {escapar_html(temas)}<br><b>Modalidad:</b> {pac["modalidad"]} · '
                    f'<b>Horario:</b> {pac["horario"]} · <b>Presupuesto:</b> ${pac["costo_maximo"]} · '
                    f'<b>Idioma:</b> {pac["idioma"]}</p>'
                    f'<p>Tus 3 opciones en orden: ______ , ______ , ______</p></div>')
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hoja de anotación del matching</title>
<style>{ESTILOS_CSS} .ventana {{ display: block; }}</style></head><body>
<div class="encabezado"><h1>Hoja de anotación del matching</h1>
<p>Ordena los 3 psicólogos más adecuados para cada caso, sin ver la recomendación del programa</p></div>
<div class="contenedor">
<div class="aviso">Instrucciones: cada integrante trabaja por separado. Anota tus respuestas en
<code>corpus/evaluacion_matching.txt</code>, en tu línea <code>orden_...</code>, con 3 IDs separados
por coma (por ejemplo <code>PS05, PS15, PS13</code>). Después corre <code>python evaluar_vinculacion.py</code>.</div>
<div class="ventana"><h2>Profesionales (ficticios)</h2>
{_tabla(["ID", "Nombre", "Áreas (experiencia 0-1)", "Costo", "Modalidad", "Horarios", "Idiomas", "Acepta"], filas_psi)}
</div>
{bloques}
</div></body></html>"""
    ruta = config.ruta_salida("hoja_anotacion_matching.html")
    guardar_texto(ruta, html)
    return ruta


def main():
    print("=" * 60)
    print("EVALUACIÓN DE EXTRACCIÓN Y MATCHING")
    print("=" * 60)
    texto = ["=" * 60, "REPORTE - EVALUACIÓN DE EXTRACCIÓN Y MATCHING", "=" * 60, ""]
    secciones = ""

    # ---------- A) Extraccion ----------
    casos_e = leer_casos_extraccion(CASOS_EXTRACCION)
    r = evaluar_extraccion(casos_e)
    d, c = r["duracion"], r["contextos"]
    texto += [f"EXTRACCIÓN ({r['n']} frases etiquetadas)",
              f"Duración - detección: precision {d['precision']:.3f}, recall {d['recall']:.3f}, F1 {d['f1']:.3f}",
              f"Duración - exactitud del valor: {d['exactitud_valor']:.3f} ({d['casos_valor']} casos con días)",
              f"Duración - exactitud del campo: {d['exactitud_campo']:.3f}",
              f"Contextos - micro: precision {c['micro']['precision']:.3f}, recall {c['micro']['recall']:.3f}, "
              f"F1 {c['micro']['f1']:.3f}",
              f"Contextos - exactitud de conjunto: {c['exactitud_conjunto']:.3f}", ""]
    texto += ["Por contexto:"] + [f"  {m['contexto']:<10} P {m['precision']:.3f}  R {m['recall']:.3f}  "
                                   f"F1 {m['f1']:.3f}  soporte {m['soporte']}" for m in c["por_contexto"]]
    texto += ["", "Errores de duración (frase | esperado | extraído):"]
    texto += [f"  {f} | {e} | {x}" for f, e, x in d["errores"]] or ["  Ninguno"]
    texto += ["", "Errores de contextos (frase | esperado | extraído):"]
    texto += [f"  {f} | {e} | {x}" for f, e, x in c["errores"]] or ["  Ninguno"]

    conf = d["confusion"]
    secciones += f"""<div class="ventana"><h2>Extracción de información por campo</h2>
<div class="aviso">Las {r['n']} frases las escribió quien programó las reglas, así que estos números pueden
ser optimistas. Otro integrante debe agregar frases nuevas en <code>corpus/extraccion_prueba.txt</code>.</div>
<h3>Duración de la dificultad</h3>
{_tarjetas([("Detección (F1)", f"{d['f1']:.2f}"), ("Valor exacto", f"{d['exactitud_valor'] * 100:.0f} %"),
            ("Campo correcto", f"{d['exactitud_campo'] * 100:.0f} %")])}
<p>Detección: {conf['tp']} aciertos, {conf['fn']} duraciones no detectadas, {conf['fp']} falsas detecciones,
{conf['tn']} frases sin duración bien ignoradas. Valor exacto calculado sobre {d['casos_valor']} frases con días conocidos.</p>
{_tabla(["Frase", "Esperado (días)", "Extraído"], d["errores"]) if d["errores"] else "<p>Sin errores.</p>"}
<h3>Contextos mencionados</h3>
{_tarjetas([("Micro F1", f"{c['micro']['f1']:.2f}"), ("Precision", f"{c['micro']['precision']:.2f}"),
            ("Recall", f"{c['micro']['recall']:.2f}"), ("Conjunto exacto", f"{c['exactitud_conjunto'] * 100:.0f} %")])}
{_tabla(["Contexto", "Precision", "Recall", "F1", "Soporte"],
        [[m["contexto"], f"{m['precision']:.3f}", f"{m['recall']:.3f}", f"{m['f1']:.3f}", m["soporte"]]
         for m in c["por_contexto"]])}
<h3>Errores de contexto</h3>
{_tabla(["Frase", "Esperado", "Extraído"], c["errores"]) if c["errores"] else "<p>Sin errores.</p>"}
</div>"""

    # ---------- B) Matching ----------
    psicologos = cargar_psicologos()
    casos_m = leer_casos_matching(CASOS_MATCHING)
    ruta_hoja = generar_hoja_anotacion(casos_m, psicologos)
    m = evaluar_matching(casos_m, psicologos)
    texto.append("")
    if m is None:
        mensaje = (f"MATCHING: todavía no hay anotaciones en {CASOS_MATCHING}. Cada integrante debe "
                   f"ordenar los 3 psicólogos más adecuados por caso usando {ruta_hoja}.")
        texto.append(mensaje)
        secciones += (f'<div class="ventana"><h2>Matching</h2><div class="aviso">Todavía no hay anotaciones. '
                      f'Cada integrante debe llenar su línea <code>orden_...</code> en '
                      f'<code>corpus/evaluacion_matching.txt</code> usando la '
                      f'<a href="hoja_anotacion_matching.html">hoja de anotación</a>, sin ver la '
                      f'recomendación del programa.</div></div>')
    else:
        texto.append(f"MATCHING ({m['casos']} de {m['total_casos']} casos anotados; "
                     f"anotadores: {', '.join(m['anotadores'])})")
        filas = []
        for v in m["variantes"]:
            texto.append(f"  {v['nombre']}: precision@3 vs consenso {v['precision3_consenso']:.3f}, "
                         f"acierto@1 {v['acierto1_consenso']:.3f}, azar {v['azar']:.3f}")
            filas.append([v["nombre"], f"{v['precision3_consenso']:.3f}", f"{v['acierto1_consenso']:.3f}",
                          ", ".join(f"{a}: {p:.2f}" for a, p in v["precision3_anotador"].items() if p is not None),
                          f"{v['azar']:.3f}"])
        acuerdo = [[a, b, f"{p:.3f}", n] for a, b, p, n in m["acuerdo"]]
        for a, b, p, n in m["acuerdo"]:
            texto.append(f"  Acuerdo {a}-{b}: precision@3 {p:.3f} ({n} casos)")
        completo = m["variantes"][0]
        detalle = [[cid, ", ".join(top), ", ".join(con), f"{p:.2f}"] for cid, top, con, p in completo["detalle"]]
        secciones += f"""<div class="ventana"><h2>Matching contra el orden del equipo</h2>
<p>{m['casos']} de {m['total_casos']} casos anotados · anotadores: {', '.join(m['anotadores'])}</p>
{_tabla(["Variante", "precision@3 (consenso)", "acierto@1", "precision@3 por anotador", "Azar"], filas)}
<h3>Acuerdo entre anotadores</h3>
{_tabla(["Anotador", "Anotador", "precision@3", "Casos"], acuerdo) if acuerdo else "<p>Se necesita más de un anotador.</p>"}
<div class="info">Si el acuerdo entre personas es bajo, la tarea es ambigua y no se puede esperar que el
algoritmo coincida mucho más que eso.</div>
<h3>Detalle por caso (algoritmo completo)</h3>
{_tabla(["Caso", "Top 3 del algoritmo", "Top 3 del consenso", "precision@3"], detalle)}
</div>"""

    ruta_txt = config.ruta_salida("reporte_vinculacion.txt")
    guardar_texto(ruta_txt, "\n".join(texto) + "\n")
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Evaluación de extracción y matching</title>
<style>{ESTILOS_CSS} .ventana {{ display: block; }}</style></head><body>
<div class="encabezado"><h1>Evaluación de extracción y matching</h1>
<p>Métricas calculadas con funciones propias · sin librerías</p></div>
<div class="contenedor"><p><a href="inicio.html">← Volver al inicio</a></p>{secciones}</div></body></html>"""
    ruta_html = config.ruta_salida("reporte_vinculacion.html")
    guardar_texto(ruta_html, html)

    print("\n".join(texto[4:11]))
    print(texto[-1] if m is None else "\n".join(t for t in texto if t.startswith("  Completo") or
                                                  t.startswith("MATCHING")))
    print("\nReporte de texto:  ", ruta_txt)
    print("Reporte visual:    ", ruta_html)
    print("Hoja de anotación: ", ruta_hoja)


if __name__ == "__main__":
    main()
