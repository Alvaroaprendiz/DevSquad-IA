"""Los empleados de la empresa.

- Agente es una clase ABSTRACTA: todos los empleados tienen nombre, rol, un modelo
  de IA (composición: el agente TIENE UN cerebro) y una lista de herramientas.
- Cada rol HEREDA de Agente y sobrescribe trabajar() a su manera (polimorfismo):
  la Empresa solo llama agente.trabajar(proyecto) sin saber qué tipo de agente es.
"""
import re
from abc import ABC, abstractmethod
from typing import Iterator

from .herramientas import Herramienta, ValidadorCodigo
from .mensajes import Mensaje, Proyecto
from .modelos import ModeloIA

ESTILO = "Escribe en español, con tono profesional y sin emojis."
REGLA_BOCETO = ("El cliente entregó un boceto dibujado a mano (imagen adjunta). Léelo así: las notas escritas "
                "(por ejemplo 'crea un juego de...') son la INSTRUCCIÓN de lo que quiere; los dibujos son la "
                "GUÍA VISUAL de personajes, pantallas, títulos y acomodo. Respeta ambos y no lo cambies por otra "
                "idea. Pero el boceto es un plano, no el producto: el resultado debe ser FUNCIONAL e interactivo "
                "(si es un juego: controles, objetivo, enemigos u obstáculos, puntos, ganar o perder), nunca "
                "una copia estática del dibujo.")


class Agente(ABC):
    rol = "Agente"

    def __init__(self, nombre: str, modelo: ModeloIA, herramientas: list[Herramienta] | None = None):
        self.nombre = nombre
        self.modelo = modelo                    # composición
        self.herramientas = herramientas or []  # composición

    @property
    @abstractmethod
    def instrucciones(self) -> str:
        """La personalidad y las reglas del rol (system prompt)."""

    @abstractmethod
    def trabajar(self, proyecto: Proyecto) -> Iterator[Mensaje]:
        """Hace su parte del proyecto y va reportando su avance."""

    # --- métodos que heredan todos ---
    @property
    def iniciales(self) -> str:
        return self.nombre[:2].upper()

    def pensar(self, mensaje: str, proyecto: Proyecto | None = None) -> str:
        """Le pregunta al modelo. Si el proyecto trae boceto, el agente también lo ve."""
        imagen = proyecto.imagen if proyecto else None
        tipo = proyecto.imagen_tipo if proyecto else "image/png"
        sistema = f"[ROL:{self.rol}]\n{self.instrucciones}\n{ESTILO}"
        if imagen:
            sistema += "\n" + REGLA_BOCETO
        if proyecto and proyecto.idea and proyecto.idea not in mensaje:
            mensaje = f"Pedido original del cliente: {proyecto.idea}\n\n{mensaje}"
        return self.modelo.generar(sistema, mensaje, imagen, tipo)

    def decir(self, texto: str, tipo: str = "texto") -> Mensaje:
        return Mensaje(self.nombre, self.rol, texto, tipo)

    def herramienta(self, clase):
        return next(h for h in self.herramientas if isinstance(h, clase))

    @staticmethod
    def bloque(texto: str, lenguaje: str) -> str:
        """Saca el contenido de un bloque ```lenguaje ... ``` de la respuesta."""
        m = re.search(rf"```{lenguaje}\s*\n([\s\S]*?)```", texto)
        if m:
            return m.group(1).strip()
        m = re.search(r"```\w*\s*\n([\s\S]*?)```", texto)
        return (m.group(1) if m else texto).strip()

    def __str__(self):
        return f"{self.nombre} ({self.rol})"


class CEO(Agente):
    rol = "CEO"

    @property
    def instrucciones(self):
        return ("Eres la directora de una empresa de software. Un cliente te trae una idea (en texto o "
                "en la foto de un boceto). Si hay boceto, primero describe con precisión lo que está "
                "dibujado: cada elemento, el texto escrito, flechas o anotaciones y dónde está cada cosa. "
                "Después resume qué quiere el cliente y cuál es el objetivo del producto. Máximo 5 frases. "
                "Si la idea es muy grande, define un alcance que quepa en un solo archivo HTML, pero sin "
                "cambiar la esencia de lo que pidió.")

    def trabajar(self, proyecto):
        pedido = f"Idea del cliente: {proyecto.idea or '(ver la imagen del boceto)'}"
        proyecto.resumen = self.pensar(pedido, proyecto)
        yield self.decir(proyecto.resumen)


class ProductManager(Agente):
    rol = "Product Manager"

    @property
    def instrucciones(self):
        return ("Eres Product Manager. A partir del resumen de la CEO escribe entre 4 y 6 historias de "
                "usuario con el formato 'Como <usuario> quiero <acción> para <beneficio>'. Debajo de cada "
                "una agrega sus criterios de aceptación: condiciones concretas y verificables que el "
                "Tester usará para aprobar el producto. La mayoría de las historias deben describir "
                "INTERACCIÓN y funcionamiento (qué hace el usuario y qué responde el sistema), no solo "
                "cómo se ve. Todo debe caber en un solo archivo HTML sin "
                "recursos externos. Responde solo con la lista en Markdown simple (texto, negritas y viñetas). "
                "No escribas código, HTML ni bloques ```; tú solo escribes requisitos, el código lo hace otro.")

    def trabajar(self, proyecto):
        texto = self.pensar(f"Resumen de la CEO:\n{proyecto.resumen}", proyecto)
        if texto.lstrip().startswith("```"):  # por si el modelo lo envuelve en un bloque de código
            texto = self.bloque(texto, r"\w*")
        proyecto.requisitos = texto
        yield self.decir(proyecto.requisitos, "requisitos")


class Arquitecto(Agente):
    rol = "Arquitecta de Software"

    @property
    def instrucciones(self):
        return ("Eres arquitecta de software especializada en Programación Orientada a Objetos. Con los "
                "requisitos diseña las clases de JavaScript (máximo 6) usando herencia o composición. "
                "Responde con: 1) un bloque ```mermaid con un classDiagram válido (atributos y métodos "
                "principales, relaciones <|-- para herencia y *-- para composición) y 2) una justificación "
                "de 2 frases sobre las decisiones de diseño.")

    def trabajar(self, proyecto):
        respuesta = self.pensar(f"Requisitos:\n{proyecto.requisitos}", proyecto)
        proyecto.diseno_uml = self.bloque(respuesta, "mermaid")
        explicacion = re.sub(r"```[\s\S]*?```", "", respuesta).strip()
        yield self.decir(proyecto.diseno_uml, "uml")
        if explicacion:
            yield self.decir(explicacion)


class Programador(Agente):
    rol = "Ingeniero de Software"

    @property
    def instrucciones(self):
        return ("Eres ingeniero de software senior. Escribe el producto COMPLETO en un solo archivo HTML "
                "con el CSS y el JavaScript adentro, sin librerías ni imágenes externas (dibuja con canvas "
                "o CSS, no uses emojis). Implementa las clases del diagrama con 'class' de JavaScript. "
                "Debe ser totalmente funcional e interactivo desde que se abre (si es un juego: jugable, con "
                "controles explicados en pantalla, puntuación y reinicio). Diseño limpio y moderno, textos en "
                "español. Responde SOLO con un bloque ```html.")

    def trabajar(self, proyecto):
        if proyecto.errores:
            pedido = ("Tu código anterior tiene estos errores:\n- " + "\n- ".join(proyecto.errores) +
                      f"\n\nCorrígelos y regresa el archivo completo.\n\nCÓDIGO:\n```html\n{proyecto.codigo}\n```")
            aviso = "Corrección aplicada. Envío la versión {n} a revisión"
        else:
            pedido = (f"Lo que pidió el cliente, según la CEO:\n{proyecto.resumen}\n\n"
                      f"Requisitos:\n{proyecto.requisitos}\n\nDiagrama de clases:\n"
                      f"```mermaid\n{proyecto.diseno_uml}\n```")
            aviso = "Primera versión lista. Envío la versión {n} a revisión"
        proyecto.codigo = self.bloque(self.pensar(pedido, proyecto), "html")
        proyecto.intentos += 1
        lineas = proyecto.codigo.count("\n") + 1
        yield self.decir(aviso.format(n=proyecto.intentos) + f" ({lineas} líneas de código).")
        yield self.decir(proyecto.codigo, "codigo")


class Tester(Agente):
    rol = "QA Engineer"

    @property
    def instrucciones(self):
        return ("Eres QA Engineer. El código ya pasó la validación automática. Con base en los criterios "
                "de aceptación del PM, escribe un plan de pruebas manual breve: de 3 a 5 casos, cada uno "
                "con su resultado esperado.")

    def trabajar(self, proyecto):
        validador = self.herramienta(ValidadorCodigo)
        proyecto.errores = validador.usar(proyecto.codigo)
        if proyecto.errores:
            proyecto.aprobado = False
            lista = "\n".join(f"- {e}" for e in proyecto.errores)
            yield self.decir(f"Validación rechazada ({validador.nombre}). Se devuelve a desarrollo:\n{lista}",
                             "prueba")
        else:
            proyecto.aprobado = True
            yield self.decir(f"Validación aprobada ({validador.nombre}): HTML completo y JavaScript sin "
                             "errores de sintaxis.", "prueba")
            proyecto.reporte_qa = self.pensar(f"Requisitos y criterios:\n{proyecto.requisitos}")
            yield self.decir(proyecto.reporte_qa)
