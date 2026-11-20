"""La Empresa coordina a los agentes (composición: la empresa TIENE empleados)."""
from typing import Iterator

from .agentes import CEO, Arquitecto, Agente, ProductManager, Programador, Tester
from .herramientas import AbrirNavegador, GuardarArchivo, ValidadorCodigo
from .mensajes import Mensaje, Proyecto
from .modelos import ModeloIA


class Empresa:
    def __init__(self, nombre: str, modelo: ModeloIA, max_intentos: int = 3):
        self.nombre = nombre
        self.modelo = modelo
        self.max_intentos = max_intentos
        self.guardar = GuardarArchivo()
        self.abrir = AbrirNavegador()
        # Cada empleado recibe el mismo cerebro y solo las herramientas de su puesto.
        self.ceo = CEO("Valeria", modelo)
        self.pm = ProductManager("Marco", modelo)
        self.arquitecta = Arquitecto("Sofía", modelo)
        self.programador = Programador("Diego", modelo, [self.guardar])
        self.tester = Tester("Lucía", modelo, [ValidadorCodigo()])

    @property
    def empleados(self) -> list[Agente]:
        return [self.ceo, self.pm, self.arquitecta, self.programador, self.tester]

    @staticmethod
    def _turno(agente: Agente, proyecto: Proyecto) -> Iterator[Mensaje]:
        """Avisa que el agente empezó (tipo "estado") y luego deja que haga su trabajo."""
        yield Mensaje(agente.nombre, agente.rol, "", "estado")
        yield from agente.trabajar(proyecto)

    def ejecutar(self, proyecto: Proyecto, abrir_al_final: bool = False) -> Iterator[Mensaje]:
        """Pasa el proyecto por toda la empresa y va emitiendo los mensajes de actividad."""
        yield Mensaje("Cliente", "Cliente", proyecto.idea or "Adjunto el boceto de la idea.")
        # 1. Cada uno hace su parte en orden (polimorfismo: mismo método, distinto trabajo)
        for agente in (self.ceo, self.pm, self.arquitecta):
            yield from self._turno(agente, proyecto)

        # 2. Programador y Tester iteran hasta aprobar o agotar los intentos
        while proyecto.intentos < self.max_intentos:
            yield from self._turno(self.programador, proyecto)
            yield from self._turno(self.tester, proyecto)
            if proyecto.aprobado:
                break

        # 3. Entregar
        nombre = proyecto.idea[:40] if proyecto.idea else "boceto"
        proyecto.archivo = self.guardar.usar(proyecto.codigo, nombre)
        estado = "aprobado por QA" if proyecto.aprobado else "entregado con observaciones de QA"
        yield Mensaje(self.ceo.nombre, self.ceo.rol,
                      f"Proyecto {estado} tras {proyecto.intentos} iteración(es). "
                      f"Archivo: {proyecto.archivo}", "final")
        if abrir_al_final:
            self.abrir.usar(proyecto.archivo)
