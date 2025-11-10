# motor_inferencia/fuzzificacion.py
from typing import Dict, Any

"""
Fuzzificación simple sin dependencia externa pesada.
Define categorías para latencia y pérdida de paquetes:
- latencia: baja (<=50ms), media (~50-300ms), alta (>300ms)
- perdida: baja (<1%), media (1-10%), alta (>10%)
Devuelve grados (0..1) y una recomendación difusa.
"""

def membership_latencia(lat_ms: float) -> Dict[str, float]:
    if lat_ms is None:
        return {"baja": 0.0, "media": 0.0, "alta": 1.0}
    baja = max(0.0, min(1.0, (50 - lat_ms)/50)) if lat_ms <= 50 else 0.0
    media = 0.0
    if 50 < lat_ms <= 300:
        media = (lat_ms - 50) / (300 - 50)
        media = max(0.0, min(1.0, media))
    alta = 1.0 if lat_ms > 300 else max(0.0, (lat_ms - 50) / (300 - 50))
    return {"baja": baja, "media": media, "alta": alta}

def membership_perdida(pct: float) -> Dict[str, float]:
    if pct is None:
        return {"baja": 1.0, "media": 0.0, "alta": 0.0}
    baja = 1.0 if pct <= 1 else max(0.0, (10 - pct)/9) if pct <= 10 else 0.0
    media = 0.0
    if 1 < pct <= 10:
        media = (pct - 1) / (10 - 1)
    alta = 1.0 if pct > 10 else max(0.0, (pct - 1) / 9) if pct > 1 else 0.0
    return {"baja": baja, "media": media, "alta": alta}

def evaluar_severidad(lat_ms: float, perdida_pct: float) -> str:
    """
    Agrega ambas fuzzificaciones y entrega una severidad textual: 'baja','media','alta'
    Método simple: si cualquiera tiene grado alto>0.6 => 'alta', else if any media>0.5 => 'media' else 'baja'
    """
    lat = membership_latencia(lat_ms)
    per = membership_perdida(perdida_pct)
    if lat["alta"] > 0.6 or per["alta"] > 0.6:
        return "alta"
    if lat["media"] > 0.5 or per["media"] > 0.5:
        return "media"
    return "baja"
