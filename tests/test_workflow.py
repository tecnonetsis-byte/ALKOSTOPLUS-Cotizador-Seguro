import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from cotizador.core import Cotizador, clasificar
from cotizador.evaluation import evaluar


class TestsWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'estado.json'
        self.m = Cotizador(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ruta_venta(self):
        self.assertEqual(clasificar('¿Cuánto cuesta CEL-A1?')['ruta'], 'debe_usar')

    def test_ruta_externa(self):
        self.assertEqual(clasificar('¿Qué tiempo hará mañana?')['ruta'], 'no_debe_usar')

    def test_datos_sensibles_bloqueados(self):
        res = self.m.procesar('Cotiza CEL-A1 con datos personales de un cliente real')
        self.assertEqual(res['estado'], 'FUERA_DE_ALCANCE')
        self.assertFalse(self.path.exists())

    def test_precio_real_del_catalogo_ficticio(self):
        r = self.m.procesar('Cotiza 2 unidades de CEL-A1 con 5% de descuento')
        self.assertEqual(r['estado'], 'APROBADO_AUTOMATICO')
        self.assertEqual(r['solicitud']['total'], '2945.00')
        self.assertEqual(r['solicitud']['moneda'], 'BOB')

    def test_precio_sin_descuento(self):
        self.assertEqual(self.m.procesar('Precio de AUD-H1')['solicitud']['total'], '230.00')

    def test_aprobacion_humana_obligatoria(self):
        r = self.m.procesar('Cotiza 1 unidad de TAB-T1 con 15% de descuento')
        self.assertEqual(r['estado'], 'PENDIENTE_APROBACION')
        self.assertEqual(r['solicitud']['total'], '2380.00')
        self.assertEqual(self.m.almacen.obtener(r['solicitud']['id'])['estado'], 'PENDIENTE_APROBACION')

    def test_humano_aprueba(self):
        r = self.m.procesar('Cotiza CEL-A1 con 15% de descuento')
        a = self.m.decidir(r['solicitud']['id'], 'aprobar', 'Revisor simulado')
        self.assertEqual(a['estado'], 'APROBADO_HUMANO')
        self.assertEqual(a['solicitud']['historial'][-1]['responsable_demo'],'Revisor simulado')

    def test_humano_rechaza(self):
        r = self.m.procesar('Cotiza CEL-A1 con 15% de descuento')
        self.assertEqual(self.m.decidir(r['solicitud']['id'],'rechazar','Revisor simulado')['estado'], 'RECHAZADO_HUMANO')

    def test_prohibido_aprobar_dos_veces(self):
        r = self.m.procesar('Cotiza CEL-A1 con 15% de descuento')
        i = r['solicitud']['id']
        self.m.decidir(i,'aprobar','Revisor simulado')
        self.assertEqual(self.m.decidir(i,'aprobar','Revisor simulado')['estado'],'ERROR_CONTROL')

    def test_prohibido_aprobar_sin_responsable(self):
        r = self.m.procesar('Cotiza CEL-A1 con 15% de descuento')
        self.assertEqual(self.m.decidir(r['solicitud']['id'],'aprobar','')['estado'],'ERROR_CONTROL')

    def test_stock_bloqueado(self):
        self.assertEqual(self.m.procesar('Cotiza 99 unidades de ACC-C1')['estado'], 'RECHAZADO_REGLA')
        self.assertFalse(self.path.exists())

    def test_descuento_excesivo(self):
        self.assertEqual(self.m.procesar('Cotiza CEL-A1 con 30% de descuento')['control'],'BLOQUEO_DESCUENTO')

    def test_codigo_inexistente(self):
        self.assertEqual(self.m.procesar('Precio de CEL-Z9')['estado'],'ERROR_VALIDACION')

    def test_codigo_omitido(self):
        self.assertEqual(self.m.procesar('Cotiza un dispositivo')['estado'],'ERROR_VALIDACION')

    def test_cantidad_cero(self):
        self.assertEqual(self.m.procesar('Cotiza 0 unidades de CEL-A1')['estado'],'ERROR_VALIDACION')

    def test_dos_productos_rechazados(self):
        self.assertEqual(self.m.procesar('Cotiza CEL-A1 y ACC-C1')['estado'],'ERROR_VALIDACION')

    def test_almacen_no_guarda_mensaje(self):
        r=self.m.procesar('Cotiza CEL-A1')
        data=json.loads(self.path.read_text())
        self.assertNotIn('mensaje', str(data))
        self.assertIn(r['solicitud']['id'],data['solicitudes'])

    def test_eval_14_casos(self):
        r=evaluar()
        self.assertEqual(r['casos'],14)
        self.assertEqual(r['aciertos'],14)
        self.assertEqual(r['porcentaje_acierto'],100.0)

if __name__ == '__main__': unittest.main()
