#!/usr/bin/env python3
"""
Demostración del sistema de autodescubrimiento de nodos
"""

import time
import threading
import logging
from crucigrama_crdt import CrucigramaCRDT
from sincronizacion import ClienteP2P
from descubrimiento_nodos import GestorDescubrimiento, TipoDescubrimiento


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def demo_udp_broadcast():
    """Demo del algoritmo UDP Broadcast"""
    print("=== Demo: Autodescubrimiento UDP Broadcast ===\n")
    
    # Crear 3 nodos simulados
    nodos = []
    for i in range(3):
        nombre = f"Usuario_{i+1}"
        crucigrama = CrucigramaCRDT(10, 10, f"nodo_{i+1}")
        cliente = ClienteP2P(
            crucigrama, 
            puerto=12345 + i,
            nombre_usuario=nombre,
            habilitar_autodescubrimiento=True
        )
        nodos.append((nombre, cliente))
    
    print("Nodos creados:")
    for nombre, cliente in nodos:
        print(f"- {nombre}: {cliente.crucigrama.node_id}")
    
    # Iniciar autodescubrimiento en todos los nodos
    print("\nIniciando autodescubrimiento...")
    for nombre, cliente in nodos:
        cliente.iniciar_autodescubrimiento()
        time.sleep(1)  # Esperar entre inicios
    
    # Esperar a que se descubran mutuamente
    print("\nEsperando descubrimiento mutuo (15 segundos)...")
    time.sleep(15)
    
    # Mostrar resultados
    print("\n=== Resultados del Descubrimiento ===")
    for nombre, cliente in nodos:
        nodos_descubiertos = cliente.obtener_nodos_descubiertos()
        stats = cliente.obtener_estadisticas_descubrimiento()
        
        print(f"\n{nombre} ({cliente.crucigrama.node_id[:8]}...):")
        print(f"  Nodos descubiertos: {len(nodos_descubiertos)}")
        
        for nodo in nodos_descubiertos:
            print(f"    - {nodo.nombre_usuario} en {nodo.ip_address}:{nodo.puerto}")
        
        print(f"  Estadísticas: {stats}")
    
    # Detener servicios
    print("\nDeteniendo servicios...")
    for nombre, cliente in nodos:
        cliente.detener_sync()
    
    print("Demo completado.")


def demo_interactivo():
    """Demo interactivo donde el usuario puede agregar nodos dinámicamente"""
    print("=== Demo Interactivo: Autodescubrimiento ===")
    print("Puedes agregar nodos dinámicamente y ver cómo se descubren")
    
    nodos_activos = {}
    contador_nodos = 0
    
    def crear_nodo(nombre_personalizado=None):
        nonlocal contador_nodos
        contador_nodos += 1
        
        nombre = nombre_personalizado or f"Nodo_{contador_nodos}"
        crucigrama = CrucigramaCRDT(10, 10, f"nodo_{contador_nodos}")
        cliente = ClienteP2P(
            crucigrama,
            puerto=12345 + contador_nodos,
            nombre_usuario=nombre,
            habilitar_autodescubrimiento=True
        )
        
        # Configurar callbacks para mostrar eventos
        if cliente.gestor_descubrimiento:
            cliente.gestor_descubrimiento.agregar_callback_cambio(
                lambda tipo, nodo, n=nombre: print(f"[{n}] {tipo.upper()}: {nodo.nombre_usuario}")
            )
        
        cliente.iniciar_autodescubrimiento()
        nodos_activos[nombre] = cliente
        print(f"Nodo '{nombre}' creado y activo")
        return cliente
    
    def mostrar_estado():
        print(f"\n=== Estado Actual ({len(nodos_activos)} nodos activos) ===")
        for nombre, cliente in nodos_activos.items():
            nodos_desc = cliente.obtener_nodos_descubiertos()
            print(f"{nombre}: {len(nodos_desc)} nodos descubiertos")
    
    def detener_nodo(nombre):
        if nombre in nodos_activos:
            nodos_activos[nombre].detener_sync()
            del nodos_activos[nombre]
            print(f"Nodo '{nombre}' detenido")
        else:
            print(f"Nodo '{nombre}' no encontrado")
    
    # Crear primer nodo
    crear_nodo("NodoInicial")
    
    print("\nComandos disponibles:")
    print("  'add [nombre]' - Agregar nuevo nodo")
    print("  'status' - Mostrar estado actual")
    print("  'stop [nombre]' - Detener nodo específico")
    print("  'quit' - Salir")
    
    try:
        while True:
            comando = input("\n> ").strip().lower()
            
            if comando == 'quit':
                break
            elif comando == 'status':
                mostrar_estado()
            elif comando.startswith('add'):
                partes = comando.split()
                nombre_nuevo = partes[1] if len(partes) > 1 else None
                crear_nodo(nombre_nuevo)
            elif comando.startswith('stop'):
                partes = comando.split()
                if len(partes) > 1:
                    detener_nodo(partes[1])
                else:
                    print("Especifica el nombre del nodo a detener")
            else:
                print("Comando no reconocido")
    
    except KeyboardInterrupt:
        pass
    
    # Limpiar al salir
    print("\nDeteniendo todos los nodos...")
    for cliente in nodos_activos.values():
        cliente.detener_sync()
    
    print("Demo interactivo terminado.")


def demo_algoritmos_multiples():
    """Demo usando múltiples algoritmos de descubrimiento simultáneamente"""
    print("=== Demo: Múltiples Algoritmos de Descubrimiento ===\n")
    
    # Crear gestor con múltiples algoritmos
    gestor = GestorDescubrimiento("nodo_maestro", "Usuario_Maestro")
    
    # Agregar diferentes algoritmos
    try:
        gestor.agregar_descubridor(TipoDescubrimiento.UDP_BROADCAST, 12345)
        print("✓ UDP Broadcast configurado")
    except Exception as e:
        print(f"✗ Error configurando UDP Broadcast: {e}")
    
    try:
        gestor.agregar_descubridor(TipoDescubrimiento.SCAN_PUERTOS, 12345)
        print("✓ Escaneo de puertos configurado")
    except Exception as e:
        print(f"✗ Error configurando escaneo de puertos: {e}")
    
    # Configurar callbacks
    def on_nodo_cambio(tipo, nodo):
        print(f"[MAESTRO] {tipo.upper()}: {nodo.nombre_usuario} ({nodo.ip_address})")
    
    gestor.agregar_callback_cambio(on_nodo_cambio)
    
    # Iniciar todos los descubridores
    print("\nIniciando todos los algoritmos...")
    gestor.iniciar_todos()
    
    # Crear algunos nodos cliente para que sean descubiertos
    print("Creando nodos cliente...")
    clientes = []
    for i in range(2):
        nombre = f"Cliente_{i+1}"
        crucigrama = CrucigramaCRDT(10, 10, f"cliente_{i+1}")
        cliente = ClienteP2P(
            crucigrama,
            puerto=13000 + i,
            nombre_usuario=nombre,
            habilitar_autodescubrimiento=True
        )
        cliente.iniciar_autodescubrimiento()
        clientes.append(cliente)
        time.sleep(2)
    
    # Monitoreo por 30 segundos
    print("\nMonitoreando por 30 segundos...")
    for i in range(30):
        time.sleep(1)
        if i % 10 == 9:  # Cada 10 segundos
            stats = gestor.obtener_estadisticas()
            print(f"Estadísticas (t={i+1}s): {stats}")
    
    # Cleanup
    print("\nDeteniendo servicios...")
    gestor.detener_todos()
    for cliente in clientes:
        cliente.detener_sync()
    
    print("Demo de múltiples algoritmos completado.")


def main():
    """Función principal con menú de demos"""
    print("=== Demos de Autodescubrimiento de Nodos ===\n")
    print("Selecciona el demo a ejecutar:")
    print("1. UDP Broadcast básico")
    print("2. Demo interactivo")
    print("3. Múltiples algoritmos")
    print("4. Ejecutar todos")
    
    try:
        opcion = input("\nOpción (1-4): ").strip()
        
        if opcion == "1":
            demo_udp_broadcast()
        elif opcion == "2":
            demo_interactivo()
        elif opcion == "3":
            demo_algoritmos_multiples()
        elif opcion == "4":
            print("Ejecutando todos los demos...\n")
            demo_udp_broadcast()
            time.sleep(2)
            demo_algoritmos_multiples()
            time.sleep(2)
            demo_interactivo()
        else:
            print("Opción no válida")
    
    except KeyboardInterrupt:
        print("\nDemo cancelado por el usuario")
    except Exception as e:
        print(f"Error ejecutando demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()