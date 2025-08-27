#!/usr/bin/env python3
"""
Punto de entrada para la versión Canvas del crucigrama cooperativo
Versión optimizada con mejor rendimiento y experiencia visual
"""

from gui_canvas import CrucigramaCanvasGUI


def main():
    """Función principal para ejecutar la GUI con Canvas"""
    try:
        print("Iniciando Crucigrama Cooperativo - Versión Canvas...")
        app = CrucigramaCanvasGUI()
        app.ejecutar()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback a la versión con widgets
        print("\nIntentando con la versión clásica...")
        try:
            from gui_crucigrama import CrucigramaGUI
            app_fallback = CrucigramaGUI()
            app_fallback.ejecutar()
        except Exception as e2:
            print(f"Error también en versión clásica: {e2}")


if __name__ == "__main__":
    main()