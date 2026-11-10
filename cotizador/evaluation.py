"""Conjunto público de pruebas funcionales, incluye rutas y decisiones humanas.

Porcentaje = casos que cumplen simultáneamente ruta y estado esperados / total * 100.
"""
from pathlib import Path
import json
import tempfile
from .core import Cotizador

CASOS = [
    ("C01", "Cotiza 2 unidades de CEL-A1 con 5% de descuento", "debe_usar", "APROBADO_AUTOMATICO", None),
    ("C02", "Cotiza 1 unidad de TAB-T1 con 15% de descuento", "debe_usar", "PENDIENTE_APROBACION", None),
    ("C03", "Cotiza 1 unidad de CEL-A1 con 30% de descuento", "debe_usar", "RECHAZADO_REGLA", None),
    ("C04", "Cotiza 99 unidades de ACC-C1", "debe_usar", "RECHAZADO_REGLA", None),
    ("C05", "¿Cuánto cuesta CEL-Z9?", "debe_usar", "ERROR_VALIDACION", None),
    ("C06", "¿Qué tiempo hará mañana?", "no_debe_usar", "FUERA_DE_ALCANCE", None),
    ("C07", "Busca datos personales de un cliente real", "no_debe_usar", "FUERA_DE_ALCANCE", None),
    ("C08", "Dame una receta de sopa", "no_debe_usar", "FUERA_DE_ALCANCE", None),
    ("C09", "Cotiza un dispositivo con 5% de descuento", "debe_usar", "ERROR_VALIDACION", None),
    ("C10", "Cotiza 1 unidad de AUD-H1 con 20% de descuento", "debe_usar", "RECHAZADO_HUMANO", "rechazar"),
    ("C11", "Cotiza 1 unidad de TAB-T1 con 12% de descuento", "debe_usar", "APROBADO_HUMANO", "aprobar"),
    ("C12", "Precio de AUD-H1", "debe_usar", "APROBADO_AUTOMATICO", None),
    ("C13", "Cotiza 0 unidades de CEL-A1", "debe_usar", "ERROR_VALIDACION", None),
    ("C14", "Cotiza 2 unidades de CEL-A1 y ACC-C1", "debe_usar", "ERROR_VALIDACION", None),
]


def evaluar(guardar: str | None = None) -> dict:
    filas = []
    with tempfile.TemporaryDirectory(prefix="evaluacion_cotizador_") as tmp:
        motor = Cotizador(Path(tmp) / "estado.json")
        for cid, mensaje, ruta_e, estado_e, decision in CASOS:
            res = motor.procesar(mensaje)
            if decision:
                res = motor.decidir(res["solicitud"]["id"], decision, "Evaluador ficticio")
            correcto = res["ruta"] == ruta_e and res["estado"] == estado_e
            filas.append({"caso": cid, "mensaje_simulado": mensaje,
                          "ruta_esperada": ruta_e, "ruta_obtenida": res["ruta"],
                          "estado_esperado": estado_e, "estado_obtenido": res["estado"],
                          "acierto": correcto, "control": res.get("control", "NO_APLICA")})
    aciertos = sum(f["acierto"] for f in filas)
    resultado = {"casos": len(filas), "aciertos": aciertos,
                 "porcentaje_acierto": round(100 * aciertos / len(filas), 2),
                 "formula": "aciertos / casos * 100", "filas": filas,
                 "alcance": "Pruebas funcionales sintéticas; no valida desempeño de IA generativa ni en producción"}
    if guardar:
        ruta = Path(guardar)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(resultado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return resultado
