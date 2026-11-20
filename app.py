"""DevSquad — interfaz web con Streamlit.

Ejecutar:  streamlit run app.py
"""
import html
import os
import socket
import time
from pathlib import Path

import segno
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from devsquad import Empresa, Mensaje, Proyecto, crear_modelo
from devsquad.buzon import Buzon

load_dotenv(Path(__file__).with_name(".env"))
st.set_page_config(page_title="DevSquad", layout="wide", initial_sidebar_state="collapsed")

ROMANOS = ["I", "II", "III", "IV", "V"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@300;400;500&display=swap');
:root {
  --bg: #0D0C0A; --surface: #13120F; --line: #26231E; --line-2: #34302A;
  --ivory: #ECE6D9; --text: #CFC8BA; --muted: #8A8377; --faint: #5B564D; --brass: #A89270;
}
html, body, .stApp, .stMarkdown, p, li, td, th, button, input, textarea, label, select,
span:not([data-testid="stIconMaterial"]), div { font-family: 'Inter', sans-serif !important; }
.serif, .serif *, .hero h1, .hero h1 *, .kpi .value, .step .name, .av, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: 'Cormorant Garamond', Georgia, serif !important; }
code, pre, code *, pre * { font-family: ui-monospace, 'SFMono-Regular', Consolas, monospace !important; }

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] { background: transparent; }
.stApp { background: var(--bg); }
.block-container { padding-top: 3.4rem; max-width: 1120px; }
[data-testid="stSidebar"] { background: #0F0E0C; border-right: 1px solid var(--line); }

/* etiquetas en versalitas */
.label, .eyebrow, .section, .step .st, .step .num, .time, .badge, .kpi .label, .role-cap {
  font-size: 10.5px !important; letter-spacing: .22em; text-transform: uppercase; font-weight: 400; }
.eyebrow { color: var(--muted); }

.hero { text-align: center; padding: 10px 0 6px; }
.hero .rule { width: 46px; height: 1px; background: var(--brass); margin: 22px auto; opacity: .7; }
.hero h1 { font-size: 64px; line-height: 1.02; font-weight: 400; letter-spacing: -0.01em; color: var(--ivory);
           margin: 0 0 18px; padding: 0; }
.hero h1 em { font-style: italic; color: var(--brass); font-weight: 400; }
.hero p { font-size: 15px; color: var(--muted); max-width: 560px; margin: 0 auto; line-height: 1.75; font-weight: 300; }
.motor { margin-top: 26px; color: var(--faint); }

.section { color: var(--muted); margin: 48px 0 16px; display: flex; align-items: center; gap: 18px; }
.section::after { content: ""; flex: 1; height: 1px; background: var(--line); }

/* equipo */
.pipe { display: grid; grid-template-columns: repeat(5, 1fr); border-top: 1px solid var(--line);
        border-bottom: 1px solid var(--line); margin-top: 30px; }
.step { padding: 20px 18px 18px; border-right: 1px solid var(--line); position: relative; transition: all .4s; }
.step:last-child { border-right: none; }
.step .num { color: var(--faint); font-family: 'Cormorant Garamond', serif !important; font-size: 14px !important;
             letter-spacing: .1em; }
.step .name { font-size: 24px; color: var(--ivory); margin-top: 10px; font-weight: 500; }
.step .rol { font-size: 12px; color: var(--muted); margin-top: 2px; font-weight: 300; }
.step .st { color: var(--faint); margin-top: 16px; }
.step.encurso::before { content: ""; position: absolute; top: -1px; left: 0; right: 0; height: 1px; background: var(--brass); }
.step.encurso .st { color: var(--brass); }
.step.concluido .st { color: var(--text); }

/* mensajes */
.msg-head { display: flex; align-items: center; gap: 14px; margin-bottom: 8px; }
.av { border-radius: 50%; border: 1px solid var(--line-2); color: var(--ivory); font-size: 15px; font-weight: 500;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0; letter-spacing: .04em; }
.who { font-size: 14px; font-weight: 500; color: var(--ivory); line-height: 1.3; }
.role { font-size: 12px; color: var(--muted); font-weight: 300; }
.time { margin-left: auto; color: var(--faint); }
.badge { display: inline-block; border: 1px solid var(--line-2); color: var(--text); padding: 5px 10px; margin-bottom: 10px; }
.badge.ok { border-color: var(--brass); color: var(--brass); }

[data-testid="stVerticalBlockBorderWrapper"] { background: var(--surface); border: 1px solid var(--line) !important;
  border-radius: 2px; }
.stMarkdown p, .stMarkdown li { color: var(--text); font-size: 14.5px; line-height: 1.75; font-weight: 300; }
.stMarkdown strong { color: var(--ivory); font-weight: 500; }
.stMarkdown table { border-collapse: collapse; width: 100%; }
.stMarkdown th { color: var(--muted); font-weight: 400; font-size: 10.5px; letter-spacing: .18em; text-transform: uppercase;
                 text-align: left; border-bottom: 1px solid var(--line-2) !important; }
.stMarkdown td { border-bottom: 1px solid var(--line) !important; font-size: 13.5px; }
.stMarkdown th, .stMarkdown td { border-left: none !important; border-right: none !important; border-top: none !important;
                                 padding: 12px 14px !important; background: transparent !important; }
.stMarkdown code { background: #1A1814; color: var(--ivory); border-radius: 2px; padding: 1px 6px; }

/* indicadores */
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.kpi { padding: 22px 22px; border-right: 1px solid var(--line); }
.kpi:last-child { border-right: none; }
.kpi .label { color: var(--muted); }
.kpi .value { font-size: 40px; font-weight: 400; color: var(--ivory); margin-top: 6px; line-height: 1.1; }

/* controles */
.stTextArea textarea { background: transparent !important; border: none !important; border-bottom: 1px solid var(--line-2) !important;
  border-radius: 0 !important; color: var(--ivory) !important; font-size: 17px !important; font-weight: 300 !important; padding-left: 0 !important; }
.stTextArea [data-baseweb="textarea"], .stTextArea [data-baseweb="base-input"] { background: transparent !important; border: none !important; }
.stTextArea textarea:focus { border-bottom-color: var(--brass) !important; box-shadow: none !important; }
.stTextArea textarea::placeholder { color: var(--faint) !important; font-style: italic; }
.stTextArea label p, .stFileUploader label p, .stSelectbox label p { font-size: 10.5px !important; letter-spacing: .22em;
  text-transform: uppercase; color: var(--muted) !important; font-weight: 400 !important; }
[data-testid="stFileUploaderDropzone"] { background: transparent; border: 1px solid var(--line-2); border-radius: 2px; }
[data-testid="stFileUploaderDropzoneInstructions"] { display: none; }
[data-testid="stFileUploaderDropzone"] button { background: transparent; border: none; color: var(--text); }
.stButton button[kind="primary"] { background: var(--ivory); color: #0D0C0A; border: none; border-radius: 0;
  font-size: 11px; letter-spacing: .24em; text-transform: uppercase; font-weight: 500; padding: 14px 34px; }
.stButton button[kind="primary"] p { font-size: 11px; letter-spacing: .24em; font-weight: 500; }
.stButton button[kind="primary"]:hover { background: #FFFFFF; color: #0D0C0A; }
.stButton button[kind="primary"]:disabled { background: transparent; color: var(--faint); border: 1px solid var(--line-2); }
.stDownloadButton button { background: transparent; border: 1px solid var(--line-2); color: var(--text); border-radius: 0;
  letter-spacing: .2em; text-transform: uppercase; font-size: 11px; }
.stTabs [data-baseweb="tab-list"] { gap: 28px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { color: var(--faint); padding: 10px 0; }
.stTabs [data-baseweb="tab"] p { font-size: 10.5px; letter-spacing: .22em; text-transform: uppercase; }
.stTabs [aria-selected="true"], .stTabs [aria-selected="true"] p { color: var(--ivory); }
.stTabs [data-baseweb="tab-highlight"] { background: var(--brass); height: 1px; }
.stTabs [data-baseweb="tab-border"] { display: none; }
[data-testid="stExpander"] details { background: transparent; border: 1px solid var(--line); border-radius: 2px; }
[data-testid="stExpander"] summary p { color: var(--muted); font-size: 12px; }
.empty { text-align: center; padding: 54px 0; color: var(--faint); font-family: 'Cormorant Garamond', serif !important;
         font-style: italic; font-size: 19px; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.stToggle label p { font-size: 13px !important; color: var(--text) !important; }
.hero.movil h1 { font-size: 46px; }
@media (max-width: 700px) {
  .block-container { padding-top: 1.6rem; }
  .hero h1 { font-size: 42px; }
  .pipe, .kpis { grid-template-columns: 1fr 1fr; }
}
</style>
"""

UML_SISTEMA = """classDiagram
    class ModeloIA {
        <<abstract>>
        +generar(instrucciones, mensaje, imagen)*
    }
    ModeloIA <|-- GeminiIA
    ModeloIA <|-- ClaudeIA
    ModeloIA <|-- ModeloDemo
    class Herramienta {
        <<abstract>>
        +usar()*
    }
    Herramienta <|-- ValidadorCodigo
    Herramienta <|-- GuardarArchivo
    Herramienta <|-- AbrirNavegador
    class Agente {
        <<abstract>>
        +nombre
        +modelo: ModeloIA
        +herramientas: list
        +trabajar(proyecto)*
        +pensar(mensaje)
    }
    Agente <|-- CEO
    Agente <|-- ProductManager
    Agente <|-- Arquitecto
    Agente <|-- Programador
    Agente <|-- Tester
    Agente o-- ModeloIA : piensa con
    Agente o-- Herramienta : usa
    class Empresa {
        +empleados
        +ejecutar(proyecto)
    }
    Empresa *-- Agente : 5 empleados
    Empresa ..> Proyecto : trabaja en
    class Proyecto {
        +idea
        +requisitos
        +diseno_uml
        +codigo
        +errores
    }
"""


# ---------------------------------------------------------------- componentes
def mermaid(codigo: str, alto: int = 460):
    components.html(f"""
    <style>body{{margin:0;background:#13120F}} .mermaid{{display:flex;justify-content:center;padding:14px}}</style>
    <div class="mermaid">{html.escape(codigo)}</div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
    <script>
      mermaid.initialize({{startOnLoad: false, theme: 'base', themeVariables: {{
        background: '#13120F', primaryColor: '#13120F', primaryTextColor: '#ECE6D9', primaryBorderColor: '#4A443A',
        lineColor: '#6B655A', secondaryColor: '#13120F', tertiaryColor: '#13120F', fontSize: '13px',
        fontFamily: 'Inter, Segoe UI, sans-serif', textColor: '#8A8377' }} }});
      // espera a que el iframe sea visible (las pestañas ocultas miden 0 y mermaid falla)
      const dibujar = () => document.body.clientWidth > 0 ? mermaid.run() : setTimeout(dibujar, 300);
      dibujar();
    </script>""", height=alto, scrolling=False)


def avatar(nombre: str, tam: int = 38) -> str:
    return f'<div class="av" style="width:{tam}px;height:{tam}px">{html.escape(nombre[:1].upper())}</div>'


def tarjeta(m: Mensaje, segundos: float):
    with st.container(border=True):
        st.markdown(f'<div class="msg-head">{avatar(m.autor)}<div><div class="who">{html.escape(m.autor)}</div>'
                    f'<div class="role">{html.escape(m.rol)}</div></div>'
                    f'<div class="time">{segundos:04.1f} s</div></div>', unsafe_allow_html=True)
        if m.autor == "Cliente" and st.session_state.get("boceto_img"):
            st.image(st.session_state.boceto_img, width=320)
        if m.tipo == "uml":
            mermaid(m.texto, 520)
        elif m.tipo == "codigo":
            with st.expander(f"Código fuente  ·  {m.texto.count(chr(10)) + 1} líneas"):
                st.code(m.texto, language="html")
        elif m.tipo == "prueba":
            aprobado = m.texto.startswith("Validación aprobada")
            st.markdown(f'<span class="badge {"ok" if aprobado else ""}">'
                        f'{"Aprobado" if aprobado else "Devuelto a desarrollo"}</span>', unsafe_allow_html=True)
            st.markdown(m.texto)
        elif m.tipo == "final":
            st.markdown('<span class="badge ok">Entregado</span>', unsafe_allow_html=True)
            st.markdown(m.texto)
        else:
            st.markdown(m.texto)


def pipeline(empleados, estados: dict) -> str:
    pasos = "".join(
        f'<div class="step {estados.get(e.nombre, "").lower().replace(" ", "")}"><div class="num">{ROMANOS[i]}</div>'
        f'<div class="name">{e.nombre}</div><div class="rol">{e.rol}</div>'
        f'<div class="st">{estados.get(e.nombre, "En espera")}</div></div>'
        for i, e in enumerate(empleados))
    return f'<div class="pipe">{pasos}</div>'


def kpis(proyecto: Proyecto, duracion: float) -> str:
    datos = [("Dictamen", "Aprobado" if proyecto.aprobado else "Observado"),
             ("Iteraciones", proyecto.intentos),
             ("Líneas de código", proyecto.codigo.count("\n") + 1),
             ("Tiempo", f"{duracion:.1f} s")]
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="label">{k}</div><div class="value">{v}</div></div>' for k, v in datos) + "</div>"


@st.cache_resource
def buzon_compartido() -> Buzon:
    """Un solo buzón para todo el servidor: lo comparten el celular y la pantalla."""
    return Buzon()


def url_celular() -> str:
    """Link que abre el celular (va dentro del código QR)."""
    base = os.getenv("PUBLIC_URL") or str(getattr(st.context, "url", "") or "http://localhost:8501")
    if "localhost" in base or "127.0.0.1" in base:  # en la red local se usa la IP de esta computadora
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            base = base.replace("localhost", ip).replace("127.0.0.1", ip)
        except OSError:
            pass
    return base.split("?")[0].rstrip("/") + "/?modo=celular"


def pagina_celular(buzon: Buzon):
    """Página sencilla para el voluntario: toma la foto del dibujo y la envía a la pantalla."""
    st.markdown("""
    <div class="hero movil">
      <div class="eyebrow">DevSquad &nbsp;·&nbsp; Casa de software</div>
      <div class="rule"></div>
      <h1>Envía el<br><em>boceto</em>.</h1>
      <p>Toma una foto clara de la hoja y envíala. El equipo empezará a trabajar en la pantalla.</p>
    </div>""", unsafe_allow_html=True)
    foto = st.file_uploader("Foto del boceto", type=["png", "jpg", "jpeg", "webp", "heic"])
    if foto:
        st.image(foto, use_container_width=True)
    nota = st.text_input("Comentario (opcional)", placeholder="Ej. que tenga niveles")
    if st.button("Enviar a DevSquad", type="primary", disabled=not foto, use_container_width=True):
        buzon.depositar(foto.getvalue(), foto.type or "image/jpeg", nota)
        st.success("Recibido. Mira la pantalla.")


def cuenta_regresiva(segundos: int = 10):
    components.html(f"""
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500&family=Inter:wght@400&display=swap" rel="stylesheet">
    <style>
      body {{ margin:0; background:transparent; text-align:center; font-family:Inter,sans-serif; }}
      #n {{ font-family:'Cormorant Garamond',Georgia,serif; font-size:132px; line-height:1; color:#ECE6D9;
            font-variant-numeric: lining-nums; font-feature-settings: "lnum" 1; }}
      #n.fin {{ color:#A89270; font-size:64px; padding:34px 0; }}
      button {{ margin-top:14px; background:transparent; color:#CFC8BA; border:1px solid #34302A; padding:11px 22px;
               font-size:10.5px; letter-spacing:.22em; text-transform:uppercase; cursor:pointer; font-family:Inter,sans-serif; }}
      button:hover {{ border-color:#A89270; color:#ECE6D9; }}
    </style>
    <div id="n">{segundos}</div>
    <button id="b">Iniciar cuenta regresiva</button>
    <script>
      const n = document.getElementById('n'), b = document.getElementById('b'); let t;
      b.onclick = () => {{
        clearInterval(t); let s = {segundos}; n.className = ''; n.textContent = s; b.textContent = 'Reiniciar';
        t = setInterval(() => {{ s--; if (s <= 0) {{ clearInterval(t); n.className = 'fin'; n.textContent = 'Tiempo'; }}
                                 else n.textContent = s; }}, 1000);
      }};
    </script>""", height=230)


def panel_presentacion(buzon: Buzon):
    url = url_celular()
    qr = segno.make(url, error="m").svg_inline(scale=7, dark="#ECE6D9", light=None, border=0)
    c1, c2, c3 = st.columns([1, 1, 1], gap="large")
    with c1:
        st.markdown('<div class="label" style="color:#8A8377">I &nbsp;·&nbsp; El voluntario dibuja</div>',
                    unsafe_allow_html=True)
        cuenta_regresiva(10)
    with c2:
        st.markdown(f'<div class="label" style="color:#8A8377">II &nbsp;·&nbsp; Escanea y envía la foto</div>'
                    f'<div style="margin-top:18px;text-align:center">{qr}</div>'
                    f'<div style="text-align:center;margin-top:10px;font-size:11px;color:#5B564D">{html.escape(url)}</div>',
                    unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="label" style="color:#8A8377">III &nbsp;·&nbsp; El equipo trabaja</div>',
                    unsafe_allow_html=True)
        vigilar_buzon(buzon)


@st.fragment(run_every=2)
def vigilar_buzon(buzon: Buzon):
    """Cada 2 segundos revisa si el celular ya mandó la foto; si sí, arranca el proyecto."""
    if buzon.tiene_algo:
        st.session_state.entrada = buzon.retirar()
        st.rerun(scope="app")
    st.markdown('<div class="empty" style="margin-top:18px;padding:70px 0">Esperando el boceto…</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------- página
st.markdown(CSS, unsafe_allow_html=True)
buzon = buzon_compartido()

if st.query_params.get("modo") == "celular":
    pagina_celular(buzon)
    st.stop()

with st.sidebar:
    st.markdown('<div class="eyebrow">Configuración</div>', unsafe_allow_html=True)
    hay_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
    opcion = st.selectbox("Motor de IA", ["Gemini (capa gratuita)", "Claude (Anthropic)", "Modo demo (sin conexión)"],
                          index=0 if hay_key else 2)
    proveedor = {"Gemini": "gemini", "Claude": "claude", "Modo d": "demo"}[opcion[:6]]
    modelo = crear_modelo(proveedor)
    if proveedor != "demo" and type(modelo).__name__ == "ModeloDemo":
        st.caption("No se encontró la API key en el archivo .env. Se usa el modo demo.")

empresa_base = Empresa("DevSquad", modelo)
conectado = type(modelo).__name__ != "ModeloDemo"

st.markdown(f"""
<div class="hero">
  <div class="eyebrow">DevSquad &nbsp;·&nbsp; Casa de software &nbsp;·&nbsp; MMXXVI</div>
  <div class="rule"></div>
  <h1>Tu idea, construida<br>por <em>un equipo de agentes</em>.</h1>
  <p>Cinco agentes de inteligencia artificial analizan, especifican, diseñan, programan
  y validan un producto funcional, con el rigor de una firma de ingeniería.</p>
  <div class="eyebrow motor">Motor &nbsp;·&nbsp; {html.escape(str(modelo))}</div>
</div>""", unsafe_allow_html=True)

tab_proyecto, tab_sistema = st.tabs(["Proyecto", "Arquitectura del sistema"])

with tab_sistema:
    st.markdown('<div class="section">Diagrama de clases</div>', unsafe_allow_html=True)
    mermaid(UML_SISTEMA, 640)
    st.markdown('<div class="section">Principios de POO aplicados</div>', unsafe_allow_html=True)
    st.markdown("""
| Principio | Implementación |
|---|---|
| Clases abstractas | `Agente`, `ModeloIA` y `Herramienta` definen el contrato; las subclases lo implementan. |
| Herencia | `CEO`, `ProductManager`, `Arquitecto`, `Programador` y `Tester` heredan de `Agente`. |
| Polimorfismo | `Empresa` invoca `agente.trabajar(proyecto)` sin conocer el tipo concreto de cada agente. |
| Composición | `Empresa` contiene a sus agentes; cada `Agente` contiene un `ModeloIA` y sus `Herramienta`s. |
| Encapsulamiento | Las instrucciones de cada rol viven dentro de su clase; hacia afuera solo se expone `trabajar()`. |
""")

with tab_proyecto:
    pipe_ph = st.empty()
    st.markdown('<div class="section">Encargo</div>', unsafe_allow_html=True)
    en_vivo = st.toggle("Modo presentación: recibir el boceto desde un celular")
    if en_vivo:
        panel_presentacion(buzon)
        iniciar, idea, boceto = False, "", None
    else:
        c1, c2 = st.columns([3, 1.1], gap="large")
        idea = c1.text_area("Descripción de la idea", height=96,
                            placeholder="Un juego donde el jugador atrapa estrellas que caen y evita bombas.")
        boceto = c2.file_uploader("Boceto (opcional)", type=["png", "jpg", "jpeg", "webp"])
        if boceto:
            c2.image(boceto, use_container_width=True)
        iniciar = st.button("Iniciar proyecto", type="primary", disabled=not (idea or boceto))

    st.markdown('<div class="section">Bitácora</div>', unsafe_allow_html=True)
    feed = st.container()

    entrada = st.session_state.pop("entrada", None)  # foto que llegó desde el celular
    if iniciar or entrada:
        if entrada:
            proyecto = Proyecto(entrada.nota, entrada.imagen, entrada.tipo)
        else:
            proyecto = Proyecto(idea.strip(), boceto.getvalue() if boceto else None,
                                boceto.type if boceto else "image/png")
        st.session_state.update(historial=[], proyecto=None, estados={}, boceto_img=proyecto.imagen)
        empresa = Empresa("DevSquad", modelo)
        estados, inicio = {}, time.time()
        try:
            with feed:
                espera = st.empty()
                for m in empresa.ejecutar(proyecto):
                    for nombre, valor in estados.items():
                        if valor == "En curso" and nombre != m.autor:
                            estados[nombre] = "Concluido"
                    if m.autor != "Cliente":
                        estados[m.autor] = "En curso"
                    pipe_ph.markdown(pipeline(empresa.empleados, estados), unsafe_allow_html=True)
                    if m.tipo == "estado":  # solo avisa quién empezó a trabajar
                        espera.markdown(f'<div class="empty">{m.autor} está trabajando…</div>',
                                        unsafe_allow_html=True)
                        if not conectado:
                            time.sleep(1.0)  # ritmo legible en la demostración
                        continue
                    espera.empty()
                    segundos = time.time() - inicio
                    st.session_state.historial.append((m, segundos))
                    tarjeta(m, segundos)
                    espera = st.empty()  # siempre debajo de la última tarjeta
                    if not conectado:
                        time.sleep(0.4)
            st.session_state.update(proyecto=proyecto, duracion=time.time() - inicio,
                                    estados={e.nombre: "Concluido" for e in empresa.empleados})
        except Exception as error:  # cuota agotada, sin internet, key inválida, etc.
            st.error(f"Error del proveedor de IA: {error}. Intenta de nuevo en un minuto o usa el modo demo.")
        st.rerun()

    pipe_ph.markdown(pipeline(empresa_base.empleados, st.session_state.get("estados", {})),
                     unsafe_allow_html=True)
    with feed:
        historial = st.session_state.get("historial", [])
        if not historial:
            st.markdown('<div class="empty">La bitácora del equipo aparecerá aquí.</div>', unsafe_allow_html=True)
        for m, s in historial:
            tarjeta(m, s)

    proyecto = st.session_state.get("proyecto")
    if proyecto and proyecto.codigo:
        st.markdown('<div class="section">Entrega</div>', unsafe_allow_html=True)
        st.markdown(kpis(proyecto, st.session_state.get("duracion", 0)), unsafe_allow_html=True)
        st.write("")
        t1, t2, t3, t4, t5 = st.tabs(["Vista previa", "Historias de usuario", "Arquitectura",
                                       "Código fuente", "Control de calidad"])
        with t1:
            components.html(proyecto.codigo, height=660, scrolling=True)
            st.download_button("Descargar HTML", proyecto.codigo, file_name="devsquad-producto.html",
                               mime="text/html")
        with t2:
            st.markdown(proyecto.requisitos)
        with t3:
            mermaid(proyecto.diseno_uml, 560)
        with t4:
            st.code(proyecto.codigo, language="html")
        with t5:
            st.markdown(proyecto.reporte_qa or "Sin reporte.")
