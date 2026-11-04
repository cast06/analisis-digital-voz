# ==============================================================
# NAIVE BAYES MULTINOMIAL DESDE CERO (LINEA BASE PARA TEXTO)
# ==============================================================
#
# Supone que, dada la clase, cada termino aparece de forma
# independiente:
#
#   P(c | d) ∝ P(c) * prod_t P(t | c)^{n_t}
#
# Se trabaja con logaritmos para evitar numeros muy pequeños:
#
#   log P(c | d) = log P(c) + sum_t n_t log P(t | c) + constante
#
#   P(c)     = documentos de c / documentos totales
#   P(t | c) = (conteo de t en c + alfa) / (terminos en c + alfa |V|)
#
# alfa = 1 es el suavizado de Laplace: evita probabilidad 0 para
# terminos que no aparecieron en una clase durante el entrenamiento.
# ==============================================================

from nucleo.matematicas import logaritmo_natural, softmax, indice_maximo


class NaiveBayesMultinomial:

    def __init__(self, alfa=1.0):
        if alfa <= 0:
            raise ValueError("El suavizado alfa debe ser positivo.")
        self.alfa = alfa
        self.log_prior = []
        self.log_verosimilitud = []   # [clase][termino]

    def entrenar(self, conteos, Y, numero_clases, numero_terminos):
        """conteos: lista de diccionarios {indice_termino: veces}."""
        if len(conteos) != len(Y) or not conteos:
            raise ValueError("Conteos y etiquetas deben tener la misma longitud.")

        documentos = [0] * numero_clases
        totales = [[0.0] * numero_terminos for _ in range(numero_clases)]
        for conteo, y in zip(conteos, Y):
            documentos[y] += 1
            for t, n in conteo.items():
                totales[y][t] += n

        n_docs = len(Y)
        self.log_prior = [logaritmo_natural((d + 1e-12) / n_docs) for d in documentos]
        self.log_verosimilitud = []
        for c in range(numero_clases):
            denominador = sum(totales[c]) + self.alfa * numero_terminos
            self.log_verosimilitud.append(
                [logaritmo_natural((totales[c][t] + self.alfa) / denominador)
                 for t in range(numero_terminos)]
            )
        return self

    def puntajes(self, conteo):
        return [
            self.log_prior[c] + sum(n * self.log_verosimilitud[c][t] for t, n in conteo.items())
            for c in range(len(self.log_prior))
        ]

    def predecir_probabilidades(self, conteo):
        # softmax de los log-puntajes = probabilidades normalizadas
        return softmax(self.puntajes(conteo))

    def predecir(self, conteo):
        return indice_maximo(self.puntajes(conteo))
