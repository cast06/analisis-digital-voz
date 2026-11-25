# ==============================================================
# ALGORITMO DE COMPATIBILIDAD PACIENTE - PSICOLOGO
# ==============================================================
#
# Objetivo: ORDENAR opciones compatibles con criterios transparentes.
# No elige "al mejor psicologo"; la decision final es del usuario.
#
# 1. Representacion vectorial (K = 8 temas de config.CATEGORIAS_MOTIVO)
#      n = (n_1, ..., n_K)  necesidad del paciente: probabilidades
#                           que da el clasificador de texto (suman 1)
#      e = (e_1, ..., e_K)  experiencia del psicologo: pesos en [0, 1]
#
# 2. Afinidad tematica (similitud coseno, implementada a mano)
#      s_tema = (n · e) / (||n|| ||e||)
#    Como n y e no tienen componentes negativos, s_tema esta en [0, 1].
#
# 3. Criterios practicos, cada uno en [0, 1]
#      s_costo:
#        presupuesto M > 0:  1 si c <= M;  max(0, 1 - (c - M) / M) si c > M
#        presupuesto M = 0:  1 si c = 0;   0 en otro caso
#      s_modalidad = 1 si coincide o el paciente acepta cualquiera, 0 si no.
#        Si el paciente quiere atencion PRESENCIAL y dio su alcaldia:
#        s_modalidad = 1 * cercania(d), con d la distancia al consultorio
#        (ver vinculacion/geografia.py: 1 hasta 5 km, 0 desde 25 km).
#      s_horario   = 1 si coincide o el paciente acepta cualquiera, 0 si no
#
# 4. Puntaje final (pesos w en config.PESOS_COMPATIBILIDAD, suman 1)
#      S = w_tema s_tema + w_costo s_costo + w_mod s_modalidad + w_hor s_horario
#    S esta en [0, 1] y se muestra como porcentaje.
#
# 5. Filtros obligatorios (no se puntuan, excluyen):
#      - el psicologo no acepta pacientes nuevos
#      - no atiende en el idioma del paciente (si el paciente eligio
#        "otro" no se filtra, se avisa)
#    Los excluidos se reportan con su motivo, no desaparecen sin explicacion.
#
# Complejidad: O(P * K) para P psicologos y K temas, mas O(P log P)
# para ordenar. Con P = 18 y K = 8 es instantaneo.
# ==============================================================

import config
from nucleo.matematicas import similitud_coseno
from vinculacion.geografia import (
    ubicacion_alcaldia, ubicacion_consultorio, distancia_km, puntaje_cercania
)


def vector_experiencia(psicologo):
    """Pesos del psicologo en el orden de config.CATEGORIAS_MOTIVO."""
    return [psicologo["areas"].get(tema, 0.0) for tema in config.CATEGORIAS_MOTIVO]


def puntaje_costo(costo, presupuesto):
    if costo < 0 or presupuesto < 0:
        raise ValueError("Costo y presupuesto deben ser mayores o iguales a 0.")
    if presupuesto == 0:
        return 1.0 if costo == 0 else 0.0
    if costo <= presupuesto:
        return 1.0
    return max(0.0, 1.0 - (costo - presupuesto) / presupuesto)


def puntaje_opcion(preferencia, ofrecidas):
    """1 si la preferencia esta entre las ofrecidas o es 'cualquiera'."""
    return 1.0 if preferencia == "cualquiera" or preferencia in ofrecidas else 0.0


def _verificar_pesos(pesos):
    if set(pesos) != {"tema", "costo", "modalidad", "horario"}:
        raise ValueError("Los pesos deben ser: tema, costo, modalidad y horario.")
    if any(w < 0 for w in pesos.values()):
        raise ValueError("Los pesos no pueden ser negativos.")
    if abs(sum(pesos.values()) - 1.0) > 1e-9:
        raise ValueError("Los pesos deben sumar 1.")


def motivo_excluido(paciente, psicologo):
    """Devuelve el motivo de exclusion o None si pasa los filtros."""
    if not psicologo["acepta_pacientes"]:
        return "No acepta pacientes nuevos por ahora."
    idioma = paciente["idioma"]
    if idioma != "otro" and idioma not in psicologo["idiomas"]:
        return f"No atiende en {idioma}."
    return None


def evaluar(paciente, psicologo, pesos=None):
    """
    Calcula el puntaje de un psicologo para un paciente.
    paciente: probabilidades (lista K), modalidad, horario,
              costo_maximo, idioma.
    Devuelve un diccionario con el total, cada componente y las razones.
    """
    pesos = pesos or config.PESOS_COMPATIBILIDAD
    _verificar_pesos(pesos)
    necesidad = paciente["probabilidades"]
    if len(necesidad) != len(config.CATEGORIAS_MOTIVO):
        raise ValueError("El vector de necesidad debe tener un valor por tema.")
    if any(p < 0 for p in necesidad) or sum(necesidad) == 0:
        raise ValueError("El vector de necesidad debe ser no negativo y no nulo.")

    componentes = {
        "tema": similitud_coseno(necesidad, vector_experiencia(psicologo)),
        "costo": puntaje_costo(psicologo["costo"], paciente["costo_maximo"]),
        "modalidad": puntaje_opcion(paciente["modalidad"], psicologo["modalidad"]),
        "horario": puntaje_opcion(paciente["horario"], psicologo["horarios"]),
    }
    distancia = calcular_distancia(paciente, psicologo)
    if paciente["modalidad"] == "presencial" and distancia is not None:
        componentes["modalidad"] *= puntaje_cercania(distancia)
    total = sum(pesos[c] * componentes[c] for c in componentes)
    return {
        "psicologo": psicologo,
        "total": total,
        "componentes": componentes,
        "distancia": distancia,
        "razones": explicar(paciente, psicologo, componentes, distancia),
    }


def calcular_distancia(paciente, psicologo):
    """Km entre la alcaldia del paciente y el consultorio, o None si falta algun dato
    o el psicologo no atiende presencial."""
    if "presencial" not in psicologo["modalidad"]:
        return None
    origen = ubicacion_alcaldia(paciente.get("alcaldia", ""))
    destino = ubicacion_consultorio(psicologo)
    if origen is None or destino is None:
        return None
    return distancia_km(origen, destino)


def explicar(paciente, psicologo, componentes, distancia=None):
    """Lista de frases a favor (+) y en contra (-) para mostrar al usuario."""
    razones = []
    nombres = list(config.CATEGORIAS_MOTIVO)
    necesidad = paciente["probabilidades"]
    # Temas donde coinciden la necesidad (>= 15 %) y la experiencia (>= 0.5)
    coincidencias = [nombres[i] for i in sorted(range(len(nombres)), key=lambda i: -necesidad[i])
                     if necesidad[i] >= 0.15 and psicologo["areas"].get(nombres[i], 0) >= 0.5]
    if coincidencias:
        temas = ", ".join(config.CATEGORIAS_MOTIVO[t] for t in coincidencias)
        razones.append(("+", f"Experiencia en lo que describiste: {temas}"))
    else:
        razones.append(("-", "Su experiencia coincide poco con el tema principal que describiste"))

    costo, maximo = psicologo["costo"], paciente["costo_maximo"]
    if costo == 0:
        razones.append(("+", "Atención gratuita"))
    elif componentes["costo"] == 1.0:
        razones.append(("+", f"Costo ${costo} dentro de tu presupuesto de ${maximo}"))
    else:
        razones.append(("-", f"Costo ${costo}: supera tu presupuesto de ${maximo}"))

    if paciente["modalidad"] != "cualquiera":
        texto = "en línea" if paciente["modalidad"] == "linea" else "presencial"
        # se revisa la modalidad sola (la cercania se explica aparte)
        signo = "+" if puntaje_opcion(paciente["modalidad"], psicologo["modalidad"]) == 1.0 else "-"
        razones.append((signo, f"{'Atiende' if signo == '+' else 'No atiende'} {texto}"))
    if distancia is not None:
        lugar = psicologo.get("alcaldia", "")
        if paciente["modalidad"] == "presencial":
            signo = "+" if puntaje_cercania(distancia) >= 0.5 else "-"
            razones.append((signo, f"Consultorio a {distancia:.1f} km ({lugar})"))
        elif distancia <= 10:
            razones.append(("+", f"Si prefieres presencial, su consultorio está a {distancia:.1f} km ({lugar})"))
    if paciente["horario"] != "cualquiera":
        signo = "+" if componentes["horario"] == 1.0 else "-"
        razones.append((signo, f"{'Tiene' if signo == '+' else 'No tiene'} horario de "
                               f"{paciente['horario'].replace('manana', 'mañana')}"))
    if paciente["idioma"] == "otro":
        razones.append(("-", "Pediste otro idioma: confirma con el profesional si puede atenderte"))
    return razones


def recomendar(paciente, psicologos, cantidad=None, pesos=None):
    """
    Devuelve (opciones, excluidos):
      opciones  -> lista ordenada de resultados de evaluar(), maximo 'cantidad'
      excluidos -> lista de (psicologo, motivo)
    Empates: se ordena por puntaje y despues por ID para que el
    resultado sea siempre el mismo (reproducible).
    """
    cantidad = cantidad or config.OPCIONES_RECOMENDADAS
    evaluados, excluidos = [], []
    for psicologo in psicologos:
        motivo = motivo_excluido(paciente, psicologo)
        if motivo:
            excluidos.append((psicologo, motivo))
        else:
            evaluados.append(evaluar(paciente, psicologo, pesos))
    evaluados.sort(key=lambda r: (-r["total"], r["psicologo"]["id"]))
    return evaluados[:cantidad], excluidos


def texto_opcion(posicion, resultado):
    """Formato de una opcion para la consola."""
    p = resultado["psicologo"]
    c = resultado["componentes"]
    lineas = [
        f"{posicion}. {p['nombre']}  [{p['id']}]  compatibilidad {resultado['total'] * 100:.0f} %",
        f"   {p['formacion']} · enfoque {p['enfoque']} · {p['poblacion']}",
        f"   Afinidad con tu tema {c['tema'] * 100:.0f} % · costo {c['costo'] * 100:.0f} % · "
        f"{'modalidad y cercanía' if resultado.get('distancia') is not None else 'modalidad'} "
        f"{c['modalidad'] * 100:.0f} % · horario {c['horario'] * 100:.0f} %",
    ]
    for signo, frase in resultado["razones"]:
        lineas.append(f"   [{signo}] {frase}")
    return "\n".join(lineas)
