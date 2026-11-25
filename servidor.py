# ==============================================================
# SERVIDOR WEB DEL SISTEMA (todo desde el navegador)
# ==============================================================
#
# Ejecutar desde la carpeta del proyecto:
#     python servidor.py
# y abrir http://localhost:8000 (se abre solo).
#
# Capa web: usa modulos de la BIBLIOTECA ESTANDAR de Python
# (http.server, urllib.parse, json, webbrowser), permitidos por el
# profesor para la interfaz. No se instala ningun framework.
# El servidor solo escucha en esta computadora (127.0.0.1): los
# datos no salen de ella.
#
# Toda la logica la hacen nuestros modulos (texto/, vinculacion/,
# emociones/, palabras/). Esta capa recibe formularios, llama a
# esas funciones y devuelve paginas.
# ==============================================================

import json
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import config
from nucleo.archivos import existe_archivo
from vinculacion.panel import escapar_html
from web import paginas
from web.diseno import pagina, tarjeta

PUERTO = 8000
TAMANO_MAXIMO_FORMULARIO = 200_000           # bytes
TAMANO_MAXIMO_AUDIO = 15_000_000             # ~7 minutos a 16 kHz
TIPOS = {".html": "text/html; charset=utf-8", ".svg": "image/svg+xml", ".txt": "text/plain; charset=utf-8",
         ".wav": "audio/wav", ".css": "text/css"}


def analizar_audio(datos, tipo_voz):
    """Guarda el WAV recibido, lo analiza con nuestros modelos y lo transcribe si hay vosk."""
    from orientacion import analizar_voz_sin_preguntas
    from voz_en_vivo import transcripcion
    numero = 1
    while existe_archivo(config.ruta_salida(f"grabacion_{numero:03d}.wav")):
        numero += 1
    ruta = config.ruta_salida(f"grabacion_{numero:03d}.wav")
    with open(ruta, "wb") as archivo:
        archivo.write(datos)
    resultado = analizar_voz_sin_preguntas(ruta, tipo_voz)
    respuesta = {"archivo": ruta}
    if "emocion" in resultado:
        respuesta["emocion"] = resultado["emocion"]
        respuesta["emocion_prob"] = round(resultado["emocion_probabilidad"] * 100)
    if "palabra" in resultado:
        respuesta["palabra"] = resultado["palabra"]
    disponible, motivo = transcripcion.disponible()
    if disponible:
        try:
            respuesta["texto"] = transcripcion.transcribir(ruta)
        except Exception as error:
            respuesta["aviso"] = f"No se pudo transcribir: {error}"
    else:
        respuesta["aviso"] = f"Transcripción no disponible ({motivo}). Escribe tu relato."
    return respuesta


class Manejador(BaseHTTPRequestHandler):

    # ---------- utilidades ----------
    def enviar(self, cuerpo, codigo=200, tipo="text/html; charset=utf-8"):
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(datos)

    def redirigir(self, destino):
        self.send_response(303)
        self.send_header("Location", destino)
        self.end_headers()

    def no_encontrado(self):
        self.enviar(pagina("No encontrado", tarjeta("Página no encontrada",
                    '<p><a class="boton" href="/">Volver al inicio</a></p>')), 404)

    def leer_cuerpo(self, maximo):
        largo = int(self.headers.get("Content-Length", 0) or 0)
        if largo > maximo:
            raise ValueError("El envío es demasiado grande.")
        return self.rfile.read(largo)

    def formulario(self):
        return parse_qs(self.leer_cuerpo(TAMANO_MAXIMO_FORMULARIO).decode("utf-8"), keep_blank_values=True)

    def log_message(self, formato, *argumentos):       # consola mas limpia
        print("  ", self.command, self.path)

    # ---------- GET ----------
    def do_GET(self):
        ruta = urlparse(self.path).path.rstrip("/") or "/"
        try:
            if ruta == "/":
                return self.enviar(paginas.inicio())
            if ruta == "/orientacion":
                return self.enviar(paginas.orientacion_paso1())
            if ruta.startswith("/recomendacion/"):
                html = paginas.recomendacion(ruta.split("/")[-1].upper())
                return self.enviar(html) if html else self.no_encontrado()
            if ruta == "/panel":
                return self.enviar(paginas.panel_lista())
            if ruta.startswith("/panel/"):
                return self.enviar(paginas.panel(ruta.split("/")[2].upper()))
            if ruta == "/seguimiento":
                return self.enviar(paginas.seguimiento())
            if ruta == "/permisos":
                return self.enviar(paginas.permisos())
            if ruta == "/psicologos/nuevo":
                return self.enviar(paginas.psicologo_nuevo())
            if ruta == "/reportes":
                return self.enviar(paginas.reportes())
            if ruta.startswith("/salidas/"):
                return self.archivo_salida(ruta[len("/salidas/"):])
            return self.no_encontrado()
        except ValueError as error:
            self.enviar(pagina("Aviso", tarjeta("No se pudo mostrar", f'<div class="error">{escapar_html(error)}</div>')), 400)

    def archivo_salida(self, nombre):
        """Solo archivos directos de salidas/ (sin subcarpetas ni '..')."""
        if not nombre or "/" in nombre or "\\" in nombre or ".." in nombre:
            return self.no_encontrado()
        extension = nombre[nombre.rfind("."):].lower() if "." in nombre else ""
        ruta = config.ruta_salida(nombre)
        if extension not in TIPOS or not existe_archivo(ruta):
            return self.no_encontrado()
        with open(ruta, "rb") as archivo:
            self.enviar(archivo.read(), tipo=TIPOS[extension])

    # ---------- POST ----------
    def do_POST(self):
        url = urlparse(self.path)
        ruta = url.path.rstrip("/")
        try:
            if ruta == "/api/voz":
                return self.api_voz(parse_qs(url.query).get("tipo", ["f"])[0])
            datos = self.formulario()
            if ruta == "/orientacion":
                return self.enviar(paginas.orientacion_paso2(datos))
            if ruta == "/orientacion/registrar":
                try:
                    id_paciente = paginas.orientacion_registrar(datos)
                except ValueError as error:
                    return self.enviar(paginas.orientacion_paso2(datos, str(error)))
                return self.redirigir(f"/recomendacion/{id_paciente}")
            if ruta == "/solicitar":
                return self.enviar(paginas.solicitar(datos))
            if ruta.startswith("/panel/") and ruta.endswith("/estado"):
                id_psicologo = ruta.split("/")[2].upper()
                paginas.panel_estado(id_psicologo, datos)
                return self.redirigir(f"/panel/{id_psicologo}")
            if ruta == "/seguimiento":
                try:
                    return self.enviar(paginas.seguimiento_guardar(datos))
                except ValueError as error:
                    return self.enviar(paginas.seguimiento(datos, str(error)))
            if ruta == "/permisos":
                try:
                    return self.enviar(paginas.permisos_guardar(datos))
                except ValueError as error:
                    return self.enviar(paginas.permisos(str(error)))
            if ruta == "/psicologos/nuevo":
                try:
                    return self.enviar(paginas.psicologo_guardar(datos))
                except ValueError as error:
                    return self.enviar(paginas.psicologo_nuevo(str(error)))
            if ruta == "/evaluar":
                return self.enviar(paginas.evaluar())
            return self.no_encontrado()
        except PermissionError:
            from texto.seguridad import evaluar_prioridad
            return self.enviar(paginas.pagina_protocolo(evaluar_prioridad("no quiero vivir")))
        except ValueError as error:
            self.enviar(pagina("Aviso", tarjeta("No se pudo completar",
                        f'<div class="error">{escapar_html(error)}</div>'
                        '<p><a class="boton secundario" href="javascript:history.back()">Regresar</a></p>')), 400)

    def api_voz(self, tipo):
        try:
            datos = self.leer_cuerpo(TAMANO_MAXIMO_AUDIO)
            if datos[:4] != b"RIFF" or datos[8:12] != b"WAVE":
                raise ValueError("El audio recibido no es un WAV válido.")
            respuesta = analizar_audio(datos, "M" if tipo == "m" else "F")
        except Exception as error:
            respuesta = {"error": f"No se pudo analizar el audio: {error}"}
        self.enviar(json.dumps(respuesta, ensure_ascii=False), tipo="application/json; charset=utf-8")


def main():
    try:
        paginas.modelo_texto()
    except (FileNotFoundError, ValueError) as error:
        print(error)
        print("Ejecuta primero: python entrenar_texto.py")
        return
    servidor = ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
    url = f"http://localhost:{PUERTO}"
    print("=" * 60)
    print(" Sistema de Orientación Psicológica - servidor web")
    print(f" Abre en tu navegador: {url}")
    print(" Para detenerlo presiona Ctrl + C")
    print("=" * 60)
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
