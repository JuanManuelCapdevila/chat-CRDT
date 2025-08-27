#!/usr/bin/env python3
"""
Demostración de la GUI con múltiples ventanas simultáneas
"""

import threading
import time
from gui_crucigrama import CrucigramaGUI
from crucigrama_crdt import CrucigramaCRDT
from sincronizacion import ClienteP2P


def crear_ventana_usuario(nombre_usuario, palabras_iniciales=None):
    """Crea una ventana para un usuario específico"""
    def ejecutar_gui():
        app = CrucigramaGUI()
        app.nombre_usuario = nombre_usuario
        app.crucigrama = CrucigramaCRDT(15, 15, nombre_usuario)
        app.cliente_p2p = ClienteP2P(app.crucigrama)
        
        # Agregar palabras iniciales si se proporcionan
        if palabras_iniciales:
            for palabra_data in palabras_iniciales:
                app.crucigrama.agregar_palabra(**palabra_data, autor=nombre_usuario)
        
        # Actualizar el título de la ventana
        app.root.title(f"Crucigrama Cooperativo - {nombre_usuario}")
        app.ejecutar()
    
    return ejecutar_gui


def demo_multiples_usuarios():
    """Demostración con múltiples usuarios simultáneos"""
    print("=== Demo: Múltiples usuarios con GUI ===")
    print("Se abrirán 2 ventanas representando diferentes usuarios")
    print("Cada usuario puede trabajar simultáneamente en el crucigrama")
    print("Los cambios se sincronizan automáticamente entre ventanas")
    
    # Datos iniciales para cada usuario
    palabras_usuario1 = [
        {
            'pista': 'Lenguaje de programación interpretado',
            'respuesta': 'PYTHON',
            'fila_inicio': 3,
            'columna_inicio': 2,
            'direccion': 'horizontal'
        }
    ]
    
    palabras_usuario2 = [
        {
            'pista': 'Estructura de datos tipo LIFO',
            'respuesta': 'PILA',
            'fila_inicio': 5,
            'columna_inicio': 5,
            'direccion': 'vertical'
        }
    ]
    
    # Crear y ejecutar GUIs en hilos separados
    gui1 = crear_ventana_usuario("Usuario1", palabras_usuario1)
    gui2 = crear_ventana_usuario("Usuario2", palabras_usuario2)
    
    # Ejecutar en hilos separados
    thread1 = threading.Thread(target=gui1, daemon=True)
    thread2 = threading.Thread(target=gui2, daemon=True)
    
    print("Iniciando Usuario1...")
    thread1.start()
    time.sleep(2)  # Esperar un poco antes de abrir la segunda ventana
    
    print("Iniciando Usuario2...")
    thread2.start()
    
    # Esperar a que los hilos terminen
    try:
        thread1.join()
        thread2.join()
    except KeyboardInterrupt:
        print("Cerrando demo...")


def demo_conexion_automatica():
    """Demo con conexión automática entre clientes"""
    import tkinter as tk
    from tkinter import messagebox
    
    # Lista para almacenar las aplicaciones
    apps = []
    clientes_conectados = []
    
    def crear_cliente_conectado(nombre):
        app = CrucigramaGUI()
        app.nombre_usuario = nombre
        app.crucigrama = CrucigramaCRDT(15, 15, nombre)
        app.cliente_p2p = ClienteP2P(app.crucigrama)
        
        # Conectar con clientes existentes
        for i, otro_cliente in enumerate(clientes_conectados):
            app.cliente_p2p.conectar_peer(f"cliente_{i}", otro_cliente)
            otro_cliente.conectar_peer(nombre, app.cliente_p2p)
        
        apps.append(app)
        clientes_conectados.append(app.cliente_p2p)
        
        # Actualizar título
        app.root.title(f"Crucigrama Cooperativo - {nombre} (Conectado con {len(clientes_conectados)-1} usuarios)")
        
        return app
    
    # Crear primera aplicación
    app1 = crear_cliente_conectado("Usuario_Alpha")
    
    # Crear segunda aplicación después de 3 segundos
    def crear_segundo_usuario():
        time.sleep(3)
        app2 = crear_cliente_conectado("Usuario_Beta")
        app2.ejecutar()
    
    # Ejecutar segundo usuario en hilo separado
    thread = threading.Thread(target=crear_segundo_usuario, daemon=True)
    thread.start()
    
    # Ejecutar primer usuario
    app1.ejecutar()


if __name__ == "__main__":
    import sys
    
    print("Selecciona el tipo de demo:")
    print("1. Múltiples usuarios (ventanas separadas)")
    print("2. Conexión automática entre usuarios")
    print("3. Usuario único con GUI")
    
    try:
        opcion = input("Opción (1-3): ").strip()
        
        if opcion == "1":
            demo_multiples_usuarios()
        elif opcion == "2":
            demo_conexion_automatica()
        elif opcion == "3":
            from main_gui import main
            main()
        else:
            print("Opción no válida")
            
    except KeyboardInterrupt:
        print("\nDemo cancelado por el usuario")
    except Exception as e:
        print(f"Error en demo: {e}")
        import traceback
        traceback.print_exc()