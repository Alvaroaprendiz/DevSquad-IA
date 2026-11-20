"""Mensajes que se mandan los agentes y el proyecto que van armando entre todos."""
from dataclasses import dataclass, field


@dataclass
class Mensaje:
    """Un mensaje en el registro de actividad de la empresa."""
    autor: str          # nombre del agente (o "Cliente")
    rol: str
    texto: str
    tipo: str = "texto"  # texto | requisitos | uml | codigo | prueba | final


@dataclass
class Proyecto:
    """Lo que la empresa va construyendo paso a paso.

    Cada agente lee lo que dejaron los anteriores y agrega su parte.
    """
    idea: str
    imagen: bytes | None = None      # foto del boceto (opcional)
    imagen_tipo: str = "image/png"
    resumen: str = ""                # lo que entendió la CEO
    requisitos: str = ""             # historias de usuario del PM
    diseno_uml: str = ""             # diagrama de clases en Mermaid (Arquitecta)
    codigo: str = ""                 # HTML del juego/app (Programador)
    errores: list[str] = field(default_factory=list)  # lo que encontró el Tester
    reporte_qa: str = ""
    intentos: int = 0
    aprobado: bool = False
    archivo: str = ""                # ruta donde se guardó el resultado
