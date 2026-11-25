# ==============================================================
# EVALUACION DE LA EXTRACCION Y DEL MATCHING
# ==============================================================
#
# A) Extraccion por campo (corpus/extraccion_prueba.txt)
#    Duracion:
#      - Deteccion: precision, recall y F1 de "menciona una duracion".
#      - Exactitud del valor: casos con dias conocidos donde el valor
#        extraido es exactamente el etiquetado.
#      - Exactitud del campo: proporcion de casos con el campo correcto
#        (nada si no se menciona; algo si es "?"; el valor exacto si hay dias).
#    Contextos (multi-etiqueta):
#      - Por contexto c: TP, FP, FN -> precision, recall, F1.
#      - Micro-promedio: se suman TP, FP y FN de todos los contextos.
#      - Exactitud de conjunto: casos con el conjunto identico.
#
# B) Matching (corpus/evaluacion_matching.txt)
#    Cada anotador ordena, SIN ver el resultado del algoritmo, los
#    3 psicologos que considera mas adecuados para cada caso.
#      precision@3 = |top3_algoritmo ∩ top3_anotador| / 3
#      acierto@1   = 1 si el primero del algoritmo esta en el top 3 del anotador
#    Consenso de anotadores por conteo de Borda (3, 2 y 1 puntos).
#    Acuerdo entre anotadores: precision@3 promedio entre cada par;
#    indica que tan facil es la tarea incluso para personas.
#    Referencia de azar: con N elegibles, E[precision@3] = 3 / N.
#    Variantes del algoritmo (comparacion de pesos):
#      completo, solo tema y solo criterios practicos.
# ==============================================================

import config
from nucleo.tabla import leer_texto_flexible
from nucleo.archivos import existe_archivo
from texto.extraccion import extraer_duracion, extraer_contextos
from vinculacion.almacen import leer_registros, a_lista, a_pesos
from vinculacion.compatibilidad import recomendar

CONTEXTOS_VALIDOS = ["escuela", "trabajo", "familia", "pareja", "amistades", "salud", "economia"]

VARIANTES = {
    "Completo (0.55 / 0.20 / 0.15 / 0.10)": None,
    "Solo afinidad temática": {"tema": 1.0, "costo": 0.0, "modalidad": 0.0, "horario": 0.0},
    "Solo criterios prácticos": {"tema": 0.0, "costo": 0.4, "modalidad": 0.35, "horario": 0.25},
}


def _division(a, b):
    return a / b if b else 0.0


def _f1(p, r):
    return _division(2 * p * r, p + r)


# --------------------------------------------------------------
# A) Extraccion
# --------------------------------------------------------------

def leer_casos_extraccion(ruta):
    if not existe_archivo(ruta):
        raise FileNotFoundError(f"No se encontró {ruta}")
    casos = []
    for numero, linea in enumerate(leer_texto_flexible(ruta).splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        partes = [p.strip() for p in linea.split("|")]
        if len(partes) != 3:
            raise ValueError(f"{ruta}, línea {numero}: se esperaban 3 campos separados por '|'.")
        frase, duracion, contextos = partes
        if duracion not in ("-", "?") and not duracion.isdigit():
            raise ValueError(f"{ruta}, línea {numero}: duración inválida '{duracion}'.")
        lista = [] if contextos == "-" else a_lista(contextos)
        desconocidos = [c for c in lista if c not in CONTEXTOS_VALIDOS]
        if desconocidos:
            raise ValueError(f"{ruta}, línea {numero}: contextos no válidos {desconocidos}.")
        casos.append({"frase": frase, "duracion": duracion, "contextos": set(lista)})
    return casos


def evaluar_extraccion(casos):
    tp = fp = fn = tn = 0
    valor_correcto = valor_total = campo_correcto = 0
    errores_duracion = []
    conteos = {c: {"tp": 0, "fp": 0, "fn": 0} for c in CONTEXTOS_VALIDOS}
    conjunto_correcto = 0
    errores_contexto = []

    for caso in casos:
        extraida = extraer_duracion(caso["frase"])
        dias = extraida["dias"] if extraida else None
        real = caso["duracion"]
        menciona = real != "-"
        if menciona and dias is not None:
            tp += 1
        elif menciona:
            fn += 1
        elif dias is not None:
            fp += 1
        else:
            tn += 1
        if real.isdigit():
            valor_total += 1
            valor_correcto += int(dias == int(real))
        correcto = ((real == "-" and dias is None) or (real == "?" and dias is not None)
                    or (real.isdigit() and dias == int(real)))
        campo_correcto += int(correcto)
        if not correcto:
            errores_duracion.append((caso["frase"], real, "-" if dias is None else str(dias)))

        predichos = set(extraer_contextos(caso["frase"]))
        for c in CONTEXTOS_VALIDOS:
            if c in predichos and c in caso["contextos"]:
                conteos[c]["tp"] += 1
            elif c in predichos:
                conteos[c]["fp"] += 1
            elif c in caso["contextos"]:
                conteos[c]["fn"] += 1
        if predichos == caso["contextos"]:
            conjunto_correcto += 1
        else:
            errores_contexto.append((caso["frase"], ", ".join(sorted(caso["contextos"])) or "-",
                                     ", ".join(sorted(predichos)) or "-"))

    p_det = _division(tp, tp + fp)
    r_det = _division(tp, tp + fn)
    por_contexto = []
    for c in CONTEXTOS_VALIDOS:
        k = conteos[c]
        p = _division(k["tp"], k["tp"] + k["fp"])
        r = _division(k["tp"], k["tp"] + k["fn"])
        por_contexto.append({"contexto": c, "precision": p, "recall": r, "f1": _f1(p, r),
                             "soporte": k["tp"] + k["fn"]})
    stp = sum(k["tp"] for k in conteos.values())
    sfp = sum(k["fp"] for k in conteos.values())
    sfn = sum(k["fn"] for k in conteos.values())
    p_micro, r_micro = _division(stp, stp + sfp), _division(stp, stp + sfn)
    n = len(casos)
    return {
        "n": n,
        "duracion": {"precision": p_det, "recall": r_det, "f1": _f1(p_det, r_det),
                     "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
                     "exactitud_valor": _division(valor_correcto, valor_total),
                     "casos_valor": valor_total,
                     "exactitud_campo": _division(campo_correcto, n),
                     "errores": errores_duracion},
        "contextos": {"por_contexto": por_contexto,
                      "micro": {"precision": p_micro, "recall": r_micro, "f1": _f1(p_micro, r_micro)},
                      "exactitud_conjunto": _division(conjunto_correcto, n),
                      "errores": errores_contexto},
    }


# --------------------------------------------------------------
# B) Matching
# --------------------------------------------------------------

def leer_casos_matching(ruta):
    """Devuelve lista de casos; cada uno con 'paciente' y 'anotaciones' {anotador: [ids]}."""
    casos = []
    for r in leer_registros(ruta):
        pesos = a_pesos(r.get("necesidad", ""))
        desconocidos = [t for t in pesos if t not in config.CATEGORIAS_MOTIVO]
        if desconocidos:
            raise ValueError(f"{r['id']}: temas no válidos en 'necesidad': {desconocidos}")
        if not r.get("costo_maximo", "").isdigit():
            raise ValueError(f"{r['id']}: 'costo_maximo' debe ser un entero.")
        paciente = {
            "probabilidades": [pesos.get(t, 0.0) for t in config.CATEGORIAS_MOTIVO],
            "modalidad": r.get("modalidad", "cualquiera"),
            "horario": r.get("horario", "cualquiera"),
            "costo_maximo": int(r["costo_maximo"]),
            "idioma": r.get("idioma", "espanol"),
        }
        anotaciones = {}
        for clave, valor in r.items():
            if clave.startswith("orden_") and valor.strip():
                ids = [x.upper() for x in a_lista(valor)]
                if len(ids) != 3 or len(set(ids)) != 3:
                    raise ValueError(f"{r['id']}: '{clave}' debe tener 3 IDs distintos.")
                anotaciones[clave[len("orden_"):]] = ids
        casos.append({"id": r["id"], "descripcion": r.get("descripcion", ""),
                      "paciente": paciente, "anotaciones": anotaciones})
    return casos


def precision_en_k(predichos, relevantes, k=3):
    return len(set(predichos[:k]) & set(relevantes[:k])) / k


def consenso_borda(listas):
    """3 puntos al primero, 2 al segundo y 1 al tercero; empates por ID."""
    puntos = {}
    for lista in listas:
        for posicion, identificador in enumerate(lista):
            puntos[identificador] = puntos.get(identificador, 0) + (3 - posicion)
    return [i for i, _ in sorted(puntos.items(), key=lambda par: (-par[1], par[0]))][:3]


def evaluar_matching(casos, psicologos):
    """
    Devuelve None si nadie ha anotado. Si hay anotaciones, compara cada
    variante del algoritmo contra cada anotador y contra el consenso.
    """
    anotados = [c for c in casos if c["anotaciones"]]
    if not anotados:
        return None
    ids_validos = {p["id"] for p in psicologos}
    anotadores = sorted({a for c in anotados for a in c["anotaciones"]})

    variantes = []
    for nombre, pesos in VARIANTES.items():
        por_anotador = {a: [] for a in anotadores}
        consenso_p3, consenso_a1, azar = [], [], []
        detalle = []
        for caso in anotados:
            opciones, excluidos = recomendar(caso["paciente"], psicologos, 3, pesos)
            top = [o["psicologo"]["id"] for o in opciones]
            for lista in caso["anotaciones"].values():
                invalidos = [i for i in lista if i not in ids_validos]
                if invalidos:
                    raise ValueError(f"{caso['id']}: IDs inexistentes {invalidos}")
            for a, lista in caso["anotaciones"].items():
                por_anotador[a].append(precision_en_k(top, lista))
            consenso = consenso_borda(list(caso["anotaciones"].values()))
            consenso_p3.append(precision_en_k(top, consenso))
            consenso_a1.append(1.0 if top and top[0] in consenso else 0.0)
            elegibles = len(psicologos) - len(excluidos)
            azar.append(min(1.0, 3 / elegibles) if elegibles else 0.0)
            detalle.append((caso["id"], top, consenso, consenso_p3[-1]))
        variantes.append({
            "nombre": nombre,
            "precision3_consenso": sum(consenso_p3) / len(consenso_p3),
            "acierto1_consenso": sum(consenso_a1) / len(consenso_a1),
            "precision3_anotador": {a: (sum(v) / len(v) if v else None) for a, v in por_anotador.items()},
            "azar": sum(azar) / len(azar),
            "detalle": detalle,
        })

    # Acuerdo entre anotadores (precision@3 entre cada par, en casos que ambos anotaron)
    pares = []
    for i in range(len(anotadores)):
        for j in range(i + 1, len(anotadores)):
            a, b = anotadores[i], anotadores[j]
            valores = [precision_en_k(c["anotaciones"][a], c["anotaciones"][b])
                       for c in anotados if a in c["anotaciones"] and b in c["anotaciones"]]
            if valores:
                pares.append((a, b, sum(valores) / len(valores), len(valores)))

    return {"casos": len(anotados), "total_casos": len(casos), "anotadores": anotadores,
            "variantes": variantes, "acuerdo": pares}
