# ==============================================================
# ANALIZAR UNA GRABACION: QUE PALABRA SE DICE Y CON QUE EMOCION
# ==============================================================
#
# Ejecutar desde la carpeta del proyecto (despues de entrenar):
#     python clasificar_voz.py
#
# Usa los dos modelos si existen:
#   - datos/modelo_palabras.txt   (python entrenar_palabras.py)
#   - datos/modelo_emociones.txt  (python entrenar_emociones.py)
# ==============================================================

from nucleo.archivos import existe_archivo
from emociones.modelo_emocion import cargar_modelo as cargar_emociones, predecir_emocion_archivo
from palabras.modelo_palabras import cargar_modelo as cargar_palabras, reconocer_palabra_archivo


def _cargar(funcion, nombre):
    try:
        return funcion()
    except (FileNotFoundError, ValueError) as error:
        print(f"[{nombre}] {error}")
        return None


def pedir_tipo_voz():
    while True:
        respuesta = input("Tipo de voz para la normalización (F = femenina, M = masculina): ")
        respuesta = respuesta.strip().upper()
        if respuesta in ("F", "M"):
            return respuesta
        print("Escribe F o M.")


def _barras(pares):
    for etiqueta, p in pares:
        print(f"  {etiqueta:<12} {p * 100:6.2f} %  {'#' * int(p * 30)}")


def main():
    modelo_palabras = _cargar(cargar_palabras, "Palabras")
    modelo_emociones = _cargar(cargar_emociones, "Emociones")
    if modelo_palabras is None and modelo_emociones is None:
        return

    while True:
        ruta = input("\nRuta del archivo .wav (Enter para salir): ").strip().strip('"')
        if not ruta:
            break
        if not existe_archivo(ruta):
            print("No se encontró el archivo.")
            continue

        if modelo_palabras is not None:
            try:
                resultado = reconocer_palabra_archivo(ruta, modelo_palabras)
                print(f"\nPalabra reconocida: {resultado['palabra'].upper()}")
                _barras(resultado["candidatas"])
                print(resultado["aviso"])
            except Exception as error:
                print("No se pudo reconocer la palabra:", error)

        if modelo_emociones is not None:
            tipo_voz = pedir_tipo_voz()
            try:
                resultado = predecir_emocion_archivo(ruta, tipo_voz, modelo_emociones)
                print(f"\nEmoción percibida: {resultado['emocion'].upper()}")
                _barras(sorted(resultado["probabilidades"].items(), key=lambda par: -par[1]))
                print(resultado["aviso"])
            except Exception as error:
                print("No se pudo analizar la emoción:", error)


if __name__ == "__main__":
    main()
