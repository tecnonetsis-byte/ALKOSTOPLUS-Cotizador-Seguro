"""Servidor local estándar (sin frameworks ni dependencias externas)."""
from __future__ import annotations
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .core import Cotizador, catalogo

WEB = Path(__file__).resolve().parent.parent / "web"


class Handler(BaseHTTPRequestHandler):
    cotizador: Cotizador

    def respuesta(self, obj: dict, codigo: int = 200):
        contenido = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def do_GET(self):
        ruta = urlparse(self.path).path
        if ruta in ("/api/catalogo", "/api/estado", "/api/salud"):
            valor = (catalogo() if ruta == "/api/catalogo" else
                     self.cotizador.almacen.resumen() if ruta == "/api/estado" else
                     {"estado": "ok", "modo": "solo_datos_simulados"})
            return self.respuesta(valor)
        archivos = {"/": ("index.html", "text/html"),
                    "/styles.css": ("styles.css", "text/css"),
                    "/app.js": ("app.js", "text/javascript")}
        if ruta not in archivos:
            return self.respuesta({"error": "No encontrado"}, 404)
        nombre, tipo = archivos[ruta]
        contenido = (WEB / nombre).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo + "; charset=utf-8")
        self.send_header("Content-Length", str(len(contenido)))
        self.end_headers()
        self.wfile.write(contenido)

    def do_POST(self):
        ruta = urlparse(self.path).path
        if ruta not in ("/api/procesar", "/api/decidir"):
            return self.respuesta({"error": "No encontrado"}, 404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n > 8000 or n <= 0:
                return self.respuesta({"error": "Tamaño de petición no admitido"}, 413)
            obj = json.loads(self.rfile.read(n))
            if not isinstance(obj, dict):
                return self.respuesta({"error": "Se requiere objeto JSON"}, 400)
            if ruta == "/api/procesar":
                txt = obj.get("mensaje", "")
                if not isinstance(txt, str) or len(txt) > 1200:
                    return self.respuesta({"error": "Mensaje inválido"}, 400)
                result = self.cotizador.procesar(txt)
            else:
                ident = obj.get("id", "")
                decision = obj.get("decision", "")
                responsable = obj.get("responsable", "")
                if not all(isinstance(i, str) and len(i) <= 100 for i in (ident, decision, responsable)):
                    return self.respuesta({"error": "Parámetros no válidos"}, 400)
                result = self.cotizador.decidir(ident, decision, responsable)
            return self.respuesta(result)
        except (ValueError, json.JSONDecodeError) as err:
            return self.respuesta({"error": "Petición incorrecta: " + str(err)}, 400)

    def log_message(self, formato, *args):
        # No imprimir el cuerpo de mensajes para evitar exposición accidental.
        pass


def main():
    ap = argparse.ArgumentParser(description="Interfaz web local del cotizador")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--puerto", type=int, default=8765)
    ap.add_argument("--estado", default=None)
    a = ap.parse_args()
    Handler.cotizador = Cotizador(a.estado)
    servidor = ThreadingHTTPServer((a.host, a.puerto), Handler)
    print(f"Demo local disponible en http://{a.host}:{a.puerto}", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Servidor detenido")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
