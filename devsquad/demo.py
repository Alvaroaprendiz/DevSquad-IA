"""Respuestas preparadas para el modo demo (sin API key ni internet).

Sirven de respaldo en la presentación por si falla el internet o se agota la cuota gratuita.
"""

RESUMEN = (
    "El cliente quiere un **juego arcade de reflejos** para navegador: el jugador controla una "
    "plataforma para **atrapar estrellas** que caen y **evitar bombas**. Está pensado para sesiones "
    "cortas de uno o dos minutos y debe sentirse retador desde el primer nivel. "
    "Alcance definido: un solo archivo HTML, sin instalación ni recursos externos."
)

REQUISITOS = """**HU-1.** Como jugador quiero mover la plataforma con el teclado o el mouse para atrapar objetos.
- La plataforma responde a las flechas izquierda/derecha y al movimiento del mouse.
- La plataforma nunca sale de los límites del área de juego.

**HU-2.** Como jugador quiero sumar puntos al atrapar estrellas para medir mi desempeño.
- Cada estrella atrapada suma 10 puntos.
- El puntaje se muestra siempre en la parte superior.

**HU-3.** Como jugador quiero perder vidas al tocar bombas para que el juego tenga riesgo.
- El jugador inicia con 3 vidas, visibles en pantalla.
- Cada bomba atrapada resta una vida.

**HU-4.** Como jugador quiero que la dificultad aumente para mantener el reto.
- Cada 100 puntos sube un nivel y aumenta la velocidad de caída.

**HU-5.** Como jugador quiero reiniciar y ver mi récord para intentar superarme.
- Con 0 vidas se muestra la pantalla de fin de juego con el puntaje.
- La partida se reinicia con la barra espaciadora o con un clic.
- El récord se conserva entre sesiones (localStorage)."""

UML = """```mermaid
classDiagram
    class Juego {
        -canvas
        -puntos: int
        -vidas: int
        -nivel: int
        +iniciar()
        +actualizar()
        +dibujar()
        +finDelJuego()
    }
    class Entidad {
        <<abstract>>
        +x: float
        +y: float
        +dibujar(ctx)
        +mover()
    }
    class Jugador {
        +velocidad: float
        +moverA(x)
    }
    class Objeto {
        +vel: float
        +alTocar(juego)
    }
    class Estrella {
        +alTocar(juego)
    }
    class Bomba {
        +alTocar(juego)
    }
    Entidad <|-- Jugador
    Entidad <|-- Objeto
    Objeto <|-- Estrella
    Objeto <|-- Bomba
    Juego *-- Jugador
    Juego *-- Objeto
```
Se usa **herencia** porque Estrella y Bomba son objetos que caen y solo difieren en su efecto al
ser atrapados (polimorfismo en `alTocar`). Se usa **composición** porque el Juego contiene al
jugador y a la colección de objetos activos."""

JUEGO = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Stellar Catch</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; background: #0d0c0a; display: flex; flex-direction: column;
         align-items: center; justify-content: center; font-family: "Inter", "Segoe UI", Arial, sans-serif;
         color: #ece6d9; }
  header { width: 480px; display: flex; justify-content: space-between; align-items: baseline;
           margin-bottom: 12px; }
  h1 { margin: 0; font-size: 22px; font-weight: 500; font-family: Georgia, serif; letter-spacing: .02em; }
  span { font-size: 12px; color: #8a8377; }
  canvas { border: 1px solid #26231e; border-radius: 8px; cursor: none; }
</style>
</head>
<body>
<header><h1>Stellar Catch</h1><span>Flechas o mouse &middot; Espacio para reiniciar</span></header>
<canvas id="juego" width="480" height="560"></canvas>
<script>
class Entidad {
  constructor(x, y) { this.x = x; this.y = y; }
  dibujar(ctx) {}
  mover() {}
}

class Jugador extends Entidad {
  constructor(x, y) { super(x, y); this.ancho = 76; this.velocidad = 7; this.dir = 0; }
  mover(limite) {
    const m = this.ancho / 2;
    this.x = Math.max(m, Math.min(limite - m, this.x + this.dir * this.velocidad));
  }
  moverA(x) { this.x = x; }
  dibujar(ctx) {
    ctx.fillStyle = "#ece6d9";
    ctx.beginPath(); ctx.roundRect(this.x - this.ancho / 2, this.y - 5, this.ancho, 10, 5); ctx.fill();
  }
}

class Objeto extends Entidad {
  constructor(x, vel) { super(x, -20); this.vel = vel; this.radio = 11; }
  mover() { this.y += this.vel; }
  alTocar(juego) {}
  //FIN-OBJETO
}

class Estrella extends Objeto {
  dibujar(ctx) {
    ctx.save(); ctx.translate(this.x, this.y); ctx.rotate(this.y / 60);
    ctx.fillStyle = "#c9b37e"; ctx.shadowColor = "#c9b37e"; ctx.shadowBlur = 6;
    ctx.beginPath();
    for (let i = 0; i < 10; i++) {
      const r = i % 2 === 0 ? this.radio : this.radio * 0.45, a = Math.PI / 5 * i - Math.PI / 2;
      ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r);
    }
    ctx.closePath(); ctx.fill(); ctx.restore();
  }
  alTocar(juego) { juego.puntos += 10; juego.aviso(this.x, this.y, "+10", "#c9b37e"); }
}

class Bomba extends Objeto {
  constructor(x, vel) { super(x, vel * 1.1); }
  dibujar(ctx) {
    ctx.save(); ctx.fillStyle = "#8f3b36"; ctx.shadowColor = "#8f3b36"; ctx.shadowBlur = 6;
    ctx.beginPath(); ctx.arc(this.x, this.y, this.radio - 1, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    ctx.strokeStyle = "#0d0c0a"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(this.x - 4, this.y - 4); ctx.lineTo(this.x + 4, this.y + 4);
    ctx.moveTo(this.x + 4, this.y - 4); ctx.lineTo(this.x - 4, this.y + 4); ctx.stroke();
  }
  alTocar(juego) { juego.vidas -= 1; juego.aviso(this.x, this.y, "-1 vida", "#8f3b36"); }
}

class Juego {
  constructor(canvas) {
    this.canvas = canvas; this.ctx = canvas.getContext("2d");
    this.record = Number(localStorage.getItem("stellar-record") || 0);
    this.avisos = [];
    this.fondo = Array.from({ length: 60 }, () => [Math.random() * canvas.width, Math.random() * canvas.height, Math.random()]);
    this.controles();
    this.iniciar();
    requestAnimationFrame(() => this.ciclo());
  }
  iniciar() {
    this.jugador = new Jugador(this.canvas.width / 2, this.canvas.height - 34);
    this.objetos = []; this.puntos = 0; this.vidas = 3; this.nivel = 1;
    this.cuadros = 0; this.terminado = false;
  }
  controles() {
    addEventListener("keydown", e => {
      if (e.key === "ArrowLeft") this.jugador.dir = -1;
      if (e.key === "ArrowRight") this.jugador.dir = 1;
      if (e.code === "Space" && this.terminado) this.iniciar();
    });
    addEventListener("keyup", e => {
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") this.jugador.dir = 0;
    });
    this.canvas.addEventListener("mousemove", e => {
      const r = this.canvas.getBoundingClientRect();
      this.jugador.moverA((e.clientX - r.left) * this.canvas.width / r.width);
    });
    this.canvas.addEventListener("click", () => { if (this.terminado) this.iniciar(); });
  }
  crearObjeto() {
    const x = 20 + Math.random() * (this.canvas.width - 40);
    const vel = 2 + this.nivel * 0.6 + Math.random();
    this.objetos.push(Math.random() < 0.72 ? new Estrella(x, vel) : new Bomba(x, vel));
  }
  aviso(x, y, texto, color) { this.avisos.push({ x, y, texto, color, vida: 40 }); }
  actualizar() {
    if (this.terminado) return;
    this.cuadros++;
    if (this.cuadros % Math.max(14, 40 - this.nivel * 4) === 0) this.crearObjeto();
    this.jugador.mover(this.canvas.width);
    for (const o of this.objetos) {
      o.mover();
      if (Math.abs(o.x - this.jugador.x) < this.jugador.ancho / 2 + 6 && Math.abs(o.y - this.jugador.y) < 14) {
        o.alTocar(this); o.usado = true;
      }
    }
    this.objetos = this.objetos.filter(o => !o.usado && o.y < this.canvas.height + 30);
    this.nivel = 1 + Math.floor(this.puntos / 100);
    if (this.vidas <= 0) this.finDelJuego();
  }
  finDelJuego() {
    this.terminado = true;
    if (this.puntos > this.record) {
      this.record = this.puntos; localStorage.setItem("stellar-record", this.record);
    }
  }
  dibujar() {
    const { ctx, canvas } = this;
    const g = ctx.createLinearGradient(0, 0, 0, canvas.height);
    g.addColorStop(0, "#0d0c0a"); g.addColorStop(1, "#16140f");
    ctx.fillStyle = g; ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (const [x, y, b] of this.fondo) {
      ctx.fillStyle = "rgba(255,255,255," + (0.15 + b * 0.35) + ")"; ctx.fillRect(x, y, 1.5, 1.5);
    }
    this.objetos.forEach(o => o.dibujar(ctx));
    this.jugador.dibujar(ctx);
    ctx.textAlign = "center"; ctx.font = "600 13px Inter, Segoe UI, Arial";
    for (const a of this.avisos) {
      ctx.globalAlpha = a.vida / 40; ctx.fillStyle = a.color;
      ctx.fillText(a.texto, a.x, a.y); a.y -= 1; a.vida--;
    }
    ctx.globalAlpha = 1; this.avisos = this.avisos.filter(a => a.vida > 0);
    this.marcador();
    if (this.terminado) this.pantallaFinal();
  }
  marcador() {
    const { ctx, canvas } = this;
    ctx.fillStyle = "#8a8377"; ctx.font = "500 10px Inter, Segoe UI, Arial"; ctx.textAlign = "left";
    ctx.fillText("PUNTOS", 18, 24); ctx.fillText("NIVEL", 110, 24);
    ctx.textAlign = "right"; ctx.fillText("RÉCORD", canvas.width - 18, 24);
    ctx.fillStyle = "#ece6d9"; ctx.font = "600 18px Inter, Segoe UI, Arial"; ctx.textAlign = "left";
    ctx.fillText(this.puntos, 18, 46); ctx.fillText(this.nivel, 110, 46);
    ctx.textAlign = "right"; ctx.fillText(this.record, canvas.width - 18, 46);
    for (let i = 0; i < 3; i++) {
      ctx.fillStyle = i < this.vidas ? "#ece6d9" : "#34302a";
      ctx.beginPath(); ctx.arc(canvas.width / 2 - 14 + i * 14, 38, 4, 0, Math.PI * 2); ctx.fill();
    }
  }
  pantallaFinal() {
    const { ctx, canvas } = this;
    ctx.fillStyle = "rgba(13,12,10,0.88)"; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.textAlign = "center"; ctx.fillStyle = "#8a8377"; ctx.font = "500 11px Inter, Segoe UI, Arial";
    ctx.fillText("FIN DE LA PARTIDA", canvas.width / 2, canvas.height / 2 - 48);
    ctx.fillStyle = "#ece6d9"; ctx.font = "400 56px Georgia, serif";
    ctx.fillText(this.puntos, canvas.width / 2, canvas.height / 2);
    ctx.fillStyle = "#8a8377"; ctx.font = "400 13px Inter, Segoe UI, Arial";
    ctx.fillText("Récord: " + this.record, canvas.width / 2, canvas.height / 2 + 30);
    ctx.fillText("Presiona Espacio o haz clic para jugar de nuevo", canvas.width / 2, canvas.height / 2 + 62);
  }
  ciclo() { this.actualizar(); this.dibujar(); requestAnimationFrame(() => this.ciclo()); }
}

new Juego(document.getElementById("juego"));
</script>
</body>
</html>"""

# Primer intento con un error a propósito: falta cerrar la clase Objeto.
JUEGO_CON_ERROR = JUEGO.replace("  //FIN-OBJETO\n}", "  //FIN-OBJETO\n")
JUEGO = JUEGO.replace("  //FIN-OBJETO\n", "")

PRUEBAS = """**Plan de pruebas**

| Caso | Acción | Resultado esperado |
|---|---|---|
| CP-1 | Mover con flechas y con el mouse | La plataforma se desplaza y no sale del área de juego |
| CP-2 | Atrapar una estrella | El puntaje aumenta 10 puntos |
| CP-3 | Atrapar una bomba | Se pierde una vida y el indicador se actualiza |
| CP-4 | Llegar a 100 puntos | El nivel sube a 2 y los objetos caen más rápido |
| CP-5 | Perder las 3 vidas y presionar Espacio | Aparece el fin de partida, se guarda el récord y el juego reinicia |"""


def responder(instrucciones: str, mensaje: str) -> str:
    if "[ROL:CEO]" in instrucciones:
        return RESUMEN
    if "[ROL:Product Manager]" in instrucciones:
        return REQUISITOS
    if "[ROL:Arquitecta de Software]" in instrucciones:
        return UML
    if "[ROL:Ingeniero de Software]" in instrucciones:
        codigo = JUEGO if "errores" in mensaje else JUEGO_CON_ERROR
        return f"```html\n{codigo}\n```"
    if "[ROL:QA Engineer]" in instrucciones:
        return PRUEBAS
    return "Entendido."
