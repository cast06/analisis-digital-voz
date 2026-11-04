# ==============================================================
# FORMATEO DE CARACTERISTICAS PARA TERMINAL, TXT Y HTML
# ==============================================================


def formatear_valor_caracteristica(nombre, caracteristicas):
    if caracteristicas is None or nombre not in caracteristicas:
        return "No disponible"

    valor = caracteristicas[nombre]
    rms = caracteristicas.get("rms", 0.0)

    if nombre == "frecuencia_fundamental":
        if valor <= 0.0:
            return "No disponible (sin periodicidad clara)"
        return f"{round(valor, 2)} Hz"

    if nombre == "variacion_f0":
        if caracteristicas.get("frecuencia_fundamental", 0.0) <= 0.0:
            return "No disponible"
        return f"{round(valor, 2)} Hz"

    if nombre in ("frecuencia_dominante", "centroide_espectral", "ancho_banda_espectral"):
        if rms <= 0.0 and valor <= 0.0:
            return "No disponible (silencio)"
        return f"{round(valor, 2)} Hz"

    if nombre == "frecuencia_muestreo":
        return f"{int(valor)} Hz"

    if nombre in ("duracion", "tiempo_hablado", "tiempo_silencio"):
        return f"{round(valor, 4)} s"

    if isinstance(valor, float):
        return f"{round(valor, 6)}"

    return str(valor)


def formatear_bloque_segmento_txt(resultado):
    c = resultado["caracteristicas"]

    def fmt(nombre):
        return formatear_valor_caracteristica(nombre, c)

    lineas = [
        f"\nSegmento {resultado['id_segmento']}",
        f"  Inicio: {resultado['inicio']:.3f} s",
        f"  Fin: {resultado['fin']:.3f} s",
        f"  Duración: {resultado['duracion']:.3f} s",
        f"  Tiempo hablado activo: {c['tiempo_hablado']:.3f} s | Silencio interno: {c['tiempo_silencio']:.3f} s",
        f"  Amplitud máxima: {c['amplitud_maxima']:.4f} | Pico a pico: {c['pico_a_pico']:.4f}",
        f"  RMS: {c['rms']:.4f}",
        f"  Energía de la señal: {c['energia']:.4f}",
        f"  Tasa de cruces por cero (ZCR): {c['zcr']:.4f}",
        f"  Frecuencia dominante: {fmt('frecuencia_dominante')}",
        f"  Centroide espectral: {fmt('centroide_espectral')}",
        f"  Ancho de banda espectral: {fmt('ancho_banda_espectral')}",
        f"  Frecuencia fundamental (F0): {fmt('frecuencia_fundamental')} (Variación F0: {fmt('variacion_f0')})",
        f"  Clasificación del segmento: {resultado['tipo_segmento']}",
        f"  Estado de reconocimiento: {resultado['estado']}"
    ]
    return "\n".join(lineas) + "\n"
