# ui/cli.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import argparse
from motor_inferencia import engine
from storage.historial import leer_historial
import pprint
from sistema_experto_conectividad.motor_inferencia import engine
from sistema_experto_conectividad.storage.historial import leer_historial


def menu_interactivo():
    while True:
        print("\n--- SISTEMA EXPERTO DE CONECTIVIDAD ---")
        print("1) Ejecutar diagnóstico automático")
        print("2) Ver historial de diagnósticos")
        print("3) Salir")
        o = input("Selecciona opción: ").strip()
        if o == "1":
            gateway = input("Introduce IP del gateway (default 192.168.1.1): ").strip() or "192.168.1.1"
            print("\nEjecutando diagnóstico... (puede tardar unos segundos)")
            resultado = engine.diagnosticar_y_registrar(gateway)
            print("\n=== RESULTADO ===")
            pprint.pprint(resultado)
            print("=================")
        elif o == "2":
            h = leer_historial()
            if not h:
                print("No hay historial registrado.")
            else:
                for i, item in enumerate(h, start=1):
                    print(f"{i}. {item.get('timestamp')} | Diagnóstico: {item.get('diagnostico')}")
        elif o == "3":
            print("Saliendo...")
            break
        else:
            print("Opción inválida.")

def main():
    parser = argparse.ArgumentParser(prog="red-expert")
    parser.add_argument("--auto", action="store_true", help="Ejecuta una prueba rápida con gateway por defecto")
    args = parser.parse_args()
    if args.auto:
        resultado = engine.diagnosticar_y_registrar("192.168.1.1")
        import pprint; pprint.pprint(resultado)
    else:
        menu_interactivo()

if __name__ == "__main__":
    main()
