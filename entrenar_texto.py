# ==============================================================
# ENTRENAMIENTO Y EVALUACION DEL MODULO DE TEXTO
# ==============================================================
#
# Ejecutar desde la carpeta del proyecto:
#     python entrenar_texto.py
#
# 1. Validacion cruzada estratificada (5 pliegues) en el corpus de
#    entrenamiento: Naive Bayes contra red neuronal MLP.
# 2. Entrenamiento con todo el corpus de entrenamiento y evaluacion
#    en el corpus de PRUEBA (frases que el modelo nunca vio).
# 3. Evaluacion del modulo de prioridad con los casos de seguridad.
# 4. Guarda el modelo en datos/modelo_texto.txt y los reportes en
#    salidas/reporte_texto.txt y salidas/reporte_texto.html
# ==============================================================

import config
from nucleo.archivos import guardar_texto
from nucleo.matematicas import indice_maximo
from modelos.evaluacion import (
    matriz_confusion, sumar_matrices, exactitud, f1_macro, metricas_por_clase,
    resumen_pliegues, matriz_a_texto, metricas_a_texto
)
from emociones.preparacion import asignar_pliegues_estratificados
from texto.modelo_texto import leer_corpus, entrenar_modelos, predecir, guardar_modelo, clases_ordenadas
from texto.seguridad import evaluar_prioridad, ORDEN_NIVELES
from visual.svg import crear_svg_matriz_confusion, crear_svg_curvas
from visual.html import ESTILOS_CSS

NOMBRES_MODELO = {"nb": "Naive Bayes multinomial", "red": "Red neuronal MLP (TF-IDF)"}


def _evaluar(modelos, datos, tipo):
    clases = modelos["clases"]
    Y = [clases.index(c) for c, _ in datos]
    Yp = [indice_maximo(predecir(modelos, f, tipo)) for _, f in datos]
    return matriz_confusion(Y, Yp, len(clases)), Yp


def validacion_cruzada(entrenamiento):
    registros = [{"categoria": c, "frase": f} for c, f in entrenamiento]
    pliegues = asignar_pliegues_estratificados(registros, "categoria",
                                               config.NUMERO_PLIEGUES, config.SEMILLA)
    n = len(clases_ordenadas())
    resultados = {t: {"matriz": [[0] * n for _ in range(n)], "exactitudes": [], "f1s": []}
                  for t in NOMBRES_MODELO}

    for k in range(config.NUMERO_PLIEGUES):
        ent = [d for d, p in zip(entrenamiento, pliegues) if p != k]
        pru = [d for d, p in zip(entrenamiento, pliegues) if p == k]
        modelos = entrenar_modelos([f for _, f in ent], [c for c, _ in ent], config.SEMILLA + k)
        for tipo, r in resultados.items():
            matriz, _ = _evaluar(modelos, pru, tipo)
            r["matriz"] = sumar_matrices(r["matriz"], matriz)
            r["exactitudes"].append(exactitud(matriz))
            r["f1s"].append(f1_macro(matriz))
        print(f"  Pliegue {k + 1}/{config.NUMERO_PLIEGUES}: "
              + " | ".join(f"{NOMBRES_MODELO[t]}: {resultados[t]['exactitudes'][-1]:.3f}"
                           for t in NOMBRES_MODELO))
    return resultados


def evaluar_seguridad():
    casos = leer_corpus(config.CASOS_SEGURIDAD)
    niveles = ORDEN_NIVELES
    reales, predichos, falsos_negativos, falsas_alarmas = [], [], [], []
    for nivel, frase in casos:
        detectado = evaluar_prioridad(frase)["nivel"]
        reales.append(niveles.index(nivel))
        predichos.append(niveles.index(detectado))
        if niveles.index(detectado) < niveles.index(nivel):
            falsos_negativos.append((nivel, detectado, frase))
        elif niveles.index(detectado) > niveles.index(nivel):
            falsas_alarmas.append((nivel, detectado, frase))
    matriz = matriz_confusion(reales, predichos, len(niveles))
    return {"matriz": matriz, "falsos_negativos": falsos_negativos,
            "falsas_alarmas": falsas_alarmas, "total": len(casos)}


def _tabla_metricas_html(matriz, nombres):
    html = ('<table class="tabla"><tr><th>Clase</th><th>Precision</th><th>Recall</th>'
            '<th>F1</th><th>Soporte</th></tr>')
    for nombre, m in zip(nombres, metricas_por_clase(matriz)):
        html += (f"<tr><td>{nombre}</td><td>{m['precision']:.3f}</td><td>{m['recall']:.3f}</td>"
                 f"<td>{m['f1']:.3f}</td><td>{m['soporte']}</td></tr>")
    return html + "</table>"


def _lista_casos_html(casos, vacio):
    if not casos:
        return f"<p>{vacio}</p>"
    html = '<table class="tabla"><tr><th>Nivel real</th><th>Nivel detectado</th><th>Frase</th></tr>'
    for real, detectado, frase in casos:
        html += f"<tr><td>{real}</td><td>{detectado}</td><td>{frase}</td></tr>"
    return html + "</table>"


def main():
    print("=" * 60)
    print("MODULO DE TEXTO - ENTRENAMIENTO Y EVALUACION")
    print("=" * 60)

    entrenamiento = leer_corpus(config.CORPUS_ENTRENAMIENTO)
    prueba = leer_corpus(config.CORPUS_PRUEBA)
    clases = clases_ordenadas()
    nombres = [config.CATEGORIAS_MOTIVO[c] for c in clases]
    print(f"Frases de entrenamiento: {len(entrenamiento)} | de prueba: {len(prueba)} "
          f"| categorias: {len(clases)}")

    print(f"\nValidacion cruzada ({config.NUMERO_PLIEGUES} pliegues) en entrenamiento:")
    cv = validacion_cruzada(entrenamiento)

    print("\nEntrenando con todo el corpus de entrenamiento...")
    modelos = entrenar_modelos([f for _, f in entrenamiento], [c for c, _ in entrenamiento])
    guardar_modelo(modelos)
    print("Vocabulario TF-IDF:", modelos["vectorizador"].tamano(), "terminos")
    print("Modelo guardado en:", config.MODELO_TEXTO)

    prueba_resultados = {}
    errores_red = []
    for tipo in NOMBRES_MODELO:
        matriz, Yp = _evaluar(modelos, prueba, tipo)
        prueba_resultados[tipo] = matriz
        if tipo == "red":
            errores_red = [(c, clases[p], f) for (c, f), p in zip(prueba, Yp) if clases[p] != c]

    seguridad = evaluar_seguridad()
    met_seg = metricas_por_clase(seguridad["matriz"])
    recall_protocolo = met_seg[ORDEN_NIVELES.index("protocolo")]["recall"]

    # ----- Reporte de texto -----
    texto = ["=" * 60, "REPORTE - MODULO DE TEXTO", "=" * 60,
             "Corpus sintetico escrito para el prototipo (no proviene de personas reales).",
             f"Entrenamiento: {len(entrenamiento)} frases | Prueba: {len(prueba)} frases",
             f"Vocabulario TF-IDF: {modelos['vectorizador'].tamano()} terminos", "",
             "VALIDACION CRUZADA (entrenamiento)"]
    for tipo, r in cv.items():
        em, ed = resumen_pliegues(r["exactitudes"])
        fm, fd = resumen_pliegues(r["f1s"])
        texto.append(f"  {NOMBRES_MODELO[tipo]}: exactitud {em:.3f} ± {ed:.3f} | F1 macro {fm:.3f} ± {fd:.3f}")
    texto += ["", "CONJUNTO DE PRUEBA (frases nunca vistas)"]
    for tipo, matriz in prueba_resultados.items():
        texto.append(f"  {NOMBRES_MODELO[tipo]}: exactitud {exactitud(matriz):.3f} | F1 macro {f1_macro(matriz):.3f}")
    texto += ["", "Red neuronal en prueba, por categoria:",
              metricas_a_texto(prueba_resultados["red"], clases), "",
              "Matriz de confusion (red neuronal, prueba):",
              matriz_a_texto(prueba_resultados["red"], clases), "",
              "MODULO DE PRIORIDAD",
              f"  Casos: {seguridad['total']} | Recall de 'protocolo': {recall_protocolo:.3f}",
              f"  Casos de riesgo NO detectados (falsos negativos): {len(seguridad['falsos_negativos'])}",
              f"  Falsas alarmas: {len(seguridad['falsas_alarmas'])}"]
    for real, detectado, frase in seguridad["falsos_negativos"]:
        texto.append(f"    [NO DETECTADO] {real} -> {detectado}: {frase}")
    for real, detectado, frase in seguridad["falsas_alarmas"]:
        texto.append(f"    [FALSA ALARMA] {real} -> {detectado}: {frase}")
    texto.append(matriz_a_texto(seguridad["matriz"], ORDEN_NIVELES))

    ruta_txt = config.ruta_salida("reporte_texto.txt")
    guardar_texto(ruta_txt, "\n".join(texto) + "\n")

    # ----- Reporte HTML -----
    resumen = ('<table class="tabla"><tr><th>Modelo</th><th>Validación cruzada: exactitud</th>'
               '<th>Validación cruzada: F1 macro</th><th>Prueba: exactitud</th><th>Prueba: F1 macro</th></tr>')
    for tipo in NOMBRES_MODELO:
        em, ed = resumen_pliegues(cv[tipo]["exactitudes"])
        fm, fd = resumen_pliegues(cv[tipo]["f1s"])
        m = prueba_resultados[tipo]
        resumen += (f"<tr><td>{NOMBRES_MODELO[tipo]}</td><td>{em:.3f} ± {ed:.3f}</td>"
                    f"<td>{fm:.3f} ± {fd:.3f}</td><td>{exactitud(m):.3f}</td><td>{f1_macro(m):.3f}</td></tr>")
    resumen += f"<tr><td>Azar</td><td>{1 / len(clases):.3f}</td><td>—</td><td>{1 / len(clases):.3f}</td><td>—</td></tr></table>"

    errores_html = '<table class="tabla"><tr><th>Real</th><th>Predicho</th><th>Frase</th></tr>'
    for real, pred, frase in errores_red:
        errores_html += (f"<tr><td>{config.CATEGORIAS_MOTIVO[real]}</td>"
                         f"<td>{config.CATEGORIAS_MOTIVO[pred]}</td><td>{frase}</td></tr>")
    errores_html += "</table>"

    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Módulo de texto</title>
<style>{ESTILOS_CSS} .ventana {{ display: block; }}</style></head>
<body>
<div class="encabezado"><h1>MÓDULO DE TEXTO</h1>
<p>Motivos de consulta y prioridad · procesamiento de lenguaje implementado desde cero</p></div>
<div class="contenedor">
<div class="ventana"><h2>Alcance</h2><div class="info">El clasificador infiere el tema principal
de lo que la persona escribe. No es un diagnóstico. El corpus es sintético, escrito para el
prototipo.</div>
<p>Entrenamiento: <strong>{len(entrenamiento)}</strong> frases · Prueba: <strong>{len(prueba)}</strong>
frases · Vocabulario TF-IDF: <strong>{modelos['vectorizador'].tamano()}</strong> términos</p></div>
<div class="ventana"><h2>Clasificación de motivos</h2>{resumen}
<div class="grafica">{crear_svg_curvas([("Red neuronal", modelos["historial"], "#C74440")],
                                       "Pérdida de entrenamiento (modelo final)", "texto_perdida.svg")}</div>
<h3>Red neuronal en el conjunto de prueba</h3>
<div class="grafica">{crear_svg_matriz_confusion(prueba_resultados["red"], clases,
                                                 "Matriz de confusión - prueba", "texto_matriz.svg",
                                                 tamano_celda=58)}</div>
{_tabla_metricas_html(prueba_resultados["red"], nombres)}
<h3>Errores de la red neuronal en prueba</h3>{errores_html}</div>
<div class="ventana"><h2>Módulo de prioridad</h2>
<p>Casos evaluados: <strong>{seguridad['total']}</strong> · Recall de "protocolo":
<strong>{recall_protocolo:.3f}</strong> · Riesgos no detectados:
<strong>{len(seguridad['falsos_negativos'])}</strong> · Falsas alarmas:
<strong>{len(seguridad['falsas_alarmas'])}</strong></p>
<div class="info">Criterio: ante la duda se prefiere una falsa alarma a un caso de riesgo sin
detectar. Las reglas se diseñaron junto con estos casos, así que estos números son optimistas;
hace falta un conjunto de casos escrito por otra persona y revisión de un profesional.</div>
<div class="grafica">{crear_svg_matriz_confusion(seguridad["matriz"], ORDEN_NIVELES,
                                                 "Matriz de confusión - prioridad", "seguridad_matriz.svg")}</div>
<h3>Riesgos no detectados</h3>{_lista_casos_html(seguridad["falsos_negativos"], "Ninguno.")}
<h3>Falsas alarmas</h3>{_lista_casos_html(seguridad["falsas_alarmas"], "Ninguna.")}</div>
</div></body></html>
"""
    ruta_html = config.ruta_salida("reporte_texto.html")
    guardar_texto(ruta_html, html)

    print("\n" + "\n".join(texto[6:]))
    print("\nReporte de texto:", ruta_txt)
    print("Reporte visual:  ", ruta_html)


if __name__ == "__main__":
    main()
