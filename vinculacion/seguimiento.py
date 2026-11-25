# ==============================================================
# SEGUIMIENTO VOLUNTARIO ENTRE SESIONES
# ==============================================================
#
# El paciente registra despues de cada sesion:
#   fecha (AAAA-MM-DD), animo (1 a 10), sueno (horas por noche, 0 a 24),
#   acontecimiento (texto libre, opcional) y si lo comparte.
#
# Analisis por variable x_1 ... x_n (en orden de sesion):
#
#  a) Cambio reciente. Con R = SESIONES_RECIENTES:
#        Delta = media(x_{n-R+1} ... x_n) - media(x_1 ... x_{n-R})
#     Se marca si |Delta| >= UMBRAL_CAMBIO[variable].
#     Requiere al menos R + SESIONES_ANTERIORES_MINIMAS registros.
#
#  b) Tendencia general: pendiente de minimos cuadrados con t = 1..n
#        b = sum (t - t_media)(x - x_media) / sum (t - t_media)^2
#     Unidades: puntos (o horas) por sesion.
#
# Los resultados se presentan como DATOS INFORMATIVOS para el
# profesional. El sistema no saca conclusiones clinicas.
#
# Complejidad: O(n) por variable.
# ==============================================================

import config
from nucleo.matematicas import media
from vinculacion.almacen import leer_registros, guardar_registros, siguiente_id, limpiar_valor

VARIABLES = {
    "animo": ("Ánimo (1-10)", 1.0, 10.0, "puntos"),
    "sueno": ("Sueño (horas)", 0.0, 24.0, "horas"),
}

COMENTARIO_SEGUIMIENTO = "Registros voluntarios entre sesiones. Datos personales: no subir."


def es_bisiesto(anio):
    return anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0)


def validar_fecha(texto):
    """
    Valida 'AAAA-MM-DD' sin modulos externos. Devuelve la misma cadena
    o lanza ValueError. (Sin el modulo time no se puede comparar con la
    fecha actual; se pide al usuario.)
    """
    partes = texto.strip().split("-")
    if len(partes) != 3 or not all(p.isdigit() for p in partes) or len(partes[0]) != 4:
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD, por ejemplo 2026-11-24.")
    anio, mes, dia = int(partes[0]), int(partes[1]), int(partes[2])
    if not 1 <= mes <= 12:
        raise ValueError("El mes debe estar entre 1 y 12.")
    dias_mes = [31, 29 if es_bisiesto(anio) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if not 1 <= dia <= dias_mes[mes - 1]:
        raise ValueError(f"El mes {mes} de {anio} no tiene el día {dia}.")
    return f"{anio:04d}-{mes:02d}-{dia:02d}"


def validar_valor(variable, texto):
    nombre, minimo, maximo, _ = VARIABLES[variable]
    try:
        valor = float(texto.replace(",", "."))
    except ValueError:
        raise ValueError(f"{nombre}: escribe un número.")
    if not minimo <= valor <= maximo:
        raise ValueError(f"{nombre}: debe estar entre {minimo:g} y {maximo:g}.")
    return valor


def registrar(id_paciente, fecha, animo, sueno, acontecimiento="", compartir=True, ruta=None):
    """Valida y guarda un registro. Devuelve su ID (SE####)."""
    ruta = ruta or config.REGISTRO_SEGUIMIENTO
    fecha = validar_fecha(fecha)
    animo = validar_valor("animo", str(animo))
    sueno = validar_valor("sueno", str(sueno))
    registros = leer_registros(ruta)
    identificador = siguiente_id(registros, "SE", 4)
    registros.append({"id": identificador, "paciente": id_paciente, "fecha": fecha,
                      "animo": f"{animo:g}", "sueno": f"{sueno:g}",
                      "acontecimiento": limpiar_valor(acontecimiento),
                      "compartir": "si" if compartir else "no"})
    guardar_registros(ruta, registros, COMENTARIO_SEGUIMIENTO)
    return identificador


def registros_de(id_paciente, solo_compartidos=False, ruta=None):
    """Registros del paciente en orden de fecha (y de captura si hay empate)."""
    registros = [r for r in leer_registros(ruta or config.REGISTRO_SEGUIMIENTO)
                 if r["paciente"] == id_paciente]
    if solo_compartidos:
        registros = [r for r in registros if r.get("compartir") == "si"]
    return sorted(registros, key=lambda r: (r["fecha"], r["id"]))


def pendiente_minimos_cuadrados(valores):
    """Pendiente b de la recta x = a + b t con t = 1..n. Requiere n >= 2."""
    n = len(valores)
    if n < 2:
        raise ValueError("Se necesitan al menos 2 valores para la pendiente.")
    t_media = (n + 1) / 2
    x_media = media(valores)
    numerador = sum((t - t_media) * (x - x_media) for t, x in zip(range(1, n + 1), valores))
    denominador = sum((t - t_media) ** 2 for t in range(1, n + 1))
    return numerador / denominador


def analizar_variable(variable, valores):
    """
    Devuelve un diccionario con la pendiente, el cambio reciente y un
    mensaje neutral. 'marcado' indica si el cambio supera el umbral.
    """
    nombre, _, _, unidad = VARIABLES[variable]
    recientes = config.SESIONES_RECIENTES
    minimo = recientes + config.SESIONES_ANTERIORES_MINIMAS
    resultado = {"variable": variable, "nombre": nombre, "n": len(valores),
                 "pendiente": None, "delta": None, "marcado": False}
    if len(valores) >= 2:
        resultado["pendiente"] = pendiente_minimos_cuadrados(valores)
    if len(valores) < minimo:
        resultado["mensaje"] = (f"{nombre}: hay {len(valores)} registros; se necesitan al menos "
                                f"{minimo} para comparar las últimas {recientes} sesiones.")
        return resultado

    delta = media(valores[-recientes:]) - media(valores[:-recientes])
    resultado["delta"] = delta
    resultado["marcado"] = abs(delta) >= config.UMBRAL_CAMBIO[variable]
    direccion = "subió" if delta > 0 else "bajó"
    if resultado["marcado"]:
        resultado["mensaje"] = (f"{nombre}: el promedio de las últimas {recientes} sesiones "
                                f"{direccion} {abs(delta):.1f} {unidad} respecto a las anteriores. "
                                "Dato informativo para revisar en consulta; no es una conclusión clínica.")
    else:
        resultado["mensaje"] = (f"{nombre}: sin cambios mayores a {config.UMBRAL_CAMBIO[variable]:g} "
                                f"{unidad} en las últimas {recientes} sesiones "
                                f"(diferencia {delta:+.1f}).")
    return resultado


def analizar_paciente(id_paciente, solo_compartidos=True, ruta=None):
    registros = registros_de(id_paciente, solo_compartidos, ruta)
    series = {v: [float(r[v]) for r in registros] for v in VARIABLES}
    return {
        "registros": registros,
        "series": series,
        "analisis": [analizar_variable(v, series[v]) for v in VARIABLES],
    }
