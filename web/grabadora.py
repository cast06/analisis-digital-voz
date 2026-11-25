# ==============================================================
# GRABADORA DE VOZ EN EL NAVEGADOR
# ==============================================================
# El navegador captura el microfono con la Web Audio API, convierte
# el audio a WAV PCM de 16 bits a 16 kHz (en JavaScript) y lo envia
# a /api/voz. El servidor lo guarda y lo analiza con nuestros modelos
# (emocion percibida) y, si esta instalado, lo transcribe con vosk.
# localhost cuenta como sitio seguro, asi que el navegador permite
# usar el microfono sin certificado.
# ==============================================================

HTML_GRABADORA = """
<div class="grabadora">
  <button type="button" class="boton" id="boton-grabar">🎙 Grabar mi voz</button>
  <label style="margin:0;font-weight:400">Tipo de voz
    <select id="tipo-voz" style="width:auto;margin-left:6px">
      <option value="f">femenina</option><option value="m">masculina</option>
    </select></label>
  <span class="estado" id="estado-voz">Presiona grabar, habla y vuelve a presionar para terminar.</span>
</div>
<div id="resultado-voz"></div>
<input type="hidden" name="voz_emocion" id="voz_emocion">
<input type="hidden" name="voz_emocion_prob" id="voz_emocion_prob">
<input type="hidden" name="voz_palabra" id="voz_palabra">
"""

SCRIPT_GRABADORA = """
<script>
(function () {
  var boton = document.getElementById("boton-grabar");
  var estado = document.getElementById("estado-voz");
  var contexto = null, fuente = null, procesador = null, flujo = null, trozos = [], grabando = false;

  function aWav(muestras, fs) {
    var buffer = new ArrayBuffer(44 + muestras.length * 2), v = new DataView(buffer);
    function texto(o, s) { for (var i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); }
    texto(0, "RIFF"); v.setUint32(4, 36 + muestras.length * 2, true); texto(8, "WAVE");
    texto(12, "fmt "); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, fs, true); v.setUint32(28, fs * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
    texto(36, "data"); v.setUint32(40, muestras.length * 2, true);
    for (var i = 0; i < muestras.length; i++) {
      var s = Math.max(-1, Math.min(1, muestras[i]));
      v.setInt16(44 + i * 2, s < 0 ? s * 32768 : s * 32767, true);
    }
    return new Blob([buffer], {type: "audio/wav"});
  }

  function a16k(muestras, fs) {          // interpolacion lineal si el navegador no grabo a 16 kHz
    if (fs === 16000) return muestras;
    var n = Math.floor(muestras.length * 16000 / fs), salida = new Float32Array(n);
    for (var i = 0; i < n; i++) {
      var x = i * fs / 16000, j = Math.floor(x), f = x - j;
      salida[i] = muestras[j] * (1 - f) + (muestras[j + 1] || 0) * f;
    }
    return salida;
  }

  async function iniciar() {
    flujo = await navigator.mediaDevices.getUserMedia({audio: true});
    try { contexto = new AudioContext({sampleRate: 16000}); } catch (e) { contexto = new AudioContext(); }
    fuente = contexto.createMediaStreamSource(flujo);
    procesador = contexto.createScriptProcessor(4096, 1, 1);
    trozos = [];
    procesador.onaudioprocess = function (e) { trozos.push(new Float32Array(e.inputBuffer.getChannelData(0))); };
    fuente.connect(procesador); procesador.connect(contexto.destination);
    grabando = true; boton.textContent = "⏹ Terminar"; boton.classList.add("grabando");
    estado.textContent = "Grabando... habla con calma.";
  }

  async function terminar() {
    procesador.disconnect(); fuente.disconnect(); flujo.getTracks().forEach(function (t) { t.stop(); });
    grabando = false; boton.textContent = "🎙 Grabar otra vez"; boton.classList.remove("grabando");
    var total = trozos.reduce(function (a, t) { return a + t.length; }, 0), todo = new Float32Array(total), k = 0;
    trozos.forEach(function (t) { todo.set(t, k); k += t.length; });
    var fs = contexto.sampleRate; contexto.close();
    if (total < fs * 0.5) { estado.textContent = "La grabación fue muy corta. Intenta de nuevo."; return; }
    estado.textContent = "Analizando tu voz...";
    var respuesta = await fetch("/api/voz?tipo=" + document.getElementById("tipo-voz").value,
                                {method: "POST", body: aWav(a16k(todo, fs), 16000)});
    var datos = await respuesta.json();
    var html = "";
    if (datos.error) { estado.textContent = datos.error; return; }
    if (datos.emocion) {
      html += '<span class="etiqueta aceptada">Emoción percibida: ' + datos.emocion + " (" + datos.emocion_prob + " %)</span> ";
      document.getElementById("voz_emocion").value = datos.emocion;
      document.getElementById("voz_emocion_prob").value = datos.emocion_prob;
    }
    if (datos.palabra) {
      html += '<span class="etiqueta pendiente">Palabra: ' + datos.palabra + "</span>";
      document.getElementById("voz_palabra").value = datos.palabra;
    }
    if (datos.texto) {
      var area = document.getElementById("relato");
      area.value = (area.value ? area.value + " " : "") + datos.texto;
      estado.textContent = "Listo. Revisa el texto transcrito y corrígelo si hace falta.";
    } else {
      estado.textContent = datos.aviso || "No se pudo transcribir; escribe tu relato.";
    }
    document.getElementById("resultado-voz").innerHTML = html ? '<p>' + html + '</p>' : "";
  }

  boton.addEventListener("click", function () {
    (grabando ? terminar() : iniciar()).catch(function (e) {
      estado.textContent = "No se pudo usar el micrófono: " + e.message;
    });
  });
})();
</script>
"""
