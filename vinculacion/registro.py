# ==============================================================
# REGISTRO DE PSICOLOGOS Y PACIENTES
# ==============================================================
#
# Psicologo (datos/psicologos.txt, se edita a mano o con el menu):
#   nombre, formacion, cedula, enfoque, poblacion
#   areas      -> experiencia por tema, pesos en [0, 1]
#   idiomas, modalidad, horarios -> listas
#   costo      -> pesos por sesion (0 = gratuito)
#   acepta_pacientes -> si / no
#
# Paciente (datos/pacientes.txt, lo crea el flujo de orientacion):
#   alias (no se pide el nombre completo: minimizacion de datos),
#   motivo inferido y probabilidades por tema, duracion, contextos,
#   prioridad, preferencias y consentimiento para compartir.
#   El relato completo solo se guarda si la persona autoriza
#   compartirlo con un profesional.
# ==============================================================

import config
from vinculacion.geografia import ALCALDIAS
from vinculacion.almacen import (
    leer_registros, guardar_registros, siguiente_id, buscar,
    a_lista, de_lista, a_pesos, de_pesos
)

COMENTARIO_PSICOLOGOS = (
    "Perfiles FICTICIOS para el prototipo académico. No corresponden a personas reales.\n"
    "areas: experiencia por tema entre 0 y 1. Temas válidos: "
    + ", ".join(config.CATEGORIAS_MOTIVO) + "\n"
    "costo: pesos por sesión (0 = gratuito). alcaldia: ubicación ficticia del consultorio."
)
COMENTARIO_PACIENTES = ("Perfiles preliminares de orientación (NO diagnósticos). "
                        "Contiene datos personales: no subir a repositorios.")


def _verificar_opciones(valores, validas, campo, identificador):
    desconocidas = [v for v in valores if v not in validas]
    if desconocidas:
        raise ValueError(f"{identificador}: valor no válido en '{campo}': {desconocidas}. "
                         f"Opciones: {validas}")


def validar_psicologo(registro):
    """
    Convierte el registro de texto en un diccionario con tipos.
    Lanza ValueError con un mensaje claro si falta o sobra algo.
    """
    identificador = registro.get("id", "?")
    obligatorios = ["nombre", "areas", "idiomas", "modalidad", "horarios", "costo"]
    faltantes = [c for c in obligatorios if not registro.get(c)]
    if faltantes:
        raise ValueError(f"{identificador}: faltan los campos {faltantes}.")

    areas = a_pesos(registro["areas"])
    _verificar_opciones(list(areas), list(config.CATEGORIAS_MOTIVO), "areas", identificador)
    if not any(peso > 0 for peso in areas.values()):
        raise ValueError(f"{identificador}: debe tener al menos un área con peso mayor a 0.")

    idiomas = a_lista(registro["idiomas"])
    modalidad = a_lista(registro["modalidad"])
    horarios = a_lista(registro["horarios"])
    _verificar_opciones(idiomas, config.IDIOMAS, "idiomas", identificador)
    _verificar_opciones(modalidad, config.MODALIDADES, "modalidad", identificador)
    _verificar_opciones(horarios, config.HORARIOS, "horarios", identificador)

    alcaldia = registro.get("alcaldia", "")
    if alcaldia and alcaldia not in ALCALDIAS:
        raise ValueError(f"{identificador}: alcaldía desconocida '{alcaldia}'. Opciones: {list(ALCALDIAS)}")

    if not registro["costo"].isdigit():
        raise ValueError(f"{identificador}: 'costo' debe ser un entero mayor o igual a 0.")

    return {
        "id": identificador,
        "nombre": registro["nombre"],
        "formacion": registro.get("formacion", ""),
        "cedula": registro.get("cedula", "validación pendiente (prototipo)"),
        "enfoque": registro.get("enfoque", ""),
        "poblacion": registro.get("poblacion", ""),
        "alcaldia": alcaldia,
        "areas": areas,
        "idiomas": idiomas,
        "modalidad": modalidad,
        "horarios": horarios,
        "costo": int(registro["costo"]),
        "acepta_pacientes": registro.get("acepta_pacientes", "si") == "si",
    }


def cargar_psicologos(ruta=None, solo_disponibles=False):
    ruta = ruta or config.REGISTRO_PSICOLOGOS
    psicologos = [validar_psicologo(r) for r in leer_registros(ruta)]
    if solo_disponibles:
        psicologos = [p for p in psicologos if p["acepta_pacientes"]]
    return psicologos


def psicologo_a_registro(p):
    return {
        "id": p["id"], "nombre": p["nombre"], "formacion": p["formacion"],
        "cedula": p["cedula"], "enfoque": p["enfoque"], "poblacion": p["poblacion"],
        "alcaldia": p["alcaldia"],
        "areas": de_pesos(p["areas"]), "idiomas": de_lista(p["idiomas"]),
        "modalidad": de_lista(p["modalidad"]), "horarios": de_lista(p["horarios"]),
        "costo": str(p["costo"]), "acepta_pacientes": "si" if p["acepta_pacientes"] else "no",
    }


def registrar_psicologo(datos, ruta=None):
    """Valida, asigna un ID nuevo (PS##) y guarda. Devuelve el ID."""
    ruta = ruta or config.REGISTRO_PSICOLOGOS
    registros = leer_registros(ruta)
    datos = dict(datos)
    datos["id"] = siguiente_id(registros, "PS", 2)
    psicologo = validar_psicologo(datos)          # lanza ValueError si algo esta mal
    registros.append(psicologo_a_registro(psicologo))
    guardar_registros(ruta, registros, COMENTARIO_PSICOLOGOS)
    return datos["id"]


# --------------------------------------------------------------
# Pacientes
# --------------------------------------------------------------

def registrar_paciente(perfil, ruta=None):
    """
    perfil: diccionario producido por el flujo de orientacion.
    Devuelve el ID asignado (PA###).
    """
    ruta = ruta or config.REGISTRO_PACIENTES
    registros = leer_registros(ruta)
    identificador = siguiente_id(registros, "PA", 3)
    probabilidades = perfil["probabilidades"]
    if len(probabilidades) != len(config.CATEGORIAS_MOTIVO):
        raise ValueError("El vector de probabilidades no coincide con las categorías.")
    registro = {
        "id": identificador,
        "alias": perfil.get("alias") or identificador,
        "motivo_principal": perfil["motivo_principal"],
        "motivos_secundarios": de_lista(perfil.get("motivos_secundarios", [])),
        "motivo_confirmado": perfil.get("motivo_confirmado", "sin respuesta"),
        "probabilidades": de_pesos(dict(zip(config.CATEGORIAS_MOTIVO, probabilidades))),
        "duracion_dias": str(perfil.get("duracion_dias", "")),
        "contextos": de_lista(perfil.get("contextos", [])),
        "prioridad": perfil.get("prioridad", "ordinario"),
        "emocion_voz": perfil.get("emocion_voz", ""),
        "palabra_voz": perfil.get("palabra_voz", ""),
        "modalidad": perfil["preferencias"]["modalidad"],
        "horario": perfil["preferencias"]["horario"],
        "costo_maximo": str(perfil["preferencias"]["costo_maximo"]),
        "idioma": perfil["preferencias"]["idioma"],
        "alcaldia": perfil["preferencias"].get("alcaldia", ""),
        "consentimiento_compartir": "si" if perfil.get("compartir") else "no",
    }
    # El relato solo se conserva si la persona autorizo compartirlo
    if perfil.get("compartir") and perfil.get("relato"):
        registro["relato"] = perfil["relato"]
    registros.append(registro)
    guardar_registros(ruta, registros, COMENTARIO_PACIENTES)
    return identificador


def cargar_paciente(identificador, ruta=None):
    """Devuelve el paciente con tipos convertidos, o None si no existe."""
    registro = buscar(leer_registros(ruta or config.REGISTRO_PACIENTES), identificador)
    if registro is None:
        return None
    pesos = a_pesos(registro.get("probabilidades", ""))
    paciente = dict(registro)
    paciente["probabilidades"] = [pesos.get(c, 0.0) for c in config.CATEGORIAS_MOTIVO]
    paciente["motivos_secundarios"] = a_lista(registro.get("motivos_secundarios", ""))
    paciente["contextos"] = a_lista(registro.get("contextos", ""))
    paciente["costo_maximo"] = int(registro.get("costo_maximo", "0") or 0)
    duracion = registro.get("duracion_dias", "")
    paciente["duracion_dias"] = int(duracion) if duracion.isdigit() else None
    paciente["consentimiento_compartir"] = registro.get("consentimiento_compartir") == "si"
    return paciente


def actualizar_paciente(identificador, cambios, ruta=None):
    """Modifica campos de un paciente (por ejemplo, revocar consentimiento)."""
    ruta = ruta or config.REGISTRO_PACIENTES
    registros = leer_registros(ruta)
    registro = buscar(registros, identificador)
    if registro is None:
        raise ValueError(f"No existe el paciente {identificador}.")
    for clave, valor in cambios.items():
        if valor is None:
            registro.pop(clave, None)
        else:
            registro[clave] = valor
    guardar_registros(ruta, registros, COMENTARIO_PACIENTES)
