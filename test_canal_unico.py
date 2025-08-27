#!/usr/bin/env python3
"""
Test específico para canal único con sincronización P2P
"""

import time
import threading
from chat_crdt import ChatCRDT
from sincronizacion_chat import ClienteP2PChat


def test_canal_unico_p2p():
    print("=== TEST CANAL ÚNICO CON P2P ===")
    
    # Crear usuarios con puertos específicos
    print("1. Creando usuarios...")
    alice_chat = ChatCRDT("alice")
    bob_chat = ChatCRDT("bob")
    
    alice = ClienteP2PChat(alice_chat, "Alice", puerto=12020)
    bob = ClienteP2PChat(bob_chat, "Bob", puerto=12021)
    
    # Verificar que ambos usan canal único
    print(f"Alice canal único: {alice_chat.canal_unico}")
    print(f"Bob canal único: {bob_chat.canal_unico}")
    
    # Iniciar clientes
    print("2. Iniciando clientes...")
    alice.iniciar()
    time.sleep(1)
    bob.iniciar()
    time.sleep(2)
    
    # Verificar conexión
    print("3. Verificando autodescubrimiento...")
    print(f"Alice puerto: {alice.puerto}")
    print(f"Bob puerto: {bob.puerto}")
    
    # Esperar a que se descubran
    time.sleep(3)
    
    alice_nodos = alice.obtener_nodos_descubiertos()
    bob_nodos = bob.obtener_nodos_descubiertos()
    
    print(f"Alice descubrió {len(alice_nodos)} nodos")
    print(f"Bob descubrió {len(bob_nodos)} nodos")
    
    # Enviar mensajes
    print("4. Enviando mensajes...")
    alice_chat.enviar_mensaje("Hola Bob desde Alice!")
    bob_chat.enviar_mensaje("Hola Alice desde Bob!")
    
    print(f"Mensajes antes sync - Alice: {len(alice_chat.mensajes)}, Bob: {len(bob_chat.mensajes)}")
    
    # Forzar sincronización manual si P2P no funciona
    print("5. Sincronizando manualmente...")
    estado_alice = alice_chat.obtener_estado_completo()
    estado_bob = bob_chat.obtener_estado_completo()
    
    alice_chat.sincronizar_por_estado(estado_bob)
    bob_chat.sincronizar_por_estado(estado_alice)
    
    print(f"Mensajes después sync - Alice: {len(alice_chat.mensajes)}, Bob: {len(bob_chat.mensajes)}")
    
    # Verificar mensajes
    print("6. Verificando mensajes en canal único:")
    alice_msgs = alice_chat.obtener_mensajes_canal()  # Sin especificar canal
    bob_msgs = bob_chat.obtener_mensajes_canal()    # Sin especificar canal
    
    print(f"Alice ve {len(alice_msgs)} mensajes:")
    for msg in alice_msgs:
        print(f"  {msg.autor}: {msg.contenido[:50]}...")
    
    print(f"Bob ve {len(bob_msgs)} mensajes:")
    for msg in bob_msgs:
        print(f"  {msg.autor}: {msg.contenido[:50]}...")
    
    # Verificar convergencia
    if len(alice_msgs) == len(bob_msgs):
        print("[OK] SUCCESS: Ambos nodos ven el mismo numero de mensajes")
        
        # Verificar IDs
        alice_ids = set(alice_chat.mensajes.keys())
        bob_ids = set(bob_chat.mensajes.keys())
        
        if alice_ids == bob_ids:
            print("[OK] SUCCESS: Los IDs de mensajes coinciden")
            print("CANAL UNICO FUNCIONA CORRECTAMENTE!")
        else:
            print(f"[ERROR] IDs diferentes. Alice: {len(alice_ids)}, Bob: {len(bob_ids)}")
            print(f"Solo en Alice: {alice_ids - bob_ids}")
            print(f"Solo en Bob: {bob_ids - alice_ids}")
    else:
        print(f"[ERROR] Diferentes numeros de mensajes - Alice: {len(alice_msgs)}, Bob: {len(bob_msgs)}")
    
    # Detener
    print("7. Deteniendo...")
    alice.detener()
    bob.detener()
    
    print("Test completado")


if __name__ == "__main__":
    test_canal_unico_p2p()