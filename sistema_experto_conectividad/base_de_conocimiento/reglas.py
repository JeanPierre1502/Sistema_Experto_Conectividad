# base_de_conocimiento/reglas.py
from typing import Dict, Any, List, Tuple

"""
Reglas declarativas del sistema experto.
Contiene reglas 'simbólicas' (si-entonces) y plantillas que el motor de inferencia consume.
"""

# Regla simple: prioridad (mayor = primero)
# Cada regla devuelve (match_bool, mensaje, prioridad)
def regla_sin_conexion(datos: Dict[str, Any]) -> Tuple[bool, str, int]:
    if not datos.get("conexion") and not datos.get("dns") and not datos.get("gateway"):
        return True, "Sin conexión: posible desconexión física o adaptador deshabilitado.", 100
    return False, "", 0

def regla_gateway_inaccesible(datos: Dict[str, Any]) -> Tuple[bool, str, int]:
    if not datos.get("gateway") and datos.get("conexion") and (not datos.get("puertos_http") or not datos.get("puertos_https")):
        return True, "Gateway inaccesible o puertos bloqueados: posible fallo del router o reglas de firewall.", 90
    if not datos.get("gateway") and not datos.get("conexion"):
        return True, "Gateway inaccesible: posible fallo del router o red local.", 90
    return False, "", 0

def regla_fallo_dns(datos: Dict[str, Any]) -> Tuple[bool, str, int]:
    if datos.get("conexion") and not datos.get("dns"):
        return True, "Fallo de DNS: revisar configuración del servidor DNS o resolver local.", 95
    return False, "", 0

def regla_puerto_http_bloqueado(datos: Dict[str, Any]) -> Tuple[bool, str, int]:
    if datos.get("conexion") and not datos.get("puertos_http"):
        return True, "Puerto HTTP (80) bloqueado: revisar firewall/proxy.", 85
    return False, "", 0

def regla_puerto_https_bloqueado(datos: Dict[str, Any]) -> Tuple[bool, str, int]:
    if datos.get("conexion") and not datos.get("puertos_https"):
        return True, "Puerto HTTPS (443) bloqueado: revisar firewall/proxy.", 85
    return False, "", 0

def regla_latencia_alta(datos: Dict[str, Any]) -> Tuple[bool, str, int]:
    # datos puede contener 'latencia_ms' y 'perdida_pct'
    lat = datos.get("latencia_ms")
    pérdida = datos.get("perdida_pct")
    if lat is not None and (lat > 300 or (pérdida is not None and pérdida > 10)):
        return True, f"Conexión inestable: latencia alta ({lat} ms) o pérdida de paquetes ({pérdida}%).", 80
    return False, "", 0

# Lista de reglas (el motor puede recorrerlas y priorizar)
REGLAS = [
    regla_sin_conexion,
    regla_fallo_dns,
    regla_gateway_inaccesible,
    regla_puerto_http_bloqueado,
    regla_puerto_https_bloqueado,
    regla_latencia_alta,
]
