"""Buzón compartido: un celular deja ahí la foto del boceto y la pantalla principal la recoge.

Es un solo objeto para todo el servidor (todas las sesiones lo comparten), y usa un Lock
para que dos personas no lo modifiquen al mismo tiempo.
"""
import threading
import time
from dataclasses import dataclass, field


@dataclass
class Entrega:
    imagen: bytes
    tipo: str
    nota: str = ""
    hora: float = field(default_factory=time.time)


class Buzon:
    def __init__(self):
        self._lock = threading.Lock()
        self._entrega: Entrega | None = None

    def depositar(self, imagen: bytes, tipo: str, nota: str = "") -> None:
        with self._lock:
            self._entrega = Entrega(imagen, tipo, nota.strip())

    def retirar(self) -> Entrega | None:
        """Regresa la entrega pendiente (si hay) y deja el buzón vacío."""
        with self._lock:
            entrega, self._entrega = self._entrega, None
            return entrega

    @property
    def tiene_algo(self) -> bool:
        return self._entrega is not None
