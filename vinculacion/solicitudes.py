# ==============================================================
# SOLICITUDES DE VINCULACION Y RESUMEN PARA EL PROFESIONAL
# ==============================================================
#
# Una solicitud une a un paciente con el psicologo que ELIGIO.
# Estados:  pendiente -> aceptada | rechazada
#
# El resumen de la entrevista solo se genera si el paciente
# autorizo compartirlo. Siempre incluye el aviso de que se genero
# automaticamente y no es un diagnostico. Si despues el paciente
# revoca el permiso, el resumen deja de mostrarse en el panel.
# ==============================================================

import config
from vinculacion.almacen import leer_registros, guardar_registros, siguiente_id, buscar
from vinculacion.registro import cargar_paciente, actualizar_paciente
from texto.extraccion import describir_duracion

ESTADOS = ["pendiente", "aceptada", "rechazada"]

AVISO_RESUMEN = ("Este resumen fue GENERADO AUTOMÁTICAMENTE a partir de lo que la persona "
                 "expresó en la entrevista inicial. NO constituye un diagnóstico y debe ser "
                 "validado por el profesional durante la consulta.")

COMENTARIO_SOLICITUDES = "Solicitudes de vinculación paciente-psicólogo. Datos personales: no subir."


def generar_resumen(paciente, compatibilidad=None):
    """
    Resumen estructurado para el profesional.
    Lanza PermissionError si el paciente no autorizo compartir.
    Separa lo que la persona dijo de lo que el sistema infiere.
    """
    if not paciente.get("consentimiento_compartir"):
        raise PermissionError("El paciente no autorizó compartir su información.")
    nombres = config.CATEGORIAS_MOTIVO
    duracion = paciente.get("duracion_dias")
    lineas = [
        "RESUMEN DE ENTREVISTA INICIAL",
        AVISO_RESUMEN,
        "",
        f"Paciente: {paciente['alias']} ({paciente['id']})",
        "",
        "LO QUE LA PERSONA EXPRESÓ",
        f"  Relato: {paciente.get('relato', '(no disponible)')}",
        f"  Duración mencionada: {describir_duracion(duracion) if duracion else 'No mencionada'}",
        f"  Contextos mencionados: {', '.join(paciente['contextos']) or 'Ninguno identificado'}",
        "",
        "LO QUE EL SISTEMA INFIERE (por confirmar)",
        f"  Motivo principal: {nombres.get(paciente['motivo_principal'], paciente['motivo_principal'])}",
    ]
    confirmado = {"si": "la persona confirmó este tema",
                  "corregido": "la persona eligió este tema al corregir al sistema"}.get(
        paciente.get("motivo_confirmado", ""), "la persona no lo confirmó")
    lineas.append(f"  Confirmación: {confirmado}")
    if paciente["motivos_secundarios"]:
        lineas.append("  Motivos secundarios: "
                      + ", ".join(nombres.get(m, m) for m in paciente["motivos_secundarios"]))
    lineas.append(f"  Nivel de prioridad del flujo: {paciente.get('prioridad', 'ordinario')}")
    if paciente.get("emocion_voz"):
        lineas.append(f"  Emoción percibida en la voz: {paciente['emocion_voz']} "
                      "(dato orientativo, no evidencia clínica)")
    lineas += [
        "",
        "PREFERENCIAS",
        f"  Modalidad: {paciente['modalidad']}",
        f"  Horario: {paciente['horario']}",
        f"  Idioma: {paciente['idioma']}",
        f"  Presupuesto por sesión: ${paciente['costo_maximo']}",
    ]
    if compatibilidad is not None:
        lineas.append(f"  Compatibilidad calculada por el sistema: {compatibilidad * 100:.0f} %")
    return "\n".join(lineas)


def crear_solicitud(id_paciente, id_psicologo, compatibilidad, ruta=None):
    """Registra la solicitud en estado pendiente. Devuelve su ID (SO###)."""
    ruta = ruta or config.REGISTRO_SOLICITUDES
    if not 0.0 <= compatibilidad <= 1.0:
        raise ValueError("La compatibilidad debe estar entre 0 y 1.")
    registros = leer_registros(ruta)
    for r in registros:
        if r["paciente"] == id_paciente and r["psicologo"] == id_psicologo and r["estado"] == "pendiente":
            raise ValueError("Ya existe una solicitud pendiente con ese profesional.")
    identificador = siguiente_id(registros, "SO", 3)
    registros.append({"id": identificador, "paciente": id_paciente, "psicologo": id_psicologo,
                      "estado": "pendiente", "compatibilidad": f"{compatibilidad:.4f}"})
    guardar_registros(ruta, registros, COMENTARIO_SOLICITUDES)
    return identificador


def solicitudes_de(id_psicologo, ruta=None):
    return [r for r in leer_registros(ruta or config.REGISTRO_SOLICITUDES)
            if r["psicologo"] == id_psicologo]


def cambiar_estado(id_solicitud, estado, ruta=None):
    """Solo una solicitud pendiente puede aceptarse o rechazarse."""
    ruta = ruta or config.REGISTRO_SOLICITUDES
    if estado not in ("aceptada", "rechazada"):
        raise ValueError("El estado nuevo debe ser 'aceptada' o 'rechazada'.")
    registros = leer_registros(ruta)
    solicitud = buscar(registros, id_solicitud)
    if solicitud is None:
        raise ValueError(f"No existe la solicitud {id_solicitud}.")
    if solicitud["estado"] != "pendiente":
        raise ValueError(f"La solicitud ya está {solicitud['estado']}.")
    solicitud["estado"] = estado
    guardar_registros(ruta, registros, COMENTARIO_SOLICITUDES)


def resumen_autorizado(solicitud, ruta_pacientes=None):
    """
    Devuelve el resumen si el paciente sigue autorizando compartirlo;
    si no, devuelve None. Se consulta cada vez: si el paciente revoca
    el permiso, el profesional deja de verlo.
    """
    paciente = cargar_paciente(solicitud["paciente"], ruta_pacientes)
    if paciente is None or not paciente["consentimiento_compartir"]:
        return None
    return generar_resumen(paciente, float(solicitud["compatibilidad"]))


def revocar_consentimiento(id_paciente, ruta=None):
    """Retira el permiso y borra el relato guardado del registro."""
    actualizar_paciente(id_paciente, {"consentimiento_compartir": "no", "relato": None}, ruta)
