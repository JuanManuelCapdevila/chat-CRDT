#!/usr/bin/env python3
"""
Punto de entrada para el chat cooperativo con CRDTs
"""

from gui_chat import ChatGUI


def main():
    """Función principal para ejecutar el chat"""
    try:
        print("Iniciando Chat Cooperativo - CRDT...")
        app = ChatGUI()
        app.ejecutar()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()