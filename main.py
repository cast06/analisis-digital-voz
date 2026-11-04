# ==============================================================
# SISTEMA INTELIGENTE MULTIMODAL DE ACCESO, ORIENTACION Y
# VINCULACION PSICOLOGICA - PROGRAMA PRINCIPAL
# ==============================================================
#
# Modulo actual: analisis digital de voz desde cero.
#
# El programa NO importa ninguna libreria: ni externa ni de la
# biblioteca estandar. Las unicas importaciones son entre los
# modulos propios del proyecto (nucleo/, audio/, visual/, ...).
#
# Ejecucion (desde la carpeta del proyecto):
#     python main.py
#     python pruebas.py
# ==============================================================

from config import ARCHIVO_VOZ_DETALLE, ARCHIVOS_AUDIO_LOTE, DIRECTORIO_SALIDAS, ruta_salida
from nucleo.archivos import existe_archivo, guardar_texto
from audio.referencias import cargar_referencias
from reportes.lote import procesar_lote_audios, buscar_ruta_audio
from experimentos.sinteticos import (
    experimento_seno, experimento_seno_coseno, experimento_senal_compleja,
    generar_ondas_abecedario
)
from experimentos.voz import analizar_voz_real, analizar_fragmentos_voz
from visual.html import generar_html


def verificar_carpeta_salidas():
    """Sin os no se pueden crear carpetas: se comprueba que salidas/ exista."""
    prueba = ruta_salida("LEEME.txt")
    try:
        guardar_texto(prueba, "ok")
        return True
    except OSError:
        print("ERROR: no existe o no se puede escribir en la carpeta:", DIRECTORIO_SALIDAS)
        print("Crea la carpeta 'salidas' junto a main.py y vuelve a ejecutar.")
        return False


def elegir_audio_detalle(resultados_lote):
    """Usa voz.wav si existe; si no, la primera grabacion del lote que se leyo bien."""
    ruta = buscar_ruta_audio(ARCHIVO_VOZ_DETALLE)
    if existe_archivo(ruta):
        return ruta
    for item in resultados_lote:
        if item.get("exito"):
            return item["ruta"]
    return ruta


def main():
    print("Iniciando Sistema de Análisis Digital de Voz desde Cero...")

    if not verificar_carpeta_salidas():
        return

    # 1. Banco de referencias (declaradas en referencias/indice.txt)
    referencias = cargar_referencias()

    # 2. Lote de grabaciones continuas -> salidas/resultado_analisis.txt
    resultados_lote = procesar_lote_audios(ARCHIVOS_AUDIO_LOTE, referencias=referencias)

    # 3. Experimentos sinteticos de validacion
    print("\nGenerando experimentos matemáticos y gráficas SVG/HTML...")
    experimento1 = experimento_seno()
    experimento2 = experimento_seno_coseno()
    experimento3 = experimento_senal_compleja()
    ondas_abecedario = generar_ondas_abecedario()

    # 4. Vista detallada de una grabacion real
    ruta_voz = elegir_audio_detalle(resultados_lote)
    voz = analizar_voz_real(ruta_voz)
    fragmentos_voz = analizar_fragmentos_voz(ruta_voz, referencias=referencias)

    # 5. Pagina HTML con todos los resultados
    ruta_html = generar_html(
        experimento1, experimento2, experimento3,
        voz, fragmentos_voz, ondas_abecedario,
        referencias=referencias,
        resultados_lote=resultados_lote
    )
    print("Reporte visual HTML generado en:", ruta_html)


if __name__ == "__main__":
    main()
