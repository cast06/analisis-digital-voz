# ==============================================================
# ENTRENAMIENTO Y EVALUACION DEL RECONOCEDOR DE PALABRAS AISLADAS
# ==============================================================
#
# Ejecutar desde la carpeta del proyecto:
#     python entrenar_palabras.py
#
# Usa la misma lista de MESD que las emociones (datos/lista_mesd.txt).
# ==============================================================

import config
from nucleo.archivos import guardar_texto
from emociones.preparacion import contar_por
from modelos.evaluacion import resumen_pliegues, matriz_a_texto, metricas_a_texto, metricas_por_clase
from palabras.datos_palabras import construir_tabla_palabras, dimension_vector
from palabras.modelo_palabras import (
    evaluar, pliegues_por_voz, pliegues_estratificados, entrenar_modelo_final, AVISO_PALABRAS
)
from visual.svg import crear_svg_matriz_confusion, crear_svg_curvas
from visual.html import ESTILOS_CSS

COLORES = ["#2878B5", "#C74440", "#E39A26", "#3A9A5B"]


def _curva_promedio(historiales):
    if not historiales:
        return []
    largo = min(len(h) for h in historiales)
    return [sum(h[i] for h in historiales) / len(historiales) for i in range(largo)]


def _resumen(resultado):
    em, ed = resumen_pliegues(resultado["exactitudes"])
    fm, fd = resumen_pliegues(resultado["f1s"])
    return em, ed, fm, fd


def _tabla_resumen_html(resultados, numero_clases):
    html = ('<table class="tabla"><tr><th>Evaluación</th><th>Modelo</th>'
            '<th>Exactitud (media ± desv.)</th><th>F1 macro (media ± desv.)</th></tr>')
    for evaluacion, nombre, r in resultados:
        em, ed, fm, fd = _resumen(r)
        html += (f"<tr><td>{evaluacion}</td><td>{nombre}</td>"
                 f"<td>{em:.3f} ± {ed:.3f}</td><td>{fm:.3f} ± {fd:.3f}</td></tr>")
    html += (f"<tr><td>—</td><td>Azar (referencia)</td><td>{1 / numero_clases:.3f}</td>"
             f"<td>—</td></tr></table>")
    return html


def _tabla_metricas_html(matriz, clases):
    html = ('<table class="tabla"><tr><th>Palabra</th><th>Precision</th><th>Recall</th>'
            '<th>F1</th><th>Soporte</th></tr>')
    for clase, m in zip(clases, metricas_por_clase(matriz)):
        html += (f"<tr><td>{clase}</td><td>{m['precision']:.3f}</td><td>{m['recall']:.3f}</td>"
                 f"<td>{m['f1']:.3f}</td><td>{m['soporte']}</td></tr>")
    return html + "</table>"


def _detalle_voz_html(resultado):
    html = '<table class="tabla"><tr><th>Tipo de voz de prueba</th><th>Entrenamiento</th><th>Prueba</th><th>Exactitud</th></tr>'
    for etiqueta, n_ent, n_pru, exa in resultado["detalle"]:
        html += f"<tr><td>{etiqueta}</td><td>{n_ent}</td><td>{n_pru}</td><td>{exa:.3f}</td></tr>"
    return html + "</table>"


def main():
    print("=" * 60)
    print("RECONOCIMIENTO DE PALABRAS AISLADAS - ENTRENAMIENTO")
    print("=" * 60)

    registros = construir_tabla_palabras()
    if not registros:
        print("\nNo se encontraron grabaciones del corpus A de MESD.")
        print(f"Revisa la lista de archivos en: {config.LISTA_MESD}")
        return

    conteo_inicial = contar_por(registros, "palabra")
    descartadas = sorted(p for p, n in conteo_inicial.items()
                         if n < config.MINIMO_GRABACIONES_POR_PALABRA)
    if descartadas:
        registros = [r for r in registros if r["palabra"] not in descartadas]
        print(f"\nSe descartan {len(descartadas)} palabras con menos de "
              f"{config.MINIMO_GRABACIONES_POR_PALABRA} grabaciones: {', '.join(descartadas)}")
    if not registros:
        print("No quedan palabras con suficientes grabaciones.")
        return

    clases = sorted(set(r["palabra"] for r in registros))
    conteo_palabra = contar_por(registros, "palabra")
    conteo_voz = contar_por(registros, "voz")
    print(f"\nGrabaciones: {len(registros)} | Palabras distintas: {len(clases)}")
    print("Por tipo de voz:", conteo_voz)
    print("Grabaciones por palabra: min", min(conteo_palabra.values()),
          "max", max(conteo_palabra.values()))

    resultados = []
    p_voz, etiquetas_voz = pliegues_por_voz(registros)
    p_estr = pliegues_estratificados(registros)

    for nombre, capas in config.ARQUITECTURAS_PALABRAS:
        print(f"\nEvaluacion por tipo de voz (voz no vista): {nombre}")
        resultados.append(("Por tipo de voz (voz no vista)", nombre,
                           evaluar(registros, p_voz, capas, clases, nombre, etiquetas_voz)))
    for nombre, capas in config.ARQUITECTURAS_PALABRAS:
        print(f"\nEvaluacion estratificada de {config.NUMERO_PLIEGUES} pliegues: {nombre}")
        resultados.append((f"Estratificada {config.NUMERO_PLIEGUES} pliegues", nombre,
                           evaluar(registros, p_estr, capas, clases, nombre)))

    nombre_final, capas_finales = config.ARQUITECTURAS_PALABRAS[-1]
    print(f"\nEntrenando modelo final ({nombre_final}) con todos los datos...")
    _, historial_final = entrenar_modelo_final(registros, capas_finales, clases)
    print("Modelo guardado en:", config.MODELO_PALABRAS)

    # ----- Reporte de texto -----
    texto = [
        "=" * 60, "REPORTE - RECONOCIMIENTO DE PALABRAS AISLADAS", "=" * 60,
        AVISO_PALABRAS, "",
        f"Grabaciones: {len(registros)} | Palabras: {len(clases)} | Por voz: {conteo_voz}",
        f"Palabras descartadas (menos de {config.MINIMO_GRABACIONES_POR_PALABRA} grabaciones): "
        f"{len(descartadas)}",
        "Vocabulario: " + ", ".join(clases),
        f"Entrada: MFCC {config.MFCC_COEFICIENTES} coef. x {config.MFCC_TRAMOS} tramos "
        f"= {dimension_vector()} valores (con normalizacion de media cepstral)",
        f"Referencia de azar: {1 / len(clases):.3f}", ""
    ]
    for evaluacion, nombre, r in resultados:
        em, ed, fm, fd = _resumen(r)
        texto += ["-" * 60, f"{evaluacion} | {nombre}", "-" * 60,
                  f"Exactitud: {em:.3f} ± {ed:.3f} | F1 macro: {fm:.3f} ± {fd:.3f}", ""]
    mejor = resultados[len(config.ARQUITECTURAS_PALABRAS) - 1][2]
    texto += ["Metricas por palabra (MLP, voz no vista):",
              metricas_a_texto(mejor["matriz"], clases), ""]

    ruta_txt = config.ruta_salida("reporte_palabras.txt")
    guardar_texto(ruta_txt, "\n".join(texto))

    # ----- Reporte HTML -----
    svg_matriz = crear_svg_matriz_confusion(
        mejor["matriz"], clases, "Matriz de confusión - MLP, voz no vista",
        "palabras_matriz.svg", tamano_celda=34)
    curvas = [(("Voz no vista" if ev.startswith("Por") else "Estratificada") + " · "
               + ("softmax" if "softmax" in nom else "MLP"),
               _curva_promedio(r["historiales"]), COLORES[i % 4])
              for i, (ev, nom, r) in enumerate(resultados)]
    svg_curvas = crear_svg_curvas(curvas, "Pérdida de entrenamiento (promedio de pliegues)",
                                  "palabras_perdida.svg")

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reconocimiento de palabras aisladas</title>
<style>{ESTILOS_CSS} .ventana {{ display: block; }}</style></head>
<body>
<div class="encabezado"><h1>RECONOCIMIENTO DE PALABRAS AISLADAS</h1>
<p>MFCC + FFT + red neuronal implementados desde cero · Datos: MESD, corpus A</p></div>
<div class="contenedor">
<div class="ventana"><h2>Alcance</h2><div class="info">{AVISO_PALABRAS}</div>
<p>Grabaciones: <strong>{len(registros)}</strong> · Palabras: <strong>{len(clases)}</strong>
· Por tipo de voz: {conteo_voz}</p>
<p><strong>Vocabulario:</strong> {", ".join(clases)}</p></div>
<div class="ventana"><h2>Comparación</h2>{_tabla_resumen_html(resultados, len(clases))}
<div class="info"><strong>Por tipo de voz:</strong> se entrena con dos tipos de voz y se prueba
con el tercero, que el modelo nunca escuchó. <strong>Estratificada:</strong> todas las voces
aparecen en entrenamiento y en prueba.</div>
<h3>MLP, detalle por tipo de voz de prueba</h3>{_detalle_voz_html(mejor)}
<div class="grafica">{svg_curvas}</div></div>
<div class="ventana"><h2>Matriz de confusión (MLP, voz no vista)</h2>
<div class="grafica">{svg_matriz}</div>{_tabla_metricas_html(mejor["matriz"], clases)}</div>
</div></body></html>
"""
    ruta_html = config.ruta_salida("reporte_palabras.html")
    guardar_texto(ruta_html, html)

    print("\n" + "\n".join(texto[-(len(resultados) * 5 + 3):]))
    print("Reporte de texto:", ruta_txt)
    print("Reporte visual:  ", ruta_html)


if __name__ == "__main__":
    main()
