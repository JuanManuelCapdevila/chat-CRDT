#!/usr/bin/env python3
"""
Test final de sincronización por estado con P2P
"""

import time
import threading
from chat_crdt import ChatCRDT
from sincronizacion_chat import ClienteP2PChat


def test_p2p_con_estado():
    print("=== TEST P2P CON SINCRONIZACION POR ESTADO ===")
    
    # Crear usuarios
    usuarios = []
    
    print("1. Creando usuarios...")
    alice = ClienteP2PChat(ChatCRDT("alice"), "Alice", puerto=12010)
    bob = ClienteP2PChat(ChatCRDT("bob"), "Bob", puerto=12011)
    
    usuarios = [alice, bob]
    
    # Iniciar clientes
    print("2. Iniciando clientes...")
    alice.iniciar()
    time.sleep(2)
    bob.iniciar()
    time.sleep(3)
    
    print(f"Alice puerto: {alice.puerto}")
    print(f"Bob puerto: {bob.puerto}")
    
    # Enviar mensajes
    print("3. Enviando mensajes...")
    alice.chat.enviar_mensaje("Hola Bob desde Alice!")
    bob.chat.enviar_mensaje("Hola Alice desde Bob!")
    
    print("4. Esperando sincronización...")
    time.sleep(5)
    
    # Verificar estado
    print("5. Verificando estados:")
    print(f"Alice tiene {len(alice.chat.mensajes)} mensajes:")
    for msg in alice.chat.obtener_mensajes_canal("chat"):
        contenido_safe = msg.contenido.encode('ascii', 'ignore').decode('ascii')
        print(f"   {msg.autor}: {contenido_safe}")
    
    print(f"Bob tiene {len(bob.chat.mensajes)} mensajes:")
    for msg in bob.chat.obtener_mensajes_canal("chat"):
        contenido_safe = msg.contenido.encode('ascii', 'ignore').decode('ascii')
        print(f"   {msg.autor}: {contenido_safe}")
    
    # Verificar autodescubrimiento
    print("6. Nodos descubiertos:")
    alice_nodos = alice.obtener_nodos_descubiertos()
    bob_nodos = bob.obtener_nodos_descubiertos()
    
    print(f"Alice conoce {len(alice_nodos)} nodos:")
    for nodo in alice_nodos:
        print(f"   {nodo.nombre_usuario} ({nodo.ip_address}:{nodo.puerto})")
    
    print(f"Bob conoce {len(bob_nodos)} nodos:")
    for nodo in bob_nodos:
        print(f"   {nodo.nombre_usuario} ({nodo.ip_address}:{nodo.puerto})")
    
    # Verificar conexiones
    print("7. Conexiones activas:")
    print(f"Alice conexiones: {len(alice.conexiones_activas)}")
    print(f"Bob conexiones: {len(bob.conexiones_activas)}")
    
    # Detener
    print("8. Deteniendo...")
    alice.detener()
    bob.detener()
    
    print("Test completado")


if __name__ == "__main__":
    test_p2p_con_estado()