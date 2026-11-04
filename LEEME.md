# Sistema Inteligente Multimodal de Acceso, Orientación y Vinculación Psicológica

Módulo actual: análisis digital de voz desde cero (Temas Selectos de Aprendizaje Profundo, ESCOM-IPN).

## Cómo ejecutar

Desde esta carpeta:

```
python main.py      # procesa los audios y genera salidas/resultado.html y salidas/resultado_analisis.txt
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

## Estructura

```
main.py                    Programa principal (orquesta todo)
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
orientacion.py             Flujo de orientación integrado
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
| 26. Programa principal | `main.py` |

## Variables acústicas del vector oficial (orden fijo)

Definidas en `audio/caracteristicas.py` → `VARIABLES_SEGMENTO`:

1. amplitud_maxima  2. pico_a_pico  3. rms  4. zcr  5. frecuencia_dominante
6. frecuencia_fundamental  7. variacion_f0  8. duracion  9. tiempo_hablado
10. tiempo_silencio  11. centroide_espectral  12. ancho_banda_espectral

Estas variables describen propiedades físicas de la señal y no se usan como indicador clínico.
