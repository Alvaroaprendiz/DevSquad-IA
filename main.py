"""Versión de consola: python main.py "un juego de ..."  (la versión bonita es app.py)."""
import sys

from dotenv import load_dotenv

from devsquad import Empresa, Proyecto, crear_modelo


def main():
    load_dotenv()
    idea = " ".join(sys.argv[1:]) or input("¿Qué quieres que construya la empresa? ")
    modelo = crear_modelo()
    empresa = Empresa("DevSquad IA", modelo)
    print(f"\n{empresa.nombre} | motor: {modelo}\n")
    for m in empresa.ejecutar(Proyecto(idea), abrir_al_final=True):
        if m.tipo == "estado":
            print(f"... {m.autor} está trabajando")
            continue
        texto = m.texto if m.tipo != "codigo" else f"[código HTML de {m.texto.count(chr(10)) + 1} líneas]"
        print(f"{m.autor} - {m.rol}\n{texto}\n" + "-" * 60)


if __name__ == "__main__":
    main()
