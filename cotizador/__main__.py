"""Interfaz CLI reproducible para cotización, aprobación y evaluación."""
import argparse
import json
from .core import Cotizador, catalogo, clasificar


def main() -> None:
    ap = argparse.ArgumentParser(description="Cotizador seguro - solo datos ficticios")
    sub = ap.add_subparsers(dest="accion", required=True)
    sub.add_parser("catalogo", help="Muestra el catálogo ficticio")
    ruta = sub.add_parser("ruta", help="Determina debe_usar / no_debe_usar")
    ruta.add_argument("--mensaje", required=True)
    proc = sub.add_parser("procesar", help="Ejecuta workflow completo")
    proc.add_argument("--mensaje", required=True)
    proc.add_argument("--estado", default=None)
    dec = sub.add_parser("decidir", help="Aprobación/rechazo por humano")
    dec.add_argument("--id", required=True)
    dec.add_argument("--decision", choices=["aprobar", "rechazar"], required=True)
    dec.add_argument("--responsable", required=True)
    dec.add_argument("--estado", default=None)
    ev = sub.add_parser("evaluar", help="Ejecuta casos reproducibles")
    ev.add_argument("--guardar", default=None, help="Archivo JSON de resultados")
    args = ap.parse_args()
    if args.accion == "catalogo":
        res = catalogo()
    elif args.accion == "ruta":
        res = clasificar(args.mensaje)
    elif args.accion == "procesar":
        res = Cotizador(args.estado).procesar(args.mensaje)
    elif args.accion == "decidir":
        res = Cotizador(args.estado).decidir(args.id, args.decision, args.responsable)
    else:
        from .evaluation import evaluar
        res = evaluar(args.guardar)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
