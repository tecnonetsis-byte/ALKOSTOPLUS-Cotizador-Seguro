"""Verifica la presencia de entregables. Ejecutar desde la raíz del repositorio.
No requiere paquetes externos. Para inspeccionar duración necesita ffprobe opcional.
"""
from pathlib import Path
import json
import subprocess
import sys

raiz = Path(__file__).resolve().parent
archivos = [
    'README.md', '.env.example', '.gitignore', 'TEXTO_PARA_ENTREGAR.txt',
    'config/catalogo_simulado.json', 'config/politicas.json',
    'cotizador/__main__.py', 'cotizador/core.py', 'cotizador/evaluation.py',
    'cotizador/webserver.py', 'web/index.html', 'web/app.js', 'web/styles.css',
    'tests/test_workflow.py', 'tests/test_webserver.py', 'resultados/evaluacion.json',
    'resultados/ejecucion_unittest.txt', 'docs/PRUEBAS_Y_MEJORAS.md',
    'docs/GUION_VIDEO.md', 'entregables/VIDEO_DEMO.mp4',
]
faltan=[p for p in archivos if not (raiz/p).is_file()]
for p in archivos:
    print(('FALTA' if p in faltan else 'OK   '),p)
if faltan:
    print('NO APTO: faltan archivos obligatorios.')
    sys.exit(1)
r=json.loads((raiz/'resultados/evaluacion.json').read_text(encoding='utf-8'))
assert r['aciertos']==14 and r['casos']==14, 'Resultados inesperados'
try:
    f=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                      '-of','default=noprint_wrappers=1:nokey=1',
                      str(raiz/'entregables/VIDEO_DEMO.mp4')],capture_output=True,
                      text=True,check=True)
    segundos=float(f.stdout.strip())
    assert 180 <= segundos <= 300, f'Duracion no valida: {segundos}'
    print(f'VIDEO VERIFICADO: {segundos/60:.2f} minutos')
except FileNotFoundError:
    print('Duracion no validada: ffprobe no esta instalado; archivo presente.')
print('ARCHIVOS VERIFICADOS. Recuerda publicar el repositorio y aportar nombres reales.')
