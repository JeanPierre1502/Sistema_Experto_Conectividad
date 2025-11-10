# storage/history.py
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import math

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "historial_diagnosticos.json")

def _leer_raw() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _escribir_raw(items: List[Dict[str, Any]]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

def registrar_diagnostico(datos: Dict[str, Any], resultado: str, solucion_aplicada: Optional[str] = None) -> None:
    registro = dict(datos)
    registro["diagnostico"] = resultado
    registro["solucion_aplicada"] = solucion_aplicada
    registro["timestamp"] = datetime.utcnow().isoformat() + "Z"
    historico = _leer_raw()
    historico.append(registro)
    _escribir_raw(historico)

def leer_historial(limit: int = 100) -> List[Dict[str, Any]]:
    return _leer_raw()[-limit:]

def _score_similitud(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    """
    Calcula una puntuación de similitud entre 0 y 1.
    - Comparaciones booleanas: +0.2 por coincidencia relevante (conexion, dns, gateway, puertos_http/https)
    - Latencia y pérdida: penalización por diferencia relativa.
    """
    score = 0.0
    # Booleans (peso total 0.6)
    keys_bool = ["conexion", "dns", "gateway", "puertos_http", "puertos_https"]
    per_key = 0.6 / len(keys_bool)
    for k in keys_bool:
        if k in a and k in b and a[k] == b[k]:
            score += per_key
    # Latencia (peso 0.25) - si ambos tienen latencia calculamos diferencia relativa
    lat_a = a.get("latencia_ms")
    lat_b = b.get("latencia_ms")
    if lat_a is not None and lat_b is not None:
        # normalizamos en rango [0,1], diferencias pequeñas -> +score
        diff = abs(lat_a - lat_b) / max(1.0, (lat_a + lat_b) / 2.0)
        score += max(0.0, 0.25 * (1.0 - min(diff, 1.0)))
    else:
        # si ninguno tiene latencia asignamos pequeño bonus
        score += 0.05
    # Pérdida (peso 0.15)
    p_a = a.get("perdida_pct")
    p_b = b.get("perdida_pct")
    if p_a is not None and p_b is not None:
        diff = abs(p_a - p_b) / max(1.0, (p_a + p_b) / 2.0)
        score += max(0.0, 0.15 * (1.0 - min(diff, 1.0)))
    else:
        score += 0.02
    # clamp
    return min(1.0, score)

def buscar_casos_similares(datos: Dict[str, Any], top_n: int = 3, min_score: float = 0.4) -> List[Dict[str, Any]]:
    historico = _leer_raw()
    scored = []
    for item in historico:
        s = _score_similitud(datos, item)
        if s >= min_score:
            scored.append((s, item))
    scored.sort(key=lambda x: -x[0])
    return [dict(item, similitud=round(score, 3)) for score, item in scored[:top_n]]

def aplicar_solucion_a_caso(caso: Dict[str, Any], solucion: str) -> None:
    """
    Permite etiquetar un caso existente con la solución aplicada (útil para mejorar la KB).
    Busca un match exacto por timestamp y actualiza el campo.
    """
    if "timestamp" not in caso:
        return
    historico = _leer_raw()
    updated = False
    for it in historico:
        if it.get("timestamp") == caso["timestamp"]:
            it["solucion_aplicada"] = solucion
            updated = True
            break
    if updated:
        _escribir_raw(historico)
