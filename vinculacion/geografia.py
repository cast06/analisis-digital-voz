# ==============================================================
# UBICACION APROXIMADA Y DISTANCIA (SIN LIBRERIAS)
# ==============================================================
#
# Privacidad: la ubicacion del paciente se guarda solo a nivel de
# ALCALDIA (centro aproximado), nunca su direccion.
# Los consultorios de los psicologos ficticios se ubican cerca del
# centro de su alcaldia con un pequeno desplazamiento fijo por ID,
# para que no queden encimados en el mapa.
#
# Distancia (aproximacion equirrectangular), con angulos en radianes:
#     x = (lon2 - lon1) * cos((lat1 + lat2) / 2)
#     y = (lat2 - lat1)
#     d = R * sqrt(x^2 + y^2),   R = 6371 km
# Para distancias dentro de una ciudad (< 50 km) el error frente a la
# formula de Haversine es menor a 0.1 %, y solo necesita coseno y
# raiz cuadrada, que ya estan implementados en nucleo/matematicas.py.
#
# Cercania (solo cuando el paciente quiere atencion presencial):
#     d <= 5 km        -> 1
#     5 < d < 25 km    -> 1 - (d - 5) / 20     (baja en linea recta)
#     d >= 25 km       -> 0
# ==============================================================

from nucleo.matematicas import PI, coseno, raiz_cuadrada

RADIO_TIERRA_KM = 6371.0
DISTANCIA_PLENA_KM = 5.0
DISTANCIA_NULA_KM = 25.0

# Centro aproximado de cada alcaldia de la Ciudad de Mexico (lat, lon).
# Son valores redondeados para el prototipo, no coordenadas oficiales.
ALCALDIAS = {
    "Álvaro Obregón": (19.360, -99.230),
    "Azcapotzalco": (19.487, -99.184),
    "Benito Juárez": (19.372, -99.157),
    "Coyoacán": (19.328, -99.161),
    "Cuajimalpa": (19.357, -99.299),
    "Cuauhtémoc": (19.433, -99.150),
    "Gustavo A. Madero": (19.482, -99.110),
    "Iztacalco": (19.395, -99.097),
    "Iztapalapa": (19.358, -99.060),
    "Magdalena Contreras": (19.315, -99.243),
    "Miguel Hidalgo": (19.433, -99.200),
    "Milpa Alta": (19.192, -99.023),
    "Tláhuac": (19.286, -99.004),
    "Tlalpan": (19.290, -99.170),
    "Venustiano Carranza": (19.430, -99.104),
    "Xochimilco": (19.257, -99.103),
}


def a_radianes(grados):
    return grados * PI / 180.0


def distancia_km(punto1, punto2):
    """Distancia aproximada en km entre dos puntos (lat, lon) en grados."""
    for lat, lon in (punto1, punto2):
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            raise ValueError("Coordenadas fuera de rango.")
    lat1, lon1 = a_radianes(punto1[0]), a_radianes(punto1[1])
    lat2, lon2 = a_radianes(punto2[0]), a_radianes(punto2[1])
    x = (lon2 - lon1) * coseno((lat1 + lat2) / 2.0)
    y = lat2 - lat1
    return RADIO_TIERRA_KM * raiz_cuadrada(x * x + y * y)


def puntaje_cercania(distancia):
    if distancia < 0:
        raise ValueError("La distancia no puede ser negativa.")
    if distancia <= DISTANCIA_PLENA_KM:
        return 1.0
    if distancia >= DISTANCIA_NULA_KM:
        return 0.0
    return 1.0 - (distancia - DISTANCIA_PLENA_KM) / (DISTANCIA_NULA_KM - DISTANCIA_PLENA_KM)


def ubicacion_alcaldia(nombre):
    """Centro aproximado de la alcaldia o None si no se conoce."""
    return ALCALDIAS.get(nombre)


def ubicacion_consultorio(psicologo):
    """
    Punto del consultorio: centro de su alcaldia mas un desplazamiento
    fijo segun su ID (hasta ~1.5 km), para que no se encimen en el mapa.
    """
    centro = ALCALDIAS.get(psicologo.get("alcaldia", ""))
    if centro is None:
        return None
    numero = sum(ord(c) for c in psicologo["id"])
    dlat = ((numero % 7) - 3) * 0.004
    dlon = (((numero // 7) % 7) - 3) * 0.004
    return (centro[0] + dlat, centro[1] + dlon)
