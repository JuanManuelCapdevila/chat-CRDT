#!/usr/bin/env python3
"""
Test específico para red real - verifica IPs y conectividad P2P
"""

import time
import socket
from chat_crdt import ChatCRDT
from sincronizacion_chat import ClienteP2PChat


def obtener_ip_local():
    """Obtiene la IP local de la máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def test_red_real():
    print("=== TEST CONECTIVIDAD RED REAL ===")
    
    # Verificar IP local
    ip_local = obtener_ip_local()
    print(f"IP local de esta máquina: {ip_local}")
    
    if ip_local == "127.0.0.1":
        print("[WARNING] No se pudo detectar IP de red - usando loopback")
    else:
        print(f"[OK] IP de red detectada correctamente")
    
    # Crear cliente de prueba
    print("\n1. Creando cliente de prueba...")
    chat = ChatCRDT("test_user")
    cliente = ClienteP2PChat(chat, "TestUser", habilitar_autodescubrimiento=True)
    
    # Verificar puerto asignado
    print(f"Puerto asignado: {cliente.puerto}")
    
    # Iniciar cliente
    print("\n2. Iniciando cliente...")
    cliente.iniciar()
    
    # Esperar descubrimiento
    print("\n3. Esperando descubrimiento de nodos (10 segundos)...")
    time.sleep(10)
    
    # Verificar nodos descubiertos
    nodos = cliente.obtener_nodos_descubiertos()
    print(f"\n4. Nodos descubiertos: {len(nodos)}")
    
    for nodo in nodos:
        print(f"   - {nodo.nombre_usuario} ({nodo.node_id})")
        print(f"     IP: {nodo.ip_address}")
        print(f"     Puerto: {nodo.puerto}")
        print(f"     Timestamp: {nodo.timestamp}")
        
        # Verificar conectividad
        if nodo.ip_address != "localhost" and nodo.ip_address != "127.0.0.1":
            print(f"     [OK] IP de red real detectada")
        else:
            print(f"     [WARNING] Usando IP local")
    
    # Verificar conexiones activas
    conexiones = len(cliente.conexiones_activas)
    print(f"\n5. Conexiones P2P activas: {conexiones}")
    
    if conexiones > 0:
        print("[OK] Hay conexiones P2P activas")
        
        # Enviar mensaje de prueba
        print("\n6. Enviando mensaje de prueba...")
        chat.enviar_mensaje("Mensaje de prueba desde test_red_real")
        
        time.sleep(2)  # Esperar sincronización
        
        print(f"Total mensajes en chat: {len(chat.mensajes)}")
    else:
        print("[INFO] No hay conexiones P2P - solo este nodo")
    
    # Estadísticas finales
    stats = cliente.obtener_estadisticas_conexion()
    print(f"\n7. Estadísticas finales:")
    print(f"   Nodos conocidos: {stats['nodos_conocidos']}")
    print(f"   Conexiones activas: {stats['conexiones_activas']}")
    print(f"   Puerto local: {stats['puerto_local']}")
    print(f"   Autodescubrimiento: {'activo' if stats['autodescubrimiento_activo'] else 'inactivo'}")
    
    # Detener
    print("\n8. Deteniendo cliente...")
    cliente.detener()
    
    print("Test completado")


if __name__ == "__main__":
    test_red_real()