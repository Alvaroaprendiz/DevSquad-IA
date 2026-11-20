"""Herramientas: lo que los agentes pueden HACER además de pensar.

Todas heredan de la clase abstracta Herramienta y tienen el mismo método usar(),
así un agente puede tener cualquier lista de herramientas (composición).
"""
import os
import re
import shutil
import subprocess
import tempfile
import webbrowser
from abc import ABC, abstractmethod
from datetime import datetime
from html.parser import HTMLParser


class Herramienta(ABC):
    nombre = "herramienta"
    descripcion = ""

    @abstractmethod
    def usar(self, *args, **kwargs):
        """Ejecuta la herramienta."""

    def __str__(self):
        return self.nombre


class _ExtraerScripts(HTMLParser):
    """Junta el código JavaScript que está dentro de las etiquetas <script>."""

    def __init__(self):
        super().__init__()
        self.scripts, self._dentro, self.etiquetas = [], False, set()

    def handle_starttag(self, tag, attrs):
        self.etiquetas.add(tag)
        self._dentro = tag == "script" and not dict(attrs).get("src")

    def handle_endtag(self, tag):
        if tag == "script":
            self._dentro = False

    def handle_data(self, data):
        if self._dentro:
            self.scripts.append(data)


class ValidadorCodigo(Herramienta):
    """Revisa que el HTML esté completo y que el JavaScript no tenga errores de sintaxis."""
    nombre = "Validador de código"
    descripcion = "Revisa el HTML y ejecuta node --check sobre el JavaScript."

    def usar(self, codigo: str) -> list[str]:
        errores = []
        if not codigo.strip():
            return ["El archivo está vacío."]
        if "<html" not in codigo.lower():
            errores.append("Falta la etiqueta <html>.")
        p = _ExtraerScripts()
        p.feed(codigo)
        if "body" not in p.etiquetas:
            errores.append("Falta la etiqueta <body>.")
        js = "\n".join(p.scripts)
        if not js.strip():
            errores.append("No hay JavaScript: el juego/app no haría nada.")
        else:
            errores += self._revisar_js(js)
        return errores

    def _revisar_js(self, js: str) -> list[str]:
        node = shutil.which("node")
        if node:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
                f.write(js)
            try:
                r = subprocess.run([node, "--check", f.name], capture_output=True, text=True, timeout=20)
            finally:
                os.unlink(f.name)
            if r.returncode != 0:
                linea = next((l for l in r.stderr.splitlines() if "Error" in l), r.stderr.strip()[:200])
                return [f"Error de sintaxis en JavaScript: {linea}"]
            return []
        return self._balance(js)

    @staticmethod
    def _balance(js: str) -> list[str]:
        """Plan B si no hay Node: revisar que llaves y paréntesis cierren."""
        sin_cadenas = re.sub(r"(['\"`])(?:\\.|(?!\1).)*\1|//.*|/\*[\s\S]*?\*/", "", js)
        pares, pila = {")": "(", "]": "[", "}": "{"}, []
        for c in sin_cadenas:
            if c in "([{":
                pila.append(c)
            elif c in pares:
                if not pila or pila.pop() != pares[c]:
                    return [f"Error de sintaxis: '{c}' sin abrir."]
        return [f"Error de sintaxis: falta cerrar '{pila[-1]}'."] if pila else []


class GuardarArchivo(Herramienta):
    """Guarda el resultado en la carpeta proyectos/."""
    nombre = "Guardar archivo"
    descripcion = "Guarda el código en proyectos/<nombre>.html"

    def __init__(self, carpeta: str | None = None):
        # por defecto: DevSquad-IA/proyectos, sin importar desde dónde se ejecute
        self.carpeta = carpeta or os.path.join(os.path.dirname(os.path.dirname(__file__)), "proyectos")

    def usar(self, codigo: str, nombre: str) -> str:
        os.makedirs(self.carpeta, exist_ok=True)
        limpio = re.sub(r"[^a-z0-9]+", "-", nombre.lower()).strip("-")[:40] or "proyecto"
        ruta = os.path.abspath(os.path.join(
            self.carpeta, f"{datetime.now():%Y%m%d-%H%M%S}-{limpio}.html"))
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(codigo)
        return ruta


class AbrirNavegador(Herramienta):
    """Abre el archivo terminado en el navegador."""
    nombre = "Abrir en navegador"
    descripcion = "Abre el juego/app para usarlo."

    def usar(self, ruta: str) -> bool:
        return webbrowser.open(f"file:///{ruta.replace(os.sep, '/')}")
