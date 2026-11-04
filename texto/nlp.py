# ==============================================================
# PROCESAMIENTO DE LENGUAJE NATURAL DESDE CERO
# ==============================================================
#
# Pasos para convertir una frase en un vector:
#
# 1. Normalizacion: minusculas, sin acentos (á -> a), ñ -> n.
#    Asi "sueño" y "sueno" (escrito sin ñ) quedan iguales.
# 2. Tokenizacion: se separan palabras; los signos . , ; : ! ?
#    marcan el fin de una clausula.
# 3. Negacion: despues de "no", "nunca", "jamas", "tampoco", "ni"
#    o "sin", las siguientes 3 palabras con contenido llevan el
#    prefijo "no_" hasta el fin de la clausula o hasta una palabra
#    como "pero", "porque", "desde" o "y".
#       "no duermo bien" -> no_duerm, no_bien
#    Asi el modelo distingue "duermo bien" de "no duermo bien".
# 4. Palabras vacias: se quitan articulos, preposiciones, etc.
# 5. Raiz (stemming ligero): se quitan sufijos frecuentes.
#       "preocupada", "preocupado", "preocupaciones" -> "preocup"
# 6. N-gramas: palabras sueltas y pares consecutivos (bigramas).
# 7. TF-IDF:
#       tf(t, d)  = veces que aparece t en d / terminos de d
#       idf(t)    = ln((1 + N) / (1 + df(t))) + 1
#       x_t       = tf * idf, despues se normaliza ||x|| = 1
#    Las palabras que aparecen en casi todas las frases pesan menos.
#
# Los vectores TF-IDF se guardan como diccionarios {indice: valor}
# (representacion dispersa) porque casi todos sus valores son 0.
# ==============================================================

from nucleo.matematicas import logaritmo_natural, raiz_cuadrada

_SIN_ACENTO = {
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
    "à": "a", "è": "e", "ì": "i", "ò": "o", "ù": "u"
}
_FIN_CLAUSULA = ".,;:!?¡¿\n"
FIN = "<fin>"

NEGADORES = {"no", "nunca", "jamas", "tampoco", "ni", "sin"}
ALCANCE_NEGACION = 3
# Palabras que terminan el alcance de una negacion
CORTAN_NEGACION = {"pero", "porque", "aunque", "sino", "desde", "hace", "y", "e",
                   "cuando", "mientras", "entonces", "pues"}

# Lista propia de palabras vacias. NO incluye negadores ni palabras
# como "todo", "nada", "nadie", "solo" que cambian el sentido.
PALABRAS_VACIAS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "lo", "al", "del",
    "de", "a", "en", "con", "por", "para", "entre", "sobre", "hacia", "hasta", "desde",
    "y", "e", "o", "u", "que", "pero", "porque", "pues", "como", "cuando", "donde",
    "si", "ya", "muy", "mas", "tan", "tanto", "tambien", "aun", "asi", "bien",
    "me", "mi", "mis", "yo", "te", "tu", "tus", "se", "su", "sus", "le", "les",
    "nos", "nuestro", "nuestra", "este", "esta", "estos", "estas", "ese", "esa",
    "esos", "esas", "eso", "esto", "aqui", "alli", "ahi",
    "es", "son", "soy", "eres", "fue", "era", "ser", "estoy", "esta", "estan",
    "estar", "he", "ha", "han", "hay", "haber", "tengo", "tiene", "tener",
    "hace", "hacer", "algo", "alguien", "cada", "otro", "otra", "otros", "otras",
    "mucho", "mucha", "muchos", "muchas", "poco", "poca", "pocos", "pocas",
    "ahora", "hoy", "ayer", "dia", "dias", "veces", "vez", "tiempo", "siento", "sentir",
    "eh", "pues", "bueno", "osea", "verdad"
}

# Sufijos ordenados del mas largo al mas corto
_SUFIJOS = sorted([
    "amientos", "imientos", "amiento", "imiento", "aciones", "uciones", "acion", "ucion",
    "arme", "erme", "irme", "arse", "erse", "irse", "arte", "erte", "irte",
    "mente", "idades", "idad", "ancias", "ancia", "encias", "encia",
    "ismos", "ismo", "istas", "ista", "ables", "able", "ibles", "ible",
    "osos", "osas", "oso", "osa", "ando", "iendo", "aron", "ieron",
    "amos", "emos", "imos", "aban", "aba", "ados", "adas", "ado", "ada",
    "idos", "idas", "ido", "ida", "ar", "er", "ir", "as", "es", "os", "a", "e", "o", "s"
], key=len, reverse=True)
_LARGO_MINIMO_RAIZ = 3


def normalizar_texto(texto):
    return "".join(_SIN_ACENTO.get(c, c) for c in texto.lower())


def tokenizar(texto):
    """Devuelve palabras normalizadas y la marca <fin> entre clausulas."""
    tokens = []
    actual = ""
    for c in normalizar_texto(texto):
        if ("a" <= c <= "z") or ("0" <= c <= "9"):
            actual += c
        else:
            if actual:
                tokens.append(actual)
                actual = ""
            if c in _FIN_CLAUSULA and tokens and tokens[-1] != FIN:
                tokens.append(FIN)
    if actual:
        tokens.append(actual)
    return tokens


def raiz(palabra):
    """Stemming ligero: quita el sufijo mas largo que deje una raiz de 3+ letras."""
    for sufijo in _SUFIJOS:
        if palabra.endswith(sufijo) and len(palabra) - len(sufijo) >= _LARGO_MINIMO_RAIZ:
            return palabra[:-len(sufijo)]
    return palabra


def terminos(texto):
    """
    Lista de terminos de contenido: sin palabras vacias, con raiz y con
    la marca de negacion aplicada.
    """
    resultado = []
    negacion_restante = 0
    for token in tokenizar(texto):
        if token == FIN:
            negacion_restante = 0
            continue
        if token in NEGADORES:
            negacion_restante = ALCANCE_NEGACION
            continue
        if token in CORTAN_NEGACION:
            negacion_restante = 0
        if token in PALABRAS_VACIAS:
            continue
        termino = raiz(token)
        if negacion_restante > 0:
            termino = "no_" + termino
            negacion_restante -= 1
        resultado.append(termino)
    return resultado


def ngramas(texto, n_max=2):
    """Unigramas y bigramas de los terminos de contenido."""
    base = terminos(texto)
    resultado = base[:]
    if n_max >= 2:
        resultado += [base[i] + "_" + base[i + 1] for i in range(len(base) - 1)]
    return resultado


# --------------------------------------------------------------
# TF-IDF
# --------------------------------------------------------------


class VectorizadorTFIDF:

    def __init__(self, frecuencia_minima=2, n_max=2):
        self.frecuencia_minima = frecuencia_minima
        self.n_max = n_max
        self.vocabulario = {}     # termino -> indice
        self.idf = []

    def ajustar(self, textos):
        """Construye el vocabulario y el idf con los textos de entrenamiento."""
        if not textos:
            raise ValueError("Se necesitan textos para construir el vocabulario.")
        frecuencia_documental = {}
        for texto in textos:
            for termino in set(ngramas(texto, self.n_max)):
                frecuencia_documental[termino] = frecuencia_documental.get(termino, 0) + 1

        seleccionados = sorted(t for t, df in frecuencia_documental.items()
                               if df >= self.frecuencia_minima)
        self.vocabulario = {t: i for i, t in enumerate(seleccionados)}
        n = len(textos)
        self.idf = [logaritmo_natural((1 + n) / (1 + frecuencia_documental[t])) + 1.0
                    for t in seleccionados]
        return self

    def conteos(self, texto):
        """{indice: veces} solo de terminos del vocabulario."""
        resultado = {}
        for termino in ngramas(texto, self.n_max):
            indice = self.vocabulario.get(termino)
            if indice is not None:
                resultado[indice] = resultado.get(indice, 0) + 1
        return resultado

    def transformar(self, texto):
        """Vector TF-IDF disperso y normalizado: {indice: valor}."""
        conteo = self.conteos(texto)
        total = sum(conteo.values())
        if total == 0:
            return {}
        vector = {i: (c / total) * self.idf[i] for i, c in conteo.items()}
        norma = raiz_cuadrada(sum(v * v for v in vector.values()))
        return {i: v / norma for i, v in vector.items()}

    def tamano(self):
        return len(self.vocabulario)

    def a_lineas(self):
        terminos_ordenados = sorted(self.vocabulario, key=self.vocabulario.get)
        return [
            f"tfidf;{self.frecuencia_minima};{self.n_max}",
            "vocabulario;" + ";".join(terminos_ordenados),
            "idf;" + ";".join(repr(v) for v in self.idf)
        ]

    @classmethod
    def desde_lineas(cls, lineas):
        vectorizador = cls()
        for linea in lineas:
            clave, _, resto = linea.partition(";")
            valores = resto.split(";") if resto else []
            if clave == "tfidf":
                vectorizador.frecuencia_minima = int(valores[0])
                vectorizador.n_max = int(valores[1])
            elif clave == "vocabulario":
                vectorizador.vocabulario = {t: i for i, t in enumerate(valores)}
            elif clave == "idf":
                vectorizador.idf = [float(v) for v in valores]
        return vectorizador
