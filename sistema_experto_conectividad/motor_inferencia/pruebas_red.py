# motor_inferencia/pruebas_red.py
import socket
import subprocess
import sys
import re
from typing import Dict, Any, Tuple, List
from ping3 import ping
import psutil
import time

DEFAULT_PING_HOST = "8.8.8.8"
DNS_TEST_DOMAINS = ["www.google.com", "www.cloudflare.com", "www.openai.com"]
SERVICE_TESTS = ["mail.google.com", "facebook.com", "youtube.com"]

def detectar_gateway_sistema() -> str:
    """
    Intenta detectar la puerta de enlace por varios métodos:
    1) netifaces (si está instalado)
    2) 'ip route' en Linux/macOS
    3) 'ipconfig' / 'route print' en Windows (busca 'Default Gateway' o 'Puerta predeterminada')
    4) fallback heurístico: toma la IP local y pone .1 en el último octeto
    Retorna una IP string o None si falla.
    """

    try:
        out = subprocess.check_output(["ip", "route"], stderr=subprocess.DEVNULL, universal_newlines=True, timeout=2)
        m = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', out)
        if m:
            return m.group(1)
    except Exception:
        pass

    if sys.platform.startswith("win"):
        try:
            out = subprocess.check_output(["ipconfig"], universal_newlines=True, stderr=subprocess.DEVNULL, timeout=2)
            # Recorremos líneas buscando "Default Gateway" o "Puerta predeterminada"
            lines = out.splitlines()
            gw = None
            for i, line in enumerate(lines):
                if ("Default Gateway" in line) or ("Puerta predeterminada" in line):
                    # la IP puede estar en la misma línea o en la siguiente
                    parts = re.findall(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if parts:
                        gw = parts[0]; break
                    # else check next few lines
                    for j in range(1, 3):
                        if i + j < len(lines):
                            parts = re.findall(r'(\d+\.\d+\.\d+\.\d+)', lines[i + j])
                            if parts:
                                gw = parts[0]; break
                if gw:
                    break
            if gw:
                return gw
        except Exception:
            pass

        try:
            out = subprocess.check_output(["route", "print"], universal_newlines=True, stderr=subprocess.DEVNULL, timeout=2)
            m = re.search(r'\s0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)', out)
            if m:
                return m.group(1)
        except Exception:
            pass

    try:
        local_ip = socket.gethostbyname(socket.gethostname())
        if local_ip and re.match(r'\d+\.\d+\.\d+\.\d+', local_ip):
            octs = local_ip.split('.')
            octs[-1] = '1'
            gw = '.'.join(octs)
            return gw
    except Exception:
        pass

    return None


def verificar_conexion(host: str = DEFAULT_PING_HOST, count: int = 3, timeout: float = 2.0) -> Tuple[bool, float, float]:
    """
    Realiza varios pings y devuelve (hay_conexion, latencia_media_ms, perdida_pct).
    """
    tiempos: List[float] = []
    fallos = 0
    for _ in range(count):
        try:
            t = ping(host, timeout=timeout, unit="ms")
            if t is None:
                fallos += 1
            else:
                tiempos.append(float(t))
        except Exception:
            fallos += 1
        time.sleep(0.15)
    total = count
    perdida = (fallos / total) * 100.0
    latencia = sum(tiempos) / len(tiempos) if tiempos else None
    return (len(tiempos) > 0, latencia, perdida)

def verificar_dns(domains: list = DNS_TEST_DOMAINS, timeout: float = 2.0) -> bool:
    for d in domains:
        try:
            socket.gethostbyname(d)
            return True
        except Exception:
            continue
    return False

def verificar_gateway(ip: str, timeout: float = 2.0) -> bool:
    try:
        resp = ping(ip, timeout=timeout, unit="ms")
        return resp is not None
    except Exception:
        return False

def comprobar_puerto(host: str, port: int, timeout: float = 3.0) -> bool:
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except Exception:
        return False

def estado_adaptadores() -> Dict[str, bool]:
    stats = psutil.net_if_stats()
    return {name: stats[name].isup for name in stats}

def probar_servicios(domains: list = SERVICE_TESTS) -> Dict[str, bool]:
    resultados = {}
    for d in domains:
        try:
            host = socket.gethostbyname(d)
            ok = comprobar_puerto(host, 443, timeout=3.0)
            resultados[d] = ok
        except Exception:
            resultados[d] = False
    return resultados
