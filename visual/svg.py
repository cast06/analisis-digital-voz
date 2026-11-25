# ==============================================================
# GRAFICAS SVG GENERADAS MANUALMENTE
# ==============================================================
# Estas funciones se reutilizaran despues para la matriz de
# confusion, las curvas de perdida y el seguimiento longitudinal.
# ==============================================================

from config import ruta_salida
from nucleo.archivos import guardar_texto
from nucleo.matematicas import DOS_PI, seno, maximo_absoluto


def _guardar_svg(nombre_archivo, contenido):
    if nombre_archivo:
        guardar_texto(ruta_salida(nombre_archivo), contenido)


def _puntos_envolvente(muestras, x0, ancho_grafica, centro_y, escala_y, maximo):
    """
    Reduce la señal a una columna por pixel conservando el minimo y el
    maximo de cada columna, para no perder la forma de la onda ni
    generar archivos SVG gigantescos.
    """
    total = len(muestras)
    columnas = int(ancho_grafica)
    puntos = []
    for col in range(columnas):
        ini = int(col * total / columnas)
        fin = int((col + 1) * total / columnas)
        if fin <= ini:
            fin = ini + 1
        bloque = muestras[ini:fin]
        v_min = min(bloque)
        v_max = max(bloque)
        x = x0 + (col / max(1, columnas - 1)) * ancho_grafica
        y_max = centro_y - (v_max / maximo) * escala_y
        y_min = centro_y - (v_min / maximo) * escala_y
        puntos.append(f"{round(x, 2)},{round(y_max, 2)}")
        if v_min != v_max:
            puntos.append(f"{round(x, 2)},{round(y_min, 2)}")
    return puntos


def crear_svg(
        muestras,
        nombre_archivo,
        titulo,
        ancho=1200,
        alto=450):
    """Forma de onda en el dominio del tiempo."""

    if len(muestras) < 2:
        return ""

    maximo = maximo_absoluto(muestras)
    if maximo == 0:
        maximo = 1.0

    margen = 50
    ancho_grafica = ancho - 2 * margen
    alto_grafica = alto - 2 * margen
    escala_y = alto_grafica * 0.45

    total_muestras = len(muestras)

    if total_muestras <= ancho_grafica * 2:
        puntos = []
        for i in range(total_muestras):
            x = margen + (i / (total_muestras - 1)) * ancho_grafica
            y = alto / 2 - (muestras[i] / maximo) * escala_y
            puntos.append(f"{round(x, 2)},{round(y, 2)}")
    else:
        puntos = _puntos_envolvente(muestras, margen, ancho_grafica, alto / 2, escala_y, maximo)

    contenido = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<text x="50" y="30" font-family="Arial" font-size="18">{titulo}</text>'
        f'<line x1="{margen}" y1="{alto / 2}" x2="{ancho - margen}" y2="{alto / 2}" stroke="gray"/>'
        f'<line x1="{margen}" y1="{margen}" x2="{margen}" y2="{alto - margen}" stroke="gray"/>'
        f'<polyline fill="none" stroke="black" stroke-width="1" points="{" ".join(puntos)}"/>'
        f'</svg>'
    )

    _guardar_svg(nombre_archivo, contenido)
    return contenido


def crear_svg_espectro(
        espectro,
        nombre_archivo,
        titulo,
        frecuencia_maxima=4000,
        ancho=1200,
        alto=450):
    """Magnitud del espectro entre 0 Hz y frecuencia_maxima."""

    frecuencias = []
    magnitudes = []

    for frecuencia, magnitud in espectro:
        if frecuencia <= frecuencia_maxima:
            frecuencias.append(frecuencia)
            magnitudes.append(magnitud)

    if len(frecuencias) < 2:
        return ""

    maximo = maximo_absoluto(magnitudes)
    if maximo == 0:
        maximo = 1.0

    margen = 50
    ancho_grafica = ancho - 2 * margen
    alto_grafica = alto - 2 * margen

    puntos = []
    for frecuencia, magnitud in zip(frecuencias, magnitudes):
        x = margen + (frecuencia / frecuencia_maxima) * ancho_grafica
        y = alto - margen - (magnitud / maximo) * alto_grafica
        puntos.append(f"{round(x, 2)},{round(y, 2)}")

    # Correccion: los ejes ahora dependen de 'ancho' y 'alto'
    # (antes estaban fijos en 400 y 1150).
    contenido = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<text x="50" y="30" font-family="Arial" font-size="18">{titulo}</text>'
        f'<line x1="{margen}" y1="{alto - margen}" x2="{ancho - margen}" y2="{alto - margen}" stroke="gray"/>'
        f'<line x1="{margen}" y1="{margen}" x2="{margen}" y2="{alto - margen}" stroke="gray"/>'
        f'<polyline fill="none" stroke="black" stroke-width="1" points="{" ".join(puntos)}"/>'
        f'</svg>'
    )

    _guardar_svg(nombre_archivo, contenido)
    return contenido


def crear_svg_tres_intensidades(
        letra,
        frecuencia,
        ancho=900,
        alto=320,
        cantidad_muestras=240):
    """Senoide de ejemplo con tres amplitudes (demostracion sintetica)."""

    duracion = 0.03
    amplitudes = [
        ("Baja", 0.3, "#2878B5"),
        ("Media", 0.6, "#E39A26"),
        ("Fuerte", 1.0, "#C74440")
    ]

    margen = 50
    ancho_grafica = ancho - 2 * margen
    alto_grafica = alto - 2 * margen

    contenido = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {ancho} {alto}" '
        f'width="{ancho}" height="{alto}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<text x="50" y="25" font-family="Arial" font-size="18" fill="#222">'
        f'Letra {letra} - Frecuencia de ejemplo: {frecuencia} Hz</text>'
        f'<line x1="{margen}" y1="{alto / 2}" x2="{ancho - margen}" y2="{alto / 2}" stroke="#888" stroke-width="1"/>'
        f'<line x1="{margen}" y1="{margen}" x2="{margen}" y2="{alto - margen}" stroke="#888" stroke-width="1"/>'
    )

    for nombre, amplitud, color in amplitudes:
        puntos = []
        for n in range(cantidad_muestras):
            tiempo = n * duracion / (cantidad_muestras - 1)
            valor = amplitud * seno(DOS_PI * frecuencia * tiempo)
            x = margen + n * ancho_grafica / (cantidad_muestras - 1)
            y = alto / 2 - valor * alto_grafica * 0.42
            puntos.append(f"{round(x, 2)},{round(y, 2)}")

        contenido += (
            f'<polyline fill="none" stroke="{color}" '
            f'stroke-width="2" points="{" ".join(puntos)}"/>'
        )

    posicion_x = margen
    for nombre, amplitud, color in amplitudes:
        contenido += (
            f'<line x1="{posicion_x}" y1="{alto - 15}" '
            f'x2="{posicion_x + 25}" y2="{alto - 15}" '
            f'stroke="{color}" stroke-width="3"/>'
            f'<text x="{posicion_x + 32}" y="{alto - 10}" '
            f'font-family="Arial" font-size="12">'
            f'{nombre} (A={amplitud})</text>'
        )
        posicion_x += 180

    contenido += '</svg>'
    return contenido


def crear_svg_segmentacion(
        muestras,
        fs,
        segmentos,
        nombre_archivo,
        titulo,
        ancho=1200,
        alto=360):
    """
    Onda completa del audio con franjas sombreadas (S1, S2, ...) para
    cada segmento de voz detectado automaticamente.
    """
    if len(muestras) < 2 or fs <= 0:
        return ""

    duracion_total = len(muestras) / fs
    if duracion_total <= 0:
        return ""

    maximo = maximo_absoluto(muestras)
    if maximo == 0:
        maximo = 1.0

    margen_izq = 55
    margen_der = 30
    margen_sup = 45
    margen_inf = 40

    ancho_grafica = ancho - margen_izq - margen_der
    alto_grafica = alto - margen_sup - margen_inf
    centro_y = margen_sup + alto_grafica / 2.0

    contenido = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<text x="{margen_izq}" y="26" font-family="Arial" font-size="16" font-weight="bold" fill="#222">'
        f'{titulo}</text>'
    )

    for seg in segmentos:
        x_ini = margen_izq + (seg["inicio"] / duracion_total) * ancho_grafica
        x_fin = margen_izq + (seg["fin"] / duracion_total) * ancho_grafica
        ancho_seg = max(2.0, x_fin - x_ini)

        contenido += (
            f'<rect x="{round(x_ini, 2)}" y="{margen_sup}" '
            f'width="{round(ancho_seg, 2)}" height="{alto_grafica}" '
            f'fill="#d4e9f7" fill-opacity="0.65" stroke="#2878B5" stroke-width="1"/>'
            f'<text x="{round(x_ini + 3, 2)}" y="{margen_sup + 14}" '
            f'font-family="Arial" font-size="10" font-weight="bold" fill="#1b5583">'
            f'S{seg["id_segmento"]}</text>'
        )

    contenido += (
        f'<line x1="{margen_izq}" y1="{round(centro_y, 2)}" '
        f'x2="{ancho - margen_der}" y2="{round(centro_y, 2)}" stroke="#888"/>'
        f'<line x1="{margen_izq}" y1="{margen_sup}" '
        f'x2="{margen_izq}" y2="{alto - margen_inf}" stroke="#555"/>'
    )

    num_marcas = 10
    for m in range(num_marcas + 1):
        t_marca = (m / num_marcas) * duracion_total
        x_marca = margen_izq + (m / num_marcas) * ancho_grafica
        contenido += (
            f'<line x1="{round(x_marca, 2)}" y1="{alto - margen_inf}" '
            f'x2="{round(x_marca, 2)}" y2="{alto - margen_inf + 5}" stroke="#555"/>'
            f'<text x="{round(x_marca - 12, 2)}" y="{alto - 12}" '
            f'font-family="Arial" font-size="11" fill="#444">{round(t_marca, 1)}s</text>'
        )

    puntos = _puntos_envolvente(
        muestras, margen_izq, ancho_grafica, centro_y, alto_grafica * 0.45, maximo
    )

    contenido += (
        f'<polyline fill="none" stroke="#222222" stroke-width="1" '
        f'points="{" ".join(puntos)}"/>'
        f'</svg>'
    )

    _guardar_svg(nombre_archivo, contenido)
    return contenido


def crear_svg_barras_segmentos(
        segmentos,
        titulo,
        ancho=1200,
        alto=280):
    """Grafica de barras con la F0 estimada de cada segmento."""
    if not segmentos:
        return ""

    margen_izq = 55
    margen_der = 30
    margen_sup = 45
    margen_inf = 45

    ancho_grafica = ancho - margen_izq - margen_der
    alto_grafica = alto - margen_sup - margen_inf
    base_y = margen_sup + alto_grafica

    max_f0 = max(seg["caracteristicas"].get("frecuencia_fundamental", 0.0) for seg in segmentos)
    if max_f0 < 300.0:
        max_f0 = 300.0

    contenido = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<text x="{margen_izq}" y="25" font-family="Arial" font-size="16" font-weight="bold" fill="#222">'
        f'{titulo}</text>'
        f'<line x1="{margen_izq}" y1="{base_y}" x2="{ancho - margen_der}" y2="{base_y}" stroke="#555"/>'
        f'<line x1="{margen_izq}" y1="{margen_sup}" x2="{margen_izq}" y2="{base_y}" stroke="#555"/>'
    )

    for f_guia in (100, 200, 300):
        if f_guia <= max_f0:
            y_guia = base_y - (f_guia / max_f0) * alto_grafica
            contenido += (
                f'<line x1="{margen_izq}" y1="{round(y_guia, 2)}" '
                f'x2="{ancho - margen_der}" y2="{round(y_guia, 2)}" '
                f'stroke="#dddddd" stroke-dasharray="4,4"/>'
                f'<text x="10" y="{round(y_guia + 4, 2)}" '
                f'font-family="Arial" font-size="11" fill="#555">{f_guia} Hz</text>'
            )

    paso_x = ancho_grafica / len(segmentos)
    ancho_barra = max(8.0, min(42.0, paso_x * 0.55))

    for i, seg in enumerate(segmentos):
        f0 = seg["caracteristicas"].get("frecuencia_fundamental", 0.0)
        altura_barra = (f0 / max_f0) * alto_grafica if f0 > 0 else 2.0
        x_barra = margen_izq + i * paso_x + (paso_x - ancho_barra) / 2.0
        y_barra = base_y - altura_barra
        centro_x = round(x_barra + ancho_barra / 2, 2)

        color_barra = "#2878B5" if f0 < 160.0 else "#E39A26"
        contenido += (
            f'<rect x="{round(x_barra, 2)}" y="{round(y_barra, 2)}" '
            f'width="{round(ancho_barra, 2)}" height="{round(altura_barra, 2)}" '
            f'fill="{color_barra}" rx="2"/>'
        )
        if f0 > 0:
            contenido += (
                f'<text x="{centro_x}" y="{round(y_barra - 5, 2)}" '
                f'text-anchor="middle" font-family="Arial" font-size="10" fill="#222">'
                f'{f0:.0f}</text>'
            )
        contenido += (
            f'<text x="{centro_x}" y="{base_y + 16}" '
            f'text-anchor="middle" font-family="Arial" font-size="11" fill="#333">'
            f'S{seg["id_segmento"]}</text>'
        )

    contenido += '</svg>'
    return contenido


def crear_svg_matriz_confusion(matriz, clases, titulo, nombre_archivo="", tamano_celda=90):
    """Matriz de confusion como mapa de calor (color por proporcion de la fila)."""
    n = len(clases)
    largo_etiqueta = max(len(c) for c in clases)
    compacta = tamano_celda < 60          # muchas clases: celdas chicas
    margen_izq = max(120, 30 + largo_etiqueta * 7)
    margen_sup = 80 if not compacta else 50 + largo_etiqueta * 6
    letra_valor = 16 if not compacta else max(9, int(tamano_celda * 0.33))
    ancho = margen_izq + n * tamano_celda + 30
    alto = margen_sup + n * tamano_celda + 60

    contenido = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<text x="10" y="24" font-family="Arial" font-size="15" font-weight="bold">{titulo}</text>'
        f'<text x="{margen_izq + n * tamano_celda / 2}" y="{42 if compacta else margen_sup - 30}" text-anchor="middle" '
        f'font-family="Arial" font-size="12" fill="#555">Predicho</text>'
        f'<text x="14" y="{margen_sup + n * tamano_celda / 2}" font-family="Arial" font-size="12" '
        f'fill="#555" transform="rotate(-90 14 {margen_sup + n * tamano_celda / 2})" '
        f'text-anchor="middle">Real</text>'
    )

    for j, clase in enumerate(clases):
        x = margen_izq + j * tamano_celda + tamano_celda / 2
        if compacta:
            contenido += (f'<text x="{x}" y="{margen_sup - 6}" text-anchor="start" '
                          f'font-family="Arial" font-size="11" '
                          f'transform="rotate(-60 {x} {margen_sup - 6})">{clase}</text>')
        else:
            contenido += (f'<text x="{x}" y="{margen_sup - 8}" text-anchor="middle" '
                          f'font-family="Arial" font-size="12">{clase}</text>')

    for i, fila in enumerate(matriz):
        total_fila = sum(fila) or 1
        y = margen_sup + i * tamano_celda
        contenido += (f'<text x="{margen_izq - 8}" y="{y + tamano_celda / 2 + 4}" text-anchor="end" '
                      f'font-family="Arial" font-size="12">{clases[i]}</text>')
        for j, valor in enumerate(fila):
            proporcion = valor / total_fila
            # Escala de blanco (0) a azul (1)
            r = int(255 - proporcion * (255 - 40))
            g = int(255 - proporcion * (255 - 100))
            b = int(255 - proporcion * (255 - 170))
            color_texto = "white" if proporcion > 0.5 else "#222"
            x = margen_izq + j * tamano_celda
            contenido += (
                f'<rect x="{x}" y="{y}" width="{tamano_celda}" height="{tamano_celda}" '
                f'fill="rgb({r},{g},{b})" stroke="#ccc"/>'
                f'<text x="{x + tamano_celda / 2}" y="{y + tamano_celda / 2 + (4 if compacta else 0)}" '
                f'text-anchor="middle" font-family="Arial" font-size="{letra_valor}" '
                f'fill="{color_texto}">{valor if (valor or not compacta) else ""}</text>'
            )
            if not compacta:
                contenido += (
                    f'<text x="{x + tamano_celda / 2}" y="{y + tamano_celda / 2 + 18}" text-anchor="middle" '
                    f'font-family="Arial" font-size="11" fill="{color_texto}">{proporcion * 100:.0f}%</text>'
                )

    contenido += '</svg>'
    _guardar_svg(nombre_archivo, contenido)
    return contenido


def crear_svg_curvas(curvas, titulo, nombre_archivo="", etiqueta_y="Pérdida",
                     ancho=900, alto=340, etiqueta_x="Época", y_min=None, y_max=None, leyenda=True):
    """
    Grafica de lineas. curvas: lista de (nombre, valores, color).
    Se usa para la perdida de entrenamiento por epoca.
    """
    curvas = [c for c in curvas if len(c[1]) >= 2]
    if not curvas:
        return ""

    margen_izq, margen_der, margen_sup, margen_inf = 60, (280 if leyenda else 30), 45, 45
    ancho_g = ancho - margen_izq - margen_der
    alto_g = alto - margen_sup - margen_inf
    maximo = max(max(v) for _, v, _ in curvas) if y_max is None else y_max
    minimo = min(0.0, min(min(v) for _, v, _ in curvas)) if y_min is None else y_min
    rango = (maximo - minimo) or 1.0
    epocas = max(len(v) for _, v, _ in curvas)

    contenido = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="{alto}" '
        f'viewBox="0 0 {ancho} {alto}">'
        f'<rect width="100%" height="100%" fill="white"/>'
        f'<text x="{margen_izq}" y="25" font-family="Arial" font-size="15" font-weight="bold">{titulo}</text>'
        f'<line x1="{margen_izq}" y1="{margen_sup + alto_g}" x2="{margen_izq + ancho_g}" '
        f'y2="{margen_sup + alto_g}" stroke="#555"/>'
        f'<line x1="{margen_izq}" y1="{margen_sup}" x2="{margen_izq}" y2="{margen_sup + alto_g}" stroke="#555"/>'
        f'<text x="{margen_izq + ancho_g / 2}" y="{alto - 8}" text-anchor="middle" '
        f'font-family="Arial" font-size="12" fill="#555">{etiqueta_x}</text>'
        f'<text x="14" y="{margen_sup + alto_g / 2}" font-family="Arial" font-size="12" fill="#555" '
        f'transform="rotate(-90 14 {margen_sup + alto_g / 2})" text-anchor="middle">{etiqueta_y}</text>'
    )

    for k in range(5):
        valor = minimo + rango * k / 4
        y = margen_sup + alto_g - (valor - minimo) / rango * alto_g
        contenido += (f'<text x="{margen_izq - 6}" y="{y + 4:.1f}" text-anchor="end" '
                      f'font-family="Arial" font-size="10" fill="#555">{valor:.2f}</text>')
    contenido += (f'<text x="{margen_izq + ancho_g}" y="{margen_sup + alto_g + 15}" text-anchor="end" '
                  f'font-family="Arial" font-size="10" fill="#555">{epocas}</text>')

    for indice, (nombre, valores, color) in enumerate(curvas):
        puntos = []
        for i, v in enumerate(valores):
            x = margen_izq + i / max(1, epocas - 1) * ancho_g
            y = margen_sup + alto_g - (v - minimo) / rango * alto_g
            puntos.append(f"{x:.1f},{y:.1f}")
        contenido += f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{" ".join(puntos)}"/>'
        if len(valores) <= 30:          # puntos visibles cuando hay pocos valores (sesiones)
            for punto in puntos:
                px, py = punto.split(",")
                contenido += f'<circle cx="{px}" cy="{py}" r="4" fill="{color}"/>'
        if not leyenda:
            continue
        y_ley = margen_sup + 10 + indice * 20
        contenido += (
            f'<line x1="{margen_izq + ancho_g + 15}" y1="{y_ley}" x2="{margen_izq + ancho_g + 35}" '
            f'y2="{y_ley}" stroke="{color}" stroke-width="3"/>'
            f'<text x="{margen_izq + ancho_g + 40}" y="{y_ley + 4}" font-family="Arial" '
            f'font-size="11">{nombre}</text>'
        )

    contenido += '</svg>'
    _guardar_svg(nombre_archivo, contenido)
    return contenido
