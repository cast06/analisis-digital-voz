# ==============================================================
# ENTRENAMIENTO Y EVALUACION DEL RECONOCIMIENTO DE EMOCIONES
# ==============================================================
#
# Ejecutar desde la carpeta del proyecto:
#     python entrenar_emociones.py
#
# Pasos:
# 1. Lee datos/lista_mesd.txt y calcula (o recupera del cache) las
#    11 variables acusticas de cada grabacion.
# 2. Compara dos modelos con validacion cruzada de 5 pliegues
#    agrupada por palabra:
#       - regresion softmax (sin capas ocultas), como linea base
#       - red neuronal MLP con capas ocultas
# 3. Entrena el ultimo modelo con todos los datos y lo guarda en
#    datos/modelo_emociones.txt.
# 4. Escribe salidas/reporte_emociones.txt y salidas/reporte_emociones.html
# ==============================================================

import config
from nucleo.archivos import guardar_texto
from audio.caracteristicas import VARIABLES_EMOCION
from emociones.mesd import construir_tabla_mesd
from emociones.preparacion import contar_por
from emociones.modelo_emocion import validacion_cruzada, entrenar_modelo_final, AVISO
from modelos.evaluacion import (
    exactitud, f1_macro, resumen_pliegues, matriz_a_texto, metricas_a_texto, metricas_por_clase
)
from visual.svg import crear_svg_matriz_confusion, crear_svg_curvas
from visual.html import ESTILOS_CSS

COLORES = ["#6C1D45", "#B38E5D", "#3A7D7C", "#C7546E", "#5B5B8C"]


def _curva_promedio(historiales):
    if not historiales:
        return []
    largo = min(len(h) for h in historiales)
    return [sum(h[i] for h in historiales) / len(historiales) for i in range(largo)]


def _seccion_txt(nombre, resultado):
    exa_media, exa_desv = resumen_pliegues(resultado["exactitudes"])
    f1_media, f1_desv = resumen_pliegues(resultado["f1s"])
    return "\n".join([
        "-" * 60,
        f"MODELO: {nombre}",
        "-" * 60,
        f"Exactitud por pliegue: " + ", ".join(f"{v:.3f}" for v in resultado["exactitudes"]),
        f"Exactitud media: {exa_media:.3f} ± {exa_desv:.3f}",
        f"F1 macro medio:  {f1_media:.3f} ± {f1_desv:.3f}",
        "",
        "Matriz de confusion (suma de los pliegues):",
        matriz_a_texto(resultado["matriz"], config.CLASES_EMOCION),
        "",
        metricas_a_texto(resultado["matriz"], config.CLASES_EMOCION),
        ""
    ])


def _tabla_metricas_html(matriz):
    html = ('<table class="tabla"><tr><th>Emoción</th><th>Precision</th><th>Recall</th>'
            '<th>F1</th><th>Soporte</th></tr>')
    for clase, m in zip(config.CLASES_EMOCION, metricas_por_clase(matriz)):
        html += (f"<tr><td>{clase}</td><td>{m['precision']:.3f}</td><td>{m['recall']:.3f}</td>"
                 f"<td>{m['f1']:.3f}</td><td>{m['soporte']}</td></tr>")
    return html + "</table>"


def _reporte_html(conteo_emocion, conteo_voz, total, resultados, historial_final):
    filas_datos = "".join(f"<tr><td>{e}</td><td>{conteo_emocion.get(e, 0)}</td></tr>"
                          for e in config.CLASES_EMOCION)
    filas_voz = "".join(f"<tr><td>{v}</td><td>{conteo_voz.get(v, 0)}</td></tr>"
                        for v in sorted(conteo_voz))

    resumen = ('<table class="tabla"><tr><th>Modelo</th><th>Exactitud (media ± desv.)</th>'
               '<th>F1 macro (media ± desv.)</th></tr>')
    for nombre, _, r in resultados:
        em, ed = resumen_pliegues(r["exactitudes"])
        fm, fd = resumen_pliegues(r["f1s"])
        resumen += f"<tr><td>{nombre}</td><td>{em:.3f} ± {ed:.3f}</td><td>{fm:.3f} ± {fd:.3f}</td></tr>"
    resumen += (f"<tr><td>Azar (referencia)</td><td>{1 / len(config.CLASES_EMOCION):.3f}</td>"
                f"<td>—</td></tr></table>")

    detalle = ""
    for i, (nombre, _, r) in enumerate(resultados, start=1):
        detalle += f"<h3>{nombre}</h3>"
        detalle += '<div class="grafica">' + crear_svg_matriz_confusion(
            r["matriz"], config.CLASES_EMOCION, f"Matriz de confusión - {nombre}",
            f"emociones_matriz_{i}.svg") + "</div>"
        detalle += _tabla_metricas_html(r["matriz"])

    curvas = [(nombre, _curva_promedio(r["historiales"]), COLORES[i % len(COLORES)])
              for i, (nombre, _, r) in enumerate(resultados)]
    svg_curvas = crear_svg_curvas(curvas, "Pérdida de entrenamiento (promedio de pliegues)",
                                  "emociones_perdida_cv.svg")
    svg_final = crear_svg_curvas([("Modelo final", historial_final, COLORES[1])],
                                 "Pérdida de entrenamiento del modelo final",
                                 "emociones_perdida_final.svg")

    variables = "".join(f"<li><code>{v}</code></li>" for v in VARIABLES_EMOCION)

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reconocimiento de emociones en la voz</title>
<style>{ESTILOS_CSS} .ventana {{ display: block; }}</style></head>
<body>
<div class="encabezado"><h1>RECONOCIMIENTO DE EMOCIONES EN LA VOZ</h1>
<p>Red neuronal implementada desde cero · Datos: MESD (voces adultas)</p></div>
<div class="contenedor">
<div class="ventana"><h2>Aviso</h2><div class="info">{AVISO}</div></div>
<div class="ventana"><h2>Datos utilizados</h2>
<p>Total de grabaciones: <strong>{total}</strong></p>
<div class="dos_columnas">
<table class="tabla"><tr><th>Emoción</th><th>Grabaciones</th></tr>{filas_datos}</table>
<table class="tabla"><tr><th>Tipo de voz</th><th>Grabaciones</th></tr>{filas_voz}</table>
</div>
<h3>Variables de entrada ({len(VARIABLES_EMOCION)})</h3><ul>{variables}</ul>
<div class="info">Validación cruzada de {config.NUMERO_PLIEGUES} pliegues agrupada por palabra:
ninguna palabra de prueba aparece en entrenamiento. Normalización z por tipo de voz calculada
solo con los datos de entrenamiento de cada pliegue.</div>
</div>
<div class="ventana"><h2>Comparación de modelos</h2>{resumen}
<div class="grafica">{svg_curvas}</div></div>
<div class="ventana"><h2>Resultados por modelo</h2>{detalle}</div>
<div class="ventana"><h2>Modelo final guardado</h2>
<p>Arquitectura: {resultados[-1][0]}, entrenado con las {total} grabaciones.</p>
<div class="grafica">{svg_final}</div></div>
</div></body></html>
"""


def main():
    print("=" * 60)
    print("RECONOCIMIENTO DE EMOCIONES EN LA VOZ - ENTRENAMIENTO")
    print("=" * 60)

    registros = construir_tabla_mesd()
    if not registros:
        print("\nNo se encontraron grabaciones de MESD.")
        print(f"Genera la lista de archivos en: {config.LISTA_MESD}")
        print("Las instrucciones estan en LEEME.md (seccion 'Reconocimiento de emociones').")
        return

    conteo_emocion = contar_por(registros, "emocion")
    conteo_voz = contar_por(registros, "voz")
    print(f"\nGrabaciones utilizables: {len(registros)}")
    print("Por emocion:", conteo_emocion)
    print("Por tipo de voz:", conteo_voz)

    if len(set(r["palabra"] for r in registros)) < config.NUMERO_PLIEGUES:
        print("Hay muy pocas palabras distintas para la validacion cruzada.")
        return

    resultados = []
    for nombre, capas in config.ARQUITECTURAS_EMOCION:
        print(f"\nValidacion cruzada: {nombre}")
        resultados.append((nombre, capas, validacion_cruzada(registros, capas, nombre)))

    nombre_final, capas_finales, _ = resultados[-1]
    print(f"\nEntrenando modelo final ({nombre_final}) con todos los datos...")
    _, _, historial_final = entrenar_modelo_final(registros, capas_finales)
    print("Modelo guardado en:", config.MODELO_EMOCIONES)

    texto = [
        "=" * 60,
        "REPORTE - RECONOCIMIENTO DE EMOCIONES EN LA VOZ",
        "=" * 60,
        AVISO,
        "",
        f"Grabaciones: {len(registros)} | Por emocion: {conteo_emocion} | Por voz: {conteo_voz}",
        f"Variables ({len(VARIABLES_EMOCION)}): " + ", ".join(VARIABLES_EMOCION),
        f"Validacion cruzada: {config.NUMERO_PLIEGUES} pliegues agrupados por palabra",
        f"Hiperparametros: epocas={config.EPOCAS}, tasa={config.TASA_APRENDIZAJE}, "
        f"lote={config.TAMANO_LOTE}, momento={config.MOMENTO}, L2={config.REGULARIZACION_L2}",
        f"Referencia de azar: exactitud {1 / len(config.CLASES_EMOCION):.3f}",
        ""
    ]
    for nombre, _, r in resultados:
        texto.append(_seccion_txt(nombre, r))

    ruta_txt = config.ruta_salida("reporte_emociones.txt")
    guardar_texto(ruta_txt, "\n".join(texto))
    ruta_html = config.ruta_salida("reporte_emociones.html")
    guardar_texto(ruta_html, _reporte_html(conteo_emocion, conteo_voz, len(registros),
                                           resultados, historial_final))

    print("\n" + "\n".join(texto[-len(resultados):]))
    print("Reporte de texto:", ruta_txt)
    print("Reporte visual:  ", ruta_html)


if __name__ == "__main__":
    main()
