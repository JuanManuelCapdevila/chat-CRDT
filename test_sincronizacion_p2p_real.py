#!/usr/bin/env python3
"""
Test de sincronización P2P con IPs reales - simula dos nodos físicos diferentes
"""

import time
import threading
from chat_crdt import ChatCRDT
from sincronizacion_chat import ClienteP2PChat


def test_sincronizacion_p2p():
    print("=== TEST SINCRONIZACION P2P CON IPS REALES ===")
    
    # Crear dos nodos con puertos diferentes
    print("1. Creando nodos...")
    alice_chat = ChatCRDT("alice")
    bob_chat = ChatCRDT("bob")
    
    alice = ClienteP2PChat(alice_chat, "Alice", puerto=12030)
    bob = ClienteP2PChat(bob_chat, "Bob", puerto=12031)
    
    # Verificar puertos asignados
    print(f"Alice puerto: {alice.puerto}")
    print(f"Bob puerto: {bob.puerto}")
    
    # Iniciar nodos
    print("\n2. Iniciando nodos...")
    alice.iniciar()
    time.sleep(1)
    bob.iniciar()
    time.sleep(3)
    
    # Verificar autodescubrimiento
    print("\n3. Verificando autodescubrimiento...")
    alice_nodos = alice.obtener_nodos_descubiertos()
    bob_nodos = bob.obtener_nodos_descubiertos()
    
    print(f"Alice descubrió {len(alice_nodos)} nodos:")
    for nodo in alice_nodos:
        print(f"   {nodo.nombre_usuario} en {nodo.ip_address}:{nodo.puerto}")
    
    print(f"Bob descubrió {len(bob_nodos)} nodos:")
    for nodo in bob_nodos:
        print(f"   {nodo.nombre_usuario} en {nodo.ip_address}:{nodo.puerto}")
    
    # Verificar conexiones
    print(f"\nConexiones activas - Alice: {len(alice.conexiones_activas)}, Bob: {len(bob.conexiones_activas)}")
    
    # Enviar mensajes
    print("\n4. Enviando mensajes...")
    alice_chat.enviar_mensaje("Hola desde Alice!")
    bob_chat.enviar_mensaje("Hola desde Bob!")
    
    print(f"Mensajes iniciales - Alice: {len(alice_chat.mensajes)}, Bob: {len(bob_chat.mensajes)}")
    
    # Esperar sincronización automática
    print("\n5. Esperando sincronización automática (10 segundos)...")
    time.sleep(10)
    
    print(f"Después de sync automático - Alice: {len(alice_chat.mensajes)}, Bob: {len(bob_chat.mensajes)}")
    
    # Mostrar mensajes en cada nodo
    print("\n6. Mensajes en Alice:")
    for msg in alice_chat.obtener_mensajes_canal():
        print(f"   {msg.autor}: {msg.contenido}")
    
    print("Mensajes en Bob:")
    for msg in bob_chat.obtener_mensajes_canal():
        print(f"   {msg.autor}: {msg.contenido}")
    
    # Verificar sincronización manual si la automática falló
    if len(alice_chat.mensajes) != len(bob_chat.mensajes):
        print("\n7. Sincronización automática falló - probando manual...")
        estado_alice = alice_chat.obtener_estado_completo()
        estado_bob = bob_chat.obtener_estado_completo()
        
        alice_chat.sincronizar_por_estado(estado_bob)
        bob_chat.sincronizar_por_estado(estado_alice)
        
        print(f"Después de sync manual - Alice: {len(alice_chat.mensajes)}, Bob: {len(bob_chat.mensajes)}")
        
        if len(alice_chat.mensajes) == len(bob_chat.mensajes):
            print("[OK] Sincronización manual exitosa")
        else:
            print("[ERROR] Sincronización manual también falló")
    else:
        print("\n[OK] Sincronización automática exitosa")
    
    # Verificar convergencia
    alice_ids = set(alice_chat.mensajes.keys())
    bob_ids = set(bob_chat.mensajes.keys())
    
    if alice_ids == bob_ids:
        print("[SUCCESS] Ambos nodos convergieron correctamente")
    else:
        print("[ERROR] Los nodos no convergieron")
        print(f"Solo en Alice: {alice_ids - bob_ids}")
        print(f"Solo en Bob: {bob_ids - alice_ids}")
    
    # Detener
    print("\n8. Deteniendo nodos...")
    alice.detener()
    bob.detener()
    
    print("Test completado")


if __name__ == "__main__":
    test_sincronizacion_p2p()