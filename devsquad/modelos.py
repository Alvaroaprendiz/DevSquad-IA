"""Los "cerebros" de los agentes.

ModeloIA es una clase abstracta: define QUÉ debe saber hacer un modelo (generar texto),
pero no CÓMO. Cada subclase lo implementa con un proveedor distinto (polimorfismo):
a un agente no le importa si piensa con Gemini, con Claude o en modo demo.

Las llamadas se hacen por HTTP con la librería estándar (urllib), sin SDKs, para que
el proyecto funcione aunque Windows bloquee librerías compiladas como pydantic_core.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod

from . import demo


class ErrorIA(Exception):
    """Error del proveedor de IA con un mensaje entendible."""

    def __init__(self, mensaje: str, codigo: int = 0):
        super().__init__(mensaje)
        self.codigo = codigo


class ModeloIA(ABC):
    """Clase abstracta para cualquier modelo de lenguaje."""

    reintentos = 2       # intentos por modelo antes de rendirse (o pasar al modelo de respaldo)
    tiempo_limite = 90   # segundos máximos esperando una respuesta

    def __init__(self, nombre: str):
        self.nombre = nombre

    @abstractmethod
    def generar(self, instrucciones: str, mensaje: str,
                imagen: bytes | None = None, imagen_tipo: str = "image/png") -> str:
        """Recibe las instrucciones del rol y el mensaje; regresa la respuesta en texto."""

    def _post(self, url: str, cuerpo: dict, encabezados: dict) -> dict:
        """POST JSON con un reintento corto cuando el proveedor está saturado o hay límite de uso."""
        datos = json.dumps(cuerpo).encode("utf-8")
        for intento in range(self.reintentos):
            ultimo = intento == self.reintentos - 1
            req = urllib.request.Request(url, data=datos, method="POST",
                                         headers={"content-type": "application/json", **encabezados})
            try:
                with urllib.request.urlopen(req, timeout=self.tiempo_limite) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detalle = e.read().decode("utf-8", "replace")[:400]
                if e.code in (429, 500, 502, 503, 529) and not ultimo:
                    espera = int(e.headers.get("retry-after") or 0) or 5
                    time.sleep(min(espera, 30))
                    continue
                raise ErrorIA(self._explicar(e.code, detalle), e.code) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                # si se agotó el tiempo no se reintenta el mismo modelo: se pasa al de respaldo
                lento = isinstance(e, TimeoutError) or isinstance(getattr(e, "reason", None), TimeoutError)
                if not ultimo and not lento:
                    time.sleep(3)
                    continue
                motivo = getattr(e, "reason", None) or "tiempo de espera agotado"
                raise ErrorIA(f"El proveedor no respondió a tiempo ({motivo}).", 504) from None
        raise ErrorIA("El proveedor no respondió.", 504)

    @staticmethod
    def _explicar(codigo: int, detalle: str) -> str:
        if "has not been used in project" in detalle or "SERVICE_DISABLED" in detalle:
            return ("La API de Gemini no está activada en tu proyecto de Google (si acabas de crear la "
                    "key, espera unos minutos).")
        if codigo in (400, 401, 403) and ("key" in detalle.lower() or codigo != 400):
            return "La API key no es válida o no tiene permiso."
        if codigo == 404:
            return "El modelo configurado no existe. Revisa GEMINI_MODEL o CLAUDE_MODEL en el .env."
        if codigo == 429:
            return "Se alcanzó el límite de uso gratuito. Espera un minuto e intenta de nuevo."
        return f"Error {codigo} del proveedor: {detalle}"

    def __str__(self):
        return self.nombre


class GeminiIA(ModeloIA):
    """Google Gemini con la capa gratuita de AI Studio (API REST)."""

    URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

    def __init__(self, api_key: str, modelos: str = "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash"):
        # se aceptan varios modelos separados por coma: si uno está saturado o retirado, se usa el siguiente
        self._modelos = [m.strip() for m in modelos.split(",") if m.strip()]
        super().__init__(f"Gemini · {self._modelos[0]}")
        self._key = api_key

    def generar(self, instrucciones, mensaje, imagen=None, imagen_tipo="image/png"):
        for i, modelo in enumerate(self._modelos):
            try:
                return self._generar(modelo, instrucciones, mensaje, imagen, imagen_tipo)
            except ErrorIA as e:
                if e.codigo in (404, 429, 500, 503, 504) and i < len(self._modelos) - 1:
                    continue
                raise

    def _generar(self, modelo, instrucciones, mensaje, imagen, imagen_tipo):
        partes = [{"text": mensaje}]
        if imagen:
            partes.append({"inline_data": {"mime_type": imagen_tipo,
                                           "data": base64.b64encode(imagen).decode()}})
        cuerpo = {"system_instruction": {"parts": [{"text": instrucciones}]},
                  "contents": [{"role": "user", "parts": partes}],
                  "generationConfig": {"temperature": 0.7, "maxOutputTokens": 32768}}
        r = self._post(self.URL.format(modelo=modelo), cuerpo, {"x-goog-api-key": self._key})
        try:
            candidato = r["candidates"][0]
            return "".join(p.get("text", "") for p in candidato["content"]["parts"]
                           if not p.get("thought"))
        except (KeyError, IndexError):
            motivo = r.get("promptFeedback", {}).get("blockReason") or "respuesta vacía"
            raise ErrorIA(f"Gemini no devolvió texto ({motivo}).") from None


class ClaudeIA(ModeloIA):
    """Claude de Anthropic (opcional; la API se paga aparte)."""

    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, modelo: str = "claude-opus-5-5"):
        super().__init__(f"Claude · {modelo}")
        self._key = api_key
        self._modelo = modelo

    def generar(self, instrucciones, mensaje, imagen=None, imagen_tipo="image/png"):
        contenido = []
        if imagen:
            contenido.append({"type": "image", "source": {
                "type": "base64", "media_type": imagen_tipo,
                "data": base64.standard_b64encode(imagen).decode()}})
        contenido.append({"type": "text", "text": mensaje})
        cuerpo = {"model": self._modelo, "max_tokens": 16000, "thinking": {"type": "adaptive"},
                  "system": instrucciones, "messages": [{"role": "user", "content": contenido}]}
        r = self._post(self.URL, cuerpo, {"x-api-key": self._key, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in r.get("content", []) if b.get("type") == "text")


class ModeloDemo(ModeloIA):
    """Respuestas ya preparadas, para probar o presentar sin internet ni API key.

    El Programador se equivoca a propósito en su primer intento, para que se vea
    cómo el Tester encuentra el error y se lo regresa.
    """

    def __init__(self):
        super().__init__("Modo demo (sin conexión)")

    def generar(self, instrucciones, mensaje, imagen=None, imagen_tipo="image/png"):
        return demo.responder(instrucciones, mensaje)


def crear_modelo(proveedor: str | None = None) -> ModeloIA:
    """Fábrica: lee el .env y regresa el modelo que se pueda usar."""
    proveedor = (proveedor or os.getenv("PROVEEDOR", "gemini")).lower()
    if proveedor == "claude" and os.getenv("ANTHROPIC_API_KEY"):
        return ClaudeIA(os.environ["ANTHROPIC_API_KEY"], os.getenv("CLAUDE_MODEL") or "claude-opus-5-5")
    if proveedor == "gemini" and os.getenv("GEMINI_API_KEY"):
        return GeminiIA(os.environ["GEMINI_API_KEY"],
                        os.getenv("GEMINI_MODEL") or "gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-3.5-flash")
    return ModeloDemo()
