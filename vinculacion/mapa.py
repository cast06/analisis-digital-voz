# ==============================================================
# PAGINA DE RECOMENDACION CON MAPA: salidas/recomendacion_PA###.html
# ==============================================================
#
# Muestra las opciones compatibles como tarjetas (estilo app de
# transporte) junto a un mapa con la zona del paciente y los
# consultorios.
#
# Dos mapas en la misma pagina:
#   1. Leaflet + OpenStreetMap (biblioteca de JavaScript SOLO para
#      dibujar el mapa; necesita internet). Ningun calculo depende
#      de ella: distancias y puntajes vienen de nuestro codigo.
#   2. Mapa esquematico en SVG generado por nosotros (sin internet).
#      Se muestra automaticamente si Leaflet no carga, y hay un boton
#      para cambiar entre ambos.
#
# Proyeccion del SVG (equirrectangular, igual que la distancia):
#     x = (lon - lon_min) * cos(lat_media) * escala
#     y = (lat_max - lat) * escala
# ==============================================================

import config
from nucleo.archivos import guardar_texto
from nucleo.matematicas import coseno
from visual.html import ESTILOS_CSS
from vinculacion.geografia import (
    ALCALDIAS, ubicacion_alcaldia, ubicacion_consultorio, a_radianes, RADIO_TIERRA_KM, distancia_km
)
from vinculacion.panel import escapar_html

URL_LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
URL_LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"

ESTILOS_MAPA = """
.distribucion { display: grid; grid-template-columns: 420px 1fr; gap: 20px; align-items: start; }
.lista { display: flex; flex-direction: column; gap: 14px; max-height: 760px; overflow-y: auto; padding-right: 4px; }
.opcion { background: white; border: 1px solid var(--borde); border-radius: 14px; padding: 16px 18px;
          box-shadow: var(--sombra); cursor: pointer; transition: border-color .15s, transform .15s; }
.opcion:hover, .opcion.activa { border-color: var(--primario); transform: translateY(-2px); }
.opcion .fila { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.numero { width: 30px; height: 30px; border-radius: 50%; background: var(--primario); color: white;
          display: inline-flex; align-items: center; justify-content: center; font-weight: 700; flex: none; }
.opcion h3 { margin: 0; font-size: 16px; color: var(--texto); flex: 1; }
.porcentaje { font-size: 22px; font-weight: 700; color: var(--primario); }
.datos { display: flex; gap: 14px; flex-wrap: wrap; color: var(--suave); font-size: 13px; margin: 8px 0 6px 40px; }
.razones { list-style: none; margin: 6px 0 0 40px; padding: 0; font-size: 13px; }
.razones li { padding: 2px 0; }
.razones .mas { color: var(--ok); } .razones .menos { color: var(--error); }
.contenedor-mapa { position: sticky; top: 16px; background: white; border: 1px solid var(--borde);
                   border-radius: 14px; box-shadow: var(--sombra); overflow: hidden; }
#mapa { height: 620px; }
#mapa-svg { display: none; padding: 10px; }
#mapa-svg svg { width: 100%; height: auto; }
.barra-mapa { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px;
              border-bottom: 1px solid var(--borde); font-size: 13px; color: var(--suave); }
.barra-mapa button { border: 1px solid var(--borde); background: white; border-radius: 999px;
                     padding: 6px 12px; cursor: pointer; font-size: 13px; }
.marcador { background: #1f6f8b; color: white; border-radius: 50%; width: 28px; height: 28px;
            display: flex; align-items: center; justify-content: center; font-weight: 700;
            border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,.35); }
@media (max-width: 950px) { .distribucion { grid-template-columns: 1fr; } .contenedor-mapa { position: static; } }
"""


def _js(texto):
    """Cadena segura para insertar en JavaScript."""
    return '"' + (str(texto).replace("\\", "\\\\").replace('"', '\\"')
                  .replace("<", "\\u003c").replace("\n", " ")) + '"'


def _svg_esquematico(origen, puntos):
    """
    origen: (lat, lon) o None. puntos: lista de (numero, (lat, lon), nombre).
    Dibuja los centros de las alcaldias como referencia, la zona del
    paciente y los consultorios numerados, con lineas punteadas y la
    distancia en km.
    """
    todos = list(ALCALDIAS.values())
    lat_min = min(p[0] for p in todos) - 0.02
    lat_max = max(p[0] for p in todos) + 0.02
    lon_min = min(p[1] for p in todos) - 0.03
    lon_max = max(p[1] for p in todos) + 0.03
    factor = coseno(a_radianes((lat_min + lat_max) / 2))
    ancho = 760
    escala = ancho / ((lon_max - lon_min) * factor)
    alto = int((lat_max - lat_min) * escala)

    def xy(punto):
        return ((punto[1] - lon_min) * factor * escala, (lat_max - punto[0]) * escala)

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}">'
           f'<rect width="{ancho}" height="{alto}" fill="#f7f9fb"/>')
    # cuadricula cada 0.05 grados
    paso = 0.05
    valor = int(lat_min / paso) * paso
    while valor <= lat_max:
        y = (lat_max - valor) * escala
        svg += f'<line x1="0" y1="{y:.1f}" x2="{ancho}" y2="{y:.1f}" stroke="#e3e8ee"/>'
        valor += paso
    valor = int(lon_min / paso) * paso
    while valor <= lon_max:
        x = (valor - lon_min) * factor * escala
        svg += f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{alto}" stroke="#e3e8ee"/>'
        valor += paso
    for nombre, punto in ALCALDIAS.items():
        x, y = xy(punto)
        svg += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#b8c2cc"/>'
                f'<text x="{x + 6:.1f}" y="{y + 4:.1f}" font-family="Arial" font-size="11" '
                f'fill="#8a96a3">{escapar_html(nombre)}</text>')
    if origen:
        ox, oy = xy(origen)
        for numero, punto, _ in puntos:
            x, y = xy(punto)
            km = distancia_km(origen, punto)
            svg += (f'<line x1="{ox:.1f}" y1="{oy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#1f6f8b" '
                    f'stroke-dasharray="5 4" stroke-width="1.5"/>'
                    f'<text x="{(ox + x) / 2:.1f}" y="{(oy + y) / 2 - 4:.1f}" font-family="Arial" '
                    f'font-size="11" fill="#1f6f8b" text-anchor="middle">{km:.1f} km</text>')
        radio = 1.5 / (RADIO_TIERRA_KM * a_radianes(1)) * escala   # 1.5 km en pixeles
        svg += (f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{radio:.1f}" fill="#e2725b" fill-opacity="0.18" '
                f'stroke="#e2725b"/><circle cx="{ox:.1f}" cy="{oy:.1f}" r="6" fill="#e2725b"/>'
                f'<text x="{ox:.1f}" y="{oy - radio - 6:.1f}" font-family="Arial" font-size="12" '
                f'font-weight="bold" fill="#c0503a" text-anchor="middle">Tu zona</text>')
    for numero, punto, nombre in puntos:
        x, y = xy(punto)
        svg += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="#1f6f8b" stroke="white" stroke-width="2"/>'
                f'<text x="{x:.1f}" y="{y + 4.5:.1f}" font-family="Arial" font-size="13" font-weight="bold" '
                f'fill="white" text-anchor="middle">{numero}</text>')
    # barra de escala de 5 km
    largo = 5 / (RADIO_TIERRA_KM * a_radianes(1)) * escala
    svg += (f'<line x1="20" y1="{alto - 20}" x2="{20 + largo:.1f}" y2="{alto - 20}" stroke="#333" stroke-width="3"/>'
            f'<text x="20" y="{alto - 28}" font-family="Arial" font-size="11" fill="#333">5 km</text>')
    return svg + "</svg>"


def generar_recomendacion_html(paciente, opciones):
    """Escribe salidas/recomendacion_<ID>.html y devuelve su ruta."""
    origen = ubicacion_alcaldia(paciente.get("alcaldia", ""))
    tarjetas, marcadores, puntos = "", [], []
    for numero, opcion in enumerate(opciones, start=1):
        p = opcion["psicologo"]
        lugar = ubicacion_consultorio(p) if "presencial" in p["modalidad"] else None
        distancia = opcion.get("distancia")
        datos = ["Gratuito" if p["costo"] == 0 else f"${p['costo']}",
                 " · ".join("En línea" if m == "linea" else "Presencial" for m in p["modalidad"])]
        if distancia is not None:
            datos.append(f"{distancia:.1f} km")
        elif lugar is None:
            datos.append("Solo en línea")
        razones = "".join(
            f'<li class="{"mas" if signo == "+" else "menos"}">{"✓" if signo == "+" else "✗"} '
            f'{escapar_html(frase)}</li>' for signo, frase in opcion["razones"])
        tarjetas += (f'<div class="opcion" data-numero="{numero}"><div class="fila">'
                     f'<span class="numero">{numero}</span><h3>{escapar_html(p["nombre"])}</h3>'
                     f'<span class="porcentaje">{opcion["total"] * 100:.0f}%</span></div>'
                     f'<div class="datos">{"".join(f"<span>{escapar_html(d)}</span>" for d in datos)}</div>'
                     f'<ul class="razones">{razones}</ul></div>')
        if lugar is not None:
            puntos.append((numero, lugar, p["nombre"]))
            texto_dist = f"{distancia:.1f} km" if distancia is not None else ""
            marcadores.append(f"{{n:{numero},lat:{lugar[0]:.5f},lon:{lugar[1]:.5f},"
                              f"nombre:{_js(p['nombre'])},compat:{opcion['total'] * 100:.0f},"
                              f"lugar:{_js(p.get('alcaldia', ''))},dist:{_js(texto_dist)}}}")

    origen_js = f"[{origen[0]:.5f},{origen[1]:.5f}]" if origen else "null"
    aviso_zona = ("" if origen else '<div class="info">No indicaste alcaldía, así que el mapa no '
                  'muestra distancias. Puedes elegir atención presencial para verlas.</div>')
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Profesionales compatibles - {escapar_html(paciente['alias'])}</title>
<link rel="stylesheet" href="{URL_LEAFLET_CSS}">
<style>{ESTILOS_CSS} .ventana {{ display: block; }} {ESTILOS_MAPA}</style></head>
<body>
<div class="encabezado"><h1>Profesionales compatibles</h1>
<p>{escapar_html(paciente['alias'])} ({escapar_html(paciente['id'])}) · ordenados por compatibilidad · tú decides</p></div>
<div class="contenedor">
<p><a href="inicio.html">← Volver al inicio</a></p>
<div class="aviso">Orientación automática, no diagnóstico. Las distancias son aproximadas: se calculan
desde el centro de tu alcaldía. Los profesionales son ficticios.</div>
{aviso_zona}
<div class="distribucion">
<div class="lista">{tarjetas}</div>
<div class="contenedor-mapa">
<div class="barra-mapa"><span id="tipo-mapa">Mapa</span>
<button id="cambiar" onclick="cambiarMapa()">Ver mapa sin internet</button></div>
<div id="mapa"></div>
<div id="mapa-svg">{_svg_esquematico(origen, puntos)}</div>
</div></div></div>
<div class="pie">Página generada por <code>python main.py</code> · mapa: Leaflet y OpenStreetMap
(solo visualización) o mapa esquemático propio</div>
<script src="{URL_LEAFLET_JS}"></script>
<script>
var ORIGEN = {origen_js};
var PUNTOS = [{",".join(marcadores)}];
var usandoSvg = false, mapa = null, capas = {{}};
function mostrarSvg() {{
  document.getElementById("mapa").style.display = "none";
  document.getElementById("mapa-svg").style.display = "block";
  document.getElementById("tipo-mapa").textContent = "Mapa esquemático (sin internet)";
  document.getElementById("cambiar").textContent = "Ver mapa real";
  usandoSvg = true;
}}
function mostrarLeaflet() {{
  if (typeof L === "undefined") {{ alertaSinInternet(); return; }}
  document.getElementById("mapa-svg").style.display = "none";
  document.getElementById("mapa").style.display = "block";
  document.getElementById("tipo-mapa").textContent = "Mapa real (requiere internet)";
  document.getElementById("cambiar").textContent = "Ver mapa sin internet";
  usandoSvg = false;
  if (!mapa) iniciarLeaflet(); else mapa.invalidateSize();
}}
function alertaSinInternet() {{
  document.getElementById("tipo-mapa").textContent = "Sin internet: se muestra el mapa esquemático";
  document.getElementById("cambiar").style.display = "none";
}}
function cambiarMapa() {{ if (usandoSvg) mostrarLeaflet(); else mostrarSvg(); }}
function iniciarLeaflet() {{
  mapa = L.map("mapa");
  // Estilo claro tipo app de transporte (CARTO Voyager, datos de OpenStreetMap).
  // Si sus mosaicos fallan, se cambia al mapa estandar de OpenStreetMap.
  var estilo = L.tileLayer("https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png",
    {{maxZoom: 19, subdomains: "abcd", attribution: "© OpenStreetMap · © CARTO"}}).addTo(mapa);
  var fallas = 0;
  estilo.on("tileerror", function () {{
    fallas += 1;
    if (fallas === 4) {{
      mapa.removeLayer(estilo);
      L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
                  {{maxZoom: 19, attribution: "© OpenStreetMap"}}).addTo(mapa);
    }}
  }});
  var limites = [];
  if (ORIGEN) {{
    L.circle(ORIGEN, {{radius: 1500, color: "#e2725b", fillOpacity: 0.15}}).addTo(mapa)
      .bindPopup("<b>Tu zona</b> (aproximada)");
    limites.push(ORIGEN);
  }}
  PUNTOS.forEach(function (p) {{
    var icono = L.divIcon({{className: "", html: '<div class="marcador">' + p.n + '</div>',
                           iconSize: [28, 28], iconAnchor: [14, 14]}});
    var m = L.marker([p.lat, p.lon], {{icon: icono}}).addTo(mapa).bindPopup(
      "<b>" + p.n + ". " + p.nombre + "</b><br>Compatibilidad " + p.compat + " %<br>" +
      p.lugar + (p.dist ? " · " + p.dist : ""));
    if (ORIGEN) L.polyline([ORIGEN, [p.lat, p.lon]], {{color: "#1f6f8b", dashArray: "6 6", weight: 2}}).addTo(mapa);
    capas[p.n] = m;
    limites.push([p.lat, p.lon]);
  }});
  if (limites.length > 1) mapa.fitBounds(limites, {{padding: [40, 40]}});
  else if (limites.length === 1) mapa.setView(limites[0], 13);
  else mapa.setView([19.40, -99.14], 11);
}}
document.querySelectorAll(".opcion").forEach(function (tarjeta) {{
  tarjeta.addEventListener("click", function () {{
    document.querySelectorAll(".opcion").forEach(function (t) {{ t.classList.remove("activa"); }});
    tarjeta.classList.add("activa");
    var n = tarjeta.getAttribute("data-numero");
    if (!usandoSvg && mapa && capas[n]) {{ mapa.setView(capas[n].getLatLng(), 14); capas[n].openPopup(); }}
  }});
}});
if (typeof L === "undefined") {{ mostrarSvg(); alertaSinInternet(); }} else {{ mostrarLeaflet(); }}
</script>
</body></html>
"""
    ruta = config.ruta_salida(f"recomendacion_{paciente['id']}.html")
    guardar_texto(ruta, html)
    return ruta
