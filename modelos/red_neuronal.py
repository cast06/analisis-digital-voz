# ==============================================================
# RED NEURONAL MULTICAPA (MLP) DESDE CERO
# ==============================================================
#
# Arquitectura: entrada -> [capas ocultas ReLU] -> salida softmax
#
# Propagacion hacia adelante (capa l):
#     z_l = W_l a_{l-1} + b_l
#     a_l = ReLU(z_l)            capas ocultas
#     p   = softmax(z_L)         capa de salida
#
# Perdida (entropia cruzada + regularizacion L2):
#     J = -(1/n) sum_i ln p_i[y_i] + (lambda/2) sum ||W_l||^2
#
# Retropropagacion:
#     delta_L = p - y_onehot
#     dJ/dW_l = delta_l a_{l-1}^T,   dJ/db_l = delta_l
#     delta_{l-1} = (W_l^T delta_l) * ReLU'(z_{l-1})
#
# Actualizacion: descenso del gradiente por mini-lotes con momento
#     v = mu v - eta g ;  W = W + v
#
# Si no hay capas ocultas, el modelo es una regresion softmax
# (regresion logistica multinomial).
#
# Complejidad por epoca: O(n * sum_l (n_l * n_{l-1}))
# ==============================================================

from nucleo.matematicas import (
    raiz_cuadrada, softmax, logaritmo_natural, indice_maximo, matriz_ceros
)
from nucleo.aleatorio import GeneradorAleatorio
from nucleo.archivos import leer_lineas


class RedNeuronal:

    def __init__(self, tamanos, semilla=42):
        """
        tamanos: lista [entradas, oculta_1, ..., oculta_k, clases]
        Inicializacion de He: W ~ N(0, sqrt(2 / entradas_de_la_capa))
        """
        if len(tamanos) < 2:
            raise ValueError("Se necesitan al menos capa de entrada y de salida.")
        for t in tamanos:
            if t < 1:
                raise ValueError("Cada capa debe tener al menos una neurona.")

        self.tamanos = list(tamanos)
        generador = GeneradorAleatorio(semilla)
        self.pesos = []
        self.sesgos = []
        for entrada, salida in zip(tamanos[:-1], tamanos[1:]):
            escala = raiz_cuadrada(2.0 / entrada)
            self.pesos.append([[generador.normal(0.0, escala) for _ in range(entrada)]
                               for _ in range(salida)])
            self.sesgos.append([0.0] * salida)

    # ----------------------------------------------------------
    # Propagacion hacia adelante
    # ----------------------------------------------------------

    def _propagar(self, x):
        """
        Devuelve (activaciones, preactivaciones) de todas las capas.
        x puede ser una lista (vector denso) o un diccionario
        {indice: valor} (vector disperso, como TF-IDF). En el caso
        disperso solo se multiplican las entradas distintas de cero.
        """
        disperso = isinstance(x, dict)
        if not disperso and len(x) != self.tamanos[0]:
            raise ValueError(f"Se esperaban {self.tamanos[0]} entradas y llegaron {len(x)}.")

        activaciones = [x]
        preactivaciones = []
        ultima = len(self.pesos) - 1

        for l, (W, b) in enumerate(zip(self.pesos, self.sesgos)):
            a_previa = activaciones[-1]
            if l == 0 and disperso:
                z = [sum(fila[j] * v for j, v in a_previa.items()) + bias
                     for fila, bias in zip(W, b)]
            else:
                z = [sum(w * a for w, a in zip(fila, a_previa)) + bias
                     for fila, bias in zip(W, b)]
            preactivaciones.append(z)
            if l == ultima:
                activaciones.append(softmax(z))
            else:
                activaciones.append([v if v > 0.0 else 0.0 for v in z])

        return activaciones, preactivaciones

    def predecir_probabilidades(self, x):
        return self._propagar(x)[0][-1]

    def predecir(self, x):
        return indice_maximo(self.predecir_probabilidades(x))

    # ----------------------------------------------------------
    # Perdida y gradientes
    # ----------------------------------------------------------

    def perdida(self, X, Y, l2=0.0):
        total = 0.0
        for x, y in zip(X, Y):
            p = self.predecir_probabilidades(x)[y]
            total -= logaritmo_natural(max(p, 1e-15))
        penalizacion = sum(w * w for W in self.pesos for fila in W for w in fila)
        return total / len(X) + 0.5 * l2 * penalizacion

    def gradientes(self, X, Y, l2=0.0):
        """Gradientes promedio de la perdida respecto a pesos y sesgos."""
        gW = [matriz_ceros(len(W), len(W[0])) for W in self.pesos]
        gb = [[0.0] * len(b) for b in self.sesgos]
        n = len(X)

        for x, y in zip(X, Y):
            activaciones, preactivaciones = self._propagar(x)

            # delta de la capa de salida: p - y_onehot
            delta = activaciones[-1][:]
            delta[y] -= 1.0

            for l in range(len(self.pesos) - 1, -1, -1):
                a_previa = activaciones[l]
                gW_l = gW[l]
                entradas = a_previa.items() if isinstance(a_previa, dict) else enumerate(a_previa)
                entradas = list(entradas)
                for i, d in enumerate(delta):
                    if d == 0.0:
                        continue
                    fila = gW_l[i]
                    for j, a in entradas:
                        fila[j] += d * a
                    gb[l][i] += d

                if l > 0:
                    W = self.pesos[l]
                    z_previa = preactivaciones[l - 1]
                    delta = [
                        sum(W[i][j] * delta[i] for i in range(len(delta)))
                        if z_previa[j] > 0.0 else 0.0
                        for j in range(len(a_previa))
                    ]

        for l, W in enumerate(self.pesos):
            for i, fila in enumerate(W):
                for j in range(len(fila)):
                    gW[l][i][j] = gW[l][i][j] / n + l2 * fila[j]
                gb[l][i] /= n
        return gW, gb

    # ----------------------------------------------------------
    # Entrenamiento
    # ----------------------------------------------------------

    def entrenar(self, X, Y, epocas=200, tasa=0.05, tamano_lote=16,
                 momento=0.9, l2=0.0, semilla=7, mostrar_cada=0,
                 restaurar_mejor=True):
        """
        Devuelve la lista con la perdida de entrenamiento por epoca.
        Si restaurar_mejor=True, al terminar se quedan los pesos de la
        epoca con menor perdida de entrenamiento (el descenso con momento
        puede oscilar y la ultima epoca no siempre es la mejor).
        """
        if len(X) != len(Y) or not X:
            raise ValueError("X y Y deben tener la misma longitud y no estar vacios.")

        generador = GeneradorAleatorio(semilla)
        vW = [matriz_ceros(len(W), len(W[0])) for W in self.pesos]
        vb = [[0.0] * len(b) for b in self.sesgos]
        indices = list(range(len(X)))
        historial = []
        mejor_perdida = None
        mejores_pesos = None
        mejores_sesgos = None
        mejor_epoca = 0

        for epoca in range(1, epocas + 1):
            generador.barajar(indices)
            for inicio in range(0, len(indices), tamano_lote):
                lote = indices[inicio:inicio + tamano_lote]
                gW, gb = self.gradientes([X[i] for i in lote], [Y[i] for i in lote], l2)

                for l in range(len(self.pesos)):
                    W, V, G = self.pesos[l], vW[l], gW[l]
                    for i in range(len(W)):
                        for j in range(len(W[i])):
                            V[i][j] = momento * V[i][j] - tasa * G[i][j]
                            W[i][j] += V[i][j]
                        vb[l][i] = momento * vb[l][i] - tasa * gb[l][i]
                        self.sesgos[l][i] += vb[l][i]

            historial.append(self.perdida(X, Y, l2))
            if mejor_perdida is None or historial[-1] < mejor_perdida:
                mejor_perdida = historial[-1]
                mejor_epoca = epoca
                mejores_pesos = [[fila[:] for fila in W] for W in self.pesos]
                mejores_sesgos = [b[:] for b in self.sesgos]

            if mostrar_cada and epoca % mostrar_cada == 0:
                print(f"    Epoca {epoca}/{epocas} - perdida: {historial[-1]:.4f}")

        if restaurar_mejor and mejores_pesos is not None:
            self.pesos = mejores_pesos
            self.sesgos = mejores_sesgos
            if mostrar_cada:
                print(f"    Se conservan los pesos de la epoca {mejor_epoca} "
                      f"(perdida {mejor_perdida:.4f})")

        return historial

    # ----------------------------------------------------------
    # Guardar y cargar (texto plano)
    # ----------------------------------------------------------

    def a_lineas(self):
        lineas = ["capas;" + ";".join(str(t) for t in self.tamanos)]
        for l, (W, b) in enumerate(zip(self.pesos, self.sesgos)):
            for fila in W:
                lineas.append(f"W{l};" + ";".join(repr(v) for v in fila))
            lineas.append(f"b{l};" + ";".join(repr(v) for v in b))
        return lineas

    @classmethod
    def desde_lineas(cls, lineas):
        tamanos = None
        filas_W = {}
        sesgos = {}
        for linea in lineas:
            partes = linea.split(";")
            clave, valores = partes[0], partes[1:]
            if clave == "capas":
                tamanos = [int(v) for v in valores]
            elif clave.startswith("W"):
                filas_W.setdefault(int(clave[1:]), []).append([float(v) for v in valores])
            elif clave.startswith("b"):
                sesgos[int(clave[1:])] = [float(v) for v in valores]

        if tamanos is None:
            raise ValueError("El archivo no contiene la linea 'capas'.")
        red = cls(tamanos)
        for l in range(len(tamanos) - 1):
            red.pesos[l] = filas_W[l]
            red.sesgos[l] = sesgos[l]
        return red


def cargar_lineas_modelo(ruta):
    return leer_lineas(ruta)
