# ==============================================================
# VOZ EN VIVO (MODULO OPCIONAL CON LIBRERIAS EXTERNAS)
# ==============================================================
# Es la UNICA parte del proyecto que usa librerias externas, y solo
# para dos tareas que Python puro no puede hacer:
#   - sounddevice: acceder al microfono (necesita el controlador de
#     audio del sistema operativo).
#   - vosk: transcribir habla libre a texto (requiere un modelo
#     acustico entrenado con miles de horas de voz).
# Todo lo demas sigue siendo propio: la grabacion se guarda con
# nuestro escritor WAV, y la emocion, la seguridad, el motivo y la
# recomendacion se calculan con nuestros algoritmos.
# Si las librerias no estan instaladas, el sistema sigue funcionando
# con texto o con un archivo .wav.
# ==============================================================
