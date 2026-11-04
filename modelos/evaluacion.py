# ==============================================================
# METRICAS DE EVALUACION DESDE CERO
# ==============================================================
#
# Matriz de confusion M[i][j]: ejemplos de la clase real i que el
# modelo predijo como clase j.
#
#   precision_c = VP / (VP + FP)    (de lo que predijo como c, cuanto era c)
#   recall_c    = VP / (VP + FN)    (de lo que era c, cuanto encontro)
#   F1_c        = 2 P R / (P + R)
#   exactitud   = sum diagonal / total
#   F1 macro    = promedio simple de F1_c (todas las clases pesan igual)
# ==============================================================

from nucleo.matematicas import media, desviacion_estandar


def matriz_confusion(reales, predichos, numero_clases):
    if len(reales) != len(predichos):
        raise ValueError("Las listas de reales y predichos deben medir lo mismo.")
    matriz = [[0] * numero_clases for _ in range(numero_clases)]
    for r, p in zip(reales, predichos):
        matriz[r][p] += 1
    return matriz


def sumar_matrices(a, b):
    return [[x + y for x, y in zip(fa, fb)] for fa, fb in zip(a, b)]


def metricas_por_clase(matriz):
    n = len(matriz)
    resultados = []
    for c in range(n):
        vp = matriz[c][c]
        fp = sum(matriz[i][c] for i in range(n)) - vp
        fn = sum(matriz[c]) - vp
        precision = vp / (vp + fp) if vp + fp > 0 else 0.0
        recall = vp / (vp + fn) if vp + fn > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
        resultados.append({
            "precision": precision, "recall": recall, "f1": f1, "soporte": vp + fn
        })
    return resultados


def exactitud(matriz):
    total = sum(sum(fila) for fila in matriz)
    if total == 0:
        return 0.0
    return sum(matriz[i][i] for i in range(len(matriz))) / total


def f1_macro(matriz):
    return media([m["f1"] for m in metricas_por_clase(matriz)])


def resumen_pliegues(valores):
    """Media y desviacion estandar de una metrica entre pliegues."""
    return media(valores), desviacion_estandar(valores)


def matriz_a_texto(matriz, clases):
    ancho = max(10, max(len(c) for c in clases) + 2)
    lineas = ["Real \\ Predicho".ljust(ancho + 6) + "".join(c[:ancho - 1].rjust(ancho) for c in clases)]
    for clase, fila in zip(clases, matriz):
        lineas.append(clase.ljust(ancho + 6) + "".join(str(v).rjust(ancho) for v in fila))
    return "\n".join(lineas)


def metricas_a_texto(matriz, clases):
    lineas = [f"{'Clase':<12}{'Precision':>11}{'Recall':>9}{'F1':>8}{'Soporte':>9}"]
    for clase, m in zip(clases, metricas_por_clase(matriz)):
        lineas.append(
            f"{clase:<12}{m['precision']:>11.3f}{m['recall']:>9.3f}{m['f1']:>8.3f}{m['soporte']:>9}"
        )
    lineas.append(f"\nExactitud: {exactitud(matriz):.3f} | F1 macro: {f1_macro(matriz):.3f}")
    return "\n".join(lineas)
