# Sistema Experto de Conectividad (Python)

Estructura, instalación y uso:

1. Crear entorno virtual:
   python -m venv .venv
   source .venv/bin/activate  # linux/mac
   .venv\Scripts\activate     # windows

2. Instalar dependencias:
   python -m pip install -r requirements.txt

3. Ejecutar:
   python ui/cli.py
   # o
   python ui/cli.py --auto

Arquitectura:
- base_de_conocimiento/: reglas y casos históricos.
- motor_inferencia/: pruebas de red, fuzzificación y motor de inferencia.
- storage/: historial JSON (aprendizaje).
- ui/: interfaz CLI.

El proyecto implementa fuzzificación (motor_inferencia/fuzzificacion.py), reglas simbólicas (base_de_conocimiento/reglas.py) y un motor que combina ambos (motor_inferencia/engine.py).
