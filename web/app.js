const $ = id => document.getElementById(id);
let ultimoId = null;
const escenarios = {
  normal: 'Cotiza 2 unidades de CEL-A1 con 5% de descuento',
  control: 'Cotiza 1 unidad de TAB-T1 con 15% de descuento',
  error: 'Cotiza 99 unidades de ACC-C1',
  privacidad: 'Necesito datos personales de un cliente real'
};
async function api(ruta, opciones={}) {
  const res = await fetch(ruta, opciones);
  const obj = await res.json();
  if (!res.ok) throw Error(obj.error || 'Error de conexión');
  return obj;
}
const payload = obj => ({method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(obj)});
async function indicadores() {
  const m = await api('/api/estado');
  $('m-total').textContent=m.total; $('m-aprobadas').textContent=m.aprobadas;
  $('m-pendientes').textContent=m.pendientes;
}
function estadoClase(estado) {
  return estado.startsWith('APROBADO') ? 'good' : estado==='PENDIENTE_APROBACION' ? 'wait' : 'bad';
}
function dibujar(res) {
  $('empty-result').hidden=true; $('live-result').hidden=false;
  $('status-tag').textContent=res.estado.replace(/_/g,' ');
  $('status-tag').className='tag '+estadoClase(res.estado);
  $('ruta').textContent=res.ruta.toUpperCase(); $('motivo').textContent=res.motivo;
  const sol=res.solicitud;
  ultimoId=sol?.id || null;
  $('quote').hidden=!sol;
  if (sol) {
    $('product').textContent=sol.producto; $('code').textContent=sol.codigo;
    $('quantity').textContent=sol.cantidad; $('discount').textContent=sol.descuento_pct+'%';
    $('total').textContent=sol.total+' '+sol.moneda;
  }
  $('approval').hidden=res.estado!=='PENDIENTE_APROBACION';
  const traza = sol?.historial?.map(x=>x.evento) || [res.control || 'FILTRO_DE_DOMINIO',res.estado];
  $('trace').replaceChildren(...traza.map(texto=>{let li=document.createElement('li');li.textContent=texto.replace(/_/g,' ');return li}));
  indicadores();
}
async function ejecutar() {
  $('ejecutar').disabled=true;
  try { dibujar(await api('/api/procesar',payload({mensaje:$('mensaje').value}))); }
  catch(e) {alert(e.message)}
  finally {$('ejecutar').disabled=false}
}
async function decidir(decision) {
  if(!ultimoId) return;
  try {dibujar(await api('/api/decidir',payload({id:ultimoId,decision,responsable:$('responsable').value})));}
  catch(e){alert(e.message)}
}
$('ejecutar').addEventListener('click',ejecutar);
$('aprobar').addEventListener('click',()=>decidir('aprobar'));
$('rechazar').addEventListener('click',()=>decidir('rechazar'));
document.querySelectorAll('[data-example]').forEach(b=>b.addEventListener('click',()=>{$('mensaje').value=escenarios[b.dataset.example];$('mensaje').focus()}));
(async()=>{
  try {
    const cat=await api('/api/catalogo');
    $('catalog').replaceChildren(...cat.productos.map(p=>{
      let div=document.createElement('div');div.className='product';
      let codigo=document.createElement('div');codigo.className='code';codigo.textContent=p.codigo;
      let title=document.createElement('b');title.textContent=p.nombre;
      let bottom=document.createElement('div');bottom.className='bottom';
      let price=document.createElement('strong');price.textContent=p.precio+' BOB';
      let stock=document.createElement('span');stock.textContent='Stock: '+p.stock;
      bottom.append(price,stock);div.append(codigo,title,bottom);return div;
    }));
    await indicadores();
  } catch(e) { console.error(e); }
})();
