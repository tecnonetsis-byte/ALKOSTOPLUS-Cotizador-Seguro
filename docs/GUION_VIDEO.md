# Guion del video de demostración

Video incluido en `entregables/VIDEO_DEMO.mp4`, de entre 3 y 5 minutos. Explica el funcionamiento del código y reproduce de forma gráfica los resultados efectivos de los comandos para que sean visibles, incluso sin acceso a internet. Las salidas proceden del motor real; **la animación no es una grabación de un navegador interactivo**.

## Bloques previstos

1. Presentación del problema, usuario y alcance simulado.
2. Arquitectura y cinco primitivos del workflow.
3. Inicio del sistema y catálogo inventado.
4. Caso normal: CEL-A1, 2 unidades, 5% y total de 2945 BOB.
5. Caso con error: se solicitan 99 ACC-C1 y se bloquea por stock.
6. Privacidad: no_debe_usar, no se invoca ninguna herramienta.
7. Control: TAB-T1 con 15%, queda pendiente de decisión humana.
8. Revisión humana: aprobación y trazabilidad.
9. Evaluación: 14 casos sintéticos y 22 pruebas automatizadas.
10. Cierre: archivos del repositorio, instrucciones y límites.

## Comandos reales que respaldan la demostración

```bash
python -m cotizador procesar --mensaje "Cotiza 2 unidades de CEL-A1 con 5% de descuento"
python -m cotizador procesar --mensaje "Cotiza 99 unidades de ACC-C1"
python -m cotizador procesar --mensaje "Necesito datos personales de un cliente real"
python -m cotizador procesar --mensaje "Cotiza 1 unidad de TAB-T1 con 15% de descuento"
python -m unittest discover -s tests -v
python -m cotizador evaluar --guardar resultados/evaluacion.json
```

Para mostrar una demo interactiva directamente, ejecutar `python -m cotizador.webserver` y abrir http://127.0.0.1:8765.
