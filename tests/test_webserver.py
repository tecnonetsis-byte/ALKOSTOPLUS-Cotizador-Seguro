import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from cotizador.core import Cotizador
from cotizador.webserver import Handler

class PruebasHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        Handler.cotizador=Cotizador(Path(cls.temp.name)/'http.json')
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.cleanup()

    def req(self,route,data=None):
        if data is None:
            with urlopen(self.base+route,timeout=5) as r:
                return r.status,r.read().decode()
        req=Request(self.base+route,method='POST',headers={'Content-Type':'application/json'},data=json.dumps(data).encode())
        with urlopen(req,timeout=5) as r:
            return r.status,json.loads(r.read())

    def test_index_html_responde(self):
        status,body=self.req('/')
        self.assertEqual(status,200)
        self.assertIn('Cotizador Seguro',body)

    def test_catalogo_responde(self):
        status,body=self.req('/api/catalogo')
        self.assertEqual(status,200)
        self.assertEqual(len(json.loads(body)['productos']),4)

    def test_post_procesar(self):
        status,data=self.req('/api/procesar',{'mensaje':'Cotiza 2 unidades de CEL-A1 con 5% de descuento'})
        self.assertEqual(status,200)
        self.assertEqual(data['solicitud']['total'],'2945.00')

    def test_post_aprobacion(self):
        _,data=self.req('/api/procesar',{'mensaje':'Cotiza TAB-T1 con 15% de descuento'})
        self.assertEqual(data['estado'],'PENDIENTE_APROBACION')
        _,dec=self.req('/api/decidir',{'id':data['solicitud']['id'],'decision':'aprobar','responsable':'Revisor simulado'})
        self.assertEqual(dec['estado'],'APROBADO_HUMANO')

if __name__ == '__main__':unittest.main()
