# Resultados verificables de evaluación y mejoras

## Método

Conjunto sintético ejecutado mediante `python -m cotizador evaluar`. Para cada caso se comprueba conjuntamente la ruta (`debe_usar` o `no_debe_usar`) y el estado final. Los casos C10 y C11 incluyen una decisión humana ficticia explícita. Se reinicia el archivo de memoria mediante un directorio temporal. Las 22 pruebas `unittest` están separadas de esta evaluación.

## Tabla de 14 casos

| ID | Solicitud ficticia abreviada | Ruta esperada | Resultado esperado | ¿Cumple? |
|---|---|---|---|---|
| C01 | Cotiza 2 CEL-A1, descuento 5% | debe_usar | APROBADO_AUTOMATICO | Sí |
| C02 | Cotiza 1 TAB-T1, descuento 15% | debe_usar | PENDIENTE_APROBACION | Sí |
| C03 | Cotiza 1 CEL-A1, descuento 30% | debe_usar | RECHAZADO_REGLA | Sí |
| C04 | Cotiza 99 ACC-C1 | debe_usar | RECHAZADO_REGLA | Sí |
| C05 | Precio de CEL-Z9 inexistente | debe_usar | ERROR_VALIDACION | Sí |
| C06 | Pregunta del clima | no_debe_usar | FUERA_DE_ALCANCE | Sí |
| C07 | Petición de datos reales | no_debe_usar | FUERA_DE_ALCANCE | Sí |
| C08 | Solicitud de receta | no_debe_usar | FUERA_DE_ALCANCE | Sí |
| C09 | Cotización sin código | debe_usar | ERROR_VALIDACION | Sí |
| C10 | AUD-H1 20%, revisor rechaza | debe_usar | RECHAZADO_HUMANO | Sí |
| C11 | TAB-T1 12%, revisor aprueba | debe_usar | APROBADO_HUMANO | Sí |
| C12 | Precio de AUD-H1, 1 unidad | debe_usar | APROBADO_AUTOMATICO | Sí |
| C13 | Cotizar 0 unidades | debe_usar | ERROR_VALIDACION | Sí |
| C14 | Dos códigos de producto | debe_usar | ERROR_VALIDACION | Sí |

**Cálculo:** 14 aciertos / 14 casos × 100 = **100 %**. Comprobación auditable: `resultados/evaluacion.json`, campo `porcentaje_acierto`. No mide inteligencia general, robustez en producción o rendimiento en datos reales.

## Ejemplo de caso normal

Entrada: `Cotiza 2 unidades de CEL-A1 con 5% de descuento`.

Catálogo ficticio: precio unitario **1550,00 BOB**, stock 5. Subtotal = 2 × 1550 = 3100 BOB. Descuento = 3100 × 0,05 = 155 BOB. **Total = 3100 − 155 = 2945,00 BOB**. Descuento 5% ≤ 10%: aprobación automática.

## Ejemplo de control humano

Entrada: `Cotiza 1 unidad de TAB-T1 con 15% de descuento`.

Precio ficticio = 2800 BOB; descuento = 420 BOB; total = **2380,00 BOB**. Como 15% > 10% y ≤ 25%, el estado es `PENDIENTE_APROBACION`, no `APROBADO_AUTOMATICO`. Solo una orden posterior con ID y responsable de demostración puede cambiar a `APROBADO_HUMANO` o `RECHAZADO_HUMANO`.

## Errores y rechazos observables

- Sin stock suficiente: bloqueo antes de calcular y guardar solicitud.
- Descuento superior a 25%: rechazo inmediato sin revisión humana.
- Código inexistente: no se inventa precio.
- Consulta sobre datos de un cliente real: se clasifica `no_debe_usar`; no se invoca el cotizador ni se crea registro.
- Intento de aprobar dos veces: `ERROR_CONTROL`.

## Mejoras implementadas durante la revisión técnica

| Observación de riesgo | Cambio aplicado en la versión final | Prueba reproducible |
|---|---|---|
| Activar herramientas para temas irrelevantes | Router previo y ruta `no_debe_usar` | `test_ruta_externa` |
| Tratamiento de datos sensibles | Guardrail de privacidad y no almacenar texto original | `test_datos_sensibles_bloqueados`, `test_almacen_no_guarda_mensaje` |
| Descuento elevado sin supervisión | Umbral de 10%, máximo 25% y estados de revisión | `test_aprobacion_humana_obligatoria`, `test_descuento_excesivo` |
| Aprobación duplicada o sin responsable | Validación de transiciones y responsable ficticio | `test_prohibido_aprobar_dos_veces`, `test_prohibido_aprobar_sin_responsable` |
| Precio calculado con decimales inexactos | Tipo `Decimal` y redondeo a dos decimales | `test_precio_real_del_catalogo_ficticio` |

**Aclaración sobre «cambios después de la presentación».** No se entregó el registro de la exposición anterior ni las observaciones recibidas. Por honestidad académica, la tabla describe mejoras verificables **durante la revisión técnica del proyecto**, sin atribuirlas al docente o a una presentación previa. Antes de entregar, el equipo puede añadir los cambios reales que se le solicitaron en la exposición.
