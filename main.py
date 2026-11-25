# ==============================================================
# MENU PRINCIPAL DEL SISTEMA DE ORIENTACION Y VINCULACION
# ==============================================================
#
# Ejecutar desde la carpeta del proyecto:
#     python main.py
#
# Requiere: python entrenar_texto.py (una vez) y el archivo
# datos/psicologos.txt con los perfiles ficticios.
#
# Pacientes:   orientacion, recomendaciones, seguimiento, permisos
# Psicologos:  panel (aceptar/rechazar, ver resumen y seguimiento),
#              registro de nuevos perfiles
# ==============================================================

import config
import orientacion
from orientacion import preguntar
from vinculacion.registro import cargar_paciente, cargar_psicologos, registrar_psicologo
from vinculacion.solicitudes import (
    solicitudes_de, cambiar_estado, resumen_autorizado, revocar_consentimiento
)
from vinculacion.seguimiento import registrar, analizar_paciente, validar_fecha, validar_valor
from vinculacion.panel import generar_panel_html
from visual.portal import generar_inicio
import evaluar_vinculacion

MENU = """
============================================================
 SISTEMA DE ORIENTACIÓN Y VINCULACIÓN PSICOLÓGICA (prototipo)
============================================================
 PACIENTES
  1. Nueva orientación inicial
  2. Ver otra vez profesionales compatibles
  3. Registrar seguimiento entre sesiones
  4. Retirar mi permiso para compartir el resumen
 PSICÓLOGOS
  5. Panel del psicólogo
  6. Registrar un psicólogo
 PÁGINAS
  7. Generar la página de inicio y los paneles (salidas/inicio.html)
 EVALUACIÓN
  8. Evaluar extracción y matching (salidas/reporte_vinculacion.html)
 PÁGINA WEB
  9. Abrir el sistema en el navegador (http://localhost:8000)
  0. Salir
"""


def pedir_paciente():
    identificador = preguntar("Tu número de paciente (por ejemplo PA001): ").upper()
    paciente = cargar_paciente(identificador)
    if paciente is None:
        print("No encontramos ese número.")
    return paciente


def pedir_validado(texto, validar):
    """Repite la pregunta hasta que la funcion validar no lance ValueError."""
    while True:
        try:
            return validar(input(texto).strip())
        except ValueError as error:
            print(" ", error)


def menu_recomendaciones():
    paciente = pedir_paciente()
    if paciente is not None:
        orientacion.recomendar_y_solicitar(paciente["id"])


def menu_seguimiento():
    paciente = pedir_paciente()
    if paciente is None:
        return
    print("\nRegistro voluntario. Solo lo verá tu psicólogo si lo compartes y aceptó tu solicitud.")
    fecha = pedir_validado("  Fecha de la sesión (AAAA-MM-DD): ", validar_fecha)
    animo = pedir_validado("  ¿Cómo estuvo tu ánimo esta semana? (1 = muy bajo, 10 = muy bien): ",
                           lambda t: validar_valor("animo", t))
    sueno = pedir_validado("  ¿Cuántas horas dormiste por noche en promedio? ",
                           lambda t: validar_valor("sueno", t))
    acontecimiento = preguntar("  ¿Algo importante que quieras anotar? (Enter para omitir): ",
                               permitir_vacio=True)
    compartir = preguntar("  ¿Compartir este registro con tu psicólogo? (si / no): ",
                          ["si", "no"]) == "si"
    identificador = registrar(paciente["id"], fecha, animo, sueno, acontecimiento, compartir)
    print(f"Registro {identificador} guardado.")
    for resultado in analizar_paciente(paciente["id"], solo_compartidos=False)["analisis"]:
        print("  ·", resultado["mensaje"])


def menu_revocar():
    paciente = pedir_paciente()
    if paciente is None:
        return
    if not paciente["consentimiento_compartir"]:
        print("Ya no tenías un permiso activo.")
        return
    if preguntar("¿Seguro que quieres retirar el permiso? Tu relato se borrará del registro "
                 "(si / no): ", ["si", "no"]) == "si":
        revocar_consentimiento(paciente["id"])
        print("Permiso retirado. Los profesionales dejarán de ver tu resumen.")


def menu_panel():
    psicologos = {p["id"]: p for p in cargar_psicologos()}
    identificador = preguntar("Tu ID de psicólogo (por ejemplo PS01): ").upper()
    if identificador not in psicologos:
        print("No existe ese ID.")
        return
    while True:
        solicitudes = solicitudes_de(identificador)
        ruta = generar_panel_html(identificador)
        print(f"\nPanel de {psicologos[identificador]['nombre']}  (página: {ruta})")
        if not solicitudes:
            print("  No hay solicitudes.")
            return
        for s in solicitudes:
            print(f"  {s['id']}  paciente {s['paciente']}  {s['estado']}  "
                  f"compatibilidad {float(s['compatibilidad']) * 100:.0f} %")
        id_solicitud = preguntar("ID de solicitud para revisar (Enter para salir): ",
                                 permitir_vacio=True).upper()
        if not id_solicitud:
            return
        solicitud = next((s for s in solicitudes if s["id"] == id_solicitud), None)
        if solicitud is None:
            print("No es una de tus solicitudes.")
            continue
        resumen = resumen_autorizado(solicitud)
        print("\n" + (resumen or "El paciente no autorizó compartir su resumen."))
        if solicitud["estado"] == "pendiente":
            accion = preguntar("\n¿Aceptar, rechazar o dejar pendiente? "
                               "(aceptar / rechazar / pendiente): ",
                               ["aceptar", "rechazar", "pendiente"])
            if accion != "pendiente":
                estado = "aceptada" if accion == "aceptar" else "rechazada"
                cambiar_estado(id_solicitud, estado)
                print(f"Solicitud {estado}.")
        elif solicitud["estado"] == "aceptada":
            for resultado in analizar_paciente(solicitud["paciente"])["analisis"]:
                print("  ·", resultado["mensaje"])


def menu_registrar_psicologo():
    print("\nRegistro de profesional (prototipo: la cédula queda como validación pendiente).")
    temas = ", ".join(config.CATEGORIAS_MOTIVO)
    datos = {
        "nombre": preguntar("  Nombre: "),
        "formacion": preguntar("  Formación: "),
        "enfoque": preguntar("  Enfoque terapéutico: "),
        "poblacion": preguntar("  Población que atiende: "),
        "areas": preguntar(f"  Áreas y experiencia de 0 a 1 (temas: {temas})\n"
                           "  ejemplo 'ansiedad:1, estres:0.5': "),
        "idiomas": preguntar("  Idiomas separados por coma (espanol, ingles, otro): "),
        "modalidad": preguntar("  Modalidad (linea, presencial): "),
        "horarios": preguntar("  Horarios (manana, tarde, noche): "),
        "costo": preguntar("  Costo por sesión en pesos (0 = gratuito): "),
        "alcaldia": orientacion.pedir_alcaldia(),
        "acepta_pacientes": "si",
    }
    try:
        identificador = registrar_psicologo(datos)
        print(f"Registrado como {identificador}.")
    except ValueError as error:
        print("No se registró:", error)


def menu_paginas():
    for psicologo in cargar_psicologos():
        generar_panel_html(psicologo["id"])
    ruta = generar_inicio()
    print("Páginas actualizadas. Abre en tu navegador:", ruta)


def abrir_pagina_web():
    import servidor
    servidor.main()


def main():
    acciones = {
        "1": orientacion.main,
        "2": menu_recomendaciones,
        "3": menu_seguimiento,
        "4": menu_revocar,
        "5": menu_panel,
        "6": menu_registrar_psicologo,
        "7": menu_paginas,
        "8": evaluar_vinculacion.main,
        "9": abrir_pagina_web,
    }
    while True:
        print(MENU)
        opcion = preguntar("Opción: ", list(acciones) + ["0"])
        if opcion == "0":
            break
        try:
            acciones[opcion]()
        except (ValueError, FileNotFoundError) as error:
            print("Error:", error)


if __name__ == "__main__":
    main()
