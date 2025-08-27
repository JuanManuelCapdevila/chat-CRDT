#!/usr/bin/env python3
"""
Punto de entrada para la versión GUI del crucigrama cooperativo
"""

from gui_crucigrama import CrucigramaGUI


def main():
    """Función principal para ejecutar la GUI"""
    try:
        app = CrucigramaGUI()
        app.ejecutar()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()