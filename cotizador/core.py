"""Motor verificable: instrucciones, herramientas, memoria, estado y control.

Todos los datos son ficticios. Solo se persisten campos mínimos del pedido;
jamás se guarda el mensaje original ni información personal.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent.parent
CATALOGO = BASE / "config" / "catalogo_simulado.json"
POLITICAS = BASE / "config" / "politicas.json"
ESTADO_PREDETERMINADO = BASE / "estado" / "solicitudes.json"
CODIGO_RE = re.compile(r"\b(?:CEL|TAB|ACC|AUD)-[A-Z0-9]+\b", re.I)


def limpiar(t: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", t.lower())
                   if unicodedata.category(ch) != "Mn")


def momento() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dinero(n: Decimal) -> str:
    return str(n.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _json(ruta: Path) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def catalogo() -> dict[str, Any]:
    return _json(CATALOGO)


def politicas() -> dict[str, Any]:
    return _json(POLITICAS)


def clasificar(mensaje: str) -> dict[str, str]:
    """Router previo a herramientas. Rechaza PII y consultas fuera de dominio."""
    if not isinstance(mensaje, str) or not mensaje.strip():
        return {"ruta": "no_debe_usar", "motivo": "Mensaje vacío o inválido"}
    m = limpiar(mensaje)
    prohibidos = (
        "cliente real", "clientes reales", "dato personal", "datos personales",
        "cedula", "c.i.", "numero de tarjeta", "tarjeta de credito",
        "contrasena", "password", "api key", "apikey", "clave privada",
        "pin bancario", "cvv", "documento de identidad"
    )
    if any(p in m for p in prohibidos):
        return {"ruta": "no_debe_usar", "motivo": "Control de privacidad: no usar datos sensibles"}
    indicios = ("cotiza", "cotizar", "cotizacion", "precio", "cuanto cuesta",
                "cuanto vale", "presupuesto", "comprar", "descuento", "coste")
    if CODIGO_RE.search(mensaje.upper()) or any(p in m for p in indicios):
        return {"ruta": "debe_usar", "motivo": "Solicitud comercial dentro del dominio"}
    return {"ruta": "no_debe_usar", "motivo": "Consulta fuera del alcance del cotizador"}


class ArchivoEstado:
    """Memoria persistente mínima de solicitudes, local y sin PII."""
    def __init__(self, ruta: str | Path | None = None):
        self.ruta = Path(ruta or os.getenv("RUTA_ESTADO", str(ESTADO_PREDETERMINADO)))
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def cargar(self) -> dict[str, Any]:
        if not self.ruta.exists():
            return {"solicitudes": {}}
        data = _json(self.ruta)
        if not isinstance(data.get("solicitudes"), dict):
            raise ValueError("El archivo de estado está corrupto")
        return data

    def guardar(self, data: dict[str, Any]) -> None:
        # Escritura atómica. La demo es monousuario; no apto para producción concurrente.
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False,
                                         dir=self.ruta.parent, suffix=".tmp") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            temporal = f.name
        os.replace(temporal, self.ruta)

    def poner(self, solicitud: dict[str, Any]) -> None:
        data = self.cargar()
        data["solicitudes"][solicitud["id"]] = solicitud
        self.guardar(data)

    def obtener(self, ident: str) -> dict[str, Any] | None:
        return self.cargar()["solicitudes"].get(ident)

    def resumen(self) -> dict[str, int]:
        solicitudes = list(self.cargar()["solicitudes"].values())
        return {"total": len(solicitudes),
                "aprobadas": sum(x["estado"].startswith("APROBADO") for x in solicitudes),
                "pendientes": sum(x["estado"] == "PENDIENTE_APROBACION" for x in solicitudes),
                "rechazadas": sum(x["estado"].startswith("RECHAZADO") for x in solicitudes)}


class Cotizador:
    def __init__(self, estado: str | Path | None = None):
        self.catalogo = catalogo()
        self.politicas = politicas()
        self.almacen = ArchivoEstado(estado)
        self.memoria_sesion: list[dict[str, str]] = []  # memoria efímera, sin PII

    def _resultado(self, ruta: str, estado: str, motivo: str, **extra: Any) -> dict[str, Any]:
        return {"ruta": ruta, "estado": estado, "motivo": motivo, **extra}

    def _validar(self, texto: str) -> tuple[dict[str, Any] | None, str | None]:
        codigos = list(dict.fromkeys(c.upper() for c in CODIGO_RE.findall(texto)))
        if len(codigos) != 1:
            return None, "Indique exactamente un código de producto, por ejemplo CEL-A1"
        producto = next((p for p in self.catalogo["productos"]
                         if p["codigo"] == codigos[0]), None)
        if not producto:
            return None, "Código inexistente en el catálogo simulado: " + codigos[0]
        m = limpiar(texto)
        cantidad = 1
        encontrado = re.search(r"\b(\d+)\s*(?:unidades?|uds?|piezas?)\b", m)
        if not encontrado:
            encontrado = re.search(r"\bx\s*(\d+)\b", m)
        if encontrado:
            cantidad = int(encontrado.group(1))
        if cantidad < 1:
            return None, "La cantidad debe ser al menos 1"
        tasa = Decimal("0")
        descuento = re.search(r"(-?\d+(?:[.,]\d+)?)\s*%", m)
        if descuento:
            try:
                tasa = Decimal(descuento.group(1).replace(",", "."))
            except InvalidOperation:
                return None, "Descuento no válido"
        if tasa < 0:
            return None, "El descuento no puede ser negativo"
        return {"producto": producto, "cantidad": cantidad, "descuento": tasa}, None

    def procesar(self, texto: str) -> dict[str, Any]:
        ruta = clasificar(texto)
        if ruta["ruta"] == "no_debe_usar":
            return self._resultado("no_debe_usar", "FUERA_DE_ALCANCE", ruta["motivo"],
                                   control="HERRAMIENTAS_NO_INVOCADAS")
        datos, error = self._validar(texto)
        if error:
            return self._resultado("debe_usar", "ERROR_VALIDACION", error,
                                   control="SIN_COTIZACION")
        assert datos is not None
        p = datos["producto"]
        cantidad = datos["cantidad"]
        descuento = datos["descuento"]
        if cantidad > p["stock"]:
            return self._resultado("debe_usar", "RECHAZADO_REGLA",
                f"Stock ficticio insuficiente: solicitado {cantidad}, disponible {p['stock']}",
                control="BLOQUEO_STOCK")
        maximo = Decimal(self.politicas["descuento_absoluto_max_pct"])
        if descuento > maximo:
            return self._resultado("debe_usar", "RECHAZADO_REGLA",
                f"Descuento {descuento}% excede el máximo absoluto de {maximo}%",
                control="BLOQUEO_DESCUENTO")
        precio = Decimal(p["precio"])
        subtotal = precio * cantidad
        total = subtotal * (Decimal(100) - descuento) / Decimal(100)
        pendiente = descuento > Decimal(self.politicas["descuento_automatico_max_pct"])
        estado = "PENDIENTE_APROBACION" if pendiente else "APROBADO_AUTOMATICO"
        pedido = {
            "id": "SOL-" + uuid.uuid4().hex[:10].upper(),
            "creado_utc": momento(),
            "codigo": p["codigo"], "producto": p["nombre"],
            "cantidad": cantidad, "moneda": self.catalogo["moneda"],
            "precio_unitario": dinero(precio), "subtotal": dinero(subtotal),
            "descuento_pct": dinero(descuento), "total": dinero(total),
            "estado": estado,
            "control": "ESPERA_APROBACION_HUMANA" if pendiente else "REGLAS_AUTOMATICAS_OK",
            "historial": [
                {"fecha_utc": momento(), "evento": "RECIBIDO"},
                {"fecha_utc": momento(), "evento": "VALIDADO_CATALOGO_Y_STOCK"},
                {"fecha_utc": momento(), "evento": estado}
            ]
        }
        self.almacen.poner(pedido)
        self.memoria_sesion.append({"id": pedido["id"], "codigo": p["codigo"]})
        return self._resultado("debe_usar", estado,
            "Requiere aprobación humana" if pendiente else "Cotización autorizada automáticamente",
            solicitud=pedido, control=pedido["control"])

    def decidir(self, ident: str, decision: str, responsable: str) -> dict[str, Any]:
        if not responsable or len(responsable.strip()) < 3:
            return self._resultado("debe_usar", "ERROR_CONTROL", "Se requiere responsable identificable")
        if decision not in ("aprobar", "rechazar"):
            return self._resultado("debe_usar", "ERROR_CONTROL", "Decisión inválida")
        pedido = self.almacen.obtener(ident)
        if not pedido:
            return self._resultado("debe_usar", "ERROR_CONTROL", "Solicitud inexistente")
        if pedido["estado"] != "PENDIENTE_APROBACION":
            return self._resultado("debe_usar", "ERROR_CONTROL",
                                   "Solo se puede decidir sobre una solicitud pendiente")
        pedido["estado"] = "APROBADO_HUMANO" if decision == "aprobar" else "RECHAZADO_HUMANO"
        pedido["control"] = "DECISION_HUMANA_REGISTRADA"
        pedido["historial"].append({"fecha_utc": momento(), "evento": pedido["estado"],
                                    "responsable_demo": responsable.strip()[:60]})
        self.almacen.poner(pedido)
        return self._resultado("debe_usar", pedido["estado"],
                               "Decisión humana aplicada y registrada", solicitud=pedido,
                               control=pedido["control"])
