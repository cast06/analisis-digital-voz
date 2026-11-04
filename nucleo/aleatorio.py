# ==============================================================
# GENERADOR PSEUDOALEATORIO PROPIO (CONGRUENCIAL LINEAL)
# ==============================================================
#
#   x_{n+1} = (a x_n + c) mod m
#   a = 6364136223846793005, c = 1442695040888963407, m = 2^64
#   (constantes de Knuth para MMIX)
#
# Con la misma semilla siempre se obtiene la misma secuencia, lo
# que hace reproducibles la inicializacion de pesos y las
# particiones de entrenamiento y prueba.
# ==============================================================

from nucleo.matematicas import raiz_cuadrada, logaritmo_natural, coseno, DOS_PI

_A = 6364136223846793005
_C = 1442695040888963407
_M = 1 << 64


class GeneradorAleatorio:

    def __init__(self, semilla=42):
        self.estado = semilla % _M

    def siguiente_entero(self):
        self.estado = (_A * self.estado + _C) % _M
        # Los bits altos tienen mejor calidad estadistica en un LCG
        return self.estado >> 11

    def uniforme(self, minimo=0.0, maximo=1.0):
        """Numero real en [minimo, maximo)."""
        u = self.siguiente_entero() / float(1 << 53)
        return minimo + (maximo - minimo) * u

    def normal(self, media=0.0, desviacion=1.0):
        """
        Distribucion normal por el metodo de Box-Muller:
            z = sqrt(-2 ln u1) cos(2 pi u2)
        """
        u1 = self.uniforme()
        while u1 <= 1e-300:
            u1 = self.uniforme()
        u2 = self.uniforme()
        z = raiz_cuadrada(-2.0 * logaritmo_natural(u1)) * coseno(DOS_PI * u2)
        return media + desviacion * z

    def barajar(self, lista):
        """Algoritmo de Fisher-Yates. Modifica la lista y la devuelve."""
        for i in range(len(lista) - 1, 0, -1):
            j = self.siguiente_entero() % (i + 1)
            lista[i], lista[j] = lista[j], lista[i]
        return lista
