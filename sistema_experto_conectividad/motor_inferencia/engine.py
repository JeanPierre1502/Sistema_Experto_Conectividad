# motor_inferencia/engine.py
from typing import Dict, Any, List
import logging
from sistema_experto_conectividad.base_de_conocimiento import reglas as reglas_mod
import sistema_experto_conectividad.motor_inferencia.pruebas_red as pruebas_red
import sistema_experto_conectividad.motor_inferencia.fuzzificacion as fuzzificacion
from sistema_experto_conectividad.storage import historial
from sistema_experto_conectividad.storage.historial import registrar_diagnostico

logger = logging.getLogger("engine")
logger.setLevel(logging.INFO)

def ejecutar_diagnostico(gateway_ip: str = None, auto_detect_gateway: bool = True) -> Dict[str, Any]:
    """
    Ejecuta pruebas y devuelve dict con resultados.
    Si gateway_ip es None y auto_detect_gateway True, intenta detectarlo automáticamente.
    """
    used_gateway = gateway_ip
    if not gateway_ip and auto_detect_gateway:
        gw = pruebas_red.detectar_gateway_sistema()
        used_gateway = gw

    conn_ok, lat_ms, perdida = pruebas_red.verificar_conexion()
    dns_ok = pruebas_red.verificar_dns()
    gw_ok = False
    if used_gateway:
        gw_ok = pruebas_red.verificar_gateway(used_gateway)
    estado_adaptadores = pruebas_red.estado_adaptadores()
    puertos_http = pruebas_red.comprobar_puerto("www.google.com", 80)
    puertos_https = pruebas_red.comprobar_puerto("www.google.com", 443)
    servicios = pruebas_red.probar_servicios()

    severidad = fuzzificacion.evaluar_severidad(lat_ms, perdida)

    datos = {
        "conexion": conn_ok,
        "latencia_ms": lat_ms,
        "perdida_pct": perdida,
        "dns": dns_ok,
        "gateway": gw_ok,
        "gateway_ip": used_gateway,
        "estado_adaptadores": estado_adaptadores,
        "puertos_http": puertos_http,
        "puertos_https": puertos_https,
        "servicios": servicios,
        "severidad": severidad
    }
    return datos

def inferir(datos: Dict[str, Any]) -> List[str]:
    hallazgos = []
    # Usamos las reglas definidas en base_de_conocimiento.reglas.REGLAS
    for r in reglas_mod.REGLAS:
        try:
            matched, msg, prio = r(datos)
            if matched:
                hallazgos.append((prio, msg))
        except Exception as e:
            logger.exception("Error evaluando regla: %s", e)
    hallazgos.sort(key=lambda x: -x[0])
    return [h[1] for h in hallazgos] if hallazgos else ["Fallo no identificado: requiere diagnóstico avanzado."]

def generar_pasos_accion(datos: Dict[str, Any], inferencias: List[str]) -> List[Dict[str, Any]]:
    """
    Convierte las inferencias en una lista de pasos accionables y explicaciones.
    Cada paso: {title, detalle, paso_a_paso, prioridad}
    """
    pasos = []
    # Ejemplos mapeados
    for msg in inferencias:
        if "Sin conexión" in msg:
            pasos.append({
                "title": "Verifica conexión física / adaptador",
                "detalle": ("El sistema no detecta conexión ni resolución DNS. "
                            "Revisa que el cable Ethernet esté conectado o que el Wi-Fi esté activado."),
                "paso_a_paso": [
                    "Comprueba el cable o conecta al Wi-Fi.",
                    "En Windows: Panel de control > Centro de redes > Cambiar configuración del adaptador.",
                    "Ejecuta 'ipconfig /renew' (Windows) o 'sudo dhclient' (Linux) si usas DHCP."
                ],
                "prioridad": 100
            })
        elif "DNS" in msg:
            pasos.append({
                "title": "Problema con DNS",
                "detalle": "No se resolvieron nombres de dominio. Podría ser fallo del servidor DNS o configuración local.",
                "paso_a_paso": [
                    "Probar cambiar DNS a 8.8.8.8 / 1.1.1.1 en configuración del adaptador.",
                    "Reiniciar el adaptador de red o el servicio DNS (ej. 'systemd-resolved' en Linux).",
                    "Si hay proxy o filtro, valida su configuración."
                ],
                "prioridad": 95
            })
        elif "HTTP" in msg or "HTTPS" in msg:
            pasos.append({
                "title": "Puertos HTTP/HTTPS bloqueados",
                "detalle": "No se pudo establecer conexión a los puertos 80/443. Revisa firewall o proxy.",
                "paso_a_paso": [
                    "Desactiva temporalmente el firewall local y prueba de nuevo.",
                    "Si usas proxy, verifica credenciales y excepciones.",
                    "Comprueba reglas de salida en el router."
                ],
                "prioridad": 90
            })
        elif "latencia" in msg or "inestable" in msg:
            pasos.append({
                "title": "Latencia alta o pérdida de paquetes",
                "detalle": f"Latencia detectada: {datos.get('latencia_ms')} ms, pérdida: {datos.get('perdida_pct')}%",
                "paso_a_paso": [
                    "Acerque el equipo al AP Wi-Fi o usa cable Ethernet.",
                    "Reinicia el router y verifica intensidad de señal.",
                    "Utiliza 'traceroute' para localizar el salto con mayor latencia."
                ],
                "prioridad": 80
            })
        else:
            pasos.append({
                "title": "Diagnóstico avanzado requerido",
                "detalle": msg,
                "paso_a_paso": ["Contacte a soporte con el reporte generado."],
                "prioridad": 10
            })
    # Añadir sugerencias desde historial de casos similares
    similares = historial.buscar_casos_similares(datos, top_n=3, min_score=0.45)
    if similares:
        # Insertar al inicio una sugerencia basada en casos previos
        for s in similares:
            pasos.insert(0, {
                "title": f"Solución aplicada previamente (similitud {s.get('similitud')})",
                "detalle": f"En un caso similar se aplicó: {s.get('solucion_aplicada')}",
                "paso_a_paso": [s.get("solucion_aplicada")] if s.get("solucion_aplicada") else [],
                "prioridad": 110
            })
    pasos.sort(key=lambda x: -x.get("prioridad", 0))
    return pasos

def diagnosticar_y_registrar(gateway_ip: str = None, auto_detect_gateway: bool = True) -> Dict[str, Any]:
    datos = ejecutar_diagnostico(gateway_ip=gateway_ip, auto_detect_gateway=auto_detect_gateway)
    inferencias = inferir(datos)
    pasos = generar_pasos_accion(datos, inferencias)
    diagnostico_final = "; ".join(inferencias)
    # Guardamos sin solucion_aplicada (se podrá añadir desde la UI)
    registrar_diagnostico({
        "conexion": datos["conexion"],
        "dns": datos["dns"],
        "gateway": datos["gateway"],
        "puertos_http": datos["puertos_http"],
        "puertos_https": datos["puertos_https"],
        "latencia_ms": datos["latencia_ms"],
        "perdida_pct": datos["perdida_pct"],
        "severidad": datos["severidad"]
    }, diagnostico_final, solucion_aplicada=None)
    datos["diagnostico"] = diagnostico_final
    datos["inferencias"] = inferencias
    datos["pasos"] = pasos
    return datos
