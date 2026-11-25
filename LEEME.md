# Sistema Inteligente Multimodal de Acceso, Orientación y Vinculación Psicológica

Prototipo desde cero: análisis de voz, texto, vinculación con psicólogos y seguimiento (Temas Selectos de Aprendizaje Profundo, ESCOM-IPN).

## Cómo ejecutar

Desde esta carpeta:

```
python servidor.py             # PÁGINA WEB: todo el sistema en http://localhost:8000
python main.py                 # MENÚ PRINCIPAL: orientación, recomendación, panel, seguimiento y evaluación
python analisis_senales.py     # experimentos de señales: genera salidas/resultado.html
python evaluar_vinculacion.py  # evalúa la extracción y el matching
python pruebas.py   # pruebas con valores conocidos
python entrenar_emociones.py   # entrena y evalúa el reconocimiento de emociones (MESD)
python entrenar_palabras.py    # entrena y evalúa el reconocimiento de palabras aisladas (MESD)
python clasificar_voz.py       # dice qué palabra se dijo y con qué emoción en un .wav
python entrenar_texto.py       # entrena y evalúa motivos de consulta y prioridad
python orientacion.py          # flujo completo de orientación (texto + voz opcional)
```

1. Copia las grabaciones `.wav` a `audios/` (también se buscan en `C:\Users\sharo\Downloads\nuevo`).
2. La lista de grabaciones está en `config.py` (`ARCHIVOS_AUDIO_LOTE`).
3. Los resultados aparecen en `salidas/`.

## Restricción de librerías

**Excepción declarada: `voz_en_vivo/`** (opcional). Python sin librerías no puede abrir el micrófono
ni transcribir habla libre, así que solo ese módulo usa `sounddevice` (micrófono) y `vosk`
(transcripción sin internet). La grabación se guarda con nuestro escritor WAV y todo el análisis
posterior (emoción, seguridad, motivo, extracción, recomendación) sigue siendo propio. Si esas
librerías no están instaladas, el sistema funciona igual con texto o con un archivo `.wav`.


El programa no importa nada: ni librerías externas ni módulos de la biblioteca estándar
(se quitaron `pathlib` y `time`). Las únicas líneas `import` son entre archivos propios del proyecto.
Se usan solo funciones nativas de Python (`open`, `print`, `len`, `sum`, `min`, `max`, `sorted`, `zip`...).

Consecuencias de no usar `os`/`pathlib`/`time`:

- No se pueden crear carpetas: `audios/`, `salidas/` y `referencias/` ya vienen creadas.
- No se puede listar una carpeta: las grabaciones de referencia se declaran en `referencias/indice.txt`.
- No se puede medir el tiempo de procesamiento (latencia). Si el profesor permite `time`, se puede volver a agregar.

## Reconocimiento de emociones en la voz (MESD)

El modelo distingue 4 emociones percibidas en la voz: neutral, tristeza, enojo y alegría.
Usa solo las voces adultas (F y M) de la Mexican Emotional Speech Database.
Es un resultado orientativo, no un diagnóstico.

### 1. Generar la lista de archivos (una sola vez)

El programa no puede recorrer carpetas sin módulos externos, así que necesita una lista
con la ruta de cada `.wav`. Abre **PowerShell** dentro de la carpeta del proyecto y ejecuta
(cambia la ruta por la carpeta donde descomprimiste MESD):

```
Get-ChildItem -Path "C:\Users\sharo\Downloads\MESD" -Recurse -Filter *.wav | ForEach-Object { $_.FullName } | Set-Content -Encoding UTF8 datos\lista_mesd.txt
```

Se crea `datos/lista_mesd.txt` con una ruta por línea.

### 2. Entrenar y evaluar

```
python entrenar_emociones.py
```

- La primera vez calcula las variables de cada grabación (puede tardar varios minutos) y las
  guarda en `datos/caracteristicas_mesd.csv`. Las siguientes veces las lee de ahí.
- Compara una regresión softmax (línea base) contra una red neuronal MLP con validación cruzada
  de 5 pliegues agrupada por palabra.
- Guarda el modelo en `datos/modelo_emociones.txt` y los reportes en
  `salidas/reporte_emociones.txt` y `salidas/reporte_emociones.html`.

Revisa en la terminal el conteo por emoción y tipo de voz. Con MESD completo deberían
salir 48 grabaciones por emoción y tipo de voz (384 en total). Si salen más, la lista
incluye también las versiones de naturalidad reducida; en ese caso genera la lista solo
con la carpeta de las grabaciones originales.

Si cambias las variables o quieres recalcular todo, borra `datos/caracteristicas_mesd.csv`.

### 3. Clasificar una grabación nueva

```
python clasificar_voz.py
```

Pide la ruta del `.wav` y el tipo de voz (F o M), y muestra la probabilidad de cada emoción.

### Variables usadas para emociones (11)

Definidas en `audio/caracteristicas.py` → `VARIABLES_EMOCION`: rms, variacion_rms, zcr,
frecuencia_dominante, centroide_espectral, ancho_banda_espectral, frecuencia_fundamental,
variacion_f0, rango_f0, proporcion_silencio y tasa_silabica.

## Reconocimiento de palabras aisladas (MESD, corpus A)

Reconoce qué palabra se dijo dentro de un **vocabulario cerrado**: las 24 palabras del
corpus A de MESD, que se repiten en las 6 emociones y en las voces de mujer, hombre y niño.
No transcribe frases ni habla libre.

Usa la misma lista `datos/lista_mesd.txt` que las emociones. Para entrenar:

```
python entrenar_palabras.py
```

- La primera vez calcula los MFCC de cada grabación y los guarda en
  `datos/caracteristicas_palabras.csv`.
- Hace dos evaluaciones: por tipo de voz (se prueba con una voz que el modelo nunca
  escuchó) y estratificada de 5 pliegues.
- Guarda el modelo en `datos/modelo_palabras.txt` y los reportes en
  `salidas/reporte_palabras.txt` y `salidas/reporte_palabras.html`.

Con MESD completo deberían salir 432 grabaciones (24 palabras × 6 emociones × 3 voces).

Método: preénfasis → ventanas de 25 ms → Hann → FFT de 512 puntos → banco de 26 filtros
mel → logaritmo → DCT (13 coeficientes) → normalización de media cepstral → promedio en
5 tramos de la palabra (65 valores) → red neuronal.

## Módulo de texto: motivos de consulta y prioridad

```
python entrenar_texto.py
python orientacion.py
```

- `entrenar_texto.py` compara Naive Bayes contra una red neuronal sobre TF-IDF, con validación
  cruzada y con un conjunto de prueba aparte. También evalúa el módulo de prioridad. Guarda el
  modelo en `datos/modelo_texto.txt` y los reportes en `salidas/reporte_texto.*`.
- `orientacion.py` es el flujo para el paciente: consentimiento → relato libre → prioridad
  (primero) → motivo inferido + duración y contextos → voz opcional → preferencias →
  perfil preliminar no diagnóstico en `salidas/perfil_###.txt`.

Categorías de motivo (8): estrés, ansiedad percibida, problemas de sueño, duelo o pérdida,
relaciones, soledad o aislamiento, escuela o trabajo, ánimo bajo.

Niveles de prioridad: **protocolo** (riesgo para la vida o violencia: se detiene la orientación
y se muestran la Línea de la Vida 800 911 2000 y el 911), **prioritario** (malestar intenso o
desesperanza: se continúa marcado) y **ordinario**.

Los corpus están en `corpus/` y son **sintéticos**. Para mejorar la evaluación, otro integrante
del equipo debe escribir frases nuevas en `corpus/motivos_prueba.txt` y casos nuevos en
`corpus/casos_seguridad.txt` sin ver los de entrenamiento ni las reglas.

## Página web (`python servidor.py`)

Todo el sistema funciona desde el navegador en `http://localhost:8000` (se abre solo):

| Página | Qué hace |
|---|---|
| `/` | Inicio con accesos y resultados de los modelos |
| `/orientacion` | Paso 1: consentimiento, grabar voz o escribir el relato · Paso 2: tema inferido y confirmación · Paso 3: preferencias |
| `/recomendacion/PA###` | Opciones compatibles con mapa y botón "Solicitar contacto" |
| `/panel`, `/panel/PS##` | Panel del psicólogo: aceptar o rechazar, resumen autorizado, seguimiento |
| `/seguimiento` | Registro de ánimo y sueño con gráficas |
| `/permisos` | Retirar el permiso de compartir el resumen |
| `/psicologos/nuevo` | Registrar un profesional |
| `/reportes` | Reportes de evaluación y hoja de anotación |

- La capa web usa solo la **biblioteca estándar** (`http.server`, `urllib.parse`, `json`, `webbrowser`);
  no se instala ningún framework. Escucha solo en `127.0.0.1`: los datos no salen de la computadora.
- La grabación de voz usa el micrófono del navegador (Web Audio API), convierte a WAV 16 kHz en
  JavaScript y lo envía al servidor, que lo analiza con nuestro modelo de emociones y lo transcribe
  con vosk si está instalado.
- Para detener el servidor: `Ctrl + C` en la terminal.
- Colores institucionales: guinda IPN (#6C1D45) y blanco, con acentos dorados (#B38E5D).

## Vinculación: psicólogos, compatibilidad, solicitudes, panel y seguimiento

```
python entrenar_texto.py   # una vez, si no existe datos/modelo_texto.txt
python main.py
```

Menú de `main.py`:

| Opción | Quién | Qué hace |
|---|---|---|
| 1 | Paciente | Orientación inicial → registro (PA###) → profesionales compatibles → solicitud |
| 2 | Paciente | Volver a ver las opciones compatibles |
| 3 | Paciente | Registrar seguimiento entre sesiones (fecha, ánimo 1-10, horas de sueño, nota) |
| 4 | Paciente | Retirar el permiso para compartir el resumen (también borra el relato guardado) |
| 5 | Psicólogo | Panel: ver solicitudes, leer el resumen autorizado, aceptar o rechazar, ver seguimiento |
| 6 | Psicólogo | Registrar un perfil nuevo |
| 7 | Todos | Generar `salidas/inicio.html` (página de inicio con reportes y paneles) |
| 8 | Equipo | Evaluar extracción y matching (`salidas/reporte_vinculacion.html`) |

Archivos de datos (formato por bloques `[ID]` + `clave = valor`, editables a mano):

- `datos/psicologos.txt`: 18 perfiles **ficticios** (PS07 no acepta pacientes, para probar el filtro).
- `datos/pacientes.txt`, `datos/solicitudes.txt`, `datos/seguimiento.txt`: los crea el programa.
  Tienen datos personales: **no subirlos a GitHub**.
- El panel se genera como página en `salidas/panel_PS##.html` cada vez que se usa la opción 5.
- La opción 7 genera todos los paneles y `salidas/inicio.html`, que enlaza los reportes y paneles.
  Ábrela con doble clic para la presentación.

### Algoritmo de compatibilidad (`vinculacion/compatibilidad.py`)

- Necesidad del paciente: **n** = probabilidades del clasificador de texto para los 8 temas.
- Experiencia del psicólogo: **e** = pesos de 0 a 1 por tema.
- Afinidad temática: s_tema = (n · e) / (‖n‖ ‖e‖) (similitud coseno, en [0, 1]).
- Costo: 1 si está dentro del presupuesto M; si lo supera, max(0, 1 − (c − M)/M); con M = 0 solo cuenta lo gratuito.
- Modalidad y horario: 1 si coinciden o el paciente elige "cualquiera", 0 si no.
- Puntaje: S = 0.55·s_tema + 0.20·s_costo + 0.15·s_modalidad + 0.10·s_horario (pesos en `config.py`).
- Filtros obligatorios: idioma y "acepta pacientes nuevos". Los excluidos se informan con su motivo.
- Se muestran las 5 mejores opciones con sus razones a favor y en contra; la persona elige.
- Complejidad: O(P·K) con P psicólogos y K temas.

### Voz en vivo (opcional)

1. Instalar las librerías (una vez):
   ```
   pip install -r requisitos_voz.txt
   ```
2. Descargar el modelo en español `vosk-model-small-es-0.42` (39 MB, licencia Apache 2.0) desde
   https://alphacephei.com/vosk/models y descomprimirlo dentro de `datos/`, de modo que exista
   `datos/vosk-model-small-es-0.42/am/final.mdl`.
3. En la orientación elegir **voz → grabar**: se graba hasta presionar Enter, se guarda en
   `salidas/grabacion_###.wav`, se analiza la emoción percibida con nuestro modelo, se transcribe
   con vosk y la persona confirma o corrige el texto antes de continuar.

Si falta el micrófono o el modelo, el programa dice exactamente qué falta y deja seguir por texto.
La palabra del vocabulario cerrado solo se busca en grabaciones cortas (≤ 2 s), porque el modelo
se entrenó con palabras sueltas.

### Ubicación y mapa (`vinculacion/geografia.py`, `vinculacion/mapa.py`)

- Si la persona acepta atención presencial, elige su **alcaldía** (no se pide dirección).
  Los consultorios ficticios están cerca del centro de su alcaldía.
- Distancia equirrectangular: d = R·√((Δλ·cos φ̄)² + (Δφ)²), R = 6371 km (solo coseno y raíz propios).
- Cercanía: 1 hasta 5 km, baja en línea recta y vale 0 desde 25 km. Si la persona pidió presencial,
  s_modalidad = coincide × cercanía.
- Cada recomendación genera `salidas/recomendacion_PA###.html`: tarjetas con las opciones y un mapa.
  Con internet se usa **Leaflet + OpenStreetMap** (librería de JavaScript solo para dibujar; ningún
  cálculo depende de ella). Sin internet se muestra automáticamente un **mapa esquemático en SVG**
  generado por nuestro código, y hay un botón para cambiar entre ambos.

### Seguimiento (`vinculacion/seguimiento.py`)

- Cambio reciente: Δ = media(últimas 3 sesiones) − media(sesiones anteriores); se marca si
  |Δ| ≥ 2 puntos de ánimo o 1.5 horas de sueño. Requiere al menos 5 registros.
- Tendencia: pendiente de mínimos cuadrados b = Σ(t − t̄)(x − x̄) / Σ(t − t̄)².
- Los mensajes son informativos para el profesional; no son conclusiones clínicas.
- El profesional solo ve los registros que el paciente marcó como compartidos y solo si aceptó la solicitud.

### Privacidad en el prototipo

- No se pide nombre completo, solo un alias.
- El relato completo solo se guarda si el paciente autoriza compartirlo.
- El resumen siempre indica que se generó automáticamente y que no es un diagnóstico.
- Si el paciente retira el permiso, el panel deja de mostrar su resumen.

### Flujo de la orientación (opción 1)

Consentimiento → elegir texto o voz → (voz: emoción percibida y palabra reconocida en un .wav) →
relato escrito → seguridad → tema inferido → **la persona confirma o corrige el tema** → duración →
preferencias → permiso para compartir → registro → profesionales compatibles → solicitud.

Si la persona corrige el tema: n = 0.6 · (tema elegido) + 0.4 · (probabilidades del modelo).
Limitación: sin librerías no se puede transcribir habla libre; la voz aporta emoción percibida y
una palabra del vocabulario cerrado, y el relato se escribe.

### Evaluación (`python evaluar_vinculacion.py` u opción 8)

- **Extracción por campo** con `corpus/extraccion_prueba.txt` (40 frases etiquetadas):
  duración (detección P/R/F1, valor exacto, campo correcto) y contextos (P/R/F1 por contexto,
  micro-promedio y conjunto exacto).
- **Matching** con `corpus/evaluacion_matching.txt` (20 casos). Cada integrante llena su línea
  `orden_...` con los 3 psicólogos que elegiría, **sin ver la recomendación del programa**, usando
  `salidas/hoja_anotacion_matching.html`. Se calcula precision@3 y acierto@1 contra cada anotador
  y contra el consenso (conteo de Borda), el acuerdo entre anotadores y la referencia de azar (3/N).
  También se comparan tres variantes de pesos: completo, solo tema y solo criterios prácticos.

## Estructura

```
main.py                    Menú principal: conecta todos los módulos
analisis_senales.py        Experimentos de señales (antes main.py)
config.py                  Constantes, rutas y listas de archivos
pruebas.py                 Pruebas verificables
nucleo/
    matematicas.py         seno, coseno, raíz cuadrada, media, desviación estándar
    archivos.py            Rutas y lectura/escritura sin pathlib
audio/
    wav.py                 Lector WAV PCM manual
    senales.py             Señales sintéticas (seno, seno+coseno, compleja)
    espectral.py           Ventaneo, Hann, DFT, frecuencias dominantes
    caracteristicas.py     RMS, ZCR, F0, centroide, ancho de banda, vector de 12 variables
    segmentacion.py        Detección de actividad de voz (VAD) y análisis continuo
    referencias.py         Banco de referencias y distancia euclidiana ponderada
visual/
    svg.py                 Gráficas SVG
    html.py                Página de resultados por secciones
reportes/
    formato.py             Formato de valores para TXT y HTML
    lote.py                Procesamiento por lotes e informe TXT
experimentos/
    sinteticos.py          Experimentos 1-3 y abecedario (demostración)
    voz.py                 Vista detallada de una grabación y fragmentos marcados
nucleo/aleatorio.py        Generador pseudoaleatorio propio (LCG, Box-Muller, Fisher-Yates)
audio/remuestreo.py        Filtro pasa bajas FIR propio y diezmado 48 kHz -> 16 kHz
emociones/
    mesd.py                Lectura de MESD, extracción de variables y caché
    preparacion.py         Normalización por tipo de voz y pliegues por palabra
    modelo_emocion.py      Validación cruzada, modelo final, guardar/cargar, predicción
modelos/
    red_neuronal.py        Red neuronal MLP con retropropagación
    evaluacion.py          Matriz de confusión, precision, recall, F1
audio/fft.py               FFT radix-2 (Cooley-Tukey) desde cero
audio/mfcc.py              MFCC: banco mel, DCT, normalización cepstral
audio/preparar.py          Lectura + 16 kHz + volumen + recorte de silencios
nucleo/tabla.py            Caché de características en texto
palabras/
    datos_palabras.py      Lectura del corpus A y vectores MFCC
    modelo_palabras.py     Evaluación, modelo final y reconocimiento
entrenar_palabras.py       Script de entrenamiento y reporte de palabras
entrenar_emociones.py      Script de entrenamiento y reporte
clasificar_voz.py          Palabra y emoción de un .wav
texto/
    nlp.py                 Normalización, tokens, negación, raíces, n-gramas, TF-IDF
    seguridad.py           Módulo de prioridad (reglas, niveles, recursos)
    extraccion.py          Duración de la dificultad y contextos mencionados
    modelo_texto.py        Entrenamiento, guardado y predicción de motivos
modelos/naive_bayes.py     Naive Bayes multinomial
corpus/                    Frases de entrenamiento, prueba y casos de seguridad
entrenar_texto.py          Script de entrenamiento y reporte de texto
orientacion.py             Flujo de orientación integrado (incluye recomendación y solicitud)
vinculacion/
    almacen.py             Registros en archivos de texto por bloques
    registro.py            Psicólogos y pacientes: validación, alta y consulta
    compatibilidad.py      Similitud coseno + criterios ponderados + explicación
    solicitudes.py         Solicitudes, resumen para el profesional y consentimiento
    seguimiento.py         Registros entre sesiones, cambio reciente y tendencia
    panel.py               Página HTML del panel del psicólogo
    geografia.py           Alcaldías, distancia y cercanía
    mapa.py                Página de recomendación con mapa (Leaflet o SVG propio)
servidor.py                Servidor web (biblioteca estándar)
web/
    diseno.py              Navegación, estilos guinda y piezas de formulario
    paginas.py             Páginas y acciones (llaman a los módulos propios)
    grabadora.py           Grabación de voz en el navegador (JavaScript)
voz_en_vivo/               ÚNICO módulo con librerías (opcional)
    microfono.py           Grabación con sounddevice
    transcripcion.py       Transcripción con vosk
audio/escritura_wav.py     Escritor WAV PCM 16 bits hecho a mano
requisitos_voz.txt         Librerías del módulo opcional
visual/portal.py           Página de inicio (salidas/inicio.html)
vinculacion/evaluacion.py  Métricas de extracción y matching (precision@3, Borda, acuerdo)
evaluar_vinculacion.py     Script de evaluación y hoja de anotación
datos/                     Lista de MESD, caché de variables y modelo entrenado
```

## De dónde salió cada parte del archivo anterior

| Sección en `main_actualizado.py` | Archivo nuevo |
|---|---|
| 1. Constantes y rutas | `config.py` |
| 2. Funciones matemáticas, 6. Máximo absoluto | `nucleo/matematicas.py` |
| 3-5. Seno, seno+coseno, señal compleja | `audio/senales.py` |
| 7, 16. SVG de señal y espectro; abecedario, segmentación y barras | `visual/svg.py` |
| 8-9. Little-endian y lector WAV | `audio/wav.py` |
| 10-13. Ventanas, Hann, DFT, frecuencias dominantes | `audio/espectral.py` |
| 14-15. RMS, ZCR; extracción de características; núcleos silábicos; segmento completo | `audio/caracteristicas.py` |
| Detección de segmentos (VAD); análisis continuo | `audio/segmentacion.py` |
| Banco de referencias y comparación | `audio/referencias.py` |
| 18-20. Experimentos 1-3; ondas del abecedario | `experimentos/sinteticos.py` |
| 21-23. Ventana de voz, voz real, fragmentos | `experimentos/voz.py` |
| 17, 24. Conversión a HTML y página web | `visual/html.py` |
| Formateo de características | `reportes/formato.py` |
| 25. Procesamiento por lotes e informe | `reportes/lote.py` |
| 26. Programa principal | `analisis_senales.py` |

## Variables acústicas del vector oficial (orden fijo)

Definidas en `audio/caracteristicas.py` → `VARIABLES_SEGMENTO`:

1. amplitud_maxima  2. pico_a_pico  3. rms  4. zcr  5. frecuencia_dominante
6. frecuencia_fundamental  7. variacion_f0  8. duracion  9. tiempo_hablado
10. tiempo_silencio  11. centroide_espectral  12. ancho_banda_espectral

Estas variables describen propiedades físicas de la señal y no se usan como indicador clínico.
